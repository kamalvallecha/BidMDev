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
        client_summary: [],
        team_summary: []
    });
    const [loading, setLoading] = useState(true);

    const teamColumns = [
        {
            title: 'Team',
            dataIndex: 'team',
            key: 'team',
            width: '20%',
        },
        {
            title: 'No. of Bids',
            dataIndex: 'total_bids',
            key: 'total_bids',
            align: 'right',
            width: '20%',
        },
        {
            title: 'Bids In Field',
            dataIndex: 'bids_in_field',
            key: 'bids_in_field',
            align: 'right',
            width: '20%',
        },
        {
            title: 'Bids Closed',
            dataIndex: 'bids_closed',
            key: 'bids_closed',
            align: 'right',
            width: '20%',
        },
        {
            title: 'Bid Invoiced',
            dataIndex: 'bids_invoiced',
            key: 'bids_invoiced',
            align: 'right',
            width: '20%',
        },
    ];

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                setLoading(true);
                console.log('Fetching dashboard data...');
                const response = await axios.get('/api/dashboard');
                
                console.log('Received dashboard data:', response.data);
                console.log('Team summary data:', response.data.team_summary);
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
            fixed: 'left',
        },
        {
            title: 'Total Bids',
            dataIndex: 'total_bids',
            key: 'total_bids',
            align: 'right',
            width: '10%',
        },
        {
            title: 'In Field',
            dataIndex: 'bids_in_field',
            key: 'bids_in_field',
            align: 'right',
            width: '10%',
        },
        {
            title: 'Closed',
            dataIndex: 'bid_closed',
            key: 'bid_closed',
            align: 'right',
            width: '10%',
        },
        {
            title: 'Invoiced',
            dataIndex: 'bid_invoiced',
            key: 'bid_invoiced',
            align: 'right',
            width: '10%',
        },
        {
            title: 'Rejected',
            dataIndex: 'bids_rejected',
            key: 'bids_rejected',
            align: 'right',
            width: '10%',
        },
        {
            title: 'Total Amount',
            dataIndex: 'total_amount',
            key: 'total_amount',
            align: 'right',
            width: '15%',
            render: (value) => `$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
        },
        {
            title: 'Conversion Rate',
            dataIndex: 'conversion_rate',
            key: 'conversion_rate',
            align: 'right',
            width: '15%',
            render: (value) => `${value}%`,
        },
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
                <Col xs={24} md={12}>
                    <Card title="Bids by Status">
                        <PieChart data={data.bids_by_status} />
                    </Card>
                </Col>
                <Col xs={24} md={12}>
                    <Card title="Bids by Team (POD)">
                        <Table
                            columns={teamColumns}
                            dataSource={data.team_summary && data.team_summary.length > 0 ? data.team_summary : []}
                            pagination={false}
                            size="small"
                            rowKey="team"
                            locale={{ emptyText: data.team_summary && data.team_summary.length === 0 ? 'No team data available' : 'Loading...' }}
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