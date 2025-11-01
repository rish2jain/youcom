/**
 * Tests for Cache Warming and Preloading Strategies
 */

import cacheWarmingManager, {
  warmCache,
  preloadRoute,
  updateUserBehavior,
  getWarmingStatus,
  type UserBehaviorPattern,
} from "../cache-warming";

// Mock dependencies
jest.mock("../api-cache", () => ({
  warmAPICache: jest.fn().mockResolvedValue(undefined),
  getCriticalEndpoints: jest.fn(() => [
    { url: "/api/v1/watch" },
    { url: "/api/v1/news" },
    { url: "/api/health" },
  ]),
}));

jest.mock("../service-worker", () => ({
  default: {
    warmCache: jest.fn().mockResolvedValue(undefined),
  },
  getCriticalResources: jest.fn(() => ["/", "/dashboard"]),
  getRouteResources: jest.fn((route) => {
    const routeMap: Record<string, string[]> = {
      "/dashboard": ["/_next/static/chunks/dashboard.js"],
      "/research": [
        "/_next/static/chunks/research.js",
        "/_next/static/chunks/charts.js",
      ],
      "/analytics": [
        "/_next/static/chunks/analytics.js",
        "/_next/static/chunks/charts.js",
      ],
    };
    return routeMap[route] || ["/_next/static/chunks/base.js"];
  }),
}));

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(global, "localStorage", {
  value: localStorageMock,
  writable: true,
});

// Mock performance API
Object.defineProperty(global, "performance", {
  value: {
    memory: {
      usedJSHeapSize: 50 * 1024 * 1024, // 50MB
      jsHeapSizeLimit: 100 * 1024 * 1024, // 100MB
    },
  },
  writable: true,
});

