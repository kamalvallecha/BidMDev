import ReceiptIcon from '@mui/icons-material/Receipt';
import DescriptionIcon from '@mui/icons-material/Description';

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

        <ListItem 
          button 
          component={Link} 
          to="/proposals"
          sx={{
            color: 'white',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)'
            }
          }}
        >
          <ListItemIcon>
            <DescriptionIcon sx={{ color: 'white' }} />
          </ListItemIcon>
          <ListItemText primary="Proposal" />
        </ListItem>
      </List>
    </Box>
  );
}

export default Sidebar; 