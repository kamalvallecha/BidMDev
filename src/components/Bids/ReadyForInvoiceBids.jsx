import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Stack,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import KeyboardReturnIcon from "@mui/icons-material/KeyboardReturn";
import SwapHorizIcon from "@mui/icons-material/SwapHoriz";
import { useNavigate } from "react-router-dom";
import axios from "../../api/axios";

const ReadyForInvoiceBids = () => {
  const navigate = useNavigate();
  const [bids, setBids] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchBids();
  }, []);

  const fetchBids = async () => {
    try {
      const response = await axios.get("/api/bids/ready-for-invoice");
      setBids(response.data);
    } catch (error) {
      console.error("Error fetching bids:", error);
    }
  };

  const handleEditClick = (bidNumber) => {
    if (bidNumber) {
      navigate(`/invoice/${bidNumber}/edit`);
    }
  };

  const handleMoveToClosureClick = async (bidNumber) => {
    try {
      console.log("Moving bid to closure:", bidNumber);
      const moveResponse = await axios.post(
        `/api/bids/${bidNumber}/move-to-closure`,
      );
      if (moveResponse.data.message) {
        alert("Bid moved to closure successfully");
        fetchBids();
        navigate('/closure');
      }
    } catch (error) {
      console.error("Error moving bid to closure:", error);
      if (error.response?.status === 404) {
        alert("Bid not found. Please refresh the page and try again.");
      } else {
        alert("Error moving bid to closure. Please try again.");
      }
    }
  };

  const handleMoveToInfield = async (bidNumber, poNumber) => {
    try {
      console.log("Moving bid to infield:", bidNumber);
      const moveResponse = await axios.post(
        `/api/bids/${bidNumber}/move-to-infield`,
        {
          po_number: poNumber,
        },
      );

      if (moveResponse.data.message) {
        alert("Bid moved to infield successfully");
        fetchBids();
        navigate('/infield');
      }
    } catch (error) {
      console.error("Error moving bid to infield:", error);
      if (error.response?.status === 404) {
        alert("Bid not found. Please refresh the page and try again.");
      } else {
        alert("Error moving bid to infield. Please try again.");
      }
    }
  };

  const filteredBids = bids.filter(
    (bid) => {
      if (!searchTerm) return true;
      const searchLower = searchTerm.toLowerCase();
      return (
        (bid.po_number && bid.po_number.toString().toLowerCase().includes(searchLower)) ||
        (bid.bid_number && bid.bid_number.toString().toLowerCase().includes(searchLower)) ||
        (bid.study_name && bid.study_name.toLowerCase().includes(searchLower)) ||
        (bid.client_name && bid.client_name.toLowerCase().includes(searchLower))
      );
    }
  );

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Ready for Invoice Bids
      </Typography>

      <TextField
        variant="outlined"
        placeholder="Search bids..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        sx={{ 
          mb: 2,
          width: '300px',
        }}
      />

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: "primary.main" }}>
              <TableCell sx={{ color: "white" }}>PO Number</TableCell>
              <TableCell sx={{ color: "white" }}>Bid Number</TableCell>
              <TableCell sx={{ color: "white" }}>Study Name</TableCell>
              <TableCell sx={{ color: "white" }}>Client</TableCell>
              <TableCell sx={{ color: "white" }}>N-Delivered</TableCell>
              <TableCell sx={{ color: "white" }}>Avg. Final LOI</TableCell>
              <TableCell sx={{ color: "white" }}>
                Avg. Initial Vendor CPI
              </TableCell>
              <TableCell sx={{ color: "white" }}>
                Avg. Final Vendor CPI
              </TableCell>
              <TableCell sx={{ color: "white" }}>Invoice Amount</TableCell>
              <TableCell sx={{ color: "white" }}>Status</TableCell>
              <TableCell sx={{ color: "white" }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredBids.map((bid) => (
              <TableRow key={bid.bid_number}>
                <TableCell>{bid.po_number}</TableCell>
                <TableCell>{bid.bid_number}</TableCell>
                <TableCell>{bid.study_name}</TableCell>
                <TableCell>{bid.client_name}</TableCell>
                <TableCell>{bid.n_delivered}</TableCell>
                <TableCell>{bid.avg_final_loi}</TableCell>
                <TableCell>{bid.avg_initial_cpi}</TableCell>
                <TableCell>{bid.avg_final_cpi}</TableCell>
                <TableCell>{bid.invoice_amount}</TableCell>
                <TableCell>{bid.status}</TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1}>
                    <Tooltip title="Edit">
                      <IconButton
                        onClick={() => handleEditClick(bid.bid_number)}
                        color="primary"
                        size="small"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Move to Closure">
                      <IconButton
                        onClick={() => handleMoveToClosureClick(bid.bid_number)}
                        color="secondary"
                        size="small"
                      >
                        <KeyboardReturnIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Move to Infield">
                      <IconButton
                        onClick={() =>
                          handleMoveToInfield(bid.bid_number, bid.po_number)
                        }
                        color="info"
                        size="small"
                      >
                        <SwapHorizIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default ReadyForInvoiceBids;
