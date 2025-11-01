/**
 * Tests for Performance Alerting System
 */

import {
  PerformanceAlertingSystem,
  performanceAlertingSystem,
  DEFAULT_ALERT_RULES,
  usePerformanceAlerting,
} from "../performance-alerting";
import type { AlertRule, Alert } from "../performance-alerting";

// Mock browser APIs
Object.defineProperty(global, "window", {
  value: {
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
    Notification: jest.fn(),
  },
  writable: true,
});

Object.defineProperty(global, "Notification", {
  value: {
    permission: "granted",
    requestPermission: jest.fn().mockResolvedValue("granted"),
  },
  writable: true,
});

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

describe("PerformanceAlertingSystem", () => {
  let alertingSystem: PerformanceAlertingSystem;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });
    alertingSystem = new PerformanceAlertingSystem();
  });

  afterEach(() => {
    alertingSystem.cleanup();
  });

  describe("Initialization", () => {
    it("should initialize with default alert rules", () => {
      const rules = alertingSystem.getAlertRules();

      expect(rules.length).toBeGreaterThan(0);
      expect(rules).toEqual(
        expect.arrayContaining([
          expect.objectContaining({
            id: "budget-violation-critical",
            name: "Critical Budget Violation",
            enabled: true,
          }),
        ])
      );
    });

    it("should setup event listeners", () => {
      expect(window.addEventListener).toHaveBeenCalledWith(
        "core-web-vitals-update",
        expect.any(Function)
      );
      expect(window.addEventListener).toHaveBeenCalledWith(
        "performance-regression",
        expect.any(Function)
      );
    });
  });

  describe("Alert Rule Management", () => {
    it("should add new alert rule", () => {
      const newRule: AlertRule = {
        id: "test-rule",
        name: "Test Rule",
        description: "Test alert rule",
        enabled: true,
        conditions: [
          {
            type: "metric_threshold",
            metric: "lcp",
            operator: "gt",
            threshold: 3000,
          },
        ],
        actions: [
          {
            type: "console",
            config: {},
          },
        ],
        cooldownPeriod: 10,
        severity: "medium",
      };

      alertingSystem.setAlertRule(newRule);

      const rules = alertingSystem.getAlertRules();
      const addedRule = rules.find((r) => r.id === "test-rule");

      expect(addedRule).toBeDefined();
      expect(addedRule?.name).toBe("Test Rule");
    });

    it("should update existing alert rule", () => {
      const existingRule = alertingSystem.getAlertRules()[0];
      const updatedRule = {
        ...existingRule,
        name: "Updated Rule Name",
      };

      alertingSystem.setAlertRule(updatedRule);

      const rules = alertingSystem.getAlertRules();
      const rule = rules.find((r) => r.id === existingRule.id);

      expect(rule?.name).toBe("Updated Rule Name");
    });

    it("should remove alert rule", () => {
      const rules = alertingSystem.getAlertRules();
      const ruleToRemove = rules[0];

      alertingSystem.removeAlertRule(ruleToRemove.id);

      const updatedRules = alertingSystem.getAlertRules();
      const removedRule = updatedRules.find((r) => r.id === ruleToRemove.id);

      expect(removedRule).toBeUndefined();
    });
  });

  describe("Metric Threshold Monitoring", () => {
    it("should trigger alert for metric threshold violation", () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      // Simulate LCP metric update that exceeds threshold
      const event = new CustomEvent("core-web-vitals-update", {
        detail: { metric: "lcp", value: 5000, timestamp: Date.now() },
      });

      window.dispatchEvent(event);

      // Check if alert was triggered (console action)
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Performance Alert"),
        expect.any(Object)
      );

      consoleSpy.mockRestore();
    });

    it("should respect cooldown periods", () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      // Trigger first alert
      const event1 = new CustomEvent("core-web-vitals-update", {
        detail: { metric: "lcp", value: 5000, timestamp: Date.now() },
      });
      window.dispatchEvent(event1);

      // Trigger second alert immediately (should be blocked by cooldown)
      const event2 = new CustomEvent("core-web-vitals-update", {
        detail: { metric: "lcp", value: 5000, timestamp: Date.now() },
      });
      window.dispatchEvent(event2);

      // Should only have one alert due to cooldown
      expect(consoleSpy).toHaveBeenCalledTimes(1);

      consoleSpy.mockRestore();
    });
  });

  describe("Performance Regression Handling", () => {
    it("should handle performance regression alerts", () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      const regressionEvent = new CustomEvent("performance-regression", {
        detail: {
          id: "test-regression",
          timestamp: new Date(),
          metric: "lcp",
          currentValue: 4000,
          baselineValue: 2000,
          degradationPercent: 100,
          severity: "critical",
          resolved: false,
        },
      });

      window.dispatchEvent(regressionEvent);

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Performance Alert"),
        expect.any(Object)
      );

      consoleSpy.mockRestore();
    });
  });

  describe("Alert Actions", () => {
    beforeEach(() => {
      // Mock Notification constructor
      (global.Notification as jest.Mock).mockImplementation(
        (title, options) => ({
          title,
          ...options,
          close: jest.fn(),
          onclick: null,
        })
      );
    });

    it("should execute console action", () => {
      const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

      const testAlert: Alert = {
        id: "test-alert",
        ruleId: "test-rule",
        timestamp: new Date(),
        severity: "critical",
        title: "Test Alert",
        message: "Test alert message",
        data: {},
        acknowledged: false,
        resolved: false,
      };

      alertingSystem["executeConsoleAction"](testAlert);

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("🚨 Performance Alert: Test Alert"),
        expect.objectContaining({
          message: "Test alert message",
          severity: "critical",
        })
      );

      consoleSpy.mockRestore();
    });

    it("should execute browser notification action", async () => {
      const testAlert: Alert = {
        id: "test-alert",
        ruleId: "test-rule",
        timestamp: new Date(),
        severity: "critical",
        title: "Test Alert",
        message: "Test alert message",
        data: {},
        acknowledged: false,
        resolved: false,
      };

      await alertingSystem["executeBrowserNotificationAction"](testAlert, {
        title: "Custom Title",
      });

      expect(global.Notification).toHaveBeenCalledWith(
        "Custom Title",
        expect.objectContaining({
          body: "Test alert message",
          requireInteraction: true, // Critical alerts require interaction
        })
      );
    });

    it("should execute webhook action", async () => {
      const testAlert: Alert = {
        id: "test-alert",
        ruleId: "test-rule",
        timestamp: new Date(),
        severity: "high",
        title: "Test Alert",
        message: "Test alert message",
        data: { metric: "lcp", value: 4000 },
        acknowledged: false,
        resolved: false,
      };

      await alertingSystem["executeWebhookAction"](testAlert, {
        url: "https://example.com/webhook",
      });

      expect(global.fetch).toHaveBeenCalledWith(
        "https://example.com/webhook",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: expect.stringContaining("Test Alert"),
        })
      );
    });
  });

  describe("Alert Management", () => {
    let testAlert: Alert;

    beforeEach(() => {
      testAlert = {
        id: "test-alert",
        ruleId: "test-rule",
        timestamp: new Date(),
        severity: "medium",
        title: "Test Alert",
        message: "Test message",
        data: {},
        acknowledged: false,
        resolved: false,
      };

      alertingSystem["alerts"] = [testAlert];
    });

    it("should get all alerts", () => {
      const alerts = alertingSystem.getAlerts();

      expect(alerts).toHaveLength(1);
      expect(alerts[0]).toEqual(testAlert);
    });

    it("should filter alerts by criteria", () => {
      const acknowledgedAlert = {
        ...testAlert,
        id: "acknowledged-alert",
        acknowledged: true,
      };

      alertingSystem["alerts"] = [testAlert, acknowledgedAlert];

      const unacknowledged = alertingSystem.getAlerts({ acknowledged: false });
      const acknowledged = alertingSystem.getAlerts({ acknowledged: true });

      expect(unacknowledged).toHaveLength(1);
      expect(acknowledged).toHaveLength(1);
      expect(unacknowledged[0].id).toBe("test-alert");
      expect(acknowledged[0].id).toBe("acknowledged-alert");
    });

    it("should acknowledge alert", () => {
      alertingSystem.acknowledgeAlert("test-alert");

      const alerts = alertingSystem.getAlerts();
      const alert = alerts.find((a) => a.id === "test-alert");

      expect(alert?.acknowledged).toBe(true);
      expect(alert?.acknowledgedAt).toBeInstanceOf(Date);
    });

    it("should resolve alert", () => {
      alertingSystem.resolveAlert("test-alert");

      const alerts = alertingSystem.getAlerts();
      const alert = alerts.find((a) => a.id === "test-alert");

      expect(alert?.resolved).toBe(true);
      expect(alert?.resolvedAt).toBeInstanceOf(Date);
    });

    it("should clear old alerts", () => {
      const oldAlert = {
        ...testAlert,
        id: "old-alert",
        timestamp: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000), // 10 days ago
      };

      alertingSystem["alerts"] = [testAlert, oldAlert];
      alertingSystem.clearOldAlerts(7); // Clear alerts older than 7 days

      const alerts = alertingSystem.getAlerts();
      expect(alerts).toHaveLength(1);
      expect(alerts[0].id).toBe("test-alert");
    });
  });

  describe("Condition Evaluation", () => {
    it("should evaluate greater than condition correctly", () => {
      const result = alertingSystem["evaluateCondition"](150, "gt", 100);
      expect(result).toBe(true);

      const result2 = alertingSystem["evaluateCondition"](50, "gt", 100);
      expect(result2).toBe(false);
    });

    it("should evaluate less than condition correctly", () => {
      const result = alertingSystem["evaluateCondition"](50, "lt", 100);
      expect(result).toBe(true);

      const result2 = alertingSystem["evaluateCondition"](150, "lt", 100);
      expect(result2).toBe(false);
    });

    it("should evaluate equality condition correctly", () => {
      const result = alertingSystem["evaluateCondition"](100, "eq", 100);
      expect(result).toBe(true);

      const result2 = alertingSystem["evaluateCondition"](99, "eq", 100);
      expect(result2).toBe(false);
    });
  });

  describe("Message Generation", () => {
    it("should generate appropriate alert messages", () => {
      const rule: AlertRule = {
        id: "test-rule",
        name: "Test Rule",
        description: "LCP threshold exceeded",
        enabled: true,
        conditions: [],
        actions: [],
        cooldownPeriod: 10,
        severity: "high",
      };

      const data = { metric: "lcp", value: 4000 };
      const message = alertingSystem["generateAlertMessage"](rule, data);

      expect(message).toContain("LCP threshold exceeded");
      expect(message).toContain("LCP = 4000ms");
    });

    it("should format metric values correctly", () => {
      expect(alertingSystem["formatMetricValue"]("lcp", 2500)).toBe("2500ms");
      expect(alertingSystem["formatMetricValue"]("cls", 0.125)).toBe("0.125");
      expect(alertingSystem["formatMetricValue"]("bundleSize", 1024000)).toBe(
        "1000KB"
      );
    });
  });

  describe("Data Persistence", () => {
    it("should save alerts to localStorage", () => {
      const testAlert: Alert = {
        id: "test-alert",
        ruleId: "test-rule",
        timestamp: new Date(),
        severity: "medium",
        title: "Test Alert",
        message: "Test message",
        data: {},
        acknowledged: false,
        resolved: false,
      };

      alertingSystem["alerts"] = [testAlert];
      alertingSystem["saveAlerts"]();

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "performance-alerts",
        expect.stringContaining("test-alert")
      );
    });

    it("should load alerts from localStorage", () => {
      const mockAlerts = JSON.stringify([
        {
          id: "stored-alert",
          ruleId: "stored-rule",
          timestamp: new Date().toISOString(),
          severity: "low",
          title: "Stored Alert",
          message: "Stored message",
          data: {},
          acknowledged: false,
          resolved: false,
        },
      ]);

      localStorageMock.getItem.mockReturnValue(mockAlerts);

      const newSystem = new PerformanceAlertingSystem();
      const alerts = newSystem.getAlerts();

      expect(alerts).toHaveLength(1);
      expect(alerts[0].id).toBe("stored-alert");

      newSystem.cleanup();
    });
  });

  describe("Error Handling", () => {
    it("should handle localStorage errors gracefully", () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error("Storage quota exceeded");
      });

      expect(() => {
        alertingSystem["saveAlerts"]();
      }).not.toThrow();
    });

    it("should handle webhook failures gracefully", async () => {
      (global.fetch as jest.Mock).mockRejectedValue(new Error("Network error"));

      const testAlert: Alert = {
        id: "test-alert",
        ruleId: "test-rule",
        timestamp: new Date(),
        severity: "high",
        title: "Test Alert",
        message: "Test message",
        data: {},
        acknowledged: false,
        resolved: false,
      };

      await expect(
        alertingSystem["executeWebhookAction"](testAlert, {
          url: "https://example.com/webhook",
        })
      ).resolves.toBeUndefined();
    });

    it("should handle missing Notification API gracefully", async () => {
      delete (global as any).Notification;

      const testAlert: Alert = {
        id: "test-alert",
        ruleId: "test-rule",
        timestamp: new Date(),
        severity: "critical",
        title: "Test Alert",
        message: "Test message",
        data: {},
        acknowledged: false,
        resolved: false,
      };

      await expect(
        alertingSystem["executeBrowserNotificationAction"](testAlert, {})
      ).resolves.toBeUndefined();
    });
  });
});

describe("usePerformanceAlerting Hook", () => {
  it("should return null in non-browser environment", () => {
    // Temporarily remove window
    const originalWindow = global.window;
    delete (global as any).window;

    const result = usePerformanceAlerting();
    expect(result).toBeNull();

    // Restore window
    global.window = originalWindow;
  });

  it("should return alerting functions in browser environment", () => {
    const result = usePerformanceAlerting();

    expect(result).toHaveProperty("getAlerts");
    expect(result).toHaveProperty("acknowledgeAlert");
    expect(result).toHaveProperty("resolveAlert");
    expect(result).toHaveProperty("getAlertRules");
    expect(result).toHaveProperty("setAlertRule");
    expect(result).toHaveProperty("removeAlertRule");
    expect(result).toHaveProperty("clearOldAlerts");

    expect(typeof result?.getAlerts).toBe("function");
    expect(typeof result?.acknowledgeAlert).toBe("function");
  });
});
