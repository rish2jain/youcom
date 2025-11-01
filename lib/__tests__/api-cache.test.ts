/**
 * Tests for API response caching system
 */

import axios from "axios";
import { cachedApi, warmAPICache, getCriticalEndpoints } from "../api-cache";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock console methods
const consoleSpy = {
  log: jest.spyOn(console, "log").mockImplementation(),
  warn: jest.spyOn(console, "warn").mockImplementation(),
  error: jest.spyOn(console, "error").mockImplementation(),
};

describe("API Cache System", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    consoleSpy.log.mockClear();
    consoleSpy.warn.mockClear();
    consoleSpy.error.mockClear();

    // Clear cache before each test
    cachedApi.clearCache();
  });

  afterAll(() => {
    consoleSpy.log.mockRestore();
    consoleSpy.warn.mockRestore();
    consoleSpy.error.mockRestore();
  });

  describe("cachedApi.get", () => {
    it("should cache successful GET responses", async () => {
      const mockResponse = { data: { id: 1, name: "Test" } };
      mockedAxios.get.mockResolvedValueOnce({
        data: mockResponse.data,
        status: 200,
        statusText: "OK",
        headers: {},
        config: {},
      });

      // First request - should hit network
      const result1 = await cachedApi.get("/api/v1/test");
      expect(result1).toEqual(mockResponse.data);
      expect(mockedAxios.get).toHaveBeenCalledTimes(1);

      // Second request - should hit cache
      const result2 = await cachedApi.get("/api/v1/test");
      expect(result2).toEqual(mockResponse.data);
      expect(mockedAxios.get).toHaveBeenCalledTimes(1); // No additional network call
    });

    it("should handle network errors with stale cache fallback", async () => {
      const mockResponse = { data: { id: 1, name: "Test" } };

      // First successful request
      mockedAxios.get.mockResolvedValueOnce({
        data: mockResponse.data,
        status: 200,
        statusText: "OK",
        headers: {},
        config: {},
      });

      await cachedApi.get("/api/v1/test");

      // Second request fails
      mockedAxios.get.mockRejectedValueOnce(new Error("Network Error"));

      // Should return cached data
      const result = await cachedApi.get("/api/v1/test");
      expect(result).toEqual(mockResponse.data);
    });

    it("should respect TTL and refetch expired data", async () => {
      const mockResponse1 = { data: { id: 1, name: "Test1" } };
      const mockResponse2 = { data: { id: 2, name: "Test2" } };

      mockedAxios.get
        .mockResolvedValueOnce({
          data: mockResponse1.data,
          status: 200,
          statusText: "OK",
          headers: {
            date: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
          }, // 10 minutes ago
          config: {},
        })
        .mockResolvedValueOnce({
          data: mockResponse2.data,
          status: 200,
          statusText: "OK",
          headers: { date: new Date().toISOString() },
          config: {},
        });

      // First request
      const result1 = await cachedApi.get("/api/v1/news"); // Short TTL endpoint
      expect(result1).toEqual(mockResponse1.data);

      // Wait for cache to expire (mocked by old date header)
      const result2 = await cachedApi.get("/api/v1/news");
      expect(result2).toEqual(mockResponse2.data);
      expect(mockedAxios.get).toHaveBeenCalledTimes(2);
    });
  });

  describe("cachedApi.post", () => {
    it("should not cache POST responses but should invalidate related cache", async () => {
      const getResponse = { data: { items: [] } };
      const postResponse = { data: { id: 1, created: true } };

      // Setup GET cache
      mockedAxios.get.mockResolvedValueOnce({
        data: getResponse.data,
        status: 200,
        statusText: "OK",
        headers: {},
        config: {},
      });

      await cachedApi.get("/api/v1/watch");

      // POST request
      mockedAxios.post.mockResolvedValueOnce({
        data: postResponse.data,
        status: 201,
        statusText: "Created",
        headers: {},
        config: {},
      });

      const result = await cachedApi.post("/api/v1/watch", {
        name: "New Item",
      });
      expect(result).toEqual(postResponse.data);

      // Verify cache invalidation by checking if GET hits network again
      mockedAxios.get.mockResolvedValueOnce({
        data: { items: [{ id: 1, name: "New Item" }] },
        status: 200,
        statusText: "OK",
        headers: {},
        config: {},
      });

      await cachedApi.get("/api/v1/watch");
      expect(mockedAxios.get).toHaveBeenCalledTimes(2); // Cache was invalidated
    });
  });

  describe("Cache Management", () => {
    it("should provide cache statistics", async () => {
      const mockResponse = { data: { test: true } };
      mockedAxios.get.mockResolvedValue({
        data: mockResponse.data,
        status: 200,
        statusText: "OK",
        headers: {},
        config: {},
      });

      // Make some requests
      await cachedApi.get("/api/v1/test1");
      await cachedApi.get("/api/v1/test2");
      await cachedApi.get("/api/v1/test1"); // Cache hit

      const stats = cachedApi.getCacheStats();
      expect(stats.hits).toBe(1);
      expect(stats.misses).toBe(2);
      expect(stats.size).toBe(2);
      expect(stats.hitRate).toBe(1 / 3);
    });

    it("should clear cache when requested", async () => {
      const mockResponse = { data: { test: true } };
      mockedAxios.get.mockResolvedValue({
        data: mockResponse.data,
        status: 200,
        statusText: "OK",
        headers: {},
        config: {},
      });

      await cachedApi.get("/api/v1/test");

      let stats = cachedApi.getCacheStats();
      expect(stats.size).toBe(1);

      cachedApi.clearCache();

      stats = cachedApi.getCacheStats();
      expect(stats.size).toBe(0);
    });

    it("should invalidate cache by tags", async () => {
      const mockResponse = { data: { test: true } };
      mockedAxios.get.mockResolvedValue({
        data: mockResponse.data,
        status: 200,
        statusText: "OK",
        headers: {},
        config: {},
      });

      // Cache some endpoints
      await cachedApi.get("/api/v1/watch");
      await cachedApi.get("/api/v1/news");
      await cachedApi.get("/api/v1/analytics");

      let stats = cachedApi.getCacheStats();
      expect(stats.size).toBe(3);

      // Invalidate news-related cache
      const invalidated = cachedApi.invalidateCache(["news"]);
      expect(invalidated).toBe(1);

      stats = cachedApi.getCacheStats();
      expect(stats.size).toBe(2);
    });
  });

  describe("Cache Warming", () => {
    it("should warm cache for critical endpoints", async () => {
      const mockResponse = { data: { test: true } };
      mockedAxios.get.mockResolvedValue({
        data: mockResponse.data,
        status: 200,
        statusText: "OK",
        headers: {},
        config: {},
      });

      const endpoints = getCriticalEndpoints();
      await warmAPICache(endpoints);

      // Verify requests were made
      expect(mockedAxios.get).toHaveBeenCalledTimes(endpoints.length);

      // Verify cache is populated
      const stats = cachedApi.getCacheStats();
      expect(stats.size).toBe(endpoints.length);
    });

    it("should handle warming failures gracefully", async () => {
      mockedAxios.get
        .mockResolvedValueOnce({
          data: { success: true },
          status: 200,
          statusText: "OK",
          headers: {},
          config: {},
        })
        .mockRejectedValueOnce(new Error("Network Error"));

      const endpoints = [
        { url: "/api/v1/success" },
        { url: "/api/v1/failure" },
      ];

      await warmAPICache(endpoints);

      // Should not throw error
      const stats = cachedApi.getCacheStats();
      expect(stats.size).toBe(1); // Only successful request cached
    });
  });

  describe("Stale While Revalidate", () => {
    it("should return stale data while fetching fresh data in background", async () => {
      const staleResponse = { data: { version: 1 } };
      const freshResponse = { data: { version: 2 } };

      // First request - populate cache
      mockedAxios.get.mockResolvedValueOnce({
        data: staleResponse.data,
        status: 200,
        statusText: "OK",
        headers: { date: new Date(Date.now() - 1000).toISOString() }, // 1 second ago
        config: {},
      });

      await cachedApi.get("/api/v1/watch");

      // Second request - should return stale and fetch fresh in background
      mockedAxios.get.mockResolvedValueOnce({
        data: freshResponse.data,
        status: 200,
        statusText: "OK",
        headers: { date: new Date().toISOString() },
        config: {},
      });

      const result = await cachedApi.get("/api/v1/watch");

      // Should return stale data immediately
      expect(result).toEqual(staleResponse.data);

      // Background fetch should have been triggered
      expect(mockedAxios.get).toHaveBeenCalledTimes(2);
    });
  });
});
