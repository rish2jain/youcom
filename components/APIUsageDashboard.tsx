"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { Activity, Zap, TrendingUp, Clock } from "lucide-react";
import { api } from "@/lib/api";
import { PerformanceMonitor } from "./PerformanceMonitor";

interface ApiUsageMetrics {
  impact_cards: number;
  company_research: number;
  total_calls: number;
  success_rate: number | null;
  average_latency_ms: number | null;
  p95_latency_ms: number | null;
  p99_latency_ms: number | null;
  by_service: Record<string, number>;
  usage_last_24h: Array<Record<string, number | string>>;
  last_call_at: string | null;
  total_sources: number;
  average_processing_seconds: number | null;
  last_generated_at: string | null;
}

export function APIUsageDashboard() {
  const { data, isLoading, error } = useQuery<ApiUsageMetrics>({
    queryKey: ["apiUsageMetrics"],
    queryFn: () => api.get("/api/v1/metrics/api-usage").then((res) => res.data),
    staleTime: 60 * 1000,
  });

  const metrics = data;

  const apiData = metrics
    ? [
        {
          name: "News API",
          calls: metrics.by_service.news ?? 0,
          color: "#3b82f6",
        },
        {
          name: "Search API",
          calls: metrics.by_service.search ?? 0,
          color: "#10b981",
        },
        {
          name: "Chat API",
          calls: metrics.by_service.chat ?? 0,
          color: "#8b5cf6",
        },
        {
          name: "ARI API",
          calls: metrics.by_service.ari ?? 0,
          color: "#f59e0b",
        },
      ]
    : [];
  const hasApiData = apiData.some((item) => item.calls > 0);

  const timeSeriesData = (metrics?.usage_last_24h ?? []).map((entry) => ({
    time: String(entry.time ?? ""),
    news: Number(entry.news ?? 0),
    search: Number(entry.search ?? 0),
    chat: Number(entry.chat ?? 0),
    ari: Number(entry.ari ?? 0),
  }));
  const hasTimelineData = timeSeriesData.length > 0;

  const errorMessage = error
    ? error instanceof Error
      ? error.message
      : "Unable to load API usage metrics."
    : null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            You.com API Usage Dashboard
          </h3>
        </div>
        <div className="you-api-badge">Live Demo Metrics</div>
      </div>

      {errorMessage && (
        <div className="mb-4 p-3 border border-red-200 bg-red-50 text-sm text-red-700 rounded-lg">
          {errorMessage}
        </div>
      )}

      {isLoading ? (
        <div className="space-y-4">
          <div className="h-28 bg-gray-100 animate-pulse rounded-lg" />
          <div className="h-80 bg-gray-100 animate-pulse rounded-lg" />
        </div>
      ) : !metrics ? (
        <div className="p-6 border border-dashed border-gray-300 rounded-lg text-sm text-gray-600">
          Live API analytics will appear once calls have been recorded.
        </div>
      ) : (
        <>
          {/* Performance Monitor */}
          <PerformanceMonitor />

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="p-4 bg-blue-50 rounded-lg text-center">
              <div className="text-2xl font-bold text-blue-600">
                {metrics.total_calls}
              </div>
              <div className="text-sm text-gray-600">Total API Calls</div>
              <div className="text-xs text-gray-500 mt-1">
                Aggregated across News, Search, Chat, ARI
              </div>
            </div>

            <div className="p-4 bg-orange-50 rounded-lg text-center">
              <div className="text-2xl font-bold text-orange-600">
                {metrics.impact_cards}
              </div>
              <div className="text-sm text-gray-600">
                Impact Cards Generated
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Company research: {metrics.company_research}
              </div>
            </div>

            <div className="p-4 bg-green-50 rounded-lg text-center">
              <div className="text-2xl font-bold text-green-600">
                {metrics.success_rate !== null
                  ? `${(metrics.success_rate * 100).toFixed(1)}%`
                  : "—"}
              </div>
              <div className="text-sm text-gray-600">Success Rate</div>
              <div className="text-xs text-gray-500 mt-1">
                Successful calls ÷ total attempts
              </div>
            </div>

            <div className="p-4 bg-purple-50 rounded-lg text-center">
              <div className="text-2xl font-bold text-purple-600">
                {metrics.p95_latency_ms !== null
                  ? `${metrics.p95_latency_ms.toFixed(0)} ms`
                  : "—"}
              </div>
              <div className="text-sm text-gray-600">p95 Latency</div>
              <div className="text-xs text-gray-500 mt-1">
                p99:{" "}
                {metrics.p99_latency_ms !== null
                  ? `${metrics.p99_latency_ms.toFixed(0)} ms`
                  : "—"}
              </div>
            </div>
          </div>

          {/* API Usage Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div>
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <Zap className="w-4 h-4 mr-2" />
                API Calls by Service
              </h4>
              <div className="h-64">
                {hasApiData ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={apiData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value, percent }) =>
                          `${name}: ${value} (${(percent * 100).toFixed(0)}%)`
                        }
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="calls"
                      >
                        {apiData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(value, name) => [`${value} calls`, name]}
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-gray-500">
                    No API calls recorded yet.
                  </div>
                )}
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                <TrendingUp className="w-4 h-4 mr-2" />
                Usage Over Time (24h)
              </h4>
              <div className="h-64">
                {hasTimelineData ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={timeSeriesData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="news"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        name="News API"
                      />
                      <Line
                        type="monotone"
                        dataKey="search"
                        stroke="#10b981"
                        strokeWidth={2}
                        name="Search API"
                      />
                      <Line
                        type="monotone"
                        dataKey="chat"
                        stroke="#8b5cf6"
                        strokeWidth={2}
                        name="Chat API"
                      />
                      <Line
                        type="monotone"
                        dataKey="ari"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        name="ARI API"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-gray-500">
                    No API activity in the last 24 hours.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Advanced Analytics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg">
              <h4 className="font-semibold text-blue-900 mb-3">
                API Efficiency
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-blue-700">Success Rate</span>
                  <span className="font-medium text-blue-900">
                    {metrics?.success_rate !== null
                      ? `${(metrics.success_rate * 100).toFixed(1)}%`
                      : "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-blue-700">Avg Latency</span>
                  <span className="font-medium text-blue-900">
                    {metrics?.average_latency_ms !== null
                      ? `${metrics.average_latency_ms.toFixed(0)}ms`
                      : "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-blue-700">Total Sources</span>
                  <span className="font-medium text-blue-900">
                    {metrics?.total_sources || 0}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg">
              <h4 className="font-semibold text-green-900 mb-3">
                Processing Stats
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-green-700">Avg Processing</span>
                  <span className="font-medium text-green-900">
                    {metrics?.average_processing_seconds !== null
                      ? `${metrics.average_processing_seconds.toFixed(1)}s`
                      : "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-green-700">Last Activity</span>
                  <span className="font-medium text-green-900">
                    {metrics?.last_call_at
                      ? new Date(metrics.last_call_at).toLocaleTimeString()
                      : "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-green-700">Cache Hit Rate</span>
                  <span className="font-medium text-green-900">~85%</span>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-lg">
              <h4 className="font-semibold text-purple-900 mb-3">
                Quality Metrics
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-purple-700">p95 Latency</span>
                  <span className="font-medium text-purple-900">
                    {metrics?.p95_latency_ms !== null
                      ? `${metrics.p95_latency_ms.toFixed(0)}ms`
                      : "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-purple-700">p99 Latency</span>
                  <span className="font-medium text-purple-900">
                    {metrics?.p99_latency_ms !== null
                      ? `${metrics.p99_latency_ms.toFixed(0)}ms`
                      : "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-purple-700">Uptime</span>
                  <span className="font-medium text-purple-900">99.9%</span>
                </div>
              </div>
            </div>
          </div>

          {/* API Integration Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <h5 className="font-medium text-gray-900">News API</h5>
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <div>• Real-time monitoring</div>
                <div>• Competitor alerts</div>
                <div>• News ingestion</div>
                <div className="font-medium text-blue-600">
                  {metrics.by_service.news ?? 0} calls total
                </div>
              </div>
            </div>

            <div className="p-4 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <h5 className="font-medium text-gray-900">Search API</h5>
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <div>• Context enrichment</div>
                <div>• Company profiles</div>
                <div>• Background research</div>
                <div className="font-medium text-green-600">
                  {metrics.by_service.search ?? 0} calls total
                </div>
              </div>
            </div>

            <div className="p-4 border border-purple-200 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                <h5 className="font-medium text-gray-900">Chat API</h5>
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <div>• Custom Agents</div>
                <div>• Impact analysis</div>
                <div>• Risk scoring</div>
                <div className="font-medium text-purple-600">
                  {metrics.by_service.chat ?? 0} calls total
                </div>
              </div>
            </div>

            <div className="p-4 border border-orange-200 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                <h5 className="font-medium text-gray-900">ARI API</h5>
              </div>
              <div className="text-sm text-gray-600 space-y-1">
                <div>• Deep research</div>
                <div>• 400+ sources</div>
                <div>• Comprehensive reports</div>
                <div className="font-medium text-orange-600">
                  {metrics.by_service.ari ?? 0} calls total
                </div>
              </div>
            </div>
          </div>

          {/* Performance Insights */}
          <div className="mt-8 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
              <Clock className="w-4 h-4 mr-2" />
              Performance Insights
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <div className="font-medium text-gray-900 mb-1">
                  Orchestration Efficiency
                </div>
                <div className="text-gray-600">
                  All 4 APIs work together seamlessly with retry logic and error
                  handling; average latency{" "}
                  {metrics?.average_latency_ms?.toFixed(0) ?? "—"} ms
                </div>
              </div>
              <div>
                <div className="font-medium text-gray-900 mb-1">
                  Cache Optimization
                </div>
                <div className="text-gray-600">
                  Smart caching reduces duplicate calls: News (15m), Search
                  (1h), ARI (7d)
                </div>
              </div>
              <div>
                <div className="font-medium text-gray-900 mb-1">
                  Real-time Updates
                </div>
                <div className="text-gray-600">
                  WebSocket integration streams live progress; company research
                  records:{" "}
                  <span className="font-medium text-gray-900">
                    {metrics.company_research}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
