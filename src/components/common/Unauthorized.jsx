import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const Unauthorized = () => {
    const navigate = useNavigate();

    return (
        <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h4" gutterBottom>
                Unauthorized Access
            </Typography>
            <Typography variant="body1" sx={{ mb: 3 }}>
                You don't have permission to access this page.
            </Typography>
            <Button variant="contained" onClick={() => navigate('/')}>
                Go to Dashboard
            </Button>
        </Box>
    );
};

export default Unauthorized; 