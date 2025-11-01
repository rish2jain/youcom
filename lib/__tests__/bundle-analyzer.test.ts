/**
 * Tests for bundle analyzer utilities
 */

import {
  BundleAnalyzer,
  bundleAnalyzer,
  PERFORMANCE_BUDGETS,
  ROUTE_BUNDLES,
  measureBundleLoad,
} from "../bundle-analyzer";

// Mock performance API
Object.defineProperty(window, "performance", {
  value: {
    now: jest.fn(() => Date.now()),
  },
});

// Mock gtag
Object.defineProperty(window, "gtag", {
  value: jest.fn(),
});

describe("Bundle Analyzer Configuration", () => {
  describe("PERFORMANCE_BUDGETS", () => {
    it("should have reasonable budget limits", () => {
      expect(PERFORMANCE_BUDGETS.initialBundle).toBe(500000); // 500KB
      expect(PERFORMANCE_BUDGETS.routeBundle).toBe(200000); // 200KB
      expect(PERFORMANCE_BUDGETS.vendorBundle).toBe(300000); // 300KB
      expect(PERFORMANCE_BUDGETS.totalSize).toBe(2000000); // 2MB
    });

    it("should have hierarchical budget structure", () => {
      expect(PERFORMANCE_BUDGETS.routeBundle).toBeLessThan(
        PERFORMANCE_BUDGETS.initialBundle
      );
      expect(PERFORMANCE_BUDGETS.vendorBundle).toBeGreaterThan(
        PERFORMANCE_BUDGETS.routeBundle
      );
      expect(PERFORMANCE_BUDGETS.totalSize).toBeGreaterThan(
        PERFORMANCE_BUDGETS.vendorBundle
      );
    });
  });

  describe("ROUTE_BUNDLES", () => {
    it("should define bundles for all major routes", () => {
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
          ROUTE_BUNDLES[route as keyof typeof ROUTE_BUNDLES]
        ).toBeDefined();
        expect(
          ROUTE_BUNDLES[route as keyof typeof ROUTE_BUNDLES].length
        ).toBeGreaterThan(0);
      });
    });

    it("should include common bundle in all routes", () => {
      Object.values(ROUTE_BUNDLES).forEach((bundles) => {
        expect(bundles).toContain("common");
      });
    });

    it("should have route-specific bundles", () => {
      expect(ROUTE_BUNDLES.research).toContain("company-research");
      expect(ROUTE_BUNDLES.analytics).toContain("charts");
      expect(ROUTE_BUNDLES.monitoring).toContain("watchlist");
    });
  });
});

