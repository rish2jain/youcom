/**
 * Performance budget configuration and validation
 * Implements performance budget enforcement and CI/CD integration
 */

import {
  PerformanceBudget,
  BudgetValidationResult,
} from "./performance-monitor";

export interface BudgetConfig {
  budgets: Record<string, PerformanceBudget>;
  alertThresholds: {
    warning: number; // percentage of budget used
    critical: number; // percentage of budget used
  };
  notifications: {
    email?: string[];
    slack?: string;
    webhook?: string;
  };
}

export interface BudgetViolationAlert {
  id: string;
  timestamp: Date;
  environment: "development" | "staging" | "production";
  violations: BudgetValidationResult["violations"];
  severity: "warning" | "critical";
  resolved: boolean;
}

// Default budget configurations for different environments
export const DEFAULT_BUDGET_CONFIG: BudgetConfig = {
  budgets: {
    development: {
      maxBundleSize: 1000000, // 1MB - more lenient for development
      maxInitialLoadTime: 5000, // 5 seconds
      maxLCP: 4000, // 4 seconds
      maxFID: 300, // 300ms
      maxCLS: 0.25, // 0.25 score
      maxFCP: 3000, // 3 seconds
      maxTTFB: 1500, // 1.5 seconds
    },
    staging: {
      maxBundleSize: 750000, // 750KB
      maxInitialLoadTime: 4000, // 4 seconds
      maxLCP: 3000, // 3 seconds
      maxFID: 200, // 200ms
      maxCLS: 0.15, // 0.15 score
      maxFCP: 2500, // 2.5 seconds
      maxTTFB: 1000, // 1 second
    },
    production: {
      maxBundleSize: 500000, // 500KB - strict production limits
      maxInitialLoadTime: 3000, // 3 seconds
      maxLCP: 2500, // 2.5 seconds
      maxFID: 100, // 100ms
      maxCLS: 0.1, // 0.1 score
      maxFCP: 1800, // 1.8 seconds
      maxTTFB: 800, // 800ms
    },
  },
  alertThresholds: {
    warning: 80, // 80% of budget
    critical: 100, // 100% of budget (violation)
  },
  notifications: {
    // Configure based on environment
  },
};

export class PerformanceBudgetManager {
  private config: BudgetConfig;
  private alerts: BudgetViolationAlert[] = [];
  private readonly STORAGE_KEY = "performance-budget-alerts";

  constructor(config: BudgetConfig = DEFAULT_BUDGET_CONFIG) {
    this.config = config;
    this.loadAlerts();
  }

  /**
   * Validate performance against budget for specific environment
   */
  async validateBudget(
    metrics: {
      bundleSize: number;
      loadTime: number;
      lcp: number;
      fid: number;
      cls: number;
      fcp: number;
      ttfb: number;
    },
    environment: keyof BudgetConfig["budgets"] = "production"
  ): Promise<BudgetValidationResult> {
    const budget = this.config.budgets[environment];
    if (!budget) {
      throw new Error(
        `No budget configuration found for environment: ${environment}`
      );
    }

    const violations: BudgetValidationResult["violations"] = [];

    // Check each metric against budget
    const checks = [
      {
        metric: "bundleSize",
        actual: metrics.bundleSize,
        budget: budget.maxBundleSize,
      },
      {
        metric: "loadTime",
        actual: metrics.loadTime,
        budget: budget.maxInitialLoadTime,
      },
      { metric: "lcp", actual: metrics.lcp, budget: budget.maxLCP },
      { metric: "fid", actual: metrics.fid, budget: budget.maxFID },
      { metric: "cls", actual: metrics.cls, budget: budget.maxCLS },
      { metric: "fcp", actual: metrics.fcp, budget: budget.maxFCP },
      { metric: "ttfb", actual: metrics.ttfb, budget: budget.maxTTFB },
    ];

    checks.forEach((check) => {
      const percentage = (check.actual / check.budget) * 100;

      if (percentage >= this.config.alertThresholds.critical) {
        violations.push({
          metric: check.metric,
          actual: check.actual,
          budget: check.budget,
          severity: "critical",
        });
      } else if (percentage >= this.config.alertThresholds.warning) {
        violations.push({
          metric: check.metric,
          actual: check.actual,
          budget: check.budget,
          severity: "warning",
        });
      }
    });

    const totalChecks = checks.length;
    const passedChecks =
      totalChecks - violations.filter((v) => v.severity === "critical").length;
    const score = Math.round((passedChecks / totalChecks) * 100);

    const result: BudgetValidationResult = {
      passed: violations.filter((v) => v.severity === "critical").length === 0,
      violations,
      score,
    };

    // Create alert if there are violations
    if (violations.length > 0) {
      await this.createAlert(violations, environment as any);
    }

    return result;
  }

