import { useState } from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper,
  Button,
  TextField
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import './Bids.css';

function Bids() {
  const navigate = useNavigate();
  const [bids, setBids] = useState([]);

  return (
    <div className="bids-container">
      <div className="bids-header">
        <h2>Bid Management</h2>
        <div className="search-add">
          <TextField
            size="small"
            placeholder="Search bids..."
            className="search-input"
          />
          <Button 
            variant="contained" 
            color="primary"
            onClick={() => navigate('/bids/new')}
          >
            ADD BID
          </Button>
        </div>
      </div>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Bid Number</TableCell>
              <TableCell>Study Name</TableCell>
              <TableCell>Client</TableCell>
              <TableCell>Methodology</TableCell>
              <TableCell>Countries</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {bids.map((bid) => (
              <TableRow key={bid.id}>
                <TableCell>{bid.bid_number}</TableCell>
                <TableCell>{bid.study_name}</TableCell>
                <TableCell>{bid.client}</TableCell>
                <TableCell>{bid.methodology}</TableCell>
                <TableCell>{bid.countries}</TableCell>
                <TableCell>{bid.status}</TableCell>
                <TableCell>
                  <Button size="small" color="primary">Edit</Button>
                  <Button size="small" color="error">Delete</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}

export default Bids; 