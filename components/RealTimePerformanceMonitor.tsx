/**
 * Real-time Performance Monitor Component
 * Lightweight component for embedding performance metrics in other pages
 */

"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Eye,
  Gauge,
  Minimize2,
  Maximize2,
  Zap,
} from "lucide-react";
import { usePerformanceMonitoring } from "@/lib/hooks/usePerformanceMonitoring";

interface CompactMetricProps {
  label: string;
  value: number;
  budget: number;
  unit: string;
  icon: React.ReactNode;
}

const CompactMetric: React.FC<CompactMetricProps> = ({
  label,
  value,
  budget,
  unit,
  icon,
}) => {
  const percentage = budget > 0 ? (value / budget) * 100 : 0;
  const status =
    percentage > 100 ? "critical" : percentage > 80 ? "warning" : "good";

  const formatValue = (val: number) => {
    if (unit === "ms") return `${Math.round(val)}ms`;
    if (unit === "KB") return `${Math.round(val / 1024)}KB`;
    if (unit === "score") return val.toFixed(3);
    return val.toString();
  };

  return (
    <div className="flex items-center space-x-2">
      <div
        className={`p-1 rounded ${
          status === "critical"
            ? "bg-red-100 text-red-600"
            : status === "warning"
            ? "bg-yellow-100 text-yellow-600"
            : "bg-green-100 text-green-600"
        }`}
      >
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xs text-muted-foreground truncate">{label}</div>
        <div className="text-sm font-medium">{formatValue(value)}</div>
      </div>
      <Badge
        variant={
          status === "critical"
            ? "destructive"
            : status === "warning"
            ? "secondary"
            : "default"
        }
        className="text-xs"
      >
        {percentage.toFixed(0)}%
      </Badge>
    </div>
  );
};