  /**
   * Create performance budget violation alert
   */
  private async createAlert(
    violations: BudgetValidationResult["violations"],
    environment: "development" | "staging" | "production"
  ): Promise<void> {
    const hasCritical = violations.some((v) => v.severity === "critical");

    const alert: BudgetViolationAlert = {
      id: `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      environment,
      violations,
      severity: hasCritical ? "critical" : "warning",
      resolved: false,
    };

    this.alerts.push(alert);
    this.saveAlerts();

    // Send notifications
    await this.sendNotifications(alert);
  }

  /**
   * Send notifications for budget violations
   */
  private async sendNotifications(alert: BudgetViolationAlert): Promise<void> {
    const message = this.formatAlertMessage(alert);

    // Console logging (always available)
    if (alert.severity === "critical") {
      console.error("🚨 Performance Budget Violation (Critical):", message);
    } else {
      console.warn("⚠️ Performance Budget Warning:", message);
    }

    // Webhook notification
    if (this.config.notifications.webhook) {
      try {
        await fetch(this.config.notifications.webhook, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            type: "performance_budget_violation",
            alert,
            message,
          }),
        });
      } catch (error) {
        console.error("Failed to send webhook notification:", error);
      }
    }

    // In a real implementation, you would also send email/Slack notifications
    // This would require server-side integration
  }

  /**
   * Format alert message for notifications
   */
  private formatAlertMessage(alert: BudgetViolationAlert): string {
    const violationSummary = alert.violations
      .map(
        (v) =>
          `${v.metric}: ${this.formatMetricValue(
            v.metric,
            v.actual
          )} (budget: ${this.formatMetricValue(v.metric, v.budget)})`
      )
      .join(", ");

    return `Performance budget ${alert.severity} in ${alert.environment}: ${violationSummary}`;
  }

  /**
   * Format metric values for display
   */
  private formatMetricValue(metric: string, value: number): string {
    switch (metric) {
      case "bundleSize":
        return `${Math.round(value / 1024)}KB`;
      case "loadTime":
      case "lcp":
      case "fid":
      case "fcp":
      case "ttfb":
        return `${Math.round(value)}ms`;
      case "cls":
        return value.toFixed(3);
      default:
        return value.toString();
    }
  }

  /**
   * Get CI/CD exit code based on validation result
   */
  getCIExitCode(result: BudgetValidationResult): number {
    const criticalViolations = result.violations.filter(
      (v) => v.severity === "critical"
    );
    return criticalViolations.length > 0 ? 1 : 0; // Exit code 1 for failures
  }

  /**
   * Generate CI/CD report
   */
  generateCIReport(
    result: BudgetValidationResult,
    environment: string
  ): string {
    const lines = [
      "# Performance Budget Report",
      `Environment: ${environment}`,
      `Score: ${result.score}/100`,
      `Status: ${result.passed ? "✅ PASSED" : "❌ FAILED"}`,
      "",
    ];

    if (result.violations.length > 0) {
      lines.push("## Violations");
      result.violations.forEach((violation) => {
        const icon = violation.severity === "critical" ? "🚨" : "⚠️";
        lines.push(
          `${icon} **${violation.metric}**: ${this.formatMetricValue(
            violation.metric,
            violation.actual
          )} ` +
            `(budget: ${this.formatMetricValue(
              violation.metric,
              violation.budget
            )})`
        );
      });
      lines.push("");
    }

    lines.push("## Recommendations");
    if (result.violations.length === 0) {
      lines.push("✅ All performance budgets are within limits!");
    } else {
      lines.push("Consider the following optimizations:");
      result.violations.forEach((violation) => {
        lines.push(
          `- Optimize ${violation.metric} to meet budget requirements`
        );
      });
    }

    return lines.join("\n");
  }

  /**
   * Update budget configuration
   */
  updateBudgets(budgets: Partial<BudgetConfig["budgets"]>): void {
    Object.entries(budgets).forEach(([key, value]) => {
      if (value) {
        this.config.budgets[key] = value;
      }
    });
  }

  /**
   * Get current budget for environment
   */
  getBudget(
    environment: keyof BudgetConfig["budgets"]
  ): PerformanceBudget | null {
    return this.config.budgets[environment] || null;
  }

  /**
   * Get all unresolved alerts
   */
  getUnresolvedAlerts(): BudgetViolationAlert[] {
    return this.alerts.filter((alert) => !alert.resolved);
  }

  /**
   * Resolve an alert
   */
  resolveAlert(alertId: string): void {
    const alert = this.alerts.find((a) => a.id === alertId);
    if (alert) {
      alert.resolved = true;
      this.saveAlerts();
    }
  }

  /**
   * Clear old alerts (older than specified days)
   */
  clearOldAlerts(days: number = 30): void {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);

    this.alerts = this.alerts.filter((alert) => alert.timestamp >= cutoff);
    this.saveAlerts();
  }

  /**
   * Load alerts from storage
   */
  private loadAlerts(): void {
    if (typeof window === "undefined") return;

    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        this.alerts = parsed.map((alert: any) => ({
          ...alert,
          timestamp: new Date(alert.timestamp),
        }));
      }
    } catch (error) {
      console.warn("Failed to load performance alerts:", error);
    }
  }

  /**
   * Save alerts to storage
   */
  private saveAlerts(): void {
    if (typeof window === "undefined") return;

    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.alerts));
    } catch (error) {
      console.warn("Failed to save performance alerts:", error);
    }
  }
}

// Global budget manager instance
export const performanceBudgetManager = new PerformanceBudgetManager();

// Utility function for CI/CD integration
export async function validatePerformanceBudgets(
  metrics: Parameters<PerformanceBudgetManager["validateBudget"]>[0],
  environment: string = "production"
): Promise<{
  exitCode: number;
  report: string;
  result: BudgetValidationResult;
}> {
  const result = await performanceBudgetManager.validateBudget(
    metrics,
    environment as any
  );
  const exitCode = performanceBudgetManager.getCIExitCode(result);
  const report = performanceBudgetManager.generateCIReport(result, environment);

  return { exitCode, report, result };
}
