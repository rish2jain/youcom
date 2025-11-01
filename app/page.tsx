"use client";

import React, { useState } from "react";
import {
  ArrowRight,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Activity,
  Loader2,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import { LearningLoop } from "@/components/LearningLoop";
import { useDashboardData } from "@/lib/hooks/useDashboardData";

interface Alert {
  id: string;
  company: string;
  riskScore: number;
  riskLevel: "high" | "medium" | "low";
  timeAgo: string;
  summary: string;
}

interface RecentResearch {
  id: string;
  company: string;
  sources: number;
  summary: string;
  completedAt: string;
}

export default function DashboardPage() {
  // Fetch data from APIs
  const { alerts, research, isLoading, hasError, refetch, dataUpdatedAt } = useDashboardData();
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Ensure alerts.data is always an array for safety
  const alertsData = Array.isArray(alerts?.data) ? alerts.data : [];
  const researchData = Array.isArray(research?.data) ? research.data : [];

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refetch();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const formatLastUpdated = (timestamp: number) => {
    if (!timestamp) return "Never";
    const now = Date.now();
    const diffMs = now - timestamp;
    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    
    if (diffSeconds < 10) return "Just now";
    if (diffSeconds < 60) return `${diffSeconds} seconds ago`;
    if (diffMinutes < 60) return `${diffMinutes} ${diffMinutes === 1 ? "minute" : "minutes"} ago`;
    return new Date(timestamp).toLocaleTimeString();
  };

  // Calculate highest threat score from actual data
  const highestThreat = alertsData.length > 0
    ? Math.max(...alertsData.map((a) => a.riskScore))
    : 0;

  const getRiskColor = (level: string) => {
    switch (level) {
      case "critical":
        return "text-red-700 bg-red-100 border-red-300";
      case "high":
        return "text-red-600 bg-red-50 border-red-200";
      case "medium":
        return "text-orange-600 bg-orange-50 border-orange-200";
      case "low":
        return "text-green-600 bg-green-50 border-green-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getRiskIcon = (level: string) => {
    if (level === "critical" || level === "high") return "🚨";
    if (level === "medium") return "⚠️";
    return "✅";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Value Proposition Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 py-4 px-6 rounded-lg text-white mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold mb-1">
                👔 Business Intelligence Dashboard
              </h2>
              <p className="text-blue-50 text-sm">
                <strong>So what?</strong> Track high-priority threats,
                competitor activity, and strategic insights in one place.
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">
                {isLoading ? (
                  <Loader2 className="w-8 h-8 animate-spin inline" />
                ) : (
                  `${highestThreat.toFixed(1)}/10`
                )}
              </div>
              <div className="text-blue-100 text-xs">
                Highest Current Threat
              </div>
            </div>
          </div>
        </div>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                Intelligence Dashboard
              </h1>
              <p className="text-gray-600">
                Your competitive intelligence alerts and recent analyses
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-gray-500">
                  Last updated: {formatLastUpdated(dataUpdatedAt)}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Auto-refreshes every hour
                </p>
              </div>
              <button
                onClick={handleRefresh}
                disabled={isRefreshing || isLoading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Refresh dashboard data"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
                {isRefreshing ? "Refreshing..." : "Refresh"}
              </button>
            </div>
          </div>
        </div>

        {/* Top Alerts Section */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">🎯 Top Alerts</h2>
            <Link
              href="/monitoring"
              className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-2"
            >
              View All Competitors
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {isLoading && alerts.isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="border-2 rounded-xl p-6 bg-gray-100 animate-pulse h-32"
                ></div>
              ))}
            </div>
          ) : alerts.error ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
              <p className="text-red-600 mb-2">
                Failed to load alerts. Please try again later.
              </p>
              <p className="text-sm text-red-500">
                {alerts.error instanceof Error
                  ? alerts.error.message
                  : "Unknown error"}
              </p>
            </div>
          ) : alertsData.length === 0 ? (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center">
              <p className="text-gray-600">
                No alerts available. Generate impact cards to see alerts here.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {alertsData.map((alert) => (
                <div
                  key={alert.id}
                  className={`border-2 rounded-xl p-6 transition-all hover:shadow-lg ${getRiskColor(
                    alert.riskLevel
                  )}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-2xl">
                          {getRiskIcon(alert.riskLevel)}
                        </span>
                        <h3 className="text-xl font-bold">
                          {alert.riskLevel.toUpperCase()} THREAT: {alert.company}
                        </h3>
                      </div>
                      <p className="text-gray-700 mb-3">{alert.summary}</p>
                      <div className="flex items-center gap-6 text-sm">
                        <span className="font-semibold">
                          Score: {alert.riskScore.toFixed(1)}/10
                        </span>
                        <span className="text-gray-600">{alert.timeAgo}</span>
                      </div>
                    </div>
                    <Link
                      href={`/research/${alert.id}`}
                      className="ml-4 px-4 py-2 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                    >
                      View Full Analysis
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Intelligence Section */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            📊 Recent Intelligence
          </h2>
          {isLoading && research.isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="bg-white border border-gray-200 rounded-xl p-6 animate-pulse h-48"
                ></div>
              ))}
            </div>
          ) : research.error ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
              <p className="text-red-600 mb-2">
                Failed to load research data. Please try again later.
              </p>
              <p className="text-sm text-red-500">
                {research.error instanceof Error
                  ? research.error.message
                  : "Unknown error"}
              </p>
            </div>
          ) : researchData.length === 0 ? (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 text-center">
              <p className="text-gray-600">
                No research available. Start researching companies to see them here.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {researchData.map((researchItem) => (
                <div
                  key={researchItem.id}
                  className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all"
                >
                  <div className="flex items-start justify-between mb-3">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                    <span className="text-sm text-gray-500">
                      {researchItem.completedAt}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">
                    {researchItem.company}
                  </h3>
                  <p className="text-gray-600 text-sm mb-4">
                    {researchItem.summary}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">
                      {researchItem.sources} sources analyzed
                    </span>
                    <div className="flex gap-2">
                      <Link
                        href={`/research/${researchItem.id}`}
                        className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                      >
                        View Report
                      </Link>
                      <button className="text-gray-600 hover:text-gray-700 text-sm font-medium">
                        Share
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Business Insights Section */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            💡 Key Insights This Week
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <TrendingUp className="w-8 h-8 text-blue-600" />
                <div className="text-2xl font-bold text-blue-900">
                  {isLoading ? (
                    <Loader2 className="w-8 h-8 animate-spin" />
                  ) : (
                    alertsData.length
                  )}
                </div>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">
                Active Alerts
              </h3>
              <p className="text-sm text-gray-700">
                {alertsData.length > 0
                  ? `${alertsData.length} ${alertsData.length === 1 ? "active threat" : "active threats"} requiring attention. Monitor competitor activity closely.`
                  : "No active alerts. Your competitive landscape is stable."}
              </p>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <AlertTriangle className="w-8 h-8 text-purple-600" />
                <div className="text-2xl font-bold text-purple-900">
                  {isLoading ? (
                    <Loader2 className="w-8 h-8 animate-spin" />
                  ) : (
                    `${highestThreat.toFixed(1)}/10`
                  )}
                </div>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">
                Highest Threat
              </h3>
              <p className="text-sm text-gray-700">
                {alertsData.length > 0
                  ? `${alertsData[0].company} poses ${alertsData[0].riskLevel} competitive threat. Recommend immediate response strategy.`
                  : "No threats detected. Monitor competitors to track risks."}
              </p>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <CheckCircle className="w-8 h-8 text-green-600" />
                <div className="text-2xl font-bold text-green-900">
                  {isLoading ? (
                    <Loader2 className="w-8 h-8 animate-spin" />
                  ) : (
                    researchData.length
                  )}
                </div>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">
                Reports Generated
              </h3>
              <p className="text-sm text-gray-700">
                {researchData.length > 0
                  ? `Comprehensive intelligence reports completed. ${researchData.length} ${researchData.length === 1 ? "report" : "reports"} available.`
                  : "No reports generated yet. Start researching companies to create reports."}
              </p>
            </div>
          </div>
        </div>

        {/* Learning Loop Section */}
        <div className="mb-12">
          <LearningLoop
            onInsightApplied={(insight) => {
              // Track insight application for analytics
              if (typeof window !== "undefined" && (window as any).gtag) {
                (window as any).gtag("event", "insight_applied", {
                  event_category: "learning",
                  event_label: insight.type || "unknown",
                  value: insight.confidence || 0,
                });
              }

              // Could also dispatch to state management or show toast notification
              // For now, we'll just track the event
            }}
          />
        </div>

        {/* Quick Actions */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl p-8 text-white">
          <h2 className="text-2xl font-bold mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link
              href="/monitoring"
              className="bg-white/20 hover:bg-white/30 backdrop-blur border border-white/30 rounded-lg p-4 text-center transition-all"
            >
              <TrendingUp className="w-8 h-8 mx-auto mb-2" />
              <div className="font-medium">Add Competitor</div>
            </Link>
            <Link
              href="/research"
              className="bg-white/20 hover:bg-white/30 backdrop-blur border border-white/30 rounded-lg p-4 text-center transition-all"
            >
              <Activity className="w-8 h-8 mx-auto mb-2" />
              <div className="font-medium">Research New</div>
            </Link>
            <Link
              href="/monitoring"
              className="bg-white/20 hover:bg-white/30 backdrop-blur border border-white/30 rounded-lg p-4 text-center transition-all"
            >
              <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
              <div className="font-medium">Go to Monitoring</div>
            </Link>
            <Link
              href="/settings"
              className="bg-white/20 hover:bg-white/30 backdrop-blur border border-white/30 rounded-lg p-4 text-center transition-all"
            >
              <CheckCircle className="w-8 h-8 mx-auto mb-2" />
              <div className="font-medium">View Settings</div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
