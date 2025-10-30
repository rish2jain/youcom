"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Clock,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Activity,
} from "lucide-react";

interface DeltaHighlight {
  id: number;
  highlight_type: string;
  title: string;
  description?: string;
  importance_score: number;
  freshness_hours?: number;
  badge_type?: string;
  badge_color?: string;
  source_url?: string;
  source_name?: string;
  created_at: string;
  is_dismissed: boolean;
}

interface TrendSparkline {
  id: number;
  company_name: string;
  metric_type: string;
  data_points: Array<{ timestamp: string; value: number }>;
  time_range: string;
  trend_direction?: string;
  trend_strength?: number;
}

interface InsightTimelineData {
  id: number;
  company_name: string;
  current_risk_score: number;
  previous_risk_score?: number;
  risk_score_delta?: number;
  new_stories_count: number;
  updated_stories_count: number;
  new_evidence_count: number;
  key_changes?: string[];
  fresh_insights?: string[];
  trend_shifts?: string[];
  created_at: string;
  previous_analysis_date?: string;
  confidence_score?: number;
  delta_highlights: DeltaHighlight[];
}

interface InsightDeltaResponse {
  timeline: InsightTimelineData;
  sparkline_data?: TrendSparkline;
  summary: {
    status: string;
    message: string;
    time_since_last?: {
      hours: number;
      formatted: string;
    };
    key_metrics: {
      risk_score: number;
      risk_score_change?: number;
      new_stories: number;
      updated_stories: number;
      evidence_count: number;
    };
  };
  recommendations: string[];
}

interface InsightTimelineProps {
  companyName: string;
  impactCardId: number;
  onAnalyzeComplete?: (data: InsightDeltaResponse) => void;
}

