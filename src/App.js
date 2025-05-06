import React from 'react';
import { Layout, Menu } from 'antd';
import {
    HomeOutlined,
    FileOutlined,
    TeamOutlined,
    UserOutlined,
    CheckCircleOutlined,
    DollarOutlined
} from '@ant-design/icons';
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import Home from './components/Home';
import Partners from './components/Partners/Partners';
import './App.css';

const { Content, Sider } = Layout;

function App() {
    const location = useLocation();

    const menuItems = [
        {
            key: '/',
            icon: <HomeOutlined />,
            label: <Link to="/">Home</Link>,
        },
        {
            key: '/bids',
            icon: <FileOutlined />,
            label: <Link to="/bids">Bids</Link>,
        },
        {
            key: '/infield',
            icon: <TeamOutlined />,
            label: <Link to="/infield">InField</Link>,
        },
        {
            key: '/closure',
            icon: <CheckCircleOutlined />,
            label: <Link to="/closure">Closure</Link>,
        },
        {
            key: '/ready-for-invoice',
            icon: <DollarOutlined />,
            label: <Link to="/ready-for-invoice">Ready for Invoice</Link>,
        },
        {
            key: '/accrual',
            icon: <FileOutlined />,
            label: <Link to="/accrual">Accrual</Link>,
        },
        {
            key: '/all-users',
            icon: <UserOutlined />,
            label: <Link to="/all-users">All Users</Link>,
        },
        {
            key: '/partners',
            icon: <TeamOutlined />,
            label: <Link to="/partners">Partners</Link>,
        },
    ];

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <Sider
                theme="light"
                style={{
                    overflow: 'auto',
                    height: '100vh',
                    position: 'fixed',
                    left: 0,
                    top: 0,
                    bottom: 0,
                }}
            >
                <div className="logo">SmartProcure</div>
                <Menu
                    theme="light"
                    selectedKeys={[location.pathname]}
                    mode="inline"
                    items={menuItems}
                    defaultSelectedKeys={['/']}
                />
            </Sider>
            <Layout style={{ marginLeft: 200 }}>
                <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/bids" element={<div>Bids Page</div>} />
                        <Route path="/infield" element={<div>InField Page</div>} />
                        <Route path="/closure" element={<div>Closure Page</div>} />
                        <Route path="/ready-for-invoice" element={<div>Ready for Invoice Page</div>} />
                        <Route path="/accrual" element={<div>Accrual Page</div>} />
                        <Route path="/all-users" element={<div>All Users Page</div>} />
                        <Route path="/partners" element={<Partners />} />
                    </Routes>
                </Content>
            </Layout>
        </Layout>
    );
}

export default App; 