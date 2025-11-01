/**
 * Performance Validation Functions
 * Validates that performance optimizations meet specified targets
 */

// Performance validation functions
export function validateBundleSizeReduction(
  baselineSizeBytes: number,
  optimizedSizeBytes: number
): boolean {
  if (baselineSizeBytes <= 0 || optimizedSizeBytes <= 0) {
    throw new Error("Bundle sizes must be positive numbers");
  }

  const reduction =
    ((baselineSizeBytes - optimizedSizeBytes) / baselineSizeBytes) * 100;
  return reduction >= 40; // 40% reduction target
}

import { CORE_WEB_VITALS_THRESHOLDS } from "./perf-constants";

export function validateLoadTimes(metrics: {
  lcp: number;
  fcp: number;
  ttfb: number;
}): boolean {
  if (
    typeof metrics.lcp !== "number" ||
    typeof metrics.fcp !== "number" ||
    typeof metrics.ttfb !== "number"
  ) {
    throw new Error("Load time metrics must be numbers");
  }

  if (metrics.lcp <= 0 || metrics.fcp <= 0 || metrics.ttfb <= 0) {
    return false;
  }

  return (
    metrics.lcp <= CORE_WEB_VITALS_THRESHOLDS.LCP && // Use shared constant
    metrics.fcp <= CORE_WEB_VITALS_THRESHOLDS.FCP && // Use shared constant
    metrics.ttfb <= CORE_WEB_VITALS_THRESHOLDS.TTFB // Use shared constant
  );
}

export function validateCoreWebVitals(metrics: {
  lcp: number;
  fid: number;
  cls: number;
}): boolean {
  if (
    typeof metrics.lcp !== "number" ||
    typeof metrics.fid !== "number" ||
    typeof metrics.cls !== "number"
  ) {
    throw new Error("Core Web Vitals metrics must be numbers");
  }

  return (
    metrics.lcp <= CORE_WEB_VITALS_THRESHOLDS.LCP &&
    metrics.fid <= CORE_WEB_VITALS_THRESHOLDS.FID &&
    metrics.cls <= CORE_WEB_VITALS_THRESHOLDS.CLS
  );
}

interface PerformanceBudgets {
  initialBundle: number;
  totalBundle: number;
  loadTime: number;
  cacheHitRate: number;
}

import { PERFORMANCE_BUDGETS } from "./perf-constants";

export function validatePerformanceBudgets(
  actualMetrics: Partial<PerformanceBudgets>,
  budgetLimits: Partial<PerformanceBudgets> = {}
): boolean {
  const defaultBudgets: PerformanceBudgets = {
    initialBundle: PERFORMANCE_BUDGETS.INITIAL_BUNDLE_SIZE,
    totalBundle: PERFORMANCE_BUDGETS.TOTAL_BUNDLE_SIZE,
    loadTime: PERFORMANCE_BUDGETS.LOAD_TIME,
    cacheHitRate: PERFORMANCE_BUDGETS.CACHE_HIT_RATE,
  };

  const finalBudgets = { ...defaultBudgets, ...budgetLimits };
  const metrics = { ...defaultBudgets, ...actualMetrics };

  // Validate inputs
  Object.values(finalBudgets).forEach((value) => {
    if (typeof value !== "number" || value <= 0) {
      throw new Error("Budget values must be positive numbers");
    }
  });

  return (
    (metrics.initialBundle || 0) <= finalBudgets.initialBundle && // <= for size limits
    (metrics.totalBundle || 0) <= finalBudgets.totalBundle && // <= for size limits
    (metrics.loadTime || 0) <= finalBudgets.loadTime && // <= for time limits
    (metrics.cacheHitRate || 0) >= finalBudgets.cacheHitRate // >= for cache hit rate
  );
}

interface PerformanceMetrics {
  lcp: number;
  bundleSize: number;
}

export function validatePerformanceImprovements(
  beforeMetrics: PerformanceMetrics,
  afterMetrics: PerformanceMetrics
): boolean {
  // Validate inputs
  if (
    beforeMetrics.lcp <= 0 ||
    beforeMetrics.bundleSize <= 0 ||
    afterMetrics.lcp <= 0 ||
    afterMetrics.bundleSize <= 0
  ) {
    return false;
  }

  if (
    typeof beforeMetrics.lcp !== "number" ||
    typeof beforeMetrics.bundleSize !== "number" ||
    typeof afterMetrics.lcp !== "number" ||
    typeof afterMetrics.bundleSize !== "number"
  ) {
    throw new Error("Performance metrics must be numbers");
  }

  const lcpImprovement =
    ((beforeMetrics.lcp - afterMetrics.lcp) / beforeMetrics.lcp) * 100;
  const bundleSizeReduction =
    ((beforeMetrics.bundleSize - afterMetrics.bundleSize) /
      beforeMetrics.bundleSize) *
    100;

  return lcpImprovement >= 50 && bundleSizeReduction >= 50;
}

// Performance monitoring system validation
export async function validatePerformanceMonitoring(): Promise<boolean> {
  try {
    // Test that performance monitoring modules can be imported
    if (typeof window === "undefined") {
      // Server-side validation
      return true;
    }

    // Client-side validation using dynamic imports
    const [
      { coreWebVitalsMonitor },
      { performanceAlertingSystem },
      { performanceBudgetManager },
    ] = await Promise.all([
      import("./core-web-vitals-monitor"),
      import("./performance-alerting"),
      import("./performance-budgets"),
    ]);

    // Basic functionality checks
    const hasMonitor = typeof coreWebVitalsMonitor === "object";
    const hasAlerting = typeof performanceAlertingSystem === "object";
    const hasBudgets = typeof performanceBudgetManager === "object";

    return hasMonitor && hasAlerting && hasBudgets;
  } catch (error) {
    console.error("Performance monitoring validation failed:", error);
    return false;
  }
}

