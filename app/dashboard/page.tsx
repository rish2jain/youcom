"use client";

import React from "react";
import dynamic from "next/dynamic";
import {
  ArrowRight,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Activity,
  Loader2,
  RefreshCw,
  HelpCircle,
} from "lucide-react";
import Link from "next/link";
import { useDashboardData } from "@/lib/hooks/useDashboardData";
import { useNotificationContext } from "@/app/notifications/NotificationProvider";

// Lazy load dashboard-specific components for better code splitting
const DashboardInsights = dynamic(
  () =>
    import("@/components/DashboardInsights")
      .then((mod) => ({ default: mod.default }))
      .catch((error) => {
        console.error("Failed to load DashboardInsights:", error);
        return {
          default: () => (
            <div className="h-48 bg-red-50 border border-red-200 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <p className="text-red-600 text-sm mb-2">
                  Failed to load insights
                </p>
                <button
                  onClick={() => window.location.reload()}
                  className="text-red-600 text-xs underline hover:no-underline"
                >
                  Retry
                </button>
              </div>
            </div>
          ),
        };
      }),
  {
    ssr: false,
    loading: () => (
      <div className="h-48 bg-gray-100 rounded-lg animate-pulse"></div>
    ),
  }
);

const QuickActions = dynamic(
  () =>
    import("@/components/QuickActions")
      .then((mod) => ({ default: mod.default }))
      .catch((error) => {
        console.error("Failed to load QuickActions:", error);
        return {
          default: () => (
            <div className="h-32 bg-red-50 border border-red-200 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <p className="text-red-600 text-sm mb-2">
                  Failed to load quick actions
                </p>
                <button
                  onClick={() => window.location.reload()}
                  className="text-red-600 text-xs underline hover:no-underline"
                >
                  Retry
                </button>
              </div>
            </div>
          ),
        };
      }),
  {
    ssr: false,
    loading: () => (
      <div className="h-32 bg-gray-100 rounded-lg animate-pulse"></div>
    ),
  }
);

export default function DashboardPage() {
  // Fetch data from APIs
  const { alerts, research, isLoading, hasError, refetch, dataUpdatedAt } = useDashboardData();
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const { addNotification } = useNotificationContext();

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

  const formatTimestamp = (timestamp: number) => {
    if (!timestamp) return "N/A";
    return new Date(timestamp).toISOString().replace("T", " ").substring(0, 19);
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
              <div className="flex items-center justify-end gap-2">
                <div className="text-2xl font-bold">
                  {isLoading ? (
                    <Loader2 className="w-8 h-8 animate-spin inline" />
                  ) : (
                    `${highestThreat.toFixed(1)}/10`
                  )}
                </div>
                <div className="group relative">
                  <HelpCircle className="w-4 h-4 text-blue-100 cursor-help" />
                  <div className="absolute bottom-full right-0 mb-2 p-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    Threat scores range from 0-10, where 10 represents maximum competitive threat. Scores are calculated based on competitor activity, market signals, and strategic moves.
                  </div>
                </div>
              </div>
              <div className="text-blue-100 text-xs">
                Highest Current Threat
              </div>
            </div>
          </div>
        </div>

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
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
                <p className="text-xs text-gray-400 mt-1" title={formatTimestamp(dataUpdatedAt)}>
                  {dataUpdatedAt ? formatTimestamp(dataUpdatedAt) : "Auto-refreshes every hour"}
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
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 border border-gray-200 rounded-xl p-6 text-center">
              <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                No Alerts Yet
              </h3>
              <p className="text-gray-600 mb-4">
                No alerts available. Generate impact cards to see alerts here.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
                <Link
                  href="/monitoring"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium inline-flex items-center gap-2"
                >
                  <Activity className="w-4 h-4" />
                  Add Competitor to Monitor
                </Link>
                <Link
                  href="/research"
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-medium inline-flex items-center gap-2"
                >
                  <TrendingUp className="w-4 h-4" />
                  Research a Company
                </Link>
              </div>
              <div className="mt-4 p-3 bg-blue-50 rounded-lg text-left max-w-md mx-auto">
                <p className="text-xs text-blue-800 mb-2">
                  <strong>💡 Tip:</strong> Alerts appear here when:
                </p>
                <ul className="text-xs text-blue-700 space-y-1 list-disc list-inside">
                  <li>Competitors make strategic moves</li>
                  <li>High-risk market signals are detected</li>
                  <li>Impact cards are generated from research</li>
                </ul>
              </div>
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
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 border border-gray-200 rounded-xl p-6 text-center">
              <CheckCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                No Research Reports Yet
              </h3>
              <p className="text-gray-600 mb-4">
                No research available. Start researching companies to see them here.
              </p>
              <Link
                href="/research"
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors font-medium inline-flex items-center gap-2"
              >
                <TrendingUp className="w-4 h-4" />
                Research Your First Company
              </Link>
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
                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                    {researchItem.summary || "Comprehensive research report generated using You.com APIs."}
                  </p>
                  
                  {/* Preview Key Insights */}
                  {researchItem.summary && (
                    <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-xs font-semibold text-blue-900 mb-1">
                        Key Insights Preview:
                      </p>
                      <p className="text-xs text-blue-800 line-clamp-2">
                        {researchItem.summary.length > 100 
                          ? `${researchItem.summary.substring(0, 100)}...`
                          : researchItem.summary}
                      </p>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">
                      {researchItem.sources || 0} sources analyzed
                    </span>
                    <div className="flex gap-2">
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          // Navigate to research page with company name if available
                          const companyName = researchItem.company || researchItem.company_name;
                          if (companyName) {
                            window.location.href = `/research?company=${encodeURIComponent(companyName)}`;
                          } else {
                            addNotification({
                              type: "warning",
                              message: "Report details may have been deleted. Generate a new report?",
                              autoClose: true,
                              duration: 5000,
                            });
                          }
                        }}
                        className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                      >
                        View Report
                      </button>
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
