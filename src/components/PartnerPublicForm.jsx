import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Paper,
  Typography,
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
  Box
} from '@mui/material';
import axios from '../api/axios';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import DownloadIcon from '@mui/icons-material/Download';

function formToCSV({ data, form, pmf, currency }) {
  if (!data || !form) return '';
  const rows = [
    [
      'Bid Number', 'Project Name', 'Project Requirement', 'Partner Name', 'LOI', 'Audience', 'IR', 'Country', 'BE/Max', 'Commitment', 'CPI', 'Timeline', 'Comments'
    ]
  ];
  for (const loi of data.lois || []) {
    for (const aud of data.audiences || []) {
      const audData = form[loi]?.[aud.id];
      if (!audData) continue;
      for (const country of Object.keys(audData.countries || {})) {
        const c = audData.countries[country];
        rows.push([
          data.bid?.bid_number || '',
          data.bid?.study_name || '',
          data.bid?.project_requirement || '',
          data.partner?.partner_name || '',
          loi,
          aud.audience_name || '',
          aud.ir || '',
          country,
          c.commitment_type === 'be_max' ? 'Yes' : '',
          c.commitment,
          c.cpi,
          audData.timeline,
          audData.comments
        ]);
      }
    }
  }
  return rows.map(r => r.map(x => `"${(x ?? '').toString().replace(/"/g, '""')}"`).join(',')).join('\r\n');
}

