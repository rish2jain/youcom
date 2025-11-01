/**
 * Performance Alerting and Notification System
 * Handles performance degradation alerts, budget violations, and proactive monitoring
 */

import { useMemo } from "react";
import { RegressionAlert } from "./core-web-vitals-monitor";

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  conditions: AlertCondition[];
  actions: AlertAction[];
  cooldownPeriod: number; // minutes
  severity: "low" | "medium" | "high" | "critical";
}

export interface AlertCondition {
  type:
    | "metric_threshold"
    | "budget_violation"
    | "trend_degradation"
    | "regression_detected";
  metric?: string;
  operator?: "gt" | "lt" | "gte" | "lte" | "eq";
  threshold?: number;
  duration?: number; // minutes
  percentage?: number;
}

export interface AlertAction {
  type:
    | "console"
    | "notification"
    | "webhook"
    | "email"
    | "slack"
    | "browser_notification";
  config: Record<string, any>;
}

export interface Alert {
  id: string;
  ruleId: string;
  timestamp: Date;
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  message: string;
  data: Record<string, any>;
  acknowledged: boolean;
  resolved: boolean;
  resolvedAt?: Date;
  acknowledgedAt?: Date;
}

export interface NotificationChannel {
  id: string;
  name: string;
  type: "webhook" | "email" | "slack" | "browser";
  config: Record<string, any>;
  enabled: boolean;
}

// Default alert rules for performance monitoring
export const DEFAULT_ALERT_RULES: AlertRule[] = [
  {
    id: "budget-violation-critical",
    name: "Critical Budget Violation",
    description:
      "Alert when performance metrics exceed budget by more than 50%",
    enabled: true,
    conditions: [
      {
        type: "budget_violation",
        percentage: 150, // 50% over budget
      },
    ],
    actions: [
      { type: "console", config: {} },
      {
        type: "browser_notification",
        config: { title: "Critical Performance Issue" },
      },
      {
        type: "webhook",
        config: {
          url:
            (typeof process !== "undefined" &&
              process.env?.PERFORMANCE_WEBHOOK_URL) ||
            "",
        },
      },
    ],
    cooldownPeriod: 15, // 15 minutes
    severity: "critical",
  },
  {
    id: "budget-violation-warning",
    name: "Budget Warning",
    description: "Alert when performance metrics exceed 80% of budget",
    enabled: true,
    conditions: [
      {
        type: "budget_violation",
        percentage: 80,
      },
    ],
    actions: [
      { type: "console", config: {} },
      { type: "notification", config: {} },
    ],
    cooldownPeriod: 30, // 30 minutes
    severity: "medium",
  },
  {
    id: "lcp-threshold",
    name: "LCP Threshold Exceeded",
    description: "Alert when Largest Contentful Paint exceeds 4 seconds",
    enabled: true,
    conditions: [
      {
        type: "metric_threshold",
        metric: "lcp",
        operator: "gt",
        threshold: 4000, // 4 seconds
        duration: 5, // sustained for 5 minutes
      },
    ],
    actions: [
      { type: "console", config: {} },
      {
        type: "browser_notification",
        config: { title: "LCP Performance Issue" },
      },
    ],
    cooldownPeriod: 20,
    severity: "high",
  },
  {
    id: "cls-threshold",
    name: "CLS Threshold Exceeded",
    description: "Alert when Cumulative Layout Shift exceeds 0.25",
    enabled: true,
    conditions: [
      {
        type: "metric_threshold",
        metric: "cls",
        operator: "gt",
        threshold: 0.25,
        duration: 3,
      },
    ],
    actions: [
      { type: "console", config: {} },
      { type: "notification", config: {} },
    ],
    cooldownPeriod: 25,
    severity: "high",
  },
  {
    id: "performance-regression",
    name: "Performance Regression Detected",
    description: "Alert when performance regression is detected",
    enabled: true,
    conditions: [
      {
        type: "regression_detected",
        percentage: 20, // 20% degradation
      },
    ],
    actions: [
      { type: "console", config: {} },
      {
        type: "browser_notification",
        config: { title: "Performance Regression" },
      },
      {
        type: "webhook",
        config: {
          url:
            (typeof process !== "undefined" &&
              process.env?.REGRESSION_WEBHOOK_URL) ||
            "",
        },
      },
    ],
    cooldownPeriod: 10,
    severity: "high",
  },
];

