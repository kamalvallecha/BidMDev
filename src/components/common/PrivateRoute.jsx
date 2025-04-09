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

    // For non-admin users, check specific permissions
    if (requiredPermissions.length > 0) {
        const hasRequiredPermissions = requiredPermissions.every(
            permission => user?.permissions?.[permission]
        );

        if (!hasRequiredPermissions) {
            return <Navigate to="/unauthorized" />;
        }
    }

    return children;
};

export default PrivateRoute; 