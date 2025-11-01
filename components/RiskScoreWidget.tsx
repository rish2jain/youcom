"use client";

import React, { memo, useState, useEffect } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { api } from "@/lib/api";

interface ImpactCard {
  id: number;
  competitor_name: string;
  risk_score: number;
  risk_level: string;
  confidence_score: number;
  impact_areas: Array<{
    area: string;
    impact_score: number;
    description: string;
  }>;
  credibility_score: number;
  created_at: string;
}

interface RiskScoreWidgetProps {
  card: ImpactCard;
  isExpanded: boolean;
  onToggle: () => void;
}

interface TrendData {
  created_at: string | null;
  risk_score: number;
  credibility_score: number;
}

const RiskScoreWidget = memo<RiskScoreWidgetProps>(
  ({ card, isExpanded, onToggle }) => {
    const [trendData, setTrendData] = useState<TrendData[]>([]);
    const [trendLoading, setTrendLoading] = useState(false);
    const [showBreakdown, setShowBreakdown] = useState(false);

    // Fetch trend data when component mounts or card changes
    useEffect(() => {
      if (!card) return;

      setTrendLoading(true);
      api
        .get("/api/v1/impact/comparison", {
          params: { competitors: card.competitor_name },
        })
        .then((res) => {
          const series = res.data.series?.[card.competitor_name] ?? [];
          setTrendData(series);
        })
        .catch(() => {
          setTrendData([]);
        })
        .finally(() => setTrendLoading(false));
    }, [card]);

    const getRiskColor = (riskLevel: string) => {
      switch (riskLevel) {
        case "critical":
          return "text-red-600 bg-red-100";
        case "high":
          return "text-orange-600 bg-orange-100";
        case "medium":
          return "text-yellow-600 bg-yellow-100";
        case "low":
          return "text-green-600 bg-green-100";
        default:
          return "text-gray-600 bg-gray-100";
      }
    };

    const getRiskGaugeColor = (score: number) => {
      if (score >= 80) return "#ef4444"; // red
      if (score >= 60) return "#f97316"; // orange
      if (score >= 40) return "#eab308"; // yellow
      return "#22c55e"; // green
    };

    const calculateTrend = () => {
      if (trendData.length < 2) return "stable";

      const recent = trendData.slice(-2);
      const diff = recent[1].risk_score - recent[0].risk_score;

      if (diff > 5) return "up";
      if (diff < -5) return "down";
      return "stable";
    };

    const getTrendIcon = (trend: string) => {
      switch (trend) {
        case "up":
          return <TrendingUp className="w-4 h-4 text-red-500" />;
        case "down":
          return <TrendingDown className="w-4 h-4 text-green-500" />;
        default:
          return <Minus className="w-4 h-4 text-gray-500" />;
      }
    };

    const getTrendColor = (trend: string) => {
      switch (trend) {
        case "up":
          return "text-red-600";
        case "down":
          return "text-green-600";
        default:
          return "text-gray-600";
      }
    };

    const trend = calculateTrend();

    // Prepare gauge data
    const gaugeData = [
      {
        value: card.risk_score,
        fill: getRiskGaugeColor(card.risk_score),
      },
      {
        value: 100 - card.risk_score,
        fill: "#e5e7eb",
      },
    ];

    // Prepare trend chart data
    const chartData = trendData.map((point) => ({
      time: point.created_at
        ? new Date(point.created_at).toLocaleDateString()
        : "Unknown",
      risk: point.risk_score,
      credibility: Math.round(point.credibility_score * 100),
    }));

    return (
      <div className="mb-6 border border-gray-200 rounded-lg">
        {/* Header */}
        <div
          className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={onToggle}
        >
          <div className="flex justify-between items-center">
            <h5 className="font-semibold text-gray-900 flex items-center space-x-2">
              <span>Risk Score Analysis</span>
              {getTrendIcon(trend)}
            </h5>
            <div className="flex items-center space-x-2">
              <span className={`text-sm ${getTrendColor(trend)}`}>
                {trend === "up" && "Increasing Risk"}
                {trend === "down" && "Decreasing Risk"}
                {trend === "stable" && "Stable"}
              </span>
              {isExpanded ? (
                <ChevronUp className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              )}
            </div>
          </div>
        </div>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-100">
            {/* Risk Score Gauge and Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6 mt-4">
              {/* Risk Score Gauge */}
              <div className="text-center">
                <div className="relative w-32 h-32 mx-auto mb-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={gaugeData}
                        cx="50%"
                        cy="50%"
                        startAngle={90}
                        endAngle={-270}
                        innerRadius={40}
                        outerRadius={60}
                        dataKey="value"
                      >
                        {gaugeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {card.risk_score}
                      </div>
                      <div className="text-xs text-gray-500">Risk Score</div>
                    </div>
                  </div>
                </div>
                <div
                  className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(
                    card.risk_level
                  )}`}
                >
                  {card.risk_level.toUpperCase()} RISK
                </div>
              </div>

              {/* Confidence Score */}
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">
                  {card.confidence_score}%
                </div>
                <div className="text-sm text-gray-600">Confidence Score</div>
                <div className="text-xs text-gray-500 mt-1">
                  AI Analysis Confidence
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${card.confidence_score}%` }}
                  ></div>
                </div>
              </div>

              {/* Credibility Score */}
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 mb-2">
                  {Math.round(card.credibility_score * 100)}%
                </div>
                <div className="text-sm text-gray-600">Credibility Score</div>
                <div className="text-xs text-gray-500 mt-1">
                  Source Quality Rating
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div
                    className="bg-green-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${card.credibility_score * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>

            {/* Impact Areas Breakdown */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-3">
                <h6 className="font-medium text-gray-900">Impact Breakdown</h6>
                <button
                  onClick={() => setShowBreakdown(!showBreakdown)}
                  className="text-sm text-blue-600 hover:underline"
                >
                  {showBreakdown ? "Hide" : "Show"} Details
                </button>
              </div>

              {showBreakdown && card.impact_areas.length > 0 && (
                <div className="space-y-3">
                  {card.impact_areas.map((area, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium capitalize text-sm">
                          {area.area}
                        </span>
                        <span
                          className="text-sm font-medium"
                          style={{
                            color: getRiskGaugeColor(area.impact_score),
                          }}
                        >
                          {area.impact_score}/100
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                        <div
                          className="h-2 rounded-full transition-all duration-500"
                          style={{
                            width: `${area.impact_score}%`,
                            backgroundColor: getRiskGaugeColor(
                              area.impact_score
                            ),
                          }}
                        ></div>
                      </div>
                      <p className="text-xs text-gray-600">
                        {area.description}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Trend Chart */}
            {chartData.length > 1 && (
              <div className="mb-4">
                <h6 className="font-medium text-gray-900 mb-3">Risk Trend</h6>
                {trendLoading ? (
                  <div className="text-sm text-gray-500 text-center py-8">
                    Loading trend data...
                  </div>
                ) : (
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData}>
                        <XAxis
                          dataKey="time"
                          tick={{ fontSize: 12 }}
                          interval="preserveStartEnd"
                        />
                        <YAxis tick={{ fontSize: 12 }} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "white",
                            border: "1px solid #e5e7eb",
                            borderRadius: "6px",
                            fontSize: "12px",
                          }}
                        />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="risk"
                          name="Risk Score"
                          stroke="#2563eb"
                          strokeWidth={2}
                          dot={{ fill: "#2563eb", strokeWidth: 2, r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                        <Line
                          type="monotone"
                          dataKey="credibility"
                          name="Credibility %"
                          stroke="#10b981"
                          strokeWidth={2}
                          dot={{ fill: "#10b981", strokeWidth: 2, r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
            )}

            {/* Risk Level Explanation */}
            <div className="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg">
              <strong>Risk Level Guide:</strong>
              <div className="mt-1 space-y-1">
                <div>
                  • <span className="text-red-600">Critical (80-100):</span>{" "}
                  Immediate action required
                </div>
                <div>
                  • <span className="text-orange-600">High (60-79):</span>{" "}
                  Monitor closely, plan response
                </div>
                <div>
                  • <span className="text-yellow-600">Medium (40-59):</span>{" "}
                  Keep informed, assess impact
                </div>
                <div>
                  • <span className="text-green-600">Low (0-39):</span>{" "}
                  Awareness level monitoring
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }
);

RiskScoreWidget.displayName = "RiskScoreWidget";

export default RiskScoreWidget;
