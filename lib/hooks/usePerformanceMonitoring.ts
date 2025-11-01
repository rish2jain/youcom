/**
 * React hook for performance monitoring integration
 * Provides real-time performance metrics and budget validation
 */

import { useEffect, useState, useCallback } from "react";
import {
  coreWebVitalsMonitor,
  CoreWebVitalsEntry,
  PerformanceTrend,
  RegressionAlert,
} from "../core-web-vitals-monitor";
import {
  performanceMonitor,
  BudgetValidationResult,
  PerformanceMetrics,
} from "../performance-monitor";
import { performanceBudgetManager } from "../performance-budgets";

export interface PerformanceState {
  currentMetrics: Partial<CoreWebVitalsEntry>;
  budgetValidation: BudgetValidationResult | null;
  trends: PerformanceTrend[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export interface PerformanceActions {
  recordEntry: () => CoreWebVitalsEntry;
  validateBudgets: () => Promise<BudgetValidationResult>;
  refreshMetrics: () => Promise<void>;
  exportData: (format?: "json" | "csv") => string;
  clearData: () => void;
}

export function usePerformanceMonitoring(): PerformanceState &
  PerformanceActions {
  const [state, setState] = useState<PerformanceState>({
    currentMetrics: {},
    budgetValidation: null,
    trends: [],
    isLoading: true,
    error: null,
    lastUpdated: null,
  });

  const [regressionAlerts, setRegressionAlerts] = useState<RegressionAlert[]>(
    []
  );

  // Update metrics when Core Web Vitals change
  useEffect(() => {
    const handleMetricUpdate = (event: CustomEvent) => {
      const { metric, value, timestamp } = event.detail;

      setState((prev) => ({
        ...prev,
        currentMetrics: {
          ...prev.currentMetrics,
          [metric]: value,
        },
        lastUpdated: new Date(timestamp),
      }));
    };

    const handleRegressionAlert = (event: CustomEvent) => {
      const alert: RegressionAlert = event.detail;
      setRegressionAlerts((prev) => [...prev, alert]);

      // Update error state for critical regressions
      if (alert.severity === "critical") {
        setState((prev) => ({
          ...prev,
          error: `Critical performance regression detected in ${
            alert.metric
          }: ${alert.degradationPercent.toFixed(1)}% degradation`,
        }));
      }
    };

    window.addEventListener(
      "core-web-vitals-update",
      handleMetricUpdate as EventListener
    );
    window.addEventListener(
      "performance-regression",
      handleRegressionAlert as EventListener
    );

    return () => {
      window.removeEventListener(
        "core-web-vitals-update",
        handleMetricUpdate as EventListener
      );
      window.removeEventListener(
        "performance-regression",
        handleRegressionAlert as EventListener
      );
    };
  }, []);

  // Initialize performance monitoring
  useEffect(() => {
    const initializeMonitoring = async () => {
      try {
        setState((prev) => ({ ...prev, isLoading: true, error: null }));

        // Get initial metrics
        const currentMetrics = coreWebVitalsMonitor.getCurrentMetrics();
        const summary = coreWebVitalsMonitor.getPerformanceSummary();

        // Validate against budgets
        let budgetValidation: BudgetValidationResult | null = null;
        if (Object.keys(currentMetrics).length > 0) {
          budgetValidation = await performanceMonitor.validateBudgets();
        }

        setState((prev) => ({
          ...prev,
          currentMetrics,
          budgetValidation,
          trends: summary.trends,
          lastUpdated: summary.lastUpdated,
          isLoading: false,
        }));
      } catch (error) {
        setState((prev) => ({
          ...prev,
          error:
            error instanceof Error
              ? error.message
              : "Failed to initialize performance monitoring",
          isLoading: false,
        }));
      }
    };

    initializeMonitoring();
  }, []);

  // Record performance entry
  const recordEntry = useCallback((): CoreWebVitalsEntry => {
    try {
      const entry = coreWebVitalsMonitor.recordEntry();

      // Update state with new entry
      setState((prev) => ({
        ...prev,
        currentMetrics: {
          lcp: entry.lcp,
          fid: entry.fid,
          cls: entry.cls,
          fcp: entry.fcp,
          ttfb: entry.ttfb,
        },
        lastUpdated: entry.timestamp,
        error: null,
      }));

      return entry;
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error:
          error instanceof Error
            ? error.message
            : "Failed to record performance entry",
      }));
      throw error;
    }
  }, []);

  // Validate performance budgets
  const validateBudgets =
    useCallback(async (): Promise<BudgetValidationResult> => {
      try {
        const result = await performanceMonitor.validateBudgets();

        setState((prev) => ({
          ...prev,
          budgetValidation: result,
          error: result.passed
            ? null
            : `Performance budget violations detected: ${result.violations.length} issues`,
        }));

        return result;
      } catch (error) {
        const errorMessage =
          error instanceof Error
            ? error.message
            : "Failed to validate performance budgets";
        setState((prev) => ({
          ...prev,
          error: errorMessage,
        }));
        throw error;
      }
    }, []);

  // Refresh all metrics
  const refreshMetrics = useCallback(async (): Promise<void> => {
    try {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      // Get fresh metrics
      const currentMetrics = coreWebVitalsMonitor.getCurrentMetrics();
      const summary = coreWebVitalsMonitor.getPerformanceSummary();

      // Validate budgets if we have metrics
      let budgetValidation: BudgetValidationResult | null = null;
      if (Object.keys(currentMetrics).length > 0) {
        budgetValidation = await performanceMonitor.validateBudgets();
      }

      setState((prev) => ({
        ...prev,
        currentMetrics,
        budgetValidation,
        trends: summary.trends,
        lastUpdated: summary.lastUpdated,
        isLoading: false,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error:
          error instanceof Error
            ? error.message
            : "Failed to refresh performance metrics",
        isLoading: false,
      }));
    }
  }, []);

  // Export performance data
  const exportData = useCallback((format: "json" | "csv" = "json"): string => {
    try {
      return coreWebVitalsMonitor.exportData(format);
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error:
          error instanceof Error
            ? error.message
            : "Failed to export performance data",
      }));
      return "";
    }
  }, []);

  // Clear performance data
  const clearData = useCallback((): void => {
    try {
      coreWebVitalsMonitor.clearData();
      setRegressionAlerts([]);

      setState((prev) => ({
        ...prev,
        currentMetrics: {},
        budgetValidation: null,
        trends: [],
        lastUpdated: null,
        error: null,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error:
          error instanceof Error
            ? error.message
            : "Failed to clear performance data",
      }));
    }
  }, []);

  return {
    ...state,
    recordEntry,
    validateBudgets,
    refreshMetrics,
    exportData,
    clearData,
  };
}

