/**
 * Performance monitoring and measurement tools
 * Implements Core Web Vitals tracking and performance budget validation
 */

export interface CoreWebVitals {
  lcp: number; // Largest Contentful Paint
  fid: number; // First Input Delay
  cls: number; // Cumulative Layout Shift
  fcp: number; // First Contentful Paint
  ttfb: number; // Time to First Byte
}

export interface PerformanceBudget {
  maxBundleSize: number; // bytes
  maxInitialLoadTime: number; // milliseconds
  maxLCP: number; // milliseconds
  maxFID: number; // milliseconds
  maxCLS: number; // score
  maxFCP: number; // milliseconds
  maxTTFB: number; // milliseconds
}

export interface PerformanceMetrics {
  bundleSize: number;
  loadTime: number;
  coreWebVitals: CoreWebVitals;
  timestamp: Date;
  url: string;
  userAgent: string;
}

export interface BudgetValidationResult {
  passed: boolean;
  violations: Array<{
    metric: string;
    actual: number;
    budget: number;
    severity: "critical" | "warning";
  }>;
  score: number; // 0-100
}

// Default performance budgets based on requirements
export const DEFAULT_PERFORMANCE_BUDGETS: PerformanceBudget = {
  maxBundleSize: 500000, // 500KB initial bundle (40% reduction target)
  maxInitialLoadTime: 3000, // 3 seconds
  maxLCP: 2500, // 2.5 seconds
  maxFID: 100, // 100ms
  maxCLS: 0.1, // 0.1 score
  maxFCP: 1800, // 1.8 seconds
  maxTTFB: 800, // 800ms
};

export class PerformanceMonitor {
  private metrics: PerformanceMetrics[] = [];
  private budgets: PerformanceBudget;
  private observers: Map<string, PerformanceObserver> = new Map();

  constructor(budgets: PerformanceBudget = DEFAULT_PERFORMANCE_BUDGETS) {
    this.budgets = budgets;
    this.initializeObservers();
  }

