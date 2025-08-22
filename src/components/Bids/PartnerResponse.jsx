import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
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
  Box,
} from "@mui/material";
import axios from "../../api/axios";
import "./Bids.css";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import Tooltip from "@mui/material/Tooltip";
import IconButton from "@mui/material/IconButton";

function PartnerResponse() {
  const navigate = useNavigate();
  const { bidId } = useParams();
  const [selectedPartner, setSelectedPartner] = useState(0);
  const [selectedLOI, setSelectedLOI] = useState("");
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
  const [linkError, setLinkError] = useState("");
  const [copied, setCopied] = useState(false);

  const currentPartner = partners[selectedPartner];

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [bidResponse, partnerResponse] = await Promise.all([
          axios.get(`/api/bids/${bidId}`),
          axios.get(`/api/bids/${bidId}/partner-responses`),
        ]);

        console.log("Bid Response:", bidResponse.data);
        console.log("Partner Response:", partnerResponse.data);

        setBidData(bidResponse.data);
        setPartners(bidResponse.data.partners || []);

        // Initialize responses with existing data
        const existingResponses = partnerResponse.data.responses || {};
        setResponses(existingResponses);
        setPartnerSettings(partnerResponse.data.settings || {});

        // Mark responses as initialized to prevent overwriting
        setResponsesInitialized(true);
      } catch (error) {
        console.error("Error fetching data:", error);
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

    const isComplete = partners.every((partner) =>
      bidData.loi.every((loi) => {
        const responseKey = `${partner.id}-${loi}`;
        const response = responses[responseKey];

        if (!response) return false;

        const allAudiencesComplete = bidData.target_audiences.every(
          (audience) => {
            const audienceResponse = response.audiences?.[audience.id];
            if (!audienceResponse) return false;

            const allCountriesComplete = Object.entries(
              audience.country_samples || {},
            ).every(([country]) => {
              const countryResponse = audienceResponse[country];
              if (!countryResponse) return false;

              // Check if country is passed - if so, it's valid
              if (countryResponse.pass === true) {
                return true;
              }

              // Check if either:
              // 1. It's BE/Max (commitment_type is 'be_max')
              // 2. It has a valid commitment value >= 0 (including 0)
              const hasValidCommitment =
                countryResponse.commitment_type === "be_max" ||
                (countryResponse.commitment !== undefined &&
                  countryResponse.commitment !== null &&
                  countryResponse.commitment !== "" &&
                  Number.isFinite(countryResponse.commitment) &&
                  countryResponse.commitment >= 0);

              // CPI must be >= 0 (allowing 0 for pass scenarios)
              const hasValidCPI =
                countryResponse.cpi !== undefined &&
                countryResponse.cpi !== null &&
                countryResponse.cpi !== "" &&
                Number.isFinite(countryResponse.cpi) &&
                countryResponse.cpi >= 0;

              return hasValidCommitment && hasValidCPI;
            });

            // Check if all countries are passed for this audience
            const allCountriesPassed = Object.entries(
              audience.country_samples || {},
            ).every(([country]) => {
              const countryResponse = audienceResponse[country];
              return countryResponse && countryResponse.pass === true;
            });

            // If all countries are passed, timeline can be 0
            // Otherwise, timeline must be > 0
            const hasValidTimeline = allCountriesPassed
              ? audienceResponse.timeline !== undefined &&
                audienceResponse.timeline !== null &&
                audienceResponse.timeline !== ""
              : audienceResponse.timeline > 0;

            return allCountriesComplete && hasValidTimeline;
          },
        );

        return allAudiencesComplete;
      }),
    );

    setAllResponsesComplete(isComplete);
  }, [responses, bidData, partners]);

  useEffect(() => {
    if (bidData && partners) {
      const initialStatus = {};
      partners.forEach((partner) => {
        bidData.loi.forEach((loi) => {
          initialStatus[`${partner.id}-${loi}`] = "unsaved";
        });
      });
      setSavingStatus(initialStatus);
    }
  }, [bidData, partners]);

  useEffect(() => {
    sessionStorage.setItem("partnerResponsesData", JSON.stringify(responses));
  }, [responses]);

  useEffect(() => {
    if (!responsesInitialized && bidData && partners && bidData.loi) {
      const initialResponses = { ...responses };

      partners.forEach((partner) => {
        bidData.loi.forEach((loi) => {
          const key = `${partner.id}-${loi}`;
          if (!initialResponses[key]) {
            initialResponses[key] = {
              partner_id: partner.id,
              loi: loi,
              status: "pending",
              currency: partnerSettings[partner.id]?.currency || "USD",
              pmf: "",
              audiences: {},
            };
          }

          // Ensure all audiences are present
          bidData.target_audiences.forEach((audience) => {
            if (!initialResponses[key].audiences[audience.id]) {
              initialResponses[key].audiences[audience.id] = {
                timeline: "",
                comments: "",
              };
            }
            // Ensure all countries are present for each audience
            Object.entries(audience.country_samples || {}).forEach(
              ([country, sample]) => {
                if (!initialResponses[key].audiences[audience.id][country]) {
                  initialResponses[key].audiences[audience.id][country] = {
                    commitment_type: "fixed",
                    commitment: 0,
                    cpi: 0,
                  };
                }
              },
            );
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
      console.log("Saving partner responses for bid:", bidId);

      // DEBUG: Show current responses state before saving
      alert(
        `DEBUG: About to save responses!\nBid ID: ${bidId}\nResponses count: ${Object.keys(responses).length}\nCurrent responses state: ${JSON.stringify(responses, null, 2)}`,
      );

      // Convert empty PMF to 0 before sending to backend
      const responsesToSend = {};
      Object.entries(responses).forEach(([key, response]) => {
        responsesToSend[key] = {
          ...response,
          pmf: response.pmf === "" ? 0 : response.pmf,
        };
      });

      console.log("Data being sent:", responsesToSend);

      // DEBUG: Show what we're sending to backend
      alert(
        `DEBUG: Data being sent to backend:\n${JSON.stringify(responsesToSend, null, 2)}`,
      );

      // Create a custom axios instance with longer timeout for this specific request
      const saveRequest = axios.create({
        timeout: 60000, // 60 seconds instead of 30
        baseURL: axios.defaults.baseURL,
      });

      // Add the same interceptors as the main axios instance
      const userData = localStorage.getItem("user");
      const headers = {};
      if (userData) {
        try {
          const user = JSON.parse(userData);
          headers["X-User-Id"] = user.id;
          headers["X-User-Team"] = user.team;
          headers["X-User-Role"] = user.role;
          headers["X-User-Name"] = user.name;
        } catch (error) {
          console.error("Error parsing user data:", error);
        }
      }

      // DEBUG: Show exactly what we're sending
      alert(
        `DEBUG: Backend API Call\nURL: /api/bids/${bidId}/partner-responses\nMethod: PUT\nData being sent:\n${JSON.stringify({ responses: responsesToSend }, null, 2)}`,
      );

      // DEBUG: Show specific pass field values
      let passFieldDebug = "DEBUG: Pass field values in data:\n";
      Object.entries(responsesToSend).forEach(([key, response]) => {
        Object.entries(response.audiences || {}).forEach(
          ([audienceId, audience]) => {
            Object.entries(audience).forEach(([field, value]) => {
              if (
                field !== "timeline" &&
                field !== "comments" &&
                typeof value === "object" &&
                value !== null
              ) {
                passFieldDebug += `Key: ${key}, Audience: ${audienceId}, Country: ${field}, pass: ${value.pass}\n`;
              }
            });
          },
        );
      });
      alert(passFieldDebug);

      // ADDITIONAL DEBUG: Check the exact structure being sent
      console.log("=== DEBUG: Detailed Data Structure ===");
      console.log("Full responsesToSend object:", responsesToSend);

      // Check each key specifically
      Object.keys(responsesToSend).forEach((key) => {
        console.log(`Key ${key} structure:`, responsesToSend[key]);
        if (responsesToSend[key]?.audiences) {
          Object.keys(responsesToSend[key].audiences).forEach((audienceId) => {
            console.log(
              `  Audience ${audienceId}:`,
              responsesToSend[key].audiences[audienceId],
            );
            Object.keys(responsesToSend[key].audiences[audienceId]).forEach(
              (field) => {
                if (field !== "timeline" && field !== "comments") {
                  console.log(
                    `    Field ${field}:`,
                    responsesToSend[key].audiences[audienceId][field],
                  );
                }
              },
            );
          });
        }
      });

      const response = await saveRequest.put(
        `/api/bids/${bidId}/partner-responses`,
        {
          responses: responsesToSend,
        },
        { headers },
      );

      console.log("Save response:", response.data);

      // DEBUG: Show what the backend returned
      alert(
        `DEBUG: Backend Response\nStatus: ${response.status}\nResponse Data:\n${JSON.stringify(response.data, null, 2)}`,
      );

      alert("Partner responses saved successfully");
    } catch (error) {
      console.error("Error saving partner responses:", error);
      console.error("Error details:", error.response?.data);

      let errorMessage = "Failed to save partner responses";
      if (error.code === "ECONNABORTED") {
        errorMessage =
          "Request timed out. The server may be processing a large amount of data. Please try again.";
      } else if (error.response?.data?.error) {
        errorMessage = `Failed to save partner responses: ${error.response.data.error}`;
      } else if (error.message) {
        errorMessage = `Failed to save partner responses: ${error.message}`;
      }

      alert(errorMessage);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Validate all responses are complete
      if (!allResponsesComplete) {
        alert("Please complete all partner responses before submitting");
        return;
      }

      // Create complete responses for all LOIs
      const updatedResponses = {};
      partners.forEach((partner) => {
        bidData.loi.forEach((loi) => {
          const key = `${partner.id}-${loi}`;

          // Create complete response structure for each LOI
          const response = {
            partner_id: partner.id,
            loi: loi,
            status: "submitted",
            currency: partnerSettings[partner.id]?.currency || "USD",
            pmf:
              partnerSettings[partner.id]?.pmf === ""
                ? 0
                : partnerSettings[partner.id]?.pmf || 0,
            audiences: {},
          };

          // Add audience data for each target audience
          bidData.target_audiences.forEach((audience) => {
            const audienceKey = `audience-${audience.id}`;
            response.audiences[audience.id] = {
              ...responses[key]?.audiences?.[audience.id],
              timeline: responses[key]?.audiences?.[audience.id]?.timeline || 0,
              comments:
                responses[key]?.audiences?.[audience.id]?.comments || "",
            };

            // Add country data for each audience
            Object.entries(audience.country_samples || {}).forEach(
              ([country, sample]) => {
                const countryData =
                  responses[key]?.audiences?.[audience.id]?.[country] || {};
                response.audiences[audience.id][country] = {
                  commitment_type: countryData.commitment_type || "fixed",
                  commitment:
                    countryData.commitment_type === "be_max"
                      ? 0
                      : countryData.commitment || 0,
                  cpi: countryData.cpi || 0,
                };
              },
            );
          });

          updatedResponses[key] = response;
        });
      });

      // Send all responses to backend
      const response = await axios.put(`/api/bids/${bidId}/partner-responses`, {
        responses: updatedResponses,
      });

      if (response.status === 200) {
        alert("Partner responses submitted successfully");
        navigate("/bids");
      }
    } catch (error) {
      console.error("Full error details:", error);
      console.error("Error response data:", error.response?.data);
      alert(
        `Error submitting responses: ${error.response?.data?.error || error.message}`,
      );
    }
  };

  const handleBack = () => {
    if (bidId.startsWith("temp_")) {
      // For new bids, preserve the form data
      navigate("/bids/new", {
        state: {
          preserveResponses: true,
          fromEdit: true,
        },
      });
    } else {
      // For existing bids, go back to edit mode
      navigate(`/bids/edit/${bidId}`, {
        state: { fromEdit: true },
      });
    }
  };

  const handlePMFChange = (partnerId, value) => {
    // Allow empty string in UI but store as 0 in settings
    const pmf = value === "" ? "" : parseFloat(value);
    setPartnerSettings((prev) => ({
      ...prev,
      [partnerId]: { ...prev[partnerId], pmf },
    }));

    // Update all responses for this partner with new PMF
    setResponses((prev) => {
      const updated = { ...prev };
      Object.keys(updated).forEach((key) => {
        if (key.startsWith(`${partnerId}-`)) {
          updated[key] = {
            ...updated[key],
            pmf: value === "" ? 0 : parseFloat(value), // Store as 0 in responses when empty
          };
        }
      });
      return updated;
    });
  };

  const handleGenerateLink = async () => {
    setLinkLoading(true);
    setLinkError("");
    try {
      const res = await axios.post(
        `/api/bids/${bidId}/partners/${currentPartner.id}/generate-link`,
      );
      setLinkData((prev) => ({
        ...prev,
        [currentPartner.id]: {
          link: res.data.link,
          expiresAt: res.data.expires_at,
        },
      }));
    } catch (err) {
      setLinkError("Failed to generate link");
    }
    setLinkLoading(false);
  };

  // Helper to format time remaining
  const getTimeRemaining = (expiresAt) => {
    if (!expiresAt) return "";
    const expiry = new Date(expiresAt);
    const now = new Date();
    const diffMs = expiry - now;
    if (diffMs <= 0) return "Expired";
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
          <Button onClick={() => navigate("/bids/new")}>Go Back</Button>
        </Paper>
      </div>
    );
  }

  if (!bidData) {
    return (
      <div className="partner-response-container">
        <Paper className="partner-response-form">
          <Typography>No bid data found</Typography>
          <Button onClick={() => navigate("/bids/new")}>Go Back</Button>
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
                onChange={(e) => {
                  const newLOI = e.target.value;
                  console.log(`=== DEBUG: LOI Changed ===`);
                  console.log("Previous LOI:", selectedLOI);
                  console.log("New LOI:", newLOI);
                  console.log("Current partner:", currentPartner?.id);
                  console.log("Responses state before change:", responses);

                  setSelectedLOI(newLOI);

                  // Log the state after a brief delay to see if it updates
                  setTimeout(() => {
                    console.log("Responses state after LOI change:", responses);
                    console.log(`Current key: ${currentPartner?.id}-${newLOI}`);
                    console.log(
                      `Responses for new LOI:`,
                      responses[`${currentPartner?.id}-${newLOI}`],
                    );
                  }, 100);
                }}
                displayEmpty
                placeholder="Select LOI"
              >
                <MenuItem value="" disabled>
                  Select LOI
                </MenuItem>
                {bidData.loi.map((loi) => (
                  <MenuItem key={loi} value={loi}>
                    {loi} mins
                  </MenuItem>
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
                      {linkLoading ? "Generating..." : "Generate Link"}
                    </Button>
                    {linkData[currentPartner.id] && (
                      <div>
                        <strong>Link:</strong>{" "}
                        <a
                          href={linkData[currentPartner.id].link}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {linkData[currentPartner.id].link}
                        </a>
                        <Tooltip
                          title={copied ? "Copied!" : "Copy link"}
                          open={copied}
                          onClose={() => setCopied(false)}
                        >
                          <IconButton
                            size="small"
                            onClick={() => {
                              navigator.clipboard.writeText(
                                linkData[currentPartner.id].link,
                              );
                              setCopied(true);
                              setTimeout(() => setCopied(false), 1200);
                            }}
                          >
                            <ContentCopyIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <br />
                        <strong>Expires At:</strong>{" "}
                        {getTimeRemaining(
                          linkData[currentPartner.id].expiresAt,
                        )}
                      </div>
                    )}
                    {linkError && (
                      <div style={{ color: "red" }}>{linkError}</div>
                    )}
                  </div>
                  <div className="partner-settings">
                    <FormControl className="currency-select">
                      <Select
                        value={
                          partnerSettings[currentPartner.id]?.currency || "USD"
                        }
                        onChange={(e) =>
                          setPartnerSettings((prev) => ({
                            ...prev,
                            [currentPartner.id]: {
                              ...prev[currentPartner.id],
                              currency: e.target.value,
                            },
                          }))
                        }
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
                      value={partnerSettings[currentPartner.id]?.pmf || ""}
                      onChange={(e) =>
                        handlePMFChange(currentPartner.id, e.target.value)
                      }
                      disabled={(() => {
                        // Check if any audience has all countries passed
                        return bidData.target_audiences.some((audience) => {
                          const countries = Object.keys(
                            audience.country_samples || {},
                          );
                          return (
                            countries.length > 0 &&
                            countries.every(
                              (country) =>
                                responses[`${currentPartner.id}-${selectedLOI}`]
                                  ?.audiences?.[audience.id]?.[country]?.pass,
                            )
                          );
                        });
                      })()}
                      sx={{
                        "& .MuiInputBase-root.Mui-disabled": {
                          backgroundColor: "#f5f5f5",
                          color: "#666",
                        },
                      }}
                    />
                  </div>

                  {bidData.target_audiences.map((audience, audienceIndex) => (
                    <div key={audience.id} className="audience-section">
                      <Box
                        display="flex"
                        justifyContent="space-between"
                        alignItems="center"
                        mb={2}
                      >
                        <Typography
                          variant="subtitle1"
                          className="audience-title"
                          sx={{ fontWeight: "bold" }}
                        >
                          Audience: {audience.ta_category} -{" "}
                          {audience.broader_category} - {audience.mode} - IR{" "}
                          {audience.ir}%
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2" fontSize="small">
                            Pass All Countries (LOI {selectedLOI})
                          </Typography>
                          <input
                            type="checkbox"
                            checked={(() => {
                              const countries = Object.keys(
                                audience.country_samples || {},
                              );
                              const currentKey = `${currentPartner.id}-${selectedLOI}`;
                              const allPassed =
                                countries.length > 0 &&
                                countries.every(
                                  (country) =>
                                    responses[currentKey]?.audiences?.[
                                      audience.id
                                    ]?.[country]?.pass,
                                );

                              // DEBUG: Checkbox state calculation
                              console.log(
                                `=== DEBUG: Checkbox State for LOI ${selectedLOI} ===`,
                              );
                              console.log("Current key:", currentKey);
                              console.log("Countries:", countries);
                              console.log(
                                "Responses for this key:",
                                responses[currentKey],
                              );
                              console.log("All countries passed:", allPassed);

                              countries.forEach((country) => {
                                const passValue =
                                  responses[currentKey]?.audiences?.[
                                    audience.id
                                  ]?.[country]?.pass;
                                console.log(
                                  `Country ${country}: pass=${passValue}`,
                                );
                              });

                              return allPassed;
                            })()}
                            onChange={(e) => {
                              const countries = Object.keys(
                                audience.country_samples || {},
                              );
                              const newPassValue = e.target.checked;

                              // DEBUG: Show what we're about to do
                              alert(
                                `DEBUG: Pass All Countries for LOI ${selectedLOI} clicked!\nAudience ID: ${audience.id}\nCountries: ${countries.join(", ")}\nNew Pass Value: ${newPassValue}\nCurrent Partner: ${currentPartner.id}\nSelected LOI: ${selectedLOI}\n\nCountry Samples Structure:\n${JSON.stringify(audience.country_samples, null, 2)}\n\nCheckbox checked state: ${e.target.checked}\nnewPassValue: ${newPassValue}`,
                              );

                              console.log(
                                "=== DEBUG: Pass All Countries for LOI ===",
                              );
                              console.log("Countries:", countries);
                              console.log("New Pass Value:", newPassValue);
                              console.log(
                                "Current Partner:",
                                currentPartner.id,
                              );
                              console.log("Selected LOI:", selectedLOI);
                              console.log(
                                "Current responses state:",
                                responses,
                              );

                              // DEBUG: Show audience.country_samples structure
                              console.log(
                                "audience.country_samples:",
                                audience.country_samples,
                              );
                              console.log(
                                "audience.country_samples keys:",
                                Object.keys(audience.country_samples || {}),
                              );
                              console.log(
                                "audience.country_samples values:",
                                Object.values(audience.country_samples || {}),
                              );

                              // DEBUG: Show the actual country data structure
                              console.log("Full audience object:", audience);
                              console.log(
                                "Country samples entries:",
                                Object.entries(audience.country_samples || {}),
                              );

                              setResponses((prev) => {
                                console.log("Previous responses state:", prev);

                                // Create a deep copy to avoid mutation issues
                                const updated = JSON.parse(
                                  JSON.stringify(prev),
                                );

                                // Update ONLY the CURRENT LOI, not all LOIs
                                const currentKey = `${currentPartner.id}-${selectedLOI}`;
                                console.log(
                                  `=== DEBUG: LOI-Specific Update ===`,
                                );
                                console.log(
                                  `Updating only LOI key: ${currentKey}`,
                                );

                                // Ensure the structure exists for this LOI
                                if (!updated[currentKey]) {
                                  updated[currentKey] = {
                                    partner_id: currentPartner.id,
                                    loi: selectedLOI,
                                    audiences: {},
                                  };
                                }

                                if (!updated[currentKey].audiences) {
                                  updated[currentKey].audiences = {};
                                }

                                if (
                                  !updated[currentKey].audiences[audience.id]
                                ) {
                                  updated[currentKey].audiences[audience.id] =
                                    {};
                                }

                                // Update timeline and comments for this LOI only
                                updated[currentKey].audiences[
                                  audience.id
                                ].timeline = newPassValue
                                  ? 0
                                  : prev[currentKey]?.audiences?.[audience.id]
                                      ?.timeline || "";
                                updated[currentKey].audiences[
                                  audience.id
                                ].comments = newPassValue
                                  ? "NA"
                                  : prev[currentKey]?.audiences?.[audience.id]
                                      ?.comments || "";

                                // Update each country for this LOI only
                                countries.forEach((country) => {
                                  console.log(
                                    `Setting pass=${newPassValue} for country: ${country} in LOI: ${selectedLOI}`,
                                  );

                                  if (
                                    !updated[currentKey].audiences[audience.id][
                                      country
                                    ]
                                  ) {
                                    updated[currentKey].audiences[audience.id][
                                      country
                                    ] = {};
                                  }

                                  // DEBUG: Show what we're setting for this country
                                  console.log(
                                    `Setting for country ${country} in LOI ${selectedLOI}: pass=${newPassValue}, commitment="${newPassValue ? "" : prev[currentKey]?.audiences?.[audience.id]?.[country]?.commitment || ""}", cpi="${newPassValue ? "" : prev[currentKey]?.audiences?.[audience.id]?.[country]?.cpi || ""}"`,
                                  );

                                  updated[currentKey].audiences[audience.id][
                                    country
                                  ] = {
                                    ...prev[currentKey]?.audiences?.[
                                      audience.id
                                    ]?.[country],
                                    pass: newPassValue,
                                    commitment: newPassValue
                                      ? ""
                                      : prev[currentKey]?.audiences?.[
                                          audience.id
                                        ]?.[country]?.commitment || "",
                                    cpi: newPassValue
                                      ? ""
                                      : prev[currentKey]?.audiences?.[
                                          audience.id
                                        ]?.[country]?.cpi || "",
                                  };
                                });

                                // CRITICAL FIX: Ensure all other LOIs for this partner have pass=false for this audience
                                // This prevents undefined values from being sent to backend
                                Object.keys(updated).forEach((key) => {
                                  if (
                                    key.startsWith(`${currentPartner.id}-`) &&
                                    key !== currentKey
                                  ) {
                                    console.log(
                                      `=== DEBUG: Initializing pass field for LOI key: ${key} ===`,
                                    );

                                    if (!updated[key]) {
                                      updated[key] = {
                                        partner_id: currentPartner.id,
                                        loi: key.split("-")[1],
                                        audiences: {},
                                      };
                                    }

                                    if (!updated[key].audiences) {
                                      updated[key].audiences = {};
                                    }

                                    if (!updated[key].audiences[audience.id]) {
                                      updated[key].audiences[audience.id] = {};
                                    }

                                    // Initialize each country with pass=false for other LOIs
                                    countries.forEach((country) => {
                                      if (
                                        !updated[key].audiences[audience.id][
                                          country
                                        ]
                                      ) {
                                        updated[key].audiences[audience.id][
                                          country
                                        ] = {};
                                      }

                                      // Only set pass=false if it's not already set
                                      if (
                                        updated[key].audiences[audience.id][
                                          country
                                        ].pass === undefined
                                      ) {
                                        console.log(
                                          `Setting pass=false for country ${country} in LOI ${key.split("-")[1]} (other LOI)`,
                                        );
                                        updated[key].audiences[audience.id][
                                          country
                                        ] = {
                                          ...updated[key].audiences[
                                            audience.id
                                          ][country],
                                          pass: false,
                                        };
                                      }
                                    });
                                  }
                                });

                                console.log(
                                  "Updated responses state:",
                                  updated,
                                );
                                return updated;
                              });

                              // Also update PMF to 0 when all countries are passed for this LOI
                              if (newPassValue) {
                                alert(
                                  `DEBUG: Setting PMF to 0 for partner ${currentPartner.id}, LOI ${selectedLOI}`,
                                );

                                setPartnerSettings((prev) => ({
                                  ...prev,
                                  [currentPartner.id]: {
                                    ...prev[currentPartner.id],
                                    pmf: 0,
                                  },
                                }));

                                // Also update this specific LOI response with PMF = 0
                                setResponses((prev) => {
                                  const updated = { ...prev };
                                  const currentKey = `${currentPartner.id}-${selectedLOI}`;
                                  if (updated[currentKey]) {
                                    updated[currentKey] = {
                                      ...updated[currentKey],
                                      pmf: 0,
                                    };
                                  }
                                  return updated;
                                });
                              }
                            }}
                          />
                        </Box>
                      </Box>

                      <TableContainer>
                        <Table>
                          <TableHead>
                            <TableRow>
                              <TableCell>Country</TableCell>
                              <TableCell>Required</TableCell>
                              <TableCell>Pass</TableCell>
                              <TableCell>Commitment</TableCell>
                              <TableCell>CPI</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {Object.entries(audience.country_samples || {}).map(
                              ([country, sample], idx) => (
                                <TableRow key={`${audience.id}-${country}`}>
                                  <TableCell>{country}</TableCell>
                                  <TableCell>
                                    {sample.is_best_efforts
                                      ? "BE/Max"
                                      : sample.sample_size}
                                  </TableCell>
                                  <TableCell>
                                    <input
                                      type="checkbox"
                                      checked={
                                        responses[
                                          `${currentPartner.id}-${selectedLOI}`
                                        ]?.audiences?.[audience.id]?.[country]
                                          ?.pass || false
                                      }
                                      onChange={(e) => {
                                        // DEBUG: Individual country pass checkbox
                                        alert(
                                          `DEBUG: Individual country pass changed!\nCountry: ${country}\nNew Value: ${e.target.checked}\nPartner: ${currentPartner.id}\nLOI: ${selectedLOI}\nAudience: ${audience.id}`,
                                        );

                                        console.log(
                                          "=== DEBUG: Individual Country Pass ===",
                                        );
                                        console.log("Country:", country);
                                        console.log(
                                          "New Pass Value:",
                                          e.target.checked,
                                        );
                                        console.log(
                                          "Partner:",
                                          currentPartner.id,
                                        );
                                        console.log("LOI:", selectedLOI);
                                        console.log("Audience:", audience.id);

                                        setResponses((prev) => {
                                          console.log(
                                            "Previous responses state:",
                                            prev,
                                          );

                                          const updated = {
                                            ...prev,
                                            [`${currentPartner.id}-${selectedLOI}`]:
                                              {
                                                ...prev[
                                                  `${currentPartner.id}-${selectedLOI}`
                                                ],
                                                partner_id: currentPartner.id,
                                                loi: selectedLOI,
                                                audiences: {
                                                  ...prev[
                                                    `${currentPartner.id}-${selectedLOI}`
                                                  ]?.audiences,
                                                  [audience.id]: {
                                                    ...prev[
                                                      `${currentPartner.id}-${selectedLOI}`
                                                    ]?.audiences?.[audience.id],
                                                    [country]: {
                                                      ...prev[
                                                        `${currentPartner.id}-${selectedLOI}`
                                                      ]?.audiences?.[
                                                        audience.id
                                                      ]?.[country],
                                                      pass: e.target.checked,
                                                    },
                                                  },
                                                },
                                              },
                                          };

                                          console.log(
                                            "Updated responses state:",
                                            updated,
                                          );
                                          return updated;
                                        });
                                      }}
                                    />
                                  </TableCell>
                                  <TableCell>
                                    <Box
                                      sx={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: 1,
                                      }}
                                    >
                                      <FormControl size="small">
                                        <Box
                                          sx={{
                                            display: "flex",
                                            alignItems: "center",
                                          }}
                                        >
                                          <Typography
                                            variant="body2"
                                            sx={{ mr: 1 }}
                                          >
                                            BE/Max
                                          </Typography>
                                          <input
                                            type="checkbox"
                                            checked={
                                              responses[
                                                `${currentPartner.id}-${selectedLOI}`
                                              ]?.audiences?.[audience.id]?.[
                                                country
                                              ]?.commitment_type === "be_max"
                                            }
                                            onChange={(e) => {
                                              const isBeMax = e.target.checked;
                                              setResponses((prev) => ({
                                                ...prev,
                                                [`${currentPartner.id}-${selectedLOI}`]:
                                                  {
                                                    ...prev[
                                                      `${currentPartner.id}-${selectedLOI}`
                                                    ],
                                                    partner_id:
                                                      currentPartner.id,
                                                    loi: selectedLOI,
                                                    audiences: {
                                                      ...prev[
                                                        `${currentPartner.id}-${selectedLOI}`
                                                      ]?.audiences,
                                                      [audience.id]: {
                                                        ...prev[
                                                          `${currentPartner.id}-${selectedLOI}`
                                                        ]?.audiences?.[
                                                          audience.id
                                                        ],
                                                        [country]: {
                                                          ...prev[
                                                            `${currentPartner.id}-${selectedLOI}`
                                                          ]?.audiences?.[
                                                            audience.id
                                                          ]?.[country],
                                                          commitment_type:
                                                            isBeMax
                                                              ? "be_max"
                                                              : "fixed",
                                                          commitment: 0, // Always set to 0 for BE/Max
                                                        },
                                                      },
                                                    },
                                                  },
                                              }));
                                            }}
                                          />
                                        </Box>
                                      </FormControl>
                                      <TextField
                                        type="number"
                                        size="small"
                                        inputProps={{ min: 0, step: 1 }}
                                        value={
                                          responses[
                                            `${currentPartner.id}-${selectedLOI}`
                                          ]?.audiences?.[audience.id]?.[country]
                                            ?.commitment === 0
                                            ? ""
                                            : (responses[
                                                `${currentPartner.id}-${selectedLOI}`
                                              ]?.audiences?.[audience.id]?.[
                                                country
                                              ]?.commitment ?? "")
                                        }
                                        onChange={(e) => {
                                          const rawValue = e.target.value;
                                          let value;

                                          if (rawValue === "") {
                                            value = "";
                                          } else {
                                            const numValue =
                                              parseFloat(rawValue);
                                            value = isNaN(numValue)
                                              ? ""
                                              : numValue;
                                          }

                                          setResponses((prev) => ({
                                            ...prev,
                                            [`${currentPartner.id}-${selectedLOI}`]:
                                              {
                                                ...prev[
                                                  `${currentPartner.id}-${selectedLOI}`
                                                ],
                                                partner_id: currentPartner.id,
                                                loi: selectedLOI,
                                                audiences: {
                                                  ...prev[
                                                    `${currentPartner.id}-${selectedLOI}`
                                                  ]?.audiences,
                                                  [audience.id]: {
                                                    ...prev[
                                                      `${currentPartner.id}-${selectedLOI}`
                                                    ]?.audiences?.[audience.id],
                                                    [country]: {
                                                      ...prev[
                                                        `${currentPartner.id}-${selectedLOI}`
                                                      ]?.audiences?.[
                                                        audience.id
                                                      ]?.[country],
                                                      commitment: value,
                                                    },
                                                  },
                                                },
                                              },
                                          }));
                                        }}
                                        disabled={Boolean(
                                          responses[
                                            `${currentPartner.id}-${selectedLOI}`
                                          ]?.audiences?.[audience.id]?.[country]
                                            ?.commitment_type === "be_max" ||
                                            responses[
                                              `${currentPartner.id}-${selectedLOI}`
                                            ]?.audiences?.[audience.id]?.[
                                              country
                                            ]?.pass,
                                        )}
                                        sx={{
                                          "& .MuiInputBase-root.Mui-disabled": {
                                            backgroundColor: "#f5f5f5",
                                            color: "#666",
                                          },
                                        }}
                                      />
                                    </Box>
                                  </TableCell>
                                  <TableCell>
                                    <TextField
                                      type="number"
                                      size="small"
                                      inputProps={{ min: 0, step: 0.01 }}
                                      value={
                                        responses[
                                          `${currentPartner.id}-${selectedLOI}`
                                        ]?.audiences?.[audience.id]?.[country]
                                          ?.cpi === 0
                                          ? ""
                                          : (responses[
                                              `${currentPartner.id}-${selectedLOI}`
                                            ]?.audiences?.[audience.id]?.[
                                              country
                                            ]?.cpi ?? "")
                                      }
                                      disabled={Boolean(
                                        responses[
                                          `${currentPartner.id}-${selectedLOI}`
                                        ]?.audiences?.[audience.id]?.[country]
                                          ?.pass,
                                      )}
                                      sx={{
                                        "& .MuiInputBase-root.Mui-disabled": {
                                          backgroundColor: "#f5f5f5",
                                          color: "#666",
                                        },
                                      }}
                                      onChange={(e) => {
                                        const rawValue = e.target.value;
                                        let value;

                                        if (rawValue === "") {
                                          value = "";
                                        } else {
                                          const numValue = parseFloat(rawValue);
                                          value = isNaN(numValue)
                                            ? ""
                                            : numValue;
                                        }

                                        setResponses((prev) => ({
                                          ...prev,
                                          [`${currentPartner.id}-${selectedLOI}`]:
                                            {
                                              ...prev[
                                                `${currentPartner.id}-${selectedLOI}`
                                              ],
                                              partner_id: currentPartner.id,
                                              loi: selectedLOI,
                                              audiences: {
                                                ...prev[
                                                  `${currentPartner.id}-${selectedLOI}`
                                                ]?.audiences,
                                                [audience.id]: {
                                                  ...prev[
                                                    `${currentPartner.id}-${selectedLOI}`
                                                  ]?.audiences?.[audience.id],
                                                  [country]: {
                                                    ...prev[
                                                      `${currentPartner.id}-${selectedLOI}`
                                                    ]?.audiences?.[
                                                      audience.id
                                                    ]?.[country],
                                                    cpi: value,
                                                  },
                                                },
                                              },
                                            },
                                        }));
                                      }}
                                    />
                                  </TableCell>
                                </TableRow>
                              ),
                            )}
                          </TableBody>
                        </Table>
                      </TableContainer>

                      <TextField
                        fullWidth
                        type="number"
                        label="Bid Timeline (days)"
                        className="timeline-field"
                        value={(() => {
                          const timelineValue =
                            responses[`${currentPartner.id}-${selectedLOI}`]
                              ?.audiences?.[audience.id]?.timeline;
                          // If all countries are passed, show 0, otherwise show the actual value
                          const countries = Object.keys(
                            audience.country_samples || {},
                          );
                          const allPassed =
                            countries.length > 0 &&
                            countries.every(
                              (country) =>
                                responses[`${currentPartner.id}-${selectedLOI}`]
                                  ?.audiences?.[audience.id]?.[country]?.pass,
                            );
                          return allPassed ? 0 : timelineValue || "";
                        })()}
                        onChange={(e) =>
                          setResponses((prev) => ({
                            ...prev,
                            [`${currentPartner.id}-${selectedLOI}`]: {
                              ...prev[`${currentPartner.id}-${selectedLOI}`],
                              audiences: {
                                ...prev[`${currentPartner.id}-${selectedLOI}`]
                                  ?.audiences,
                                [audience.id]: {
                                  ...prev[`${currentPartner.id}-${selectedLOI}`]
                                    ?.audiences?.[audience.id],
                                  timeline: parseFloat(e.target.value),
                                },
                              },
                            },
                          }))
                        }
                        disabled={(() => {
                          const countries = Object.keys(
                            audience.country_samples || {},
                          );
                          return (
                            countries.length > 0 &&
                            countries.every(
                              (country) =>
                                responses[`${currentPartner.id}-${selectedLOI}`]
                                  ?.audiences?.[audience.id]?.[country]?.pass,
                            )
                          );
                        })()}
                        sx={{
                          "& .MuiInputBase-root.Mui-disabled": {
                            backgroundColor: "#f5f5f5",
                            color: "#666",
                          },
                        }}
                      />
                      <TextField
                        fullWidth
                        multiline
                        rows={3}
                        label="Comments"
                        className="comments-field"
                        value={
                          responses[`${currentPartner.id}-${selectedLOI}`]
                            ?.audiences?.[audience.id]?.comments || ""
                        }
                        onChange={(e) =>
                          setResponses((prev) => ({
                            ...prev,
                            [`${currentPartner.id}-${selectedLOI}`]: {
                              ...prev[`${currentPartner.id}-${selectedLOI}`],
                              audiences: {
                                ...prev[`${currentPartner.id}-${selectedLOI}`]
                                  ?.audiences,
                                [audience.id]: {
                                  ...prev[`${currentPartner.id}-${selectedLOI}`]
                                    ?.audiences?.[audience.id],
                                  comments: e.target.value,
                                },
                              },
                            },
                          }))
                        }
                        disabled={(() => {
                          const countries = Object.keys(
                            audience.country_samples || {},
                          );
                          return (
                            countries.length > 0 &&
                            countries.every(
                              (country) =>
                                responses[`${currentPartner.id}-${selectedLOI}`]
                                  ?.audiences?.[audience.id]?.[country]?.pass,
                            )
                          );
                        })()}
                        sx={{
                          "& .MuiInputBase-root.Mui-disabled": {
                            backgroundColor: "#f5f5f5",
                            color: "#666",
                          },
                        }}
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
                color={
                  savingStatus[`${currentPartner.id}-${selectedLOI}`] ===
                  "error"
                    ? "error"
                    : "primary"
                }
                variant={
                  savingStatus[`${currentPartner.id}-${selectedLOI}`] ===
                  "saved"
                    ? "outlined"
                    : "contained"
                }
              >
                {!selectedLOI
                  ? "Select LOI"
                  : savingStatus[`${currentPartner.id}-${selectedLOI}`] ===
                      "saving"
                    ? "Saving..."
                    : savingStatus[`${currentPartner.id}-${selectedLOI}`] ===
                        "saved"
                      ? "Saved ✓"
                      : savingStatus[`${currentPartner.id}-${selectedLOI}`] ===
                          "error"
                        ? "Try Again"
                        : "Save"}
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
