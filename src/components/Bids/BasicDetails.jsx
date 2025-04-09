import { useState, useEffect } from 'react';
import { 
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  CircularProgress
} from '@mui/material';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import axios from '../../api/axios';
import './Bids.css';
import GlobeIcon from '@mui/icons-material/Public';  // Import globe icon

function BasicDetails() {
  const location = useLocation();
  const navigate = useNavigate();
  const { bidId } = useParams();
  const isEditMode = !!bidId;
  
  // Add debug log for edit mode
  console.log('Current mode:', isEditMode ? 'Edit Mode' : 'Create Mode', 'bidId:', bidId);

  const [salesContacts, setSalesContacts] = useState([]);
  const [vmContacts, setVmContacts] = useState([]);
  const [clients, setClients] = useState([]);
  const [partners, setPartners] = useState([]);
  const [countries] = useState([
    'India', 'USA', 'UK', 'Canada', 'Australia', 'Germany', 'France', 'Japan', 
    'China', 'Brazil', 'Mexico', 'South Africa', 'UAE', 'Singapore'
    // Add more countries as needed
  ]);
  const [loiOptions] = useState(Array.from({length: 60}, (_, i) => i + 1));
  const [taCategories] = useState([
    'B2B',
    'B2C',
    'HC - HCP',
    'HC - Patient'
  ]);

  const [broaderCategories] = useState([
    'Advertiser/Marketing/Media DM',
    'Advertising/Media DMs',
    'Air Travelers',
    'App Developers',
    'Asthma Patients',
    'Automobile Intenders',
    'Automobile Owners',
    'BDMs',
    'Bank account holders',
    'Broadcasters on a mobile live streaming',
    'CXOs',
    'Cancer patients',
    'Caregivers',
    'Cat and Dog owner',
    'Dairy Consumers',
    'Data Collection Group',
    'Dealers/Retailers',
    'Dermatitis patients',
    'Dermatologists',
    'Diabetes patients',
    'Educators',
    'Electronic appliance User/Owner/Intender',
    'Endocrinologists',
    'Energy influencers',
    'Farmers',
    'Financial DMs',
    'Fleet Owner/DMs',
    'Gen pop',
    'General Physician',
    'HR DMs',
    'Hematologists',
    'Hispanics',
    'Home owners',
    'Household decision makers',
    'IT/B DMs',
    'IT DMs',
    'IT Professionals',
    'Insurance purchasers',
    'Journalists',
    'Kids',
    'Liqour consumers',
    'Loyalty Members',
    'Manager & above',
    'Marketing DMs',
    'Medical Directors',
    'Medical/Pharmacy Directors',
    'Medical oncologist',
    'NGO Employees',
    'Nephrologist',
    'Neuro-oncologist',
    'Oncologists',
    'Opinion Elites',
    'PC Buyers',
    'PC Intenders',
    'Parents of kids',
    'Payers',
    'Pediatric Derms',
    'Pharmacy Directors',
    'Printer users',
    'Publisher',
    'Purchase Decision Makers and Influencers',
    'Secondary Research Group',
    'Social Media Users',
    'Teachers',
    'Teens',
    'Users of mobile live video streaming pla',
    'Veterinarian',
    'Webcam Users'
  ]);

  const [modes] = useState(['Online', 'Offline', 'Both']);
  const [irOptions] = useState(Array.from({length: 100}, (_, i) => i + 1));

  const defaultFormData = {
    bid_number: '',  // Leave this empty, will be filled by API
    bid_date: new Date().toISOString().split('T')[0],
    study_name: '',
    methodology: '',
    sales_contact: '',
    vm_contact: '',
    client: '',
    project_requirement: '',
    partners: [],
    loi: [],
    countries: [],
    target_audiences: [{
      name: 'Audience - 1',
      ta_category: '',
      broader_category: '',
      exact_ta_definition: '',
      mode: '',
      sample_required: '',
      ir: '',
      comments: ''
    }]
  };

  const [formData, setFormData] = useState(defaultFormData);
  const [selectedPartners, setSelectedPartners] = useState([]);
  const [selectedLOIs, setSelectedLOIs] = useState([]);
  const [distributionModalOpen, setDistributionModalOpen] = useState(false);
  const [sampleDistribution, setSampleDistribution] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true);
        console.log('Starting loadInitialData, isEditMode:', isEditMode, 'bidId:', bidId);

        // Get next bid number first if it's a new bid
        if (!isEditMode) {
          try {
            const bidNumberResponse = await axios.get('/api/bids/next-number');
            setFormData({
              ...defaultFormData,
              bid_number: bidNumberResponse.data.next_bid_number
            });
          } catch (error) {
            console.error('Error getting next bid number:', error);
          }
        }

        if (isEditMode && bidId) {
          console.log('Fetching bid data for ID:', bidId);
          try {
            const response = await axios.get(`/api/bids/${bidId}`);
            const bidData = response.data;
            
            console.log('Received bid data:', bidData);
            console.log('Partners from API:', bidData.partners);
            
            // Convert partners and loi to arrays if they're not already
            // Extract just the IDs from the partners array
            const partnersArray = bidData.partners ? 
              (Array.isArray(bidData.partners) ? bidData.partners.map(p => p.id || p) : [bidData.partners.id || bidData.partners]) : 
              [];
            const loiArray = bidData.loi ? (Array.isArray(bidData.loi) ? bidData.loi : [bidData.loi]) : [];
            
            console.log('Processed partners array:', partnersArray);
            
            setFormData(prevData => ({
              ...prevData,
              ...bidData,
              partners: partnersArray,
              loi: loiArray,
              countries: Array.isArray(bidData.countries) ? bidData.countries : []
            }));
            
            // Set selected partners and LOIs
            setSelectedPartners(partnersArray);
            setSelectedLOIs(loiArray);
          } catch (error) {
            console.error('Error fetching bid data:', error);
          }
        }

        // Load reference data
        try {
          const [salesRes, vmRes, clientsRes, partnersRes] = await Promise.all([
            axios.get('/api/sales'),
            axios.get('/api/vms'),
            axios.get('/api/clients'),
            axios.get('/api/partners')
          ]);

          console.log('Available partners from API:', partnersRes.data);

          setSalesContacts(salesRes.data);
          setVmContacts(vmRes.data);
          setClients(clientsRes.data);
          setPartners(partnersRes.data);
        } catch (error) {
          console.error('Error loading reference data:', error);
        }

      } catch (error) {
        console.error('Error in loadInitialData:', error);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, [bidId, isEditMode]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTargetAudienceChange = (index, field, value) => {
    setFormData(prev => {
      const newTargetAudiences = [...prev.target_audiences];
      newTargetAudiences[index] = {
        ...newTargetAudiences[index],
        [field]: value
      };
      return {
        ...prev,
        target_audiences: newTargetAudiences
      };
    });
  };

  const addTargetAudience = () => {
    setFormData(prev => ({
      ...prev,
      target_audiences: [
        ...prev.target_audiences,
        {
          name: `Audience - ${prev.target_audiences.length + 1}`,
          ta_category: '',
          broader_category: '',
          exact_ta_definition: '',
          mode: '',
          sample_required: '',
          ir: '',
          comments: ''  // Added comments for each new audience
        }
      ]
    }));
  };

  const removeTargetAudience = (index) => {
    setFormData(prev => ({
      ...prev,
      target_audiences: prev.target_audiences.filter((_, i) => i !== index)
    }));
  };

  const handleMultipleSelect = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSampleRequiredChange = (index, value) => {
    handleTargetAudienceChange(index, 'sample_required', value);
  };

  const handleSampleRequiredBlur = (index) => {
    // Remove auto-distribution on blur
    // We'll only handle distribution when clicking Next
  };

  const handleCountryChange = async (event) => {
    const selectedCountries = Array.isArray(event.target.value) ? event.target.value : [];
    setFormData(prev => ({
      ...prev,
      countries: selectedCountries
    }));
  };

  // Keep both distribution change handlers
  const handlePartnerLOIChange = (type, value) => {
    // Ensure value is always an array
    const arrayValue = Array.isArray(value) ? value : [];
    
    if (type === 'partners') {
      console.log('Setting partners to:', arrayValue);
      // We're already getting IDs from the Select component
      setSelectedPartners(arrayValue);
      setFormData(prev => ({ ...prev, partners: arrayValue }));
    } else if (type === 'loi') {
      setSelectedLOIs(arrayValue);
      setFormData(prev => ({ ...prev, loi: arrayValue }));
    }
  };

  const handleDistributionChange = (country, audienceIndex, value) => {
    const numericValue = parseInt(value) || 0;
    setSampleDistribution(prev => ({
      ...prev,
      [country]: {
        ...prev[country],
        [`audience-${audienceIndex}`]: numericValue
      }
    }));
  };

  // Add validation for the distribution input
  const validateDistribution = () => {
    let isValid = true;
    const errors = [];

    formData.target_audiences.forEach((audience, index) => {
      const total = Object.values(sampleDistribution).reduce(
        (sum, country) => sum + (country[`audience-${index}`] || 0),
        0
      );
      const required = parseInt(audience.sample_required);
      
      if (total !== required) {
        isValid = false;
        errors.push(`${audience.name}: Total (${total}) does not match required samples (${required})`);
      }
    });

    if (!isValid) {
      alert(errors.join('\n'));
    }
    return isValid;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
        if (!validateForm()) {
            return;
        }

        // Initialize sample distribution with existing data in edit mode
        const initialDistribution = {};
        formData.countries.forEach(country => {
            initialDistribution[country] = {};
            formData.target_audiences.forEach((audience, index) => {
                // Get existing sample size from country_samples if available
                const sampleSize = audience.country_samples?.[country] || 0;
                initialDistribution[country][`audience-${index}`] = parseInt(sampleSize);
            });
        });

        setSampleDistribution(initialDistribution);
        setDistributionModalOpen(true);

    } catch (error) {
        console.error('Error:', error);
        alert('Failed to process form data');
    }
  };

  // Update validation to check for partners, LOI and countries
  const validateForm = () => {
    if (!formData.study_name) {
      alert('Please enter a study name');
      return false;
    }
    if (!formData.methodology) {
      alert('Please select a methodology');
      return false;
    }
    if (!formData.sales_contact) {
      alert('Please select a sales contact');
      return false;
    }
    if (!formData.vm_contact) {
      alert('Please select a VM contact');
      return false;
    }
    if (!formData.client) {
      alert('Please select a client');
      return false;
    }
    if (!formData.project_requirement) {
      alert('Please enter project requirements');
      return false;
    }
    if (formData.countries.length === 0) {
      alert('Please select at least one country');
      return false;
    }
    if ((selectedPartners.length === 0 && formData.partners.length === 0)) {
      alert('Please select at least one partner');
      return false;
    }
    if ((selectedLOIs.length === 0 && formData.loi.length === 0)) {
      alert('Please select at least one LOI');
      return false;
    }
    return true;
  };

  // Add handleSaveDistribution function
  const handleSaveDistribution = async () => {
    try {
        // Update formData with the new distribution while preserving other data
        const updatedFormData = {
            ...formData,
            target_audiences: formData.target_audiences.map((audience, index) => ({
                ...audience, // Keep existing audience data
                // Make sure sample_required is a number, not a string
                sample_required: parseInt(audience.sample_required) || 0,
                ir: parseInt(audience.ir) || 0,
                country_samples: Object.fromEntries(
                    formData.countries.map(country => [
                        country,
                        // Ensure values are integers
                        parseInt(sampleDistribution[country]?.[`audience-${index}`] || 0)
                    ])
                )
            }))
        };

        console.log("Sending updated form data:", updatedFormData);
        
        if (isEditMode) {
            await axios.put(`/api/bids/${bidId}`, updatedFormData);
            navigate(`/bids/partner/${bidId}`);
        } else {
            const response = await axios.post('/api/bids', updatedFormData);
            navigate(`/bids/partner/${response.data.bid_id}`);
        }

        setDistributionModalOpen(false);
    } catch (error) {
        console.error('Error saving distribution:', error);
        alert('Failed to save sample distribution');
    }
  };

  return (
    <div className="bid-form-container">
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '20px' }}>
          <CircularProgress />
        </div>
      ) : (
        <Paper className="bid-form">
          <h2>Basic Detail</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <TextField
                required
                label="Bid Number"
                name="bid_number"
                value={formData.bid_number}
                InputProps={{
                  readOnly: true,
                }}
              />
              <TextField
                required
                type="date"
                label="Bid Date"
                name="bid_date"
                value={formData.bid_date}
                onChange={handleInputChange}
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                required
                label="Study Name"
                name="study_name"
                value={formData.study_name}
                onChange={handleInputChange}
              />
              <FormControl fullWidth required>
                <InputLabel>Methodology</InputLabel>
                <Select
                  name="methodology"
                  value={formData.methodology}
                  onChange={handleInputChange}
                >
                  <MenuItem value="quant">Quantitative</MenuItem>
                  <MenuItem value="qual">Qualitative</MenuItem>
                  <MenuItem value="both">Both</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth required>
                <InputLabel>Sales Contact</InputLabel>
                <Select
                  name="sales_contact"
                  value={formData.sales_contact}
                  onChange={handleInputChange}
                >
                  {salesContacts.map(contact => (
                    <MenuItem key={contact.id} value={contact.id}>
                      {contact.sales_person}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth required>
                <InputLabel>VM Contact</InputLabel>
                <Select
                  name="vm_contact"
                  value={formData.vm_contact}
                  onChange={handleInputChange}
                >
                  {vmContacts.map(contact => (
                    <MenuItem key={contact.id} value={contact.id}>
                      {contact.vm_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth required>
                <InputLabel>Client</InputLabel>
                <Select
                  name="client"
                  value={formData.client}
                  onChange={handleInputChange}
                >
                  {clients.map(client => (
                    <MenuItem key={client.id} value={client.id}>
                      {client.client_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                required
                multiline
                rows={4}
                label="Project Requirement"
                name="project_requirement"
                value={formData.project_requirement}
                onChange={handleInputChange}
              />
              <FormControl fullWidth>
                <InputLabel>Partners</InputLabel>
                <Select
                  multiple
                  value={selectedPartners || []}
                  onChange={(e) => handlePartnerLOIChange('partners', e.target.value)}
                  renderValue={(selected) => {
                    // Find partner names for selected IDs
                    const selectedNames = selected.map(id => 
                      partners.find(p => p.id === id)?.partner_name
                    ).filter(Boolean);
                    return selectedNames.join(', ');
                  }}
                >
                  {partners.map(partner => (
                    <MenuItem key={partner.id} value={partner.id}>
                      {partner.partner_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>LOI (mins)</InputLabel>
                <Select
                  multiple
                  value={selectedLOIs}
                  onChange={(e) => handlePartnerLOIChange('loi', e.target.value)}
                >
                  {loiOptions.map(minutes => (
                    <MenuItem key={minutes} value={minutes}>
                      {minutes} mins
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl fullWidth required>
                <InputLabel>Countries</InputLabel>
                <Select
                  multiple
                  name="countries"
                  value={formData.countries}
                  onChange={handleCountryChange}
                >
                  {countries.map(country => (
                    <MenuItem key={country} value={country}>
                      {country}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </div>
            <h3 className="section-title">Target Audiences</h3>
            {Array.isArray(formData.target_audiences) && formData.target_audiences.map((audience, index) => (
              <div key={index} className="target-audience-section">
                <div className="target-audience-header">
                  <h4>{audience.name}</h4>
                  {index > 0 && (
                    <Button 
                      size="small" 
                      color="error" 
                      onClick={() => removeTargetAudience(index)}
                    >
                      Remove
                    </Button>
                  )}
                </div>
                <div className="target-audience-grid">
                  <FormControl fullWidth required>
                    <InputLabel>TA Category</InputLabel>
                    <Select
                      value={audience.ta_category}
                      onChange={(e) => handleTargetAudienceChange(index, 'ta_category', e.target.value)}
                    >
                      {taCategories.map(category => (
                        <MenuItem key={category} value={category}>
                          {category}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth required>
                    <InputLabel>Broader Category</InputLabel>
                    <Select
                      value={audience.broader_category}
                      onChange={(e) => handleTargetAudienceChange(index, 'broader_category', e.target.value)}
                    >
                      {broaderCategories.map(category => (
                        <MenuItem key={category} value={category}>
                          {category}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <TextField
                    required
                    fullWidth
                    multiline
                    rows={2}
                    label="Exact TA Definition"
                    value={audience.exact_ta_definition}
                    onChange={(e) => handleTargetAudienceChange(index, 'exact_ta_definition', e.target.value)}
                  />

                  <FormControl fullWidth required>
                    <InputLabel>Mode</InputLabel>
                    <Select
                      value={audience.mode}
                      onChange={(e) => handleTargetAudienceChange(index, 'mode', e.target.value)}
                    >
                      {modes.map(mode => (
                        <MenuItem key={mode} value={mode}>
                          {mode}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <TextField
                    required
                    fullWidth
                    label="Sample Required"
                    type="number"
                    value={audience.sample_required}
                    onChange={(e) => handleSampleRequiredChange(index, e.target.value)}
                    onBlur={() => handleSampleRequiredBlur(index)}
                  />

                  <FormControl fullWidth required>
                    <InputLabel>IR (%)</InputLabel>
                    <Select
                      value={audience.ir}
                      onChange={(e) => handleTargetAudienceChange(index, 'ir', e.target.value)}
                    >
                      {irOptions.map(ir => (
                        <MenuItem key={ir} value={ir}>
                          {ir}%
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <TextField
                    fullWidth
                    multiline
                    rows={2}
                    label="Comments"
                    value={audience.comments}
                    onChange={(e) => handleTargetAudienceChange(index, 'comments', e.target.value)}
                    className="audience-comments"
                  />
                </div>
              </div>
            ))}

            <Button 
              variant="outlined" 
              color="primary" 
              onClick={addTargetAudience}
              className="add-target-audience-btn"
            >
              + ADD TARGET AUDIENCE
            </Button>

            <div className="form-actions">
              <Button onClick={() => navigate('/bids')}>CANCEL</Button>
              <Button type="submit" variant="contained" color="primary">
                NEXT
              </Button>
            </div>
          </form>
        </Paper>
      )}

      {/* Sample Distribution Modal */}
      <Dialog 
        open={distributionModalOpen} 
        onClose={() => setDistributionModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Distribute Samples Across Countries</DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Country</TableCell>
                  {formData?.target_audiences?.map((audience, index) => (
                    <TableCell key={index} align="center">
                      {audience.name}<br/>
                      (Required: {audience.sample_required})
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {formData?.countries?.map(country => (
                  <TableRow key={country}>
                    <TableCell>{country}</TableCell>
                    {formData?.target_audiences?.map((audience, index) => (
                      <TableCell key={index} align="center">
                        <TextField
                          type="number"
                          size="small"
                          value={sampleDistribution[country]?.[`audience-${index}`] || 0}
                          onChange={(e) => handleDistributionChange(country, index, e.target.value)}
                          inputProps={{ min: 0 }}
                        />
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDistributionModalOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleSaveDistribution} 
            variant="contained" 
            color="primary"
            disabled={!formData?.target_audiences?.length || !formData?.countries?.length}
          >
            Save & Continue
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default BasicDetails; 