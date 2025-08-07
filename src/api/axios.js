import axios from "axios";

// Use the Replit URL for the backend when available, fallback to localhost
const getBaseURL = () => {
  // Check if we're in Replit environment
  const replitUrl = window.location.origin.replace(":3000", ":5000");
  if (replitUrl.includes("replit.dev") || replitUrl.includes("repl.co")) {
    return replitUrl;
  }

  // Fallback to environment variable or localhost
  return import.meta.env.VITE_API_URL || "http://localhost:5000";
};

const instance = axios.create({
  baseURL: getBaseURL(),
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor to include user headers
instance.interceptors.request.use(
  (config) => {
    console.log("=== AXIOS INTERCEPTOR DEBUG ===");
    console.log("Making request to:", config.baseURL + config.url);
    console.log("Request method:", config.method);

    // Get user data from localStorage
    const userData = localStorage.getItem("user");
    console.log("User data from localStorage:", userData);

    if (userData) {
      try {
        const user = JSON.parse(userData);
        console.log("Parsed user object:", user);

        // Always set headers with actual values
        config.headers["X-User-Id"] = String(user.id || '');
        config.headers["X-User-Team"] = String(user.team || '');
        config.headers["X-User-Role"] = String(user.role || 'user');
        config.headers["X-User-Name"] = String(user.name || 'Unknown');

        console.log("Set headers:", {
          "X-User-Id": config.headers["X-User-Id"],
          "X-User-Team": config.headers["X-User-Team"],
          "X-User-Role": config.headers["X-User-Role"],
          "X-User-Name": config.headers["X-User-Name"]
        });

        console.log("Final request headers:", config.headers);
        console.log("All headers keys:", Object.keys(config.headers));
      } catch (error) {
        console.error("Error parsing user data:", error);
      }
    } else {
      console.warn("No user data found in localStorage");
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Add response interceptor for better error handling
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === "ERR_NETWORK") {
      console.error("Network error - backend server may not be running");
    }
    return Promise.reject(error);
  },
);

export default instance;