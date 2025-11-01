import axios from "axios";
import { cachedApi } from "./api-cache";

// Extend window interface for error tracking
declare global {
  interface Window {
    backendErrorLogged?: boolean;
  }
}

// Use different URLs for server-side vs client-side requests
const getBackendUrl = () => {
  // In browser, ALWAYS use localhost (browsers cannot resolve Docker hostnames)
  // This check happens at module load time, so it's safe
  if (typeof window !== "undefined") {
    return "http://localhost:8765";
  }
  
  // For server-side, check environment variable but fix backend: hostname
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  
  // Always replace Docker hostname with localhost
  if (envUrl && envUrl.includes("backend:")) {
    return envUrl.replace("backend:", "localhost:");
  }
  
  // Default to localhost:8765 if no environment variable is set
  return envUrl || "http://localhost:8765";
};

// Get initial BACKEND_URL, but we'll fix it dynamically in interceptor
// Always use localhost for client-side - browsers can't resolve Docker hostnames
const getInitialBackendUrl = () => {
  // For client-side, always use localhost
  if (typeof window !== "undefined") {
    return "http://localhost:8765";
  }
  // For server-side, use environment variable or default
  const url = getBackendUrl();
  // Ensure server-side URL also doesn't contain backend: (safety check)
  return url.includes("backend:") ? url.replace(/backend:/g, "localhost:") : url;
};

const BACKEND_URL = getInitialBackendUrl();
const LOCAL_API_URL = ""; // Use relative URLs for Next.js API routes
const isDev = process.env.NODE_ENV !== "production";

// Enable caching by default in production
const USE_CACHE =
  process.env.NODE_ENV === "production" ||
  process.env.NEXT_PUBLIC_ENABLE_CACHE === "true";

// Create backend API client
// Ensure baseURL never contains backend: (fix at creation time)
const safeBackendUrl = BACKEND_URL.includes("backend:")
  ? BACKEND_URL.replace(/backend:/g, "localhost:")
  : BACKEND_URL;

// For client-side, always force localhost
const finalBackendUrl =
  typeof window !== "undefined" ? "http://localhost:8765" : safeBackendUrl;

export const backendApi = axios.create({
  baseURL: finalBackendUrl,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // Match backend 60s timeout for API orchestration
});