// Define proper types for budget monitoring
interface Budget {
  maxBundleSize: number;
  maxLCP: number;
  maxFID: number;
  maxCLS: number;
  maxFCP: number;
  maxTTFB: number;
}

interface Violation {
  metric: string;
  actual: number;
  budget: number;
  severity: "critical" | "warning";
}

interface Alert {
  id: string;
  timestamp: Date;
  environment: "development" | "staging" | "production";
  violations: Violation[];
  severity: "warning" | "critical";
  resolved: boolean;
}

// Hook for performance budget monitoring specifically
export function usePerformanceBudgets(
  environment: "development" | "staging" | "production" = "production"
) {
  const [budgetState, setBudgetState] = useState<{
    budget: Budget | null;
    violations: Violation[];
    alerts: Alert[];
    isLoading: boolean;
    error: string | null;
  }>({
    budget: null,
    violations: [],
    alerts: [],
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    const loadBudgetData = async () => {
      try {
        setBudgetState((prev) => ({ ...prev, isLoading: true, error: null }));

        const budget = performanceBudgetManager.getBudget(environment);
        const alerts = performanceBudgetManager.getUnresolvedAlerts();

        setBudgetState((prev) => ({
          ...prev,
          budget,
          alerts,
          isLoading: false,
        }));
      } catch (error) {
        setBudgetState((prev) => ({
          ...prev,
          error:
            error instanceof Error
              ? error.message
              : "Failed to load budget data",
          isLoading: false,
        }));
      }
    };

    loadBudgetData();
  }, [environment]);

  // Using PerformanceMetrics from performance-monitor module

  const validateBudget = useCallback(
    async (metrics: PerformanceMetrics) => {
      try {
        const flatMetrics = {
          bundleSize: metrics.bundleSize,
          loadTime: metrics.loadTime,
          lcp: metrics.coreWebVitals?.lcp || 0,
          fid: metrics.coreWebVitals?.fid || 0,
          cls: metrics.coreWebVitals?.cls || 0,
          fcp: metrics.coreWebVitals?.fcp || 0,
          ttfb: metrics.coreWebVitals?.ttfb || 0,
        };

        const result = await performanceBudgetManager.validateBudget(
          flatMetrics,
          environment
        );

        setBudgetState((prev) => ({
          ...prev,
          violations: result.violations,
          error: result.passed
            ? null
            : `Budget violations detected: ${result.violations.length} issues`,
        }));

        return result;
      } catch (error) {
        setBudgetState((prev) => ({
          ...prev,
          error:
            error instanceof Error
              ? error.message
              : "Failed to validate budget",
        }));
        throw error;
      }
    },
    [environment]
  );

  const resolveAlert = useCallback((alertId: string) => {
    performanceBudgetManager.resolveAlert(alertId);
    setBudgetState((prev) => ({
      ...prev,
      alerts: prev.alerts.filter((alert) => alert.id !== alertId),
    }));
  }, []);

  return {
    ...budgetState,
    validateBudget,
    resolveAlert,
  };
}

// Hook for performance regression monitoring
export function usePerformanceRegression() {
  const [regressions, setRegressions] = useState<RegressionAlert[]>([]);

  useEffect(() => {
    const handleRegressionAlert = (event: CustomEvent) => {
      const alert: RegressionAlert = event.detail;
      setRegressions((prev) => [...prev, alert]);
    };

    window.addEventListener(
      "performance-regression",
      handleRegressionAlert as EventListener
    );

    return () => {
      window.removeEventListener(
        "performance-regression",
        handleRegressionAlert as EventListener
      );
    };
  }, []);

  const resolveRegression = useCallback((alertId: string) => {
    setRegressions((prev) =>
      prev.map((alert) =>
        alert.id === alertId ? { ...alert, resolved: true } : alert
      )
    );
  }, []);

  const clearResolvedRegressions = useCallback(() => {
    setRegressions((prev) => prev.filter((alert) => !alert.resolved));
  }, []);

  return {
    regressions: regressions.filter((alert) => !alert.resolved),
    allRegressions: regressions,
    resolveRegression,
    clearResolvedRegressions,
  };
}
