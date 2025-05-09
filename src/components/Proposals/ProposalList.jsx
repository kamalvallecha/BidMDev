import React, { useEffect, useState } from 'react';
import axios from '../../api/axios';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, Typography, Box, Tooltip, IconButton } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DownloadIcon from '@mui/icons-material/Download';

const ProposalList = () => {
  console.log('ProposalList component rendered'); // Debug log
  
  const [proposals, setProposals] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    console.log('ProposalList useEffect triggered'); // Debug log
    const fetchProposals = async () => {
      try {
        console.log('Fetching proposals...'); // Debug log
        const res = await axios.get('/api/proposals');
        console.log('Proposals response:', res.data); // Debug log
        setProposals(res.data);
      } catch (error) {
        console.error('Error fetching proposals:', error);
      }
    };
    fetchProposals();
  }, []);

  // Helper to flatten allocations for CSV
  function flattenAllocations(proposal) {
    // Add debug log
    console.log('Download proposal object:', proposal);
    // Try all possible locations for allocations
    let data = proposal.data?.data ? proposal.data.data : proposal.data || proposal;
    let allocations = data.allocations || {};
    // If still empty, try one more level
    if (Object.keys(allocations).length === 0 && proposal.data?.data?.allocations) {
      allocations = proposal.data.data.allocations;
    }
    const bidInfo = data.bidInfo || {};
    const margin = data.marginPercentage || '';
    const rows = [];
    // Helper to safely get nested values
    const getValue = (obj, path, defaultValue = '') => {
      return path.split('.').reduce((o, key) => (o && o[key] !== undefined ? o[key] : defaultValue), obj);
    };
    // Process allocations
    let found = false;
    Object.keys(allocations).forEach(audId => {
      Object.keys(allocations[audId]).forEach(country => {
        Object.keys(allocations[audId][country]).forEach(partnerId => {
          const alloc = allocations[audId][country][partnerId];
          if (alloc.selected) {
            found = true;
            rows.push({
              bid_number: bidInfo.bidNumber || proposal.bid_number || '',
              study_name: bidInfo.studyName || proposal.study_name || '',
              client_name: bidInfo.clientName || proposal.client_name || '',
              methodology: bidInfo.methodology || proposal.methodology || '',
              margin_percentage: margin,
              audience_id: audId,
              country,
              partner_id: partnerId,
              allocation: alloc.allocation,
              cpi: alloc.cpi,
              sales_price: alloc.salesPrice,
              cost: alloc.cost,
              revenue: alloc.revenue,
              commitment: alloc.commitment,
              timeline: alloc.timeline
            });
          }
        });
      });
    });
    if (!found) {
      throw new Error('No allocations to download for this proposal.');
    }
    return rows;
  }

  async function downloadProposalCSV(proposal) {
    try {
      // Always fetch the full proposal data for download
      const proposalId = proposal.proposal_id || proposal.id;
      const res = await axios.get(`/api/proposals/${proposalId}`);
      const fullProposal = res.data;
      const rows = flattenAllocations(fullProposal);
      if (rows.length === 0) {
        alert('No allocations to download for this proposal.');
        return;
      }
      // Get headers from first row
      const header = Object.keys(rows[0]);
      // Create CSV content
      const csv = [
        header.join(','),  // Header row
        ...rows.map(row => 
          header.map(h => {
            const value = String(row[h] || '').replace(/"/g, '""');
            return `"${value}"`;
          }).join(',')
        )
      ].join('\r\n');
      // Create and trigger download
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `proposal_${proposal.bid_number || proposal.data?.bidInfo?.bidNumber || proposal.proposal_id || 'export'}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading CSV:', error);
      alert(error.message || 'Error downloading CSV. Please try again.');
    }
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Proposals List</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => navigate('/proposals/new')}
        >
          Create New Proposal
        </Button>
      </Box>
      
      {proposals.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="textSecondary">
            No proposals found
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
            Click the "Create New Proposal" button to get started
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Bid Number</TableCell>
                <TableCell>Client</TableCell>
                <TableCell>Study Name</TableCell>
                <TableCell>Methodology</TableCell>
                <TableCell>Total Cost</TableCell>
                <TableCell>Total Revenue</TableCell>
                <TableCell>Total Margin ($)</TableCell>
                <TableCell>Effective Margin (%)</TableCell>
                <TableCell>Avg CPI</TableCell>
                <TableCell>Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {proposals.map((p) => (
                <TableRow key={p.proposal_id}>
                  <TableCell>{p.bid_number}</TableCell>
                  <TableCell>{p.client_name}</TableCell>
                  <TableCell>{p.study_name}</TableCell>
                  <TableCell>{p.methodology}</TableCell>
                  <TableCell>${Number(p.total_cost || 0).toFixed(2)}</TableCell>
                  <TableCell>${Number(p.total_revenue || 0).toFixed(2)}</TableCell>
                  <TableCell>${Number(p.total_margin || 0).toFixed(2)}</TableCell>
                  <TableCell>{Number(p.effective_margin || 0).toFixed(2)}%</TableCell>
                  <TableCell>${Number(p.avg_cpi || 0).toFixed(2)}</TableCell>
                  <TableCell>
                    <Tooltip title="View/Edit">
                      <IconButton size="small" onClick={() => navigate(`/proposals/${p.proposal_id}`)}>
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Download CSV">
                      <IconButton size="small" onClick={() => downloadProposalCSV(p)}>
                        <DownloadIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default ProposalList; 