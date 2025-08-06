import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from '../../api/axios';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  MenuItem,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Checkbox
} from '@mui/material';
import Autocomplete from '@mui/material/Autocomplete';
import { useAuth } from '../../contexts/AuthContext';

const ProposalForm = () => {
  const { proposalId } = useParams();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [bids, setBids] = useState([]);
  const [selectedBidId, setSelectedBidId] = useState('');
  const [bidDetails, setBidDetails] = useState(null);
  const [partnerResponses, setPartnerResponses] = useState(null);
  const [formData, setFormData] = useState({
    bid_id: '',
    totalCost: '',
    totalRevenue: '',
    totalMargin: '',
    effectiveMargin: ''
  });
  const [allocations, setAllocations] = useState({});
  const [marginPercentage, setMarginPercentage] = useState(30);
  const [proposals, setProposals] = useState([]);
  const [loadedProposalData, setLoadedProposalData] = useState(null);

  useEffect(() => {
    const fetchBidsAndProposals = async () => {
      try {
        const [bidsRes, proposalsRes] = await Promise.all([
          axios.get('/api/bids', {
            headers: {
              'X-User-Id': currentUser?.id,
              'X-User-Team': currentUser?.team,
              'X-User-Role': currentUser?.role,
              'X-User-Name': currentUser?.name,
            }
          }),
          axios.get('/api/proposals')
        ]);
        setBids(bidsRes.data.bids || []);
        setProposals(proposalsRes.data);
        // Debug logs after fetching
        console.log('DEBUG fetched bids:', bidsRes.data.bids);
        console.log('DEBUG fetched proposals:', proposalsRes.data);
      } catch (error) {
        console.error('Error fetching bids or proposals:', error);
      }
    };
    fetchBidsAndProposals();
  }, [currentUser]);

  // Show all bids in the dropdown, regardless of proposals
  const safeBids = Array.isArray(bids) ? bids : [];
  const availableBids = safeBids;
  // When editing, always show the current bid
  const dropdownBids = (!proposalId || proposalId === 'new') ? availableBids : safeBids.filter(bid => Number(bid.id) === Number(selectedBidId));

  // Debug logs for dropdown logic
  console.log('DEBUG availableBids:', availableBids);
  console.log('DEBUG dropdownBids:', dropdownBids);

  // If editing, ensure we can't change the bid
  useEffect(() => {
    if (proposalId && proposalId !== 'new') {
      const proposal = proposals.find(p => p.proposal_id === proposalId);
      if (proposal) {
        setSelectedBidId(proposal.bid_id);
      }
    }
  }, [proposalId, proposals]);

  // Fetch proposal if editing
  useEffect(() => {
    const fetchProposal = async () => {
      if (proposalId && proposalId !== 'new') {
        try {
          setLoading(true);
          const res = await axios.get(`/api/proposals/${proposalId}`);
          let proposalData = res.data.data;
          if (proposalData && proposalData.data) {
            proposalData = proposalData.data;
          }
          const bidId = res.data.bid_id || proposalData.bid_id;
          console.log('Loaded bid_id:', bidId);
          if (!bidId) {
            throw new Error('No bid_id found in proposal data');
          }
          setFormData({
            bid_id: bidId,
            ...proposalData
          });
          setSelectedBidId(bidId);
          setLoadedProposalData(proposalData);

          // Only fetch if bidId is valid
          if (bidId) {
            const [bidRes, partnerRes] = await Promise.all([
              axios.get(`/api/bids/${bidId}`),
              axios.get(`/api/bids/${bidId}/partner-responses`)
            ]);
            setBidDetails(bidRes.data);
            setPartnerResponses(partnerRes.data);
          }
        } catch (error) {
          console.error('Error fetching proposal:', error);
        } finally {
          setLoading(false);
        }
      }
    };
    fetchProposal();
  }, [proposalId]);

  // When editing, after bidDetails and partnerResponses are loaded, merge the saved allocations into a fresh allocations structure so all rows are present and prefilled
  useEffect(() => {
    if (
      proposalId && proposalId !== 'new' &&
      bidDetails && partnerResponses &&
      loadedProposalData && loadedProposalData.allocations
    ) {
      // Build fresh allocations structure from bidDetails
      const allocInit = {};
      if (bidDetails.target_audiences) {
        bidDetails.target_audiences.forEach(aud => {
          allocInit[aud.id] = {};
          Object.keys(aud.country_samples).forEach(country => {
            allocInit[aud.id][country] = {};
            bidDetails.partners.forEach(partner => {
              // Prefill from saved allocations if exists
              const saved = loadedProposalData.allocations?.[aud.id]?.[country]?.[partner.id] || {};
              allocInit[aud.id][country][partner.id] = {
                selected: !!saved.selected,
                allocation: saved.allocation || '',
                cpi: saved.cpi || '',
                salesPrice: saved.salesPrice || '',
                timeline: saved.timeline || '',
                cost: saved.cost || '',
                revenue: saved.revenue || '',
                commitment: saved.commitment || ''
              };
            });
          });
        });
      }
      setAllocations(allocInit);
      if (loadedProposalData.marginPercentage !== undefined) {
        setMarginPercentage(loadedProposalData.marginPercentage);
      }
    }
  }, [proposalId, bidDetails, partnerResponses, loadedProposalData]);

  // Fetch bid details and partner responses when a bid is selected or when editing
  useEffect(() => {
    if (selectedBidId) {
      setLoading(true);
      Promise.all([
        axios.get(`/api/bids/${selectedBidId}`),
        axios.get(`/api/bids/${selectedBidId}/partner-responses`)
      ])
        .then(([bidRes, partnerRes]) => {
          setBidDetails(bidRes.data);
          setPartnerResponses(partnerRes.data);
          // Initialize allocations state only if not editing
          if (!proposalId || proposalId === 'new') {
            const allocInit = {};
            if (bidRes.data.target_audiences) {
              bidRes.data.target_audiences.forEach(aud => {
                allocInit[aud.id] = {};
                Object.keys(aud.country_samples).forEach(country => {
                  allocInit[aud.id][country] = {};
                  bidRes.data.partners.forEach(partner => {
                    allocInit[aud.id][country][partner.id] = {
                      selected: false,
                      allocation: '',
                      cpi: '',
                      salesPrice: '',
                      timeline: '',
                      cost: '',
                      revenue: ''
                    };
                  });
                });
              });
            }
            setAllocations(allocInit);
          }
        })
        .catch(() => {
          setBidDetails(null);
          setPartnerResponses(null);
        })
        .finally(() => setLoading(false));
    } else {
      setBidDetails(null);
      setPartnerResponses(null);
      setAllocations({});
    }
  }, [selectedBidId, proposalId]);

  // Helper to get partner response for a given audience, country, partner
  const getPartnerResponse = (audienceId, country, partnerId) => {
    if (!partnerResponses || !partnerResponses.responses) return {};
    // Find the key where partner_id matches (convert to number for robust match)
    const partnerKey = Object.keys(partnerResponses.responses).find(
      key => {
        const resp = partnerResponses.responses[key];
        return resp?.partner_id == partnerId; // loose equality to match string/number
      }
    );
    if (!partnerKey) return {};
    return (
      partnerResponses.responses[partnerKey]?.audiences?.[audienceId]?.[country] || {}
    );
  };

  // Update all allocations' salesPrice and revenue when margin or CPI changes
  useEffect(() => {
    if (!bidDetails || !partnerResponses) return;
    setAllocations((prev) => {
      const updated = { ...prev };
      Object.keys(updated).forEach((audId) => {
        Object.keys(updated[audId]).forEach((country) => {
          Object.keys(updated[audId][country]).forEach((partnerId) => {
            const alloc = updated[audId][country][partnerId];
            const resp = getPartnerResponse(audId, country, partnerId);
            const cpi = parseFloat(resp.cpi) || 0;
            const allocation = parseFloat(alloc.allocation) || 0;
            const salesPrice = (cpi * (1 + marginPercentage / 100)).toFixed(2);
            updated[audId][country][partnerId] = {
              ...alloc,
              cpi: resp.cpi || '',
              timeline: resp.timeline || '',
              salesPrice: salesPrice,
              cost: (allocation * cpi).toFixed(2),
              revenue: (allocation * salesPrice).toFixed(2),
              commitment: resp.commitment || '',
            };
          });
        });
      });
      return updated;
    });
  }, [marginPercentage, partnerResponses]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleBidChange = (e) => {
    setSelectedBidId(e.target.value);
    setFormData(prev => ({ ...prev, bid_id: e.target.value }));
  };

  // Checkbox handler
  const handlePartnerSelect = (audienceId, country, partnerId, checked) => {
    setAllocations(prev => {
      const updated = { ...prev };
      updated[audienceId] = { ...updated[audienceId] };
      updated[audienceId][country] = { ...updated[audienceId][country] };
      updated[audienceId][country][partnerId] = {
        ...updated[audienceId][country][partnerId],
        selected: checked
      };
      // Optionally, prefill allocation if checked
      if (checked && bidDetails) {
        // Prefill with commitment if available
        const aud = bidDetails.target_audiences.find(a => a.id === audienceId);
        const partner = bidDetails.partners.find(p => p.id === partnerId);
        if (aud && partner) {
          updated[audienceId][country][partnerId].allocation = '' + (partner.commitment || '');
        }
      } else if (!checked) {
        // Clear values if unchecked
        updated[audienceId][country][partnerId] = {
          selected: false,
          allocation: '',
          cpi: '',
          salesPrice: '',
          timeline: '',
          cost: '',
          revenue: ''
        };
      }
      return updated;
    });
  };

  // Input handler
  const handleInputChange = (audienceId, country, partnerId, field, value) => {
    setAllocations(prev => {
      const updated = { ...prev };
      updated[audienceId] = { ...updated[audienceId] };
      updated[audienceId][country] = { ...updated[audienceId][country] };
      updated[audienceId][country][partnerId] = {
        ...updated[audienceId][country][partnerId],
        [field]: value
      };
      // Live calculate cost/revenue if allocation and cpi/salesPrice are present
      const alloc = parseFloat(updated[audienceId][country][partnerId].allocation) || 0;
      const cpi = parseFloat(updated[audienceId][country][partnerId].cpi) || 0;
      const sales = parseFloat(updated[audienceId][country][partnerId].salesPrice) || 0;
      updated[audienceId][country][partnerId].cost = (alloc * cpi).toFixed(2);
      updated[audienceId][country][partnerId].revenue = (alloc * sales).toFixed(2);
      return updated;
    });
  };

  const calculateMargins = () => {
    const cost = parseFloat(formData.totalCost) || 0;
    const revenue = parseFloat(formData.totalRevenue) || 0;
    const margin = revenue - cost;
    const effectiveMargin = cost > 0 ? (margin / cost) * 100 : 0;

    setFormData(prev => ({
      ...prev,
      totalMargin: margin.toFixed(2),
      effectiveMargin: effectiveMargin.toFixed(2)
    }));
  };

  const getSelectedAllocations = () => {
    const selected = {};
    Object.keys(allocations).forEach(audId => {
      Object.keys(allocations[audId]).forEach(country => {
        Object.keys(allocations[audId][country]).forEach(partnerId => {
          const alloc = allocations[audId][country][partnerId];
          if (alloc.selected) {
            if (!selected[audId]) selected[audId] = {};
            if (!selected[audId][country]) selected[audId][country] = {};
            selected[audId][country][partnerId] = alloc;
          }
        });
      });
    });
    return selected;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const payload = {
        bid_id: selectedBidId,
        data: {
          allocations: getSelectedAllocations(),
          summary,
          bidInfo: {
            studyName: bidDetails?.study_name || '',
            clientName: bidDetails?.client_name || '',
            methodology: bidDetails?.methodology || '',
            bidNumber: bids.find(b => b.id === selectedBidId)?.bid_number || ''
          },
          marginPercentage
        }
      };
      if (!proposalId || proposalId === 'new') {
        await axios.post('/api/proposals', payload);
      } else {
        await axios.put(`/api/proposals/${proposalId}`, payload);
      }
      navigate('/proposals');
    } catch (error) {
      console.error('Error saving proposal:', error);
    } finally {
      setLoading(false);
    }
  };

  // --- Summary Calculations ---
  console.log('DEBUG allocations:', allocations);
  const summary = React.useMemo(() => {
    let totalCost = 0;
    let totalRevenue = 0;
    let totalCompletes = 0;
    let partnersUsedSet = new Set();
    const summedAllocations = [];
    Object.keys(allocations).forEach(audId => {
      Object.keys(allocations[audId]).forEach(country => {
        Object.keys(allocations[audId][country]).forEach(partnerId => {
          // Ensure all keys are strings
          const sAudId = String(audId);
          const sCountry = String(country);
          const sPartnerId = String(partnerId);
          const alloc = allocations[sAudId][sCountry][sPartnerId];
          if (alloc.selected) {
            // Recalculate cost and revenue live
            const allocation = parseFloat(alloc.allocation) || 0;
            // Get latest CPI from partnerResponses
            const resp = getPartnerResponse(sAudId, sCountry, sPartnerId);
            console.log('DEBUG summary getPartnerResponse:', {audId: sAudId, country: sCountry, partnerId: sPartnerId, resp});
            const cpi = parseFloat(resp.cpi) || 0;
            const salesPrice = cpi * (1 + marginPercentage / 100);
            const cost = allocation * cpi;
            const revenue = allocation * salesPrice;
            totalCost += cost;
            totalRevenue += revenue;
            totalCompletes += allocation;
            partnersUsedSet.add(sPartnerId);
            summedAllocations.push({audId: sAudId, country: sCountry, partnerId: sPartnerId, allocation, cpi, cost, revenue});
          }
        });
      });
    });
    console.log('DEBUG summedAllocations:', summedAllocations);
    const totalMargin = totalRevenue - totalCost;
    const effectiveMargin = totalRevenue > 0 ? (totalMargin / totalRevenue) * 100 : 0;
    const avgCPI = totalCompletes > 0 ? totalCost / totalCompletes : 0;
    return {
      totalCost: totalCost.toFixed(2),
      totalRevenue: totalRevenue.toFixed(2),
      totalMargin: totalMargin.toFixed(2),
      effectiveMargin: effectiveMargin.toFixed(2),
      totalCompletes: totalCompletes.toFixed(0),
      partnersUsed: partnersUsedSet.size,
      avgCPI: avgCPI.toFixed(2)
    };
  }, [allocations, partnerResponses, marginPercentage]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          {proposalId === 'new' ? 'Create New Proposal' : 'Edit Proposal'}
        </Typography>
        {/* Bid selection dropdown only for new proposal */}
        {(!proposalId || proposalId === 'new') ? (
          <Box sx={{ mb: 3 }}>
            <Autocomplete
              options={dropdownBids}
              getOptionLabel={(option) => option.bid_number || ''}
              value={dropdownBids.find(b => b.id === selectedBidId) || null}
              onChange={(event, newValue) => {
                setSelectedBidId(newValue ? newValue.id : '');
                setFormData(prev => ({ ...prev, bid_id: newValue ? newValue.id : '' }));
              }}
              renderInput={(params) => (
                <TextField {...params} label="Bid" required fullWidth />
              )}
              isOptionEqualToValue={(option, value) => option.id === value.id}
            />
          </Box>
        ) : (
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              label="Bid"
              name="bid_id"
              value={selectedBidId}
              disabled
              InputProps={{ readOnly: true }}
            />
          </Box>
        )}
        {/* Top summary section: Bid Info + Margin Settings */}
        <Box sx={{ display: 'flex', flexDirection: 'row', gap: 4, mb: 3, p: 3, background: '#f5f8ff', borderRadius: 2, border: '1px solid #e0e7ef', alignItems: 'flex-start' }}>
          {/* Bid Information */}
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>Bid Information</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              <Box><b>Bid Number:</b> {selectedBidId ? (bids.find(b => b.id === selectedBidId)?.bid_number || '') : ''}</Box>
              <Box><b>Study Name:</b> {bidDetails?.study_name || ''}</Box>
              <Box><b>Client:</b> {bidDetails?.client_name || ''}</Box>
              <Box><b>Methodology:</b> {bidDetails?.methodology || ''}</Box>
            </Box>
          </Box>
          {/* Margin Settings */}
          <Box sx={{ minWidth: 260 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>Margin Settings</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <TextField
                label="Margin Percentage"
                type="number"
                value={marginPercentage}
                onChange={e => setMarginPercentage(Number(e.target.value))}
                sx={{ width: 120 }}
                InputProps={{ endAdornment: <span>%</span> }}
              />
              <Button
                variant="outlined"
                size="small"
                onClick={() => setMarginPercentage(30)}
              >
                Reset to 30%
              </Button>
            </Box>
          </Box>
        </Box>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            {selectedBidId && bidDetails && partnerResponses && (
              <>
                <Grid item xs={12}>
                  {bidDetails.target_audiences && bidDetails.target_audiences.map(audience => (
                    <Box key={audience.id} sx={{ mb: 4 }}>
                      <Typography variant="h6" sx={{ mb: 1 }}>
                        Audience: {audience.broader_category || audience.name}
                        {audience.mode || audience.methodology ? ` - ${audience.mode || audience.methodology}` : ''}
                        {(() => {
                          const irValue = parseFloat(audience.ir ?? audience.incidence_rate);
                          return !isNaN(irValue) ? ` - IR ${irValue.toFixed(2)}%` : '';
                        })()}
                      </Typography>
                      {Object.entries(audience.country_samples).map(([country, sample]) => (
                        <Box key={country} sx={{ mb: 2, ml: 2 }}>
                          <Typography variant="subtitle1">{country} (Required: {sample.sample_size})</Typography>
                          <TableContainer component={Paper}>
                            <Table size="small">
                              <TableHead>
                                <TableRow>
                                  <TableCell>Select</TableCell>
                                  <TableCell>Partner</TableCell>
                                  <TableCell>Commitment</TableCell>
                                  <TableCell>Allocation</TableCell>
                                  <TableCell>CPI</TableCell>
                                  <TableCell>Sales Price</TableCell>
                                  <TableCell>Cost</TableCell>
                                  <TableCell>Revenue</TableCell>
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {bidDetails.partners.map(partner => {
                                  const alloc = allocations[audience.id]?.[country]?.[partner.id] || {};
                                  console.log('DEBUG table alloc:', {audienceId: audience.id, country, partnerId: partner.id, alloc});
                                  const resp = getPartnerResponse(audience.id, country, partner.id);
                                  console.log('DEBUG row:', {audienceId: audience.id, country, partnerId: partner.id, resp, timeline: resp.timeline});
                                  const isSelected = !!alloc.selected;
                                  const allocation = parseFloat(alloc.allocation) || 0;
                                  const cpi = parseFloat(resp.cpi) || 0;
                                  const salesPrice = cpi ? (cpi * (1 + marginPercentage / 100)) : 0;
                                  const cost = isSelected ? (allocation * cpi).toFixed(2) : '0.00';
                                  const revenue = isSelected ? (allocation * salesPrice).toFixed(2) : '0.00';
                                  return (
                                    <TableRow key={partner.id}>
                                      <TableCell>
                                        <Checkbox
                                          checked={!!alloc.selected}
                                          onChange={e => handlePartnerSelect(audience.id, country, partner.id, e.target.checked)}
                                        />
                                      </TableCell>
                                      <TableCell>{partner.partner_name}</TableCell>
                                      <TableCell>
                                        {resp.pass 
                                          ? 'Pass'
                                          : resp.commitment_type === 'be_max' 
                                            ? 'BE/Max' 
                                            : (resp.commitment ?? '')}
                                      </TableCell>
                                                                              <TableCell>
                                          <TextField
                                            size="small"
                                            value={alloc.allocation || ''}
                                            onChange={e => handleInputChange(audience.id, country, partner.id, 'allocation', e.target.value)}
                                            disabled={!alloc.selected || resp.pass}
                                            sx={{ width: 80 }}
                                          />
                                        </TableCell>
                                      <TableCell>
                                        <TextField
                                          size="small"
                                          value={resp.cpi || ''}
                                          disabled
                                          sx={{ width: 80 }}
                                        />
                                      </TableCell>
                                      <TableCell>
                                        <TextField
                                          size="small"
                                          value={isSelected && resp.cpi ? salesPrice.toFixed(2) : ''}
                                          disabled
                                          sx={{ width: 80 }}
                                        />
                                      </TableCell>
                                      <TableCell>{isSelected ? cost : '0.00'}</TableCell>
                                      <TableCell>{isSelected ? revenue : '0.00'}</TableCell>
                                    </TableRow>
                                  );
                                })}
                              </TableBody>
                            </Table>
                          </TableContainer>
                        </Box>
                      ))}
                    </Box>
                  ))}
                </Grid>
                {/* Summary Section */}
                <Grid item xs={12}>
                  <Box sx={{ mt: 4 }}>
                    <Typography variant="h6">Proposal Summary</Typography>
                    <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                      {/* Financial Summary */}
                      <Paper sx={{ flex: 1, p: 2, background: '#f5f8ff', borderRadius: 2 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1, color: '#2a4d8f' }}>Financial Summary</Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, fontSize: 18 }}>
                          <div><b>Total Cost:</b> ${summary.totalCost}</div>
                          <div><b>Total Revenue:</b> ${summary.totalRevenue}</div>
                          <div><b>Total Margin:</b> ${summary.totalMargin}</div>
                          <div><b>Effective Margin:</b> {summary.effectiveMargin}%</div>
                        </Box>
                      </Paper>
                      {/* Project Overview */}
                      <Paper sx={{ flex: 1, p: 2, background: '#f6fff7', borderRadius: 2 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1, color: '#2a8f4d' }}>Project Overview</Typography>
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, fontSize: 18 }}>
                          <div><b>Total Completes:</b> {summary.totalCompletes}</div>
                          <div><b>Partners Used:</b> {summary.partnersUsed}</div>
                          <div><b>Avg. CPI:</b> ${summary.avgCPI}</div>
                        </Box>
                      </Paper>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                    <Button
                      variant="outlined"
                      onClick={() => navigate('/proposals')}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      variant="contained"
                      color="primary"
                      disabled={loading}
                    >
                      {loading ? 'Saving...' : 'Save Proposal'}
                    </Button>
                  </Box>
                </Grid>
              </>
            )}
          </Grid>
        </form>
      </Paper>
    </Box>
  );
};

export default ProposalForm; 