"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Calendar,
  Filter,
  Eye,
  AlertTriangle,
} from "lucide-react";
import { api } from "@/lib/api";

interface SentimentTrendData {
  timestamp: string;
  positive: number;
  negative: number;
  neutral: number;
  overall_score: number;
  volume: number;
  volatility: number;
}

interface EntitySentiment {
  entity_name: string;
  entity_type: "company" | "product" | "market";
  current_sentiment: number;
  trend_direction: "improving" | "declining" | "stable";
  change_percent: number;
  total_mentions: number;
}

interface SentimentTrendChartProps {
  entityName?: string;
  entityType?: string;
  timeRange?: "7d" | "30d" | "90d";
}

export function SentimentTrendChart({
  entityName,
  entityType = "company",
  timeRange = "30d",
}: SentimentTrendChartProps) {
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [chartType, setChartType] = useState<"line" | "area" | "bar">("line");
  const [showVolume, setShowVolume] = useState(true);

  const { data: sentimentTrends, isLoading: trendsLoading } = useQuery({
    queryKey: ["sentimentTrends", entityName, entityType, selectedTimeRange],
    queryFn: () => {
      const params: any = { time_range: selectedTimeRange };
      if (entityName) params.entity_name = entityName;
      if (entityType) params.entity_type = entityType;

      return api
        .get("/api/v1/sentiment/trends", { params })
        .then((res) => res.data.trends);
    },
    staleTime: 60000, // 1 minute
  });

  const { data: entitySentiments, isLoading: entitiesLoading } = useQuery({
    queryKey: ["entitySentiments", selectedTimeRange],
    queryFn: () =>
      api
        .get("/api/v1/sentiment/entities", {
          params: { time_range: selectedTimeRange },
        })
        .then((res) => res.data.entities),
    staleTime: 60000,
  });

  if (trendsLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const trends = sentimentTrends || [];
  const entities = entitySentiments || [];

  // Calculate summary statistics
  const latestTrend = trends[trends.length - 1];
  const firstTrend = trends[0];
  const overallChange =
    latestTrend && firstTrend && Math.abs(firstTrend.overall_score) > 0
      ? ((latestTrend.overall_score - firstTrend.overall_score) /
          Math.abs(firstTrend.overall_score)) *
        100
      : 0;

  const avgVolatility =
    trends.length > 0
      ? trends.reduce((sum, trend) => sum + trend.volatility, 0) / trends.length
      : 0;

  const totalMentions = trends.reduce((sum, trend) => sum + trend.volume, 0);

  const getSentimentColor = (score: number) => {
    if (score > 0.2) return "#10b981"; // green
    if (score > -0.2) return "#6b7280"; // gray
    return "#ef4444"; // red
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case "improving":
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case "declining":
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <div className="w-4 h-4 bg-gray-400 rounded-full"></div>;
    }
  };

  const formatSentimentScore = (score: number) => {
    if (score > 0) return `+${(score * 100).toFixed(1)}%`;
    return `${(score * 100).toFixed(1)}%`;
  };

  const renderChart = () => {
    const chartData = trends.map((trend) => ({
      ...trend,
      date: new Date(trend.timestamp).toLocaleDateString(),
      time: new Date(trend.timestamp).toLocaleTimeString(),
    }));

    const commonProps = {
      data: chartData,
      margin: { top: 5, right: 30, left: 20, bottom: 5 },
    };

    switch (chartType) {
      case "area":
        return (
          <AreaChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis yAxisId="left" domain={[-1, 1]} />
            {showVolume && <YAxis yAxisId="right" orientation="right" />}
            <Tooltip
              formatter={(value, name) => [
                name === "volume" ? value : formatSentimentScore(Number(value)),
                name === "volume"
                  ? "Volume"
                  : name.charAt(0).toUpperCase() + name.slice(1),
              ]}
            />
            <Legend />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="positive"
              stackId="1"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.6}
            />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="neutral"
              stackId="1"
              stroke="#6b7280"
              fill="#6b7280"
              fillOpacity={0.6}
            />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="negative"
              stackId="1"
              stroke="#ef4444"
              fill="#ef4444"
              fillOpacity={0.6}
            />
            {showVolume && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="volume"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={false}
              />
            )}
          </AreaChart>
        );

      case "bar":
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip
              formatter={(value) => formatSentimentScore(Number(value))}
            />
            <Legend />
            <Bar dataKey="positive" fill="#10b981" />
            <Bar dataKey="neutral" fill="#6b7280" />
            <Bar dataKey="negative" fill="#ef4444" />
          </BarChart>
        );

      default: // line
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis yAxisId="left" domain={[-1, 1]} />
            {showVolume && <YAxis yAxisId="right" orientation="right" />}
            <Tooltip
              formatter={(value, name) => [
                name === "volume" ? value : formatSentimentScore(Number(value)),
                name === "volume"
                  ? "Volume"
                  : name.charAt(0).toUpperCase() + name.slice(1),
              ]}
            />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="overall_score"
              stroke="#3b82f6"
              strokeWidth={3}
              name="Overall Sentiment"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="positive"
              stroke="#10b981"
              strokeWidth={2}
              name="Positive"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="negative"
              stroke="#ef4444"
              strokeWidth={2}
              name="Negative"
            />
            {showVolume && (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="volume"
                stroke="#8b5cf6"
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Volume"
              />
            )}
          </LineChart>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
            Sentiment Trends
            {entityName && (
              <span className="ml-2 text-sm font-normal text-gray-600">
                for {entityName}
              </span>
            )}
          </h3>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-4 mb-6">
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">
              Time Range:
            </span>
            <select
              value={selectedTimeRange}
              onChange={(e) =>
                setSelectedTimeRange(e.target.value as "7d" | "30d" | "90d")
              }
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <Eye className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">
              Chart Type:
            </span>
            <select
              value={chartType}
              onChange={(e) =>
                setChartType(e.target.value as "line" | "area" | "bar")
              }
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="line">Line Chart</option>
              <option value="area">Area Chart</option>
              <option value="bar">Bar Chart</option>
            </select>
          </div>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showVolume}
              onChange={(e) => setShowVolume(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Show Volume</span>
          </label>
        </div>

        {/* Summary Stats */}
        {latestTrend && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div
                className="text-2xl font-bold"
                style={{ color: getSentimentColor(latestTrend.overall_score) }}
              >
                {formatSentimentScore(latestTrend.overall_score)}
              </div>
              <div className="text-sm text-gray-600">Current Sentiment</div>
              <div
                className={`text-xs mt-1 ${
                  overallChange > 0
                    ? "text-green-600"
                    : overallChange < 0
                    ? "text-red-600"
                    : "text-gray-600"
                }`}
              >
                {overallChange > 0 ? "+" : ""}
                {overallChange.toFixed(1)}% vs start
              </div>
            </div>

            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {totalMentions.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Total Mentions</div>
              <div className="text-xs text-gray-500 mt-1">
                {selectedTimeRange} period
              </div>
            </div>

            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {(avgVolatility * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Avg Volatility</div>
              <div className="text-xs text-gray-500 mt-1">
                Sentiment stability
              </div>
            </div>

            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {(() => {
                  const denominator =
                    (latestTrend?.positive || 0) +
                    (latestTrend?.negative || 0) +
                    (latestTrend?.neutral || 0);
                  return denominator > 0
                    ? Math.round(
                        ((latestTrend?.positive || 0) / denominator) * 100
                      ) + "%"
                    : "0%";
                })()}
              </div>
              <div className="text-sm text-gray-600">Positive Ratio</div>
              <div className="text-xs text-gray-500 mt-1">Latest period</div>
            </div>
          </div>
        )}

        {/* Chart */}
        {trends.length > 0 ? (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              {renderChart()}
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <TrendingUp className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg mb-2">No sentiment data available</p>
            <p className="text-sm">
              {entityName
                ? `No sentiment data found for ${entityName} in the selected time range.`
                : "Sentiment data will appear here once analysis begins."}
            </p>
          </div>
        )}
      </div>

      {/* Entity Sentiment Summary */}
      {!entityName && entities.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-4">
            Entity Sentiment Overview
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {entities.slice(0, 6).map((entity: EntitySentiment) => (
              <div
                key={`${entity.entity_name}-${entity.entity_type}`}
                className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="font-medium text-gray-900">
                      {entity.entity_name}
                    </div>
                    <div className="text-xs text-gray-600 capitalize">
                      {entity.entity_type}
                    </div>
                  </div>
                  {getTrendIcon(entity.trend_direction)}
                </div>

                <div className="flex items-center justify-between">
                  <div
                    className="text-lg font-bold"
                    style={{
                      color: getSentimentColor(entity.current_sentiment),
                    }}
                  >
                    {formatSentimentScore(entity.current_sentiment)}
                  </div>
                  <div className="text-right">
                    <div
                      className={`text-sm ${
                        entity.change_percent > 0
                          ? "text-green-600"
                          : entity.change_percent < 0
                          ? "text-red-600"
                          : "text-gray-600"
                      }`}
                    >
                      {entity.change_percent > 0 ? "+" : ""}
                      {entity.change_percent.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {entity.total_mentions} mentions
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
