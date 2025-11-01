/**
 * Tests for intelligent prefetching system
 */

import {
  IntelligentPrefetcher,
  intelligentPrefetcher,
} from "../intelligent-prefetching";

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
});

// Mock route preloading
jest.mock("../route-config", () => ({
  preloadRoute: jest.fn().mockResolvedValue(undefined),
  navigationPatterns: {
    dashboard: ["research", "monitoring"],
    research: ["dashboard", "analytics"],
    analytics: ["dashboard", "monitoring"],
  },
  getRouteKey: jest.fn((path: string) => {
    if (path === "/" || path === "/dashboard") return "dashboard";
    return path.split("/")[1] || "dashboard";
  }),
}));

// Mock shared component optimizer
jest.mock("../shared-components", () => ({
  sharedComponentOptimizer: {
    preloadRouteComponents: jest.fn().mockResolvedValue(undefined),
  },
}));

describe("IntelligentPrefetcher", () => {
  let prefetcher: IntelligentPrefetcher;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);

    // Create fresh instance
    prefetcher = new (IntelligentPrefetcher as any)();
  });

  describe("Behavior Tracking", () => {
    it("should track route visits correctly", () => {
      prefetcher.trackRouteVisit("dashboard");
      prefetcher.trackRouteVisit("research", "dashboard");
      prefetcher.trackRouteVisit("analytics", "research");

      const analytics = prefetcher.getAnalytics();

      expect(analytics.behaviorData.visitedRoutes).toEqual([
        "dashboard",
        "research",
        "analytics",
      ]);
      expect(analytics.behaviorData.routeTransitions.dashboard.research).toBe(
        1
      );
      expect(analytics.behaviorData.routeTransitions.research.analytics).toBe(
        1
      );
    });

    it("should accumulate route transition counts", () => {
      prefetcher.trackRouteVisit("dashboard");
      prefetcher.trackRouteVisit("research", "dashboard");
      prefetcher.trackRouteVisit("dashboard", "research");
      prefetcher.trackRouteVisit("research", "dashboard");

      const analytics = prefetcher.getAnalytics();

      expect(analytics.behaviorData.routeTransitions.dashboard.research).toBe(
        2
      );
      expect(analytics.behaviorData.routeTransitions.research.dashboard).toBe(
        1
      );
    });

    it("should track time spent on routes", (done) => {
      prefetcher.trackRouteVisit("dashboard");

      setTimeout(() => {
        prefetcher.trackRouteVisit("research", "dashboard");

        const analytics = prefetcher.getAnalytics();
        expect(
          analytics.behaviorData.timeSpentOnRoutes.dashboard
        ).toBeGreaterThan(0);
        done();
      }, 10);
    });
  });

  describe("Prefetching Strategies", () => {
    it("should execute navigation pattern strategy", async () => {
      const mockPreloadRoute = require("../route-config").preloadRoute;

      prefetcher.trackRouteVisit("dashboard");

      // Wait for async prefetching to complete
      await new Promise((resolve) => setTimeout(resolve, 100));

      expect(mockPreloadRoute).toHaveBeenCalled();
    });

    it("should prioritize frequently visited routes", () => {
      // Simulate frequent visits to research
      for (let i = 0; i < 5; i++) {
        prefetcher.trackRouteVisit("dashboard");
        prefetcher.trackRouteVisit("research", "dashboard");
      }

      const priority = (prefetcher as any).calculateRoutePriority("research");
      expect(priority).toBeGreaterThan(0);
    });

    it("should handle empty behavior data gracefully", async () => {
      const strategies = (prefetcher as any).strategies;

      for (const strategy of strategies) {
        const result = await strategy.execute("dashboard", {
          visitedRoutes: [],
          routeTransitions: {},
          timeSpentOnRoutes: {},
          sessionStartTime: Date.now(),
          lastActivity: Date.now(),
        });

        expect(Array.isArray(result)).toBe(true);
      }
    });
  });

  describe("Hover-based Prefetching", () => {
    it("should prefetch on hover with appropriate delay", (done) => {
      const mockPreloadRoute = require("../route-config").preloadRoute;

      prefetcher.prefetchOnHover("research", 500);

      // Should not be called immediately
      expect(mockPreloadRoute).not.toHaveBeenCalled();

      setTimeout(() => {
        expect(mockPreloadRoute).toHaveBeenCalledWith("research");
        done();
      }, 200);
    });

    it("should adjust delay based on hover duration", () => {
      const addToQueueSpy = jest.spyOn(prefetcher as any, "addToPrefetchQueue");

      // Long hover should result in higher priority
      prefetcher.prefetchOnHover("research", 1000);

      expect(addToQueueSpy).toHaveBeenCalled();
    });

    it("should not prefetch already prefetched routes", () => {
      (prefetcher as any).prefetchedRoutes.add("research");

      const addToQueueSpy = jest.spyOn(prefetcher as any, "addToPrefetchQueue");
      prefetcher.prefetchOnHover("research", 500);

      expect(addToQueueSpy).not.toHaveBeenCalled();
    });
  });

  describe("Analytics and Reporting", () => {
    it("should calculate hit rate correctly", () => {
      // Simulate prefetching and visiting
      (prefetcher as any).prefetchedRoutes.add("research");
      (prefetcher as any).prefetchedRoutes.add("analytics");

      prefetcher.trackRouteVisit("research");
      // analytics not visited

      const analytics = prefetcher.getAnalytics();
      expect(analytics.hitRate).toBe(0.5); // 1 out of 2 prefetched routes visited
    });

    it("should provide comprehensive analytics", () => {
      prefetcher.trackRouteVisit("dashboard");
      prefetcher.trackRouteVisit("research", "dashboard");

      const analytics = prefetcher.getAnalytics();

      expect(analytics).toHaveProperty("prefetchedRoutes");
      expect(analytics).toHaveProperty("queueLength");
      expect(analytics).toHaveProperty("behaviorData");
      expect(analytics).toHaveProperty("hitRate");

      expect(analytics.behaviorData.visitedRoutes).toContain("dashboard");
      expect(analytics.behaviorData.visitedRoutes).toContain("research");
    });
  });

  describe("Data Persistence", () => {
    it("should save behavior data to localStorage", () => {
      prefetcher.trackRouteVisit("dashboard");

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "route-prefetch-behavior",
        expect.stringContaining("dashboard")
      );
    });

    it("should load behavior data from localStorage", () => {
      const mockData = {
        visitedRoutes: ["dashboard", "research"],
        routeTransitions: { dashboard: { research: 2 } },
        timeSpentOnRoutes: { dashboard: 5000 },
        sessionStartTime: Date.now() - 1000000,
        lastActivity: Date.now(),
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockData));

      const newPrefetcher = new (IntelligentPrefetcher as any)();
      const analytics = newPrefetcher.getAnalytics();

      expect(analytics.behaviorData.visitedRoutes).toEqual([
        "dashboard",
        "research",
      ]);
    });

    it("should ignore old behavior data", () => {
      const oldData = {
        visitedRoutes: ["dashboard"],
        sessionStartTime: Date.now() - 8 * 24 * 60 * 60 * 1000, // 8 days ago
        lastActivity: Date.now(),
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(oldData));

      const newPrefetcher = new (IntelligentPrefetcher as any)();
      const analytics = newPrefetcher.getAnalytics();

      expect(analytics.behaviorData.visitedRoutes).toEqual([]);
    });

    it("should handle localStorage errors gracefully", () => {
      localStorageMock.getItem.mockImplementation(() => {
        throw new Error("localStorage error");
      });

      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      expect(() => new (IntelligentPrefetcher as any)()).not.toThrow();
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Failed to load behavior data")
      );

      consoleSpy.mockRestore();
    });
  });

  describe("Queue Management", () => {
    it("should process prefetch queue in priority order", async () => {
      const mockPreloadRoute = require("../route-config").preloadRoute;

      // Add routes with different priorities
      (prefetcher as any).addToPrefetchQueue("research", 5);
      (prefetcher as any).addToPrefetchQueue("analytics", 10);
      (prefetcher as any).addToPrefetchQueue("settings", 3);

      await (prefetcher as any).processPrefetchQueue();

      // Should process analytics first (highest priority)
      expect(mockPreloadRoute).toHaveBeenCalledWith("analytics");
    });

    it("should limit concurrent prefetching", async () => {
      const mockPreloadRoute = require("../route-config").preloadRoute;

      // Add many routes
      for (let i = 0; i < 10; i++) {
        (prefetcher as any).addToPrefetchQueue(`route${i}`, i);
      }

      await (prefetcher as any).processPrefetchQueue();

      // Should not process more than 3 at once
      expect(mockPreloadRoute).toHaveBeenCalledTimes(3);
    });
  });

  describe("Reset Functionality", () => {
    it("should reset behavior data completely", () => {
      prefetcher.trackRouteVisit("dashboard");
      prefetcher.trackRouteVisit("research", "dashboard");

      prefetcher.resetBehaviorData();

      const analytics = prefetcher.getAnalytics();
      expect(analytics.behaviorData.visitedRoutes).toEqual([]);
      expect(analytics.behaviorData.routeTransitions).toEqual({});
      expect(localStorageMock.removeItem).toHaveBeenCalledWith(
        "route-prefetch-behavior"
      );
    });
  });
});
