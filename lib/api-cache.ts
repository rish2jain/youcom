// API Response Caching with Intelligent TTL Management
import axios, { AxiosRequestConfig, AxiosResponse } from "axios";

export interface CacheConfig {
  ttl: number; // Time to live in milliseconds
  maxSize: number; // Maximum number of cached entries
  staleWhileRevalidate?: boolean; // Return stale data while fetching fresh
  tags?: string[]; // Cache tags for invalidation
}

export interface CachedResponse<T = any> {
  data: T;
  timestamp: number;
  ttl: number;
  etag?: string;
  lastModified?: string;
  tags: string[];
}

export interface CacheStats {
  hits: number;
  misses: number;
  size: number;
  hitRate: number;
}

// Cache configuration by endpoint pattern
const CACHE_CONFIGS: Record<string, CacheConfig> = {
  // Static data - long TTL
  "/api/v1/watch": {
    ttl: 5 * 60 * 1000, // 5 minutes
    maxSize: 50,
    staleWhileRevalidate: true,
    tags: ["watchlist"],
  },

  // Company data - medium TTL
  "/api/v1/research/company": {
    ttl: 15 * 60 * 1000, // 15 minutes
    maxSize: 100,
    staleWhileRevalidate: true,
    tags: ["company", "research"],
  },

  // News data - short TTL
  "/api/v1/news": {
    ttl: 2 * 60 * 1000, // 2 minutes
    maxSize: 200,
    staleWhileRevalidate: true,
    tags: ["news"],
  },

  // Impact cards - medium TTL
  "/api/v1/impact": {
    ttl: 10 * 60 * 1000, // 10 minutes
    maxSize: 100,
    staleWhileRevalidate: true,
    tags: ["impact", "analysis"],
  },

  // Analytics data - longer TTL
  "/api/v1/analytics": {
    ttl: 30 * 60 * 1000, // 30 minutes
    maxSize: 50,
    staleWhileRevalidate: true,
    tags: ["analytics"],
  },

  // User settings - long TTL
  "/api/v1/user": {
    ttl: 60 * 60 * 1000, // 1 hour
    maxSize: 20,
    staleWhileRevalidate: false,
    tags: ["user", "settings"],
  },

  // Health checks - very short TTL
  "/api/health": {
    ttl: 30 * 1000, // 30 seconds
    maxSize: 5,
    staleWhileRevalidate: false,
    tags: ["health"],
  },
};

class APICache {
  private cache = new Map<string, CachedResponse>();
  private stats: CacheStats = { hits: 0, misses: 0, size: 0, hitRate: 0 };
  private cleanupInterval: NodeJS.Timeout;

