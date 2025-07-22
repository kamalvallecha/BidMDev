
import React, { useState, useEffect } from 'react';
import {
  IconButton,
  Badge,
  Menu,
  MenuItem,
  Typography,
  Box,
  Divider,
  Button,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip
} from '@mui/material';
import { Notifications as NotificationsIcon } from '@mui/icons-material';
import axios from '../../api/axios';
import { useAuth } from '../../contexts/AuthContext';

const NotificationBell = () => {
  const [notificationCount, setNotificationCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [anchorEl, setAnchorEl] = useState(null);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  
  const open = Boolean(anchorEl);

  // Fetch notification count
  const fetchNotificationCount = async () => {
    try {
      const response = await axios.get('/api/notifications/count');
      setNotificationCount(response.data.count || 0);
    } catch (error) {
      console.error('Error fetching notification count:', error);
    }
  };

  // Fetch detailed notifications
  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/notifications');
      setNotifications(response.data.notifications || []);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle notification click
  const handleNotificationClick = (event) => {
    setAnchorEl(event.currentTarget);
    fetchNotifications();
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  // Grant access handler
  const handleGrantAccess = async (notification) => {
    try {
      await axios.post(`/api/bids/${notification.bid_id}/access-requests/${notification.id}/grant`);
      // Refresh notifications
      fetchNotifications();
      fetchNotificationCount();
    } catch (error) {
      console.error('Error granting access:', error);
    }
  };

  // Deny access handler
  const handleDenyAccess = async (notification) => {
    try {
      await axios.post(`/api/bids/${notification.bid_id}/access-requests/${notification.id}/deny`);
      // Refresh notifications
      fetchNotifications();
      fetchNotificationCount();
    } catch (error) {
      console.error('Error denying access:', error);
    }
  };

  // Poll for notifications every 30 seconds
  useEffect(() => {
    if (user) {
      fetchNotificationCount();
      
      const interval = setInterval(() => {
        fetchNotificationCount();
      }, 30000); // 30 seconds

      return () => clearInterval(interval);
    }
  }, [user]);

  // Don't show for non-admin users
  if (!user || (!['admin', 'super_admin'].includes(user.role) && !user.name?.toLowerCase().includes('kamal vallecha'))) {
    return null;
  }

  return (
    <>
      <IconButton
        color="inherit"
        onClick={handleNotificationClick}
        sx={{ ml: 2 }}
      >
        <Badge badgeContent={notificationCount} color="error">
          <NotificationsIcon />
        </Badge>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            maxWidth: 400,
            maxHeight: 600,
            overflow: 'hidden',
          },
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2, borderBottom: '1px solid #eee' }}>
          <Typography variant="h6" component="div">
            Notifications
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {notificationCount} pending access requests
          </Typography>
        </Box>

        <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
          {loading ? (
            <MenuItem>
              <Typography>Loading...</Typography>
            </MenuItem>
          ) : notifications.length === 0 ? (
            <MenuItem>
              <Typography color="text.secondary">No pending notifications</Typography>
            </MenuItem>
          ) : (
            notifications.map((notification) => (
              <Paper key={notification.id} sx={{ m: 1, p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Access Request for Bid #{notification.bid_number}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {notification.study_name}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  Requested by: {notification.requester_name || 'Unknown'} ({notification.email || 'No email'})
                </Typography>
                <Typography variant="body2" gutterBottom>
                  Team: {notification.team}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {new Date(notification.requested_on).toLocaleDateString()} {new Date(notification.requested_on).toLocaleTimeString()}
                </Typography>
                
                <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                  <Button
                    size="small"
                    variant="contained"
                    color="success"
                    onClick={() => handleGrantAccess(notification)}
                  >
                    Grant
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="error"
                    onClick={() => handleDenyAccess(notification)}
                  >
                    Deny
                  </Button>
                </Box>
              </Paper>
            ))
          )}
        </Box>

        {notifications.length > 0 && (
          <Box sx={{ p: 1, borderTop: '1px solid #eee' }}>
            <Button
              fullWidth
              variant="text"
              onClick={() => {
                handleClose();
                // Navigate to bids page or refresh
                window.location.reload();
              }}
            >
              Refresh Page
            </Button>
          </Box>
        )}
      </Menu>
    </>
  );
};

export default NotificationBell;