// Run all validations with actual data
export async function runAllPerformanceValidations(
  bundleSizes: { baseline: number; optimized: number },
  loadTimes: { lcp: number; fcp: number; ttfb: number },
  coreWebVitals: { lcp: number; fid: number; cls: number },
  beforeMetrics: { lcp: number; bundleSize: number },
  afterMetrics: { lcp: number; bundleSize: number },
  budgets?: Partial<PerformanceBudgets>
): Promise<{
  passed: boolean;
  results: Record<string, boolean>;
  score: number;
}> {
  const results = {
    bundleSizeReduction: validateBundleSizeReduction(
      bundleSizes.baseline,
      bundleSizes.optimized
    ),
    loadTimes: validateLoadTimes(loadTimes),
    coreWebVitals: validateCoreWebVitals(coreWebVitals),
    performanceBudgets: validatePerformanceBudgets(budgets || {}),
    performanceImprovements: validatePerformanceImprovements(
      beforeMetrics,
      afterMetrics
    ),
    performanceMonitoring: await validatePerformanceMonitoring(),
  };

  const passedTests = Object.values(results).filter(Boolean).length;
  const totalTests = Object.keys(results).length;
  const score = Math.round((passedTests / totalTests) * 100);
  const passed = score >= 80; // 80% pass rate required

  return { passed, results, score };
}

// Mock version for testing/demo purposes
export async function runMockPerformanceValidations(): Promise<{
  passed: boolean;
  results: Record<string, boolean>;
  score: number;
}> {
  return runAllPerformanceValidations(
    { baseline: 2 * 1024 * 1024, optimized: 1.2 * 1024 * 1024 },
    { lcp: 2200, fcp: 1500, ttfb: 600 },
    { lcp: 2400, fid: 80, cls: 0.08 },
    { lcp: 4000, bundleSize: 2 * 1024 * 1024 },
    { lcp: 2000, bundleSize: 1 * 1024 * 1024 }
  );
}

// Performance metrics calculation
export function calculatePerformanceMetrics(
  bundleSizes: { initial: number; total: number; baseline: number },
  performanceEntries: {
    lcp: number;
    fcp: number;
    ttfb: number;
    fid: number;
    cls: number;
  },
  cacheStats: { hits: number; total: number; averageLoadTime: number }
): {
  bundleSize: { initial: number; total: number; reduction: number };
  loadTimes: { lcp: number; fcp: number; ttfb: number };
  coreWebVitals: { lcp: number; fid: number; cls: number };
  cachePerformance: { hitRate: number; averageLoadTime: number };
} {
  const bundleReduction =
    bundleSizes.baseline > 0
      ? ((bundleSizes.baseline - bundleSizes.initial) / bundleSizes.baseline) *
        100
      : 0;

  const cacheHitRate =
    cacheStats.total > 0 ? (cacheStats.hits / cacheStats.total) * 100 : 0;

  return {
    bundleSize: {
      initial: bundleSizes.initial,
      total: bundleSizes.total,
      reduction: bundleReduction,
    },
    loadTimes: {
      lcp: performanceEntries.lcp,
      fcp: performanceEntries.fcp,
      ttfb: performanceEntries.ttfb,
    },
    coreWebVitals: {
      lcp: performanceEntries.lcp,
      fid: performanceEntries.fid,
      cls: performanceEntries.cls,
    },
    cachePerformance: {
      hitRate: cacheHitRate,
      averageLoadTime: cacheStats.averageLoadTime,
    },
  };
}

// Mock version for testing/demo purposes
export function getMockPerformanceMetrics(): {
  bundleSize: { initial: number; total: number; reduction: number };
  loadTimes: { lcp: number; fcp: number; ttfb: number };
  coreWebVitals: { lcp: number; fid: number; cls: number };
  cachePerformance: { hitRate: number; averageLoadTime: number };
} {
  return {
    bundleSize: {
      initial: 800 * 1024, // 800KB
      total: 1.2 * 1024 * 1024, // 1.2MB
      reduction: 40, // 40% reduction
    },
    loadTimes: {
      lcp: 2200, // 2.2 seconds
      fcp: 1500, // 1.5 seconds
      ttfb: 600, // 600ms
    },
    coreWebVitals: {
      lcp: 2400, // 2.4 seconds
      fid: 80, // 80ms
      cls: 0.08, // 0.08 score
    },
    cachePerformance: {
      hitRate: 85, // 85%
      averageLoadTime: 150, // 150ms
    },
  };
}

// Performance optimization recommendations
export function getPerformanceRecommendations(
  metrics: ReturnType<typeof calculatePerformanceMetrics>
): string[] {
  const recommendations: string[] = [];

  if (metrics.bundleSize.initial > 1024 * 1024) {
    recommendations.push(
      "Reduce initial bundle size through code splitting and tree shaking"
    );
  }

  if (metrics.loadTimes.lcp > 2500) {
    recommendations.push(
      "Optimize Largest Contentful Paint by reducing server response times"
    );
  }

  if (metrics.coreWebVitals.fid > 100) {
    recommendations.push(
      "Improve First Input Delay by optimizing JavaScript execution"
    );
  }

  if (metrics.coreWebVitals.cls > 0.1) {
    recommendations.push(
      "Reduce Cumulative Layout Shift by setting explicit dimensions"
    );
  }

  if (metrics.cachePerformance.hitRate < 80) {
    recommendations.push(
      "Improve cache hit rate through better caching strategies"
    );
  }

  if (recommendations.length === 0) {
    recommendations.push(
      "All performance targets met! Continue monitoring for regressions."
    );
  }

  return recommendations;
}
