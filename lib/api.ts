import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765";
const isDev = process.env.NODE_ENV !== "production";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // 60 seconds for You.com API calls
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error("❌ API Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging and error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error(
      "❌ API Response Error:",
      error.response?.data || error.message
    );

    // Handle specific error cases
    if (error.response?.status === 502) {
      // You.com API error
      throw new Error(
        `You.com API Error: ${
          error.response.data?.detail || "Service unavailable"
        }`
      );
    }

    if (error.response?.status === 500) {
      throw new Error("Internal server error. Please try again.");
    }

    if (error.response?.status === 404) {
      throw new Error("Resource not found.");
    }

    return Promise.reject(error);
  }
);

export default api;
