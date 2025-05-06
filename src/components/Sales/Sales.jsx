import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Input, Form, Select, message } from 'antd';
import axios from '../../api/axios';
import './Sales.css';

const { Option } = Select;

const Sales = () => {
    const [sales, setSales] = useState([]);
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [isEditModalVisible, setIsEditModalVisible] = useState(false);
    const [currentSales, setCurrentSales] = useState(null);
    const [searchText, setSearchText] = useState('');
    const [form] = Form.useForm();
    const [editForm] = Form.useForm();
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchSales();
    }, []);

    const fetchSales = async () => {
        try {
            const response = await axios.get('/api/sales');
            setSales(response.data);
        } catch (error) {
            console.error('Error fetching sales:', error);
            message.error('Failed to fetch sales');
        }
    };

    const handleSubmit = async (values) => {
        try {
            await axios.post('/api/sales', values);
            fetchSales();
            setIsModalVisible(false);
            form.resetFields();
            message.success('Sales record created successfully');
        } catch (error) {
            console.error('Error creating sales:', error);
            message.error('Failed to create sales record');
        }
    };

    const handleEdit = (record) => {
        setCurrentSales(record);
        editForm.setFieldsValue({
            sales_id: record.sales_id,
            sales_person: record.sales_person,
            contact_person: record.contact_person,
            reporting_manager: record.reporting_manager,
            region: record.region
        });
        setIsEditModalVisible(true);
    };

    const handleEditSubmit = async (values) => {
        if (!currentSales) return;
        
        try {
            setLoading(true);
            console.log('Sending PUT request to:', `/api/sales/${currentSales.id}`, values);
            const response = await axios.put(`/api/sales/${currentSales.id}`, values);
            console.log('Response:', response);
            if (response.status === 200) {
                message.success('Sales record updated successfully');
                fetchSales();
                setIsEditModalVisible(false);
                setCurrentSales(null);
            }
        } catch (error) {
            console.error('Error updating sales:', error);
            console.error('Error details:', error.response?.data);
            message.error('Failed to update sales record: ' + (error.response?.data?.error || error.message));
        } finally {
            setLoading(false);
        }
    };

    const handleEditCancel = () => {
        setIsEditModalVisible(false);
        setCurrentSales(null);
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this sales record?')) {
            try {
                await axios.delete(`/api/sales/${id}`);
                fetchSales();
                message.success('Sales record deleted successfully');
            } catch (error) {
                console.error('Error deleting sales:', error);
                message.error('Failed to delete sales record');
            }
        }
    };

    const columns = [
        {
            title: 'ID',
            dataIndex: 'id',
            key: 'id',
            width: '5%',
        },
        {
            title: 'Sales ID',
            dataIndex: 'sales_id',
            key: 'sales_id',
            width: '10%',
        },
        {
            title: 'Sales Person',
            dataIndex: 'sales_person',
            key: 'sales_person',
            width: '20%',
        },
        {
            title: 'Contact Person',
            dataIndex: 'contact_person',
            key: 'contact_person',
            width: '20%',
        },
        {
            title: 'Reporting Manager',
            dataIndex: 'reporting_manager',
            key: 'reporting_manager',
            width: '20%',
        },
        {
            title: 'Region',
            dataIndex: 'region',
            key: 'region',
            width: '15%',
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
                        onClick={() => handleEdit(record)}
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

    const filteredSales = sales.filter(sale => 
        sale.sales_person?.toLowerCase().includes(searchText.toLowerCase()) ||
        sale.sales_id?.toLowerCase().includes(searchText.toLowerCase())
    );

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                marginBottom: '16px' 
            }}>
                <h2 style={{ margin: 0 }}>Sales List</h2>
                <div style={{ display: 'flex', gap: '16px' }}>
                    <Input.Search
                        placeholder="Search sales..."
                        style={{ width: 300 }}
                        onChange={(e) => setSearchText(e.target.value)}
                    />
                    <Button type="primary" onClick={() => setIsModalVisible(true)}>
                        ADD SALES
                    </Button>
                </div>
            </div>

            <Table
                columns={columns}
                dataSource={filteredSales}
                rowKey="id"
                bordered
                style={{ backgroundColor: 'white' }}
            />

            <Modal
                title="Add New Sales Person"
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
                            name="sales_id"
                            label="Sales ID"
                            rules={[{ required: true, message: 'Please enter Sales ID' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="sales_person"
                            label="Sales Person"
                            rules={[{ required: true, message: 'Please enter Sales Person name' }]}
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
                            name="reporting_manager"
                            label="Reporting Manager"
                            rules={[{ required: true, message: 'Please enter Reporting Manager' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="region"
                            label="Region"
                            rules={[{ required: true, message: 'Please select Region' }]}
                        >
                            <Select>
                                <Option value="north">North</Option>
                                <Option value="south">South</Option>
                                <Option value="east">East</Option>
                                <Option value="west">West</Option>
                            </Select>
                        </Form.Item>
                    </div>

                    <div style={{ textAlign: 'right', marginTop: '24px' }}>
                        <Button onClick={() => setIsModalVisible(false)} style={{ marginRight: 8 }}>
                            Cancel
                        </Button>
                        <Button type="primary" htmlType="submit">
                            Add Sales
                        </Button>
                    </div>
                </Form>
            </Modal>

            <Modal
                title="Edit Sales Person"
                open={isEditModalVisible}
                onCancel={handleEditCancel}
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
                            name="sales_id"
                            label="Sales ID"
                            rules={[{ required: true, message: 'Please enter Sales ID' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="sales_person"
                            label="Sales Person"
                            rules={[{ required: true, message: 'Please enter Sales Person name' }]}
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
                            name="reporting_manager"
                            label="Reporting Manager"
                            rules={[{ required: true, message: 'Please enter Reporting Manager' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="region"
                            label="Region"
                            rules={[{ required: true, message: 'Please select Region' }]}
                        >
                            <Select>
                                <Option value="north">North</Option>
                                <Option value="south">South</Option>
                                <Option value="east">East</Option>
                                <Option value="west">West</Option>
                            </Select>
                        </Form.Item>
                    </div>

                    <div style={{ textAlign: 'right', marginTop: '24px' }}>
                        <Button onClick={handleEditCancel} style={{ marginRight: 8 }}>
                            Cancel
                        </Button>
                        <Button type="primary" htmlType="submit" loading={loading}>
                            Update Sales
                        </Button>
                    </div>
                </Form>
            </Modal>
        </div>
    );
};

export default Sales; 