describe("BundleAnalyzer", () => {
  let analyzer: BundleAnalyzer;

  beforeEach(() => {
    analyzer = new (BundleAnalyzer as any)();
  });

  describe("Bundle Analysis", () => {
    it("should analyze bundles and return comprehensive data", async () => {
      const analysis = await analyzer.analyzeBundles();

      expect(analysis).toHaveProperty("totalSize");
      expect(analysis).toHaveProperty("routeBundles");
      expect(analysis).toHaveProperty("vendorBundles");
      expect(analysis).toHaveProperty("commonBundles");
      expect(analysis).toHaveProperty("timestamp");

      expect(analysis.totalSize).toBeGreaterThan(0);
      expect(analysis.routeBundles.length).toBeGreaterThan(0);
      expect(analysis.vendorBundles.length).toBeGreaterThan(0);
      expect(analysis.commonBundles.length).toBeGreaterThan(0);
    });

    it("should include all route bundles in analysis", async () => {
      const analysis = await analyzer.analyzeBundles();
      const routeNames = analysis.routeBundles.map((bundle) => bundle.route);

      Object.keys(ROUTE_BUNDLES).forEach((route) => {
        expect(routeNames).toContain(route);
      });
    });

    it("should calculate total size correctly", async () => {
      const analysis = await analyzer.analyzeBundles();
      const calculatedTotal = [
        ...analysis.routeBundles,
        ...analysis.vendorBundles,
        ...analysis.commonBundles,
      ].reduce((sum, bundle) => sum + bundle.size, 0);

      expect(analysis.totalSize).toBe(calculatedTotal);
    });
  });

  describe("Performance Budget Validation", () => {
    it("should validate bundles against performance budgets", async () => {
      const analysis = await analyzer.analyzeBundles();
      const budgetCheck = analyzer.checkPerformanceBudgets(analysis);

      expect(budgetCheck).toHaveProperty("passed");
      expect(budgetCheck).toHaveProperty("violations");
      expect(Array.isArray(budgetCheck.violations)).toBe(true);
    });

    it("should detect total size violations", async () => {
      const analysis = await analyzer.analyzeBundles();
      // Force a violation
      analysis.totalSize = PERFORMANCE_BUDGETS.totalSize + 1000000;

      const budgetCheck = analyzer.checkPerformanceBudgets(analysis);

      expect(budgetCheck.passed).toBe(false);
      expect(
        budgetCheck.violations.some((v) => v.includes("Total bundle size"))
      ).toBe(true);
    });

    it("should detect route bundle violations", async () => {
      const analysis = await analyzer.analyzeBundles();
      // Force a route bundle violation
      if (analysis.routeBundles.length > 0) {
        analysis.routeBundles[0].size =
          PERFORMANCE_BUDGETS.routeBundle + 100000;
      }

      const budgetCheck = analyzer.checkPerformanceBudgets(analysis);

      if (analysis.routeBundles.length > 0) {
        expect(budgetCheck.passed).toBe(false);
        expect(
          budgetCheck.violations.some((v) => v.includes("Route bundle"))
        ).toBe(true);
      }
    });

    it("should detect vendor bundle violations", async () => {
      const analysis = await analyzer.analyzeBundles();
      // Force a vendor bundle violation
      if (analysis.vendorBundles.length > 0) {
        analysis.vendorBundles[0].size =
          PERFORMANCE_BUDGETS.vendorBundle + 100000;
      }

      const budgetCheck = analyzer.checkPerformanceBudgets(analysis);

      if (analysis.vendorBundles.length > 0) {
        expect(budgetCheck.passed).toBe(false);
        expect(
          budgetCheck.violations.some((v) => v.includes("Vendor bundle"))
        ).toBe(true);
      }
    });

    it("should pass when all budgets are met", async () => {
      const analysis = await analyzer.analyzeBundles();

      // Ensure all sizes are within budget
      analysis.totalSize = PERFORMANCE_BUDGETS.totalSize - 100000;
      analysis.routeBundles.forEach((bundle) => {
        bundle.size = PERFORMANCE_BUDGETS.routeBundle - 10000;
      });
      analysis.vendorBundles.forEach((bundle) => {
        bundle.size = PERFORMANCE_BUDGETS.vendorBundle - 10000;
      });

      const budgetCheck = analyzer.checkPerformanceBudgets(analysis);

      expect(budgetCheck.passed).toBe(true);
      expect(budgetCheck.violations).toEqual([]);
    });
  });

  describe("Optimization Recommendations", () => {
    it("should generate recommendations based on analysis", async () => {
      const analysis = await analyzer.analyzeBundles();
      const recommendations = analyzer.generateRecommendations(analysis);

      expect(Array.isArray(recommendations)).toBe(true);
    });

    it("should recommend route splitting for oversized routes", async () => {
      const analysis = await analyzer.analyzeBundles();

      // Force oversized route
      if (analysis.routeBundles.length > 0) {
        analysis.routeBundles[0].size = PERFORMANCE_BUDGETS.routeBundle * 0.9;
        analysis.routeBundles[0].route = "analytics";
      }

      const recommendations = analyzer.generateRecommendations(analysis);

      expect(
        recommendations.some((r) => r.includes("Consider further splitting"))
      ).toBe(true);
    });

    it("should recommend vendor bundle optimization", async () => {
      const analysis = await analyzer.analyzeBundles();

      // Force large vendor bundle
      if (analysis.vendorBundles.length > 0) {
        analysis.vendorBundles[0].size = PERFORMANCE_BUDGETS.vendorBundle * 0.9;
      }

      const recommendations = analyzer.generateRecommendations(analysis);

      expect(recommendations.some((r) => r.includes("vendor bundles"))).toBe(
        true
      );
    });

    it("should recommend general optimizations for large total size", async () => {
      const analysis = await analyzer.analyzeBundles();

      // Force large total size
      analysis.totalSize = PERFORMANCE_BUDGETS.totalSize * 0.9;

      const recommendations = analyzer.generateRecommendations(analysis);

      expect(recommendations.some((r) => r.includes("tree shaking"))).toBe(
        true
      );
    });
  });

  describe("Bundle Load Tracking", () => {
    it("should track bundle loading performance", () => {
      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      analyzer.trackBundleLoad("dashboard", 150);

      expect(consoleSpy).toHaveBeenCalledWith(
        "Bundle dashboard loaded in 150ms"
      );

      consoleSpy.mockRestore();
    });

    it("should send analytics events when gtag is available", () => {
      const gtagSpy = window.gtag as jest.Mock;

      analyzer.trackBundleLoad("research", 200);

      expect(gtagSpy).toHaveBeenCalledWith("event", "bundle_load", {
        event_category: "performance",
        event_label: "research",
        value: 200,
      });
    });

    it("should handle missing performance API gracefully", () => {
      const originalPerformance = window.performance;
      delete (window as any).performance;

      expect(() => {
        analyzer.trackBundleLoad("analytics", 100);
      }).not.toThrow();

      window.performance = originalPerformance;
    });
  });

  describe("Size Formatting", () => {
    it("should format byte sizes correctly", () => {
      const formatSize = (analyzer as any).formatSize;

      expect(formatSize(1024)).toBe("1.0KB");
      expect(formatSize(1048576)).toBe("1.0MB");
      expect(formatSize(1073741824)).toBe("1.0GB");
      expect(formatSize(500)).toBe("500.0B");
    });

    it("should handle edge cases in size formatting", () => {
      const formatSize = (analyzer as any).formatSize;

      expect(formatSize(0)).toBe("0.0B");
      expect(formatSize(1023)).toBe("1023.0B");
      expect(formatSize(1025)).toBe("1.0KB");
    });
  });
});

