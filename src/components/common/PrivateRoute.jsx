
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const PrivateRoute = ({ children, requiredPermissions = [] }) => {
    const { user, isAuthenticated } = useAuth();
    const isAdmin = user?.role === 'admin';

    if (!isAuthenticated) {
        return <Navigate to="/login" />;
    }

    // If user is admin, allow access without checking permissions
    if (isAdmin) {
        return children;
    }

    // For non-admin users, check specific permissions based on role
    if (requiredPermissions.length > 0) {
        const rolePermissions = {
            'admin': [
                'can_view_all', 'can_view_bids', 'can_view_infield', 
                'can_view_closure', 'can_view_invoice', 'can_view_users', 
                'can_edit_all'
            ],
            'PM': [
                'can_view_infield', 'can_view_closure', 
                'can_edit_infield', 'can_edit_closure'
            ],
            'VM': [
                'can_view_bids', 'can_edit_bids'
            ]
        };

        const userRole = user?.role;
        const userPermissions = rolePermissions[userRole] || [];
        const hasRequiredPermissions = requiredPermissions.every(
            permission => userPermissions.includes(permission)
        );

        if (!hasRequiredPermissions) {
            return <Navigate to="/unauthorized" />;
        }
    }

    return children;
};

export default PrivateRoute;