export class PerformanceAlertingSystem {
  private rules: AlertRule[] = [];
  private alerts: Alert[] = [];
  private cooldowns: Map<string, Date> = new Map();
  private metricHistory: Map<
    string,
    Array<{ timestamp: Date; value: number }>
  > = new Map();

  private readonly STORAGE_KEY_RULES = "performance-alert-rules";
  private readonly STORAGE_KEY_ALERTS = "performance-alerts";
  private readonly MAX_ALERTS = 1000;
  private readonly MAX_HISTORY = 100;

  constructor() {
    this.loadConfiguration();
    this.initializeDefaultRules();
    this.setupEventListeners();
  }

  /**
   * Initialize default alert rules if none exist
   */
  private initializeDefaultRules(): void {
    if (this.rules.length === 0) {
      this.rules = [...DEFAULT_ALERT_RULES];
      this.saveRules();
    }
  }

  /**
   * Setup event listeners for performance events
   */
  private setupEventListeners(): void {
    if (typeof window === "undefined") return;

    // Listen for Core Web Vitals updates
    window.addEventListener("core-web-vitals-update", (event: Event) => {
      // Add runtime type guard before accessing detail
      if (event instanceof CustomEvent && event.detail) {
        const { metric, value, timestamp } = event.detail;
        if (metric && typeof value === "number" && timestamp) {
          this.recordMetric(metric, value, new Date(timestamp));
          this.checkMetricThresholds(metric, value);
        }
      }
    });

    // Listen for performance regressions
    window.addEventListener("performance-regression", (event: Event) => {
      // Add runtime type guard before accessing detail
      if (event instanceof CustomEvent && event.detail) {
        const regression: RegressionAlert = event.detail;
        this.handleRegressionAlert(regression);
      }
    });

    // Listen for budget violations
    window.addEventListener("budget-violation", (event: Event) => {
      // Add runtime type guard before accessing detail
      if (event instanceof CustomEvent && event.detail) {
        const violation = event.detail;
        this.handleBudgetViolation(violation);
      }
    });
  }

  /**
   * Record metric value for trend analysis
   */
  private recordMetric(metric: string, value: number, timestamp: Date): void {
    if (!this.metricHistory.has(metric)) {
      this.metricHistory.set(metric, []);
    }

    const history = this.metricHistory.get(metric)!;
    history.push({ timestamp, value });

    // Keep only recent history
    if (history.length > this.MAX_HISTORY) {
      history.splice(0, history.length - this.MAX_HISTORY);
    }
  }

  /**
   * Check metric thresholds against alert rules
   */
  private checkMetricThresholds(metric: string, value: number): void {
    const relevantRules = this.rules.filter(
      (rule) =>
        rule.enabled &&
        rule.conditions.some(
          (condition) =>
            condition.type === "metric_threshold" && condition.metric === metric
        )
    );

    relevantRules.forEach((rule) => {
      const condition = rule.conditions.find(
        (c) => c.type === "metric_threshold" && c.metric === metric
      );

      if (!condition || !condition.threshold || !condition.operator) return;

      const isTriggered = this.evaluateCondition(
        value,
        condition.operator,
        condition.threshold
      );

      if (isTriggered && condition.duration) {
        // Check if condition has been sustained for required duration
        const sustained = this.isConditionSustained(metric, condition);
        if (sustained) {
          this.triggerAlert(rule, { metric, value, condition });
        }
      } else if (isTriggered && !condition.duration) {
        this.triggerAlert(rule, { metric, value, condition });
      }
    });
  }

  /**
   * Evaluate condition operator
   */
  private evaluateCondition(
    value: number,
    operator: string,
    threshold: number
  ): boolean {
    switch (operator) {
      case "gt":
        return value > threshold;
      case "lt":
        return value < threshold;
      case "gte":
        return value >= threshold;
      case "lte":
        return value <= threshold;
      case "eq":
        return value === threshold;
      default:
        return false;
    }
  }

  /**
   * Check if condition has been sustained for required duration
   */
  private isConditionSustained(
    metric: string,
    condition: AlertCondition
  ): boolean {
    if (!condition.duration || !condition.threshold || !condition.operator)
      return false;

    const history = this.metricHistory.get(metric);
    if (!history || history.length === 0) return false;

    const durationMs = condition.duration * 60 * 1000; // Convert to milliseconds
    const cutoff = new Date(Date.now() - durationMs);

    const recentValues = history.filter((entry) => entry.timestamp >= cutoff);

    // Check if all recent values meet the condition
    return (
      recentValues.length > 0 &&
      recentValues.every((entry) =>
        this.evaluateCondition(
          entry.value,
          condition.operator!,
          condition.threshold!
        )
      )
    );
  }