// Add request interceptor to fix URL on client side
// This runs BEFORE the request is sent, so we can fix the URL dynamically
backendApi.interceptors.request.use((config) => {
  // On client side (browser), ALWAYS replace backend: with localhost:
  // This is critical because browsers cannot resolve Docker hostnames
  if (typeof window !== "undefined") {
    // FORCE baseURL to always be localhost:8765 in browser
    // Don't rely on environment variables or cached values
    config.baseURL = "http://localhost:8765";
    
    // Fix URL if it's a full URL or contains backend:
    if (config.url && typeof config.url === "string") {
      // Replace any occurrence of backend: with localhost:
      config.url = config.url.replace(/backend:/g, "localhost:");
      // Also handle backend:8765 specifically
      config.url = config.url.replace(/backend:8765/g, "localhost:8765");
      
      // If the URL is a full URL starting with http://backend:, replace it
      if (config.url.startsWith("http://backend:") || config.url.startsWith("https://backend:")) {
        config.url = config.url.replace(/^https?:\/\/backend:/, "http://localhost:");
        config.baseURL = undefined; // Clear baseURL when using full URL
      }
    }
    
    // Final safety check: ensure baseURL never contains backend:
    if (config.baseURL && typeof config.baseURL === "string") {
      config.baseURL = config.baseURL.replace(/backend:/g, "localhost:");
    }
    
    // Additional check: If axios has already constructed the full URL, fix it
    // This handles cases where axios might have combined baseURL + url before the interceptor runs
    if (config.url && config.url.includes("backend:")) {
      config.url = config.url.replace(/backend:/g, "localhost:");
      // If it's now a full URL, clear baseURL
      if (config.url.startsWith("http://localhost:")) {
        // Extract just the path
        try {
          const urlObj = new URL(config.url);
          config.url = urlObj.pathname + urlObj.search;
          config.baseURL = `${urlObj.protocol}//${urlObj.host}`;
        } catch (e) {
          // If URL parsing fails, just ensure baseURL is set
          config.baseURL = "http://localhost:8765";
        }
      }
    }
  }
  return config;
}, (error) => {
  return Promise.reject(error);
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
    // Use cached API if caching is enabled
    if (USE_CACHE) {
      return cachedApi.get(url, config);
    }

    try {
      const response = await backendApi.get(url, config);
      return response.data;
    } catch (error: any) {
      if (
        error.code === "ECONNREFUSED" ||
        error.message.includes("Network Error")
      ) {
        throw new Error(
          `Backend server unavailable. Please ensure the FastAPI server is running at ${BACKEND_URL}`
        );
      }
      throw error;
    }
  },

  async post(url: string, data?: any, config?: any) {
    // Use cached API for POST requests (handles cache invalidation)
    if (USE_CACHE) {
      return cachedApi.post(url, data, config);
    }

    try {
      const response = await backendApi.post(url, data, config);
      return response.data;
    } catch (error: any) {
      if (
        error.code === "ECONNREFUSED" ||
        error.message.includes("Network Error")
      ) {
        throw new Error(
          `Backend server unavailable. Please ensure the FastAPI server is running at ${BACKEND_URL}`
        );
      }
      throw error;
    }
  },

  async put(url: string, data?: any, config?: any) {
    // Use cached API for PUT requests (handles cache invalidation)
    if (USE_CACHE) {
      return cachedApi.put(url, data, config);
    }

    try {
      const response = await backendApi.put(url, data, config);
      return response.data;
    } catch (error: any) {
      if (
        error.code === "ECONNREFUSED" ||
        error.message.includes("Network Error")
      ) {
        throw new Error(
          `Backend server unavailable. Please ensure the FastAPI server is running at ${BACKEND_URL}`
        );
      }
      throw error;
    }
  },

  async delete(url: string, config?: any) {
    // Use cached API for DELETE requests (handles cache invalidation)
    if (USE_CACHE) {
      return cachedApi.delete(url, config);
    }

    try {
      const response = await backendApi.delete(url, config);
      return response.data;
    } catch (error: any) {
      if (
        error.code === "ECONNREFUSED" ||
        error.message.includes("Network Error")
      ) {
        throw new Error(
          `Backend server unavailable. Please ensure the FastAPI server is running at ${BACKEND_URL}`
        );
      }
      throw error;
    }
  },

  // Cache management methods (only available when caching is enabled)
  getCacheStats: USE_CACHE ? () => cachedApi.getCacheStats() : undefined,
  clearCache: USE_CACHE ? () => cachedApi.clearCache() : undefined,
  invalidateCache: USE_CACHE
    ? (tags: string[]) => cachedApi.invalidateCache(tags)
    : undefined,
};

