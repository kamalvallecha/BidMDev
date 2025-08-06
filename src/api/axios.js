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
  baseURL: getBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add authentication headers
instance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  const userStr = localStorage.getItem('user');
  
  console.log('Axios interceptor - Raw localStorage data:', {
    token: token ? 'exists' : 'missing',
    userStr: userStr
  });

  let user = {};
  if (userStr) {
    try {
      user = JSON.parse(userStr);
      console.log('Axios interceptor - Parsed user:', user);
    } catch (e) {
      console.error('Axios interceptor - Failed to parse user:', e);
    }
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Always try to add user headers if we have user data
  if (user && user.id && user.team) {
    config.headers['X-User-Id'] = String(user.id);
    config.headers['X-User-Team'] = String(user.team);
    console.log('Axios interceptor - Successfully added user headers:', {
      'X-User-Id': config.headers['X-User-Id'],
      'X-User-Team': config.headers['X-User-Team'],
      url: config.url,
      method: config.method
    });
  } else {
    console.error('Axios interceptor - Cannot add user headers:', { 
      hasUser: !!user, 
      hasUserId: !!(user && user.id), 
      hasUserTeam: !!(user && user.team),
      user: user 
    });
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