  /**
   * Handle performance regression alerts
   */
  private handleRegressionAlert(regression: RegressionAlert): void {
    const relevantRules = this.rules.filter(
      (rule) =>
        rule.enabled &&
        rule.conditions.some(
          (condition) => condition.type === "regression_detected"
        )
    );

    relevantRules.forEach((rule) => {
      const condition = rule.conditions.find(
        (c) => c.type === "regression_detected"
      );

      if (
        condition &&
        condition.percentage &&
        regression.degradationPercent >= condition.percentage
      ) {
        this.triggerAlert(rule, { regression });
      }
    });
  }

  /**
   * Handle budget violation alerts
   */
  private handleBudgetViolation(violation: any): void {
    const relevantRules = this.rules.filter(
      (rule) =>
        rule.enabled &&
        rule.conditions.some(
          (condition) => condition.type === "budget_violation"
        )
    );

    relevantRules.forEach((rule) => {
      const condition = rule.conditions.find(
        (c) => c.type === "budget_violation"
      );

      if (condition && condition.percentage) {
        const violationPercentage = (violation.actual / violation.budget) * 100;

        if (violationPercentage >= condition.percentage) {
          this.triggerAlert(rule, { violation });
        }
      }
    });
  }

  /**
   * Trigger an alert if not in cooldown period
   */
  private triggerAlert(rule: AlertRule, data: Record<string, any>): void {
    // Check cooldown period
    const lastAlert = this.cooldowns.get(rule.id);
    if (lastAlert) {
      const cooldownEnd = new Date(
        lastAlert.getTime() + rule.cooldownPeriod * 60 * 1000
      );
      if (new Date() < cooldownEnd) {
        return; // Still in cooldown
      }
    }

    // Create alert
    const alert: Alert = {
      id: `alert-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
      ruleId: rule.id,
      timestamp: new Date(),
      severity: rule.severity,
      title: rule.name,
      message: this.generateAlertMessage(rule, data),
      data,
      acknowledged: false,
      resolved: false,
    };

    this.alerts.push(alert);
    this.trimAlerts();
    this.saveAlerts();

    // Update cooldown
    this.cooldowns.set(rule.id, new Date());

    // Execute alert actions
    this.executeAlertActions(rule, alert);

    // Emit alert event
    this.emitAlertEvent(alert);
  }

  /**
   * Generate alert message based on rule and data
   */
  private generateAlertMessage(
    rule: AlertRule,
    data: Record<string, any>
  ): string {
    if (data.metric && data.value) {
      return `${
        rule.description
      }: ${data.metric.toUpperCase()} = ${this.formatMetricValue(
        data.metric,
        data.value
      )}`;
    }

    if (data.regression) {
      const reg = data.regression;
      return `Performance regression detected: ${reg.metric.toUpperCase()} degraded by ${reg.degradationPercent.toFixed(
        1
      )}%`;
    }

    if (data.violation) {
      const viol = data.violation;
      return `Budget violation: ${viol.metric.toUpperCase()} exceeded budget by ${(
        (viol.actual / viol.budget - 1) *
        100
      ).toFixed(1)}%`;
    }

    return rule.description;
  }

  /**
   * Format metric values for display
   */
  private formatMetricValue(metric: string, value: number): string {
    switch (metric) {
      case "lcp":
      case "fid":
      case "fcp":
      case "ttfb":
        return `${Math.round(value)}ms`;
      case "cls":
        return value.toFixed(3);
      case "bundleSize":
        return `${Math.round(value / 1024)}KB`;
      default:
        return value.toString();
    }
  }

  /**
   * Execute alert actions
   */
  private async executeAlertActions(
    rule: AlertRule,
    alert: Alert
  ): Promise<void> {
    for (const action of rule.actions) {
      try {
        await this.executeAction(action, alert);
      } catch (error) {
        console.error(`Failed to execute alert action ${action.type}:`, error);
      }
    }
  }

  /**
   * Execute individual alert action
   */
  private async executeAction(
    action: AlertAction,
    alert: Alert
  ): Promise<void> {
    switch (action.type) {
      case "console":
        this.executeConsoleAction(alert);
        break;
      case "notification":
        this.executeNotificationAction(alert, action.config);
        break;
      case "browser_notification":
        await this.executeBrowserNotificationAction(alert, action.config);
        break;
      case "webhook":
        await this.executeWebhookAction(alert, action.config);
        break;
      case "email":
        await this.executeEmailAction(alert, action.config);
        break;
      case "slack":
        await this.executeSlackAction(alert, action.config);
        break;
    }
  }

  /**
   * Execute console action
   */
  private executeConsoleAction(alert: Alert): void {
    const icon =
      alert.severity === "critical"
        ? "🚨"
        : alert.severity === "high"
        ? "⚠️"
        : alert.severity === "medium"
        ? "⚡"
        : "ℹ️";

    console.warn(`${icon} Performance Alert: ${alert.title}`, {
      message: alert.message,
      severity: alert.severity,
      timestamp: alert.timestamp,
      data: alert.data,
    });
  }

  /**
   * Execute notification action (custom event)
   */
  private executeNotificationAction(alert: Alert, config: any): void {
    const event = new CustomEvent("performance-alert", {
      detail: { alert, config },
    });
    window.dispatchEvent(event);
  }

  /**
   * Execute browser notification action
   */
  private async executeBrowserNotificationAction(
    alert: Alert,
    config: any
  ): Promise<void> {
    if (!("Notification" in window)) return;

    // Request permission if needed
    if (Notification.permission === "default") {
      await Notification.requestPermission();
    }

    if (Notification.permission === "granted") {
      const notification = new Notification(config.title || alert.title, {
        body: alert.message,
        icon: "/favicon.ico",
        badge: "/favicon.ico",
        tag: `performance-alert-${alert.severity}`,
        requireInteraction: alert.severity === "critical",
      });

      notification.onclick = () => {
        window.focus();
        notification.close();
      };

      // Auto-close after 10 seconds for non-critical alerts
      if (alert.severity !== "critical") {
        setTimeout(() => notification.close(), 10000);
      }
    }
  }

  /**
   * Execute webhook action
   */
  private async executeWebhookAction(alert: Alert, config: any): Promise<void> {
    if (!config.url || config.url === "") return;

    const payload = {
      alert: {
        id: alert.id,
        title: alert.title,
        message: alert.message,
        severity: alert.severity,
        timestamp: alert.timestamp.toISOString(),
      },
      data: alert.data,
      source: "performance-monitoring",
    };

    await fetch(config.url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(config.headers || {}),
      },
      body: JSON.stringify(payload),
    });
  }

  /**
   * Execute email action (would require server-side implementation)
   */
  private async executeEmailAction(alert: Alert, config: any): Promise<void> {
    // This would typically send to a server endpoint that handles email sending
    console.log("Email action would be executed:", { alert, config });
  }

  /**
   * Execute Slack action
   */
  private async executeSlackAction(alert: Alert, config: any): Promise<void> {
    if (!config.webhookUrl) return;

    const color =
      alert.severity === "critical"
        ? "danger"
        : alert.severity === "high"
        ? "warning"
        : "good";

    const payload = {
      text: `Performance Alert: ${alert.title}`,
      attachments: [
        {
          color,
          fields: [
            {
              title: "Message",
              value: alert.message,
              short: false,
            },
            {
              title: "Severity",
              value: alert.severity.toUpperCase(),
              short: true,
            },
            {
              title: "Timestamp",
              value: alert.timestamp.toISOString(),
              short: true,
            },
          ],
        },
      ],
    };

    await fetch(config.webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  /**
   * Emit alert event for UI components
   */
  private emitAlertEvent(alert: Alert): void {
    const event = new CustomEvent("performance-alert-triggered", {
      detail: alert,
    });
    window.dispatchEvent(event);
  }

  /**
   * Get all alerts
   */
  getAlerts(filter?: {
    severity?: string;
    acknowledged?: boolean;
    resolved?: boolean;
  }): Alert[] {
    let filtered = [...this.alerts];

    if (filter) {
      if (filter.severity) {
        filtered = filtered.filter(
          (alert) => alert.severity === filter.severity
        );
      }
      if (filter.acknowledged !== undefined) {
        filtered = filtered.filter(
          (alert) => alert.acknowledged === filter.acknowledged
        );
      }
      if (filter.resolved !== undefined) {
        filtered = filtered.filter(
          (alert) => alert.resolved === filter.resolved
        );
      }
    }

    return filtered.sort(
      (a, b) => b.timestamp.getTime() - a.timestamp.getTime()
    );
  }

  /**
   * Acknowledge an alert
   */
  acknowledgeAlert(alertId: string): void {
    const alert = this.alerts.find((a) => a.id === alertId);
    if (alert && !alert.acknowledged) {
      alert.acknowledged = true;
      alert.acknowledgedAt = new Date();
      this.saveAlerts();
    }
  }

  /**
   * Resolve an alert
   */
  resolveAlert(alertId: string): void {
    const alert = this.alerts.find((a) => a.id === alertId);
    if (alert && !alert.resolved) {
      alert.resolved = true;
      alert.resolvedAt = new Date();
      this.saveAlerts();
    }
  }

  /**
   * Add or update alert rule
   */
  setAlertRule(rule: AlertRule): void {
    const existingIndex = this.rules.findIndex((r) => r.id === rule.id);
    if (existingIndex >= 0) {
      this.rules[existingIndex] = rule;
    } else {
      this.rules.push(rule);
    }
    this.saveRules();
  }

  /**
   * Remove alert rule
   */
  removeAlertRule(ruleId: string): void {
    this.rules = this.rules.filter((r) => r.id !== ruleId);
    this.saveRules();
  }

  /**
   * Get alert rules
   */
  getAlertRules(): AlertRule[] {
    return [...this.rules];
  }

  /**
   * Clear old alerts
   */
  clearOldAlerts(days: number = 7): void {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);

    this.alerts = this.alerts.filter((alert) => alert.timestamp >= cutoff);
    this.saveAlerts();
  }

  /**
   * Trim alerts to maintain storage limits
   */
  private trimAlerts(): void {
    if (this.alerts.length > this.MAX_ALERTS) {
      this.alerts = this.alerts
        .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
        .slice(0, this.MAX_ALERTS);
    }
  }

  /**
   * Load configuration from storage
   */
  private loadConfiguration(): void {
    if (typeof window === "undefined") return;

    try {
      // Load rules
      const storedRules = localStorage.getItem(this.STORAGE_KEY_RULES);
      if (storedRules) {
        this.rules = JSON.parse(storedRules);
      }

      // Load alerts
      const storedAlerts = localStorage.getItem(this.STORAGE_KEY_ALERTS);
      if (storedAlerts) {
        const parsed = JSON.parse(storedAlerts);
        this.alerts = parsed.map((alert: any) => ({
          ...alert,
          timestamp: new Date(alert.timestamp),
          acknowledgedAt: alert.acknowledgedAt
            ? new Date(alert.acknowledgedAt)
            : undefined,
          resolvedAt: alert.resolvedAt ? new Date(alert.resolvedAt) : undefined,
        }));
      }
    } catch (error) {
      console.warn("Failed to load alerting configuration:", error);
    }
  }

  /**
   * Save rules to storage
   */
  private saveRules(): void {
    if (typeof window === "undefined") return;

    try {
      localStorage.setItem(this.STORAGE_KEY_RULES, JSON.stringify(this.rules));
    } catch (error) {
      console.warn("Failed to save alert rules:", error);
    }
  }

  /**
   * Save alerts to storage
   */
  private saveAlerts(): void {
    if (typeof window === "undefined") return;

    try {
      localStorage.setItem(
        this.STORAGE_KEY_ALERTS,
        JSON.stringify(this.alerts)
      );
    } catch (error) {
      console.warn("Failed to save alerts:", error);
    }
  }

  /**
   * Cleanup resources
   */
  cleanup(): void {
    this.cooldowns.clear();
    this.metricHistory.clear();
  }
}

// Global alerting system instance
export const performanceAlertingSystem = new PerformanceAlertingSystem();

// Stable API object to prevent re-renders
const stableAlertingAPI = {
  getAlerts: (filter?: any) => performanceAlertingSystem.getAlerts(filter),
  acknowledgeAlert: (alertId: string) =>
    performanceAlertingSystem.acknowledgeAlert(alertId),
  resolveAlert: (alertId: string) =>
    performanceAlertingSystem.resolveAlert(alertId),
  getAlertRules: () => performanceAlertingSystem.getAlertRules(),
  setAlertRule: (rule: AlertRule) =>
    performanceAlertingSystem.setAlertRule(rule),
  removeAlertRule: (ruleId: string) =>
    performanceAlertingSystem.removeAlertRule(ruleId),
  clearOldAlerts: (days?: number) =>
    performanceAlertingSystem.clearOldAlerts(days),
};

// React hook for performance alerting
export function usePerformanceAlerting() {
  return useMemo(() => {
    if (typeof window === "undefined") return null;
    return stableAlertingAPI;
  }, []);
}
