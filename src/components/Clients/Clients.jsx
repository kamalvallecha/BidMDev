import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Input, Form, message } from 'antd';
import axios from '../../api/axios';
import './Clients.css';

const Clients = () => {
    const [clients, setClients] = useState([]);
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [isEditModalVisible, setIsEditModalVisible] = useState(false);
    const [editingClient, setEditingClient] = useState(null);
    const [searchText, setSearchText] = useState('');
    const [form] = Form.useForm();
    const [editForm] = Form.useForm();

    useEffect(() => {
        fetchClients();
    }, []);

    const fetchClients = async () => {
        try {
            const response = await axios.get('/api/clients');
            setClients(response.data);
        } catch (error) {
            console.error('Error fetching clients:', error);
            message.error('Failed to fetch clients');
        }
    };

    const handleSubmit = async (values) => {
        try {
            await axios.post('/api/clients', values);
            fetchClients();
            setIsModalVisible(false);
            form.resetFields();
            message.success('Client created successfully');
        } catch (error) {
            console.error('Error creating client:', error);
            message.error('Failed to create client');
        }
    };

    const showEditModal = (client) => {
        setEditingClient(client);
        editForm.setFieldsValue(client);
        setIsEditModalVisible(true);
    };

    const handleEditSubmit = async (values) => {
        try {
            await axios.put(`/api/clients/${editingClient.id}`, values);
            fetchClients();
            setIsEditModalVisible(false);
            setEditingClient(null);
            message.success('Client updated successfully');
        } catch (error) {
            console.error('Error updating client:', error);
            message.error('Failed to update client');
        }
    };

    const handleDelete = async (id) => {
        try {
            await axios.delete(`/api/clients/${id}`);
            fetchClients();
            message.success('Client deleted successfully');
        } catch (error) {
            console.error('Error deleting client:', error);
            message.error('Failed to delete client');
        }
    };

    const columns = [
        {
            title: 'Client ID',
            dataIndex: 'client_id',
            key: 'client_id',
            width: '10%',
        },
        {
            title: 'Client Name',
            dataIndex: 'client_name',
            key: 'client_name',
            width: '20%',
        },
        {
            title: 'Contact Person',
            dataIndex: 'contact_person',
            key: 'contact_person',
            width: '15%',
        },
        {
            title: 'Email',
            dataIndex: 'email',
            key: 'email',
            width: '20%',
        },
        {
            title: 'Phone',
            dataIndex: 'phone',
            key: 'phone',
            width: '15%',
        },
        {
            title: 'Country',
            dataIndex: 'country',
            key: 'country',
            width: '10%',
        },
        {
            title: 'Actions',
            key: 'actions',
            width: '10%',
            render: (_, record) => (
                <span>
                    <Button 
                        type="link" 
                        style={{ color: '#1890ff', padding: '0 8px' }}
                        onClick={() => showEditModal(record)}
                    >
                        EDIT
                    </Button>
                    <Button 
                        type="link" 
                        style={{ color: '#ff4d4f', padding: '0 8px' }}
                        onClick={() => handleDelete(record.id)}
                    >
                        DELETE
                    </Button>
                </span>
            ),
        },
    ];

    const filteredClients = clients.filter(client => 
        client.client_name?.toLowerCase().includes(searchText.toLowerCase()) ||
        client.client_id?.toLowerCase().includes(searchText.toLowerCase())
    );

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                marginBottom: '16px' 
            }}>
                <h2 style={{ margin: 0 }}>Client List</h2>
                <div style={{ display: 'flex', gap: '16px' }}>
                    <Input.Search
                        placeholder="Search clients..."
                        style={{ width: 300 }}
                        onChange={(e) => setSearchText(e.target.value)}
                    />
                    <Button type="primary" onClick={() => setIsModalVisible(true)}>
                        ADD CLIENT
                    </Button>
                </div>
            </div>

            <Table
                columns={columns}
                dataSource={filteredClients}
                rowKey="id"
                bordered
                style={{ backgroundColor: 'white' }}
            />

            <Modal
                title="Add New Client"
                open={isModalVisible}
                onCancel={() => setIsModalVisible(false)}
                footer={null}
                width={800}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                >
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        <Form.Item
                            name="client_id"
                            label="Client ID"
                            rules={[{ required: true, message: 'Please enter Client ID' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="client_name"
                            label="Client Name"
                            rules={[{ required: true, message: 'Please enter Client Name' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="contact_person"
                            label="Contact Person"
                            rules={[{ required: true, message: 'Please enter Contact Person' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="email"
                            label="Email"
                            rules={[
                                { required: true, message: 'Please enter Email' },
                                { type: 'email', message: 'Please enter a valid email' }
                            ]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="phone"
                            label="Phone"
                            rules={[{ required: true, message: 'Please enter Phone' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="country"
                            label="Country"
                            rules={[{ required: true, message: 'Please enter Country' }]}
                        >
                            <Input />
                        </Form.Item>
                    </div>

                    <div style={{ textAlign: 'right', marginTop: '24px' }}>
                        <Button onClick={() => setIsModalVisible(false)} style={{ marginRight: 8 }}>
                            Cancel
                        </Button>
                        <Button type="primary" htmlType="submit">
                            Add Client
                        </Button>
                    </div>
                </Form>
            </Modal>

            <Modal
                title="Edit Client"
                open={isEditModalVisible}
                onCancel={() => {
                    setIsEditModalVisible(false);
                    setEditingClient(null);
                }}
                footer={null}
                width={800}
            >
                <Form
                    form={editForm}
                    layout="vertical"
                    onFinish={handleEditSubmit}
                >
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        <Form.Item
                            name="client_id"
                            label="Client ID"
                            rules={[{ required: true, message: 'Please enter Client ID' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="client_name"
                            label="Client Name"
                            rules={[{ required: true, message: 'Please enter Client Name' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="contact_person"
                            label="Contact Person"
                            rules={[{ required: true, message: 'Please enter Contact Person' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="email"
                            label="Email"
                            rules={[
                                { required: true, message: 'Please enter Email' },
                                { type: 'email', message: 'Please enter a valid email' }
                            ]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="phone"
                            label="Phone"
                            rules={[{ required: true, message: 'Please enter Phone' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="country"
                            label="Country"
                            rules={[{ required: true, message: 'Please enter Country' }]}
                        >
                            <Input />
                        </Form.Item>
                    </div>

                    <div style={{ textAlign: 'right', marginTop: '24px' }}>
                        <Button 
                            onClick={() => {
                                setIsEditModalVisible(false);
                                setEditingClient(null);
                            }} 
                            style={{ marginRight: 8 }}
                        >
                            Cancel
                        </Button>
                        <Button type="primary" htmlType="submit">
                            Update Client
                        </Button>
                    </div>
                </Form>
            </Modal>
        </div>
    );
};

export default Clients; 