  constructor() {
    // Cleanup expired entries every 5 minutes
    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, 5 * 60 * 1000);
  }

  private getCacheKey(url: string, config?: AxiosRequestConfig): string {
    const params = config?.params ? JSON.stringify(config.params) : "";
    const headers = config?.headers ? JSON.stringify(config.headers) : "";
    return `${url}:${params}:${headers}`;
  }

  private getCacheConfig(url: string): CacheConfig {
    // Find matching cache config by URL pattern
    for (const [pattern, config] of Object.entries(CACHE_CONFIGS)) {
      if (url.includes(pattern)) {
        return config;
      }
    }

    // Default cache config
    return {
      ttl: 5 * 60 * 1000, // 5 minutes default
      maxSize: 50,
      staleWhileRevalidate: true,
      tags: ["default"],
    };
  }

  private isExpired(cached: CachedResponse): boolean {
    return Date.now() - cached.timestamp > cached.ttl;
  }

  private isStale(cached: CachedResponse): boolean {
    // Consider stale if more than 50% of TTL has passed
    return Date.now() - cached.timestamp > cached.ttl * 0.5;
  }

  get(key: string): CachedResponse | null {
    const cached = this.cache.get(key);

    if (!cached) {
      this.stats.misses++;
      this.updateHitRate();
      return null;
    }

    if (this.isExpired(cached)) {
      this.cache.delete(key);
      this.stats.misses++;
      this.updateHitRate();
      return null;
    }

    this.stats.hits++;
    this.updateHitRate();
    return cached;
  }

  set(key: string, response: AxiosResponse, config: CacheConfig): void {
    const cached: CachedResponse = {
      data: response.data,
      timestamp: Date.now(),
      ttl: config.ttl,
      etag: response.headers.etag,
      lastModified: response.headers["last-modified"],
      tags: config.tags || [],
    };

    this.cache.set(key, cached);
    this.stats.size = this.cache.size;

    // Enforce max size
    if (this.cache.size > config.maxSize) {
      this.evictOldest();
    }
  }

  invalidate(tags: string[]): number {
    let invalidated = 0;

    for (const [key, cached] of Array.from(this.cache.entries())) {
      if (cached.tags.some((tag) => tags.includes(tag))) {
        this.cache.delete(key);
        invalidated++;
      }
    }

    this.stats.size = this.cache.size;
    return invalidated;
  }

  clear(): void {
    this.cache.clear();
    this.stats = { hits: 0, misses: 0, size: 0, hitRate: 0 };
  }

  getStats(): CacheStats {
    return { ...this.stats };
  }

  private evictOldest(): void {
    const oldestKey = this.cache.keys().next().value;
    if (oldestKey) {
      this.cache.delete(oldestKey);
      this.stats.size = this.cache.size;
    }
  }

  private cleanup(): void {
    const now = Date.now();
    let cleaned = 0;

    for (const [key, cached] of Array.from(this.cache.entries())) {
      if (now - cached.timestamp > cached.ttl) {
        this.cache.delete(key);
        cleaned++;
      }
    }

    if (cleaned > 0) {
      this.stats.size = this.cache.size;
      console.log(`[API Cache] Cleaned up ${cleaned} expired entries`);
    }
  }

  private updateHitRate(): void {
    const total = this.stats.hits + this.stats.misses;
    this.stats.hitRate = total > 0 ? this.stats.hits / total : 0;
  }

  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }
    this.clear();
  }
}

// Singleton cache instance
const apiCache = new APICache();

// Enhanced API client with caching
class CachedAPIClient {
  private baseURL: string;
  private timeout: number;

  constructor(baseURL: string, timeout = 60000) {
    // Force localhost:8765 in browser - don't trust the passed baseURL
    if (typeof window !== "undefined") {
      this.baseURL = "http://localhost:8765";
    } else {
      // On server-side, use the passed baseURL but fix backend: hostname
      this.baseURL = baseURL.includes("backend:") 
        ? baseURL.replace("backend:", "localhost:")
        : baseURL;
    }
    this.timeout = timeout;
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    // Fix baseURL on client side
    let baseURL = this.baseURL;
    if (typeof window !== "undefined" && baseURL.includes("backend:")) {
      baseURL = baseURL.replace("backend:", "localhost:");
    }
    
    const fullUrl = `${baseURL}${url}`;
    // Final safety check on full URL
    const finalUrl = (typeof window !== "undefined" && fullUrl.includes("backend:"))
      ? fullUrl.replace("backend:", "localhost:")
      : fullUrl;
    
    const cacheKey = apiCache["getCacheKey"](finalUrl, config);
    const cacheConfig = apiCache["getCacheConfig"](url);

    // Check cache first
    const cached = apiCache.get(cacheKey);

    if (cached) {
      // Return cached data immediately if not stale or if stale-while-revalidate is disabled
      if (!apiCache["isStale"](cached) || !cacheConfig.staleWhileRevalidate) {
        return cached.data;
      }

      // For stale-while-revalidate, return cached data and fetch in background
      if (cacheConfig.staleWhileRevalidate) {
        this.fetchAndCache(finalUrl, config, cacheConfig, cacheKey).catch(
          (error) => {
            console.warn("[API Cache] Background refresh failed:", error);
          }
        );
        return cached.data;
      }
    }

    // Fetch from network
    return this.fetchAndCache(finalUrl, config, cacheConfig, cacheKey);
  }

