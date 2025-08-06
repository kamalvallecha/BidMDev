import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Paper,
  Typography,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Box,
  Button,
  Stack,
  Grid,
  Alert,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import axios from '../../api/axios';
import './Bids.css';

function InvoiceEdit() {
  const { bidId } = useParams();
  const navigate = useNavigate();
  const [currentTab, setCurrentTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    partners: [],
    partner_lois: {},
    audiences: [],
    po_number: '',
    status: '',
    study_name: ''
  });

  const [selectedLOIs, setSelectedLOIs] = useState({});
  const [finalCPIs, setFinalCPIs] = useState({});
  const [savingStatus, setSavingStatus] = useState({});
  const [invoiceDetails, setInvoiceDetails] = useState({
    po_number: '',
    invoice_date: null,
    invoice_sent: null,
    invoice_serial: '',
    invoice_number: '',
    invoice_amount: '0.00'
  });

  useEffect(() => {
    fetchData();
  }, [bidId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/bids/${bidId}/invoice-data`);
      setData(response.data);
      
      // Initialize selected LOIs for each partner with their first valid LOI
      const initialSelectedLOIs = {};
      response.data.partners.forEach(partner => {
        const validLOIs = response.data.partner_lois[partner.id] || [];
        if (validLOIs.length > 0) {
          initialSelectedLOIs[partner.id] = validLOIs[0];
        }
      });
      setSelectedLOIs(initialSelectedLOIs);

      // Initialize final CPIs
      const initialCPIs = {};
      response.data.audiences.forEach(audience => {
        audience.deliverables.forEach(del => {
          const key = `${del.partner_id}-${del.loi}-${audience.id}-${del.country}`;
          initialCPIs[key] = del.final_cpi || del.initial_cpi;
        });
      });
      setFinalCPIs(initialCPIs);

      // Set PO number if available
      if (response.data.po_number) {
        setInvoiceDetails(prev => ({
          ...prev,
          po_number: response.data.po_number
        }));
      }

      setLoading(false);
    } catch (err) {
      console.error('Error fetching invoice data:', err);
      setError('Failed to load invoice data');
      setLoading(false);
    }
  };

  const handleFinalCPIChange = async (key, value) => {
    // Split the key to get components
    const [partnerId, loi, audienceId, country] = key.split('-');
    
    // Update local state first
    setFinalCPIs(prev => ({
      ...prev,
      [key]: value
    }));
    
    // Set status to saving
    setSavingStatus(prev => ({
      ...prev,
      [key]: 'saving'
    }));
    
    try {
      // Get partner name from partners array
      const partnerName = data.partners.find(p => p.id === parseInt(partnerId))?.partner_name;
      if (!partnerName) {
        throw new Error('Partner not found');
      }
      
      // Prepare the data structure expected by backend
      const finalCPI = parseFloat(value);
      const deliverable = data.audiences
        .flatMap(a => a.deliverables)
        .find(d => 
          d.partner_id === parseInt(partnerId) && 
          d.loi === parseInt(loi) && 
          d.country === country
        );
        
      if (!deliverable) {
        throw new Error('Deliverable not found');
      }
      
      const finalCost = deliverable.n_delivered * finalCPI;
      
      const invoiceData = {
        partner_name: partnerName,
        loi: parseInt(loi),
        invoice_data: {
          invoice_date: invoiceDetails.invoice_date,
          invoice_sent: invoiceDetails.invoice_sent,
          invoice_serial: invoiceDetails.invoice_serial,
          invoice_number: invoiceDetails.invoice_number,
          invoice_amount: "0.00" // Will be calculated by backend
        },
        deliverables: [{
          audience_id: parseInt(audienceId),
          country: country,
          final_cpi: finalCPI,
          final_cost: finalCost
        }]
      };
      
      // Use bid_number not bid_id for the API endpoint
      const bidNumber = data.bid_number || bidId;
      
      // Show saving indicator
      console.log(`Saving Final CPI ${finalCPI} for partner ${partnerName}, LOI ${loi}, audience ${audienceId}, country ${country}`);
      
      // Send to the backend
      await axios.post(`/api/invoice/${bidNumber}/save`, invoiceData);
      
      // Update status to saved
      setSavingStatus(prev => ({
        ...prev,
        [key]: 'saved'
      }));
      
      // Show saved status for 2 seconds then clear
      setTimeout(() => {
        setSavingStatus(prev => ({
          ...prev,
          [key]: null
        }));
      }, 2000);
      
    } catch (err) {
      console.error('Error saving CPI change:', err);
      setSavingStatus(prev => ({
        ...prev,
        [key]: 'error'
      }));
    }
  };

  const handleSubmit = async () => {
    try {
      const currentPartner = getCurrentPartner();
      const selectedLOI = selectedLOIs[currentPartner.id];
      
      if (!currentPartner || !selectedLOI) {
        alert('Please select a partner and LOI');
        return;
      }
      
      // Prepare deliverables data for the selected partner and LOI
      const deliverables = [];
      data.audiences.forEach(audience => {
        audience.deliverables
          .filter(del => 
            del.partner_id === currentPartner.id && 
            del.loi === selectedLOI
          )
          .forEach(del => {
            const key = `${del.partner_id}-${del.loi}-${audience.id}-${del.country}`;
            deliverables.push({
              audience_id: audience.id,
              country: del.country,
              final_cpi: parseFloat(finalCPIs[key] || del.initial_cpi),
              final_cost: parseFloat(finalCPIs[key] || del.initial_cpi) * del.n_delivered
            });
          });
      });
      
      // Calculate total invoice amount
      const totalAmount = deliverables.reduce((sum, del) => sum + del.final_cost, 0);
      
      // Prepare invoice data
      const invoiceData = {
        partner_name: currentPartner.partner_name,
        loi: selectedLOI,
        invoice_data: {
          invoice_date: invoiceDetails.invoice_date,
          invoice_sent: invoiceDetails.invoice_sent,
          invoice_serial: invoiceDetails.invoice_serial,
          invoice_number: invoiceDetails.invoice_number,
          invoice_amount: totalAmount.toFixed(2)
        },
        deliverables: deliverables
      };
      
      // Use bid_number not bid_id for the API endpoint
      const bidNumber = data.bid_number || bidId;
      
      // Send data to the server
      await axios.post(`/api/invoice/${bidNumber}/save`, invoiceData);
      
      alert('Changes saved successfully!');
    } catch (err) {
      console.error('Error saving changes:', err);
      alert('Failed to save changes: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleCancel = () => {
    navigate('/ready-for-invoice');
  };

  const getCurrentPartner = () => data.partners[currentTab] || null;
  const getCurrentPartnerLOIs = () => {
    const partner = getCurrentPartner();
    return partner ? (data.partner_lois[partner.id] || []) : [];
  };

  const handleLOIChange = (partnerId, loi) => {
    setSelectedLOIs(prev => ({
      ...prev,
      [partnerId]: loi
    }));
    
    // No need to reset finalCPIs as they're now kept per partner-LOI-audience-country
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="invoice-edit-container">
      <Paper className="invoice-edit-form">
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5">Ready to Invoice - {data.study_name}</Typography>
          
          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="PO Number"
                value={invoiceDetails.po_number}
                onChange={(e) => setInvoiceDetails(prev => ({ ...prev, po_number: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <DatePicker
                  label="Invoice Date"
                  value={invoiceDetails.invoice_date}
                  onChange={(date) => setInvoiceDetails(prev => ({ ...prev, invoice_date: date }))}
                  renderInput={(params) => <TextField {...params} fullWidth />}
                />
              </LocalizationProvider>
            </Grid>
            {/* Add more invoice detail fields */}
          </Grid>
        </Box>

        <Tabs
          value={currentTab}
          onChange={(e, newValue) => setCurrentTab(newValue)}
          sx={{ mb: 2 }}
        >
          {data.partners.map((partner, index) => (
            <Tab key={partner.id} label={partner.partner_name} />
          ))}
        </Tabs>

        {getCurrentPartner() && (
          <Box sx={{ mb: 2 }}>
            <Typography>Select LOI:</Typography>
            <Stack direction="row" spacing={1}>
              {getCurrentPartnerLOIs().map(loi => (
                <Button
                  key={loi}
                  variant={selectedLOIs[getCurrentPartner().id] === loi ? "contained" : "outlined"}
                  onClick={() => handleLOIChange(getCurrentPartner().id, loi)}
                >
                  {loi} MIN
                </Button>
              ))}
            </Stack>
          </Box>
        )}

        {data.audiences.map((audience) => (
          <div key={audience.id} className="audience-section">
            <Typography variant="h6" sx={{ mb: 2 }}>
              {`${audience.name} - ${audience.ta_category}`}
            </Typography>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ bgcolor: '#7c4dff' }}>
                    <TableCell sx={{ color: 'white' }}>Country</TableCell>
                    <TableCell sx={{ color: 'white' }}>Allocation</TableCell>
                    <TableCell sx={{ color: 'white' }}>N Delivered</TableCell>
                    <TableCell sx={{ color: 'white' }}>Initial CPI</TableCell>
                    <TableCell sx={{ color: 'white' }}>Final CPI</TableCell>
                    <TableCell sx={{ color: 'white' }}>Initial Cost</TableCell>
                    <TableCell sx={{ color: 'white' }}>Final Cost</TableCell>
                    <TableCell sx={{ color: 'white' }}>Savings</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {audience.deliverables
                    .filter(del => 
                      del.partner_id === getCurrentPartner()?.id && 
                      del.loi === selectedLOIs[getCurrentPartner()?.id]
                    )
                    .map((deliverable) => {
                      const key = `${deliverable.partner_id}-${deliverable.loi}-${audience.id}-${deliverable.country}`;
                      const finalCPI = finalCPIs[key] || deliverable.initial_cpi;
                      const finalCost = deliverable.n_delivered * finalCPI;
                      const savings = deliverable.initial_cost - finalCost;

                      return (
                        <TableRow key={deliverable.country}>
                          <TableCell>{deliverable.country}</TableCell>
                          <TableCell>{deliverable.allocation}</TableCell>
                          <TableCell>{deliverable.n_delivered}</TableCell>
                          <TableCell>{deliverable.initial_cpi.toFixed(2)}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <TextField
                                type="number"
                                size="small"
                                value={finalCPI}
                                onChange={(e) => handleFinalCPIChange(key, e.target.value)}
                                inputProps={{ step: 0.01, min: 0 }}
                                sx={{ mr: 1 }}
                              />
                              {savingStatus[key] === 'saving' && (
                                <span style={{ fontSize: '0.75rem', color: 'orange' }}>Saving...</span>
                              )}
                              {savingStatus[key] === 'saved' && (
                                <span style={{ fontSize: '0.75rem', color: 'green' }}>✓</span>
                              )}
                              {savingStatus[key] === 'error' && (
                                <span style={{ fontSize: '0.75rem', color: 'red' }}>Error!</span>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>{deliverable.initial_cost.toFixed(2)}</TableCell>
                          <TableCell>{finalCost.toFixed(2)}</TableCell>
                          <TableCell sx={{ color: savings > 0 ? 'green' : 'red' }}>
                            {savings.toFixed(2)}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                </TableBody>
              </Table>
            </TableContainer>
          </div>
        ))}

        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
          <Button variant="outlined" onClick={handleCancel}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSubmit}>
            Save Changes
          </Button>
        </Box>
      </Paper>
    </div>
  );
}

export default InvoiceEdit;