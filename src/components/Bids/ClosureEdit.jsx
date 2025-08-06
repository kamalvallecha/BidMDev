import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Stack,
  MenuItem,
  Alert
} from '@mui/material';
import './Bids.css';
import axios from '../../api/axios';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { parseISO } from 'date-fns';

function ClosureEdit() {
  const { bidId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [selectedPartner, setSelectedPartner] = useState('');
  const [selectedLOI, setSelectedLOI] = useState('');
  const [audienceData, setAudienceData] = useState([]);
  const [bidData, setBidData] = useState({
    partners: {},
    audiences: {}
  });
  const [formData, setFormData] = useState({});
  const [hasAllocation, setHasAllocation] = useState({});

  useEffect(() => {
    fetchBidDetails();
    // Load saved form data from session storage
    const savedFormData = sessionStorage.getItem(`bidClosure_${bidId}`);
    if (savedFormData) {
      setFormData(JSON.parse(savedFormData));
    }
  }, [bidId]);

  // Save form data to session storage whenever it changes
  useEffect(() => {
    if (Object.keys(formData).length > 0) {
      sessionStorage.setItem(`bidClosure_${bidId}`, JSON.stringify(formData));
    }
  }, [formData, bidId]);

  useEffect(() => {
    const fetchAudienceData = async () => {
      if (selectedPartner && selectedLOI) {
        try {
          const response = await axios.get(`/api/bids/${bidId}/audiences`, {
            params: { partner: selectedPartner, loi: selectedLOI }
          });
          
          // Filter out audiences where all countries have allocation = 0
          const filteredAudienceData = response.data.filter(audience => {
            // Check if at least one country has allocation > 0
            return audience.countries.some(country => country.allocation > 0);
          });

          // For each audience, filter out countries with allocation = 0
          const processedAudienceData = filteredAudienceData.map(audience => ({
            ...audience,
            countries: audience.countries.filter(country => country.allocation > 0)
          }));
          
          setAudienceData(processedAudienceData);
          
          // Update formData with fetched values
          const newFormData = { ...formData };
          processedAudienceData.forEach(audience => {
            // Set field close date
            newFormData[`${audience.id}_${selectedPartner}_${selectedLOI}_field_close_date`] = audience.field_close_date;
            
            // Set metrics
            const metricsKey = `metrics_${audience.id}_${selectedPartner}_${selectedLOI}`;
            newFormData[metricsKey] = audience.metrics;
            
            // Set n_delivered and quality_rejects values for each country
            audience.countries.forEach(country => {
              newFormData[`${audience.id}_${country.name}`] = {
                delivered: country.delivered,
                qualityRejects: country.quality_rejects
              };
            });
          });
          
          setFormData(newFormData);
          console.log('Updated form data:', newFormData); // Debug log
          
        } catch (error) {
          console.error('Error fetching audience data:', error);
        }
      }
    };

    fetchAudienceData();
  }, [selectedPartner, selectedLOI, bidId]);

  useEffect(() => {
    // Check if partner has any allocations
    const checkPartnerAllocations = (data) => {
      const allocations = {};
      Object.values(data.audiences || {}).forEach(audience => {
        Object.entries(audience.countries || {}).forEach(([_, countryData]) => {
          if (countryData.allocation > 0) {
            // If any country has allocation > 0, mark the partner as having allocation
            const partnerName = selectedPartner;
            allocations[partnerName] = true;
          }
        });
      });
      setHasAllocation(allocations);
    };

    if (bidData) {
      checkPartnerAllocations(bidData);
    }
  }, [bidData, selectedPartner]);

  const fetchBidDetails = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/bids/closure/${bidId}`);
      setBidData(response.data);
      
      // Set initial partner and LOI
      const partners = Object.keys(response.data.partners);
      if (partners.length > 0) {
        const firstPartner = partners[0];
        setSelectedPartner(firstPartner);
        
        const lois = response.data.partners[firstPartner].lois;
        if (lois.length > 0) {
          setSelectedLOI(lois[0]);
        }
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching bid details:', error);
      setLoading(false);
    }
  };

  const handleDeliveredChange = (audienceId, country, value) => {
    setFormData(prev => ({
      ...prev,
      [`${audienceId}_${country}`]: {
        ...prev[`${audienceId}_${country}`],
        delivered: value
      }
    }));
  };

  const handleQualityRejectsChange = (audienceId, country, value) => {
    setFormData(prev => ({
      ...prev,
      [`${audienceId}_${country}`]: {
        ...prev[`${audienceId}_${country}`],
        qualityRejects: value
      }
    }));
  };

  const handleMetricsChange = (audienceId, field, value) => {
    const metricsKey = `metrics_${audienceId}_${selectedPartner}_${selectedLOI}`;
    setFormData(prev => ({
      ...prev,
      [metricsKey]: {
        ...prev[metricsKey],
        [field]: value
      }
    }));
  };

  const handleFieldCloseDateChange = (audienceId, date) => {
    setFormData(prev => ({
      ...prev,
      [`${audienceId}_${selectedPartner}_${selectedLOI}_field_close_date`]: date ? date.toISOString().split('T')[0] : null
    }));
  };

  const handleSave = async (submitAfterSave = false) => {
    try {
      console.log('Selected Partner:', selectedPartner);
      console.log('Selected LOI:', selectedLOI);
      
      const response = await axios.put(`/api/bids/${bidId}/closure`, {
        partner: selectedPartner,
        loi: selectedLOI,
        data: formData,
        audienceData: audienceData.map(audience => {
          const metricsKey = `metrics_${audience.id}_${selectedPartner}_${selectedLOI}`;
          
          // Get n_delivered and quality_rejects values for each country
          const countries = audience.countries.map(country => ({
            name: country.name,
            delivered: Number(formData[`${audience.id}_${country.name}`]?.delivered || country.delivered || 0),
            qualityRejects: Number(formData[`${audience.id}_${country.name}`]?.qualityRejects || country.quality_rejects || 0)
          }));

          const data = {
            id: audience.id,
            field_close_date: formData[`${audience.id}_${selectedPartner}_${selectedLOI}_field_close_date`],
            countries: countries,
            metrics: {
              finalLOI: formData[metricsKey]?.finalLOI,
              finalIR: formData[metricsKey]?.finalIR,
              finalTimeline: formData[metricsKey]?.finalTimeline,
              qualityRejects: formData[metricsKey]?.qualityRejects,
              communication: formData[metricsKey]?.communication,
              engagement: formData[metricsKey]?.engagement,
              problemSolving: formData[metricsKey]?.problemSolving,
              additionalFeedback: formData[metricsKey]?.additionalFeedback
            }
          };
          console.log(`Saving data for audience ${audience.id}:`, data);
          return data;
        })
      });
      
      if (submitAfterSave) {
        alert('Data submitted successfully!');
        sessionStorage.removeItem(`bidClosure_${bidId}`);
        navigate('/closure');
      } else {
        alert('Data saved successfully!');
      }
    } catch (error) {
      console.error('Error saving closure data:', error);
      alert('Error saving data. Please try again.');
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="closure-edit-container">
      <Typography variant="h4" gutterBottom>
        Bid Closure
      </Typography>

      {/* Partner Selection */}
      <ToggleButtonGroup
        value={selectedPartner}
        exclusive
        onChange={(e, newPartner) => {
          if (newPartner) setSelectedPartner(newPartner);
        }}
      >
        {Object.keys(bidData?.partners || {}).map(partner => (
          <ToggleButton key={partner} value={partner}>
            {partner}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>

      {/* LOI Selection */}
      <Box sx={{ mt: 2, mb: 2 }}>
        <Typography sx={{ mb: 1 }}>Select LOI:</Typography>
        <ToggleButtonGroup
          value={selectedLOI}
          exclusive
          onChange={(e, newLOI) => {
            if (newLOI) setSelectedLOI(newLOI);
          }}
        >
          {bidData?.partners[selectedPartner]?.lois.map(loi => (
            <ToggleButton key={loi} value={loi}>
              {loi} MIN
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Box>

      {/* Show warning if partner has no allocations for selected LOI */}
      {selectedPartner && selectedLOI && 
       !bidData?.partners[selectedPartner]?.has_allocation[selectedLOI] ? (
          <Alert 
              severity="warning" 
              sx={{ 
                  mt: 2, 
                  mb: 2,
                  backgroundColor: '#fff3e0',
                  border: '1px solid #ffb74d',
                  '& .MuiAlert-icon': {
                      color: '#f57c00'
                  }
              }}
          >
              No respondents allocated to {selectedPartner} for {selectedLOI} MIN LOI
          </Alert>
      ) : (
          <Typography sx={{ mt: 2, mb: 2, color: 'text.secondary' }}>
              Currently viewing: {selectedPartner} with {selectedLOI} LOI
          </Typography>
      )}

      {/* Audience Details */}
      {audienceData.map((audience, index) => (
        <Box key={audience.id} sx={{ mb: 4 }}>
          <Typography variant="h6" className="audience-title" sx={{ fontWeight: 'bold' }}>
            Audience: {audience.ta_category} - {audience.broader_category} - {audience.mode} - IR {audience.ir}%
          </Typography>

          {/* Add Field Close Date here */}
          <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography>Field Close Date:</Typography>
            <DatePicker
              value={formData[`${audience.id}_${selectedPartner}_${selectedLOI}_field_close_date`] ? 
                parseISO(formData[`${audience.id}_${selectedPartner}_${selectedLOI}_field_close_date`]) : null}
              onChange={(date) => handleFieldCloseDateChange(audience.id, date)}
              renderInput={(params) => <TextField {...params} size="small" />}
              format="MM/dd/yyyy"
            />
          </Box>

          <TableContainer component={Paper} sx={{ mt: 3 }}>
            <Table>
              <TableHead>
                <TableRow sx={{ bgcolor: '#7c4dff' }}>
                  <TableCell sx={{ color: 'white' }}>Country</TableCell>
                  <TableCell sx={{ color: 'white' }}>Required</TableCell>
                  <TableCell sx={{ color: 'white' }}>Allocation</TableCell>
                  <TableCell sx={{ color: 'white' }}>N Delivered</TableCell>
                  <TableCell sx={{ color: 'white' }}>Quality Rejects</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {audience.countries.map((country) => (
                  <TableRow key={country.name}>
                    <TableCell>{country.name}</TableCell>
                    <TableCell>{country.required}</TableCell>
                    <TableCell>{country.allocation}</TableCell>
                    <TableCell>
                      <TextField
                        size="small"
                        type="number"
                        value={formData[`${audience.id}_${country.name}`]?.delivered ?? country.delivered ?? ''}
                        onChange={(e) => handleDeliveredChange(audience.id, country.name, e.target.value)}
                        sx={{ width: 100 }}
                      />
                    </TableCell>
                    <TableCell>
                      <TextField
                        size="small"
                        type="number"
                        value={formData[`${audience.id}_${country.name}`]?.qualityRejects ?? country.quality_rejects ?? ''}
                        onChange={(e) => handleQualityRejectsChange(audience.id, country.name, e.target.value)}
                        sx={{ width: 100 }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Partner Metrics - Now using partner-specific keys */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>Partner Metrics</Typography>
            <Stack direction="row" spacing={2}>
              <TextField
                label="Final LOI (mins)"
                size="small"
                type="number"
                value={formData[`metrics_${audience.id}_${selectedPartner}_${selectedLOI}`]?.finalLOI ?? ''}
                onChange={(e) => handleMetricsChange(audience.id, 'finalLOI', e.target.value)}
              />
              <TextField
                label="Final IR (%)"
                size="small"
                type="number"
                value={formData[`metrics_${audience.id}_${selectedPartner}_${selectedLOI}`]?.finalIR ?? ''}
                onChange={(e) => handleMetricsChange(audience.id, 'finalIR', e.target.value)}
              />
              <TextField
                label="Final Timeline (days)"
                size="small"
                type="number"
                value={formData[`metrics_${audience.id}_${selectedPartner}_${selectedLOI}`]?.finalTimeline ?? ''}
                onChange={(e) => handleMetricsChange(audience.id, 'finalTimeline', e.target.value)}
              />
            </Stack>

            <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
              <TextField
                label="Quality Rejects"
                size="small"
                type="number"
                value={(() => {
                  // Calculate sum of quality rejects from all countries
                  const sum = audience.countries.reduce((total, country) => {
                    const qualityRejects = formData[`${audience.id}_${country.name}`]?.qualityRejects ?? country.quality_rejects ?? 0;
                    return total + (parseInt(qualityRejects) || 0);
                  }, 0);
                  return sum;
                })()}
                InputProps={{
                  readOnly: true,
                }}
                helperText="Auto-calculated sum from all countries"
              />
              <TextField
                select
                label="Communication (1-5)"
                size="small"
                value={formData[`metrics_${audience.id}_${selectedPartner}_${selectedLOI}`]?.communication ?? ''}
                onChange={(e) => handleMetricsChange(audience.id, 'communication', e.target.value)}
                sx={{ width: 200 }}
              >
                {[...Array(5)].map((_, i) => (
                  <MenuItem key={i+1} value={i+1}>{i+1}</MenuItem>
                ))}
              </TextField>
              <TextField
                select
                label="Engagement (1-5)"
                size="small"
                value={formData[`metrics_${audience.id}_${selectedPartner}_${selectedLOI}`]?.engagement ?? ''}
                onChange={(e) => handleMetricsChange(audience.id, 'engagement', e.target.value)}
                sx={{ width: 200 }}
              >
                {[...Array(5)].map((_, i) => (
                  <MenuItem key={i+1} value={i+1}>{i+1}</MenuItem>
                ))}
              </TextField>
              <TextField
                select
                label="Problem Solving (1-5)"
                size="small"
                value={formData[`metrics_${audience.id}_${selectedPartner}_${selectedLOI}`]?.problemSolving ?? ''}
                onChange={(e) => handleMetricsChange(audience.id, 'problemSolving', e.target.value)}
                sx={{ width: 200 }}
              >
                {[...Array(5)].map((_, i) => (
                  <MenuItem key={i+1} value={i+1}>{i+1}</MenuItem>
                ))}
              </TextField>
            </Stack>

            <TextField
              sx={{ mt: 2 }}
              label="Additional Feedback"
              multiline
              rows={4}
              fullWidth
              value={formData[`metrics_${audience.id}_${selectedPartner}_${selectedLOI}`]?.additionalFeedback ?? ''}
              onChange={(e) => handleMetricsChange(audience.id, 'additionalFeedback', e.target.value)}
            />
          </Box>
        </Box>
      ))}

      {/* Action Buttons */}
      <Box sx={{ mt: 4 }}>
        <Button 
          variant="contained" 
          color="primary"
          sx={{ mr: 2 }}
          onClick={() => handleSave(true)} // true means submit after save
        >
          Submit
        </Button>
        <Button 
          variant="contained" 
          color="secondary"
          sx={{ mr: 2 }}
          onClick={() => handleSave(false)} // false means just save
        >
          Save
        </Button>
        <Button 
          variant="outlined"
          onClick={() => {
            if (window.confirm('Are you sure? Any unsaved changes will be lost.')) {
              sessionStorage.removeItem(`bidClosure_${bidId}`);
              navigate('/bids');
            }
          }}
        >
          Cancel
        </Button>
      </Box>
    </div>
  );
}

export default ClosureEdit; 