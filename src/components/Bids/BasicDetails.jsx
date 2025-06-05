import { useState, useEffect } from "react";
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
  CircularProgress,
  FormControlLabel,
  Checkbox,
} from "@mui/material";
import { useNavigate, useLocation, useParams } from "react-router-dom";
import axios from "../../api/axios";
import "./Bids.css";
import GlobeIcon from "@mui/icons-material/Public"; // Import globe icon

function BasicDetails() {
  const location = useLocation();
  const navigate = useNavigate();
  const { bidId } = useParams();
  const isEditMode = !!bidId;

  // Add debug log for edit mode
  console.log(
    "Current mode:",
    isEditMode ? "Edit Mode" : "Create Mode",
    "bidId:",
    bidId,
  );

  const [salesContacts, setSalesContacts] = useState([]);
  const [vmContacts, setVmContacts] = useState([]);
  const [clients, setClients] = useState([]);
  const [partners, setPartners] = useState([]);
  const [countries] = useState([
    "Afghanistan",
    "Albania",
    "Algeria",
    "Andorra",
    "Angola",
    "Antigua and Barbuda",
    "Argentina",
    "Armenia",
    "Australia",
    "Austria",
    "Azerbaijan",
    "Bahamas",
    "Bahrain",
    "Bangladesh",
    "Barbados",
    "Belarus",
    "Belgium",
    "Belize",
    "Benin",
    "Bhutan",
    "Bolivia",
    "Bosnia and Herzegovina",
    "Botswana",
    "Brazil",
    "Brunei",
    "Bulgaria",
    "Burkina Faso",
    "Burundi",
    "Cabo Verde",
    "Cambodia",
    "Cameroon",
    "Canada",
    "Central African Republic",
    "Chad",
    "Chile",
    "China",
    "Colombia",
    "Comoros",
    "Congo",
    "Costa Rica",
    "Croatia",
    "Cuba",
    "Cyprus",
    "Czech Republic",
    "Democratic Republic of the Congo",
    "Denmark",
    "Djibouti",
    "Dominica",
    "Dominican Republic",
    "Ecuador",
    "Egypt",
    "El Salvador",
    "Equatorial Guinea",
    "Eritrea",
    "Estonia",
    "Eswatini",
    "Ethiopia",
    "Fiji",
    "Finland",
    "France",
    "Gabon",
    "Gambia",
    "Georgia",
    "Germany",
    "Ghana",
    "Greece",
    "Grenada",
    "Guatemala",
    "Guinea",
    "Guinea-Bissau",
    "Guyana",
    "Haiti",
    "Honduras",
    "Hong Kong",
    "Hungary",
    "Iceland",
    "India",
    "Indonesia",
    "Iran",
    "Iraq",
    "Ireland",
    "Israel",
    "Italy",
    "Ivory Coast",
    "Jamaica",
    "Japan",
    "Jordan",
    "Kazakhstan",
    "Kenya",
    "Kiribati",
    "Kuwait",
    "Kyrgyzstan",
    "Laos",
    "Latvia",
    "Lebanon",
    "Lesotho",
    "Liberia",
    "Libya",
    "Liechtenstein",
    "Lithuania",
    "Luxembourg",
    "Madagascar",
    "Malawi",
    "Malaysia",
    "Maldives",
    "Mali",
    "Malta",
    "Marshall Islands",
    "Mauritania",
    "Mauritius",
    "Mexico",
    "Micronesia",
    "Moldova",
    "Monaco",
    "Mongolia",
    "Montenegro",
    "Morocco",
    "Mozambique",
    "Myanmar",
    "Namibia",
    "Nauru",
    "Nepal",
    "Netherlands",
    "New Zealand",
    "Nicaragua",
    "Niger",
    "Nigeria",
    "North Korea",
    "North Macedonia",
    "Norway",
    "Oman",
    "Pakistan",
    "Palau",
    "Palestine",
    "Panama",
    "Papua New Guinea",
    "Paraguay",
    "Peru",
    "Philippines",
    "Poland",
    "Portugal",
    "Qatar",
    "Romania",
    "Russia",
    "Rwanda",
    "Saint Kitts and Nevis",
    "Saint Lucia",
    "Saint Vincent and the Grenadines",
    "Samoa",
    "San Marino",
    "Sao Tome and Principe",
    "Saudi Arabia",
    "Senegal",
    "Serbia",
    "Seychelles",
    "Sierra Leone",
    "Singapore",
    "Slovakia",
    "Slovenia",
    "Solomon Islands",
    "Somalia",
    "South Africa",
    "South Korea",
    "South Sudan",
    "Spain",
    "Sri Lanka",
    "Sudan",
    "Suriname",
    "Sweden",
    "Switzerland",
    "Syria",
    "Taiwan",
    "Tajikistan",
    "Tanzania",
    "Thailand",
    "Timor-Leste",
    "Togo",
    "Tonga",
    "Trinidad and Tobago",
    "Tunisia",
    "Turkey",
    "Turkmenistan",
    "Tuvalu",
    "Uganda",
    "Ukraine",
    "United Arab Emirates",
    "United Kingdom",
    "United States",
    "Uruguay",
    "Uzbekistan",
    "Vanuatu",
    "Vatican City",
    "Venezuela",
    "Vietnam",
    "Yemen",
    "Zambia",
    "Zimbabwe",
  ]);
  const [loiOptions] = useState(Array.from({ length: 60 }, (_, i) => i + 1));
  const [taCategories] = useState(["B2B", "B2C", "HC - HCP", "HC - Patient"]);

  const [broaderCategories] = useState([
    "Advertiser/Marketing/Media DM",
    "Advertising/Media DMs",
    "Air Travelers",
    "App Developers",
    "Asthma Patients",
    "Automobile Intenders",
    "Automobile Owners",
    "BDMs",
    "Bank account holders",
    "Broadcasters on a mobile live streaming",
    "CXOs",
    "Cancer patients",
    "Caregivers",
    "Cat and Dog owner",
    "Dairy Consumers",
    "Data Collection Group",
    "Dealers/Retailers",
    "Dermatitis patients",
    "Dermatologists",
    "Diabetes patients",
    "Educators",
    "Electronic appliance User/Owner/Intender",
    "Endocrinologists",
    "Energy influencers",
    "Farmers",
    "Financial DMs",
    "Fleet Owner/DMs",
    "Gen pop",
    "General Physician",
    "HR DMs",
    "Hematologists",
    "Hispanics",
    "Home owners",
    "Household decision makers",
    "IT/B DMs",
    "IT DMs",
    "IT Professionals",
    "Insurance purchasers",
    "Journalists",
    "Kids",
    "Liqour consumers",
    "Loyalty Members",
    "Manager & above",
    "Marketing DMs",
    "Medical Directors",
    "Medical/Pharmacy Directors",
    "Medical oncologist",
    "NGO Employees",
    "Nephrologist",
    "Neuro-oncologist",
    "Oncologists",
    "Opinion Elites",
    "PC Buyers",
    "PC Intenders",
    "Parents of kids",
    "Payers",
    "Pediatric Derms",
    "Pharmacy Directors",
    "Printer users",
    "Publisher",
    "Purchase Decision Makers and Influencers",
    "Secondary Research Group",
    "Social Media Users",
    "Teachers",
    "Teens",
    "Users of mobile live video streaming pla",
    "Veterinarian",
    "Webcam Users",
    "Others",
  ]);

  const [modes] = useState(["Online", "Offline", "Both"]);
  const [irOptions] = useState(Array.from({ length: 100 }, (_, i) => i + 1));

  const defaultFormData = {
    bid_number: "", // Leave this empty, will be filled by API
    bid_date: new Date().toISOString().split("T")[0],
    study_name: "",
    methodology: "",
    sales_contact: "",
    vm_contact: "",
    client: "",
    project_requirement: "",
    partners: [],
    loi: [],
    countries: [],
    target_audiences: [
      {
        name: "Audience - 1",
        ta_category: "",
        broader_category: "",
        exact_ta_definition: "",
        mode: "",
        sample_required: "",
        is_best_efforts: false,
        ir: "",
        comments: "",
      },
    ],
  };

  const [formData, setFormData] = useState(defaultFormData);
  const [selectedPartners, setSelectedPartners] = useState([]);
  const [selectedLOIs, setSelectedLOIs] = useState([]);
  const [distributionModalOpen, setDistributionModalOpen] = useState(false);
  const [sampleDistribution, setSampleDistribution] = useState({});
  const [loading, setLoading] = useState(true);
  const [deletedAudienceIds, setDeletedAudienceIds] = useState([]);

  // Add debug logging for deletedAudienceIds
  useEffect(() => {
    console.log("Current deletedAudienceIds:", deletedAudienceIds);
  }, [deletedAudienceIds]);

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true);
        // Reset deletedAudienceIds when loading a new bid
        setDeletedAudienceIds([]);

        console.log(
          "Starting loadInitialData, isEditMode:",
          isEditMode,
          "bidId:",
          bidId,
        );

        // Get next bid number first if it's a new bid
        if (!isEditMode) {
          try {
            const bidNumberResponse = await axios.get("/api/bids/next-number");
            setFormData({
              ...defaultFormData,
              bid_number: bidNumberResponse.data.next_bid_number,
            });
          } catch (error) {
            console.error("Error getting next bid number:", error);
          }
        }

        if (isEditMode && bidId) {
          console.log("Fetching bid data for ID:", bidId);
          try {
            const response = await axios.get(`/api/bids/${bidId}`);
            const bidData = response.data;

            console.log("Received bid data:", bidData);
            console.log("Partners from API:", bidData.partners);

            // Convert partners and loi to arrays if they're not already
            // Extract just the IDs from the partners array
            const partnersArray = bidData.partners
              ? Array.isArray(bidData.partners)
                ? bidData.partners.map((p) => p.id || p)
                : [bidData.partners.id || bidData.partners]
              : [];
            const loiArray = bidData.loi
              ? Array.isArray(bidData.loi)
                ? bidData.loi
                : [bidData.loi]
              : [];

            console.log("Processed partners array:", partnersArray);

            // Sort audiences by ID to maintain consistent database order, then renumber sequentially
            const sortedAudiences = (bidData.target_audiences || []).sort((a, b) => (a.id || 0) - (b.id || 0));
            // Renumber audiences sequentially based on their sorted database ID order
            const processedAudiences = sortedAudiences.map((audience, index) => ({
              ...audience,
              name: `Audience - ${index + 1}`,
              uniqueId: `audience-${index}`, // Ensure uniqueId matches the new index
            }));

            console.log(
              "Loading audiences with IDs:",
              processedAudiences.map((a) => ({ name: a.name, id: a.id })),
            );
            console.log(
              "Initial deletedAudienceIds before setting formData:",
              deletedAudienceIds,
            );

            setFormData((prevData) => ({
              ...prevData,
              ...bidData,
              partners: partnersArray,
              loi: loiArray,
              countries: Array.isArray(bidData.countries)
                ? bidData.countries
                : [],
              target_audiences: processedAudiences,
            }));

            console.log(
              "FormData set in edit mode, current deletedAudienceIds:",
              deletedAudienceIds,
            );

            // Set selected partners and LOIs
            setSelectedPartners(partnersArray);
            setSelectedLOIs(loiArray);
          } catch (error) {
            console.error("Error fetching bid data:", error);
          }
        }

        // Load reference data
        try {
          const [salesRes, vmRes, clientsRes, partnersRes] = await Promise.all([
            axios.get("/api/sales"),
            axios.get("/api/vms"),
            axios.get("/api/clients"),
            axios.get("/api/partners"),
          ]);

          console.log("Available partners from API:", partnersRes.data);

          setSalesContacts(salesRes.data);
          setVmContacts(vmRes.data);
          setClients(clientsRes.data);
          setPartners(partnersRes.data);
        } catch (error) {
          console.error("Error loading reference data:", error);
        }
      } catch (error) {
        console.error("Error in loadInitialData:", error);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, [bidId, isEditMode]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleTargetAudienceChange = (index, field, value) => {
    setFormData((prev) => {
      const newTargetAudiences = [...prev.target_audiences];
      newTargetAudiences[index] = {
        ...newTargetAudiences[index],
        [field]: value,
        // Clear sample_required if best efforts is checked
        ...(field === "is_best_efforts" && value === true
          ? { sample_required: "" }
          : {}),
      };
      return {
        ...prev,
        target_audiences: newTargetAudiences,
      };
    });
  };

  // Utility function to relabel all audience names sequentially
  const relabelAudienceNames = (audiences) => {
    return audiences.map((audience, index) => ({
      ...audience,
      name: `Audience - ${index + 1}`,
      uniqueId: `audience-${index}`, // Ensure uniqueId matches the index
    }));
  };

  const addTargetAudience = () => {
    setFormData((prev) => {
      const newAudiences = [
        ...prev.target_audiences,
        {
          ta_category: "",
          broader_category: "",
          exact_ta_definition: "",
          mode: "",
          sample_required: "",
          is_best_efforts: false,
          ir: "",
          comments: "",
        },
      ];
      return {
        ...prev,
        target_audiences: relabelAudienceNames(newAudiences),
      };
    });
  };

  const removeTargetAudience = (index) => {
    const removed = formData.target_audiences[index];
    console.log(
      "Removing audience at index:",
      index,
      "Audience data:",
      removed,
    );

    // Only track deletion if this audience has an ID (exists in database)
    if (removed && removed.id && typeof removed.id === "number") {
      console.log("Adding audience ID to deletedAudienceIds:", removed.id);
      setDeletedAudienceIds((prevIds) => {
        const newIds = [...prevIds, removed.id];
        console.log("Updated deletedAudienceIds:", newIds);
        return newIds;
      });
    } else {
      console.log("No valid ID found for removed audience:", removed);
    }

    setFormData((prev) => {
      const newAudiences = prev.target_audiences.filter((_, i) => i !== index);
      return {
        ...prev,
        target_audiences: relabelAudienceNames(newAudiences),
      };
    });
    setSampleDistribution({});
  };

  const handleMultipleSelect = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSampleRequiredChange = (index, value) => {
    handleTargetAudienceChange(index, "sample_required", value);
  };

  const handleSampleRequiredBlur = (index) => {
    // Remove auto-distribution on blur
    // We'll only handle distribution when clicking Next
  };

  const handleCountryChange = async (event) => {
    const selectedCountries = Array.isArray(event.target.value)
      ? event.target.value
      : [];
    setFormData((prev) => ({
      ...prev,
      countries: selectedCountries,
    }));
  };

  // Keep both distribution change handlers
  const handlePartnerLOIChange = (type, value) => {
    // Ensure value is always an array
    const arrayValue = Array.isArray(value) ? value : [];

    if (type === "partners") {
      console.log("Setting partners to:", arrayValue);
      // We're already getting IDs from the Select component
      setSelectedPartners(arrayValue);
      setFormData((prev) => ({ ...prev, partners: arrayValue }));
    } else if (type === "loi") {
      setSelectedLOIs(arrayValue);
      setFormData((prev) => ({ ...prev, loi: arrayValue }));
    }
  };

  const handleDistributionChange = (
    country,
    audienceIndex,
    value,
    isBEMax = false,
  ) => {
    console.log(`=== DISTRIBUTION CHANGE DEBUG ===`);
    console.log(`Country: ${country}, Index: ${audienceIndex}, Value: ${value}, isBEMax: ${isBEMax}`);
    console.log(`Audience at index ${audienceIndex}:`, formData.target_audiences?.[audienceIndex]);
    
    setSampleDistribution((prev) => {
      const currentValue =
        prev[country]?.[`audience-${audienceIndex}`]?.value ?? "";
      const currentIsBEMax =
        prev[country]?.[`audience-${audienceIndex}`]?.isBEMax || false;

      console.log(`Previous value: ${currentValue}, Previous isBEMax: ${currentIsBEMax}`);

      const newDistribution = {
        ...prev,
        [country]: {
          ...prev[country],
          [`audience-${audienceIndex}`]: {
            value: isBEMax ? "" : value === "" ? "" : parseInt(value) || "",
            isBEMax: isBEMax,
          },
        },
      };

      console.log(`New distribution for ${country}:`, newDistribution[country]);
      return newDistribution;
    });
  };

  const validateDistribution = () => {
    let isValid = true;
    const errors = [];

    formData.target_audiences.forEach((audience, index) => {
      // Check if all countries have either a numeric value or BE/Max selected
      const hasEmptyCountries = formData.countries.some((country) => {
        const distribution = sampleDistribution[country]?.[`audience-${index}`];
        return (
          !distribution || (distribution.value === "" && !distribution.isBEMax)
        );
      });

      if (hasEmptyCountries) {
        isValid = false;
        errors.push(
          `${audience.name}: All countries must have either a numeric value or BE/Max selected`,
        );
        return;
      }

      // For audiences with numeric sample_required, validate total matches
      if (!audience.is_best_efforts && audience.sample_required) {
        const total = Object.values(sampleDistribution).reduce(
          (sum, country) => {
            const value = country[`audience-${index}`]?.value;
            return sum + (value || 0);
          },
          0,
        );
        const required = parseInt(audience.sample_required);

        if (total !== required) {
          isValid = false;
          errors.push(
            `${audience.name}: Total (${total}) does not match required samples (${required})`,
          );
        }
      }
    });

    if (!isValid) {
      alert(errors.join("\n"));
    }
    return isValid;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (!validateForm()) {
        return;
      }

      console.log("=== SUBMIT DEBUG - START ===");
      console.log("Original formData.target_audiences:", formData.target_audiences.map(a => ({ 
        id: a.id, 
        name: a.name, 
        uniqueId: a.uniqueId,
        originalIndex: formData.target_audiences.indexOf(a)
      })));

      // Sort audiences by ID first to ensure consistent database order
      const sortedAudiences = [...formData.target_audiences].sort((a, b) => {
        if (a.id && b.id) return a.id - b.id;
        if (a.id && !b.id) return -1;
        if (!a.id && b.id) return 1;
        return 0;
      });

      console.log("After sorting by ID:", sortedAudiences.map(a => ({ 
        id: a.id, 
        name: a.name, 
        uniqueId: a.uniqueId,
        sortedIndex: sortedAudiences.indexOf(a)
      })));

      // Renumber audiences sequentially based on their sorted database ID order
      const relabeledAudiences = sortedAudiences.map((audience, index) => ({
        ...audience,
        name: `Audience - ${index + 1}`,
        uniqueId: `audience-${index}`,
      }));

      console.log("After relabeling:", relabeledAudiences.map(a => ({ 
        id: a.id, 
        name: a.name, 
        uniqueId: a.uniqueId,
        finalIndex: relabeledAudiences.indexOf(a)
      })));

      // Initialize sample distribution with existing data in edit mode
      const initialDistribution = {};
      formData.countries.forEach((country) => {
        initialDistribution[country] = {};
        relabeledAudiences.forEach((audience, index) => {
          const existingSample = audience.country_samples?.[country];
          initialDistribution[country][`audience-${index}`] = {
            value: existingSample?.is_best_efforts
              ? ""
              : existingSample?.sample_size || "",
            isBEMax: existingSample?.is_best_efforts || false,
          };
          console.log(`Distribution setup for ${country}, audience-${index}:`, {
            audienceId: audience.id,
            audienceName: audience.name,
            existingSample,
            distributionValue: initialDistribution[country][`audience-${index}`]
          });
        });
      });

      console.log("Final initialDistribution:", initialDistribution);
      setSampleDistribution(initialDistribution);

      // Set relabeled audiences in state
      setFormData((prev) => ({
        ...prev,
        target_audiences: relabeledAudiences,
      }));

      console.log("=== SUBMIT DEBUG - END ===");
      setDistributionModalOpen(true);
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to process form data");
    }
  };

  // Update validation to check for partners, LOI and countries
  const validateForm = () => {
    if (!formData.study_name) {
      alert("Please enter a study name");
      return false;
    }
    if (!formData.methodology) {
      alert("Please select a methodology");
      return false;
    }
    if (!formData.sales_contact) {
      alert("Please select a sales contact");
      return false;
    }
    if (!formData.vm_contact) {
      alert("Please select a VM contact");
      return false;
    }
    if (!formData.client) {
      alert("Please select a client");
      return false;
    }
    if (!formData.project_requirement) {
      alert("Please enter project requirements");
      return false;
    }
    if (formData.countries.length === 0) {
      alert("Please select at least one country");
      return false;
    }
    if (selectedPartners.length === 0 && formData.partners.length === 0) {
      alert("Please select at least one partner");
      return false;
    }
    if (selectedLOIs.length === 0 && formData.loi.length === 0) {
      alert("Please select at least one LOI");
      return false;
    }

    // Validate each target audience
    for (const audience of formData.target_audiences) {
      if (!audience.is_best_efforts && !audience.sample_required) {
        alert(
          "Please enter sample required or check Best Efforts/Maximum Possible",
        );
        return false;
      }
    }
    return true;
  };

  // Update the handleSaveDistribution function
  const handleSaveDistribution = async () => {
    try {
      if (!validateDistribution()) {
        return;
      }

      // Capture current deletedAudienceIds state at submission time
      const currentDeletedIds = [...deletedAudienceIds];
      console.log(
        "Captured deletedAudienceIds at submission:",
        currentDeletedIds,
      );

      console.log("=== DISTRIBUTION MAPPING DEBUG ===");
      console.log("Current formData.target_audiences before processing:", 
        formData.target_audiences.map((a, i) => ({
          index: i,
          id: a.id,
          name: a.name,
          uniqueId: a.uniqueId
        }))
      );

      // Sort audiences by ID to match backend expectation, then renumber
      const sortedAudiences = [...formData.target_audiences].sort((a, b) => {
        if (a.id && b.id) return a.id - b.id;
        if (a.id && !b.id) return -1;
        if (!a.id && b.id) return 1;
        return 0;
      });

      console.log("After sorting by ID:", 
        sortedAudiences.map((a, i) => ({
          index: i,
          id: a.id,
          name: a.name,
          originalName: a.name
        }))
      );

      // Renumber audiences sequentially based on their sorted database ID order
      const relabeledAudiences = sortedAudiences.map((audience, index) => ({
        ...audience,
        name: `Audience - ${index + 1}`,
        uniqueId: `audience-${index}`,
      }));

      console.log("After relabeling:", 
        relabeledAudiences.map((a, i) => ({
          index: i,
          id: a.id,
          name: a.name,
          newName: a.name
        }))
      );

      // Create mapping from old positions to new positions
      const originalToSortedMapping = {};
      formData.target_audiences.forEach((audience, originalIndex) => {
        const newIndex = relabeledAudiences.findIndex(a => a.id === audience.id);
        if (newIndex !== -1) {
          originalToSortedMapping[originalIndex] = newIndex;
          console.log(`Mapping: original index ${originalIndex} (ID: ${audience.id}) -> new index ${newIndex}`);
        }
      });

      console.log("Index mapping:", originalToSortedMapping);
      console.log("Sample distribution before remapping:", sampleDistribution);

      // Remap sample distribution to match the new sorted order
      const remappedSampleDistribution = {};
      formData.countries.forEach(country => {
        remappedSampleDistribution[country] = {};
        
        Object.entries(sampleDistribution[country] || {}).forEach(([key, value]) => {
          const match = key.match(/^audience-(\d+)$/);
          if (match) {
            const originalIndex = parseInt(match[1]);
            const newIndex = originalToSortedMapping[originalIndex];
            if (newIndex !== undefined) {
              const newKey = `audience-${newIndex}`;
              remappedSampleDistribution[country][newKey] = value;
              console.log(`Remapping ${country}: ${key} -> ${newKey}`, value);
            }
          }
        });
      });

      console.log("Sample distribution after remapping:", remappedSampleDistribution);

      // Update formData with the new distribution using remapped data
      const updatedFormData = {
        ...formData,
        target_audiences: relabeledAudiences.map((audience, index) => ({
          ...audience,
          sample_required: audience.is_best_efforts
            ? 0
            : parseInt(audience.sample_required) || 0,
          ir: parseInt(audience.ir) || 0,
          country_samples: Object.fromEntries(
            formData.countries.map((country) => {
              const distribution = remappedSampleDistribution[country]?.[
                `audience-${index}`
              ] || { value: 0, isBEMax: false };
              console.log(`Final mapping for ${country}, audience-${index}:`, distribution);
              return [
                country,
                {
                  sample_size: distribution.value || 0,
                  is_best_efforts: distribution.isBEMax,
                },
              ];
            }),
          ),
        })),
      };

      console.log("Final updated audiences with country samples:", 
        updatedFormData.target_audiences.map(a => ({
          id: a.id,
          name: a.name,
          country_samples: a.country_samples
        }))
      );

      // Create request payload with deleted_audience_ids explicitly included
      const requestPayload = {
        ...updatedFormData,
        deleted_audience_ids: currentDeletedIds || [],
      };

      console.log("=== END DISTRIBUTION MAPPING DEBUG ===");

      if (isEditMode) {
        await axios.put(`/api/bids/${bidId}`, requestPayload, {
          headers: {
            "Content-Type": "application/json",
          },
        });
        navigate(`/bids/partner/${bidId}`);
      } else {
        const response = await axios.post("/api/bids", requestPayload, {
          headers: {
            "Content-Type": "application/json",
          },
        });
        await axios.put(`/api/bids/${response.data.bid_id}/partners`, {
          partners: selectedPartners,
          lois: selectedLOIs,
        });
        navigate(`/bids/partner/${response.data.bid_id}`);
      }

      setDistributionModalOpen(false);
    } catch (error) {
      console.error("Error saving distribution:", error);
      if (error.response) {
        console.error("Error response data:", error.response.data);
        console.error("Error response status:", error.response.status);
        alert(
          `Failed to save sample distribution: ${error.response.data.error || error.message}`,
        );
      } else if (error.request) {
        console.error("Error request:", error.request);
        alert("Failed to save sample distribution: No response from server");
      } else {
        console.error("Error message:", error.message);
        alert(`Failed to save sample distribution: ${error.message}`);
      }
    }
  };

  const copyTargetAudience = (index) => {
    setFormData((prev) => {
      const audienceToCopy = { ...prev.target_audiences[index] };
      // Remove the name, will relabel below
      delete audienceToCopy.name;
      const newAudiences = [...prev.target_audiences, audienceToCopy];
      return {
        ...prev,
        target_audiences: relabelAudienceNames(newAudiences),
      };
    });
  };

  return (
    <div className="bid-form-container">
      {loading ? (
        <div
          style={{ display: "flex", justifyContent: "center", padding: "20px" }}
        >
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
                  <MenuItem value="quant">quant</MenuItem>
                  <MenuItem value="qual">qual</MenuItem>
                  <MenuItem value="both">both</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth required>
                <InputLabel>Sales Contact</InputLabel>
                <Select
                  name="sales_contact"
                  value={formData.sales_contact}
                  onChange={handleInputChange}
                >
                  {salesContacts.map((contact) => (
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
                  {vmContacts.map((contact) => (
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
                  {clients.map((client) => (
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
                  onChange={(e) =>
                    handlePartnerLOIChange("partners", e.target.value)
                  }
                  renderValue={(selected) => {
                    // Find partner names for selected IDs
                    const selectedNames = selected
                      .map(
                        (id) => partners.find((p) => p.id === id)?.partner_name,
                      )
                      .filter(Boolean);
                    return selectedNames.join(", ");
                  }}
                >
                  {partners.map((partner) => (
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
                  onChange={(e) =>
                    handlePartnerLOIChange("loi", e.target.value)
                  }
                >
                  {loiOptions.map((minutes) => (
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
                  {countries.map((country) => (
                    <MenuItem key={country} value={country}>
                      {country}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </div>
            <h3 className="section-title">Target Audiences</h3>
            {Array.isArray(formData.target_audiences) &&
              formData.target_audiences.map((audience, index) => (
                <Paper
                  key={index}
                  elevation={3}
                  className="audience-paper"
                  style={{ padding: "20px", marginBottom: "20px" }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "20px",                    }}
                  >
                    <h3 style={{ margin: 0 }}>Audience - {index + 1}</h3>
                    <div>
                      <Button
                        variant="outlined"
                        color="primary"
                        onClick={() => copyTargetAudience(index)}
                        style={{ marginRight: "10px" }}
                      >
                        Copy
                      </Button>
                      <Button
                        variant="outlined"
                        color="error"
                        onClick={() => removeTargetAudience(index)}
                      >
                        Remove
                      </Button>
                    </div>
                  </div>
                  <div className="target-audience-grid">
                    <FormControl fullWidth required>
                      <InputLabel>TA Category</InputLabel>
                      <Select
                        value={audience.ta_category}
                        onChange={(e) =>
                          handleTargetAudienceChange(
                            index,
                            "ta_category",
                            e.target.value,
                          )
                        }
                      >
                        {taCategories.map((category) => (
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
                        onChange={(e) =>
                          handleTargetAudienceChange(
                            index,
                            "broader_category",
                            e.target.value,
                          )
                        }
                      >
                        {broaderCategories.map((category) => (
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
                      onChange={(e) =>
                        handleTargetAudienceChange(
                          index,
                          "exact_ta_definition",
                          e.target.value,
                        )
                      }
                    />

                    <FormControl fullWidth required>
                      <InputLabel>Mode</InputLabel>
                      <Select
                        value={audience.mode || ""}
                        onChange={(e) =>
                          handleTargetAudienceChange(
                            index,
                            "mode",
                            e.target.value,
                          )
                        }
                        fullWidth
                        margin="normal"
                      >
                        <MenuItem value="Online">Online</MenuItem>
                        <MenuItem value="CATI">CATI</MenuItem>
                        <MenuItem value="F2F">F2F</MenuItem>
                      </Select>
                    </FormControl>

                    <TextField
                      label="IR (%)"
                      type="number"
                      value={audience.ir || ""}
                      onChange={(e) =>
                        handleTargetAudienceChange(index, "ir", e.target.value)
                      }
                      fullWidth
                      margin="normal"
                      inputProps={{
                        min: 0,
                        max: 100,
                        step: 1,
                      }}
                    />

                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "20px",
                        width: "100%",
                      }}
                    >
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={audience.is_best_efforts || false}
                            onChange={(e) =>
                              handleTargetAudienceChange(
                                index,
                                "is_best_efforts",
                                e.target.checked,
                              )
                            }
                          />
                        }
                        label="BE/Max"
                      />
                      {!audience.is_best_efforts && (
                        <TextField
                          required
                          fullWidth
                          label="Sample Required"
                          type="number"
                          value={audience.sample_required}
                          onChange={(e) =>
                            handleTargetAudienceChange(
                              index,
                              "sample_required",
                              e.target.value,
                            )
                          }
                        />
                      )}
                    </div>

                    <TextField
                      fullWidth
                      multiline
                      rows={2}
                      label="Comments"
                      value={audience.comments}
                      onChange={(e) =>
                        handleTargetAudienceChange(
                          index,
                          "comments",
                          e.target.value,
                        )
                      }
                      className="audience-comments"
                    />
                  </div>
                </Paper>
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
              <Button onClick={() => navigate("/bids")}>CANCEL</Button>
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
          {console.log("=== MODAL RENDER DEBUG ===") || 
           console.log("Modal audiences (raw):", formData.target_audiences) ||
           console.log("Modal audiences (with indices):", formData.target_audiences?.map((a, i) => ({
             index: i,
             id: a.id,
             name: a.name,
             uniqueId: a.uniqueId
           }))) ||
           console.log("Sample distribution keys:", Object.keys(sampleDistribution)) ||
           console.log("Full sample distribution:", sampleDistribution)}
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Country</TableCell>
                  {formData?.target_audiences?.map((audience, index) => {
                    console.log(`Header - Index ${index}:`, {
                      id: audience.id,
                      name: audience.name,
                      uniqueId: audience.uniqueId,
                      is_best_efforts: audience.is_best_efforts,
                      sample_required: audience.sample_required
                    });
                    return (
                      <TableCell key={`header-${index}`} align="center">
                        {audience.name}
                        <br />
                        <small>ID: {audience.id || 'NEW'}</small>
                        <br />
                        {audience.is_best_efforts
                          ? "(Best Efforts)"
                          : `(Required: ${audience.sample_required})`}
                      </TableCell>
                    );
                  })}
                </TableRow>
              </TableHead>
              <TableBody>
                {formData?.countries?.map((country) => (
                  <TableRow key={country}>
                    <TableCell>{country}</TableCell>
                    {formData?.target_audiences?.map((audience, index) => {
                      const distributionKey = `audience-${index}`;
                      const distributionData = sampleDistribution[country]?.[distributionKey];
                      console.log(`Body - ${country}, Index ${index} (${distributionKey}):`, {
                        audienceId: audience.id,
                        audienceName: audience.name,
                        distributionData,
                        distributionExists: !!distributionData
                      });
                      
                      return (
                        <TableCell key={`body-${index}`} align="center">
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "8px",
                              justifyContent: "center",
                            }}
                          >
                            <TextField
                              type="number"
                              size="small"
                              value={
                                distributionData?.isBEMax
                                  ? ""
                                  : (distributionData?.value ?? "")
                              }
                              onChange={(e) => {
                                console.log(`TextField change - ${country}, index ${index}:`, e.target.value);
                                handleDistributionChange(
                                  country,
                                  index,
                                  e.target.value,
                                );
                              }}
                              disabled={distributionData?.isBEMax}
                              inputProps={{ min: 0 }}
                              style={{ width: "100px" }}
                              placeholder={`Idx:${index}`}
                            />
                            <FormControlLabel
                              control={
                                <Checkbox
                                  checked={distributionData?.isBEMax || false}
                                  onChange={(e) => {
                                    console.log(`Checkbox change - ${country}, index ${index}:`, e.target.checked);
                                    handleDistributionChange(
                                      country,
                                      index,
                                      "",
                                      e.target.checked,
                                    );
                                  }}
                                />
                              }
                              label="BE/Max"
                            />
                          </div>
                        </TableCell>
                      );
                    })}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDistributionModalOpen(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSaveDistribution}
            variant="contained"
            color="primary"
            disabled={
              !formData?.target_audiences?.length ||
              !formData?.countries?.length
            }
          >
            Save & Continue
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default BasicDetails;