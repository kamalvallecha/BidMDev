import React, { useState, useEffect } from 'react';
import { 
  Button,
  Modal,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import { useNavigate } from 'react-router-dom';
import InvoiceEdit from './InvoiceEdit';

const InvoiceBids = () => {
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedBid, setSelectedBid] = useState(null);
  const [bids, setBids] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchBids();
  }, []);

  const fetchBids = async () => {
    try {
      const response = await fetch('/api/bids/ready-for-invoice');
      const data = await response.json();
      setBids(data);
    } catch (error) {
      console.error('Error fetching bids:', error);
    }
  };

  const handleEditClick = (bidNumber) => {
    if (bidNumber) {
      navigate(`/invoice/${bidNumber}/edit`);
    }
  };

  const handleCancel = () => {
    setShowEditModal(false);
    setSelectedBid(null);
    navigate('/bids');
  };

  const handleSubmit = async (invoiceData) => {
    try {
      await fetch('/api/invoice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(invoiceData),
      });
      
      setShowEditModal(false);
      setSelectedBid(null);
      navigate('/bids');
      fetchBids();
    } catch (error) {
      console.error('Error submitting invoice:', error);
    }
  };

  return (
    <Box sx={{ p: 4 }}>
      <TableContainer component={Paper}>
        <Table>
          <TableHead sx={{ bgcolor: 'primary.main' }}>
            <TableRow>
              <TableCell sx={{ color: 'white' }}>PO Number</TableCell>
              <TableCell sx={{ color: 'white' }}>Bid Number</TableCell>
              <TableCell sx={{ color: 'white' }}>Study Name</TableCell>
              <TableCell sx={{ color: 'white' }}>Client</TableCell>
              <TableCell sx={{ color: 'white' }}>N-Delivered</TableCell>
              <TableCell sx={{ color: 'white' }}>Avg. Final LOI</TableCell>
              <TableCell sx={{ color: 'white' }}>Avg. Initial Vendor CPI</TableCell>
              <TableCell sx={{ color: 'white' }}>Avg. Final Vendor CPI</TableCell>
              <TableCell sx={{ color: 'white' }}>Invoice Amount</TableCell>
              <TableCell sx={{ color: 'white' }}>Status</TableCell>
              <TableCell sx={{ color: 'white' }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {bids.map((row) => (
              <TableRow key={row.bid_number}>
                <TableCell>{row.po_number}</TableCell>
                <TableCell>{row.bid_number}</TableCell>
                <TableCell>{row.studyName}</TableCell>
                <TableCell>{row.client}</TableCell>
                <TableCell>{row.nDelivered}</TableCell>
                <TableCell>{row.avgFinalLOI}</TableCell>
                <TableCell>{row.avgInitialVendorCPI}</TableCell>
                <TableCell>{row.avgFinalVendorCPI}</TableCell>
                <TableCell>{row.invoiceAmount}</TableCell>
                <TableCell>{row.status}</TableCell>
                <TableCell>
                  <IconButton 
                    onClick={() => handleEditClick(row.bid_number)}
                    color="primary"
                  >
                    <EditIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {showEditModal && (
        <Modal
          open={true}
          onClose={handleCancel}
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Box sx={{ 
            bgcolor: 'background.paper',
            boxShadow: 24,
            p: 4,
            width: '90%',
            maxHeight: '90vh',
            overflow: 'auto'
          }}>
            <InvoiceEdit 
              bid={selectedBid}
              onCancel={handleCancel}
              onSubmit={handleSubmit}
            />
          </Box>
        </Modal>
      )}
    </Box>
  );
};

export default InvoiceBids; 