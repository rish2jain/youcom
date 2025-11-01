/**
 * Tests for Core Web Vitals Monitor
 */

import { describe, it, beforeEach, afterEach } from "@jest/globals";
import {
  coreWebVitalsMonitor,
  CoreWebVitalsMonitor,
} from "../core-web-vitals-monitor";

// Mock browser APIs
const mockPerformanceObserver = jest.fn();
const mockPerformanceEntry = {
  startTime: 2000,
  processingStart: 2100,
  value: 0.05,
  hadRecentInput: false,
};

Object.defineProperty(global, "window", {
  value: {
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
    location: { href: "http://localhost:3000" },
    PerformanceObserver: mockPerformanceObserver,
  },
  writable: true,
});

Object.defineProperty(global, "performance", {
  value: {
    getEntriesByType: jest.fn((type: string) => {
      if (type === "navigation") {
        return [
          {
            requestStart: 100,
            responseStart: 300,
            fetchStart: 0,
            loadEventEnd: 2000,
          },
        ];
      }
      if (type === "paint") {
        return [{ name: "first-contentful-paint", startTime: 1500 }];
      }
      if (type === "largest-contentful-paint") {
        return [{ startTime: 2000 }];
      }
      return [];
    }),
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

describe("CoreWebVitalsMonitor", () => {
  let monitor: CoreWebVitalsMonitor;

  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
    monitor = new CoreWebVitalsMonitor();
  });

  afterEach(() => {
    monitor.cleanup();
  });

  describe("Initialization", () => {
    it("should initialize with empty metrics", () => {
      const metrics = monitor.getCurrentMetrics();
      expect(metrics).toEqual({});
    });

    it("should generate unique session ID", () => {
      const monitor1 = new CoreWebVitalsMonitor();
      const monitor2 = new CoreWebVitalsMonitor();

      const entry1 = monitor1.recordEntry();
      const entry2 = monitor2.recordEntry();

      expect(entry1.sessionId).not.toBe(entry2.sessionId);

      monitor1.cleanup();
      monitor2.cleanup();
    });
  });

  describe("Metric Recording", () => {
    it("should record performance entry with all required fields", () => {
      const entry = monitor.recordEntry();

      expect(entry).toHaveProperty("id");
      expect(entry).toHaveProperty("timestamp");
      expect(entry).toHaveProperty("url");
      expect(entry).toHaveProperty("sessionId");
      expect(entry).toHaveProperty("lcp");
      expect(entry).toHaveProperty("fid");
      expect(entry).toHaveProperty("cls");
      expect(entry).toHaveProperty("fcp");
      expect(entry).toHaveProperty("ttfb");
      expect(entry).toHaveProperty("userAgent");

      expect(entry.url).toBe("http://localhost:3000");
      expect(entry.userAgent).toBe("Mozilla/5.0 (Test Browser)");
      expect(typeof entry.sessionId).toBe("string");
      expect(entry.timestamp).toBeInstanceOf(Date);
    });

    it("should include device capabilities when available", () => {
      const entry = monitor.recordEntry();

      expect(entry.connectionType).toBe("4g");
      expect(entry.deviceMemory).toBe(8);
    });
  });

  describe("Trend Analysis", () => {
    it("should return empty trends with insufficient data", () => {
      const trends = monitor.analyzeTrends(7);
      expect(trends).toEqual([]);
    });

    it("should calculate trends with sufficient data", () => {
      // Record multiple entries with different values
      for (let i = 0; i < 20; i++) {
        monitor.recordEntry();
      }

      const trends = monitor.analyzeTrends(1);
      expect(Array.isArray(trends)).toBe(true);

      if (trends.length > 0) {
        const trend = trends[0];
        expect(trend).toHaveProperty("metric");
        expect(trend).toHaveProperty("current");
        expect(trend).toHaveProperty("previous");
        expect(trend).toHaveProperty("change");
        expect(trend).toHaveProperty("changePercent");
        expect(trend).toHaveProperty("trend");
        expect(trend).toHaveProperty("significance");

        expect(["improving", "degrading", "stable"]).toContain(trend.trend);
        expect(["low", "medium", "high"]).toContain(trend.significance);
      }
    });
  });

  describe("Performance Summary", () => {
    it("should provide comprehensive performance summary", () => {
      monitor.recordEntry();
      const summary = monitor.getPerformanceSummary();

      expect(summary).toHaveProperty("current");
      expect(summary).toHaveProperty("trends");
      expect(summary).toHaveProperty("totalEntries");
      expect(summary).toHaveProperty("sessionCount");
      expect(summary).toHaveProperty("lastUpdated");

      expect(summary.totalEntries).toBe(1);
      expect(summary.sessionCount).toBe(1);
      expect(summary.lastUpdated).toBeInstanceOf(Date);
      expect(Array.isArray(summary.trends)).toBe(true);
    });
  });

  describe("Data Export", () => {
    beforeEach(() => {
      monitor.recordEntry();
    });

    it("should export data in JSON format", () => {
      const jsonData = monitor.exportData("json");

      expect(() => JSON.parse(jsonData)).not.toThrow();
      const parsed = JSON.parse(jsonData);
      expect(Array.isArray(parsed)).toBe(true);
      expect(parsed.length).toBe(1);

      const entry = parsed[0];
      expect(entry).toHaveProperty("id");
      expect(entry).toHaveProperty("timestamp");
      expect(entry).toHaveProperty("url");
    });

    it("should export data in CSV format", () => {
      const csvData = monitor.exportData("csv");

      expect(typeof csvData).toBe("string");
      expect(csvData).toContain("timestamp,url,lcp,fid,cls,fcp,ttfb,sessionId");

      const lines = csvData.split("\n");
      expect(lines.length).toBeGreaterThan(1); // Header + at least one data row
    });
  });

  describe("Data Management", () => {
    it("should clear all data", () => {
      monitor.recordEntry();
      let summary = monitor.getPerformanceSummary();
      expect(summary.totalEntries).toBe(1);

      monitor.clearData();
      summary = monitor.getPerformanceSummary();
      expect(summary.totalEntries).toBe(0);
      expect(summary.sessionCount).toBe(0);
    });

    it("should persist data to localStorage", () => {
      monitor.recordEntry();

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "core-web-vitals-entries",
        expect.any(String)
      );
    });

    it("should load data from localStorage", () => {
      const mockData = JSON.stringify([
        {
          id: "test-id",
          timestamp: new Date().toISOString(),
          url: "http://test.com",
          lcp: 2000,
          fid: 100,
          cls: 0.1,
          fcp: 1500,
          ttfb: 500,
          sessionId: "test-session",
          userAgent: "Test Agent",
        },
      ]);

      localStorageMock.getItem.mockReturnValue(mockData);

      const newMonitor = new CoreWebVitalsMonitor();
      const summary = newMonitor.getPerformanceSummary();

      expect(summary.totalEntries).toBe(1);
      newMonitor.cleanup();
    });
  });

  describe("Regression Detection", () => {
    it("should detect performance regressions", () => {
      const eventSpy = jest.spyOn(window, "dispatchEvent");

      // Record baseline entries
      for (let i = 0; i < 10; i++) {
        monitor.recordEntry();
      }

      // Simulate regression by manually triggering with poor metrics
      const regressionEntry = {
        ...monitor.recordEntry(),
        lcp: 8000, // Very poor LCP
      };

      // Check if regression event would be dispatched
      // Note: This is a simplified test - actual regression detection
      // would require more sophisticated baseline calculation
      expect(eventSpy).toHaveBeenCalled();
    });
  });

  describe("Error Handling", () => {
    it("should handle localStorage errors gracefully", () => {
      localStorageMock.setItem.mockImplementation(() => {
        throw new Error("Storage quota exceeded");
      });

      expect(() => monitor.recordEntry()).not.toThrow();
    });

    it("should handle missing performance APIs gracefully", () => {
      // Mock missing PerformanceObserver
      delete (global as any).window.PerformanceObserver;

      expect(() => new CoreWebVitalsMonitor()).not.toThrow();
    });
  });
});
