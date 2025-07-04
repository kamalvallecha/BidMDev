import React, { useState, useContext } from 'react';
import {
  Box, Button, TextField, MenuItem, Typography, Paper, Chip, Table, TableHead, TableRow, TableCell, TableBody, CircularProgress, Grid, Dialog, DialogTitle, DialogContent, DialogActions, Checkbox
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import axios from '../../api/axios';
import KeyboardArrowDown from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowRight from '@mui/icons-material/KeyboardArrowRight';
import { useAuth } from '../../contexts/AuthContext';

const taCategories = ['B2B', 'B2C', 'HC - HCP', 'HC - Patient'];
const broaderCategories = [
  "Advertiser/Marketing/Media DM", "Advertising/Media DMs", "Air Travelers", "App Developers", "Asthma Patients", "Automobile Intenders", "Automobile Owners", "BDMs", "Bank account holders", "Broadcasters on a mobile live streaming", "CXOs", "Cancer patients", "Caregivers", "Cat and Dog owner", "Dairy Consumers", "Data Collection Group", "Dealers/Retailers", "Dermatitis patients", "Dermatologists", "Diabetes patients", "Educators", "Electronic appliance User/Owner/Intender", "Endocrinologists", "Energy influencers", "Farmers", "Financial DMs", "Fleet Owner/DMs", "Gen pop", "General Physician", "HR DMs", "Hematologists", "Hispanics", "Home owners", "Household decision makers", "IT/B DMs", "IT DMs", "IT Professionals", "Insurance purchasers", "Journalists", "Kids", "Liqour consumers", "Loyalty Members", "Manager & above", "Marketing DMs", "Medical Directors", "Medical/Pharmacy Directors", "Medical oncologist", "NGO Employees", "Nephrologist", "Neuro-oncologist", "Oncologists", "Opinion Elites", "PC Buyers", "PC Intenders", "Parents of kids", "Payers", "Pediatric Derms", "Pharmacy Directors", "Printer users", "Publisher", "Purchase Decision Makers and Influencers", "Secondary Research Group", "Social Media Users", "Teachers", "Teens", "Users of mobile live video streaming pla", "Veterinarian", "Webcam Users", "Others"
];
const modes = ['Online', 'Offline', 'Mixed'];

export default function FindSimilarBid() {
  const [form, setForm] = useState({
    taCategory: '',
    broaderCategory: '',
    mode: ''
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalBid, setModalBid] = useState(null);
  const [modalPartners, setModalPartners] = useState([]);
  const [modalSelected, setModalSelected] = useState({});
  const [expandedRows, setExpandedRows] = useState(new Set());
  const theme = useTheme();
  const { user: currentUser } = useAuth();
  const [accessRequestedBid, setAccessRequestedBid] = useState(null);
  const [accessRequestStatus, setAccessRequestStatus] = useState('');

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSearched(true);
    try {
      const response = await axios.post('/api/bids/find-similar', {
        taCategory: form.taCategory,
        broaderCategory: form.broaderCategory,
        mode: form.mode
      });
      setResults(response.data);
    } catch (error) {
      setResults([]);
    }
    setLoading(false);
  };

  function groupByBid(results) {
    const grouped = {};
    results.forEach(row => {
      if (!grouped[row.bid_number]) {
        grouped[row.bid_number] = {
          bid_number: row.bid_number,
          client: row.client || row.client_name,
          ir: row.ir,
          sample_required: row.sample_required,
          exact_ta_definition: row.exact_ta_definition,
          rows: []
        };
      }
      grouped[row.bid_number].rows.push(row);
    });
    return Object.values(grouped);
  }

  const groupedResults = groupByBid(results);

  const handleBidClick = (bid) => {
    setModalBid(bid);
    setModalPartners(bid.rows);
    setModalSelected({});
    setModalOpen(true);
  };

  const handleModalPartnerSelect = (partner_name, checked) => {
    setModalSelected(prev => ({ ...prev, [partner_name]: checked }));
  };

  const handleCopySelected = () => {
    const selected = Object.entries(modalSelected)
      .filter(([_, checked]) => checked)
      .map(([partner_name]) => ({ bid_number: modalBid.bid_number, partner_name }));
    if (selected.length === 0) {
      alert('No partners selected!');
    } else {
      alert('Selected partners:\n' + selected.map(s => `Bid: ${s.bid_number}, Partner: ${s.partner_name}`).join('\n'));
      // Replace with your actual copy/duplicate logic
    }
  };

  const handleRowExpand = (partnerName) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(partnerName)) {
        newSet.delete(partnerName);
      } else {
        newSet.add(partnerName);
      }
      return newSet;
    });
  };

  // Helper: check if user has access to a bid (reuse logic from BidList)
  const hasAccessToBid = (bid) => {
    const normalizedUserTeam = (currentUser?.team || '').replace(/\s+/g, '').toLowerCase();
    const normalizedBidTeam = (bid.rows[0]?.team || '').replace(/\s+/g, '').toLowerCase();
    const isOwnTeam = normalizedUserTeam === normalizedBidTeam;
    const isSuperAdmin = currentUser?.role === 'super_admin' || (currentUser?.name && currentUser.name.trim().toLowerCase().includes('kamal vallecha'));
    const isKamal = currentUser?.name && currentUser.name.trim().toLowerCase().includes('kamal vallecha');
    // For demo, assume user has access if own team, super admin, or Kamal
    return isSuperAdmin || isOwnTeam || isKamal;
  };

  // Request access handler
  const handleRequestAccess = async (bid) => {
    setAccessRequestedBid(bid.bid_number);
    setAccessRequestStatus('');
    try {
      await axios.post('/api/bids/request-access', {
        bidId: bid.rows[0]?.bid_id || bid.rows[0]?.id || bid.bid_number,
        bidNumber: bid.bid_number,
        studyName: bid.rows[0]?.study_name || bid.exact_ta_definition,
        userEmail: currentUser?.email,
        userName: currentUser?.name,
        userTeam: currentUser?.team,
      });
      setAccessRequestStatus('Request sent!');
    } catch (error) {
      setAccessRequestStatus('Failed to send request.');
    } finally {
      setTimeout(() => {
        setAccessRequestedBid(null);
        setAccessRequestStatus('');
      }, 3000);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)', p: { xs: 1, md: 4 } }}>
      {/* Header Section */}
      <Box sx={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        borderRadius: { xs: 0, md: 4 },
        px: { xs: 2, md: 6 },
        py: { xs: 3, md: 5 },
        mb: 4,
        position: 'relative',
        overflow: 'hidden',
      }}>
        <Box sx={{ position: 'absolute', top: 0, right: 0, width: 200, height: 200, background: 'rgba(255,255,255,0.1)', borderRadius: '50%', transform: 'translate(50%, -50%)', zIndex: 1 }} />
        <Typography variant="h3" fontWeight={700} mb={1} sx={{ position: 'relative', zIndex: 2 }}>
          🔍 Find Similar Bid
        </Typography>
        <Typography variant="h6" sx={{ opacity: 0.9, position: 'relative', zIndex: 2 }}>
          Discover and compare similar bidding opportunities across market research projects
        </Typography>
      </Box>

      {/* Search Section */}
      <Paper elevation={3} sx={{ p: { xs: 2, md: 4 }, mb: 4, borderRadius: 4, background: 'linear-gradient(145deg, #f8fafc, #edf2f7)' }}>
        <form onSubmit={handleSearch}>
          <Grid container spacing={3} alignItems="end">
            <Grid item xs={12} md={4}>
              <TextField
                select
                label="TA Category *"
                name="taCategory"
                value={form.taCategory}
                onChange={handleChange}
                required
                fullWidth
                size="medium"
                sx={{ borderRadius: 2, background: 'white' }}
              >
                {taCategories.map((cat) => (
                  <MenuItem key={cat} value={cat}>{cat}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                select
                label="Broader Category *"
                name="broaderCategory"
                value={form.broaderCategory}
                onChange={handleChange}
                required
                fullWidth
                size="medium"
                sx={{ borderRadius: 2, background: 'white' }}
              >
                {broaderCategories.map((cat) => (
                  <MenuItem key={cat} value={cat}>{cat}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                select
                label="Survey Mode *"
                name="mode"
                value={form.mode}
                onChange={handleChange}
                required
                fullWidth
                size="medium"
                sx={{ borderRadius: 2, background: 'white' }}
              >
                {modes.map((mode) => (
                  <MenuItem key={mode} value={mode}>{mode}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={1}>
              <Button
                type="submit"
                variant="contained"
                fullWidth
                sx={{
                  height: '56px',
                  minWidth: '120px',
                  background: 'linear-gradient(135deg, #667eea, #764ba2)',
                  color: 'white',
                  fontWeight: 700,
                  fontSize: '1.05em',
                  borderRadius: 2,
                  boxShadow: 3,
                  letterSpacing: '0.5px',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #667eea 80%, #20b2aa 100%)',
                  },
                }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : '🔍 Search Bid'}
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>

      {/* Results Section */}
      <Box sx={{ mt: 2 }}>
        {loading ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <CircularProgress size={48} sx={{ color: '#667eea' }} />
            <Typography variant="h6" mt={2}>Searching for similar bids...</Typography>
          </Box>
        ) : results.length > 0 ? (
          <Paper elevation={3} sx={{ p: { xs: 1, md: 3 }, borderRadius: 4, mt: 2 }}>
            <Box sx={{
              background: 'linear-gradient(135deg, #667eea, #764ba2)',
              color: 'white',
              px: 3, py: 2,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              borderTopLeftRadius: 16, borderTopRightRadius: 16,
              mb: 2
            }}>
              <Typography variant="h6" fontWeight={700}>📊 Similar Bid Results</Typography>
              <Box sx={{
                background: 'linear-gradient(135deg, #667eea, #20b2aa)',
                px: 2, py: 0.5, borderRadius: 2, fontWeight: 600, fontSize: '0.95em'
              }}>
                {results.length} Results Found
              </Box>
            </Box>
            <Box sx={{ overflowX: 'auto' }}>
              <Table sx={{ minWidth: 900, background: 'white', borderRadius: 3 }}>
                <TableHead>
                  <TableRow sx={{ background: 'linear-gradient(135deg, #667eea, #764ba2)' }}>
                    <TableCell sx={{ color: 'white', fontWeight: 600 }}>Bid Number</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600 }}>Client</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600 }}>Partner Name</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600 }}>Exact TA Definition</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600, textAlign: 'center' }}>IR</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600, textAlign: 'center' }}>Sample Required</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600 }}>Countries</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600, textAlign: 'center' }}>Committed</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600, textAlign: 'center' }}>N-delivered</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 600, textAlign: 'center' }}>CPI</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {groupedResults.map((bid, idx) => (
                    <TableRow hover key={bid.bid_number}>
                      <TableCell>
                        <span
                          style={{
                            fontWeight: 700, color: '#667eea',
                            background: 'linear-gradient(135deg, #667eea10, #667eea20)',
                            padding: '6px 10px', borderRadius: 8,
                            display: 'inline-block', cursor: 'pointer', textDecoration: 'underline'
                          }}
                          onClick={() => handleBidClick(bid)}
                        >
                          {bid.bid_number}
                        </span>
                      </TableCell>
                      <TableCell>{bid.client}</TableCell>
                      <TableCell>
                        <Box sx={{
                          maxWidth: 300, maxHeight: 60, overflowY: 'auto',
                          display: 'flex', flexWrap: 'wrap', gap: 0.5,
                          scrollbarWidth: 'thin',
                        }}>
                          {[...new Set(bid.rows.map(r => r.partner_name))].map((partner, i) => (
                            <Chip
                              key={i}
                              label={partner}
                              size="small"
                              sx={{
                                background: 'linear-gradient(45deg, #20b2aa, #667eea)',
                                color: 'white', fontWeight: 500, fontSize: '0.75em', m: 0.2
                              }}
                            />
                          ))}
                        </Box>
                      </TableCell>
                      <TableCell>{bid.exact_ta_definition}</TableCell>
                      <TableCell align="center">{bid.ir}</TableCell>
                      <TableCell align="center">{bid.sample_required}</TableCell>
                      <TableCell>
                        <Box sx={{
                          maxWidth: 300, maxHeight: 60, overflowY: 'auto',
                          display: 'flex', flexWrap: 'wrap', gap: 0.5,
                          scrollbarWidth: 'thin',
                        }}>
                          {bid.rows[0]?.countries?.split(',').map((country, i) => (
                            <Chip
                              key={i}
                              label={country.trim()}
                              size="small"
                              sx={{
                                background: 'linear-gradient(45deg, #ffd700, #ff6b6b)',
                                color: 'white', fontWeight: 500, fontSize: '0.75em', m: 0.2
                              }}
                            />
                          ))}
                        </Box>
                      </TableCell>
                      <TableCell align="center">{bid.rows[0]?.committed > 0 ? '✓' : '-'}</TableCell>
                      <TableCell align="center">{bid.rows[0]?.n_delivered ?? '-'}</TableCell>
                      <TableCell align="center">{bid.rows[0]?.cpi}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Paper>
        ) : searched ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <Typography variant="h4" color="#718096" mb={2}>No results found</Typography>
            <Typography variant="body1" color="textSecondary">Try adjusting your search criteria to find similar bids.</Typography>
          </Box>
        ) : (
          <Box sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="body2" color="textSecondary">No results yet. Use the form above to search for similar bids.</Typography>
          </Box>
        )}
      </Box>

      <Dialog open={modalOpen} onClose={() => setModalOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Bid {modalBid?.bid_number} Details</DialogTitle>
        <DialogContent>
          {modalBid && (
            <Box mb={2}>
              <Typography><b>Client:</b> {modalBid.client}</Typography>
              <Typography><b>IR:</b> {modalBid.ir}</Typography>
              <Typography><b>Sample Required:</b> {modalBid.rows?.some(r => r.is_best_efforts) ? 'BE/Max' : modalBid.sample_required}</Typography>
              <Typography><b>Exact TA Definition:</b> {modalBid.exact_ta_definition}</Typography>
            </Box>
          )}
          <Typography variant="subtitle1" gutterBottom>Partners</Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Select</TableCell>
                <TableCell>Partner Name</TableCell>
                <TableCell>Countries</TableCell>
                <TableCell>Committed</TableCell>
                <TableCell>N-delivered</TableCell>
                <TableCell>CPI</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {[...new Set(modalPartners.map(r => r.partner_name))].map((partnerName, idx) => {
                const row = modalPartners.find(r => r.partner_name === partnerName);
                return (
                  <React.Fragment key={idx}>
                    <TableRow 
                      sx={{ cursor: 'pointer', '&:hover': { bgcolor: '#f5f5f5' } }}
                    >
                      <TableCell>
                        <span
                          onClick={e => {
                            e.stopPropagation();
                            handleRowExpand(row.partner_name);
                          }}
                          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                        >
                          {expandedRows.has(row.partner_name) ? <KeyboardArrowDown /> : <KeyboardArrowRight />}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span style={{
                          background: '#20b2aa20', color: '#20b2aa',
                          padding: '4px 8px', borderRadius: 6, fontWeight: 600,
                          fontSize: '0.95em'
                        }}>{row.partner_name}</span>
                      </TableCell>
                      <TableCell>
                        <Box sx={{
                          maxWidth: 300, maxHeight: 60, overflowY: 'auto',
                          display: 'flex', flexWrap: 'wrap', gap: 0.5,
                          scrollbarWidth: 'thin',
                        }}>
                          {row.countries?.split(',').map((country, i) => (
                            <Chip
                              key={i}
                              label={country.trim()}
                              size="small"
                              sx={{
                                background: 'linear-gradient(45deg, #ffd700, #ff6b6b)',
                                color: 'white', fontWeight: 500, fontSize: '0.75em', m: 0.2
                              }}
                            />
                          ))}
                        </Box>
                      </TableCell>
                      <TableCell align="center" sx={{ fontWeight: 700, color: '#20b2aa' }}>{row.committed ?? '-'}</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 700 }}>{row.n_delivered ?? '-'}</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 700, color: '#667eea' }}>{row.cpi}</TableCell>
                    </TableRow>
                    {/* Country-wise breakdown */}
                    {expandedRows.has(row.partner_name) && (
                      <TableRow>
                        <TableCell colSpan={6} sx={{ py: 0, bgcolor: '#f5f5f5' }}>
                          <Box sx={{ margin: 1 }}>
                            <Typography variant="subtitle2" gutterBottom sx={{ color: '#666', ml: 2 }}>
                              Country-wise Breakdown:
                            </Typography>
                            <Table size="small">
                              <TableHead>
                                <TableRow>
                                  <TableCell>Country</TableCell>
                                  <TableCell align="right">Committed</TableCell>
                                  <TableCell align="right">Delivered</TableCell>
                                  <TableCell align="right">CPI</TableCell>
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {row.countries?.split(',').map((country, i) => (
                                  <TableRow key={i}>
                                    <TableCell>{country.trim()}</TableCell>
                                    <TableCell align="right">{row.country_data?.[country.trim()]?.committed || 0}</TableCell>
                                    <TableCell align="right">{row.country_data?.[country.trim()]?.delivered || 0}</TableCell>
                                    <TableCell align="right">${row.country_data?.[country.trim()]?.cpi || row.cpi || 0}</TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </Box>
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                );
              })}
            </TableBody>
          </Table>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModalOpen(false)}>Close</Button>
          {modalBid && !hasAccessToBid(modalBid) ? (
            <Button
              variant="outlined"
              color="secondary"
              onClick={() => handleRequestAccess(modalBid)}
              disabled={accessRequestedBid === modalBid.bid_number}
            >
              {accessRequestedBid === modalBid.bid_number ? accessRequestStatus || "Requesting..." : "Request Access"}
            </Button>
          ) : (
            <Button
              variant="contained"
              color="primary"
              onClick={handleCopySelected}
              disabled={Object.values(modalSelected).filter(Boolean).length === 0}
            >
              Copy Selected Partners
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
} 