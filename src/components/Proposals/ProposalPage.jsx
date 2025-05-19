import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from '../../api/axios';
import { Button, TextField, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography, Box, Checkbox } from '@mui/material';

const ProposalPage = () => {
  const { bidId } = useParams();
  const [bidInfo, setBidInfo] = useState(null);
  const [responses, setResponses] = useState({});
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [margin, setMargin] = useState(30);
  const [allocations, setAllocations] = useState({});
  const [selectedPartners, setSelectedPartners] = useState({});

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const bidRes = await axios.get(`/api/bids/${bidId}`);
      setBidInfo(bidRes.data);
      const respRes = await axios.get(`/api/bids/${bidId}/partner-responses`);
      setResponses(respRes.data.responses);
      setSettings(respRes.data.settings);
      setLoading(false);
    };
    fetchData();
  }, [bidId]);

  if (loading) return <div>Loading...</div>;
  if (!bidInfo) return <div>No bid data found.</div>;

  // Helper: Render allocation tables for each audience
  const renderAudienceTables = () => {
    if (!bidInfo.target_audiences) return null;
    return bidInfo.target_audiences.map(aud => (
      <Box key={aud.id} mb={3}>
        <Typography variant="h6">{aud.name} (Required: {aud.sample_required})</Typography>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Select</TableCell>
                <TableCell>Partner</TableCell>
                <TableCell>Commitment</TableCell>
                <TableCell>Allocation</TableCell>
                <TableCell>CPI</TableCell>
                <TableCell>Sales Price</TableCell>
                <TableCell>Timeline</TableCell>
                <TableCell>Cost</TableCell>
                <TableCell>Revenue</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.values(responses)
                .filter(r => r.audiences && r.audiences[aud.id])
                .map((resp, idx) => {
                  const partnerId = resp.partner_id;
                  const partnerName = resp.partner_name || partnerId;
                  const audienceData = resp.audiences[aud.id];
                  const allocation = allocations[`${aud.id}-${partnerId}`] || '';
                  const cpi = audienceData?.cpi || 0;
                  const salesPrice = (cpi * (1 + margin / 100)).toFixed(2);
                  const cost = allocation * cpi;
                  const revenue = allocation * salesPrice;
                  return (
                    <TableRow key={partnerId}>
                      <TableCell>
                        <Checkbox
                          checked={!!selectedPartners[`${aud.id}-${partnerId}`]}
                          onChange={e => setSelectedPartners({
                            ...selectedPartners,
                            [`${aud.id}-${partnerId}`]: e.target.checked
                          })}
                        />
                      </TableCell>
                      <TableCell>{partnerName}</TableCell>
                      <TableCell>{audienceData?.commitment || 0}</TableCell>
                      <TableCell>
                        <TextField
                          type="number"
                          value={allocation}
                          onChange={e => setAllocations({
                            ...allocations,
                            [`${aud.id}-${partnerId}`]: e.target.value
                          })}
                          size="small"
                          style={{ width: 80 }}
                        />
                      </TableCell>
                      <TableCell>${cpi}</TableCell>
                      <TableCell>${salesPrice}</TableCell>
                      <TableCell>{audienceData?.timeline || ''}</TableCell>
                      <TableCell>${cost.toFixed(2)}</TableCell>
                      <TableCell>${revenue.toFixed(2)}</TableCell>
                    </TableRow>
                  );
                })}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    ));
  };

  // Calculate summary
  const totalCost = Object.entries(allocations).reduce((sum, [key, alloc]) => {
    const [audId, partnerId] = key.split('-');
    const resp = Object.values(responses).find(r => r.partner_id == partnerId && r.audiences && r.audiences[audId]);
    const cpi = resp?.audiences[audId]?.cpi || 0;
    return sum + (Number(alloc) * cpi);
  }, 0);

  const totalRevenue = Object.entries(allocations).reduce((sum, [key, alloc]) => {
    const [audId, partnerId] = key.split('-');
    const resp = Object.values(responses).find(r => r.partner_id == partnerId && r.audiences && r.audiences[audId]);
    const cpi = resp?.audiences[audId]?.cpi || 0;
    const salesPrice = cpi * (1 + margin / 100);
    return sum + (Number(alloc) * salesPrice);
  }, 0);

  const totalMargin = totalRevenue - totalCost;
  const effectiveMargin = totalRevenue ? (totalMargin / totalRevenue) * 100 : 0;

  // Save proposal
  const handleSave = async () => {
    const proposalData = {
      bid_id: bidId,
      allocations,
      margin,
      totalCost,
      totalRevenue,
      totalMargin,
      effectiveMargin,
    };
    await axios.post('/api/proposals', { bid_id: bidId, data: proposalData, created_by: 1 });
    alert('Proposal saved!');
  };

  return (
    <Box p={2}>
      <Typography variant="h5" gutterBottom>Final Proposal Preparation</Typography>
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" justifyContent="space-between">
          <Box>
            <Typography variant="subtitle1"><b>Bid Number:</b> {bidInfo.bid_number}</Typography>
            <Typography variant="subtitle1"><b>Study Name:</b> {bidInfo.study_name}</Typography>
            <Typography variant="subtitle1"><b>Client:</b> {bidInfo.client_name}</Typography>
            <Typography variant="subtitle1"><b>Methodology:</b> {bidInfo.methodology}</Typography>
          </Box>
          <Box>
            <Typography variant="subtitle1"><b>Margin Percentage</b></Typography>
            <TextField
              type="number"
              value={margin}
              onChange={e => setMargin(Number(e.target.value))}
              InputProps={{ endAdornment: <span>%</span> }}
              sx={{ width: 120 }}
            />
            <Button onClick={() => setMargin(30)} sx={{ ml: 1 }}>Reset to 30%</Button>
          </Box>
        </Box>
      </Paper>

      <Typography variant="h6" gutterBottom>Partner Allocation</Typography>
      {renderAudienceTables()}

      {/* Proposal Summary Section */}
      <Box display="flex" gap={2} mt={3}>
        <Paper sx={{ p: 2, flex: 1, background: '#e3f0ff' }}>
          <Typography variant="subtitle1"><b>Financial Summary</b></Typography>
          <Typography>Total Cost: ${totalCost.toFixed(2)}</Typography>
          <Typography>Total Revenue: ${totalRevenue.toFixed(2)}</Typography>
          <Typography>Total Margin: ${totalMargin.toFixed(2)}</Typography>
          <Typography>Effective Margin: {effectiveMargin.toFixed(2)}%</Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: 1, background: '#eaffea' }}>
          <Typography variant="subtitle1"><b>Project Overview</b></Typography>
          <Typography>Total Completes: {/* sum allocations */}</Typography>
          <Typography>Timeline: {/* calculate timeline */}</Typography>
          <Typography>Partners Used: {/* count selected partners */}</Typography>
          <Typography>Avg. CPI: {/* calculate avg CPI */}</Typography>
        </Paper>
      </Box>

      <Box mt={2} display="flex" justifyContent="flex-end" gap={2}>
        <Button variant="outlined">Print</Button>
        <Button variant="outlined">Export</Button>
        <Button variant="contained" color="success" onClick={handleSave}>Save</Button>
        <Button variant="contained" color="primary">Finalize Proposal</Button>
      </Box>
    </Box>
  );
};

export default ProposalPage; 