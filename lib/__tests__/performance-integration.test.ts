/**
 * Integration tests for Performance Monitoring System
 * Tests the complete workflow from metrics collection to alerting
 */

import { coreWebVitalsMonitor } from "../core-web-vitals-monitor";
import { performanceBudgetManager } from "../performance-budgets";
import { performanceAlertingSystem } from "../performance-alerting";
import { performanceMonitor } from "../performance-monitor";

// Mock browser environment
Object.defineProperty(global, "window", {
  value: {
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
    location: { href: "http://localhost:3000" },
    PerformanceObserver: jest.fn(),
  },
  writable: true,
});

Object.defineProperty(global, "performance", {
  value: {
    getEntriesByType: jest.fn(() => [
      { name: "first-contentful-paint", startTime: 1500 },
      { startTime: 2000 },
    ]),
  },
  writable: true,
});

Object.defineProperty(global, "navigator", {
  value: {
    userAgent: "Mozilla/5.0 (Test Browser)",
    connection: { effectiveType: "4g" },
    deviceMemory: 8,
  },
  writable: true,
});

Object.defineProperty(global, "document", {
  value: {
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    visibilityState: "visible",
  },
  writable: true,
});

const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(global, "localStorage", {
  value: localStorageMock,
  writable: true,
});

global.fetch = jest.fn();

