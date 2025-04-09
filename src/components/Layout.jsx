import React from 'react';
import { useNavigate, useLocation, Outlet, Link } from 'react-router-dom';
import { FaHome, FaUsers, FaHandshake, FaVideo, FaChartBar } from 'react-icons/fa';
import { MdDescription, MdAssignment, MdPayment } from 'react-icons/md';
import '../styles/Layout.css';  // Import the CSS
import { useAuth } from '../contexts/AuthContext';

const Layout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [openMenuId, setOpenMenuId] = React.useState(null);
  const { user } = useAuth();
  const role = user?.role;

  // Define menu items with their role-based visibility
  const menuItems = [
    {
      id: 1,
      icon: <FaHome />,
      label: 'Dashboard',
      path: '/',
      visible: true  // Always visible
    },
    {
      id: 2,
      icon: <MdDescription />,
      label: 'Bids',
      path: '/bids',
      visible: role === 'admin' || role === 'VM'
    },
    {
      id: 3,
      icon: <FaUsers />,
      label: 'InField',
      path: '/infield',
      visible: role === 'admin' || role === 'PM'
    },
    {
      id: 4,
      icon: <MdAssignment />,
      label: 'Closure',
      path: '/closure',
      visible: role === 'admin' || role === 'PM'
    },
    {
      id: 5,
      icon: <MdPayment />,
      label: 'Ready for Invoice',
      path: '/invoice',
      visible: role === 'admin'
    },
    {
      id: 6,
      icon: <MdPayment />,
      label: 'Accrual',
      path: '/accrual',
      visible: role === 'admin'
    },
    {
      id: 7,
      icon: <FaUsers />,
      label: 'All Users',
      visible: role === 'admin',
      subItems: [
        { icon: <FaUsers />, label: 'Users', path: '/users' },
        { icon: <FaHandshake />, label: 'Partners', path: '/partners' },
        { icon: <FaVideo />, label: 'VMs', path: '/vms' },
        { icon: <FaChartBar />, label: 'Sales', path: '/sales' },
        { icon: <FaUsers />, label: 'Clients', path: '/clients' }
      ]
    }
  ];

  const handleLogout = () => {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  // Filter menu items based on visibility
  const visibleMenuItems = menuItems.filter(item => item.visible);

  return (
    <div className="app">
      <header className="header">
        <div className="logo">SmartProcure</div>
        <div className="user-info" onClick={handleLogout}>
          {user && user.name ? user.name : 'User'} ({user && user.role ? user.role : 'admin'})▼
        </div>
      </header>
      
      <div className="container">
        <nav className="sidebar">
          {visibleMenuItems.map((item) => (
            <div key={item.id}>
              {item.subItems ? (
                <>
                  <div 
                    className={`menu-item ${openMenuId === item.id ? 'active' : ''}`}
                    onClick={() => setOpenMenuId(openMenuId === item.id ? null : item.id)}
                  >
                    <span className="icon">{item.icon}</span>
                    <span className="label">{item.label}</span>
                    <span className="arrow">
                      {openMenuId === item.id ? '▼' : '▶'}
                    </span>
                  </div>
                  
                  {openMenuId === item.id && (
                    <div className="submenu">
                      {item.subItems.map((subItem, subIndex) => (
                        <div 
                          key={subIndex} 
                          className={`submenu-item ${isActive(subItem.path) ? 'active' : ''}`}
                          onClick={() => navigate(subItem.path)}
                        >
                          <span className="icon">{subItem.icon}</span>
                          <span className="label">{subItem.label}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div 
                  className={`menu-item ${isActive(item.path) ? 'active' : ''}`}
                  onClick={() => navigate(item.path)}
                >
                  <span className="icon">{item.icon}</span>
                  <span className="label">{item.label}</span>
                </div>
              )}
            </div>
          ))}
        </nav>
        
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout; 