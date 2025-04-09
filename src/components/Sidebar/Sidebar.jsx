import ReceiptIcon from '@mui/icons-material/Receipt';

function Sidebar() {
  return (
    <Box sx={{ /* existing styles */ }}>
      <List>
        {/* ... existing menu items ... */}
        
        <ListItem 
          button 
          component={Link} 
          to="/invoice"
          sx={{
            color: 'white',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)'
            }
          }}
        >
          <ListItemIcon>
            <ReceiptIcon sx={{ color: 'white' }} />
          </ListItemIcon>
          <ListItemText primary="Ready for Invoice" />
        </ListItem>
      </List>
    </Box>
  );
}

export default Sidebar; 