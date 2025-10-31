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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ScatterChart,
  Scatter,
} from "recharts";
import {
  TrendingUp,
  Target,
  Clock,
  Zap,
  AlertTriangle,
  Filter,
  Download,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";

interface BenchmarkMetrics {
  response_time: {
    current: number;
    percentile_50: number;
    percentile_90: number;
    percentile_95: number;
    industry_avg: number;
  };
  accuracy: {
    current: number;
    industry_avg: number;
    percentile_rank: number;
  };
  completeness: {
    current: number;
    industry_avg: number;
    percentile_rank: number;
  };
  source_diversity: {
    current: number;
    industry_avg: number;
    percentile_rank: number;
  };
  detection_speed: {
    current: number;
    industry_avg: number;
    percentile_rank: number;
  };
}

interface PerformanceTrend {
  timestamp: string;
  response_time: number;
  accuracy: number;
  completeness: number;
  detection_speed: number;
}

interface CompetitorBenchmark {
  competitor: string;
  response_time: number;
  accuracy: number;
  completeness: number;
  market_position: number;
}

interface AnomalyAlert {
  id: string;
  metric: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  detected_at: string;
  current_value: number;
  expected_range: [number, number];
}

export function AdvancedBenchmarkingDashboard() {
  const [timeRange, setTimeRange] = useState<"1h" | "24h" | "7d" | "30d">(
    "24h"
  );
  const [selectedMetric, setSelectedMetric] = useState<string>("all");
  const [showAnomalies, setShowAnomalies] = useState(true);

  const {
    data: benchmarkMetrics,
    isLoading: metricsLoading,
    refetch: refetchMetrics,
  } = useQuery({
    queryKey: ["benchmarkMetrics", timeRange],
    queryFn: () =>
      api
        .get("/api/v1/benchmarking/metrics", {
          params: { time_range: timeRange },
        })
        .then((res) => res.data),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // 1 minute
  });

  const { data: performanceTrends, isLoading: trendsLoading } = useQuery({
    queryKey: ["performanceTrends", timeRange],
    queryFn: () =>
      api
        .get("/api/v1/benchmarking/trends", {
          params: { time_range: timeRange },
        })
        .then((res) => res.data.trends),
    staleTime: 30000,
  });

  const { data: competitorBenchmarks, isLoading: competitorLoading } = useQuery(
    {
      queryKey: ["competitorBenchmarks"],
      queryFn: () =>
        api
          .get("/api/v1/benchmarking/competitors")
          .then((res) => res.data.benchmarks),
      staleTime: 300000, // 5 minutes
    }
  );

  const { data: anomalyAlerts, isLoading: anomaliesLoading } = useQuery({
    queryKey: ["anomalyAlerts"],
    queryFn: () =>
      api.get("/api/v1/benchmarking/anomalies").then((res) => res.data.alerts),
    staleTime: 30000,
    enabled: showAnomalies,
  });

  if (metricsLoading || trendsLoading || competitorLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const metrics = benchmarkMetrics || {};
  const trends = performanceTrends || [];
  const competitors = competitorBenchmarks || [];
  const alerts = anomalyAlerts || [];

  // Prepare radar chart data
  const radarData = [
    {
      metric: "Response Time",
      current: 100 - (metrics.response_time?.current || 0) / 10, // Invert for better visualization
      industry: 100 - (metrics.response_time?.industry_avg || 0) / 10,
    },
    {
      metric: "Accuracy",
      current: (metrics.accuracy?.current || 0) * 100,
      industry: (metrics.accuracy?.industry_avg || 0) * 100,
    },
    {
      metric: "Completeness",
      current: (metrics.completeness?.current || 0) * 100,
      industry: (metrics.completeness?.industry_avg || 0) * 100,
    },
    {
      metric: "Source Diversity",
      current: (metrics.source_diversity?.current || 0) * 100,
      industry: (metrics.source_diversity?.industry_avg || 0) * 100,
    },
    {
      metric: "Detection Speed",
      current: 100 - (metrics.detection_speed?.current || 0) / 60, // Convert minutes to score
      industry: 100 - (metrics.detection_speed?.industry_avg || 0) / 60,
    },
  ];

  const getPercentileColor = (percentile: number) => {
    if (percentile >= 90) return "text-green-600 bg-green-100";
    if (percentile >= 75) return "text-blue-600 bg-blue-100";
    if (percentile >= 50) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "text-red-600 bg-red-100 border-red-200";
      case "high":
        return "text-orange-600 bg-orange-100 border-orange-200";
      case "medium":
        return "text-yellow-600 bg-yellow-100 border-yellow-200";
      default:
        return "text-blue-600 bg-blue-100 border-blue-200";
    }
  };

  const handleExportData = () => {
    const data = {
      metrics: benchmarkMetrics,
      trends: performanceTrends,
      competitors: competitorBenchmarks,
      timestamp: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `benchmark-report-${
      new Date().toISOString().split("T")[0]
    }.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Target className="w-5 h-5 mr-2 text-blue-600" />
            Advanced Benchmarking Dashboard
          </h3>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => refetchMetrics()}
              className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
            <button
              onClick={handleExportData}
              className="flex items-center space-x-2 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-4 mb-6">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">
              Time Range:
            </span>
            <select
              value={timeRange}
              onChange={(e) =>
                setTimeRange(e.target.value as "1h" | "24h" | "7d" | "30d")
              }
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Focus:</span>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Metrics</option>
              <option value="response_time">Response Time</option>
              <option value="accuracy">Accuracy</option>
              <option value="completeness">Completeness</option>
              <option value="detection_speed">Detection Speed</option>
            </select>
          </div>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showAnomalies}
              onChange={(e) => setShowAnomalies(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Show Anomaly Alerts</span>
          </label>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {metrics.response_time?.current?.toFixed(1) || "0.0"}s
            </div>
            <div className="text-sm text-gray-600">Avg Response Time</div>
            <div className="text-xs text-gray-500 mt-1">
              Industry:{" "}
              {metrics.response_time?.industry_avg?.toFixed(1) || "0.0"}s
            </div>
            <div className="text-xs text-gray-500">
              P95: {metrics.response_time?.percentile_95?.toFixed(1) || "0.0"}s
            </div>
          </div>

          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {Math.round((metrics.accuracy?.current || 0) * 100)}%
            </div>
            <div className="text-sm text-gray-600">Accuracy Score</div>
            <div
              className={`text-xs px-2 py-1 rounded-full mt-2 ${getPercentileColor(
                metrics.accuracy?.percentile_rank || 0
              )}`}
            >
              {Math.round(metrics.accuracy?.percentile_rank || 0)}th percentile
            </div>
          </div>

          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {Math.round((metrics.completeness?.current || 0) * 100)}%
            </div>
            <div className="text-sm text-gray-600">Completeness</div>
            <div
              className={`text-xs px-2 py-1 rounded-full mt-2 ${getPercentileColor(
                metrics.completeness?.percentile_rank || 0
              )}`}
            >
              {Math.round(metrics.completeness?.percentile_rank || 0)}th
              percentile
            </div>
          </div>

          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">
              {metrics.detection_speed?.current?.toFixed(1) || "0.0"}m
            </div>
            <div className="text-sm text-gray-600">Detection Speed</div>
            <div className="text-xs text-gray-500 mt-1">
              Industry:{" "}
              {metrics.detection_speed?.industry_avg?.toFixed(1) || "0.0"}m
            </div>
          </div>
        </div>
      </div>

      {/* Anomaly Alerts */}
      {showAnomalies && alerts.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="w-4 h-4 mr-2 text-red-600" />
            Performance Anomalies ({alerts.length})
          </h4>
          <div className="space-y-3">
            {alerts.slice(0, 5).map((alert: AnomalyAlert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border ${getSeverityColor(
                  alert.severity
                )}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium text-sm">
                      {alert.metric.replace("_", " ").toUpperCase()} Anomaly
                    </div>
                    <div className="text-sm mt-1">{alert.description}</div>
                    <div className="text-xs mt-2 text-gray-600">
                      Current: {alert.current_value} | Expected:{" "}
                      {alert.expected_range[0]} - {alert.expected_range[1]}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(alert.detected_at).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Radar */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-4">
            Performance Overview
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12 }} />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 100]}
                  tick={{ fontSize: 10 }}
                />
                <Radar
                  name="Current"
                  dataKey="current"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.3}
                  strokeWidth={2}
                />
                <Radar
                  name="Industry Avg"
                  dataKey="industry"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Competitor Comparison */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-4">
            Competitor Benchmarks
          </h4>
          {competitors.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart data={competitors}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="response_time"
                    name="Response Time"
                    unit="s"
                    type="number"
                  />
                  <YAxis
                    dataKey="accuracy"
                    name="Accuracy"
                    unit="%"
                    type="number"
                    domain={[0, 100]}
                  />
                  <Tooltip
                    cursor={{ strokeDasharray: "3 3" }}
                    formatter={(value, name) => [
                      name === "accuracy"
                        ? `${Math.round(Number(value) * 100)}%`
                        : `${value}s`,
                      name === "accuracy" ? "Accuracy" : "Response Time",
                    ]}
                    labelFormatter={(label) => label}
                  />
                  <Scatter
                    name="Competitors"
                    dataKey="accuracy"
                    fill="#8b5cf6"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Target className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">No competitor benchmark data available.</p>
            </div>
          )}
        </div>
      </div>

      {/* Performance Trends */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
          <TrendingUp className="w-4 h-4 mr-2" />
          Performance Trends
        </h4>
        {trends.length > 0 ? (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) =>
                    new Date(value).toLocaleTimeString()
                  }
                />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                  formatter={(value, name) => [
                    name === "response_time"
                      ? `${Number(value).toFixed(2)}s`
                      : name === "detection_speed"
                      ? `${Number(value).toFixed(1)}m`
                      : `${Math.round(Number(value) * 100)}%`,
                    String(name).replace("_", " ").toUpperCase(),
                  ]}
                />
                <Legend />
                {selectedMetric === "all" ||
                selectedMetric === "response_time" ? (
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="response_time"
                    stroke="#3b82f6"
                    name="Response Time"
                    strokeWidth={2}
                  />
                ) : null}
                {selectedMetric === "all" || selectedMetric === "accuracy" ? (
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="accuracy"
                    stroke="#10b981"
                    name="Accuracy"
                    strokeWidth={2}
                  />
                ) : null}
                {selectedMetric === "all" ||
                selectedMetric === "completeness" ? (
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="completeness"
                    stroke="#8b5cf6"
                    name="Completeness"
                    strokeWidth={2}
                  />
                ) : null}
                {selectedMetric === "all" ||
                selectedMetric === "detection_speed" ? (
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="detection_speed"
                    stroke="#f59e0b"
                    name="Detection Speed"
                    strokeWidth={2}
                  />
                ) : null}
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Clock className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm">
              No trend data available for the selected time range.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
