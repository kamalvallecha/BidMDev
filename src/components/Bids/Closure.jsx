import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Typography,
  TextField,
  Box,
  Stack,
  IconButton,
  Tooltip
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import EditIcon from '@mui/icons-material/Edit';
import ReplayIcon from '@mui/icons-material/Replay';
import ReceiptIcon from '@mui/icons-material/Receipt';
import './Bids.css';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';

function Closure() {
  const navigate = useNavigate();
  const [bids, setBids] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const { user } = useAuth();
  const canEdit = user?.role === 'admin' || user?.permissions?.can_edit_closure;

  useEffect(() => {
    fetchClosureBids();
  }, []);

  const fetchClosureBids = async () => {
    try {
      setLoading(true);
      console.log('Fetching closure bids...');
      const response = await axios.get('/api/bids/closure');
      console.log('Closure bids response:', response.data);
      setBids(response.data || []);
    } catch (error) {
      console.error('Error fetching closure bids:', error);
      setError('Failed to fetch closure bids');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (bidId) => {
    navigate(`/closure/edit/${bidId}`);
  };

  const handleApply = () => {
    // Will implement filter functionality later
  };

  const handleReset = () => {
    setStartDate(null);
    setEndDate(null);
    setSearchTerm('');
    fetchClosureBids();
  };

  const handleBackToInField = async (bidId) => {
    try {
      await axios.post(`/api/bids/${bidId}/status`, {
        status: 'infield'
      });
      fetchClosureBids(); // Refresh the list after status update
    } catch (error) {
      console.error('Error moving bid back to infield:', error);
      alert('Error moving bid back to infield. Please try again.');
    }
  };

  const handleMoveToInvoice = async (bidId) => {
    try {
      // Update bid status to ready_for_invoice using POST
      await axios.post(`/api/bids/${bidId}/status`, {
        status: 'ready_for_invoice'
      });
      
      // Show success message
      alert('Bid moved to Ready for Invoice successfully');
      
      // Navigate to invoice page
      navigate('/invoice');
      
      // Refresh the bids list
      fetchClosureBids();
      
    } catch (error) {
      console.error('Error moving bid to ready for invoice:', error);
      alert('Failed to move bid to ready for invoice. Please try again.');
    }
  };

  return (
    <div className="bids-container">
      <Typography variant="h5">Closure Bids</Typography>

      <Box sx={{ display: 'flex', alignItems: 'center', my: 3 }}>
        <TextField
          size="small"
          placeholder="Search bids..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ width: 200 }}
        />
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow className="table-header">
              <TableCell>PO Number</TableCell>
              <TableCell>Bid Number</TableCell>
              <TableCell>Study Name</TableCell>
              <TableCell>Client</TableCell>
              <TableCell>Total N-Delivered</TableCell>
              <TableCell>Quality Rejects</TableCell>
              <TableCell>Avg LOI (mins)</TableCell>
              <TableCell>Avg IR (%)</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={11} align="center">Loading...</TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={11} align="center" sx={{ color: 'error.main' }}>
                  {error}
                </TableCell>
              </TableRow>
            ) : bids.length === 0 ? (
              <TableRow>
                <TableCell colSpan={11} align="center">No closure bids found</TableCell>
              </TableRow>
            ) : (
              bids.map((bid) => (
                <TableRow key={bid.id}>
                  <TableCell>{bid.po_number}</TableCell>
                  <TableCell>{bid.bid_number}</TableCell>
                  <TableCell>{bid.study_name}</TableCell>
                  <TableCell>{bid.client_name}</TableCell>
                  <TableCell>{bid.total_delivered}</TableCell>
                  <TableCell>{bid.quality_rejects}</TableCell>
                  <TableCell>{Number(bid.avg_loi).toFixed(2)}</TableCell>
                  <TableCell>{Number(bid.avg_ir).toFixed(2)}</TableCell>
                  <TableCell>{bid.status}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {canEdit && (
                        <Tooltip title="Edit">
                          <IconButton onClick={() => handleEdit(bid.id)}>
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      {canEdit && (
                        <Tooltip title="Back to InField">
                          <IconButton 
                            onClick={() => {
                              if (window.confirm('Move this bid back to InField status?')) {
                                handleBackToInField(bid.id);
                              }
                            }}
                            color="secondary"
                          >
                            <ReplayIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      {canEdit && (
                        <Tooltip title="Move to Ready for Invoice">
                          <IconButton
                            onClick={() => handleMoveToInvoice(bid.id)}
                            size="small"
                            sx={{ color: 'purple' }}
                          >
                            <ReceiptIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}

export default Closure; 