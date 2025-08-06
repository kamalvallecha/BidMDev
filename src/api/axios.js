import axios from 'axios';

// Use local backend URL
const getBaseURL = () => {
  // Force use of local backend on port 5002
  console.log('VITE_API_URL:', import.meta.env.VITE_API_URL);
  const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:5002';
  console.log('Using baseURL:', baseURL);
  return baseURL;
};

const instance = axios.create({
  baseURL: 'http://localhost:5000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include user headers
instance.interceptors.request.use(
  (config) => {
    console.log('Making request to:', config.baseURL + config.url);
    
    // Get user data from localStorage
    const userData = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    
    if (userData) {
      try {
        const user = JSON.parse(userData);
        config.headers['X-User-Id'] = user.id;
        config.headers['X-User-Team'] = user.team;
        config.headers['X-User-Role'] = user.role;
        config.headers['X-User-Name'] = user.name;
        console.log('Added user headers:', {
          'X-User-Id': user.id,
          'X-User-Team': user.team,
          'X-User-Role': user.role,
          'X-User-Name': user.name
        });
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
    
    // Add token to Authorization header if available
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
      console.log('Added Authorization header with token');
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for better error handling
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ERR_NETWORK') {
      console.error('Network error - backend server may not be running');
    }
    
    // Handle authentication errors
    if (error.response && error.response.status === 401) {
      console.error('Authentication error - redirecting to login');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

export default instance;