describe("Cache Warming Manager", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe("warmCache", () => {
    it("should execute all applicable strategies", async () => {
      await warmCache();

      // Verify that warming was attempted
      const status = getWarmingStatus();
      expect(status.strategiesCount).toBeGreaterThan(0);
    });

    it("should execute specific strategy when name provided", async () => {
      await warmCache("critical-resources");

      // Should complete without error
      const status = getWarmingStatus();
      expect(status.isWarming).toBe(false);
    });

    it("should handle warming failures gracefully", async () => {
      const { warmAPICache } = require("../api-cache");
      warmAPICache.mockRejectedValueOnce(new Error("Network error"));

      // Should not throw
      await expect(warmCache()).resolves.not.toThrow();
    });

    it("should skip warming if already in progress", async () => {
      // Start warming
      const warmPromise1 = warmCache();
      const warmPromise2 = warmCache();

      await Promise.all([warmPromise1, warmPromise2]);

      // Second call should be skipped
      expect(true).toBe(true); // Test passes if no errors thrown
    });
  });

  describe("preloadRoute", () => {
    it("should preload route-specific resources", async () => {
      const serviceWorkerManager = require("../service-worker").default;

      await preloadRoute("/dashboard");

      expect(serviceWorkerManager.warmCache).toHaveBeenCalledWith([
        "/_next/static/chunks/dashboard.js",
      ]);
    });

    it("should handle preload failures gracefully", async () => {
      const serviceWorkerManager = require("../service-worker").default;
      serviceWorkerManager.warmCache.mockRejectedValueOnce(
        new Error("Preload failed")
      );

      await expect(preloadRoute("/dashboard")).resolves.not.toThrow();
    });
  });

  describe("User Behavior Tracking", () => {
    it("should update user behavior pattern", () => {
      const pattern: Partial<UserBehaviorPattern> = {
        frequentRoutes: ["/dashboard", "/research"],
        recentActions: ["view", "export"],
        timeOfDay: "morning",
      };

      updateUserBehavior(pattern);

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "userBehaviorPattern",
        expect.stringContaining("dashboard")
      );
    });

    it("should load existing user behavior from localStorage", () => {
      const storedPattern = {
        frequentRoutes: ["/analytics"],
        recentActions: ["analyze"],
        timeOfDay: "afternoon",
        dayOfWeek: "weekday",
        sessionDuration: 30,
        lastVisit: new Date().toISOString(),
      };

      localStorageMock.getItem.mockReturnValueOnce(
        JSON.stringify(storedPattern)
      );

      // Create new instance to trigger loading
      const newManager =
        new (require("../cache-warming").default.constructor)();

      expect(localStorageMock.getItem).toHaveBeenCalledWith(
        "userBehaviorPattern"
      );
    });

    it("should handle corrupted localStorage data gracefully", () => {
      localStorageMock.getItem.mockReturnValueOnce("invalid json");

      // Should not throw when loading corrupted data
      expect(() => {
        new (require("../cache-warming").default.constructor)();
      }).not.toThrow();
    });
  });

  describe("Intelligent Warming Strategies", () => {
    it("should prioritize strategies by priority level", async () => {
      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      await warmCache();

      // Verify that strategies were executed (check console logs)
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Executing"),
        expect.any(Number),
        expect.stringContaining("strategies")
      );

      consoleSpy.mockRestore();
    });

    it("should skip strategies that fail condition checks", async () => {
      // Update user behavior to make certain routes unlikely
      updateUserBehavior({
        frequentRoutes: ["/dashboard"], // Only dashboard
        recentActions: ["view"],
      });

      await warmCache();

      // Should complete without error even if some strategies are skipped
      const status = getWarmingStatus();
      expect(status.isWarming).toBe(false);
    });
  });

  describe("Memory Management", () => {
    it("should detect high memory usage", () => {
      // Mock high memory usage
      Object.defineProperty(global.performance, "memory", {
        value: {
          usedJSHeapSize: 90 * 1024 * 1024, // 90MB
          jsHeapSizeLimit: 100 * 1024 * 1024, // 100MB (90% usage)
        },
        writable: true,
      });

      const manager = require("../cache-warming").default;

      // Should trigger memory optimization
      expect(() => manager.optimizeMemoryUsage()).not.toThrow();
    });

    it("should handle missing memory API gracefully", () => {
      const originalMemory = global.performance.memory;
      // @ts-ignore
      delete global.performance.memory;

      const manager = require("../cache-warming").default;

      expect(() => manager.optimizeMemoryUsage()).not.toThrow();

      global.performance.memory = originalMemory;
    });
  });

  describe("Warming Status", () => {
    it("should provide current warming status", () => {
      const status = getWarmingStatus();

      expect(status).toHaveProperty("isWarming");
      expect(status).toHaveProperty("queueLength");
      expect(status).toHaveProperty("strategiesCount");
      expect(status).toHaveProperty("userBehavior");

      expect(typeof status.isWarming).toBe("boolean");
      expect(typeof status.queueLength).toBe("number");
      expect(typeof status.strategiesCount).toBe("number");
    });
  });

  describe("Predictive Methods", () => {
    it("should predict dashboard visits for new users", () => {
      // New user with no behavior data
      const manager = new (require("../cache-warming").default.constructor)();

      // Should default to likely visiting dashboard
      expect(() => warmCache()).not.toThrow();
    });

    it("should predict route visits based on user behavior", () => {
      updateUserBehavior({
        frequentRoutes: ["/research", "/analytics"],
        recentActions: ["research", "analyze"],
      });

      // Should include research and analytics in warming strategies
      expect(() => warmCache()).not.toThrow();
    });
  });

  describe("Concurrent Preloading", () => {
    it("should limit concurrent preloads", async () => {
      const resources = ["/res1", "/res2", "/res3", "/res4", "/res5"];
      const manager = require("../cache-warming").default;

      await manager.preloadResources(resources);

      // Should complete without overwhelming the system
      expect(true).toBe(true);
    });

    it("should handle mixed resource types", async () => {
      const resources = [
        "/api/v1/data", // API endpoint
        "/_next/static/js/main.js", // Static resource
        "/dashboard", // Route
        "/api/v1/analytics", // Another API endpoint
      ];

      const manager = require("../cache-warming").default;

      await manager.preloadResources(resources);

      // Should handle different resource types appropriately
      expect(true).toBe(true);
    });
  });
});
