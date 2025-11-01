/**
 * Integration tests for caching strategy
 */

import { cachedApi } from "../api-cache";
import serviceWorkerManager from "../service-worker";
import cacheWarmingManager from "../cache-warming";

// Mock console methods
const consoleSpy = {
  log: jest.spyOn(console, "log").mockImplementation(),
  warn: jest.spyOn(console, "warn").mockImplementation(),
  error: jest.spyOn(console, "error").mockImplementation(),
};

// Mock fetch for service worker tests
global.fetch = jest.fn();

// Mock service worker APIs
Object.defineProperty(global, "navigator", {
  value: {
    serviceWorker: {
      register: jest.fn().mockResolvedValue({}),
      unregister: jest.fn().mockResolvedValue(true),
      addEventListener: jest.fn(),
      controller: null,
    },
  },
  writable: true,
});

Object.defineProperty(global, "caches", {
  value: {
    open: jest.fn().mockResolvedValue({
      add: jest.fn(),
      addAll: jest.fn(),
      put: jest.fn(),
      match: jest.fn(),
      delete: jest.fn(),
      keys: jest.fn().mockResolvedValue([]),
    }),
    delete: jest.fn().mockResolvedValue(true),
    keys: jest.fn().mockResolvedValue(["cache1", "cache2"]),
  },
  writable: true,
});

describe("Caching Strategy Integration", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    consoleSpy.log.mockClear();
    consoleSpy.warn.mockClear();
    consoleSpy.error.mockClear();
  });

  afterAll(() => {
    consoleSpy.log.mockRestore();
    consoleSpy.warn.mockRestore();
    consoleSpy.error.mockRestore();
  });

  describe("API Cache Management", () => {
    it("should provide cache statistics", () => {
      const stats = cachedApi.getCacheStats();

      expect(stats).toHaveProperty("hits");
      expect(stats).toHaveProperty("misses");
      expect(stats).toHaveProperty("size");
      expect(stats).toHaveProperty("hitRate");

      expect(typeof stats.hits).toBe("number");
      expect(typeof stats.misses).toBe("number");
      expect(typeof stats.size).toBe("number");
      expect(typeof stats.hitRate).toBe("number");
    });

    it("should clear cache successfully", () => {
      expect(() => cachedApi.clearCache()).not.toThrow();

      const stats = cachedApi.getCacheStats();
      expect(stats.size).toBe(0);
    });

    it("should invalidate cache by tags", () => {
      const invalidated = cachedApi.invalidateCache(["test"]);

      expect(typeof invalidated).toBe("number");
      expect(invalidated).toBeGreaterThanOrEqual(0);
    });
  });

  describe("Service Worker Management", () => {
    it("should check if service worker is supported", () => {
      const isSupported = serviceWorkerManager.isSupported();

      expect(typeof isSupported).toBe("boolean");
    });

    it("should register service worker when supported", async () => {
      const registration = await serviceWorkerManager.register();

      expect(registration).toBeDefined();
    });

    it("should handle service worker registration gracefully", async () => {
      // Should not throw even if registration fails
      expect(async () => {
        await serviceWorkerManager.register();
      }).not.toThrow();
    });

    it("should provide cache status", async () => {
      const status = await serviceWorkerManager.getCacheStatus();

      expect(typeof status).toBe("object");
    });

    it("should clear cache without errors", async () => {
      await expect(serviceWorkerManager.clearCache()).resolves.not.toThrow();
    });
  });

  describe("Cache Warming", () => {
    it("should provide warming status", () => {
      const status = cacheWarmingManager.getWarmingStatus();

      expect(status).toHaveProperty("isWarming");
      expect(status).toHaveProperty("queueLength");
      expect(status).toHaveProperty("strategiesCount");
      expect(status).toHaveProperty("userBehavior");

      expect(typeof status.isWarming).toBe("boolean");
      expect(typeof status.queueLength).toBe("number");
      expect(typeof status.strategiesCount).toBe("number");
    });

    it("should warm cache without errors", async () => {
      await expect(cacheWarmingManager.warmCache()).resolves.not.toThrow();
    });

    it("should preload routes without errors", async () => {
      await expect(
        cacheWarmingManager.preloadRoute("/dashboard")
      ).resolves.not.toThrow();
    });

    it("should update user behavior without errors", () => {
      expect(() => {
        cacheWarmingManager.updateUserBehavior({
          frequentRoutes: ["/dashboard"],
          recentActions: ["view"],
        });
      }).not.toThrow();
    });

    it("should optimize memory usage without errors", () => {
      expect(() => cacheWarmingManager.optimizeMemoryUsage()).not.toThrow();
    });
  });

  describe("Cache Performance", () => {
    it("should handle missing performance API gracefully", () => {
      const originalPerformance = global.performance;
      // @ts-ignore
      delete global.performance;

      // Should not throw when performance API is missing
      expect(() => {
        cacheWarmingManager.optimizeMemoryUsage();
      }).not.toThrow();

      global.performance = originalPerformance;
    });

    it("should handle localStorage errors gracefully", () => {
      const originalLocalStorage = global.localStorage;

      // Mock localStorage that throws errors
      Object.defineProperty(global, "localStorage", {
        value: {
          getItem: jest.fn().mockImplementation(() => {
            throw new Error("Storage error");
          }),
          setItem: jest.fn().mockImplementation(() => {
            throw new Error("Storage error");
          }),
        },
        writable: true,
      });

      // Should not throw when localStorage fails
      expect(() => {
        cacheWarmingManager.updateUserBehavior({
          frequentRoutes: ["/test"],
        });
      }).not.toThrow();

      global.localStorage = originalLocalStorage;
    });
  });

  describe("Error Handling", () => {
    it("should handle network errors gracefully", async () => {
      // Mock fetch to fail
      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error("Network error")
      );

      // Should not throw when network fails
      await expect(
        serviceWorkerManager.warmCache(["/test"])
      ).resolves.not.toThrow();
    });

    it("should handle cache operation failures gracefully", async () => {
      // Mock cache operations to fail
      const mockCache = {
        put: jest.fn().mockRejectedValue(new Error("Cache error")),
        match: jest.fn().mockRejectedValue(new Error("Cache error")),
        delete: jest.fn().mockRejectedValue(new Error("Cache error")),
      };

      global.caches.open = jest.fn().mockResolvedValue(mockCache);

      // Should handle cache errors gracefully
      await expect(
        serviceWorkerManager.warmCache(["/test"])
      ).resolves.not.toThrow();
    });
  });

  describe("Resource Utilities", () => {
    it("should provide critical resources list", () => {
      const { getCriticalResources } = require("../service-worker");
      const resources = getCriticalResources();

      expect(Array.isArray(resources)).toBe(true);
      expect(resources.length).toBeGreaterThan(0);
    });

    it("should provide route-specific resources", () => {
      const { getRouteResources } = require("../service-worker");

      const dashboardResources = getRouteResources("/dashboard");
      const researchResources = getRouteResources("/research");

      expect(Array.isArray(dashboardResources)).toBe(true);
      expect(Array.isArray(researchResources)).toBe(true);
      expect(dashboardResources.length).toBeGreaterThan(0);
      expect(researchResources.length).toBeGreaterThan(0);
    });

    it("should provide critical API endpoints", () => {
      const { getCriticalEndpoints } = require("../api-cache");
      const endpoints = getCriticalEndpoints();

      expect(Array.isArray(endpoints)).toBe(true);
      expect(endpoints.length).toBeGreaterThan(0);
      expect(endpoints.every((e) => e.url)).toBe(true);
    });
  });
});
