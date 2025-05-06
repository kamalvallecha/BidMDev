import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Input, Form, Select, message } from 'antd';
import axios from '../../api/axios';
import './VMs.css';

const { Option } = Select;

const VMs = () => {
    const [vms, setVMs] = useState([]);
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [isEditModalVisible, setIsEditModalVisible] = useState(false);
    const [currentVM, setCurrentVM] = useState(null);
    const [searchText, setSearchText] = useState('');
    const [form] = Form.useForm();
    const [editForm] = Form.useForm();
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchVMs();
    }, []);

    const fetchVMs = async () => {
        try {
            const response = await axios.get('/api/vms');
            setVMs(response.data);
        } catch (error) {
            console.error('Error fetching VMs:', error);
            message.error('Failed to fetch VMs');
        }
    };

    const handleSubmit = async (values) => {
        try {
            await axios.post('/api/vms', values);
            fetchVMs();
            setIsModalVisible(false);
            form.resetFields();
            message.success('VM created successfully');
        } catch (error) {
            console.error('Error creating VM:', error);
            message.error('Failed to create VM');
        }
    };

    const handleEdit = (record) => {
        setCurrentVM(record);
        editForm.setFieldsValue({
            vm_id: record.vm_id,
            vm_name: record.vm_name,
            contact_person: record.contact_person,
            reporting_manager: record.reporting_manager,
            team: record.team
        });
        setIsEditModalVisible(true);
    };

    const handleEditSubmit = async (values) => {
        if (!currentVM) return;

        try {
            setLoading(true);
            const response = await axios.put(`/api/vms/${currentVM.id}`, values);
            if (response.status === 200) {
                message.success('VM updated successfully');
                fetchVMs();
                setIsEditModalVisible(false);
                setCurrentVM(null);
            }
        } catch (error) {
            console.error('Error updating VM:', error);
            message.error('Failed to update VM: ' + (error.response?.data?.error || error.message));
        } finally {
            setLoading(false);
        }
    };

    const handleEditCancel = () => {
        setIsEditModalVisible(false);
        setCurrentVM(null);
    };

    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this VM?')) {
            try {
                await axios.delete(`/api/vms/${id}`);
                fetchVMs();
                message.success('VM deleted successfully');
            } catch (error) {
                console.error('Error deleting VM:', error);
                message.error('Failed to delete VM');
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
            title: 'VM ID',
            dataIndex: 'vm_id',
            key: 'vm_id',
            width: '10%',
        },
        {
            title: 'VM Name',
            dataIndex: 'vm_name',
            key: 'vm_name',
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
            title: 'Team',
            dataIndex: 'team',
            key: 'team',
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

    const filteredVMs = vms.filter(vm => 
        vm.vm_name?.toLowerCase().includes(searchText.toLowerCase()) ||
        vm.vm_id?.toLowerCase().includes(searchText.toLowerCase())
    );

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                marginBottom: '16px' 
            }}>
                <h2 style={{ margin: 0 }}>VM List</h2>
                <div style={{ display: 'flex', gap: '16px' }}>
                    <Input.Search
                        placeholder="Search VMs..."
                        style={{ width: 300 }}
                        onChange={(e) => setSearchText(e.target.value)}
                    />
                    <Button type="primary" onClick={() => setIsModalVisible(true)}>
                        ADD VM
                    </Button>
                </div>
            </div>

            <Table
                columns={columns}
                dataSource={filteredVMs}
                rowKey="id"
                bordered
                style={{ backgroundColor: 'white' }}
            />

            <Modal
                title="Add New VM"
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
                    <Form.Item
                        name="vm_id"
                        label="VM ID"
                        rules={[{ required: true, message: 'Please enter VM ID' }]}
                    >
                        <Input />
                    </Form.Item>

                    <Form.Item
                        name="vm_name"
                        label="VM Name"
                        rules={[{ required: true, message: 'Please enter VM name' }]}
                    >
                        <Input />
                    </Form.Item>

                    <Form.Item
                        name="contact_person"
                        label="Contact Person"
                        rules={[{ required: true, message: 'Please enter contact person' }]}
                    >
                        <Input />
                    </Form.Item>

                    <Form.Item
                        name="reporting_manager"
                        label="Reporting Manager"
                        rules={[{ required: true, message: 'Please enter reporting manager' }]}
                    >
                        <Input />
                    </Form.Item>

                    <Form.Item
                        name="team"
                        label="Team"
                        rules={[{ required: true, message: 'Please select team' }]}
                    >
                        <Select>
                            <Option value="pod1">POD 1</Option>
                            <Option value="pod2">POD 2</Option>
                            <Option value="pod3">POD 3</Option>
                            <Option value="pod4">POD 4</Option>
                            <Option value="operations">Operations</Option>
                        </Select>
                    </Form.Item>

                    <div style={{ textAlign: 'right' }}>
                        <Button onClick={() => setIsModalVisible(false)} style={{ marginRight: 8 }}>
                            Cancel
                        </Button>
                        <Button type="primary" htmlType="submit">
                            Add VM
                        </Button>
                    </div>
                </Form>
            </Modal>

            <Modal
                title="Edit VM"
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
                    <Form.Item
                        name="vm_id"
                        label="VM ID"
                        rules={[{ required: true, message: 'Please enter VM ID' }]}
                    >
                        <Input />
                    </Form.Item>

                    <Form.Item
                        name="vm_name"
                        label="VM Name"
                        rules={[{ required: true, message: 'Please enter VM name' }]}
                    >
                        <Input />
                    </Form.Item>

                    <Form.Item
                        name="contact_person"
                        label="Contact Person"
                        rules={[{ required: true, message: 'Please enter contact person' }]}
                    >
                        <Input />
                    </Form.Item>

                    <Form.Item
                        name="reporting_manager"
                        label="Reporting Manager"
                        rules={[{ required: true, message: 'Please enter reporting manager' }]}
                    >
                        <Input />
                    </Form.Item>

                    <Form.Item
                        name="team"
                        label="Team"
                        rules={[{ required: true, message: 'Please select team' }]}
                    >
                        <Select>
                            <Option value="pod1">POD 1</Option>
                            <Option value="pod2">POD 2</Option>
                            <Option value="pod3">POD 3</Option>
                            <Option value="pod4">POD 4</Option>
                            <Option value="operations">Operations</Option>
                        </Select>
                    </Form.Item>

                    <div style={{ textAlign: 'right' }}>
                        <Button onClick={handleEditCancel} style={{ marginRight: 8 }}>
                            Cancel
                        </Button>
                        <Button type="primary" htmlType="submit" loading={loading}>
                            Update VM
                        </Button>
                    </div>
                </Form>
            </Modal>
        </div>
    );
};

export default VMs;