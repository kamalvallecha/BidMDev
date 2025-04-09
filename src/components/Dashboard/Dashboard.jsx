import React, { useState, useEffect } from 'react';
import { Card, Row, Col, message, Spin } from 'antd';
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
            Completed: 0
        }
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
            <Row style={{ marginTop: '20px' }}>
                <Col span={24}>
                    <Card title="Bids by Status">
                        <PieChart data={data.bids_by_status} />
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default Dashboard; 