import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';

function PartnerResponseSuccess() {
  const handleClose = () => {
    window.close();
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
      <Paper style={{ padding: 32, textAlign: 'center' }} elevation={3}>
        <Typography variant="h5" gutterBottom>Success</Typography>
        <Typography variant="body1" gutterBottom>
          Your response has been saved successfully and file has been successfully downloaded. <br />
          Now you can close the window.
        </Typography>
        <Button variant="contained" color="primary" onClick={handleClose} sx={{ mt: 2 }}>
          Close
        </Button>
      </Paper>
    </Box>
  );
}

export default PartnerResponseSuccess; 