/**
 * Enhanced Core Web Vitals monitoring with regression detection and alerting
 * Implements comprehensive performance tracking and trend analysis
 */

// Performance budget integration available if needed
// import { performanceBudgetManager } from "./performance-budgets";

export interface CoreWebVitalsEntry {
  id: string;
  timestamp: Date;
  url: string;
  lcp: number;
  fid: number;
  cls: number;
  fcp: number;
  ttfb: number;
  userAgent: string;
  connectionType?: string;
  deviceMemory?: number;
  sessionId: string;
}

export interface PerformanceTrend {
  metric: string;
  current: number;
  previous: number;
  change: number;
  changePercent: number;
  trend: "improving" | "degrading" | "stable";
  significance: "low" | "medium" | "high";
}

export interface RegressionAlert {
  id: string;
  timestamp: Date;
  metric: string;
  currentValue: number;
  baselineValue: number;
  degradationPercent: number;
  severity: "warning" | "critical";
  resolved: boolean;
}

export class CoreWebVitalsMonitor {
  private entries: CoreWebVitalsEntry[] = [];
  private observers: Map<string, PerformanceObserver> = new Map();
  private sessionId: string;
  private currentMetrics: Partial<CoreWebVitalsEntry> = {};
  private readonly STORAGE_KEY = "core-web-vitals-entries";
  private readonly MAX_ENTRIES = 1000; // Keep last 1000 entries
  private readonly REGRESSION_THRESHOLD = 20; // 20% degradation threshold

  constructor() {
    this.sessionId = this.generateSessionId();
    this.loadEntries();
    this.initializeObservers();
    this.setupBeforeUnload();
  }

