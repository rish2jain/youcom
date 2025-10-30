"use client";

import React, { useEffect } from "react";
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
  PieChart,
  Pie,
  Cell,
  ComposedChart,
  Line,
} from "recharts";
import { TrendingUp, Users, Star, Activity, Calendar } from "lucide-react";
import { api } from "@/lib/api";

interface TemplateUsageStats {
  template_id: number;
  template_name: string;
  industry_sector: string;
  total_applications: number;
  active_applications: number;
  avg_rating: number;
  total_ratings: number;
  success_rate: number;
  last_used: string;
}

interface UsageTrend {
  date: string;
  applications: number;
  success_rate: number;
}

interface IndustryBreakdown {
  industry: string;
  count: number;
  percentage: number;
}

export function TemplateUsageAnalytics() {
  const {
    data: usageStats,
    isLoading: statsLoading,
    isError: statsError,
    error: statsErrorData,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ["templateUsageStats"],
    queryFn: () =>
      api
        .get("/api/v1/industry_templates/analytics/usage")
        .then((res) => res.data),
    staleTime: 300000, // 5 minutes
  });

  const {
    data: usageTrends,
    isLoading: trendsLoading,
    isError: trendsError,
    error: trendsErrorData,
    refetch: refetchTrends,
  } = useQuery({
    queryKey: ["templateUsageTrends"],
    queryFn: () =>
      api
        .get("/api/v1/industry_templates/analytics/trends")
        .then((res) => res.data.trends),
    staleTime: 300000,
  });

  const {
    data: industryBreakdown,
    isLoading: breakdownLoading,
    isError: breakdownError,
    error: breakdownErrorData,
    refetch: refetchBreakdown,
  } = useQuery({
    queryKey: ["templateIndustryBreakdown"],
    queryFn: () =>
      api
        .get("/api/v1/industry_templates/analytics/industries")
        .then((res) => res.data.breakdown),
    staleTime: 300000,
  });

  // Handle errors via useEffect instead of deprecated onError
  useEffect(() => {
    if (statsError) {
      console.error("Failed to fetch template usage stats:", statsError);
    }
    if (trendsError) {
      console.error("Failed to fetch template usage trends:", trendsError);
    }
    if (breakdownError) {
      console.error("Failed to fetch industry breakdown:", breakdownError);
    }
  }, [statsError, trendsError, breakdownError]);

  if (statsLoading || trendsLoading || breakdownLoading) {
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

  if (statsError || trendsError || breakdownError) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm" role="alert">
        <div className="text-center space-y-4">
          <div className="text-red-600 font-medium">
            Failed to load template analytics
          </div>
          <div className="text-gray-600 text-sm">
            {statsErrorData?.message ||
              trendsErrorData?.message ||
              breakdownErrorData?.message ||
              "An unexpected error occurred"}
          </div>
          <div className="space-x-2">
            <button
              onClick={() => {
                refetchStats();
                refetchTrends();
                refetchBreakdown();
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Retry All
            </button>
          </div>
        </div>
      </div>
    );
  }

  const stats = usageStats || {};
  const trends = usageTrends || [];
  const breakdown = industryBreakdown || [];

  // Prepare data for charts
  const topTemplates = (stats.templates || [])
    .sort(
      (a: TemplateUsageStats, b: TemplateUsageStats) =>
        b.total_applications - a.total_applications
    )
    .slice(0, 10);

  const industryColors = [
    "#3b82f6",
    "#10b981",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#06b6d4",
    "#84cc16",
    "#f97316",
    "#ec4899",
    "#6366f1",
  ];

  const totalApplications = stats.total_applications || 0;
  const totalActiveTemplates = stats.active_templates || 0;
  const avgSuccessRate = stats.avg_success_rate || 0;
  const avgRating = stats.avg_rating || 0;

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
          <Activity className="w-5 h-5 mr-2 text-blue-600" />
          Template Usage Analytics
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-3xl font-bold text-blue-600">
              {totalApplications}
            </div>
            <div className="text-sm text-gray-600">Total Applications</div>
            <div className="text-xs text-gray-500 mt-1">All time</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-3xl font-bold text-green-600">
              {totalActiveTemplates}
            </div>
            <div className="text-sm text-gray-600">Active Templates</div>
            <div className="text-xs text-gray-500 mt-1">Currently in use</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-3xl font-bold text-purple-600">
              {Math.round(avgSuccessRate * 100)}%
            </div>
            <div className="text-sm text-gray-600">Success Rate</div>
            <div className="text-xs text-gray-500 mt-1">
              Template effectiveness
            </div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-3xl font-bold text-orange-600">
              {typeof avgRating === "number" && isFinite(avgRating)
                ? avgRating.toFixed(1)
                : "0.0"}
            </div>
            <div className="text-sm text-gray-600">Average Rating</div>
            <div className="text-xs text-gray-500 mt-1">User satisfaction</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Usage Trends */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="w-4 h-4 mr-2" />
            Usage Trends
          </h4>
          {trends.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) =>
                      new Date(value).toLocaleDateString()
                    }
                  />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip
                    labelFormatter={(value) =>
                      new Date(value).toLocaleDateString()
                    }
                    formatter={(value, name) => [
                      name === "applications"
                        ? value
                        : `${Math.round(Number(value) * 100)}%`,
                      name === "applications" ? "Applications" : "Success Rate",
                    ]}
                  />
                  <Legend />
                  <Bar
                    yAxisId="left"
                    dataKey="applications"
                    fill="#3b82f6"
                    name="Applications"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="success_rate"
                    stroke="#10b981"
                    name="Success Rate"
                    strokeWidth={2}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Calendar className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">No trend data available yet.</p>
            </div>
          )}
        </div>

        {/* Industry Breakdown */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-4">
            Industry Distribution
          </h4>
          {breakdown.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={breakdown}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    dataKey="count"
                    nameKey="industry"
                  >
                    {breakdown.map(
                      (entry: IndustryBreakdown, index: number) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={industryColors[index % industryColors.length]}
                        />
                      )
                    )}
                  </Pie>
                  <Tooltip
                    formatter={(value, name) => [`${value} templates`, name]}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Users className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">No industry data available yet.</p>
            </div>
          )}
        </div>
      </div>

      {/* Top Templates */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h4 className="font-semibold text-gray-900 mb-4">
          Most Popular Templates
        </h4>
        {topTemplates.length > 0 ? (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topTemplates} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis
                  type="category"
                  dataKey="template_name"
                  width={120}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip
                  formatter={(value, name) => [
                    value,
                    name === "total_applications" ? "Applications" : "Active",
                  ]}
                />
                <Legend />
                <Bar
                  dataKey="total_applications"
                  fill="#3b82f6"
                  name="Total Applications"
                />
                <Bar
                  dataKey="active_applications"
                  fill="#10b981"
                  name="Active Applications"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Star className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm">No template usage data available yet.</p>
          </div>
        )}
      </div>

      {/* Template Performance Table */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h4 className="font-semibold text-gray-900 mb-4">
          Template Performance Details
        </h4>
        {topTemplates.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Template
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Industry
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Applications
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Success Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rating
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Used
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {topTemplates.map((template: TemplateUsageStats) => (
                  <tr key={template.template_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {template.template_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-600">
                        {template.industry_sector}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {template.total_applications}
                        <span className="text-gray-500 ml-1">
                          ({template.active_applications} active)
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {Math.round(template.success_rate * 100)}%
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Star className="w-4 h-4 text-yellow-400 fill-current mr-1" />
                        <span className="text-sm text-gray-900">
                          {template.avg_rating.toFixed(1)}
                        </span>
                        <span className="text-xs text-gray-500 ml-1">
                          ({template.total_ratings})
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {new Date(template.last_used).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="text-sm">
              No template performance data available yet.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