// Add interceptors to both clients
[backendApi, localApi].forEach((client) => {
  // Request interceptor for logging
  client.interceptors.request.use(
    (config) => {
      return config;
    },
    (error) => {
      // Only log request errors in development and not network errors
      if (
        isDev &&
        error.code !== "ECONNREFUSED" &&
        error.message !== "Network Error"
      ) {
        console.error("❌ API Request Error:", error);
      }
      return Promise.reject(error);
    }
  );

  // Response interceptor for logging and error handling
  client.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      // Handle network errors gracefully without excessive logging
      if (error.code === "ECONNREFUSED" || error.message === "Network Error") {
        // Only log once per session to avoid spam (client-side only)
        if (typeof window !== "undefined") {
          if (!window.backendErrorLogged) {
            console.warn("Backend service unavailable, using fallback data");
            window.backendErrorLogged = true;
          }
        }

        // Return a mock response for development
        if (isDev) {
          return Promise.resolve({
            data: { message: "Backend unavailable - using mock data" },
            status: 200,
            statusText: "OK",
          });
        }
      }

      // Only log other errors in development to avoid console spam
      if (
        isDev &&
        error.code !== "ECONNREFUSED" &&
        error.message !== "Network Error"
      ) {
        // Handle empty objects in error response
        const errorData = error.response?.data;
        const statusCode = error.response?.status;
        const statusText = error.response?.statusText;
        const requestUrl = error.config?.url || error.config?.baseURL || "unknown";
        
        // Safely extract error message - never allow empty objects
        let errorMessage = "Unknown error";
        if (error.message && typeof error.message === "string" && error.message.trim().length > 0) {
          errorMessage = error.message;
        } else if (error.response?.statusText && error.response.statusText.trim().length > 0) {
          errorMessage = error.response.statusText;
        }
        
        // Check if errorData has meaningful content - be very strict
        let errorContent: string | object | null = null;
        if (errorData !== undefined && errorData !== null) {
          // Handle different types of error data
          if (typeof errorData === "string" && errorData.trim().length > 0) {
            errorContent = errorData;
          } else if (Array.isArray(errorData) && errorData.length > 0) {
            errorContent = errorData;
          } else if (typeof errorData === "object") {
            const keys = Object.keys(errorData);
            if (keys.length > 0) {
              errorContent = errorData;
            }
          }
        }
        
        // Build informative error message - always log something meaningful
        // NEVER push empty objects - convert them to strings first
        const errorParts: (string | number)[] = [];
        errorParts.push("❌ API Response Error:");
        
        // Only add errorContent if it's truly meaningful and not an empty object
        // Triple-check: ensure we never push empty objects
        if (errorContent) {
          if (typeof errorContent === "object" && !Array.isArray(errorContent)) {
            const keys = Object.keys(errorContent);
            // Only push if object has keys
            if (keys.length > 0) {
              try {
                errorParts.push(JSON.stringify(errorContent, null, 2));
              } catch {
                errorParts.push(String(errorContent));
              }
            }
          } else if (typeof errorContent === "string" && errorContent.trim().length > 0) {
            errorParts.push(errorContent);
          } else if (Array.isArray(errorContent) && errorContent.length > 0) {
            errorParts.push(JSON.stringify(errorContent));
          }
        }
        
        // Always add error message (never empty)
        if (!errorContent || (typeof errorContent === "object" && Object.keys(errorContent).length === 0)) {
          errorParts.push(errorMessage);
          if (errorData !== undefined && errorData !== null && 
              typeof errorData === "object" && Object.keys(errorData).length === 0) {
            errorParts.push("(Response data was empty object)");
          }
        }
        
        if (statusCode) {
          errorParts.push(`Status: ${statusCode}`);
        }
        
        if (statusText && statusText.trim().length > 0) {
          errorParts.push(`(${statusText})`);
        }
        
        errorParts.push(`URL: ${requestUrl}`);
        
        // Final safety check - never log empty objects, convert everything to safe strings
        const safeLogParts = errorParts
          .filter((part) => {
            if (part === null || part === undefined) return false;
            if (typeof part === "object") {
              // Double-check: if it somehow got through, filter it out
              return Object.keys(part).length > 0;
            }
            return true;
          })
          .map((part) => {
            // Convert everything to string to ensure no objects slip through
            if (typeof part === "number") {
              return String(part);
            }
            if (typeof part === "object") {
              // This shouldn't happen due to filter, but extra safety
              try {
                return JSON.stringify(part);
              } catch {
                return String(part);
              }
            }
            return String(part);
          });
        
        // Log as a single formatted string to avoid any object serialization issues
        const logMessage = safeLogParts.join(" ");
        console.error(logMessage);
      }

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
