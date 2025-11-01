/**
 * Tests for shared component optimization system
 */

import {
  SharedComponentOptimizer,
  sharedComponents,
  routeComponentUsage,
  sharedComponentOptimizer,
} from "../shared-components";

// Mock component imports
const mockComponents = {
  LoadingSkeleton: { default: () => "LoadingSkeleton" },
  ErrorBoundary: { default: () => "ErrorBoundary" },
  NotificationSystem: { default: () => "NotificationSystem" },
  Header: { default: () => "Header" },
  Sidebar: { default: () => "Sidebar" },
};

describe("Shared Components Configuration", () => {
  describe("sharedComponents", () => {
    it("should have all critical components defined", () => {
      const criticalComponents = Object.entries(sharedComponents)
        .filter(([_, config]) => config.priority === "critical")
        .map(([name]) => name);

      expect(criticalComponents).toContain("LoadingSkeleton");
      expect(criticalComponents).toContain("ErrorBoundary");
    });

    it("should have proper priority distribution", () => {
      const priorities = Object.values(sharedComponents).map(
        (config) => config.priority
      );

      expect(priorities).toContain("critical");
      expect(priorities).toContain("high");
      expect(priorities).toContain("medium");
      expect(priorities).toContain("low");
    });

    it("should have preload configuration for critical components", () => {
      Object.entries(sharedComponents).forEach(([name, config]) => {
        if (config.priority === "critical") {
          expect(config.preload).toBe(true);
        }
      });
    });

    it("should have route usage defined for all components", () => {
      Object.entries(sharedComponents).forEach(([name, config]) => {
        expect(config.usedInRoutes).toBeDefined();
        expect(config.usedInRoutes.length).toBeGreaterThan(0);
      });
    });
  });

  describe("routeComponentUsage", () => {
    it("should define component usage for all major routes", () => {
      const expectedRoutes = [
        "dashboard",
        "research",
        "analytics",
        "monitoring",
        "integrations",
        "settings",
      ];

      expectedRoutes.forEach((route) => {
        expect(
          routeComponentUsage[route as keyof typeof routeComponentUsage]
        ).toBeDefined();
        expect(
          routeComponentUsage[route as keyof typeof routeComponentUsage].length
        ).toBeGreaterThan(0);
      });
    });

    it("should include critical components in all routes", () => {
      const criticalComponents = ["LoadingSkeleton", "ErrorBoundary"];

      Object.values(routeComponentUsage).forEach((components) => {
        criticalComponents.forEach((critical) => {
          expect(components).toContain(critical);
        });
      });
    });

    it("should have consistent component references", () => {
      const allUsedComponents = new Set<string>();
      Object.values(routeComponentUsage).forEach((components) => {
        components.forEach((comp) => allUsedComponents.add(comp));
      });

      allUsedComponents.forEach((component) => {
        expect(sharedComponents[component]).toBeDefined();
      });
    });
  });
});

