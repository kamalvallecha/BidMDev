import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Input, Form, Select, message } from 'antd';
import config from '../../config';
import './Users.css';

const { Option } = Select;

const Users = () => {
    const [users, setUsers] = useState([]);
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [isEditModalVisible, setIsEditModalVisible] = useState(false);
    const [editingUser, setEditingUser] = useState(null);
    const [searchText, setSearchText] = useState('');
    const [form] = Form.useForm();
    const [editForm] = Form.useForm();

    useEffect(() => {
        fetchUsers();
    }, []);

    const fetchUsers = async () => {
        try {
            const response = await fetch(`${config.API_URL}/api/users`);
            const data = await response.json();
            setUsers(data);
        } catch (error) {
            console.error('Error fetching users:', error);
            message.error('Failed to fetch users');
        }
    };

    const handleSubmit = async (values) => {
        try {
            const response = await fetch(`${config.API_URL}/api/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(values)
            });

            if (!response.ok) {
                throw new Error('Failed to create user');
            }

            await fetchUsers();
            setIsModalVisible(false);
            form.resetFields();
            message.success('User created successfully');
        } catch (error) {
            console.error('Error creating user:', error);
            message.error('Failed to create user');
        }
    };

    const handleEdit = (record) => {
        setEditingUser(record);
        editForm.setFieldsValue({
            employee_id: record.employee_id,
            name: record.name,
            email: record.email,
            role: record.role,
            team: record.team
        });
        setIsEditModalVisible(true);
    };

    const handleEditSubmit = async (values) => {
        try {
            const response = await fetch(`${config.API_URL}/api/users/${editingUser.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(values)
            });

            if (!response.ok) {
                throw new Error('Failed to update user');
            }

            await fetchUsers();
            setIsEditModalVisible(false);
            editForm.resetFields();
            setEditingUser(null);
            message.success('User updated successfully');
        } catch (error) {
            console.error('Error updating user:', error);
            message.error('Failed to update user');
        }
    };

    const handleDelete = async (id) => {
        try {
            const response = await fetch(`${config.API_URL}/api/users/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error('Failed to delete user');
            }

            await fetchUsers();
            message.success('User deleted successfully');
        } catch (error) {
            console.error('Error deleting user:', error);
            message.error('Failed to delete user');
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
            title: 'Employee ID',
            dataIndex: 'employee_id',
            key: 'employee_id',
            width: '15%',
        },
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            width: '15%',
        },
        {
            title: 'Email',
            dataIndex: 'email',
            key: 'email',
            width: '20%',
        },
        {
            title: 'Role',
            dataIndex: 'role',
            key: 'role',
            width: '10%',
        },
        {
            title: 'Team',
            dataIndex: 'team',
            key: 'team',
            width: '10%',
        },
        {
            title: 'Created At',
            dataIndex: 'created_at',
            key: 'created_at',
            width: '12.5%',
        },
        {
            title: 'Updated At',
            dataIndex: 'updated_at',
            key: 'updated_at',
            width: '12.5%',
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

    const filteredUsers = users.filter(user => 
        user.name?.toLowerCase().includes(searchText.toLowerCase()) ||
        user.email?.toLowerCase().includes(searchText.toLowerCase()) ||
        user.employee_id?.toLowerCase().includes(searchText.toLowerCase()) ||
        user.team?.toLowerCase().includes(searchText.toLowerCase())
    );

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center', 
                marginBottom: '16px' 
            }}>
                <h2 style={{ margin: 0 }}>User List</h2>
                <div style={{ display: 'flex', gap: '16px' }}>
                    <Input.Search
                        placeholder="Search by name, email, employee ID or team..."
                        style={{ width: 300 }}
                        onChange={(e) => setSearchText(e.target.value)}
                    />
                    <Button type="primary" onClick={() => setIsModalVisible(true)}>
                        ADD USER
                    </Button>
                </div>
            </div>

            <Table
                columns={columns}
                dataSource={filteredUsers}
                rowKey="id"
                bordered
                style={{ backgroundColor: 'white' }}
            />

            <Modal
                title="Add New User"
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
                            name="employee_id"
                            label="Employee ID"
                            rules={[{ required: true, message: 'Please enter Employee ID' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="name"
                            label="Name"
                            rules={[{ required: true, message: 'Please enter Name' }]}
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
                            name="password"
                            label="Password"
                            rules={[{ required: true, message: 'Please enter Password' }]}
                        >
                            <Input.Password />
                        </Form.Item>

                        <Form.Item
                            name="role"
                            label="Role"
                            rules={[{ required: true, message: 'Please select Role' }]}
                        >
                            <Select>
                                <Option value="admin">Admin</Option>
                                <Option value="PM">PM</Option>
                                <Option value="VM">VM</Option>
                            </Select>
                        </Form.Item>

                        <Form.Item
                            name="team"
                            label="Team"
                            rules={[{ required: true, message: 'Please select Team' }]}
                        >
                            <Select>
                                <Option value="POD 1">POD 1</Option>
                                <Option value="POD 2">POD 2</Option>
                                <Option value="POD 3">POD 3</Option>
                                <Option value="POD 4">POD 4</Option>
                                <Option value="Operations">Operations</Option>
                            </Select>
                        </Form.Item>
                    </div>

                    <div style={{ textAlign: 'right', marginTop: '24px' }}>
                        <Button onClick={() => setIsModalVisible(false)} style={{ marginRight: 8 }}>
                            Cancel
                        </Button>
                        <Button type="primary" htmlType="submit">
                            Add User
                        </Button>
                    </div>
                </Form>
            </Modal>

            <Modal
                title="Edit User"
                open={isEditModalVisible}
                onCancel={() => {
                    setIsEditModalVisible(false);
                    setEditingUser(null);
                    editForm.resetFields();
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
                            name="employee_id"
                            label="Employee ID"
                            rules={[{ required: true, message: 'Please enter Employee ID' }]}
                        >
                            <Input />
                        </Form.Item>

                        <Form.Item
                            name="name"
                            label="Name"
                            rules={[{ required: true, message: 'Please enter Name' }]}
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
                            name="role"
                            label="Role"
                            rules={[{ required: true, message: 'Please select Role' }]}
                        >
                            <Select>
                                <Option value="admin">Admin</Option>
                                <Option value="PM">PM</Option>
                                <Option value="VM">VM</Option>
                            </Select>
                        </Form.Item>

                        <Form.Item
                            name="team"
                            label="Team"
                            rules={[{ required: true, message: 'Please select Team' }]}
                        >
                            <Select>
                                <Option value="POD 1">POD 1</Option>
                                <Option value="POD 2">POD 2</Option>
                                <Option value="POD 3">POD 3</Option>
                                <Option value="POD 4">POD 4</Option>
                                <Option value="Operations">Operations</Option>
                            </Select>
                        </Form.Item>
                    </div>

                    <div style={{ textAlign: 'right', marginTop: '24px' }}>
                        <Button onClick={() => {
                            setIsEditModalVisible(false);
                            setEditingUser(null);
                            editForm.resetFields();
                        }} style={{ marginRight: 8 }}>
                            Cancel
                        </Button>
                        <Button type="primary" htmlType="submit">
                            Update User
                        </Button>
                    </div>
                </Form>
            </Modal>
        </div>
    );
};

export default Users; 