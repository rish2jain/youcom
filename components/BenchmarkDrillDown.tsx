"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  ComposedChart,
} from "recharts";
import {
  ChevronDown,
  ChevronRight,
  Search,
  Filter,
  TrendingUp,
  Clock,
  Target,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";

interface DrillDownData {
  metric: string;
  breakdown: {
    by_competitor: Array<{
      competitor: string;
      value: number;
      trend: "up" | "down" | "stable";
      change_percent: number;
    }>;
    by_industry: Array<{
      industry: string;
      value: number;
      percentile: number;
    }>;
    by_time_period: Array<{
      period: string;
      value: number;
      volume: number;
    }>;
  };
  detailed_metrics: {
    p50: number;
    p90: number;
    p95: number;
    p99: number;
    min: number;
    max: number;
    std_dev: number;
  };
}

interface BenchmarkDrillDownProps {
  metric: string;
  timeRange: string;
  onClose: () => void;
}

export function BenchmarkDrillDown({
  metric,
  timeRange,
  onClose,
}: BenchmarkDrillDownProps) {
  const [activeTab, setActiveTab] = useState<
    "competitors" | "industry" | "timeline"
  >("competitors");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"value" | "trend" | "name">("value");

  const {
    data: drillDownData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["benchmarkDrillDown", metric, timeRange],
    queryFn: () =>
      api
        .get("/api/v1/benchmarking/drill-down", {
          params: { metric, time_range: timeRange },
        })
        .then((res) => res.data),
    staleTime: 60000, // 1 minute
  });

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm" role="alert">
        <div className="text-center space-y-4">
          <div className="text-red-600 font-medium">
            Failed to load benchmark data
          </div>
          <div className="text-gray-600 text-sm">
            {error?.message || "An unexpected error occurred"}
          </div>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const data = drillDownData || {};
  const breakdown = data.breakdown || {};
  const detailedMetrics = data.detailed_metrics || {};

  const formatMetricValue = (value: number, metricType: string) => {
    switch (metricType) {
      case "response_time":
        return `${value.toFixed(2)}s`;
      case "detection_speed":
        return `${value.toFixed(1)}m`;
      case "accuracy":
      case "completeness":
      case "source_diversity":
        return `${Math.round(value * 100)}%`;
      default:
        return value.toString();
    }
  };

  const getMetricIcon = (metricType: string) => {
    switch (metricType) {
      case "response_time":
        return <Clock className="w-4 h-4" />;
      case "detection_speed":
        return <Zap className="w-4 h-4" />;
      case "accuracy":
      case "completeness":
        return <Target className="w-4 h-4" />;
      default:
        return <TrendingUp className="w-4 h-4" />;
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "up":
        return <TrendingUp className="w-3 h-3 text-green-600" />;
      case "down":
        return (
          <TrendingUp className="w-3 h-3 text-red-600 transform rotate-180" />
        );
      default:
        return <div className="w-3 h-3 bg-gray-400 rounded-full"></div>;
    }
  };

  const filteredCompetitors = (breakdown.by_competitor || [])
    .filter(
      (item: any) =>
        searchQuery === "" ||
        item.competitor.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a: any, b: any) => {
      switch (sortBy) {
        case "value":
          return b.value - a.value;
        case "trend":
          return b.change_percent - a.change_percent;
        case "name":
          return a.competitor.localeCompare(b.competitor);
        default:
          return 0;
      }
    });

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          {getMetricIcon(metric)}
          <span className="ml-2 capitalize">
            {metric.replace("_", " ")} Analysis
          </span>
        </h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          ✕
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-lg font-bold text-blue-600">
            {formatMetricValue(detailedMetrics.p50 || 0, metric)}
          </div>
          <div className="text-xs text-gray-600">Median (P50)</div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-lg font-bold text-green-600">
            {formatMetricValue(detailedMetrics.p90 || 0, metric)}
          </div>
          <div className="text-xs text-gray-600">P90</div>
        </div>
        <div className="text-center p-3 bg-orange-50 rounded-lg">
          <div className="text-lg font-bold text-orange-600">
            {formatMetricValue(detailedMetrics.p95 || 0, metric)}
          </div>
          <div className="text-xs text-gray-600">P95</div>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <div className="text-lg font-bold text-purple-600">
            {formatMetricValue(detailedMetrics.std_dev || 0, metric)}
          </div>
          <div className="text-xs text-gray-600">Std Dev</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab("competitors")}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === "competitors"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            By Competitor
          </button>
          <button
            onClick={() => setActiveTab("industry")}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === "industry"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            By Industry
          </button>
          <button
            onClick={() => setActiveTab("timeline")}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === "timeline"
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            Timeline
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === "competitors" && (
        <div>
          {/* Controls */}
          <div className="flex flex-wrap gap-4 mb-6">
            <div className="relative flex-1 min-w-64">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search competitors..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">
                Sort by:
              </span>
              <select
                value={sortBy}
                onChange={(e) =>
                  setSortBy(e.target.value as "value" | "trend" | "name")
                }
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="value">Performance</option>
                <option value="trend">Trend</option>
                <option value="name">Name</option>
              </select>
            </div>
          </div>

          {/* Competitor List */}
          <div className="space-y-3">
            {filteredCompetitors.map((competitor: any, index: number) => (
              <div
                key={competitor.competitor}
                className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="text-sm font-medium text-gray-900">
                      #{index + 1} {competitor.competitor}
                    </div>
                    {getTrendIcon(competitor.trend)}
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-900">
                      {formatMetricValue(competitor.value, metric)}
                    </div>
                    <div
                      className={`text-xs ${
                        competitor.change_percent > 0
                          ? "text-green-600"
                          : competitor.change_percent < 0
                          ? "text-red-600"
                          : "text-gray-600"
                      }`}
                    >
                      {competitor.change_percent > 0 ? "+" : ""}
                      {competitor.change_percent.toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {filteredCompetitors.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Search className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">
                No competitors found matching your search.
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === "industry" && (
        <div>
          <div className="h-64 mb-6">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={breakdown.by_industry || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="industry" />
                <YAxis />
                <Tooltip
                  formatter={(value) => [
                    formatMetricValue(Number(value), metric),
                    "Value",
                  ]}
                />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-3">
            {(breakdown.by_industry || []).map(
              (industry: any, index: number) => (
                <div
                  key={industry.industry}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="font-medium text-gray-900">
                    {industry.industry}
                  </div>
                  <div className="text-right">
                    <div className="font-bold">
                      {formatMetricValue(industry.value, metric)}
                    </div>
                    <div className="text-xs text-gray-600">
                      {industry.percentile}th percentile
                    </div>
                  </div>
                </div>
              )
            )}
          </div>
        </div>
      )}

      {activeTab === "timeline" && (
        <div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={breakdown.by_time_period || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip
                  formatter={(value, name) => [
                    name === "value"
                      ? formatMetricValue(Number(value), metric)
                      : value,
                    name === "value" ? "Performance" : "Volume",
                  ]}
                />
                <Legend />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.3}
                  name="Performance"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="volume"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Volume"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