function downloadCSV(csv, filename) {
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

function PartnerPublicForm() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [form, setForm] = useState({});
  const [selectedLOI, setSelectedLOI] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [pmf, setPMF] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await axios.get(`/api/partner-link/${token}`);
        setData(res.data);
        // Find the first LOI's partner_response for initial PMF/currency
        let initialPMF = '';
        let initialCurrency = 'USD';
        if (res.data.lois && res.data.lois.length > 0) {
          setSelectedLOI(res.data.lois[0]);
          const pr = (res.data.partner_responses || []).find(r => r.loi === res.data.lois[0]);
          if (pr) {
            initialPMF = pr.pmf ?? '';
            initialCurrency = pr.currency ?? 'USD';
          }
        }
        setPMF(initialPMF);
        setCurrency(initialCurrency);
        // Sort audiences by ID to maintain consistent database order, then renumber sequentially
        const sortedAudiences = (res.data.audiences || []).sort((a, b) => (a.id || 0) - (b.id || 0));
        
        // Renumber audiences sequentially based on their sorted database ID order
        const processedAudiences = sortedAudiences.map((audience, index) => ({
          ...audience,
          audience_name: `Audience - ${index + 1}`,
        }));
        
        // Update the data with processed audiences
        res.data.audiences = processedAudiences;

        // Initialize form state by LOI, pre-filling with existing responses if available
        const initialForm = {};
        (res.data.lois || []).forEach(loi => {
          initialForm[loi] = {};
          processedAudiences.forEach(aud => {
            const pr = (res.data.partner_responses || []).find(r => r.loi === loi);
            const parList = (res.data.partner_audience_responses || []).filter(par => par.partner_response_id === pr?.id && par.audience_id === aud.id);
            const timeline = parList.length > 0 ? (parList[0].timeline_days ?? '') : '';
            const comments = parList.length > 0 ? (parList[0].comments ?? '') : '';
            initialForm[loi][aud.id] = {
              timeline: timeline,
              comments: comments,
              countries: {}
            };
            (res.data.country_samples || []).filter(cs => cs.audience_id === aud.id).forEach(cs => {
              const par = parList.find(p => p.country === cs.country);
              initialForm[loi][aud.id].countries[cs.country] = {
                commitment_type: par?.commitment_type === 'be_max' || cs.is_best_efforts ? 'be_max' : 'fixed',
                commitment: par ? par.commitment ?? '' : '',
                cpi: par ? par.cpi ?? '' : '',
              };
            });
          });
        });
        setForm(initialForm);
      } catch (err) {
        setError('Invalid or expired link.');
      }
      setLoading(false);
    };
    fetchData();
  }, [token]);

  // When selectedLOI changes, update PMF and currency from the partner_response for that LOI
  useEffect(() => {
    if (!data || !selectedLOI) return;
    const pr = (data.partner_responses || []).find(r => r.loi === selectedLOI);
    setPMF(pr?.pmf ?? '');
    setCurrency(pr?.currency ?? 'USD');
  }, [selectedLOI, data]);

  const handleCountryChange = (audId, country, field, value) => {
    setForm(prev => ({
      ...prev,
      [selectedLOI]: {
        ...prev[selectedLOI],
        [audId]: {
          ...prev[selectedLOI][audId],
          countries: {
            ...prev[selectedLOI][audId].countries,
            [country]: {
              ...prev[selectedLOI][audId].countries[country],
              [field]: value
            }
          }
        }
      }
    }));
  };

  const handleTimelineChange = (audId, value) => {
    setForm(prev => ({
      ...prev,
      [selectedLOI]: {
        ...prev[selectedLOI],
        [audId]: {
          ...prev[selectedLOI][audId],
          timeline: value
        }
      }
    }));
  };

  const handleCommentsChange = (audId, value) => {
    setForm(prev => ({
      ...prev,
      [selectedLOI]: {
        ...prev[selectedLOI],
        [audId]: {
          ...prev[selectedLOI][audId],
          comments: value
        }
      }
    }));
  };

  const handleSave = async () => {
    // TODO: Implement save logic (optional for public form)
    setSuccess(true);
    setTimeout(() => setSuccess(false), 2000);
  };

  // Helper to check if all required fields are filled for all LOIs
  const isFormComplete = () => {
    if (pmf === '' || pmf === null || pmf === undefined || !currency) return false;
    for (const loi in form) {
      const loiData = form[loi];
      if (!loiData) return false;
      for (const audId in loiData) {
        const aud = loiData[audId];
        if (!aud.timeline || !aud.comments) return false;
        for (const country in aud.countries) {
          const c = aud.countries[country];
          if (c.commitment_type !== 'be_max' && (c.commitment === '' || c.commitment === null || c.commitment === undefined)) return false;
          if (!c.cpi && c.cpi !== 0) return false;
        }
      }
    }
    return true;
  };

  const handleDownloadCSV = () => {
    const csv = formToCSV({ data, form, pmf, currency });
    const filename = `Partner_Response_${data?.bid?.bid_number || ''}_${data?.partner?.partner_name || ''}.csv`;
    downloadCSV(csv, filename);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setSubmitError('');
    try {
      const res = await axios.post(`/api/partner-link/${token}`, {
        form,
        pmf,
        currency
      });
      if (res.data && res.data.success) {
        // Download CSV before redirect
        handleDownloadCSV();
        navigate('/partner-response/success');
      } else {
        setSubmitError(res.data.error || 'Submission failed.');
      }
    } catch (err) {
      setSubmitError(err.response?.data?.error || 'Submission failed.');
    }
    setSubmitting(false);
  };

  const handleDialogClose = () => {
    setShowSuccessDialog(false);
    window.close();
  };

  if (loading) return <div style={{ padding: 32 }}>Loading...</div>;
  if (error) return <div style={{ padding: 32, color: 'red' }}>{error}</div>;
  if (!data) return null;

  return (
    <div style={{ maxWidth: 900, margin: '32px auto', position: 'relative' }}>
      <Button
        variant="outlined"
        startIcon={<DownloadIcon />}
        onClick={handleDownloadCSV}
        style={{ position: 'absolute', top: 16, right: 16, zIndex: 2 }}
      >
        Download CSV
      </Button>
      <Paper style={{ padding: 32 }} elevation={3}>
        <Typography variant="h4" align="center" gutterBottom>Partner Response Form</Typography>
        <Box mb={2}>
          <Typography variant="subtitle1"><strong>Bid Number:</strong> {data.bid?.bid_number || '-'}</Typography>
          <Typography variant="subtitle1"><strong>Project Name:</strong> {data.bid?.study_name || '-'}</Typography>
          <Typography variant="subtitle1"><strong>Project Requirement:</strong> {data.bid?.project_requirement || '-'}</Typography>
        </Box>
        <Typography variant="h6" align="center" gutterBottom>
          Partner: {data.partner?.partner_name || '-'}
        </Typography>
        <Typography variant="subtitle1" align="center" gutterBottom>
          Bid: {data.bid?.study_name || data.bid?.bid_number || '-'}
        </Typography>
        {data.lois && data.lois.length > 1 && (
          <Box mb={2} display="flex" justifyContent="center">
            <FormControl size="small">
              <Select
                value={selectedLOI}
                onChange={e => setSelectedLOI(e.target.value)}
              >
                {data.lois.map(loi => (
                  <MenuItem key={loi} value={loi}>LOI: {loi}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        )}
        <Box mb={2} display="flex" gap={2} alignItems="center" justifyContent="center">
          <FormControl size="small">
            <Select value={currency} onChange={e => setCurrency(e.target.value)}>
              <MenuItem value="USD">USD</MenuItem>
              <MenuItem value="EUR">EUR</MenuItem>
              <MenuItem value="GBP">GBP</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="PMF"
            type="number"
            size="small"
            value={pmf}
            onChange={e => setPMF(e.target.value)}
            inputProps={{ min: 0, step: 0.1 }}
          />
        </Box>
        <form onSubmit={handleSubmit}>
          {(data.audiences || []).map(aud => (
            <Box key={aud.id} mb={4} p={2} style={{ background: '#fafafa', borderRadius: 8 }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                {aud.audience_name} ({aud.ta_category})
              </Typography>
              <Typography variant="body2" gutterBottom>
                Broader Category: {aud.broader_category} | Mode: {aud.mode} | IR: {aud.ir}%
              </Typography>
              {aud.exact_ta_definition && (
                <Typography variant="body2" gutterBottom sx={{ fontStyle: 'italic', mb: 2 }}>
                  <strong>Exact TA Definition:</strong> {aud.exact_ta_definition}
                </Typography>
              )}
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Country</TableCell>
                      <TableCell>Required</TableCell>
                      <TableCell>BE/Max</TableCell>
                      <TableCell>Commitment</TableCell>
                      <TableCell>CPI</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(data.country_samples || []).filter(cs => cs.audience_id === aud.id).map(cs => (
                      <TableRow key={cs.id}>
                        <TableCell>{cs.country}</TableCell>
                        <TableCell>{cs.is_best_efforts ? 'BE/Max' : cs.sample_size}</TableCell>
                        <TableCell>
                          <input
                            type="checkbox"
                            checked={form[selectedLOI]?.[aud.id]?.countries?.[cs.country]?.commitment_type === 'be_max'}
                            onChange={e => handleCountryChange(aud.id, cs.country, 'commitment_type', e.target.checked ? 'be_max' : 'fixed')}
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            type="number"
                            size="small"
                            value={form[selectedLOI]?.[aud.id]?.countries?.[cs.country]?.commitment || ''}
                            onChange={e => handleCountryChange(aud.id, cs.country, 'commitment', e.target.value)}
                            disabled={form[selectedLOI]?.[aud.id]?.countries?.[cs.country]?.commitment_type === 'be_max'}
                            inputProps={{ min: 0 }}
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            type="number"
                            size="small"
                            value={form[selectedLOI]?.[aud.id]?.countries?.[cs.country]?.cpi || ''}
                            onChange={e => handleCountryChange(aud.id, cs.country, 'cpi', e.target.value)}
                            inputProps={{ min: 0 }}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              <Box mt={2} mb={1}>
                <TextField
                  fullWidth
                  type="number"
                  label="Bid Timeline (days)"
                  value={form[selectedLOI]?.[aud.id]?.timeline || ''}
                  onChange={e => handleTimelineChange(aud.id, e.target.value)}
                />
              </Box>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Comments"
                value={form[selectedLOI]?.[aud.id]?.comments || ''}
                onChange={e => handleCommentsChange(aud.id, e.target.value)}
              />
            </Box>
          ))}
          <Box display="flex" gap={2} justifyContent="center" mt={4}>
            <Button variant="outlined" onClick={handleSave} disabled={submitting}>Save</Button>
            <Button variant="contained" color="primary" type="submit" disabled={submitting || !isFormComplete()}>
              {submitting ? 'Submitting...' : 'Submit'}
            </Button>
          </Box>
          {success && <Typography color="success.main" align="center" mt={2}>Saved!</Typography>}
          {submitError && <Typography color="error" align="center" mt={2}>{submitError}</Typography>}
        </form>
      </Paper>
      <Dialog open={showSuccessDialog} onClose={handleDialogClose}>
        <DialogTitle>Success</DialogTitle>
        <DialogContent>
          <Typography>Your response has been saved successfully.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose} color="primary" autoFocus>OK</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default PartnerPublicForm; 