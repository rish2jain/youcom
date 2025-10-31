import axios from "axios";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765";
const LOCAL_API_URL = ""; // Use relative URLs for Next.js API routes
const isDev = process.env.NODE_ENV !== "production";

// Create backend API client
export const backendApi = axios.create({
  baseURL: BACKEND_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 3000, // Shorter timeout for backend
});

// Create local API client (Next.js API routes)
export const localApi = axios.create({
  baseURL: LOCAL_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// API client that calls the FastAPI backend
// All frontend requests go through the backend, which handles:
// - You.com API calls (Search, Chat, ARI)
// - PostgreSQL database operations
// - Business logic and data processing
export const api = {
  async get(url: string, config?: any) {
    try {
      const response = await backendApi.get(url, config);
      return response.data;
    } catch (error: any) {
      if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
        throw new Error(
          `Backend server unavailable. Please ensure the FastAPI server is running at ${BACKEND_URL}`
        );
      }
      throw error;
    }
  },

  async post(url: string, data?: any, config?: any) {
    try {
      const response = await backendApi.post(url, data, config);
      return response.data;
    } catch (error: any) {
      if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
        throw new Error(
          `Backend server unavailable. Please ensure the FastAPI server is running at ${BACKEND_URL}`
        );
      }
      throw error;
    }
  },

  async put(url: string, data?: any, config?: any) {
    try {
      const response = await backendApi.put(url, data, config);
      return response.data;
    } catch (error: any) {
      if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
        throw new Error(
          `Backend server unavailable. Please ensure the FastAPI server is running at ${BACKEND_URL}`
        );
      }
      throw error;
    }
  },

  async delete(url: string, config?: any) {
    try {
      const response = await backendApi.delete(url, config);
      return response.data;
    } catch (error: any) {
      if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
        throw new Error(
          `Backend server unavailable. Please ensure the FastAPI server is running at ${BACKEND_URL}`
        );
      }
      throw error;
    }
  },
};

// Add interceptors to both clients
[backendApi, localApi].forEach((client) => {
  // Request interceptor for logging
  client.interceptors.request.use(
    (config) => {
      return config;
    },
    (error) => {
      console.error("❌ API Request Error:", error);
      return Promise.reject(error);
    }
  );

  // Response interceptor for logging and error handling
  client.interceptors.response.use(
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
});

export default api;
