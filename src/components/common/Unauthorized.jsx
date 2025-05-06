import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Unauthorized = () => {
    const navigate = useNavigate();
    const { user } = useAuth();

    const getRoleSpecificMessage = () => {
        if (!user || !user.role) return "You don't have permission to access this page.";
        
        return `Your role is ${user.role} and you don't have permission to access this page. Kindly check with Admin.`;
    };

    return (
        <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h4" gutterBottom sx={{ color: '#d32f2f' }}>
                Unauthorized Access
            </Typography>
            <Typography variant="body1" sx={{ mb: 3, color: '#666' }}>
                {getRoleSpecificMessage()}
            </Typography>
            <Button 
                variant="contained" 
                onClick={() => navigate('/')}
                sx={{
                    backgroundColor: '#1976d2',
                    '&:hover': {
                        backgroundColor: '#1565c0'
                    }
                }}
            >
                Go to Dashboard
            </Button>
        </Box>
    );
};

export default Unauthorized; 