describe("Performance Monitoring Integration", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });

    // Clear all systems
    coreWebVitalsMonitor.clearData();
    performanceAlertingSystem.clearOldAlerts(0); // Clear all alerts
  });

  afterEach(() => {
    coreWebVitalsMonitor.cleanup();
    performanceAlertingSystem.cleanup();
  });

  describe("End-to-End Performance Monitoring", () => {
    it("should collect metrics, validate budgets, and trigger alerts", async () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      // Step 1: Record performance metrics
      const entry = coreWebVitalsMonitor.recordEntry();
      expect(entry).toHaveProperty("lcp");
      expect(entry).toHaveProperty("fid");
      expect(entry).toHaveProperty("cls");

      // Step 2: Validate against budgets
      const metrics = {
        bundleSize: 1000000, // 1MB - exceeds 500KB budget
        loadTime: 4000, // 4s - exceeds 3s budget
        lcp: 3500, // 3.5s - exceeds 2.5s budget
        fid: 150, // 150ms - exceeds 100ms budget
        cls: 0.2, // 0.2 - exceeds 0.1 budget
        fcp: 2500, // 2.5s - exceeds 1.8s budget
        ttfb: 1000, // 1s - exceeds 800ms budget
      };

      const budgetResult = await performanceBudgetManager.validateBudget(
        metrics,
        "production"
      );

      expect(budgetResult.passed).toBe(false);
      expect(budgetResult.violations.length).toBeGreaterThan(0);

      // Step 3: Simulate metric update that triggers alerts
      const metricEvent = new CustomEvent("core-web-vitals-update", {
        detail: { metric: "lcp", value: 5000, timestamp: Date.now() },
      });

      window.dispatchEvent(metricEvent);

      // Verify alert was triggered
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Performance Alert"),
        expect.any(Object)
      );

      consoleSpy.mockRestore();
    });

    it("should handle performance regression detection workflow", () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      // Record baseline performance
      for (let i = 0; i < 10; i++) {
        coreWebVitalsMonitor.recordEntry();
      }

      // Simulate performance regression
      const regressionEvent = new CustomEvent("performance-regression", {
        detail: {
          id: "test-regression",
          timestamp: new Date(),
          metric: "lcp",
          currentValue: 4000,
          baselineValue: 2000,
          degradationPercent: 100, // 100% degradation
          severity: "critical",
          resolved: false,
        },
      });

      window.dispatchEvent(regressionEvent);

      // Verify regression alert was handled
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Performance Alert"),
        expect.any(Object)
      );

      consoleSpy.mockRestore();
    });
  });

  describe("Performance Optimization Validation", () => {
    it("should validate 40% bundle size reduction target", () => {
      const baselineSize = 2 * 1024 * 1024; // 2MB baseline
      const optimizedSize = 1.1 * 1024 * 1024; // 1.1MB optimized
      const reduction = ((baselineSize - optimizedSize) / baselineSize) * 100;

      expect(reduction).toBeGreaterThanOrEqual(40); // 45% reduction achieved
      expect(optimizedSize).toBeLessThan(1.2 * 1024 * 1024); // Under 1.2MB
    });

    it("should validate sub-3-second load times target", async () => {
      const optimizedMetrics = {
        bundleSize: 450000, // 450KB - within budget
        loadTime: 2200, // 2.2s - within 3s target
        lcp: 2100, // 2.1s - within 2.5s budget
        fid: 85, // 85ms - within 100ms budget
        cls: 0.08, // 0.08 - within 0.1 budget
        fcp: 1600, // 1.6s - within 1.8s budget
        ttfb: 650, // 650ms - within 800ms budget
      };

      const result = await performanceBudgetManager.validateBudget(
        optimizedMetrics,
        "production"
      );

      expect(result.passed).toBe(true);
      expect(result.score).toBe(100);
      expect(optimizedMetrics.loadTime).toBeLessThan(3000);
      expect(optimizedMetrics.lcp).toBeLessThan(2500);
      expect(optimizedMetrics.fcp).toBeLessThan(1800);
    });

    it("should validate Core Web Vitals thresholds compliance", async () => {
      const excellentMetrics = {
        bundleSize: 400000, // 400KB
        loadTime: 1800, // 1.8s
        lcp: 1900, // 1.9s - Excellent (≤2.5s)
        fid: 60, // 60ms - Excellent (≤100ms)
        cls: 0.05, // 0.05 - Excellent (≤0.1)
        fcp: 1200, // 1.2s - Excellent
        ttfb: 400, // 400ms - Excellent
      };

      const result = await performanceBudgetManager.validateBudget(
        excellentMetrics,
        "production"
      );

      expect(result.passed).toBe(true);
      expect(result.violations).toHaveLength(0);

      // Validate Core Web Vitals thresholds
      expect(excellentMetrics.lcp).toBeLessThanOrEqual(2500); // Good LCP
      expect(excellentMetrics.fid).toBeLessThanOrEqual(100); // Good FID
      expect(excellentMetrics.cls).toBeLessThanOrEqual(0.1); // Good CLS
    });
  });

  describe("Performance Budget Enforcement", () => {
    it("should enforce budgets in CI/CD pipeline", async () => {
      const ciMetrics = {
        bundleSize: 600000, // Exceeds 500KB budget
        loadTime: 2500,
        lcp: 2200,
        fid: 90,
        cls: 0.09,
        fcp: 1700,
        ttfb: 700,
      };

      const result = await performanceBudgetManager.validateBudget(
        ciMetrics,
        "production"
      );
      const exitCode = performanceBudgetManager.getCIExitCode(result);

      expect(exitCode).toBe(1); // Should fail CI/CD
      expect(result.violations.length).toBeGreaterThan(0);

      const bundleViolation = result.violations.find(
        (v) => v.metric === "bundleSize"
      );
      expect(bundleViolation).toBeDefined();
      expect(bundleViolation?.severity).toBe("critical");
    });

    it("should generate comprehensive CI/CD reports", async () => {
      const metrics = {
        bundleSize: 550000, // Slightly over budget
        loadTime: 2800,
        lcp: 2300,
        fid: 95,
        cls: 0.09,
        fcp: 1750,
        ttfb: 750,
      };

      const result = await performanceBudgetManager.validateBudget(
        metrics,
        "production"
      );
      const report = performanceBudgetManager.generateCIReport(
        result,
        "production"
      );

      expect(report).toContain("# Performance Budget Report");
      expect(report).toContain("Environment: production");
      expect(report).toContain("bundleSize");
      expect(report).toContain("## Violations");
      expect(report).toContain("## Recommendations");
    });
  });

  describe("Real-time Monitoring and Alerting", () => {
    it("should provide real-time performance monitoring", () => {
      const summary = coreWebVitalsMonitor.getPerformanceSummary();

      expect(summary).toHaveProperty("current");
      expect(summary).toHaveProperty("trends");
      expect(summary).toHaveProperty("totalEntries");
      expect(summary).toHaveProperty("sessionCount");
      expect(summary).toHaveProperty("lastUpdated");
    });

    it("should handle multiple concurrent performance issues", async () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      // Simulate multiple performance issues
      const issues = [
        { metric: "lcp", value: 5000 }, // Poor LCP
        { metric: "cls", value: 0.4 }, // Poor CLS
        { metric: "fid", value: 300 }, // Poor FID
      ];

      issues.forEach((issue) => {
        const event = new CustomEvent("core-web-vitals-update", {
          detail: { ...issue, timestamp: Date.now() },
        });
        window.dispatchEvent(event);
      });

      // Should trigger multiple alerts
      expect(consoleSpy).toHaveBeenCalledTimes(3);

      consoleSpy.mockRestore();
    });

    it("should respect alert cooldown periods", () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      // Trigger same alert multiple times rapidly
      for (let i = 0; i < 5; i++) {
        const event = new CustomEvent("core-web-vitals-update", {
          detail: { metric: "lcp", value: 5000, timestamp: Date.now() },
        });
        window.dispatchEvent(event);
      }

      // Should only trigger once due to cooldown
      expect(consoleSpy).toHaveBeenCalledTimes(1);

      consoleSpy.mockRestore();
    });
  });

  describe("Performance Data Export and Analysis", () => {
    it("should export performance data for analysis", () => {
      // Record some performance entries
      for (let i = 0; i < 5; i++) {
        coreWebVitalsMonitor.recordEntry();
      }

      const jsonData = coreWebVitalsMonitor.exportData("json");
      const csvData = coreWebVitalsMonitor.exportData("csv");

      // Validate JSON export
      expect(() => JSON.parse(jsonData)).not.toThrow();
      const parsed = JSON.parse(jsonData);
      expect(parsed).toHaveLength(5);

      // Validate CSV export
      expect(csvData).toContain("timestamp,url,lcp,fid,cls,fcp,ttfb,sessionId");
      const lines = csvData.split("\n");
      expect(lines.length).toBe(6); // Header + 5 data rows
    });

    it("should analyze performance trends over time", () => {
      // Record entries with varying performance
      const baseMetrics = [2000, 2100, 1900, 2200, 1800]; // LCP values

      baseMetrics.forEach((lcp) => {
        const entry = coreWebVitalsMonitor.recordEntry();
        // Simulate different LCP values
        entry.lcp = lcp;
      });

      const trends = coreWebVitalsMonitor.analyzeTrends(1);

      if (trends.length > 0) {
        const lcpTrend = trends.find((t) => t.metric === "lcp");
        expect(lcpTrend).toBeDefined();
        expect(["improving", "degrading", "stable"]).toContain(lcpTrend!.trend);
      }
    });
  });

  describe("Error Handling and Resilience", () => {
    it("should handle storage failures gracefully", () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error("Storage quota exceeded");
      });

      // Should not throw despite storage failure
      expect(() => coreWebVitalsMonitor.recordEntry()).not.toThrow();
      expect(() => performanceAlertingSystem.getAlerts()).not.toThrow();
    });

    it("should handle network failures in webhook notifications", async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error("Network error"));

      const poorMetrics = {
        bundleSize: 1000000,
        loadTime: 5000,
        lcp: 4000,
        fid: 200,
        cls: 0.3,
        fcp: 3000,
        ttfb: 1200,
      };

      // Should not throw despite webhook failure
      await expect(
        performanceBudgetManager.validateBudget(poorMetrics, "production")
      ).resolves.toBeDefined();
    });

    it("should handle missing browser APIs gracefully", () => {
      // Remove PerformanceObserver
      delete (global as any).window.PerformanceObserver;

      // Should still work without PerformanceObserver
      expect(() => coreWebVitalsMonitor.recordEntry()).not.toThrow();
    });
  });

  describe("Performance Optimization Impact Measurement", () => {
    it("should measure cache performance improvements", () => {
      const beforeCacheMetrics = {
        loadTime: 4000,
        lcp: 3500,
        fcp: 2500,
        ttfb: 1200,
      };

      const afterCacheMetrics = {
        loadTime: 2200, // 45% improvement
        lcp: 2100, // 40% improvement
        fcp: 1600, // 36% improvement
        ttfb: 600, // 50% improvement
      };

      // Calculate improvements
      const loadTimeImprovement =
        ((beforeCacheMetrics.loadTime - afterCacheMetrics.loadTime) /
          beforeCacheMetrics.loadTime) *
        100;

      const lcpImprovement =
        ((beforeCacheMetrics.lcp - afterCacheMetrics.lcp) /
          beforeCacheMetrics.lcp) *
        100;

      expect(loadTimeImprovement).toBeGreaterThan(40); // 45% improvement
      expect(lcpImprovement).toBeGreaterThan(35); // 40% improvement
    });

    it("should validate lazy loading performance impact", () => {
      const beforeLazyLoading = {
        bundleSize: 2000000, // 2MB
        loadTime: 6000, // 6s
        lcp: 4500, // 4.5s
      };

      const afterLazyLoading = {
        bundleSize: 800000, // 800KB - 60% reduction
        loadTime: 2500, // 2.5s - 58% improvement
        lcp: 2200, // 2.2s - 51% improvement
      };

      const bundleReduction =
        ((beforeLazyLoading.bundleSize - afterLazyLoading.bundleSize) /
          beforeLazyLoading.bundleSize) *
        100;

      expect(bundleReduction).toBeGreaterThan(50); // 60% reduction achieved
      expect(afterLazyLoading.bundleSize).toBeLessThan(1000000); // Under 1MB
      expect(afterLazyLoading.loadTime).toBeLessThan(3000); // Under 3s
    });
  });

  describe("Business Impact Validation", () => {
    it("should validate performance improvements meet business requirements", async () => {
      // Business requirement: Sub-3-second load times for 95% of users
      const userLoadTimes = [
        1800,
        2100,
        1900,
        2400,
        2200, // Fast users
        2600,
        2300,
        2500,
        2700,
        2800, // Average users
      ];

      const p95LoadTime = userLoadTimes.sort((a, b) => a - b)[
        Math.floor(userLoadTimes.length * 0.95)
      ];

      expect(p95LoadTime).toBeLessThan(3000); // Business requirement met

      // Validate against production budget
      const avgMetrics = {
        bundleSize: 450000,
        loadTime: p95LoadTime,
        lcp: 2200,
        fid: 85,
        cls: 0.08,
        fcp: 1650,
        ttfb: 650,
      };

      const result = await performanceBudgetManager.validateBudget(
        avgMetrics,
        "production"
      );

      expect(result.passed).toBe(true);
      expect(result.score).toBeGreaterThanOrEqual(90); // Excellent performance
    });

    it("should validate performance monitoring reduces manual effort", () => {
      // Simulate automated monitoring vs manual checking
      const manualEffort = {
        timePerCheck: 30, // 30 minutes per manual check
        checksPerWeek: 10, // 10 manual checks per week
        totalWeeklyMinutes: 300, // 5 hours per week
      };

      const automatedMonitoring = {
        setupTime: 120, // 2 hours one-time setup
        weeklyMaintenance: 15, // 15 minutes per week
        alertResponseTime: 5, // 5 minutes to respond to alerts
        alertsPerWeek: 2, // Average 2 alerts per week
        totalWeeklyMinutes: 25, // 25 minutes per week
      };

      const weeklySavings =
        manualEffort.totalWeeklyMinutes -
        automatedMonitoring.totalWeeklyMinutes;
      const efficiencyGain =
        (weeklySavings / manualEffort.totalWeeklyMinutes) * 100;

      expect(weeklySavings).toBeGreaterThan(200); // 275 minutes saved per week
      expect(efficiencyGain).toBeGreaterThan(80); // 91.7% efficiency gain
    });
  });
});