interface RealTimePerformanceMonitorProps {
  compact?: boolean;
  showScore?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const RealTimePerformanceMonitor: React.FC<
  RealTimePerformanceMonitorProps
> = ({
  compact = false,
  showScore = true,
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
}) => {
  const {
    currentMetrics,
    budgetValidation,
    isLoading,
    error,
    lastUpdated,
    refreshMetrics,
  } = usePerformanceMonitoring();

  const [isExpanded, setIsExpanded] = useState(!compact);
  const [isAutoRefreshing, setIsAutoRefreshing] = useState(autoRefresh);

  // Auto-refresh functionality
  useEffect(() => {
    if (!isAutoRefreshing) return;

    const interval = setInterval(() => {
      refreshMetrics();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [isAutoRefreshing, refreshInterval, refreshMetrics]);

  // Real-time metric updates
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible" && isAutoRefreshing) {
        refreshMetrics();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [isAutoRefreshing, refreshMetrics]);

  const getOverallStatus = () => {
    if (!budgetValidation) return "unknown";

    const criticalViolations = budgetValidation.violations.filter(
      (v) => v.severity === "critical"
    ).length;
    const warningViolations = budgetValidation.violations.filter(
      (v) => v.severity === "warning"
    ).length;

    if (criticalViolations > 0) return "critical";
    if (warningViolations > 0) return "warning";
    return "good";
  };

  const status = getOverallStatus();

  if (compact && !isExpanded) {
    return (
      <Card
        className={`w-fit ${
          status === "critical"
            ? "border-red-500"
            : status === "warning"
            ? "border-yellow-500"
            : status === "good"
            ? "border-green-500"
            : "border-gray-300"
        }`}
      >
        <CardContent className="p-3">
          <div className="flex items-center space-x-3">
            <div
              className={`p-2 rounded-full ${
                status === "critical"
                  ? "bg-red-100 text-red-600"
                  : status === "warning"
                  ? "bg-yellow-100 text-yellow-600"
                  : status === "good"
                  ? "bg-green-100 text-green-600"
                  : "bg-gray-100 text-gray-600"
              }`}
            >
              {status === "critical" ? (
                <AlertTriangle className="w-4 h-4" />
              ) : status === "warning" ? (
                <AlertTriangle className="w-4 h-4" />
              ) : status === "good" ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <Activity className="w-4 h-4" />
              )}
            </div>

            <div>
              <div className="text-sm font-medium">
                Performance: {budgetValidation?.score || 0}/100
              </div>
              <div className="text-xs text-muted-foreground">
                {lastUpdated
                  ? `Updated ${lastUpdated.toLocaleTimeString()}`
                  : "No data"}
              </div>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(true)}
            >
              <Maximize2 className="w-4 h-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      className={`${
        status === "critical"
          ? "border-red-500"
          : status === "warning"
          ? "border-yellow-500"
          : status === "good"
          ? "border-green-500"
          : "border-gray-300"
      }`}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <div
              className={`p-2 rounded-full ${
                status === "critical"
                  ? "bg-red-100 text-red-600"
                  : status === "warning"
                  ? "bg-yellow-100 text-yellow-600"
                  : status === "good"
                  ? "bg-green-100 text-green-600"
                  : "bg-gray-100 text-gray-600"
              }`}
            >
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-medium">Performance Monitor</h3>
              <p className="text-xs text-muted-foreground">
                {lastUpdated
                  ? `Updated ${lastUpdated.toLocaleTimeString()}`
                  : "No data available"}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {showScore && budgetValidation && (
              <Badge
                variant={
                  budgetValidation.score >= 90
                    ? "default"
                    : budgetValidation.score >= 70
                    ? "secondary"
                    : "destructive"
                }
              >
                {budgetValidation.score}/100
              </Badge>
            )}

            {compact && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(false)}
              >
                <Minimize2 className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-4 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="text-center py-4 text-sm text-muted-foreground">
            Loading performance data...
          </div>
        ) : (
          <div className="space-y-3">
            <CompactMetric
              label="Largest Contentful Paint"
              value={currentMetrics.lcp || 0}
              budget={2500}
              unit="ms"
              icon={<Eye className="w-3 h-3" />}
            />

            <CompactMetric
              label="First Input Delay"
              value={currentMetrics.fid || 0}
              budget={100}
              unit="ms"
              icon={<Zap className="w-3 h-3" />}
            />

            <CompactMetric
              label="Cumulative Layout Shift"
              value={currentMetrics.cls || 0}
              budget={0.1}
              unit="score"
              icon={<Activity className="w-3 h-3" />}
            />

            <CompactMetric
              label="First Contentful Paint"
              value={currentMetrics.fcp || 0}
              budget={1800}
              unit="ms"
              icon={<Gauge className="w-3 h-3" />}
            />
          </div>
        )}

        {budgetValidation && budgetValidation.violations.length > 0 && (
          <div className="mt-4 pt-3 border-t">
            <div className="text-xs text-muted-foreground mb-2">
              {budgetValidation.violations.length} budget violation(s)
            </div>
            <div className="space-y-1">
              {budgetValidation.violations
                .slice(0, 3)
                .map((violation, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between text-xs"
                  >
                    <span className="text-muted-foreground">
                      {violation.metric.toUpperCase()}
                    </span>
                    <Badge
                      variant={
                        violation.severity === "critical"
                          ? "destructive"
                          : "secondary"
                      }
                      className="text-xs"
                    >
                      {violation.severity}
                    </Badge>
                  </div>
                ))}
              {budgetValidation.violations.length > 3 && (
                <div className="text-xs text-muted-foreground">
                  +{budgetValidation.violations.length - 3} more
                </div>
              )}
            </div>
          </div>
        )}

        <div className="mt-4 pt-3 border-t flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={refreshMetrics}
              disabled={isLoading}
            >
              Refresh
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsAutoRefreshing(!isAutoRefreshing)}
              className={isAutoRefreshing ? "text-green-600" : "text-gray-600"}
            >
              Auto: {isAutoRefreshing ? "ON" : "OFF"}
            </Button>
          </div>

          <div className="text-xs text-muted-foreground">
            {isAutoRefreshing && `Refreshes every ${refreshInterval / 1000}s`}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

// Hook for embedding performance status in other components
export function usePerformanceStatus() {
  const { budgetValidation, currentMetrics, lastUpdated } =
    usePerformanceMonitoring();

  const getStatus = () => {
    if (!budgetValidation) return "unknown";

    const criticalViolations = budgetValidation.violations.filter(
      (v) => v.severity === "critical"
    ).length;
    const warningViolations = budgetValidation.violations.filter(
      (v) => v.severity === "warning"
    ).length;

    if (criticalViolations > 0) return "critical";
    if (warningViolations > 0) return "warning";
    return "good";
  };

  return {
    status: getStatus(),
    score: budgetValidation?.score || 0,
    violations: budgetValidation?.violations || [],
    metrics: currentMetrics,
    lastUpdated,
    hasData: Object.keys(currentMetrics).length > 0,
  };
}
