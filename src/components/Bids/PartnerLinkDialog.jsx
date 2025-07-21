import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  CircularProgress,
  Stack,
  Alert,
} from "@mui/material";
import LinkIcon from "@mui/icons-material/Link";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import UpdateIcon from "@mui/icons-material/Update";
import axios from "../../api/axios";

function PartnerLinkDialog({ open, onClose, bidId }) {
  const [loading, setLoading] = useState(false);
  const [partners, setPartners] = useState([]);
  const [links, setLinks] = useState({});
  const [copyMsg, setCopyMsg] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (open && bidId) {
      fetchPartners();
    }
    // eslint-disable-next-line
  }, [open, bidId]);

  const fetchPartners = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`/api/bids/${bidId}/partners`);
      setPartners(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.error("Error fetching partners:", e);
      setError("Failed to fetch partners");
      setPartners([]);
    }
    setLoading(false);
  };

  const handleGenerateLink = async (partnerId) => {
    setLinks((prev) => ({ ...prev, [partnerId]: { loading: true } }));
    try {
      const res = await axios.post(
        `/api/bids/${bidId}/partners/${partnerId}/generate-link`,
      );
      setLinks((prev) => ({
        ...prev,
        [partnerId]: { ...res.data, loading: false },
      }));
    } catch (e) {
      setLinks((prev) => ({
        ...prev,
        [partnerId]: { error: "Failed", loading: false },
      }));
    }
  };

  const handleExtendLink = async (partnerId) => {
    setLinks((prev) => ({
      ...prev,
      [partnerId]: { ...prev[partnerId], loading: true },
    }));
    try {
      const res = await axios.post(
        `/api/bids/${bidId}/partners/${partnerId}/extend-link`,
      );
      setLinks((prev) => ({
        ...prev,
        [partnerId]: { ...res.data, loading: false },
      }));
    } catch (e) {
      setLinks((prev) => ({
        ...prev,
        [partnerId]: {
          ...prev[partnerId],
          error: "Failed to extend",
          loading: false,
        },
      }));
    }
  };

  const handleCopy = (link) => {
    navigator.clipboard.writeText(link);
    setCopyMsg("Copied!");
    setTimeout(() => setCopyMsg(""), 1200);
  };

  const isLinkExpiringSoon = (expiresAt) => {
    if (!expiresAt) return false;
    const expiry = new Date(expiresAt);
    const now = new Date();
    const daysUntilExpiry = (expiry - now) / (1000 * 60 * 60 * 24);
    return daysUntilExpiry <= 3; // 3 days or less
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Generate Partner Links</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {loading ? (
          <Stack alignItems="center" py={4}>
            <CircularProgress />
          </Stack>
        ) : !Array.isArray(partners) || partners.length === 0 ? (
          <Typography>No partners available for this bid</Typography>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Partner Name</TableCell>
                  <TableCell>Link</TableCell>
                  <TableCell>Expires At</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {partners.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell>{p.partner_name}</TableCell>
                    <TableCell>
                      {links[p.id]?.link ? (
                        <>
                          <a
                            href={links[p.id].link}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ wordBreak: "break-all" }}
                          >
                            {links[p.id].link}
                          </a>
                          <Tooltip title="Copy Link">
                            <IconButton
                              size="small"
                              onClick={() => handleCopy(links[p.id].link)}
                            >
                              <ContentCopyIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </>
                      ) : links[p.id]?.loading ? (
                        <CircularProgress size={18} />
                      ) : (
                        <Typography variant="body2" color="textSecondary">
                          No link
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {links[p.id]?.expires_at ? (
                        <Typography
                          variant="body2"
                          color={
                            isLinkExpiringSoon(links[p.id].expires_at)
                              ? "warning.main"
                              : "inherit"
                          }
                        >
                          {new Date(links[p.id].expires_at).toLocaleString()}
                          {isLinkExpiringSoon(links[p.id].expires_at) &&
                            " (Expiring soon)"}
                        </Typography>
                      ) : (
                        <Typography variant="body2" color="textSecondary">
                          -
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Stack direction="row" spacing={1}>
                        {links[p.id]?.link ? (
                          <Tooltip title="Extend Expiry">
                            <IconButton
                              size="small"
                              onClick={() => handleExtendLink(p.id)}
                              disabled={links[p.id]?.loading}
                            >
                              <UpdateIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        ) : (
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<LinkIcon />}
                            onClick={() => handleGenerateLink(p.id)}
                            disabled={links[p.id]?.loading}
                          >
                            Generate Link
                          </Button>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
        {copyMsg && (
          <Typography color="success.main" align="center" mt={2}>
            {copyMsg}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default PartnerLinkDialog;