const InsightTimeline: React.FC<InsightTimelineProps> = ({
  companyName,
  impactCardId,
  onAnalyzeComplete,
}) => {
  const [deltaData, setDeltaData] = useState<InsightDeltaResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeDelta = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/enhancements/timeline/${encodeURIComponent(
          companyName
        )}/analyze-delta?impact_card_id=${impactCardId}`,
        { method: "POST" }
      );

      if (!response.ok) {
        throw new Error(`Failed to analyze delta: ${response.statusText}`);
      }

      const data: InsightDeltaResponse = await response.json();
      setDeltaData(data);
      onAnalyzeComplete?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze delta");
    } finally {
      setIsLoading(false);
    }
  };

  const getBadgeVariant = (badgeColor?: string) => {
    switch (badgeColor) {
      case "green":
        return "default";
      case "blue":
        return "secondary";
      case "yellow":
        return "outline";
      case "red":
        return "destructive";
      default:
        return "secondary";
    }
  };

  const getBadgeIcon = (badgeType?: string) => {
    switch (badgeType) {
      case "new":
        return <Sparkles className="w-3 h-3" />;
      case "updated":
        return <Activity className="w-3 h-3" />;
      case "trending":
        return <TrendingUp className="w-3 h-3" />;
      case "alert":
        return <AlertTriangle className="w-3 h-3" />;
      default:
        return <Info className="w-3 h-3" />;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays}d ago`;
    } else if (diffHours > 0) {
      return `${diffHours}h ago`;
    } else {
      return "Just now";
    }
  };

  const renderSparkline = (sparklineData: TrendSparkline) => {
    if (!sparklineData.data_points || sparklineData.data_points.length < 2) {
      return null;
    }

    const points = sparklineData.data_points.slice(-10); // Last 10 points
    const maxValue = Math.max(...points.map((p) => p.value));
    const minValue = Math.min(...points.map((p) => p.value));
    const range = maxValue - minValue || 1;

    const pathData = points
      .map((point, index) => {
        const x = (index / (points.length - 1)) * 100;
        const y = 100 - ((point.value - minValue) / range) * 100;
        return `${index === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");

    const trendColor =
      sparklineData.trend_direction === "up"
        ? "#10b981"
        : sparklineData.trend_direction === "down"
        ? "#ef4444"
        : "#6b7280";

    return (
      <div className="flex items-center space-x-2">
        <svg width="60" height="20" className="overflow-visible">
          <path
            d={pathData}
            stroke={trendColor}
            strokeWidth="2"
            fill="none"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        <div className="flex items-center space-x-1">
          {sparklineData.trend_direction === "up" && (
            <TrendingUp className="w-3 h-3 text-green-500" />
          )}
          {sparklineData.trend_direction === "down" && (
            <TrendingDown className="w-3 h-3 text-red-500" />
          )}
          <span className="text-xs text-gray-500">
            {sparklineData.time_range}
          </span>
        </div>
      </div>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center space-x-2">
            <Clock className="w-5 h-5" />
            <span>Since Your Last Analysis</span>
          </CardTitle>
          <Button
            onClick={analyzeDelta}
            disabled={isLoading}
            size="sm"
            variant="outline"
          >
            {isLoading ? "Analyzing..." : "Check for Changes"}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {deltaData && (
          <>
            {/* Summary Section */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-medium text-gray-900">
                  {deltaData.summary.message}
                </h3>
                {deltaData.sparkline_data &&
                  renderSparkline(deltaData.sparkline_data)}
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Risk Score</span>
                  <div className="flex items-center space-x-1">
                    <span className="font-medium">
                      {deltaData.summary.key_metrics.risk_score}
                    </span>
                    {deltaData.summary.key_metrics.risk_score_change && (
                      <span
                        className={`text-xs ${
                          deltaData.summary.key_metrics.risk_score_change > 0
                            ? "text-red-500"
                            : "text-green-500"
                        }`}
                      >
                        (
                        {deltaData.summary.key_metrics.risk_score_change > 0
                          ? "+"
                          : ""}
                        {deltaData.summary.key_metrics.risk_score_change.toFixed(
                          1
                        )}
                        )
                      </span>
                    )}
                  </div>
                </div>
                <div>
                  <span className="text-gray-500">New Stories</span>
                  <p className="font-medium">
                    {deltaData.summary.key_metrics.new_stories}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Updated</span>
                  <p className="font-medium">
                    {deltaData.summary.key_metrics.updated_stories}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Evidence</span>
                  <p className="font-medium">
                    {deltaData.summary.key_metrics.evidence_count}
                  </p>
                </div>
              </div>
            </div>

            {/* Delta Highlights */}
            {deltaData.timeline.delta_highlights &&
              deltaData.timeline.delta_highlights.length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-900">Key Changes</h4>
                  {deltaData.timeline.delta_highlights.map((highlight) => (
                    <div
                      key={highlight.id}
                      className="flex items-start space-x-3 p-3 bg-white border rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex-shrink-0 mt-0.5">
                        {getBadgeIcon(highlight.badge_type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h5 className="font-medium text-sm text-gray-900 truncate">
                            {highlight.title}
                          </h5>
                          <Badge
                            variant={getBadgeVariant(highlight.badge_color)}
                            className="text-xs"
                          >
                            {highlight.badge_type}
                          </Badge>
                          {highlight.freshness_hours !== undefined && (
                            <span className="text-xs text-gray-500">
                              {highlight.freshness_hours}h ago
                            </span>
                          )}
                        </div>
                        {highlight.description && (
                          <p className="text-sm text-gray-600">
                            {highlight.description}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

            {/* Expandable Details */}
            <div className="border-t pt-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full justify-between"
              >
                <span>View Details</span>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </Button>

              {isExpanded && (
                <div className="mt-4 space-y-4">
                  {/* Key Changes */}
                  {deltaData.timeline.key_changes &&
                    deltaData.timeline.key_changes.length > 0 && (
                      <div>
                        <h5 className="font-medium text-sm text-gray-900 mb-2">
                          Key Changes
                        </h5>
                        <ul className="space-y-1">
                          {deltaData.timeline.key_changes.map(
                            (change, index) => (
                              <li
                                key={index}
                                className="text-sm text-gray-600 flex items-start space-x-2"
                              >
                                <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                                <span>{change}</span>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {/* Fresh Insights */}
                  {deltaData.timeline.fresh_insights &&
                    deltaData.timeline.fresh_insights.length > 0 && (
                      <div>
                        <h5 className="font-medium text-sm text-gray-900 mb-2">
                          Fresh Insights
                        </h5>
                        <ul className="space-y-1">
                          {deltaData.timeline.fresh_insights.map(
                            (insight, index) => (
                              <li
                                key={index}
                                className="text-sm text-gray-600 flex items-start space-x-2"
                              >
                                <Sparkles className="w-3 h-3 text-yellow-500 mt-0.5 flex-shrink-0" />
                                <span>{insight}</span>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}

                  {/* Recommendations */}
                  {deltaData.recommendations &&
                    deltaData.recommendations.length > 0 && (
                      <div>
                        <h5 className="font-medium text-sm text-gray-900 mb-2">
                          Recommendations
                        </h5>
                        <ul className="space-y-1">
                          {deltaData.recommendations.map((rec, index) => (
                            <li
                              key={index}
                              className="text-sm text-gray-600 flex items-start space-x-2"
                            >
                              <span className="w-1.5 h-1.5 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                </div>
              )}
            </div>
          </>
        )}

        {!deltaData && !isLoading && (
          <div className="text-center py-8 text-gray-500">
            <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>
              Click "Check for Changes" to see what's new since your last
              analysis
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default InsightTimeline;