describe("SharedComponentOptimizer", () => {
  let optimizer: SharedComponentOptimizer;

  beforeEach(() => {
    optimizer = new (SharedComponentOptimizer as any)();

    // Mock component imports
    Object.entries(sharedComponents).forEach(([name, config]) => {
      config.component = jest
        .fn()
        .mockResolvedValue(
          mockComponents[name as keyof typeof mockComponents] || {
            default: () => name,
          }
        );
    });
  });

  describe("Component Preloading", () => {
    it("should preload critical components", async () => {
      await optimizer.preloadCriticalComponents();

      const criticalComponents = Object.entries(sharedComponents).filter(
        ([_, config]) => config.priority === "critical" && config.preload
      );

      criticalComponents.forEach(([name, config]) => {
        expect(config.component).toHaveBeenCalled();
        expect(optimizer.isPreloaded(name)).toBe(true);
      });
    });

    it("should handle preload failures gracefully", async () => {
      const failingComponent = "LoadingSkeleton";
      sharedComponents[failingComponent].component = jest
        .fn()
        .mockRejectedValue(new Error("Import failed"));

      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      await optimizer.preloadCriticalComponents();

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining(
          `Failed to preload critical component ${failingComponent}`
        )
      );
      expect(optimizer.isPreloaded(failingComponent)).toBe(false);

      consoleSpy.mockRestore();
    });

    it("should preload route-specific components", async () => {
      await optimizer.preloadRouteComponents("dashboard");

      const dashboardComponents = routeComponentUsage.dashboard.filter(
        (name) => sharedComponents[name]?.preload
      );

      dashboardComponents.forEach((name) => {
        expect(sharedComponents[name].component).toHaveBeenCalled();
        expect(optimizer.isPreloaded(name)).toBe(true);
      });
    });

    it("should not preload components twice", async () => {
      const componentName = "LoadingSkeleton";
      const mockComponent = sharedComponents[componentName]
        .component as jest.Mock;

      await optimizer.preloadCriticalComponents();
      await optimizer.preloadCriticalComponents();

      expect(mockComponent).toHaveBeenCalledTimes(1);
    });
  });

  describe("Component Caching", () => {
    it("should cache loaded components", async () => {
      const componentName = "LoadingSkeleton";

      await optimizer.preloadCriticalComponents();

      const cachedComponent = optimizer.getCachedComponent(componentName);
      expect(cachedComponent).toBeDefined();
      expect(typeof cachedComponent).toBe("function");
    });

    it("should return null for non-cached components", () => {
      const cachedComponent = optimizer.getCachedComponent("NonExistent");
      expect(cachedComponent).toBeNull();
    });
  });

  describe("Route Bundle Analysis", () => {
    it("should generate route component bundles", () => {
      const bundle = optimizer.getRouteComponentBundle("dashboard");

      expect(bundle).toHaveProperty("critical");
      expect(bundle).toHaveProperty("high");
      expect(bundle).toHaveProperty("medium");
      expect(bundle).toHaveProperty("low");

      expect(bundle.critical).toContain("LoadingSkeleton");
      expect(bundle.critical).toContain("ErrorBoundary");
    });

    it("should categorize components by priority", () => {
      const bundle = optimizer.getRouteComponentBundle("research");

      // Check that components are in correct priority buckets
      bundle.critical.forEach((name) => {
        expect(sharedComponents[name].priority).toBe("critical");
      });

      bundle.high.forEach((name) => {
        expect(sharedComponents[name].priority).toBe("high");
      });
    });

    it("should handle unknown routes gracefully", () => {
      const bundle = optimizer.getRouteComponentBundle("unknown");

      expect(bundle.critical).toEqual([]);
      expect(bundle.high).toEqual([]);
      expect(bundle.medium).toEqual([]);
      expect(bundle.low).toEqual([]);
    });
  });

  describe("Component Sharing Analysis", () => {
    it("should identify most shared components", () => {
      const analysis = optimizer.analyzeComponentSharing();

      expect(analysis.mostShared).toBeDefined();
      expect(analysis.mostShared.length).toBeGreaterThan(0);

      // LoadingSkeleton should be highly shared
      const loadingSkeleton = analysis.mostShared.find(
        (comp) => comp.name === "LoadingSkeleton"
      );
      expect(loadingSkeleton).toBeDefined();
      expect(loadingSkeleton!.count).toBeGreaterThan(3);
    });

    it("should calculate route overlap correctly", () => {
      const analysis = optimizer.analyzeComponentSharing();

      expect(analysis.routeOverlap).toBeDefined();
      expect(analysis.routeOverlap.dashboard).toBeDefined();
      expect(analysis.routeOverlap.dashboard.length).toBeGreaterThan(0);
    });

    it("should provide optimization opportunities", () => {
      const analysis = optimizer.analyzeComponentSharing();

      expect(analysis.optimizationOpportunities).toBeDefined();
      expect(Array.isArray(analysis.optimizationOpportunities)).toBe(true);
    });
  });

  describe("Webpack Configuration Generation", () => {
    it("should generate webpack cache groups", () => {
      const config = optimizer.generateWebpackConfig();

      expect(config.cacheGroups).toBeDefined();
      expect(config.cacheGroups["shared-critical"]).toBeDefined();
      expect(config.cacheGroups["shared-high"]).toBeDefined();
      expect(config.cacheGroups["shared-common"]).toBeDefined();
    });

    it("should set appropriate priorities", () => {
      const config = optimizer.generateWebpackConfig();

      expect(config.cacheGroups["shared-critical"].priority).toBe(20);
      expect(config.cacheGroups["shared-high"].priority).toBe(15);
      expect(config.cacheGroups["shared-common"].priority).toBe(10);
    });

    it("should enforce critical component bundling", () => {
      const config = optimizer.generateWebpackConfig();

      expect(config.cacheGroups["shared-critical"].enforce).toBe(true);
    });
  });
});

describe("Component Usage Validation", () => {
  it("should have consistent component definitions", () => {
    // All components used in routes should be defined in sharedComponents
    const allUsedComponents = new Set<string>();
    Object.values(routeComponentUsage).forEach((components) => {
      components.forEach((comp) => allUsedComponents.add(comp));
    });

    allUsedComponents.forEach((component) => {
      expect(sharedComponents[component]).toBeDefined();
    });
  });

  it("should have realistic usage patterns", () => {
    // Critical components should be used in most routes
    const criticalComponents = Object.entries(sharedComponents)
      .filter(([_, config]) => config.priority === "critical")
      .map(([name]) => name);

    criticalComponents.forEach((component) => {
      const usageCount = Object.values(routeComponentUsage).filter(
        (components) => components.includes(component)
      ).length;

      expect(usageCount).toBeGreaterThan(3); // Used in more than 3 routes
    });
  });

  it("should have proper size classifications", () => {
    // Large components should not be used in too many routes
    const largeComponents = Object.entries(sharedComponents)
      .filter(([_, config]) => config.size === "large")
      .map(([name]) => name);

    largeComponents.forEach((component) => {
      const usageCount = Object.values(routeComponentUsage).filter(
        (components) => components.includes(component)
      ).length;

      expect(usageCount).toBeLessThanOrEqual(4); // Large components shouldn't be everywhere
    });
  });
});
