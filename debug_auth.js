// Debug script to check authentication state
console.log('=== AUTHENTICATION DEBUG ===');

// Check localStorage
const userData = localStorage.getItem('user');
const token = localStorage.getItem('token');

console.log('Token exists:', !!token);
console.log('User data exists:', !!userData);

if (userData) {
  try {
    const user = JSON.parse(userData);
    console.log('User object:', user);
    console.log('User ID:', user.id);
    console.log('User Team:', user.team);
    console.log('User Role:', user.role);
    console.log('User Name:', user.name);
    
    // Check if required fields are missing
    const missingFields = [];
    if (!user.id) missingFields.push('id');
    if (!user.team) missingFields.push('team');
    if (!user.role) missingFields.push('role');
    if (!user.name) missingFields.push('name');
    
    if (missingFields.length > 0) {
      console.error('Missing required fields:', missingFields);
      console.log('This might be causing the "Missing user ID or team in headers" error');
    } else {
      console.log('All required fields are present');
    }
  } catch (error) {
    console.error('Error parsing user data:', error);
  }
} else {
  console.log('No user data found - you need to log in');
}

// Test API call
console.log('=== TESTING API CALL ===');
fetch('/api/bids', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
    'X-User-Id': userData ? JSON.parse(userData).id : '',
    'X-User-Team': userData ? JSON.parse(userData).team : '',
    'X-User-Role': userData ? JSON.parse(userData).role : '',
    'X-User-Name': userData ? JSON.parse(userData).name : ''
  }
})
.then(response => {
  console.log('API Response status:', response.status);
  return response.json();
})
.then(data => {
  console.log('API Response data:', data);
})
.catch(error => {
  console.error('API Error:', error);
}); 