  async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    // Fix baseURL on client side
    let baseURL = this.baseURL;
    if (typeof window !== "undefined" && baseURL.includes("backend:")) {
      baseURL = baseURL.replace("backend:", "localhost:");
    }
    let requestUrl = `${baseURL}${url}`;
    if (typeof window !== "undefined" && requestUrl.includes("backend:")) {
      requestUrl = requestUrl.replace("backend:", "localhost:");
    }
    
    // POST requests typically shouldn't be cached, but we can invalidate related cache entries
    const response = await this.makeRequest(
      "post",
      requestUrl,
      data,
      config
    );

    // Invalidate related cache entries
    this.invalidateRelatedCache(url);

    return response.data;
  }

  async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    // Fix baseURL on client side
    let baseURL = this.baseURL;
    if (typeof window !== "undefined" && baseURL.includes("backend:")) {
      baseURL = baseURL.replace("backend:", "localhost:");
    }
    let requestUrl = `${baseURL}${url}`;
    if (typeof window !== "undefined" && requestUrl.includes("backend:")) {
      requestUrl = requestUrl.replace("backend:", "localhost:");
    }
    
    const response = await this.makeRequest(
      "put",
      requestUrl,
      data,
      config
    );

    // Invalidate related cache entries
    this.invalidateRelatedCache(url);

    return response.data;
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    // Fix baseURL on client side
    let baseURL = this.baseURL;
    if (typeof window !== "undefined" && baseURL.includes("backend:")) {
      baseURL = baseURL.replace("backend:", "localhost:");
    }
    let requestUrl = `${baseURL}${url}`;
    if (typeof window !== "undefined" && requestUrl.includes("backend:")) {
      requestUrl = requestUrl.replace("backend:", "localhost:");
    }
    
    const response = await this.makeRequest(
      "delete",
      requestUrl,
      undefined,
      config
    );

    // Invalidate related cache entries
    this.invalidateRelatedCache(url);

    return response.data;
  }

  private async fetchAndCache<T>(
    url: string,
    config: AxiosRequestConfig | undefined,
    cacheConfig: CacheConfig,
    cacheKey: string
  ): Promise<T> {
    try {
      const response = await this.makeRequest("get", url, undefined, config);

      // Cache successful responses
      if (response.status >= 200 && response.status < 300) {
        apiCache.set(cacheKey, response, cacheConfig);
      }

      return response.data;
    } catch (error) {
      // If network fails and we have stale cache, return it
      const staleCache = apiCache.get(cacheKey);
      if (staleCache && cacheConfig.staleWhileRevalidate) {
        console.warn("[API Cache] Network failed, returning stale cache");
        return staleCache.data;
      }
      throw error;
    }
  }

  private async makeRequest(
    method: "get" | "post" | "put" | "delete",
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<AxiosResponse> {
    // On client side (browser), ALWAYS use localhost:8765 - browsers cannot resolve Docker hostnames
    let fixedUrl = url;
    let fixedBaseURL = this.baseURL;
    
    // On client side (browser), always replace backend: with localhost:
    if (typeof window !== "undefined") {
      // FORCE baseURL to always be localhost:8765 in browser
      fixedBaseURL = "http://localhost:8765";
      
      if (fixedUrl && fixedUrl.includes("backend:")) {
        fixedUrl = fixedUrl.replace(/backend:/g, "localhost:");
        fixedUrl = fixedUrl.replace(/backend:8765/g, "localhost:8765");
      }
    }
    
    // Build full URL from baseURL and url
    let fullUrl = fixedUrl.startsWith("http") 
      ? fixedUrl 
      : `${fixedBaseURL}${fixedUrl}`;
    
    // Final safety check on full URL - replace any remaining backend: references
    if (typeof window !== "undefined" && fullUrl.includes("backend:")) {
      fullUrl = fullUrl.replace(/backend:/g, "localhost:");
      fullUrl = fullUrl.replace(/backend:8765/g, "localhost:8765");
    }
    
    const finalUrl = fullUrl;
    
    const axiosConfig = {
      ...config,
      timeout: this.timeout,
      headers: {
        "Content-Type": "application/json",
        ...config?.headers,
      },
    };

    try {
      switch (method) {
        case "get":
          return await axios.get(finalUrl, axiosConfig);
        case "post":
          return await axios.post(finalUrl, data, axiosConfig);
        case "put":
          return await axios.put(finalUrl, data, axiosConfig);
        case "delete":
          return await axios.delete(finalUrl, axiosConfig);
        default:
          throw new Error(`Unsupported method: ${method}`);
      }
    } catch (error: any) {
      if (
        error.code === "ECONNREFUSED" ||
        error.message.includes("Network Error")
      ) {
        throw new Error(
          `Backend server unavailable. Please ensure the server is running at ${this.baseURL}`
        );
      }
      throw error;
    }
  }

  private invalidateRelatedCache(url: string): void {
    // Determine which cache tags to invalidate based on the URL
    const tags: string[] = [];

    if (url.includes("/watch")) tags.push("watchlist");
    if (url.includes("/research")) tags.push("research", "company");
    if (url.includes("/news")) tags.push("news");
    if (url.includes("/impact")) tags.push("impact", "analysis");
    if (url.includes("/analytics")) tags.push("analytics");
    if (url.includes("/user")) tags.push("user", "settings");

    if (tags.length > 0) {
      const invalidated = apiCache.invalidate(tags);
      console.log(
        `[API Cache] Invalidated ${invalidated} entries with tags:`,
        tags
      );
    }
  }

  // Cache management methods
  getCacheStats(): CacheStats {
    return apiCache.getStats();
  }

  clearCache(): void {
    apiCache.clear();
  }

  invalidateCache(tags: string[]): number {
    return apiCache.invalidate(tags);
  }
}

