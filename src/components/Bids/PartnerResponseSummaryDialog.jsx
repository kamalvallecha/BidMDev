import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Stack,
  CircularProgress,
  Box
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from '../../api/axios';
import { green } from '@mui/material/colors';
import dayjs from 'dayjs';

const statusColor = {
  complete: 'success',
  partial: 'warning',
  missing: 'error',
  draft: 'default',
  'not started': 'default',
};

function PartnerResponseSummaryDialog({ open, onClose, bidId }) {
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const [selectedLoi, setSelectedLoi] = useState(null);
  const [expandedPartner, setExpandedPartner] = useState(null);

  useEffect(() => {
    if (open && bidId) {
      setLoading(true);
      setError(null);
      axios.get(`/api/bids/${bidId}/partner-responses-summary`)
        .then(res => {
          setSummary(res.data);
          if (res.data.lois && res.data.lois.length > 0) {
            setSelectedLoi(res.data.lois[0]);
          }
        })
        .catch(err => {
          setError('Failed to load partner responses');
        })
        .finally(() => setLoading(false));
    }
  }, [open, bidId]);

  const handleAccordionChange = (partnerId) => {
    setExpandedPartner(expandedPartner === partnerId ? null : partnerId);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Partner Response Summary</DialogTitle>
      <DialogContent>
        {loading ? (
          <Stack alignItems="center" py={4}><CircularProgress /></Stack>
        ) : error ? (
          <Typography color="error">{error}</Typography>
        ) : summary && summary.partners && summary.partners.length > 0 ? (
          <>
            <Stack direction="row" spacing={2} mb={2} alignItems="center">
              <Typography variant="subtitle2">
                Bid #{summary.bid_number}: {summary.study_name}
                <Box component="span" ml={2}>
                  <Chip label={`Complete: ${summary.summary_counts.complete}`} size="small" sx={{ bgcolor: green[100], color: green[800], fontWeight: 600, ml: 1 }} />
                  <Chip label={`Partial: ${summary.summary_counts.partial}`} size="small" sx={{ ml: 1 }} />
                  <Chip label={`Not Started: ${summary.summary_counts.not_started}`} size="small" sx={{ ml: 1 }} />
                </Box>
              </Typography>
              <Box flex={1} />
              <Stack direction="row" spacing={1}>
                {summary.lois.map(loi => (
                  <Button
                    key={loi}
                    variant={selectedLoi === loi ? "contained" : "outlined"}
                    onClick={() => setSelectedLoi(loi)}
                    size="small"
                  >
                    {loi} min
                  </Button>
                ))}
              </Stack>
            </Stack>
            <Box>
              {summary.partners.map((partner) => {
                const loiData = partner.lois.find(l => l.loi === selectedLoi);
                const isComplete = loiData?.status === 'complete';
                return (
                  <Accordion
                    key={partner.partner_id}
                    expanded={expandedPartner === partner.partner_id}
                    onChange={() => handleAccordionChange(partner.partner_id)}
                    sx={isComplete ? { bgcolor: green[50], border: `2px solid ${green[400]}` } : {}}
                  >
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Stack direction="row" spacing={2} alignItems="center" width="100%">
                        <Typography sx={{ flex: 1, fontWeight: isComplete ? 700 : 400, color: isComplete ? green[800] : undefined }}>{partner.partner_name}</Typography>
                        <Chip label={loiData?.status || 'Not Started'} color={isComplete ? 'success' : (statusColor[loiData?.status?.toLowerCase()] || 'default')} size="small" />
                        <Typography sx={{ minWidth: 120 }}>{loiData?.updated_at ? dayjs(loiData.updated_at).format('YYYY-MM-DD HH:mm') : '-'}</Typography>
                        <Typography sx={{ minWidth: 120 }}>
                          {loiData?.complete_count || 0}/{loiData?.total_count || 0}
                          {loiData && (
                            <>
                              {' '}(
                              <span style={{ color: '#1976d2' }}>BE/Max: {loiData.be_max_count || 0}</span>,{' '}
                              <span style={{ color: '#6d4c41' }}>Committed: {loiData.commitment_count || 0}</span>
                              )
                            </>
                          )}
                        </Typography>
                      </Stack>
                    </AccordionSummary>
                    <AccordionDetails>
                      {loiData && loiData.audiences.map((aud, idx) => (
                        <Box key={idx} mb={1}>
                          <Typography variant="body2" fontWeight={600}>{aud.audience_name}</Typography>
                          <Stack direction="row" spacing={1} flexWrap="wrap">
                            {aud.countries.map((country, cidx) => (
                              <Chip
                                key={cidx}
                                label={`${country.name}${country.type === 'be_max' ? ' (BE/Max)' : ''}`}
                                color={country.status === 'complete' ? 'success' : country.status === 'partial' ? 'warning' : country.status === 'missing' ? 'error' : 'default'}
                                size="small"
                                variant={country.status === 'missing' ? 'outlined' : 'filled'}
                                sx={country.type === 'be_max' ? { border: '1px dashed #1976d2' } : {}}
                              />
                            ))}
                          </Stack>
                        </Box>
                      ))}
                    </AccordionDetails>
                  </Accordion>
                );
              })}
            </Box>
          </>
        ) : (
          <Typography>No partner responses found for this bid.</Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant="contained">Close</Button>
      </DialogActions>
    </Dialog>
  );
}

export default PartnerResponseSummaryDialog; 