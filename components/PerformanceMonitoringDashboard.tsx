/**
 * Performance Monitoring Dashboard
 * Displays Core Web Vitals, budget compliance, trends, and optimization recommendations
 */

"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  Eye,
  Gauge,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";
import {
  usePerformanceMonitoring,
  usePerformanceBudgets,
  usePerformanceRegression,
} from "@/lib/hooks/usePerformanceMonitoring";

interface MetricCardProps {
  title: string;
  value: number;
  budget: number;
  unit: string;
  icon: React.ReactNode;
  trend?: {
    direction: "up" | "down" | "stable";
    value: number;
  };
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  budget,
  unit,
  icon,
  trend,
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
    <Card
      className={`${
        status === "critical"
          ? "border-red-500 bg-red-50"
          : status === "warning"
          ? "border-yellow-500 bg-yellow-50"
          : "border-green-500 bg-green-50"
      }`}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{formatValue(value)}</div>
        <div className="text-xs text-muted-foreground">
          Budget: {formatValue(budget)}
        </div>
        <Progress
          value={Math.min(percentage, 100)}
          className={`mt-2 ${
            status === "critical"
              ? "bg-red-200"
              : status === "warning"
              ? "bg-yellow-200"
              : "bg-green-200"
          }`}
        />
        <div className="flex items-center justify-between mt-2">
          <Badge
            variant={
              status === "critical"
                ? "destructive"
                : status === "warning"
                ? "secondary"
                : "default"
            }
          >
            {percentage.toFixed(1)}% of budget
          </Badge>
          {trend && (
            <div
              className={`flex items-center text-xs ${
                trend.direction === "up"
                  ? "text-red-600"
                  : trend.direction === "down"
                  ? "text-green-600"
                  : "text-gray-600"
              }`}
            >
              {trend.direction === "up" ? (
                <TrendingUp className="w-3 h-3 mr-1" />
              ) : trend.direction === "down" ? (
                <TrendingDown className="w-3 h-3 mr-1" />
              ) : (
                <Activity className="w-3 h-3 mr-1" />
              )}
              {trend.value.toFixed(1)}%
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

interface TrendChartProps {
  data: Array<{
    timestamp: string;
    lcp: number;
    fid: number;
    cls: number;
    fcp: number;
    ttfb: number;
  }>;
}

const TrendChart: React.FC<TrendChartProps> = ({ data }) => {
  // Simple trend visualization - in a real app you'd use a charting library
  const [selectedMetric, setSelectedMetric] = useState<
    "lcp" | "fid" | "cls" | "fcp" | "ttfb"
  >("lcp");

  const metrics = [
    { key: "lcp" as const, label: "LCP", color: "bg-blue-500" },
    { key: "fid" as const, label: "FID", color: "bg-green-500" },
    { key: "cls" as const, label: "CLS", color: "bg-yellow-500" },
    { key: "fcp" as const, label: "FCP", color: "bg-purple-500" },
    { key: "ttfb" as const, label: "TTFB", color: "bg-red-500" },
  ];

  const maxValue = Math.max(...data.map((d) => d[selectedMetric]));

  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance Trends</CardTitle>
        <CardDescription>
          Historical performance metrics over time
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex space-x-2 mb-4">
          {metrics.map((metric) => (
            <Button
              key={metric.key}
              variant={selectedMetric === metric.key ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedMetric(metric.key)}
            >
              <div className={`w-2 h-2 rounded-full ${metric.color} mr-2`} />
              {metric.label}
            </Button>
          ))}
        </div>

        <div className="h-32 flex items-end space-x-1">
          {data.slice(-20).map((point, index) => {
            const height =
              maxValue > 0 ? (point[selectedMetric] / maxValue) * 100 : 0;
            return (
              <div
                key={index}
                className="flex-1 bg-blue-500 opacity-70 hover:opacity-100 transition-opacity"
                style={{ height: `${height}%` }}
                title={`${point.timestamp}: ${point[selectedMetric]}`}
              />
            );
          })}
        </div>

        {data.length === 0 && (
          <div className="text-center text-muted-foreground py-8">
            No performance data available yet
          </div>
        )}
      </CardContent>
    </Card>
  );
};

interface RecommendationsPanelProps {
  violations: Array<{
    metric: string;
    actual: number;
    budget: number;
    severity: "critical" | "warning";
  }>;
  trends: Array<{
    metric: string;
    trend: "improving" | "degrading" | "stable";
    significance: "low" | "medium" | "high";
  }>;
}

const RecommendationsPanel: React.FC<RecommendationsPanelProps> = ({
  violations,
  trends,
}) => {
  const getRecommendations = () => {
    const recommendations: Array<{
      title: string;
      description: string;
      priority: "high" | "medium" | "low";
      category: "bundle" | "loading" | "rendering" | "network";
    }> = [];

    // Bundle size recommendations
    const bundleViolation = violations.find((v) => v.metric === "bundleSize");
    if (bundleViolation) {
      recommendations.push({
        title: "Reduce Bundle Size",
        description:
          "Implement code splitting and lazy loading to reduce initial bundle size",
        priority: "high",
        category: "bundle",
      });
    }

    // LCP recommendations
    const lcpViolation = violations.find((v) => v.metric === "lcp");
    if (lcpViolation) {
      recommendations.push({
        title: "Optimize Largest Contentful Paint",
        description:
          "Preload critical images and optimize server response times",
        priority: "high",
        category: "loading",
      });
    }

    // FID recommendations
    const fidViolation = violations.find((v) => v.metric === "fid");
    if (fidViolation) {
      recommendations.push({
        title: "Reduce JavaScript Execution Time",
        description: "Break up long tasks and defer non-critical JavaScript",
        priority: "medium",
        category: "rendering",
      });
    }

    // CLS recommendations
    const clsViolation = violations.find((v) => v.metric === "cls");
    if (clsViolation) {
      recommendations.push({
        title: "Minimize Layout Shifts",
        description:
          "Set explicit dimensions for images and avoid inserting content above existing content",
        priority: "high",
        category: "rendering",
      });
    }

    // TTFB recommendations
    const ttfbViolation = violations.find((v) => v.metric === "ttfb");
    if (ttfbViolation) {
      recommendations.push({
        title: "Improve Server Response Time",
        description: "Optimize server performance and consider using a CDN",
        priority: "medium",
        category: "network",
      });
    }

    // Trend-based recommendations
    const degradingTrends = trends.filter(
      (t) => t.trend === "degrading" && t.significance !== "low"
    );
    degradingTrends.forEach((trend) => {
      recommendations.push({
        title: `Address ${trend.metric.toUpperCase()} Degradation`,
        description: `Performance trend shows ${trend.significance} degradation in ${trend.metric}`,
        priority: trend.significance === "high" ? "high" : "medium",
        category: "loading",
      });
    });

    return recommendations.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  };

  const recommendations = getRecommendations();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Optimization Recommendations</CardTitle>
        <CardDescription>
          Actionable insights to improve performance
        </CardDescription>
      </CardHeader>
      <CardContent>
        {recommendations.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
            <p>All performance metrics are within budget!</p>
            <p className="text-sm">Keep up the great work.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {recommendations.map((rec, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border-l-4 ${
                  rec.priority === "high"
                    ? "border-red-500 bg-red-50"
                    : rec.priority === "medium"
                    ? "border-yellow-500 bg-yellow-50"
                    : "border-blue-500 bg-blue-50"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium">{rec.title}</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      {rec.description}
                    </p>
                  </div>
                  <Badge
                    variant={
                      rec.priority === "high"
                        ? "destructive"
                        : rec.priority === "medium"
                        ? "secondary"
                        : "default"
                    }
                  >
                    {rec.priority}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export const PerformanceMonitoringDashboard: React.FC = () => {
  const {
    currentMetrics,
    budgetValidation,
    trends,
    isLoading,
    error,
    lastUpdated,
    recordEntry,
    validateBudgets,
    refreshMetrics,
    exportData,
    clearData,
  } = usePerformanceMonitoring();

  const { regressions } = usePerformanceRegression();
  const [activeTab, setActiveTab] = useState("overview");

  // Use actual trend data from performance monitoring
  // If trends are available from usePerformanceMonitoring, use those
  // Otherwise, show empty state or message that no trend data is available yet
  const trendData = trends || [];
  
  // Show message if no trend data available
  const hasTrendData = trendData.length > 0;

  const handleExport = (format: "json" | "csv") => {
    const data = exportData(format);
    const blob = new Blob([data], {
      type: format === "json" ? "application/json" : "text/csv",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `performance-data.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" />
        Loading performance data...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Performance Monitoring</h1>
          <p className="text-muted-foreground">
            Real-time Core Web Vitals and performance budget tracking
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={refreshMetrics}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={() => handleExport("json")}>
            <Download className="w-4 h-4 mr-2" />
            Export JSON
          </Button>
          <Button variant="outline" onClick={() => handleExport("csv")}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Card className="border-red-500 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-red-700">{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Regression Alerts */}
      {regressions.length > 0 && (
        <Card className="border-orange-500 bg-orange-50">
          <CardHeader>
            <CardTitle className="text-orange-700">
              Performance Regressions Detected
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {regressions.map((regression) => (
                <div
                  key={regression.id}
                  className="flex items-center justify-between"
                >
                  <span className="text-sm">
                    {regression.metric.toUpperCase()} degraded by{" "}
                    {regression.degradationPercent.toFixed(1)}%
                  </span>
                  <Badge
                    variant={
                      regression.severity === "critical"
                        ? "destructive"
                        : "secondary"
                    }
                  >
                    {regression.severity}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Dashboard */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="metrics">Core Web Vitals</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Overall Score */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Score</CardTitle>
              <CardDescription>
                Overall performance based on budget compliance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-4">
                <div className="text-4xl font-bold">
                  {budgetValidation?.score || 0}/100
                </div>
                <div className="flex-1">
                  <Progress
                    value={budgetValidation?.score || 0}
                    className="h-2"
                  />
                </div>
                <Badge
                  variant={
                    (budgetValidation?.score || 0) >= 90
                      ? "default"
                      : (budgetValidation?.score || 0) >= 70
                      ? "secondary"
                      : "destructive"
                  }
                >
                  {(budgetValidation?.score || 0) >= 90
                    ? "Excellent"
                    : (budgetValidation?.score || 0) >= 70
                    ? "Good"
                    : "Needs Improvement"}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Budget Violations</p>
                    <p className="text-2xl font-bold">
                      {budgetValidation?.violations.filter(
                        (v) => v.severity === "critical"
                      ).length || 0}
                    </p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-red-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Last Updated</p>
                    <p className="text-sm text-muted-foreground">
                      {lastUpdated ? lastUpdated.toLocaleTimeString() : "Never"}
                    </p>
                  </div>
                  <Clock className="w-8 h-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Improving Trends</p>
                    <p className="text-2xl font-bold">
                      {trends.filter((t) => t.trend === "improving").length}
                    </p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Degrading Trends</p>
                    <p className="text-2xl font-bold">
                      {trends.filter((t) => t.trend === "degrading").length}
                    </p>
                  </div>
                  <TrendingDown className="w-8 h-8 text-red-500" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <MetricCard
              title="Largest Contentful Paint"
              value={currentMetrics.lcp || 0}
              budget={2500}
              unit="ms"
              icon={<Eye className="w-4 h-4" />}
              trend={
                trends.find((t) => t.metric === "lcp")
                  ? {
                      direction:
                        trends.find((t) => t.metric === "lcp")?.trend ===
                        "improving"
                          ? "down"
                          : trends.find((t) => t.metric === "lcp")?.trend ===
                            "degrading"
                          ? "up"
                          : "stable",
                      value: Math.abs(
                        trends.find((t) => t.metric === "lcp")?.changePercent ||
                          0
                      ),
                    }
                  : undefined
              }
            />

            <MetricCard
              title="First Input Delay"
              value={currentMetrics.fid || 0}
              budget={100}
              unit="ms"
              icon={<Zap className="w-4 h-4" />}
              trend={
                trends.find((t) => t.metric === "fid")
                  ? {
                      direction:
                        trends.find((t) => t.metric === "fid")?.trend ===
                        "improving"
                          ? "down"
                          : trends.find((t) => t.metric === "fid")?.trend ===
                            "degrading"
                          ? "up"
                          : "stable",
                      value: Math.abs(
                        trends.find((t) => t.metric === "fid")?.changePercent ||
                          0
                      ),
                    }
                  : undefined
              }
            />

            <MetricCard
              title="Cumulative Layout Shift"
              value={currentMetrics.cls || 0}
              budget={0.1}
              unit="score"
              icon={<Activity className="w-4 h-4" />}
              trend={
                trends.find((t) => t.metric === "cls")
                  ? {
                      direction:
                        trends.find((t) => t.metric === "cls")?.trend ===
                        "improving"
                          ? "down"
                          : trends.find((t) => t.metric === "cls")?.trend ===
                            "degrading"
                          ? "up"
                          : "stable",
                      value: Math.abs(
                        trends.find((t) => t.metric === "cls")?.changePercent ||
                          0
                      ),
                    }
                  : undefined
              }
            />

            <MetricCard
              title="First Contentful Paint"
              value={currentMetrics.fcp || 0}
              budget={1800}
              unit="ms"
              icon={<Gauge className="w-4 h-4" />}
              trend={
                trends.find((t) => t.metric === "fcp")
                  ? {
                      direction:
                        trends.find((t) => t.metric === "fcp")?.trend ===
                        "improving"
                          ? "down"
                          : trends.find((t) => t.metric === "fcp")?.trend ===
                            "degrading"
                          ? "up"
                          : "stable",
                      value: Math.abs(
                        trends.find((t) => t.metric === "fcp")?.changePercent ||
                          0
                      ),
                    }
                  : undefined
              }
            />

            <MetricCard
              title="Time to First Byte"
              value={currentMetrics.ttfb || 0}
              budget={800}
              unit="ms"
              icon={<Clock className="w-4 h-4" />}
              trend={
                trends.find((t) => t.metric === "ttfb")
                  ? {
                      direction:
                        trends.find((t) => t.metric === "ttfb")?.trend ===
                        "improving"
                          ? "down"
                          : trends.find((t) => t.metric === "ttfb")?.trend ===
                            "degrading"
                          ? "up"
                          : "stable",
                      value: Math.abs(
                        trends.find((t) => t.metric === "ttfb")
                          ?.changePercent || 0
                      ),
                    }
                  : undefined
              }
            />
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          <TrendChart data={trendData} />
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-6">
          <RecommendationsPanel
            violations={budgetValidation?.violations || []}
            trends={trends}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};