// Create cached API clients
const getBackendUrl = () => {
  // In browser, ALWAYS use localhost - browsers cannot resolve Docker hostnames
  if (typeof window !== "undefined") {
    return "http://localhost:8765";
  }
  // On server-side, use environment variable or default
  const envUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765";
  // Always replace Docker hostname with localhost
  if (envUrl.includes("backend:")) {
    return envUrl.replace("backend:", "localhost:");
  }
  return envUrl;
};
// Evaluate at runtime to ensure correct URL replacement
const getRuntimeBackendUrl = () => getBackendUrl();

// Create CachedAPIClient with dynamic URL evaluation
// Use a function to evaluate URL at runtime rather than module load time
export const cachedBackendApi = (() => {
  const backendUrl = getRuntimeBackendUrl();
  return new CachedAPIClient(backendUrl);
})();

// Enhanced API object with caching
export const cachedApi = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) =>
    cachedBackendApi.get<T>(url, config),

  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    cachedBackendApi.post<T>(url, data, config),

  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    cachedBackendApi.put<T>(url, data, config),

  delete: <T = any>(url: string, config?: AxiosRequestConfig) =>
    cachedBackendApi.delete<T>(url, config),

  // Cache management
  getCacheStats: () => cachedBackendApi.getCacheStats(),
  clearCache: () => cachedBackendApi.clearCache(),
  invalidateCache: (tags: string[]) => cachedBackendApi.invalidateCache(tags),
};

// Cache warming utilities
export const warmAPICache = async (
  endpoints: Array<{ url: string; config?: AxiosRequestConfig }>
) => {
  console.log(`[API Cache] Warming cache for ${endpoints.length} endpoints...`);

  const warmPromises = endpoints.map(async ({ url, config }) => {
    try {
      await cachedApi.get(url, config);
    } catch (error) {
      console.warn(`[API Cache] Failed to warm cache for ${url}:`, error);
    }
  });

  await Promise.allSettled(warmPromises);
  console.log("[API Cache] Cache warming completed");
};

// Critical endpoints for cache warming
export const getCriticalEndpoints = () => [
  { url: "/api/v1/watch" },
  { url: "/api/v1/news?limit=10" },
  { url: "/api/v1/impact?limit=5" },
  { url: "/api/health" },
];

export default cachedApi;
