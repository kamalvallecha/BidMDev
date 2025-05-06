import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
  FormControl
} from '@mui/material';

function RejectBidDialog({ open, onClose, bidNumber, onSubmit }) {
  const [reason, setReason] = useState('');
  const [comments, setComments] = useState('');

  const handleSubmit = () => {
    onSubmit({
      reason,
      comments
    });
    setReason('');
    setComments('');
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Reject Bid {bidNumber}</DialogTitle>
      <DialogContent>
        <div style={{ marginTop: '16px' }}>
          <FormControl component="fieldset">
            <RadioGroup
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            >
              <FormControlLabel
                value="Budget constraints"
                control={<Radio />}
                label="Budget constraints"
              />
              <FormControlLabel
                value="Timeline not feasible"
                control={<Radio />}
                label="Timeline not feasible"
              />
              <FormControlLabel
                value="Scope mismatch"
                control={<Radio />}
                label="Scope mismatch"
              />
              <FormControlLabel
                value="Methodology concerns"
                control={<Radio />}
                label="Methodology concerns"
              />
              <FormControlLabel
                value="Client changed requirements"
                control={<Radio />}
                label="Client changed requirements"
              />
              <FormControlLabel
                value="Resource unavailability"
                control={<Radio />}
                label="Resource unavailability"
              />
              <FormControlLabel
                value="Other"
                control={<Radio />}
                label="Other"
              />
            </RadioGroup>
          </FormControl>
          <TextField
            label="Additional comments"
            multiline
            rows={4}
            fullWidth
            margin="normal"
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            placeholder="Add any additional context or notes"
          />
        </div>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button 
          onClick={handleSubmit} 
          color="error" 
          variant="contained"
          disabled={!reason}
        >
          Reject Bid
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default RejectBidDialog; 