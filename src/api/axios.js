
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
    
    // Get user data and token from localStorage
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');
    
    console.log('Axios interceptor - Raw localStorage data:', {
      token: token ? 'exists' : 'missing',
      userStr: userStr ? 'exists' : 'missing'
    });

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Always try to add user headers if user data exists
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        console.log('Axios interceptor - Parsed user:', user);
        
        if (user && user.id && user.team) {
          config.headers['X-User-Id'] = String(user.id);
          config.headers['X-User-Team'] = String(user.team);
          config.headers['X-User-Role'] = String(user.role || '');
          config.headers['X-User-Name'] = String(user.name || '');
          console.log('Axios interceptor - Successfully added user headers:', {
            'X-User-Id': config.headers['X-User-Id'],
            'X-User-Team': config.headers['X-User-Team'],
            'X-User-Role': config.headers['X-User-Role'],
            'X-User-Name': config.headers['X-User-Name'],
            url: config.url,
            method: config.method
          });
        } else {
          console.warn('Axios interceptor - User data incomplete:', user);
          // For API calls that require authentication, show error but don't redirect
          if (config.url && config.url.startsWith('/api/') && !config.url.includes('/login')) {
            console.error('Axios interceptor - Missing user authentication for API call:', { 
              url: config.url,
              user: user 
            });
          }
        }
      } catch (e) {
        console.error('Axios interceptor - Failed to parse user data:', e);
        // Only redirect on authentication-required endpoints
        if (config.url && config.url.startsWith('/api/') && !config.url.includes('/login')) {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
          return Promise.reject(new Error('Invalid user data'));
        }
      }
    } else {
      // No user data found
      if (config.url && config.url.startsWith('/api/') && !config.url.includes('/login')) {
        console.error('Axios interceptor - No user data found for API call:', config.url);
      }
    }

    return config;
  },
  (error) => {
    console.error('Axios interceptor error:', error);
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
    return Promise.reject(error);
  }
);

export default instance;
