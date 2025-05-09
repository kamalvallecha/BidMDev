import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Paper, 
  FormControl, 
  Select, 
  MenuItem, 
  TextField, 
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Tabs,
  Tab,
  Box
} from '@mui/material';
import axios from '../../api/axios';
import './Bids.css';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Tooltip from '@mui/material/Tooltip';
import IconButton from '@mui/material/IconButton';

function PartnerResponse() {
  const navigate = useNavigate();
  const { bidId } = useParams();
  const [selectedPartner, setSelectedPartner] = useState(0);
  const [selectedLOI, setSelectedLOI] = useState('');
  const [partners, setPartners] = useState([]);
  const [bidData, setBidData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [responses, setResponses] = useState({});
  const [savingStatus, setSavingStatus] = useState({});
  const [allResponsesComplete, setAllResponsesComplete] = useState(false);
  const [partnerSettings, setPartnerSettings] = useState({});
  const [error, setError] = useState(null);
  const [responsesInitialized, setResponsesInitialized] = useState(false);
  const [linkData, setLinkData] = useState({});
  const [linkLoading, setLinkLoading] = useState(false);
  const [linkError, setLinkError] = useState('');
  const [copied, setCopied] = useState(false);

  const currentPartner = partners[selectedPartner];

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [bidResponse, partnerResponse] = await Promise.all([
          axios.get(`/api/bids/${bidId}`),
          axios.get(`/api/bids/${bidId}/partner-responses`)
        ]);

        console.log('Bid Response:', bidResponse.data);
        console.log('Partner Response:', partnerResponse.data);

        setBidData(bidResponse.data);
        setPartners(bidResponse.data.partners || []);

        // Initialize responses with existing data
        const existingResponses = partnerResponse.data.responses || {};
        setResponses(existingResponses);
        setPartnerSettings(partnerResponse.data.settings || {});

        // Mark responses as initialized to prevent overwriting
        setResponsesInitialized(true);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [bidId]);

  useEffect(() => {
    if (bidData && bidData.loi && bidData.loi.length > 0) {
      setSelectedLOI(bidData.loi[0]);
    }
  }, [bidData]);

  useEffect(() => {
    if (!bidData || !partners) return;

    const isComplete = partners.every(partner => 
      bidData.loi.every(loi => {
        const responseKey = `${partner.id}-${loi}`;
        const response = responses[responseKey];

        if (!response) return false;

        const allAudiencesComplete = bidData.target_audiences.every(audience => {
          const audienceResponse = response.audiences?.[audience.id];
          if (!audienceResponse) return false;

          const allCountriesComplete = Object.entries(audience.country_samples || {}).every(
            ([country]) => {
              const countryResponse = audienceResponse[country];
              if (!countryResponse) return false;
              
              // Check if either:
              // 1. It's BE/Max (commitment_type is 'be_max')
              // 2. It has a valid commitment value > 0
              const hasValidCommitment = countryResponse.commitment_type === 'be_max' || 
                                       (countryResponse.commitment > 0);
              
              // CPI must always be > 0
              const hasValidCPI = countryResponse.cpi > 0;
              
              return hasValidCommitment && hasValidCPI;
            }
          );

          const hasTimeline = audienceResponse.timeline > 0;

          return allCountriesComplete && hasTimeline;
        });

        return allAudiencesComplete;
      })
    );

    setAllResponsesComplete(isComplete);
  }, [responses, bidData, partners]);

  useEffect(() => {
    if (bidData && partners) {
      const initialStatus = {};
      partners.forEach(partner => {
        bidData.loi.forEach(loi => {
          initialStatus[`${partner.id}-${loi}`] = 'unsaved';
        });
      });
      setSavingStatus(initialStatus);
    }
  }, [bidData, partners]);

  useEffect(() => {
    sessionStorage.setItem('partnerResponsesData', JSON.stringify(responses));
  }, [responses]);

  useEffect(() => {
    if (!responsesInitialized && bidData && partners && bidData.loi) {
      const initialResponses = { ...responses };

      partners.forEach(partner => {
        bidData.loi.forEach(loi => {
          const key = `${partner.id}-${loi}`;
          if (!initialResponses[key]) {
            initialResponses[key] = {
              partner_id: partner.id,
              loi: loi,
              status: 'pending',
              currency: partnerSettings[partner.id]?.currency || 'USD',
              pmf: '',
              audiences: {}
            };
          }

          // Ensure all audiences are present
          bidData.target_audiences.forEach(audience => {
            if (!initialResponses[key].audiences[audience.id]) {
              initialResponses[key].audiences[audience.id] = {
                timeline: '',
                comments: '',
              };
            }
            // Ensure all countries are present for each audience
            Object.entries(audience.country_samples || {}).forEach(([country, sample]) => {
              if (!initialResponses[key].audiences[audience.id][country]) {
                initialResponses[key].audiences[audience.id][country] = {
                  commitment_type: 'fixed',
                  commitment: 0,
                  cpi: 0
                };
              }
            });
          });
        });
      });

      setResponses(initialResponses);
      setResponsesInitialized(true);
    }
  }, [bidData, partners, responsesInitialized, responses, partnerSettings]);

  const handlePartnerChange = (event, newValue) => {
    setSelectedPartner(newValue);
  };

  const handleSave = async () => {
    try {
      // Convert empty PMF to 0 before sending to backend
      const responsesToSend = {};
      Object.entries(responses).forEach(([key, response]) => {
        responsesToSend[key] = {
          ...response,
          pmf: response.pmf === '' ? 0 : response.pmf
        };
      });

      await axios.put(`/api/bids/${bidId}/partner-responses`, {
        responses: responsesToSend
      });
      alert('Partner responses saved successfully');
    } catch (error) {
      console.error('Error saving partner responses:', error);
      alert('Failed to save partner responses');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Validate all responses are complete
      if (!allResponsesComplete) {
        alert('Please complete all partner responses before submitting');
        return;
      }

      // Create complete responses for all LOIs
      const updatedResponses = {};
      partners.forEach(partner => {
        bidData.loi.forEach(loi => {
          const key = `${partner.id}-${loi}`;

          // Create complete response structure for each LOI
          const response = {
            partner_id: partner.id,
            loi: loi,
            status: 'submitted',
            currency: partnerSettings[partner.id]?.currency || 'USD',
            pmf: partnerSettings[partner.id]?.pmf === '' ? 0 : (partnerSettings[partner.id]?.pmf || 0),
            audiences: {}
          };

          // Add audience data for each target audience
          bidData.target_audiences.forEach(audience => {
            const audienceKey = `audience-${audience.id}`;
            response.audiences[audience.id] = {
              ...responses[key]?.audiences?.[audience.id],
              timeline: responses[key]?.audiences?.[audience.id]?.timeline || 0,
              comments: responses[key]?.audiences?.[audience.id]?.comments || '',
            };

            // Add country data for each audience
            Object.entries(audience.country_samples || {}).forEach(([country, sample]) => {
              const countryData = responses[key]?.audiences?.[audience.id]?.[country] || {};
              response.audiences[audience.id][country] = {
                commitment_type: countryData.commitment_type || 'fixed',
                commitment: countryData.commitment_type === 'be_max' ? 0 : (countryData.commitment || 0),
                cpi: countryData.cpi || 0
              };
            });
          });

          updatedResponses[key] = response;
        });
      });

      // Send all responses to backend
      const response = await axios.put(`/api/bids/${bidId}/partner-responses`, {
        responses: updatedResponses
      });

      if (response.status === 200) {
        alert('Partner responses submitted successfully');
        navigate('/bids');
      }
    } catch (error) {
      console.error('Full error details:', error);
      console.error('Error response data:', error.response?.data);
      alert(`Error submitting responses: ${error.response?.data?.error || error.message}`);
    }
  };

  const handleBack = () => {
    if (bidId.startsWith('temp_')) {
      // For new bids, preserve the form data
      navigate('/bids/new', { 
        state: { 
          preserveResponses: true,
          fromEdit: true 
        } 
      });
    } else {
      // For existing bids, go back to edit mode
      navigate(`/bids/edit/${bidId}`, { 
        state: { fromEdit: true } 
      });
    }
  };

  const handlePMFChange = (partnerId, value) => {
    // Allow empty string in UI but store as 0 in settings
    const pmf = value === '' ? '' : parseFloat(value);
    setPartnerSettings(prev => ({
      ...prev,
      [partnerId]: { ...prev[partnerId], pmf }
    }));

    // Update all responses for this partner with new PMF
    setResponses(prev => {
      const updated = { ...prev };
      Object.keys(updated).forEach(key => {
        if (key.startsWith(`${partnerId}-`)) {
          updated[key] = {
            ...updated[key],
            pmf: value === '' ? 0 : parseFloat(value) // Store as 0 in responses when empty
          };
        }
      });
      return updated;
    });
  };

  const handleGenerateLink = async () => {
    setLinkLoading(true);
    setLinkError('');
    try {
      const res = await axios.post(`/api/bids/${bidId}/partners/${currentPartner.id}/generate-link`);
      setLinkData(prev => ({
        ...prev,
        [currentPartner.id]: { link: res.data.link, expiresAt: res.data.expires_at }
      }));
    } catch (err) {
      setLinkError('Failed to generate link');
    }
    setLinkLoading(false);
  };

  // Helper to format time remaining
  const getTimeRemaining = (expiresAt) => {
    if (!expiresAt) return '';
    const expiry = new Date(expiresAt);
    const now = new Date();
    const diffMs = expiry - now;
    if (diffMs <= 0) return 'Expired';
    const diffMins = Math.floor(diffMs / 60000) % 60;
    const diffHrs = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffHrs / 24);
    const hrs = diffHrs % 24;
    if (diffDays > 0) return `${diffDays}d ${hrs}h ${diffMins}m left`;
    if (hrs > 0) return `${hrs}h ${diffMins}m left`;
    return `${diffMins}m left`;
  };

  if (loading) {
    return (
      <div className="partner-response-container">
        <Paper className="partner-response-form">
          <Typography>Loading bid data...</Typography>
        </Paper>
      </div>
    );
  }

  if (error) {
    return (
      <div className="partner-response-container">
        <Paper className="partner-response-form">
          <Typography color="error">Error: {error}</Typography>
          <Button onClick={() => navigate('/bids/new')}>Go Back</Button>
        </Paper>
      </div>
    );
  }

  if (!bidData) {
    return (
      <div className="partner-response-container">
        <Paper className="partner-response-form">
          <Typography>No bid data found</Typography>
          <Button onClick={() => navigate('/bids/new')}>Go Back</Button>
        </Paper>
      </div>
    );
  }

  return (
    <div className="partner-response-container">
      {loading ? (
        <div>Loading...</div>
      ) : error ? (
        <div>Error: {error}</div>
      ) : !bidData || partners.length === 0 ? (
        <div>No data available</div>
      ) : (
        <Paper className="partner-response-form">
          <h2>Partner Response Collection</h2>
          <div className="form-controls">
            <FormControl className="loi-select">
              <Select
                value={selectedLOI}
                onChange={(e) => setSelectedLOI(e.target.value)}
                displayEmpty
                placeholder="Select LOI"
              >
                <MenuItem value="" disabled>Select LOI</MenuItem>
                {bidData.loi.map(loi => (
                  <MenuItem key={loi} value={loi}>{loi} mins</MenuItem>
                ))}
              </Select>
            </FormControl>
          </div>

          {partners.length > 0 && (
            <>
              <Tabs
                value={selectedPartner}
                onChange={handlePartnerChange}
                variant="scrollable"
                scrollButtons="auto"
                className="partner-tabs"
              >
                {partners.map((partner, index) => (
                  <Tab key={partner.id} label={partner.partner_name} />
                ))}
              </Tabs>

              {currentPartner && (
                <div className="partner-tab-content">
                  <div style={{ marginBottom: 16 }}>
                    <Button
                      variant="outlined"
                      color="secondary"
                      onClick={handleGenerateLink}
                      disabled={linkLoading}
                    >
                      {linkLoading ? 'Generating...' : 'Generate Link'}
                    </Button>
                    {linkData[currentPartner.id] && (
                      <div>
                        <strong>Link:</strong> <a href={linkData[currentPartner.id].link} target="_blank" rel="noopener noreferrer">{linkData[currentPartner.id].link}</a>
                        <Tooltip title={copied ? 'Copied!' : 'Copy link'} open={copied} onClose={() => setCopied(false)}>
                          <IconButton size="small" onClick={() => {
                            navigator.clipboard.writeText(linkData[currentPartner.id].link);
                            setCopied(true);
                            setTimeout(() => setCopied(false), 1200);
                          }}>
                            <ContentCopyIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <br />
                        <strong>Expires At:</strong> {getTimeRemaining(linkData[currentPartner.id].expiresAt)}
                      </div>
                    )}
                    {linkError && <div style={{ color: 'red' }}>{linkError}</div>}
                  </div>
                  <div className="partner-settings">
                    <FormControl className="currency-select">
                      <Select
                        value={partnerSettings[currentPartner.id]?.currency || 'USD'}
                        onChange={(e) => setPartnerSettings(prev => ({
                          ...prev,
                          [currentPartner.id]: { ...prev[currentPartner.id], currency: e.target.value }
                        }))}
                        size="small"
                      >
                        <MenuItem value="USD">USD</MenuItem>
                        <MenuItem value="EUR">EUR</MenuItem>
                        <MenuItem value="GBP">GBP</MenuItem>
                      </Select>
                    </FormControl>
                    <TextField
                      label="PMF"
                      type="number"
                      size="small"
                      className="pmf-input"
                      inputProps={{ min: 0, step: 0.1 }}
                      value={partnerSettings[currentPartner.id]?.pmf || ''}
                      onChange={(e) => handlePMFChange(currentPartner.id, e.target.value)}
                    />
                  </div>

                  {bidData.target_audiences.map((audience, audienceIndex) => (
                    <div key={audience.id} className="audience-section">
                      <Typography variant="subtitle1" className="audience-title" sx={{ fontWeight: 'bold' }}>
                        Audience: {audience.ta_category} - {audience.broader_category} - {audience.mode} - IR {audience.ir}%
                      </Typography>

                      <TableContainer>
                        <Table>
                          <TableHead>
                            <TableRow>
                              <TableCell>Country</TableCell>
                              <TableCell align="right">Required</TableCell>
                              <TableCell align="right">Commitment</TableCell>
                              <TableCell align="right">CPI</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {Object.entries(audience.country_samples || {}).map(([country, sample], idx) => (
                              <TableRow key={`${audience.id}-${country}`}>
                                <TableCell>{country}</TableCell>
                                <TableCell align="right">{sample.is_best_efforts ? "BE/Max" : sample.sample_size}</TableCell>
                                <TableCell align="right">
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'flex-end' }}>
                                    <FormControl size="small">
                                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                        <Typography variant="body2" sx={{ mr: 1 }}>BE/Max</Typography>
                                        <input
                                          type="checkbox"
                                          checked={responses[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id]?.[country]?.commitment_type === 'be_max'}
                                          onChange={(e) => {
                                            const isBeMax = e.target.checked;
                                            setResponses(prev => ({
                                              ...prev,
                                              [`${currentPartner.id}-${selectedLOI}`]: {
                                                ...prev[`${currentPartner.id}-${selectedLOI}`],
                                                partner_id: currentPartner.id,
                                                loi: selectedLOI,
                                                audiences: {
                                                  ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences,
                                                  [audience.id]: {
                                                    ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id],
                                                    [country]: {
                                                      ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id]?.[country],
                                                      commitment_type: isBeMax ? 'be_max' : 'fixed',
                                                      commitment: 0  // Always set to 0 for BE/Max
                                                    }
                                                  }
                                                }
                                              }
                                            }));
                                          }}
                                        />
                                      </Box>
                                    </FormControl>
                                    <TextField
                                      type="number"
                                      size="small"
                                      inputProps={{ min: 0 }}
                                      value={responses[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id]?.[country]?.commitment || ''}
                                      onChange={(e) => {
                                        const value = e.target.value === '' ? 0 : parseFloat(e.target.value);  // Convert empty string to 0
                                        setResponses(prev => ({
                                          ...prev,
                                          [`${currentPartner.id}-${selectedLOI}`]: {
                                            ...prev[`${currentPartner.id}-${selectedLOI}`],
                                            partner_id: currentPartner.id,
                                            loi: selectedLOI,
                                            audiences: {
                                              ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences,
                                              [audience.id]: {
                                                ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id],
                                                [country]: {
                                                  ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id]?.[country],
                                                  commitment: value
                                                }
                                              }
                                            }
                                          }
                                        }));
                                      }}
                                      disabled={responses[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id]?.[country]?.commitment_type === 'be_max'}
                                    />
                                  </Box>
                                </TableCell>
                                <TableCell align="right">
                                  <TextField
                                    type="number"
                                    size="small"
                                    inputProps={{ min: 0 }}
                                    value={responses[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id]?.[country]?.cpi || ''}
                                    onChange={(e) => {
                                      const value = parseFloat(e.target.value);
                                      setResponses(prev => ({
                                        ...prev,
                                        [`${currentPartner.id}-${selectedLOI}`]: {
                                          ...prev[`${currentPartner.id}-${selectedLOI}`],
                                          partner_id: currentPartner.id,
                                          loi: selectedLOI,
                                          audiences: {
                                            ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences,
                                            [audience.id]: {
                                              ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id],
                                              [country]: {
                                                ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id]?.[country],
                                                cpi: value
                                              }
                                            }
                                          }
                                        }
                                      }));
                                    }}
                                  />
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>

                      <TextField
                        fullWidth
                        type="number"
                        label="Bid Timeline (days)"
                        className="timeline-field"
                        value={responses[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id]?.timeline || ''}
                        onChange={(e) => setResponses(prev => ({
                          ...prev,
                          [`${currentPartner.id}-${selectedLOI}`]: {
                            ...prev[`${currentPartner.id}-${selectedLOI}`],
                            audiences: {
                              ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences,
                              [audience.id]: {
                                ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id],
                                timeline: parseFloat(e.target.value)
                              }
                            }
                          }
                        }))}
                      />
                      <TextField
                        fullWidth
                        multiline
                        rows={3}
                        label="Comments"
                        className="comments-field"
                        value={responses[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id]?.comments || ''}
                        onChange={(e) => setResponses(prev => ({
                          ...prev,
                          [`${currentPartner.id}-${selectedLOI}`]: {
                            ...prev[`${currentPartner.id}-${selectedLOI}`],
                            audiences: {
                              ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences,
                              [audience.id]: {
                                ...prev[`${currentPartner.id}-${selectedLOI}`]?.audiences?.[audience.id],
                                comments: e.target.value
                              }
                            }
                          }
                        }))}
                      />
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          <div className="form-actions">
            <Button onClick={handleBack}>BACK</Button>
            {currentPartner && (
              <Button 
                onClick={() => handleSave()}
                disabled={!selectedLOI}
                color={savingStatus[`${currentPartner.id}-${selectedLOI}`] === 'error' ? 'error' : 'primary'}
                variant={savingStatus[`${currentPartner.id}-${selectedLOI}`] === 'saved' ? 'outlined' : 'contained'}
              >
                {!selectedLOI ? 'Select LOI' :
                  savingStatus[`${currentPartner.id}-${selectedLOI}`] === 'saving' ? 'Saving...' : 
                  savingStatus[`${currentPartner.id}-${selectedLOI}`] === 'saved' ? 'Saved ✓' : 
                  savingStatus[`${currentPartner.id}-${selectedLOI}`] === 'error' ? 'Try Again' : 
                  'Save'}
              </Button>
            )}
            <Button 
              variant="contained" 
              color="primary"
              onClick={handleSubmit}
              disabled={!allResponsesComplete}
            >
              SUBMIT
            </Button>
          </div>
        </Paper>
      )}
    </div>
  );
}

export default PartnerResponse;