import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button
} from '@mui/material';

function PONumberDialog({ open, onClose, onSubmit }) {
  const [poNumber, setPoNumber] = useState('');

  const handleSubmit = () => {
    if (!poNumber.trim()) {
      alert('Please enter a PO Number');
      return;
    }
    onSubmit(poNumber);
    setPoNumber('');
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Add to InField</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          margin="dense"
          label="PO Number"
          fullWidth
          value={poNumber}
          onChange={(e) => setPoNumber(e.target.value)}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained" color="primary">
          Submit
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default PONumberDialog; 