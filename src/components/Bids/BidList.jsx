import { useState, useEffect } from 'react';
import { 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Button,
  TextField,
  IconButton,
  Typography,
  Stack
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import axios from '../../api/axios';
import './Bids.css';
import PONumberDialog from './PONumberDialog';

function BidList() {
  const [bids, setBids] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [poDialogOpen, setPoDialogOpen] = useState(false);
  const [selectedBidId, setSelectedBidId] = useState(null);

  useEffect(() => {
    fetchBids();
  }, []);

  const fetchBids = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/bids');
      setBids(response.data);
    } catch (error) {
      console.error('Error fetching bids:', error);
    } finally {
      setLoading(false);
    }
  };

  // Add this to see if bids are updating in state
  useEffect(() => {
    console.log('Current bids:', bids);
  }, [bids]);

  const handleAddBid = () => {
    navigate('/bids/new');
  };

  const handleEdit = (bid) => {
    navigate(`/bids/edit/${bid.id}`);
  };

  const handleDelete = async (bidId) => {
    if (window.confirm('Are you sure you want to delete this bid?')) {
      try {
        await axios.delete(`/api/bids/${bidId}`);
        fetchBids(); // Refresh the list
      } catch (error) {
        console.error('Error deleting bid:', error);
      }
    }
  };

  const handleMoveToInField = (bidId) => {
    setSelectedBidId(bidId);
    setPoDialogOpen(true);
  };

  const handlePoSubmit = async (poNumber) => {
    try {
      // First save PO number
      await axios.post(`/api/bids/${selectedBidId}/po`, {
        status: 'infield',
        po_number: poNumber
      });

      // Then update status to infield using POST instead of PUT
      await axios.post(`/api/bids/${selectedBidId}/status`, {
        status: 'infield'
      });

      setPoDialogOpen(false);
      fetchBids();
      navigate('/infield');
    } catch (error) {
      console.error('Error moving bid to infield:', error);
      alert('Failed to move bid to infield status');
    }
  };

  const filteredBids = bids.filter(bid => 
    bid.bid_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
    bid.study_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    bid.client_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const renderActions = (bid) => {
    const isMoveable = bid.status === 'draft'; // Only enable move button for draft status

    return (
      <Stack direction="row" spacing={1}>
        <IconButton 
          color="primary" 
          onClick={() => handleEdit(bid)}
        >
          <EditIcon />
        </IconButton>
        <IconButton 
          color="error" 
          onClick={() => handleDelete(bid.id)}
        >
          <DeleteIcon />
        </IconButton>
        <IconButton 
          color="primary"
          onClick={() => handleMoveToInField(bid.id)}
          disabled={!isMoveable}  // Disable if not in draft status
          sx={{ 
            opacity: isMoveable ? 1 : 0.5,  // Visual feedback for disabled state
            '&.Mui-disabled': {
              color: 'grey.400'  // Light grey when disabled
            }
          }}
        >
          <PlayArrowIcon />
        </IconButton>
      </Stack>
    );
  };

  return (
    <>
      <div className="bid-list-container">
        <div className="bid-list-header">
          <Typography variant="h5">Bid Management</Typography>
          <div className="bid-list-actions">
            <TextField
              size="small"
              placeholder="Search bids..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-field"
            />
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleAddBid}
            >
              ADD BID
            </Button>
          </div>
        </div>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow className="table-header">
                <TableCell>Bid Number</TableCell>
                <TableCell>Study Name</TableCell>
                <TableCell>Client</TableCell>
                <TableCell>Methodology</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">Loading...</TableCell>
                </TableRow>
              ) : filteredBids.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">No bids found</TableCell>
                </TableRow>
              ) : (
                filteredBids.map((bid) => (
                  <TableRow key={bid.id}>
                    <TableCell>{bid.bid_number}</TableCell>
                    <TableCell>{bid.study_name}</TableCell>
                    <TableCell>{bid.client_name}</TableCell>
                    <TableCell>{bid.methodology}</TableCell>
                    <TableCell>{bid.status}</TableCell>
                    <TableCell>{renderActions(bid)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </div>
      <PONumberDialog
        open={poDialogOpen}
        onClose={() => setPoDialogOpen(false)}
        onSubmit={handlePoSubmit}
      />
    </>
  );
}

export default BidList; 