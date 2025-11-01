/**
 * Tests for Performance Budget Manager
 */

import {
  PerformanceBudgetManager,
  performanceBudgetManager,
  DEFAULT_BUDGET_CONFIG,
  validatePerformanceBudgets,
} from "../performance-budgets";

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(global, "localStorage", {
  value: localStorageMock,
  writable: true,
});

// Mock fetch for webhook notifications
global.fetch = jest.fn();

describe("PerformanceBudgetManager", () => {
  let budgetManager: PerformanceBudgetManager;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    budgetManager = new PerformanceBudgetManager();
  });

  describe("Initialization", () => {
    it("should initialize with default budget configuration", () => {
      const productionBudget = budgetManager.getBudget("production");

      expect(productionBudget).toEqual(
        DEFAULT_BUDGET_CONFIG.budgets.production
      );
      expect(productionBudget?.maxBundleSize).toBe(500000); // 500KB
      expect(productionBudget?.maxLCP).toBe(2500); // 2.5s
    });

    it("should support different environment budgets", () => {
      const devBudget = budgetManager.getBudget("development");
      const stagingBudget = budgetManager.getBudget("staging");
      const prodBudget = budgetManager.getBudget("production");

      expect(devBudget?.maxBundleSize).toBeGreaterThan(
        stagingBudget?.maxBundleSize!
      );
      expect(stagingBudget?.maxBundleSize).toBeGreaterThan(
        prodBudget?.maxBundleSize!
      );
    });
  });

  describe("Budget Validation", () => {
    const goodMetrics = {
      bundleSize: 400000, // 400KB - within 500KB budget
      loadTime: 2000, // 2s - within 3s budget
      lcp: 2000, // 2s - within 2.5s budget
      fid: 80, // 80ms - within 100ms budget
      cls: 0.08, // 0.08 - within 0.1 budget
      fcp: 1500, // 1.5s - within 1.8s budget
      ttfb: 600, // 600ms - within 800ms budget
    };

    const poorMetrics = {
      bundleSize: 800000, // 800KB - exceeds 500KB budget
      loadTime: 5000, // 5s - exceeds 3s budget
      lcp: 4000, // 4s - exceeds 2.5s budget
      fid: 200, // 200ms - exceeds 100ms budget
      cls: 0.3, // 0.3 - exceeds 0.1 budget
      fcp: 3000, // 3s - exceeds 1.8s budget
      ttfb: 1200, // 1.2s - exceeds 800ms budget
    };

    it("should pass validation for good metrics", async () => {
      const result = await budgetManager.validateBudget(
        goodMetrics,
        "production"
      );

      expect(result.passed).toBe(true);
      expect(result.violations).toHaveLength(0);
      expect(result.score).toBe(100);
    });

    it("should fail validation for poor metrics", async () => {
      const result = await budgetManager.validateBudget(
        poorMetrics,
        "production"
      );

      expect(result.passed).toBe(false);
      expect(result.violations.length).toBeGreaterThan(0);
      expect(result.score).toBeLessThan(100);

      // Check that all metrics have violations
      const violatedMetrics = result.violations.map((v) => v.metric);
      expect(violatedMetrics).toContain("bundleSize");
      expect(violatedMetrics).toContain("loadTime");
      expect(violatedMetrics).toContain("lcp");
      expect(violatedMetrics).toContain("fid");
      expect(violatedMetrics).toContain("cls");
    });

    it("should detect warning thresholds", async () => {
      const warningMetrics = {
        ...goodMetrics,
        bundleSize: 420000, // 84% of 500KB budget - should trigger warning
      };

      const result = await budgetManager.validateBudget(
        warningMetrics,
        "production"
      );

      expect(result.passed).toBe(true); // No critical violations
      expect(result.warnings.length).toBeGreaterThan(0);

      const bundleWarning = result.warnings.find(
        (w) => w.metric === "bundleSize"
      );
      expect(bundleWarning).toBeDefined();
      expect(bundleWarning?.severity).toBe("warning");
    });

    it("should handle different environments correctly", async () => {
      const metrics = {
        bundleSize: 600000, // 600KB
        loadTime: 3500,
        lcp: 2800,
        fid: 120,
        cls: 0.12,
        fcp: 2000,
        ttfb: 900,
      };

      const devResult = await budgetManager.validateBudget(
        metrics,
        "development"
      );
      const prodResult = await budgetManager.validateBudget(
        metrics,
        "production"
      );

      // Should pass in development but fail in production
      expect(devResult.passed).toBe(true);
      expect(prodResult.passed).toBe(false);
      expect(prodResult.violations.length).toBeGreaterThan(
        devResult.violations.length
      );
    });
  });

  describe("Alert Management", () => {
    it("should create alerts for budget violations", async () => {
      const poorMetrics = {
        bundleSize: 1000000, // 1MB - critical violation
        loadTime: 2000,
        lcp: 2000,
        fid: 80,
        cls: 0.08,
        fcp: 1500,
        ttfb: 600,
      };

      await budgetManager.validateBudget(poorMetrics, "production");

      const alerts = budgetManager.getUnresolvedAlerts();
      expect(alerts.length).toBeGreaterThan(0);

      const bundleAlert = alerts.find((a) =>
        a.violations.some((v) => v.metric === "bundleSize")
      );
      expect(bundleAlert).toBeDefined();
      expect(bundleAlert?.severity).toBe("critical");
    });

    it("should resolve alerts", () => {
      // Create a test alert first
      const testAlert = {
        id: "test-alert",
        timestamp: new Date(),
        environment: "production" as const,
        violations: [
          {
            metric: "bundleSize",
            actual: 1000000,
            budget: 500000,
            severity: "critical" as const,
          },
        ],
        severity: "critical" as const,
        resolved: false,
      };

      budgetManager["alerts"] = [testAlert];

      budgetManager.resolveAlert("test-alert");

      const alerts = budgetManager.getUnresolvedAlerts();
      expect(alerts).toHaveLength(0);
    });

    it("should clear old alerts", () => {
      const oldDate = new Date();
      oldDate.setDate(oldDate.getDate() - 40); // 40 days ago

      const oldAlert = {
        id: "old-alert",
        timestamp: oldDate,
        environment: "production" as const,
        violations: [],
        severity: "warning" as const,
        resolved: false,
      };

      budgetManager["alerts"] = [oldAlert];
      budgetManager.clearOldAlerts(30); // Clear alerts older than 30 days

      expect(budgetManager["alerts"]).toHaveLength(0);
    });
  });

  describe("CI/CD Integration", () => {
    it("should return correct exit code for passed validation", async () => {
      const goodMetrics = {
        bundleSize: 400000,
        loadTime: 2000,
        lcp: 2000,
        fid: 80,
        cls: 0.08,
        fcp: 1500,
        ttfb: 600,
      };

      const result = await budgetManager.validateBudget(
        goodMetrics,
        "production"
      );
      const exitCode = budgetManager.getCIExitCode(result);

      expect(exitCode).toBe(0);
    });

    it("should return error exit code for failed validation", async () => {
      const poorMetrics = {
        bundleSize: 1000000,
        loadTime: 5000,
        lcp: 4000,
        fid: 200,
        cls: 0.3,
        fcp: 3000,
        ttfb: 1200,
      };

      const result = await budgetManager.validateBudget(
        poorMetrics,
        "production"
      );
      const exitCode = budgetManager.getCIExitCode(result);

      expect(exitCode).toBe(1);
    });

    it("should generate CI report", async () => {
      const metrics = {
        bundleSize: 600000, // Exceeds budget
        loadTime: 2000,
        lcp: 2000,
        fid: 80,
        cls: 0.08,
        fcp: 1500,
        ttfb: 600,
      };

      const result = await budgetManager.validateBudget(metrics, "production");
      const report = budgetManager.generateCIReport(result, "production");

      expect(report).toContain("# Performance Budget Report");
      expect(report).toContain("Environment: production");
      expect(report).toContain("Status:");
      expect(report).toContain("bundleSize");
    });
  });

  describe("Notification System", () => {
    beforeEach(() => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({}),
      });
    });

    it("should send webhook notifications for violations", async () => {
      const config = {
        ...DEFAULT_BUDGET_CONFIG,
        notifications: {
          webhook: "https://example.com/webhook",
        },
      };

      const manager = new PerformanceBudgetManager(config);

      const poorMetrics = {
        bundleSize: 1000000,
        loadTime: 2000,
        lcp: 2000,
        fid: 80,
        cls: 0.08,
        fcp: 1500,
        ttfb: 600,
      };

      await manager.validateBudget(poorMetrics, "production");

      expect(global.fetch).toHaveBeenCalledWith(
        "https://example.com/webhook",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: expect.stringContaining("performance_budget_violation"),
        })
      );
    });
  });

  describe("Budget Configuration", () => {
    it("should update budget configuration", () => {
      const newBudgets = {
        production: {
          maxBundleSize: 400000, // Stricter than default
          maxInitialLoadTime: 2500,
          maxLCP: 2000,
          maxFID: 80,
          maxCLS: 0.08,
          maxFCP: 1600,
          maxTTFB: 700,
        },
      };

      budgetManager.updateBudgets(newBudgets);

      const updatedBudget = budgetManager.getBudget("production");
      expect(updatedBudget?.maxBundleSize).toBe(400000);
      expect(updatedBudget?.maxLCP).toBe(2000);
    });

    it("should return null for unknown environment", () => {
      const budget = budgetManager.getBudget("unknown" as any);
      expect(budget).toBeNull();
    });
  });

  describe("Utility Functions", () => {
    it("should validate performance budgets utility function", async () => {
      const metrics = {
        bundleSize: 400000,
        loadTime: 2000,
        lcp: 2000,
        fid: 80,
        cls: 0.08,
        fcp: 1500,
        ttfb: 600,
      };

      const { exitCode, report, result } = await validatePerformanceBudgets(
        metrics,
        "production"
      );

      expect(exitCode).toBe(0);
      expect(result.passed).toBe(true);
      expect(report).toContain("Performance Budget Report");
    });
  });

  describe("Error Handling", () => {
    it("should handle invalid environment gracefully", async () => {
      const metrics = {
        bundleSize: 400000,
        loadTime: 2000,
        lcp: 2000,
        fid: 80,
        cls: 0.08,
        fcp: 1500,
        ttfb: 600,
      };

      await expect(
        budgetManager.validateBudget(metrics, "invalid" as any)
      ).rejects.toThrow(
        "No budget configuration found for environment: invalid"
      );
    });

    it("should handle webhook notification failures gracefully", async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error("Network error"));

      const config = {
        ...DEFAULT_BUDGET_CONFIG,
        notifications: {
          webhook: "https://example.com/webhook",
        },
      };

      const manager = new PerformanceBudgetManager(config);

      const poorMetrics = {
        bundleSize: 1000000,
        loadTime: 2000,
        lcp: 2000,
        fid: 80,
        cls: 0.08,
        fcp: 1500,
        ttfb: 600,
      };

      // Should not throw despite webhook failure
      await expect(
        manager.validateBudget(poorMetrics, "production")
      ).resolves.toBeDefined();
    });
  });
});