  /**
   * Initialize performance observers for Core Web Vitals
   */
  private initializeObservers(): void {
    if (typeof window === "undefined") return;

    // LCP Observer
    if ("PerformanceObserver" in window) {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1] as any;
        if (lastEntry) {
          this.recordMetric("lcp", lastEntry.startTime);
        }
      });

      try {
        lcpObserver.observe({ entryTypes: ["largest-contentful-paint"] });
        this.observers.set("lcp", lcpObserver);
      } catch (e) {
        console.warn("LCP observer not supported");
      }

      // FID Observer
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          this.recordMetric("fid", entry.processingStart - entry.startTime);
        });
      });

      try {
        fidObserver.observe({ entryTypes: ["first-input"] });
        this.observers.set("fid", fidObserver);
      } catch (e) {
        console.warn("FID observer not supported");
      }

      // CLS Observer
      const clsObserver = new PerformanceObserver((list) => {
        let clsValue = 0;
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        });
        this.recordMetric("cls", clsValue);
      });

      try {
        clsObserver.observe({ entryTypes: ["layout-shift"] });
        this.observers.set("cls", clsObserver);
      } catch (e) {
        console.warn("CLS observer not supported");
      }
    }
  }

  /**
   * Record a performance metric
   */
  private recordMetric(type: string, value: number): void {
    const event = new CustomEvent("performance-metric", {
      detail: { type, value, timestamp: Date.now() },
    });
    window.dispatchEvent(event);
  }

  /**
   * Measure Core Web Vitals
   */
  async measureCoreWebVitals(): Promise<CoreWebVitals> {
    if (typeof window === "undefined") {
      return {
        lcp: 0,
        fid: 0,
        cls: 0,
        fcp: 0,
        ttfb: 0,
      };
    }

    const navigation = performance.getEntriesByType(
      "navigation"
    )[0] as PerformanceNavigationTiming;
    const paint = performance.getEntriesByType("paint");

    const fcp =
      paint.find((entry) => entry.name === "first-contentful-paint")
        ?.startTime || 0;
    const ttfb = navigation?.responseStart - navigation?.requestStart || 0;

    // Get LCP from observer or fallback
    const lcpEntries = performance.getEntriesByType(
      "largest-contentful-paint"
    ) as any[];
    const lcp =
      lcpEntries.length > 0 ? lcpEntries[lcpEntries.length - 1].startTime : 0;

    // CLS and FID are collected via observers
    return {
      lcp,
      fid: 0, // Will be updated by observer
      cls: 0, // Will be updated by observer
      fcp,
      ttfb,
    };
  }

  /**
   * Measure bundle size (client-side estimation)
   */
  async measureBundleSize(): Promise<number> {
    if (typeof window === "undefined") return 0;

    try {
      const resources = performance.getEntriesByType(
        "resource"
      ) as PerformanceResourceTiming[];
      let totalSize = 0;

      resources.forEach((resource) => {
        if (
          resource.name.includes("/_next/static/") &&
          (resource.name.endsWith(".js") || resource.name.endsWith(".css"))
        ) {
          // Estimate size from transfer size or encoded body size
          totalSize += resource.transferSize || resource.encodedBodySize || 0;
        }
      });

      return totalSize;
    } catch (error) {
      console.warn("Failed to measure bundle size:", error);
      return 0;
    }
  }

  /**
   * Measure page load time
   */
  measurePageLoadTime(): number {
    if (typeof window === "undefined") return 0;

    const navigation = performance.getEntriesByType(
      "navigation"
    )[0] as PerformanceNavigationTiming;
    return navigation ? navigation.loadEventEnd - navigation.fetchStart : 0;
  }

  /**
   * Validate performance against budgets
   */
  async validateBudgets(): Promise<BudgetValidationResult> {
    const coreWebVitals = await this.measureCoreWebVitals();
    const bundleSize = await this.measureBundleSize();
    const loadTime = this.measurePageLoadTime();

    const violations: BudgetValidationResult["violations"] = [];

    // Check bundle size
    if (bundleSize > this.budgets.maxBundleSize) {
      violations.push({
        metric: "bundleSize",
        actual: bundleSize,
        budget: this.budgets.maxBundleSize,
        severity: "critical",
      });
    }

    // Check load time
    if (loadTime > this.budgets.maxInitialLoadTime) {
      violations.push({
        metric: "loadTime",
        actual: loadTime,
        budget: this.budgets.maxInitialLoadTime,
        severity: "critical",
      });
    }

    // Check Core Web Vitals
    if (coreWebVitals.lcp > this.budgets.maxLCP) {
      violations.push({
        metric: "lcp",
        actual: coreWebVitals.lcp,
        budget: this.budgets.maxLCP,
        severity: "critical",
      });
    }

    if (coreWebVitals.fid > this.budgets.maxFID) {
      violations.push({
        metric: "fid",
        actual: coreWebVitals.fid,
        budget: this.budgets.maxFID,
        severity: "warning",
      });
    }

    if (coreWebVitals.cls > this.budgets.maxCLS) {
      violations.push({
        metric: "cls",
        actual: coreWebVitals.cls,
        budget: this.budgets.maxCLS,
        severity: "critical",
      });
    }

    if (coreWebVitals.fcp > this.budgets.maxFCP) {
      violations.push({
        metric: "fcp",
        actual: coreWebVitals.fcp,
        budget: this.budgets.maxFCP,
        severity: "warning",
      });
    }

    if (coreWebVitals.ttfb > this.budgets.maxTTFB) {
      violations.push({
        metric: "ttfb",
        actual: coreWebVitals.ttfb,
        budget: this.budgets.maxTTFB,
        severity: "warning",
      });
    }

    // Calculate score (percentage of budgets passed)
    const totalChecks = 7;
    const passedChecks = totalChecks - violations.length;
    const score = Math.round((passedChecks / totalChecks) * 100);

    return {
      passed: violations.length === 0,
      violations,
      score,
    };
  }

  /**
   * Generate performance report
   */
  async generateReport(): Promise<{
    metrics: PerformanceMetrics;
    budgetValidation: BudgetValidationResult;
    recommendations: string[];
  }> {
    const coreWebVitals = await this.measureCoreWebVitals();
    const bundleSize = await this.measureBundleSize();
    const loadTime = this.measurePageLoadTime();

    const metrics: PerformanceMetrics = {
      bundleSize,
      loadTime,
      coreWebVitals,
      timestamp: new Date(),
      url: typeof window !== "undefined" ? window.location.href : "",
      userAgent: typeof navigator !== "undefined" ? navigator.userAgent : "",
    };

    const budgetValidation = await this.validateBudgets();
    const recommendations = this.generateRecommendations(budgetValidation);

    return {
      metrics,
      budgetValidation,
      recommendations,
    };
  }

  /**
   * Generate performance recommendations based on violations
   */
  private generateRecommendations(
    validation: BudgetValidationResult
  ): string[] {
    const recommendations: string[] = [];

    validation.violations.forEach((violation) => {
      switch (violation.metric) {
        case "bundleSize":
          recommendations.push(
            "Consider implementing code splitting and lazy loading to reduce initial bundle size"
          );
          break;
        case "loadTime":
          recommendations.push(
            "Optimize critical rendering path and implement resource preloading"
          );
          break;
        case "lcp":
          recommendations.push(
            "Optimize largest contentful paint by preloading critical images and reducing server response times"
          );
          break;
        case "fid":
          recommendations.push(
            "Reduce JavaScript execution time and break up long tasks"
          );
          break;
        case "cls":
          recommendations.push(
            "Set explicit dimensions for images and avoid inserting content above existing content"
          );
          break;
        case "fcp":
          recommendations.push(
            "Optimize first contentful paint by inlining critical CSS and reducing render-blocking resources"
          );
          break;
        case "ttfb":
          recommendations.push(
            "Improve server response times and consider using a CDN"
          );
          break;
      }
    });

    return recommendations;
  }

  /**
   * Cleanup observers
   */
  cleanup(): void {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers.clear();
  }
}

// Global performance monitor instance
export const performanceMonitor = new PerformanceMonitor();

// Utility function to track performance in React components
export function usePerformanceMonitoring() {
  if (typeof window === "undefined") return null;

  return {
    measureCoreWebVitals: () => performanceMonitor.measureCoreWebVitals(),
    validateBudgets: () => performanceMonitor.validateBudgets(),
    generateReport: () => performanceMonitor.generateReport(),
  };
}
