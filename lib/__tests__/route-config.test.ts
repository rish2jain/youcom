/**
 * Tests for route configuration and code splitting
 */

import {
  routeConfigs,
  navigationPatterns,
  preloadRoute,
  preloadLikelyRoutes,
  getRouteKey,
} from "../route-config";

// Mock dynamic imports
jest.mock(
  "@/app/dashboard/page",
  () => ({
    default: () => "Dashboard",
  }),
  { virtual: true }
);

jest.mock(
  "@/app/research/page",
  () => ({
    default: () => "Research",
  }),
  { virtual: true }
);

jest.mock(
  "@/app/analytics/page",
  () => ({
    default: () => "Analytics",
  }),
  { virtual: true }
);

describe("Route Configuration", () => {
  describe("routeConfigs", () => {
    it("should have all required route configurations", () => {
      const expectedRoutes = [
        "dashboard",
        "research",
        "analytics",
        "monitoring",
        "integrations",
        "settings",
        "api-showcase",
        "demo",
      ];

      expectedRoutes.forEach((route) => {
        expect(routeConfigs[route]).toBeDefined();
        expect(routeConfigs[route]).toHaveProperty("path");
        expect(routeConfigs[route]).toHaveProperty("component");
        expect(routeConfigs[route]).toHaveProperty("priority");
      });
    });

    it("should have correct priority levels", () => {
      expect(routeConfigs.dashboard.priority).toBe("high");
      expect(routeConfigs.research.priority).toBe("medium");
      expect(routeConfigs.analytics.priority).toBe("medium");
      expect(routeConfigs.settings.priority).toBe("low");
    });

    it("should have preload configuration for critical routes", () => {
      expect(routeConfigs.dashboard.preload).toBe(true);
      expect(routeConfigs.research.preload).toBe(false);
      expect(routeConfigs.settings.preload).toBe(false);
    });
  });

  describe("navigationPatterns", () => {
    it("should define navigation patterns for main routes", () => {
      expect(navigationPatterns.dashboard).toContain("research");
      expect(navigationPatterns.dashboard).toContain("monitoring");
      expect(navigationPatterns.research).toContain("dashboard");
    });

    it("should not have circular references in patterns", () => {
      Object.entries(navigationPatterns).forEach(([route, patterns]) => {
        expect(patterns).not.toContain(route);
      });
    });
  });

  describe("getRouteKey", () => {
    it("should extract correct route keys from pathnames", () => {
      expect(getRouteKey("/")).toBe("dashboard");
      expect(getRouteKey("/dashboard")).toBe("dashboard");
      expect(getRouteKey("/research")).toBe("research");
      expect(getRouteKey("/analytics/details")).toBe("analytics");
      expect(getRouteKey("/settings/profile")).toBe("settings");
    });

    it("should handle edge cases", () => {
      expect(getRouteKey("")).toBe("dashboard");
      expect(getRouteKey("/unknown")).toBe("unknown");
      expect(getRouteKey("/research/company/123")).toBe("research");
    });
  });

  describe("preloadRoute", () => {
    it("should preload valid routes without errors", async () => {
      // Mock successful import
      const mockComponent = jest
        .fn()
        .mockResolvedValue({ default: () => "MockComponent" });
      routeConfigs.dashboard.component = mockComponent;

      await expect(preloadRoute("dashboard")).resolves.toBeUndefined();
      expect(mockComponent).toHaveBeenCalled();
    });

    it("should handle preload failures gracefully", async () => {
      // Mock failed import
      const mockComponent = jest
        .fn()
        .mockRejectedValue(new Error("Import failed"));
      routeConfigs.research.component = mockComponent;

      // Should not throw, but log warning
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();
      await expect(preloadRoute("research")).resolves.toBeUndefined();
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Failed to preload route research")
      );
      consoleSpy.mockRestore();
    });

    it("should handle invalid route keys", async () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();
      await preloadRoute("nonexistent");
      expect(consoleSpy).not.toHaveBeenCalled(); // Should return early
      consoleSpy.mockRestore();
    });
  });

  describe("preloadLikelyRoutes", () => {
    beforeEach(() => {
      // Mock all route components
      Object.keys(routeConfigs).forEach((route) => {
        routeConfigs[route].component = jest.fn().mockResolvedValue({
          default: () => `Mock${route}`,
        });
      });
    });

    it("should preload high priority routes first", async () => {
      const highPriorityMock = jest
        .fn()
        .mockResolvedValue({ default: () => "High" });
      const mediumPriorityMock = jest
        .fn()
        .mockResolvedValue({ default: () => "Medium" });

      routeConfigs.research.component = highPriorityMock;
      routeConfigs.research.priority = "high";
      routeConfigs.analytics.component = mediumPriorityMock;
      routeConfigs.analytics.priority = "medium";

      // Mock navigation patterns
      navigationPatterns.dashboard = ["research", "analytics"];

      await preloadLikelyRoutes("dashboard");

      // High priority should be called immediately
      expect(highPriorityMock).toHaveBeenCalled();
    });

    it("should handle routes with no navigation patterns", async () => {
      await expect(preloadLikelyRoutes("unknown")).resolves.toBeUndefined();
    });
  });
});

describe("Route Bundle Performance", () => {
  it("should have reasonable bundle size estimates", () => {
    // Test that route configurations suggest reasonable bundle sizes
    const heavyRoutes = ["analytics", "research"];
    const lightRoutes = ["settings", "integrations"];

    heavyRoutes.forEach((route) => {
      expect(routeConfigs[route].dependencies?.length).toBeGreaterThan(0);
    });

    lightRoutes.forEach((route) => {
      const deps = routeConfigs[route].dependencies || [];
      expect(deps.length).toBeLessThanOrEqual(2);
    });
  });

  it("should have proper dependency declarations", () => {
    // Analytics should depend on charts
    expect(routeConfigs.analytics.dependencies).toContain("charts");

    // Research should depend on company-research
    expect(routeConfigs.research.dependencies).toContain("company-research");

    // All routes should depend on common-ui
    Object.values(routeConfigs).forEach((config) => {
      if (config.dependencies) {
        expect(config.dependencies).toContain("common-ui");
      }
    });
  });
});