describe("Bundle Load Measurement", () => {
  beforeEach(() => {
    (window.performance.now as jest.Mock).mockClear();
  });

  it("should measure bundle load time", () => {
    (window.performance.now as jest.Mock)
      .mockReturnValueOnce(1000) // Start time
      .mockReturnValueOnce(1150); // End time

    const endMeasurement = measureBundleLoad("dashboard");
    const loadTime = endMeasurement();

    expect(loadTime).toBe(150);
  });

  it("should track bundle load with analyzer", () => {
    const trackSpy = jest.spyOn(bundleAnalyzer, "trackBundleLoad");

    (window.performance.now as jest.Mock)
      .mockReturnValueOnce(2000) // Start time
      .mockReturnValueOnce(2250); // End time

    const endMeasurement = measureBundleLoad("research");
    endMeasurement();

    expect(trackSpy).toHaveBeenCalledWith("research", 250);
  });
});

describe("Singleton Pattern", () => {
  it("should return the same instance", () => {
    const instance1 = BundleAnalyzer.getInstance();
    const instance2 = BundleAnalyzer.getInstance();

    expect(instance1).toBe(instance2);
  });

  it("should use the exported singleton", () => {
    const instance = BundleAnalyzer.getInstance();
    expect(bundleAnalyzer).toBe(instance);
  });
});
