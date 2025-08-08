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

    // Get user data from localStorage
    const userData = localStorage.getItem("user");
    console.log("Raw userData from localStorage:", userData);
    console.log("UserData exists:", !!userData);

    if (userData) {
      try {
        const user = JSON.parse(userData);
        console.log("Parsed user object:", user);
        console.log("User ID exists:", !!user?.id, "Value:", user?.id);
        console.log("User team exists:", !!user?.team, "Value:", user?.team);
        console.log("User role exists:", !!user?.role, "Value:", user?.role);
        console.log("User name exists:", !!user?.name, "Value:", user?.name);

        // Ensure we have valid user data before setting headers
        if (user && user.id && user.team) {
          // Always set headers with actual values
          config.headers["X-User-Id"] = String(user.id);
          config.headers["X-User-Team"] = String(user.team);
          config.headers["X-User-Role"] = String(user.role || 'user');
          config.headers["X-User-Name"] = String(user.name || 'Unknown');

          console.log("✅ Headers SET successfully:", {
            "X-User-Id": config.headers["X-User-Id"],
            "X-User-Team": config.headers["X-User-Team"],
            "X-User-Role": config.headers["X-User-Role"],
            "X-User-Name": config.headers["X-User-Name"]
          });
        } else {
          console.error("❌ FAILED validation - Missing required fields:");
          console.error("- user object exists:", !!user);
          console.error("- user.id exists:", !!user?.id);
          console.error("- user.team exists:", !!user?.team);
          console.warn("Invalid user data structure:", user);
          // Clear invalid data
          localStorage.removeItem("user");
          localStorage.removeItem("token");
        }

        console.log("Final request headers keys:", Object.keys(config.headers));
        console.log("Auth headers specifically:", {
          "X-User-Id": config.headers["X-User-Id"],
          "X-User-Team": config.headers["X-User-Team"],
          "X-User-Role": config.headers["X-User-Role"],
          "X-User-Name": config.headers["X-User-Name"]
        });
      } catch (error) {
        console.error("❌ Error parsing user data:", error);
        console.error("Raw userData that failed:", userData);
        // Clear corrupted data
        localStorage.removeItem("user");
        localStorage.removeItem("token");
      }
    } else {
      console.warn("❌ No user data found in localStorage - headers will not be set");
      console.log("Available localStorage keys:", Object.keys(localStorage));
    }
    console.log("=== END AXIOS INTERCEPTOR DEBUG ===");
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
