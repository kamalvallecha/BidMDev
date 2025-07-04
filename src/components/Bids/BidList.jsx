import { useState, useEffect } from 'react';
import { 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Button,
  TextField,
  IconButton,
  Typography,
  Stack,
  Tooltip,
  Pagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Badge
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import BlockIcon from '@mui/icons-material/Block';
import RestoreIcon from '@mui/icons-material/Restore';
import GroupIcon from '@mui/icons-material/Group';
import LinkIcon from '@mui/icons-material/Link';
import DescriptionIcon from '@mui/icons-material/Description';
import FileCopyIcon from '@mui/icons-material/FileCopy';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import VpnKeyOutlinedIcon from '@mui/icons-material/VpnKeyOutlined';
import axios from '../../api/axios';
import './Bids.css';
import PONumberDialog from './PONumberDialog';
import RejectBidDialog from './RejectBidDialog';
import PartnerResponseSummaryDialog from './PartnerResponseSummaryDialog';
import PartnerLinkDialog from './PartnerLinkDialog';
import { useAuth } from '../../contexts/AuthContext';

// Helper function to normalize team names for comparison
const normalizeTeam = (team) => {
  if (!team) return '';
  // Remove all spaces and convert to lowercase for robust comparison
  return team.toString().replace(/\s+/g, '').toLowerCase();
};

function BidList() {
  const { user: currentUser } = useAuth();
  const [bids, setBids] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [poDialogOpen, setPoDialogOpen] = useState(false);
  const [selectedBidId, setSelectedBidId] = useState(null);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [bidToReject, setBidToReject] = useState(null);
  const [summaryOpen, setSummaryOpen] = useState(false);
  const [selectedBid, setSelectedBid] = useState(null);
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [linkDialogBid, setLinkDialogBid] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);
  // Add state for access request feedback
  const [accessRequestedBid, setAccessRequestedBid] = useState(null);
  const [accessRequestStatus, setAccessRequestStatus] = useState('');
  // Grant Access Modal State
  const [grantModalOpen, setGrantModalOpen] = useState(false);
  const [grantModalBid, setGrantModalBid] = useState(null);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [grantedAccess, setGrantedAccess] = useState([]);
  const [grantLoading, setGrantLoading] = useState(false);
  const [grantError, setGrantError] = useState("");
  // Helper to check if a bid has pending requests (for icon display)
  const [bidsPendingRequests, setBidsPendingRequests] = useState({});
  const [bidAccessMap, setBidAccessMap] = useState({}); // NEW: per-bid access
  // Add state for granted access counts
  const [bidsGrantedCounts, setBidsGrantedCounts] = useState({});
  const [vmContacts, setVmContacts] = useState([]);

  const isSuperAdmin = currentUser?.role === 'super_admin' || 
    (currentUser?.name && currentUser.name.trim().toLowerCase().includes('kamal vallecha'));
  const isKamal = currentUser?.name && currentUser.name.trim().toLowerCase().includes('kamal vallecha');
  const isAdmin = currentUser?.role === 'admin';

  // Debug: Log current user info
  useEffect(() => {
    console.log('Current user:', currentUser);
    console.log('Current user team (normalized):', normalizeTeam(currentUser?.team));
  }, [currentUser]);

  useEffect(() => {
    fetchBids();
    // eslint-disable-next-line
  }, [page, pageSize, searchTerm]);

  // NEW: Check per-bid access for non-admin/non-owner
  useEffect(() => {
    const checkAccessForBids = async () => {
      if (!currentUser || !bids.length) return;
      const isAdmin = currentUser?.role === 'admin';
      const isKamal = currentUser?.name && currentUser.name.trim().toLowerCase().includes('kamal vallecha');
      const normalizedUserTeam = normalizeTeam(currentUser?.team);
      const accessResults = {};
      await Promise.all(
        bids.map(async (bid) => {
          const normalizedBidTeam = normalizeTeam(bid.team);
          const isOwnTeam = normalizedUserTeam === normalizedBidTeam;
          if (isAdmin || isKamal || isOwnTeam) {
            accessResults[bid.id] = true;
          } else {
            try {
              const res = await axios.get(`/api/bids/${bid.id}/access`, {
                params: { user_id: currentUser.id, team: currentUser.team }
              });
              accessResults[bid.id] = res.data.has_access;
            } catch {
              accessResults[bid.id] = false;
            }
          }
        })
      );
      setBidAccessMap(accessResults);
    };
    checkAccessForBids();
  }, [bids, currentUser]);

  const fetchBids = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/bids?page=${page}&page_size=${pageSize}&search=${encodeURIComponent(searchTerm)}`, {
        headers: {
          'X-User-Id': currentUser?.id,
          'X-User-Team': currentUser?.team,
          'X-User-Role': currentUser?.role,
          'X-User-Name': currentUser?.name,
        }
      });
      setBids(response.data.bids || []);
      setTotal(response.data.total || 0);
      setVmContacts(response.data.vmContacts || []);
    } catch (error) {
      console.error('Error fetching bids:', error);
    } finally {
      setLoading(false);
    }
  };

  // Add this to see if bids are updating in state
  useEffect(() => {
    console.log('Current bids:', bids);
  }, [bids]);

  const handleAddBid = () => {
    navigate('/bids/new');
  };

  const handleEdit = (bid) => {
    navigate(`/bids/edit/${bid.id}`);
  };

  const handleDelete = async (bidId) => {
    if (window.confirm('Are you sure you want to delete this bid?')) {
      try {
        await axios.delete(`/api/bids/${bidId}`);
        fetchBids(); // Refresh the list
      } catch (error) {
        console.error('Error deleting bid:', error);
      }
    }
  };

  const handleMoveToInField = (bidId) => {
    setSelectedBidId(bidId);
    setPoDialogOpen(true);
  };

  const handlePoSubmit = async (poNumber) => {
    try {
      // First save PO number
      await axios.post(`/api/bids/${selectedBidId}/po`, {
        status: 'infield',
        po_number: poNumber
      });

      // Then update status to infield using POST instead of PUT
      await axios.post(`/api/bids/${selectedBidId}/status`, {
        status: 'infield'
      });

      setPoDialogOpen(false);
      fetchBids();
      navigate('/infield');
    } catch (error) {
      console.error('Error moving bid to infield:', error);
      alert('Failed to move bid to infield status');
    }
  };

  const handleRejectClick = (bid) => {
    setBidToReject(bid);
    setRejectDialogOpen(true);
  };

  const handleRejectSubmit = async ({ reason, comments }) => {
    try {
      await axios.post(`/api/bids/${bidToReject.id}/status`, {
        status: 'rejected',
        rejection_reason: reason,
        rejection_comments: comments
      });
      setRejectDialogOpen(false);
      setBidToReject(null);
      fetchBids();
    } catch (error) {
      console.error('Error rejecting bid:', error);
      alert('Failed to reject bid');
    }
  };

  const handleReactivateBid = async (bidId) => {
    try {
      await axios.post(`/api/bids/${bidId}/status`, {
        status: 'draft'
      });
      fetchBids(); // Refresh the list
    } catch (error) {
      console.error('Error reactivating bid:', error);
      alert('Failed to reactivate bid');
    }
  };

  const handleShowPartnerSummary = (bid) => {
    setSelectedBid(bid);
    setSummaryOpen(true);
  };

  const handleShowPartnerLinks = (bid) => {
    setLinkDialogBid(bid);
    setLinkDialogOpen(true);
  };

  const handleCreateProposal = (bid) => {
    navigate(`/proposals/${bid.id}`);
  };

  // Function to handle access request
  const handleRequestAccess = async (bid) => {
    setAccessRequestedBid(bid.id);
    setAccessRequestStatus('');
    try {
      const response = await axios.post('/api/bids/request-access', {
        bidId: bid.id,
        bidNumber: bid.bid_number,
        studyName: bid.study_name,
        userEmail: currentUser?.email,
        userName: currentUser?.name,
        userTeam: currentUser?.team,
      });
      
      if (response.data.warning) {
        setAccessRequestStatus('Request received (email not configured)');
      } else if (response.data.error) {
        setAccessRequestStatus('Request received (email failed)');
      } else {
        setAccessRequestStatus('Request sent successfully!');
      }
    } catch (error) {
      console.error('Error requesting access:', error);
      setAccessRequestStatus('Failed to send request.');
    } finally {
      setTimeout(() => {
        setAccessRequestedBid(null);
        setAccessRequestStatus('');
      }, 3000);
    }
  };

  // Copy Bid handler
  const handleCopyBid = async () => {
    try {
      const response = await axios.post(`/api/bids/${bid.id}/copy`, {
        created_by: currentUser?.id,
        team: currentUser?.team
      });
      const newBidId = response.data.new_bid_id;
      navigate(`/bids/edit/${newBidId}`);
    } catch (error) {
      alert('Failed to copy bid: ' + (error.response?.data?.error || error.message));
    }
  };

  // Fetch pending requests for a bid
  const fetchPendingRequests = async (bidId) => {
    setGrantLoading(true);
    setGrantError("");
    try {
      const res = await axios.get(`/api/bids/${bidId}/access-requests`);
      setPendingRequests(res.data.requests || []);
      // Fetch granted access
      const grantedRes = await axios.get(`/api/bids/${bidId}/granted-access`);
      setGrantedAccess(grantedRes.data.granted || []);
    } catch (err) {
      setGrantError("Failed to fetch requests");
    }
    setGrantLoading(false);
  };

  // Open Grant Access Modal
  const handleOpenGrantModal = async (bid) => {
    setGrantModalBid(bid);
    setGrantModalOpen(true);
    await fetchPendingRequests(bid.id);
  };

  // Close Grant Access Modal
  const handleCloseGrantModal = () => {
    setGrantModalOpen(false);
    setGrantModalBid(null);
    setPendingRequests([]);
    setGrantError("");
  };

  // Grant or Deny a request
  const handleGrantOrDeny = async (action, request) => {
    setGrantLoading(true);
    setGrantError("");
    try {
      if (action === 'grant') {
        await axios.post(`/api/bids/${grantModalBid.id}/access-requests/${request.id}/grant`);
      } else {
        await axios.post(`/api/bids/${grantModalBid.id}/access-requests/${request.id}/deny`);
      }
      // Refresh requests after action
      await fetchPendingRequests(grantModalBid.id);
    } catch (err) {
      setGrantError(`Failed to ${action} request`);
    }
    setGrantLoading(false);
  };

  // Revoke access handler
  const handleRevokeAccess = async (request) => {
    setGrantLoading(true);
    setGrantError("");
    try {
      await axios.post(`/api/bids/${grantModalBid.id}/revoke-access`, {
        user_id: request.user_id,
        team: request.team,
      });
      await fetchPendingRequests(grantModalBid.id);
    } catch (err) {
      setGrantError("Failed to revoke access");
    }
    setGrantLoading(false);
  };

  // Helper to check if a bid has pending requests (for icon display)
  useEffect(() => {
    // Batch fetch pending requests for all visible bids
    const fetchAllPending = async () => {
      if (bids.length === 0) return;
      const bidIds = bids.map(bid => bid.id).join(',');
      try {
        const res = await axios.get(`/api/bids/pending-requests?bid_ids=${bidIds}`);
        setBidsPendingRequests(res.data || {});
      } catch {
        // fallback: set all to 0
      const result = {};
        bids.forEach(bid => { result[bid.id] = 0; });
        setBidsPendingRequests(result);
      }
    };
    fetchAllPending();
  }, [bids]);

  // Batch fetch granted access counts for all visible bids
  useEffect(() => {
    const fetchGrantedCounts = async () => {
      if (bids.length === 0) return;
      const bidIds = bids.map(bid => bid.id).join(',');
      try {
        const res = await axios.get(`/api/bids/granted-counts?bid_ids=${bidIds}`);
        setBidsGrantedCounts(res.data || {});
          } catch {
        const result = {};
        bids.forEach(bid => { result[bid.id] = 0; });
        setBidsGrantedCounts(result);
          }
    };
    fetchGrantedCounts();
  }, [bids]);

  const renderActions = (bid) => {
    const normalizedUserTeam = normalizeTeam(currentUser?.team);
    const normalizedBidTeam = normalizeTeam(bid.team);
    const isOwnTeam = normalizedUserTeam === normalizedBidTeam;
    const hasAccess = isSuperAdmin || isOwnTeam || isKamal || bidAccessMap[bid.id];

    if (!hasAccess) {
      return (
        <div style={{ opacity: 0.5 }}>
          <Button
            variant="outlined"
            color="secondary"
            size="small"
            onClick={() => handleRequestAccess(bid)}
            disabled={accessRequestedBid === bid.id}
          >
            {accessRequestedBid === bid.id ? accessRequestStatus || "Requesting..." : "Request Access"}
          </Button>
          <Tooltip title="Copy Bid">
            <IconButton color="primary" disabled>
              <FileCopyIcon />
            </IconButton>
          </Tooltip>
        </div>
      );
    }

    const isMoveable = bid.status === 'draft' && isOwnTeam;
    const isRejected = bid.status === 'rejected';

    // Show Grant Access icon if there are pending requests or if user can manage access
    const hasPendingRequests = bidsPendingRequests[bid.id] > 0;
    // Debug log for Grant Access visibility
    console.log(`Bid ${bid.bid_number}: hasPendingRequests=${hasPendingRequests}, pendingCount=${bidsPendingRequests[bid.id]}, isAdmin=${isAdmin}`);

    // Helper: who can manage access for a bid?
    const isBidOwner = currentUser?.id === bid.created_by;
    const isOwnTeamAdmin = currentUser?.role === 'admin' && normalizeTeam(currentUser?.team) === normalizeTeam(bid.team);
    const canManageAccess = isSuperAdmin || isBidOwner || isOwnTeamAdmin;

    const grantedCount = bidsGrantedCounts[bid.id] || 0;

    // Find VM team if available
    let vmTeam = '';
    if (bid.vm_contact && Array.isArray(vmContacts)) {
      const vm = vmContacts.find(vm => vm.id === bid.vm_contact);
      vmTeam = vm?.team || '';
    }

    return (
      <Stack direction="row" spacing={1}>
        <IconButton 
          color="primary" 
          onClick={() => handleEdit(bid)}
          disabled={isRejected}
        >
          <EditIcon />
        </IconButton>
        <IconButton 
          color="primary"
          onClick={() => handleMoveToInField(bid.id)}
          disabled={!isMoveable}
          sx={{ 
            opacity: isMoveable ? 1 : 0.5,
            '&.Mui-disabled': {
              color: 'grey.400'
            }
          }}
        >
          <PlayArrowIcon />
        </IconButton>
        {!isRejected ? (
          <Tooltip title="Reject Bid">
            <IconButton 
              color="error"
              onClick={() => handleRejectClick(bid)}
              disabled={bid.status !== 'draft'}
              sx={{ 
                opacity: bid.status === 'draft' ? 1 : 0.5,
                '&.Mui-disabled': {
                  color: 'grey.400'
                }
              }}
            >
              <BlockIcon />
            </IconButton>
          </Tooltip>
        ) : (
          <Tooltip title="Reactivate Bid">
            <IconButton 
              color="success"
              onClick={() => handleReactivateBid(bid.id)}
            >
              <RestoreIcon />
            </IconButton>
          </Tooltip>
        )}
        <Tooltip title="Partner Response Summary">
          <IconButton color="info" onClick={() => handleShowPartnerSummary(bid)}>
            <GroupIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Generate Partner Link">
          <IconButton color="primary" onClick={() => handleShowPartnerLinks(bid)}>
            <LinkIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Copy Bid">
          <IconButton color="primary" onClick={handleCopyBid}>
            <FileCopyIcon />
          </IconButton>
        </Tooltip>
        {/* Unified Grant Access icon - shows for both pending requests and access management */}
        {(hasPendingRequests || canManageAccess) && (
          <Tooltip title={
            hasPendingRequests 
              ? `Grant Access Requests (${bidsPendingRequests[bid.id]} pending${grantedCount > 0 ? `, ${grantedCount} granted` : ''})`
              : grantedCount > 0 
                ? `Manage Access (${grantedCount} granted)` 
                : 'Manage Access (no one granted yet)'
          }>
            <span>
              <Badge badgeContent={grantedCount > 0 ? grantedCount : null} color="primary">
                <IconButton size="small" onClick={() => handleOpenGrantModal(bid)}>
                  {grantedCount > 0 ? <VpnKeyIcon color="primary" /> : <VpnKeyOutlinedIcon />}
                </IconButton>
              </Badge>
            </span>
          </Tooltip>
        )}
      </Stack>
    );
  };

  return (
    <>
      <div className="bid-list-container">
        <div className="bid-list-header">
          <Typography variant="h5">Bid Management</Typography>
          <div className="bid-list-actions">
            <TextField
              size="small"
              placeholder="Search bids..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              className="search-field"
            />
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleAddBid}
            >
              ADD BID
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              style={{ marginLeft: 8 }}
              onClick={() => navigate('/bids/find-similar')}
            >
              Find Similar Bid
            </Button>
          </div>
        </div>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow className="table-header">
                <TableCell>Bid Number</TableCell>
                <TableCell>Study Name</TableCell>
                <TableCell>Client</TableCell>
                <TableCell>Team</TableCell>
                <TableCell>Methodology</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">Loading...</TableCell>
                </TableRow>
              ) : bids.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">No bids found</TableCell>
                </TableRow>
              ) : (
                bids.map((bid) => {
                  const normalizedUserTeam = normalizeTeam(currentUser?.team);
                  const normalizedBidTeam = normalizeTeam(bid.team);
                  const isOwnTeam = normalizedUserTeam === normalizedBidTeam;
                  const isKamal = currentUser?.name && currentUser.name.trim().toLowerCase().includes('kamal vallecha');
                  const isAdmin = currentUser?.role === 'admin';
                  const hasAccess = isSuperAdmin || isOwnTeam || isKamal || bidAccessMap[bid.id];
                  // Find VM team if available
                  let vmTeam = '';
                  if (bid.vm_contact && Array.isArray(vmContacts)) {
                    const vm = vmContacts.find(vm => vm.id === bid.vm_contact);
                    vmTeam = vm?.team || '';
                  }
                  return (
                    <TableRow key={bid.id} style={!hasAccess ? { opacity: 0.5 } : {}}>
                    <TableCell>{bid.bid_number}</TableCell>
                    <TableCell>{bid.study_name}</TableCell>
                    <TableCell>{bid.client_name}</TableCell>
                    <TableCell>{bid.team}</TableCell>
                    <TableCell>{bid.methodology}</TableCell>
                    <TableCell>{bid.status}</TableCell>
                    <TableCell>{renderActions(bid)}</TableCell>
                  </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <div style={{ display: 'flex', justifyContent: 'center', margin: '16px 0' }}>
          <Pagination
            count={Math.ceil(total / pageSize)}
            page={page}
            onChange={(e, value) => setPage(value)}
            color="primary"
            shape="rounded"
          />
        </div>
      </div>
      <PONumberDialog
        open={poDialogOpen}
        onClose={() => setPoDialogOpen(false)}
        onSubmit={handlePoSubmit}
      />
      <RejectBidDialog
        open={rejectDialogOpen}
        onClose={() => {
          setRejectDialogOpen(false);
          setBidToReject(null);
        }}
        bidNumber={bidToReject?.bid_number}
        onSubmit={handleRejectSubmit}
      />
      <PartnerResponseSummaryDialog
        open={summaryOpen}
        onClose={() => setSummaryOpen(false)}
        bidId={selectedBid?.id}
      />
      <PartnerLinkDialog
        open={linkDialogOpen}
        onClose={() => setLinkDialogOpen(false)}
        bidId={linkDialogBid?.id}
      />
      <Dialog open={grantModalOpen} onClose={handleCloseGrantModal} maxWidth="sm" fullWidth>
        <DialogTitle>Pending Access Requests for Bid {grantModalBid?.bid_number}</DialogTitle>
        <DialogContent>
          {grantLoading ? (
            <div>Loading...</div>
          ) : grantError ? (
            <div style={{ color: 'red' }}>{grantError}</div>
          ) : grantedAccess.length === 0 ? (
            <div>No users/teams have been granted access yet.</div>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Team</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {grantedAccess.map((access) => (
                  <TableRow key={access.user_id || access.team}>
                    <TableCell>{access.name || '-'}</TableCell>
                    <TableCell>{access.email || '-'}</TableCell>
                    <TableCell>{access.team || '-'}</TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        color="error"
                        variant="outlined"
                        onClick={() => handleRevokeAccess(access)}
                        disabled={grantLoading}
                      >
                        Revoke
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
          {pendingRequests.length === 0 ? (
            <div>No pending requests.</div>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Team</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {pendingRequests.map((req) => (
                  <TableRow key={req.id}>
                    <TableCell>{req.name || '-'}</TableCell>
                    <TableCell>{req.email || '-'}</TableCell>
                    <TableCell>{req.team || '-'}</TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        color="success"
                        variant="contained"
                        onClick={() => handleGrantOrDeny('grant', req)}
                        disabled={grantLoading}
                        style={{ marginRight: 8 }}
                      >
                        Grant
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        variant="outlined"
                        onClick={() => handleGrantOrDeny('deny', req)}
                        disabled={grantLoading}
                      >
                        Deny
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseGrantModal}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default BidList;