  /**
   * Initialize performance observers for real-time monitoring
   */
  private initializeObservers(): void {
    if (typeof window === "undefined") return;

    // Enhanced LCP Observer with better tracking
    if ("PerformanceObserver" in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1] as any;
          if (lastEntry) {
            this.currentMetrics.lcp = lastEntry.startTime;
            this.emitMetricUpdate("lcp", lastEntry.startTime);
          }
        });
        lcpObserver.observe({ entryTypes: ["largest-contentful-paint"] });
        this.observers.set("lcp", lcpObserver);
      } catch (e) {
        console.warn("LCP observer not supported:", e);
      }

      // Enhanced FID Observer
      try {
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            const fidValue = entry.processingStart - entry.startTime;
            this.currentMetrics.fid = fidValue;
            this.emitMetricUpdate("fid", fidValue);
          });
        });
        fidObserver.observe({ entryTypes: ["first-input"] });
        this.observers.set("fid", fidObserver);
      } catch (e) {
        console.warn("FID observer not supported:", e);
      }

      // Enhanced CLS Observer with session tracking
      try {
        let clsValue = 0;
        const clsObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          });
          this.currentMetrics.cls = clsValue;
          this.emitMetricUpdate("cls", clsValue);
        });
        clsObserver.observe({ entryTypes: ["layout-shift"] });
        this.observers.set("cls", clsObserver);
      } catch (e) {
        console.warn("CLS observer not supported:", e);
      }

      // FCP Observer
      try {
        const fcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const fcpEntry = entries.find(
            (entry) => entry.name === "first-contentful-paint"
          );
          if (fcpEntry) {
            this.currentMetrics.fcp = fcpEntry.startTime;
            this.emitMetricUpdate("fcp", fcpEntry.startTime);
          }
        });
        fcpObserver.observe({ entryTypes: ["paint"] });
        this.observers.set("fcp", fcpObserver);
      } catch (e) {
        console.warn("FCP observer not supported:", e);
      }
    }

    // Measure TTFB immediately
    this.measureTTFB();
  }

  /**
   * Measure Time to First Byte
   */
  private measureTTFB(): void {
    if (typeof window === "undefined") return;

    const navigation = performance.getEntriesByType(
      "navigation"
    )[0] as PerformanceNavigationTiming;
    if (navigation) {
      const ttfb = navigation.responseStart - navigation.requestStart;
      this.currentMetrics.ttfb = ttfb;
      this.emitMetricUpdate("ttfb", ttfb);
    }
  }

  /**
   * Emit metric update event
   */
  private emitMetricUpdate(metric: string, value: number): void {
    const event = new CustomEvent("core-web-vitals-update", {
      detail: {
        metric,
        value,
        timestamp: Date.now(),
        sessionId: this.sessionId,
      },
    });
    window.dispatchEvent(event);
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;
  }

  /**
   * Get current Core Web Vitals snapshot
   */
  getCurrentMetrics(): Partial<CoreWebVitalsEntry> {
    return { ...this.currentMetrics };
  }

  /**
   * Record complete Core Web Vitals entry
   */
  recordEntry(): CoreWebVitalsEntry {
    const entry: CoreWebVitalsEntry = {
      id: `entry-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
      timestamp: new Date(),
      url: window.location.href,
      lcp: this.currentMetrics.lcp || 0,
      fid: this.currentMetrics.fid || 0,
      cls: this.currentMetrics.cls || 0,
      fcp: this.currentMetrics.fcp || 0,
      ttfb: this.currentMetrics.ttfb || 0,
      userAgent: navigator.userAgent,
      connectionType: this.getConnectionType(),
      deviceMemory: this.getDeviceMemory(),
      sessionId: this.sessionId,
    };

    this.entries.push(entry);
    this.trimEntries();
    this.saveEntries();

    // Check for regressions
    this.checkForRegressions(entry);

    return entry;
  }

  /**
   * Get connection type if available
   */
  private getConnectionType(): string | undefined {
    const connection =
      (navigator as any).connection ||
      (navigator as any).mozConnection ||
      (navigator as any).webkitConnection;
    return connection?.effectiveType;
  }

  /**
   * Get device memory if available
   */
  private getDeviceMemory(): number | undefined {
    return (navigator as any).deviceMemory;
  }

  /**
   * Check for performance regressions
   */
  private checkForRegressions(currentEntry: CoreWebVitalsEntry): void {
    const baseline = this.calculateBaseline();
    if (!baseline) return;

    const metrics = ["lcp", "fid", "cls", "fcp", "ttfb"] as const;

    metrics.forEach((metric) => {
      const currentValue = currentEntry[metric];
      const baselineValue = baseline[metric];

      if (
        currentValue > 0 &&
        baselineValue !== undefined &&
        baselineValue > 0
      ) {
        const degradationPercent =
          ((currentValue - baselineValue) / baselineValue) * 100;

        if (degradationPercent > this.REGRESSION_THRESHOLD) {
          this.createRegressionAlert(
            metric,
            currentValue,
            baselineValue,
            degradationPercent
          );
        }
      }
    });
  }

  /**
   * Calculate performance baseline from recent entries
   */
  private calculateBaseline(): Partial<CoreWebVitalsEntry> | null {
    const recentEntries = this.entries
      .filter((entry) => {
        const dayAgo = new Date();
        dayAgo.setDate(dayAgo.getDate() - 1);
        return entry.timestamp >= dayAgo;
      })
      .slice(-20); // Last 20 entries

    if (recentEntries.length < 5) return null;

    const baseline: Partial<CoreWebVitalsEntry> = {};
    const metrics = ["lcp", "fid", "cls", "fcp", "ttfb"] as const;

    metrics.forEach((metric) => {
      const values = recentEntries
        .map((entry) => entry[metric])
        .filter((value) => value > 0)
        .sort((a, b) => a - b);

      if (values.length > 0) {
        // Use 75th percentile as baseline
        const p75Index = Math.floor(values.length * 0.75);
        baseline[metric] = values[p75Index];
      }
    });

    return baseline;
  }

  /**
   * Create regression alert
   */
  private createRegressionAlert(
    metric: string,
    currentValue: number,
    baselineValue: number,
    degradationPercent: number
  ): void {
    const severity = degradationPercent > 50 ? "critical" : "warning";

    const alert: RegressionAlert = {
      id: `regression-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
      timestamp: new Date(),
      metric,
      currentValue,
      baselineValue,
      degradationPercent,
      severity,
      resolved: false,
    };

    // Emit regression alert event
    const event = new CustomEvent("performance-regression", {
      detail: alert,
    });
    window.dispatchEvent(event);

    console.warn(
      `Performance regression detected: ${metric} degraded by ${degradationPercent.toFixed(
        1
      )}%`,
      alert
    );
  }

  /**
   * Analyze performance trends
   */
  analyzeTrends(days: number = 7): PerformanceTrend[] {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);

    const recentEntries = this.entries.filter(
      (entry) => entry.timestamp >= cutoff
    );
    if (recentEntries.length < 10) return [];

    const midpoint = Math.floor(recentEntries.length / 2);
    const earlierEntries = recentEntries.slice(0, midpoint);
    const laterEntries = recentEntries.slice(midpoint);

    const trends: PerformanceTrend[] = [];
    const metrics = ["lcp", "fid", "cls", "fcp", "ttfb"] as const;

    metrics.forEach((metric) => {
      const earlierAvg = this.calculateAverage(earlierEntries, metric);
      const laterAvg = this.calculateAverage(laterEntries, metric);

      if (earlierAvg > 0 && laterAvg > 0) {
        const change = laterAvg - earlierAvg;
        const changePercent = (change / earlierAvg) * 100;

        let trend: PerformanceTrend["trend"] = "stable";
        let significance: PerformanceTrend["significance"] = "low";

        if (Math.abs(changePercent) > 5) {
          trend = changePercent < 0 ? "improving" : "degrading";
          significance = Math.abs(changePercent) > 20 ? "high" : "medium";
        }

        trends.push({
          metric,
          current: laterAvg,
          previous: earlierAvg,
          change,
          changePercent,
          trend,
          significance,
        });
      }
    });

    return trends;
  }

  /**
   * Calculate average for a metric across entries
   */
  private calculateAverage(
    entries: CoreWebVitalsEntry[],
    metric: keyof CoreWebVitalsEntry
  ): number {
    const values = entries
      .map((entry) => entry[metric] as number)
      .filter((value) => typeof value === "number" && value > 0);

    return values.length > 0
      ? values.reduce((sum, value) => sum + value, 0) / values.length
      : 0;
  }

  /**
   * Get performance summary for dashboard
   */
  getPerformanceSummary(): {
    current: Partial<CoreWebVitalsEntry>;
    trends: PerformanceTrend[];
    totalEntries: number;
    sessionCount: number;
    lastUpdated: Date | null;
  } {
    const uniqueSessions = new Set(this.entries.map((entry) => entry.sessionId))
      .size;
    const lastEntry = this.entries[this.entries.length - 1];

    return {
      current: this.getCurrentMetrics(),
      trends: this.analyzeTrends(),
      totalEntries: this.entries.length,
      sessionCount: uniqueSessions,
      lastUpdated: lastEntry ? lastEntry.timestamp : null,
    };
  }

  /**
   * Export performance data for analysis
   */
  exportData(format: "json" | "csv" = "json"): string {
    if (format === "csv") {
      const headers = [
        "timestamp",
        "url",
        "lcp",
        "fid",
        "cls",
        "fcp",
        "ttfb",
        "sessionId",
      ];
      const rows = this.entries.map((entry) => [
        entry.timestamp.toISOString(),
        entry.url,
        entry.lcp,
        entry.fid,
        entry.cls,
        entry.fcp,
        entry.ttfb,
        entry.sessionId,
      ]);

      return [headers, ...rows].map((row) => row.join(",")).join("\n");
    }

    return JSON.stringify(this.entries, null, 2);
  }

  /**
   * Setup beforeunload handler to record final metrics
   */
  private setupBeforeUnload(): void {
    if (typeof window === "undefined") return;

    window.addEventListener("beforeunload", () => {
      this.recordEntry();
    });

    // Also record on visibility change (tab switching)
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") {
        this.recordEntry();
      }
    });
  }

  /**
   * Trim entries to maintain storage limits
   */
  private trimEntries(): void {
    if (this.entries.length > this.MAX_ENTRIES) {
      this.entries = this.entries.slice(-this.MAX_ENTRIES);
    }
  }

  /**
   * Load entries from storage
   */
  private loadEntries(): void {
    if (typeof window === "undefined") return;

    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        this.entries = parsed.map((entry: any) => ({
          ...entry,
          timestamp: new Date(entry.timestamp),
        }));
      }
    } catch (error) {
      console.warn("Failed to load Core Web Vitals entries:", error);
    }
  }

  /**
   * Save entries to storage
   */
  private saveEntries(): void {
    if (typeof window === "undefined") return;

    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.entries));
    } catch (error) {
      console.warn("Failed to save Core Web Vitals entries:", error);
    }
  }

  /**
   * Clear all stored data
   */
  clearData(): void {
    this.entries = [];
    this.currentMetrics = {};
    if (typeof window !== "undefined") {
      localStorage.removeItem(this.STORAGE_KEY);
    }
  }

  /**
   * Cleanup observers and event listeners
   */
  cleanup(): void {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers.clear();
  }
}

// Global Core Web Vitals monitor instance
export const coreWebVitalsMonitor = new CoreWebVitalsMonitor();

// React hook for Core Web Vitals monitoring
export function useCoreWebVitalsMonitoring() {
  if (typeof window === "undefined") return null;

  return {
    getCurrentMetrics: () => coreWebVitalsMonitor.getCurrentMetrics(),
    recordEntry: () => coreWebVitalsMonitor.recordEntry(),
    analyzeTrends: (days?: number) => coreWebVitalsMonitor.analyzeTrends(days),
    getPerformanceSummary: () => coreWebVitalsMonitor.getPerformanceSummary(),
    exportData: (format?: "json" | "csv") =>
      coreWebVitalsMonitor.exportData(format),
    clearData: () => coreWebVitalsMonitor.clearData(),
  };
}
