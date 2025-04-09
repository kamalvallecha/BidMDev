import React, { useState, useEffect } from 'react';
import { 
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  FormControl,
  Select,
  MenuItem,
  Typography,
  Box,
  Tabs,
  Tab,
  styled,
  InputAdornment,
  Alert
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Styled components
const StyledTab = styled(Tab)({
  color: '#666',
  '&.Mui-selected': {
    color: '#1976d2',
  }
});

const LOIButton = styled(Button)(({ theme, isActive }) => ({
  borderRadius: '20px',
  marginRight: '10px',
  backgroundColor: isActive ? theme.palette.primary.main : 'transparent',
  color: isActive ? 'white' : theme.palette.primary.main,
  '&:hover': {
    backgroundColor: isActive ? theme.palette.primary.dark : 'rgba(25, 118, 210, 0.04)',
  }
}));

const InvoiceEdit = () => {
  const { bidId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [activeVendor, setActiveVendor] = useState(0);
  const [activeLOI, setActiveLOI] = useState(null);
  const [partners, setPartners] = useState([]);
  const [lois, setLois] = useState([]);
  const [audienceIds, setAudienceIds] = useState([]);
  const [invoiceData, setInvoiceData] = useState({
    poNumber: '',
    invoiceDate: '',
    invoiceSerial: '',
    invoiceNumber: '',
    invoiceAmount: '0.00',
    deliverables: []
  });
  const [invoiceSent, setInvoiceSent] = useState('');
  const [formData, setFormData] = useState({
    poNumber: '',
    invoiceDate: '',
    invoiceSerial: '',
    invoiceNumber: '',
    invoiceSent: '',
    invoiceAmount: '0.00'
  });
  const [partnerFormData, setPartnerFormData] = useState({});
  const [finalCPIData, setFinalCPIData] = useState({});
  const [partnerInvoiceDetails, setPartnerInvoiceDetails] = useState({});
  const [hasInvalidCPI, setHasInvalidCPI] = useState(false);

  useEffect(() => {
    if (bidId) {
      fetchPartnerData();
    } else {
      navigate('/invoice');
    }
  }, [bidId]);

  useEffect(() => {
    if (bidId && partners.length > 0 && activeLOI !== null) {
      fetchInvoiceData();
    }
  }, [bidId, activeVendor, activeLOI]);

  useEffect(() => {
    // Load from session storage
    const savedState = sessionStorage.getItem(`invoice_${bidId}`);
    if (savedState && (!invoiceData.deliverables.length || !formData.invoiceDate)) {
      const { 
        formData: savedForm, 
        invoiceData: savedInvoice, 
        partnerFormData: savedPartnerForm,
        finalCPIData: savedFinalCPI 
      } = JSON.parse(savedState);
      setFormData(savedForm);
      setInvoiceData(savedInvoice);
      setPartnerFormData(savedPartnerForm || {});
      setFinalCPIData(savedFinalCPI || {});
    }
  }, []);

  useEffect(() => {
    // Add effect to save to session storage
    sessionStorage.setItem(`invoice_${bidId}`, JSON.stringify({
      formData,
      invoiceData,
      partnerFormData,
      finalCPIData
    }));
  }, [formData, invoiceData, partnerFormData, finalCPIData]);

  useEffect(() => {
    if (bidId && partners.length > 0) {
      checkAllFinalCPIs();
    }
  }, [bidId, partners, invoiceData]);

  const fetchPartnerData = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/invoice/${bidId}/partner-data`);
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch partner data');
      }

      const data = await response.json();
      
      // Extract unique partners and LOIs from partner_data keys
      const uniquePartners = [...new Set(Object.keys(data.partner_data).map(key => key.split('_')[0]))];
      const uniqueLois = [...new Set(Object.keys(data.partner_data).map(key => parseInt(key.split('_')[1])))].sort((a, b) => a - b);
      const uniqueAudiences = [...new Set(
        Object.values(data.partner_data)
          .flatMap(pd => pd.deliverables)
          .map(d => d.audience_id)
      )].sort((a, b) => a - b);
      
      setPartners(uniquePartners);
      setLois(uniqueLois);
      setAudienceIds(uniqueAudiences);

      // Store invoice details for each partner-LOI combination
      const partnerDetails = {};
      Object.entries(data.partner_data).forEach(([key, value]) => {
        partnerDetails[key] = {
          poNumber: data.po_number || '',
          invoiceDate: value.invoice_date || '',
          invoiceSent: value.invoice_sent || '',
          invoiceSerial: value.invoice_serial || '',
          invoiceNumber: value.invoice_number || '',
          invoiceAmount: value.invoice_amount || '0.00'
        };
      });
      setPartnerInvoiceDetails(partnerDetails);

      // Set initial form data for first partner and LOI
      if (uniquePartners.length > 0 && uniqueLois.length > 0) {
        const initialKey = `${uniquePartners[0]}_${uniqueLois[0]}`;
        const initialDetails = partnerDetails[initialKey] || {
          poNumber: data.po_number || '',
          invoiceDate: '',
          invoiceSent: '',
          invoiceSerial: '',
          invoiceNumber: '',
          invoiceAmount: '0.00'
        };
        setFormData(initialDetails);
        setActiveVendor(0);
        setActiveLOI(uniqueLois[0]);
      }
    } catch (error) {
      console.error('Error fetching partner data:', error);
    }
  };

  const fetchInvoiceData = async () => {
    try {
      const response = await fetch(`http://localhost:5000/api/invoice/${bidId}/${partners[activeVendor]}/${activeLOI}/details`);
      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      // Check if there are any deliverables with n_delivered > 0
      const hasDeliveries = data.deliverables.some(item => item.nDelivered > 0);

      if (!hasDeliveries) {
        setInvoiceData({
          ...invoiceData,
          deliverables: [],
          message: 'No respondents delivered for this LOI'
        });
        return;
      }

      // If we have deliveries, show all data
      setInvoiceData({
        ...data,
        deliverables: data.deliverables,
        message: null
      });

      // Calculate total invoice amount
      const totalInvoiceAmount = data.deliverables.reduce((sum, item) => {
        return sum + (item.finalCPI || item.initialCPI) * item.nDelivered;
      }, 0);

      // Update form data
      setFormData(prev => ({
        ...prev,
        poNumber: data.po_number || '',
        invoiceAmount: totalInvoiceAmount.toFixed(2)
      }));

    } catch (error) {
      console.error('Error fetching invoice data:', error);
      message.error('Failed to fetch invoice data');
    }
  };

  const handleCancel = () => {
    navigate('/invoice');
  };

  const handleSubmit = async () => {
    try {
        // Check current page first
        const currentDeliverables = invoiceData.deliverables.filter(item => item.nDelivered > 0);
        const hasInvalidCurrentCPI = currentDeliverables.some(item => 
            !item.finalCPI || 
            parseFloat(item.finalCPI) === 0 || 
            item.finalCPI === '0' || 
            item.finalCPI === ''
        );

        if (hasInvalidCurrentCPI) {
            alert(`Please fill in all Final CPI values for ${partners[activeVendor]} with ${activeLOI} min LOI`);
            return;
        }

        // Then check all other partner-LOI combinations
        for (let partnerIndex = 0; partnerIndex < partners.length; partnerIndex++) {
            const currentPartner = partners[partnerIndex];
            
            for (const loi of lois) {
                // Skip current combination as we already checked it
                if (currentPartner === partners[activeVendor] && loi === activeLOI) {
                    continue;
                }

                const response = await fetch(`http://localhost:5000/api/invoice/${bidId}/${currentPartner}/${loi}/details`);
                const data = await response.json();
                
                if (data.deliverables && data.deliverables.length > 0) {
                    const deliveredItems = data.deliverables.filter(item => item.nDelivered > 0);
                    
                    if (deliveredItems.length > 0) {
                        const hasInvalidCPI = deliveredItems.some(item => 
                            !item.finalCPI || 
                            parseFloat(item.finalCPI) === 0 || 
                            item.finalCPI === '0' || 
                            item.finalCPI === ''
                        );
                        
                        if (hasInvalidCPI) {
                            alert(`Please check ${currentPartner} with ${loi} min LOI for Final CPI`);
                            return;
                        }
                    }
                }
            }
        }

        // If we get here, all CPIs are valid - proceed with save and submit
        await handleSave();  // Save current page first

        // Submit the invoice
        const submitResponse = await fetch(`http://localhost:5000/api/invoice/${bidId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!submitResponse.ok) {
            throw new Error('Failed to submit invoice');
        }

        alert('Invoice submitted successfully!');
        navigate('/invoice');
        
    } catch (error) {
        console.error('Error submitting invoice:', error);
        alert(error.message || 'Failed to submit invoice');
    }
  };

  const handleInputChange = (field) => (event) => {
    const newValue = event.target.value;
    const currentPartner = partners[activeVendor];
    
    // Update form data for current view
    setFormData(prev => ({
      ...prev,
      [field]: newValue
    }));

    // Sync the same field across all LOIs for the current partner
    setPartnerInvoiceDetails(prev => {
      const updatedDetails = { ...prev };
      // Update all LOIs for the current partner
      lois.forEach(loi => {
        const key = `${currentPartner}_${loi}`;
        updatedDetails[key] = {
          ...(updatedDetails[key] || {}),
          poNumber: formData.poNumber, // Keep existing PO number
          [field]: newValue // Update only the changed field
        };
      });
      return updatedDetails;
    });
  };

  const handleFinalCPIChange = (item) => (event) => {
    const newValue = Number(event.target.value);
    const updatedDeliverables = invoiceData.deliverables.map(d => {
      if (d.audience_id === item.audience_id && d.country === item.country) {
        const initialCost = d.nDelivered * d.initialCPI;
        const finalCost = d.nDelivered * newValue;
        return {
          ...d,
          finalCPI: newValue,
          initialCost: initialCost,
          finalCost: finalCost,
          savings: initialCost - finalCost
        };
      }
      return d;
    });

    setInvoiceData(prev => ({
      ...prev,
      deliverables: updatedDeliverables
    }));

    // Recalculate total invoice amount
    const totalAmount = updatedDeliverables.reduce((sum, item) => {
      return sum + (item.finalCPI || item.initialCPI) * item.nDelivered;
    }, 0);

    setFormData(prev => ({
      ...prev,
      invoiceAmount: totalAmount.toFixed(2)
    }));

    // Check CPIs after update
    checkAllFinalCPIs();
  };

  const handlePartnerChange = (event, newValue) => {
    const currentPartner = partners[activeVendor];
    const newPartner = partners[newValue];

    // Save current form data across all LOIs for current partner
    if (currentPartner) {
      const updatedDetails = { ...partnerInvoiceDetails };
      lois.forEach(loi => {
        const key = `${currentPartner}_${loi}`;
        updatedDetails[key] = {
          ...formData
        };
      });
      setPartnerInvoiceDetails(updatedDetails);
    }

    // Load form data for new partner (use data from first LOI if exists)
    if (newPartner) {
      const firstLOIKey = `${newPartner}_${lois[0]}`;
      const partnerDetails = partnerInvoiceDetails[firstLOIKey] || {
        poNumber: formData.poNumber, // Keep PO number as it's bid-specific
        invoiceDate: '',
        invoiceSent: '',
        invoiceSerial: '',
        invoiceNumber: '',
        invoiceAmount: '0.00'
      };
      setFormData(partnerDetails);
    }

    setActiveVendor(newValue);
  };

  const handleLOIChange = (newLOI) => {
    const currentPartner = partners[activeVendor];
    
    // When changing LOI, just load the same data as current partner's first LOI
    const firstLOIKey = `${currentPartner}_${lois[0]}`;
    const partnerDetails = partnerInvoiceDetails[firstLOIKey] || {
      poNumber: formData.poNumber,
      invoiceDate: formData.invoiceDate,
      invoiceSent: formData.invoiceSent,
      invoiceSerial: formData.invoiceSerial,
      invoiceNumber: formData.invoiceNumber,
      invoiceAmount: formData.invoiceAmount
    };
    
    setFormData(partnerDetails);
    setActiveLOI(newLOI);
  };

  const handleSave = async () => {
    try {
      const currentPartner = partners[activeVendor];
      
      // Save invoice data only for the currently selected LOI
      const dataToSave = {
        bid_id: bidId,
        partner_name: currentPartner,
        loi: parseInt(activeLOI),
        invoice_data: {
          invoice_date: formData.invoiceDate,
          invoice_sent: formData.invoiceSent,
          invoice_serial: formData.invoiceSerial,
          invoice_number: formData.invoiceNumber,
          invoice_amount: formData.invoiceAmount
        },
        deliverables: invoiceData.deliverables
          .filter(item => item.nDelivered > 0)
          .map(item => ({
            audience_id: item.audience_id,
            country: item.country,
            final_cpi: parseFloat(item.finalCPI),
            final_cost: parseFloat(item.finalCost)
          }))
      };

      const response = await fetch(`http://localhost:5000/api/invoice/${bidId}/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(dataToSave)
      });

      if (!response.ok) {
        throw new Error(`Failed to save data for LOI ${activeLOI}`);
      }

      alert(`Data saved successfully for ${currentPartner} with ${activeLOI} min LOI!`);
    } catch (error) {
      console.error('Error saving data:', error);
      alert('Failed to save data');
    }
  };

  const checkAllFinalCPIs = async () => {
    try {
      for (let partnerIndex = 0; partnerIndex < partners.length; partnerIndex++) {
        const currentPartner = partners[partnerIndex];
        
        for (const loi of lois) {
          const response = await fetch(`http://localhost:5000/api/invoice/${bidId}/${currentPartner}/${loi}/details`);
          const data = await response.json();
          
          if (data.deliverables && data.deliverables.length > 0) {
            const deliveredItems = data.deliverables.filter(item => item.nDelivered > 0);
            
            if (deliveredItems.length > 0) {
              const hasInvalidCPI = deliveredItems.some(item => 
                !item.finalCPI || 
                item.finalCPI === 0 || 
                item.finalCPI === '0' || 
                item.finalCPI === ''
              );
              
              if (hasInvalidCPI) {
                setHasInvalidCPI(true);
                return;
              }
            }
          }
        }
      }
      setHasInvalidCPI(false);
    } catch (error) {
      console.error('Error checking Final CPIs:', error);
    }
  };

  const renderAudienceTable = (audienceId) => {
    // Filter for rows with deliveries
    const audienceDeliverables = invoiceData.deliverables.filter(
      item => item.audience_id === audienceId && item.nDelivered > 0
    );

    if (!audienceDeliverables.length) return null;

    return (
      <TableContainer component={Paper} sx={{ mb: 4 }} key={audienceId}>
        <Typography variant="h6" sx={{ p: 2 }}>
          Deliverables & Costs - Audience {audienceId}
        </Typography>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Country</TableCell>
              <TableCell align="right">Allocation</TableCell>
              <TableCell align="right">N Delivered</TableCell>
              <TableCell align="right">Initial CPI</TableCell>
              <TableCell align="right">Final CPI</TableCell>
              <TableCell align="right">Initial Cost</TableCell>
              <TableCell align="right">Final Cost</TableCell>
              <TableCell align="right">Savings</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {audienceDeliverables.map((item, index) => (
              <TableRow key={index}>
                <TableCell>{item.country}</TableCell>
                <TableCell align="right">{item.allocation}</TableCell>
                <TableCell align="right">{item.nDelivered}</TableCell>
                <TableCell align="right">
                  ${Number(item.initialCPI).toFixed(2)}
                </TableCell>
                <TableCell align="right">
                  <TextField
                    type="number"
                    value={item.finalCPI}
                    onChange={handleFinalCPIChange(item)}
                    inputProps={{ 
                      step: "0.01",
                      min: "0"
                    }}
                    size="small"
                    sx={{ width: '100px' }}
                  />
                </TableCell>
                <TableCell align="right">
                  ${Number(item.initialCost).toFixed(2)}
                </TableCell>
                <TableCell align="right">
                  ${Number(item.finalCost).toFixed(2)}
                </TableCell>
                <TableCell align="right">
                  ${Number(item.savings).toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 3 }}>Ready to Invoice</Typography>
      
      <Tabs 
        value={activeVendor} 
        onChange={handlePartnerChange}
        sx={{ mb: 3 }}
      >
        {partners.map((partner, index) => (
          <StyledTab key={partner} label={partner} />
        ))}
      </Tabs>

      <Box sx={{ mb: 3, bgcolor: '#f5f5f5', p: 2 }}>
        <Typography sx={{ mb: 1 }}>Select LOI:</Typography>
        <Box>
          {lois.map(loi => (
            <LOIButton 
              key={loi}
              variant={activeLOI === loi ? 'contained' : 'outlined'}
              onClick={() => handleLOIChange(loi)}
              isActive={activeLOI === loi}
            >
              {loi} min
            </LOIButton>
          ))}
        </Box>
      </Box>

      <Typography sx={{ mb: 1, color: 'primary.main' }}>
        Currently viewing: {partners[activeVendor]} with {activeLOI} min LOI
      </Typography>

      {invoiceData.message ? (
        <Alert 
          severity="info" 
          sx={{ mb: 3 }}
        >
          {invoiceData.message}
        </Alert>
      ) : (
        <>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 2, mb: 3 }}>
            <TextField
              label="PO Number"
              value={formData.poNumber}
              InputProps={{ readOnly: true }}
              fullWidth
            />
            <TextField
              label="Invoice Date"
              type="date"
              InputLabelProps={{ shrink: true }}
              fullWidth
              value={formData.invoiceDate}
              onChange={handleInputChange('invoiceDate')}
            />
            <TextField
              label="Invoice Sent"
              type="date"
              InputLabelProps={{ shrink: true }}
              fullWidth
              value={formData.invoiceSent}
              onChange={handleInputChange('invoiceSent')}
            />
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 2, mb: 4 }}>
            <TextField
              label="Invoice Serial #"
              fullWidth
              value={formData.invoiceSerial}
              onChange={handleInputChange('invoiceSerial')}
            />
            <TextField
              label="Invoice #"
              fullWidth
              value={formData.invoiceNumber}
              onChange={handleInputChange('invoiceNumber')}
            />
            <TextField
              label="Invoice Amount"
              fullWidth
              value={formData.invoiceAmount}
              onChange={handleInputChange('invoiceAmount')}
              InputProps={{
                readOnly: true,
                startAdornment: <InputAdornment position="start">$</InputAdornment>
              }}
            />
          </Box>

          {audienceIds.map(audienceId => renderAudienceTable(audienceId))}

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button variant="outlined" onClick={handleCancel}>
              Cancel
            </Button>
            {isAdmin && (
              <Button variant="contained" color="secondary" onClick={handleSave}>
                Save
              </Button>
            )}
            {isAdmin && (
              <Button 
                variant="contained" 
                onClick={handleSubmit}
                disabled={hasInvalidCPI}
              >
                Submit
              </Button>
            )}
          </Box>
        </>
      )}
    </Box>
  );
};

export default InvoiceEdit; 