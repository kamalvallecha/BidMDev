import axios from 'axios';

// Use the Replit URL for the backend when available, fallback to localhost
const getBaseURL = () => {
  // Check if we're in Replit environment
  const replitUrl = window.location.origin.replace(':3000', ':5000');
  if (replitUrl.includes('replit.dev') || replitUrl.includes('repl.co')) {
    return replitUrl;
  }
  
  // Fallback to environment variable or localhost
  return import.meta.env.VITE_API_URL || 'http://localhost:5000';
};

const instance = axios.create({
  baseURL: getBaseURL(),
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
    if (userData) {
      try {
        const user = JSON.parse(userData);
        config.headers['X-User-Id'] = user.id;
        config.headers['X-User-Team'] = user.team;
        config.headers['X-User-Role'] = user.role;
        config.headers['X-User-Name'] = user.name;
      } catch (error) {
        console.error('Error parsing user data:', error);
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }

  return config;
}, (error) => {
  console.error('Axios interceptor error:', error);
  return Promise.reject(error);
});

// Add response interceptor for better error handling
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ERR_NETWORK') {
      console.error('Network error - backend server may not be running');
    }
    return Promise.reject(error);
  }
);

export default instance;