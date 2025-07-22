import React, { useState, useEffect } from 'react';
import { Card, Row, Col, message, Spin, Table } from 'antd';
import { UserOutlined, CheckCircleOutlined, DollarOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { PieChart } from './PieChart';
import './Dashboard.css';
import axios from '../../api/axios';

const Dashboard = () => {
    const [data, setData] = useState({
        total_bids: 0,
        active_bids: 0,
        total_savings: 0,
        avg_turnaround_time: 0,
        bids_by_status: {
            Draft: 0,
            "Partner Response": 0,
            "In Field": 0,
            Closure: 0,
            "Ready to Invoice": 0,
            Completed: 0,
            Rejected: 0
        },
        client_summary: []
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                setLoading(true);
                console.log('Fetching dashboard data...');
                const response = await axios.get('/api/dashboard');

                console.log('Received dashboard data:', response.data);
                setData(response.data);
            } catch (error) {
                console.error('Error fetching dashboard data:', error);
                message.error('Failed to load dashboard data');
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    const columns = [
        {
            title: 'Client Name',
            dataIndex: 'client_name',
            key: 'client_name',
            width: '15%',
            sorter: (a, b) => a.client_name.localeCompare(b.client_name),
        },
        {
            title: 'Total Bids',
            dataIndex: 'total_bids',
            key: 'total_bids',
            align: 'center',
            width: '10%',
            sorter: (a, b) => a.total_bids - b.total_bids,
        },
        {
            title: 'In Field',
            dataIndex: 'in_field',
            key: 'in_field',
            align: 'center',
            width: '10%',
            sorter: (a, b) => a.in_field - b.in_field,
        },
        {
            title: 'Closed',
            dataIndex: 'closed',
            key: 'closed',
            align: 'center',
            width: '10%',
            sorter: (a, b) => a.closed - b.closed,
        },
        {
            title: 'Invoiced',
            dataIndex: 'invoiced',
            key: 'invoiced',
            align: 'center',
            width: '10%',
            sorter: (a, b) => a.invoiced - b.invoiced,
        },
        {
            title: 'Rejected',
            dataIndex: 'rejected',
            key: 'rejected',
            align: 'center',
            width: '10%',
            sorter: (a, b) => a.rejected - b.rejected,
        },
        {
            title: 'Total Amount',
            dataIndex: 'total_amount',
            key: 'total_amount',
            align: 'center',
            width: '15%',
            sorter: (a, b) => a.total_amount - b.total_amount,
            render: (amount) => `$${amount?.toLocaleString() || 0}`,
        },
        {
            title: 'Conversion Rate',
            dataIndex: 'conversion_rate',
            key: 'conversion_rate',
            align: 'center',
            width: '15%',
            sorter: (a, b) => a.conversion_rate - b.conversion_rate,
            render: (rate) => `${rate || 0}%`,
        }
    ];

    if (loading) {
        return (
            <div className="loading-container">
                <Spin size="large" tip="Loading dashboard..." />
            </div>
        );
    }

    return (
        <div className="dashboard-container">
            <h1>Dashboard</h1>

            {/* Summary Cards */}
            <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} lg={6}>
                    <Card className="dashboard-card">
                        <div className="card-content">
                            <UserOutlined className="card-icon" />
                            <div className="card-info">
                                <h2>{data.total_bids}</h2>
                                <p>Total Bids</p>
                            </div>
                        </div>
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card className="dashboard-card">
                        <div className="card-content">
                            <CheckCircleOutlined className="card-icon" />
                            <div className="card-info">
                                <h2>{data.active_bids}</h2>
                                <p>Active Bids</p>
                            </div>
                        </div>
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card className="dashboard-card">
                        <div className="card-content">
                            <DollarOutlined className="card-icon" />
                            <div className="card-info">
                                <h2>${data.total_savings.toLocaleString()}</h2>
                                <p>Total Savings</p>
                            </div>
                        </div>
                    </Card>
                </Col>
                <Col xs={24} sm={12} lg={6}>
                    <Card className="dashboard-card">
                        <div className="card-content">
                            <ClockCircleOutlined className="card-icon" />
                            <div className="card-info">
                                <h2>{data.avg_turnaround_time} days</h2>
                                <p>Avg. Turnaround Time</p>
                            </div>
                        </div>
                    </Card>
                </Col>
            </Row>

            {/* Pie Chart and Team Summary */}
            <Row gutter={[16, 16]} style={{ marginTop: '20px' }}>
                <Col xs={24} lg={12}>
                    <Card title="Bids by Status">
                        <PieChart data={data.bids_by_status} />
                    </Card>
                </Col>
                <Col xs={24} lg={12}>
                    <Card title="Team Summary">
                        <Table
                            columns={[
                                {
                                    title: 'Team',
                                    dataIndex: 'team',
                                    key: 'team',
                                    width: '25%',
                                },
                                {
                                    title: 'No. of Bids',
                                    dataIndex: 'total_bids',
                                    key: 'total_bids',
                                    align: 'center',
                                    width: '25%',
                                },
                                {
                                    title: 'Bids In Field',
                                    dataIndex: 'bids_in_field',
                                    key: 'bids_in_field',
                                    align: 'center',
                                    width: '25%',
                                },
                                {
                                    title: 'Bids Closed',
                                    dataIndex: 'bids_closed',
                                    key: 'bids_closed',
                                    align: 'center',
                                    width: '25%',
                                },
                                {
                                    title: 'Bid Invoiced',
                                    dataIndex: 'bid_invoiced',
                                    key: 'bid_invoiced',
                                    align: 'center',
                                    width: '25%',
                                }
                            ]}
                            dataSource={data.team_summary || []}
                            pagination={false}
                            size="small"
                            rowKey="team"
                        />
                    </Card>
                </Col>
            </Row>

            {/* Client Summary Table */}
            <Row gutter={[16, 16]} style={{ marginTop: '20px' }}>
                <Col xs={24}>
                    <Card title="Client Summary">
                        <Table
                            columns={columns}
                            dataSource={data.client_summary}
                            pagination={false}
                            scroll={{ x: 1200 }}
                            size="middle"
                            rowKey="client_name"
                        />
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default Dashboard;