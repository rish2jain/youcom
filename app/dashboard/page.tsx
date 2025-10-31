"use client";

import { useState } from "react";
import { ArrowRight, AlertTriangle, CheckCircle, TrendingUp, Activity } from "lucide-react";
import Link from "next/link";

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
  // Sample data - in production, this would come from API/database
  const [alerts] = useState<Alert[]>([
    {
      id: "1",
      company: "OpenAI GPT-4 Turbo",
      riskScore: 8.8,
      riskLevel: "high",
      timeAgo: "2 minutes ago",
      summary: "Major model release with 128K context window and vision capabilities",
    },
    {
      id: "2",
      company: "Anthropic Claude 3",
      riskScore: 6.2,
      riskLevel: "medium",
      timeAgo: "4 hours ago",
      summary: "New pricing model and enterprise features announced",
    },
    {
      id: "3",
      company: "Google Gemini Ultra",
      riskScore: 5.5,
      riskLevel: "medium",
      timeAgo: "1 day ago",
      summary: "Integration with Google Workspace announced",
    },
  ]);

  const [recentResearch] = useState<RecentResearch[]>([
    {
      id: "1",
      company: "Perplexity AI",
      sources: 387,
      summary: "AI-powered search engine with real-time web integration...",
      completedAt: "3 hours ago",
    },
    {
      id: "2",
      company: "Anthropic",
      sources: 412,
      summary: "Claude LLM company focusing on safety and interpretability...",
      completedAt: "1 day ago",
    },
    {
      id: "3",
      company: "Stripe",
      sources: 445,
      summary: "Payment infrastructure with developer-first API design...",
      completedAt: "2 days ago",
    },
  ]);

  const getRiskColor = (level: string) => {
    switch (level) {
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
    if (level === "high") return "🚨";
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
              <h2 className="text-xl font-bold mb-1">👔 Business Intelligence Dashboard</h2>
              <p className="text-blue-50 text-sm">
                <strong>So what?</strong> Track high-priority threats, competitor activity, and strategic insights in one place.
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">8.8/10</div>
              <div className="text-blue-100 text-xs">Highest Current Threat</div>
            </div>
          </div>
        </div>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Intelligence Dashboard</h1>
          <p className="text-gray-600">Your competitive intelligence alerts and recent analyses</p>
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

          <div className="space-y-4">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`border-2 rounded-xl p-6 transition-all hover:shadow-lg ${getRiskColor(
                  alert.riskLevel
                )}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{getRiskIcon(alert.riskLevel)}</span>
                      <h3 className="text-xl font-bold">
                        {alert.riskLevel.toUpperCase()} THREAT: {alert.company}
                      </h3>
                    </div>
                    <p className="text-gray-700 mb-3">{alert.summary}</p>
                    <div className="flex items-center gap-6 text-sm">
                      <span className="font-semibold">Score: {alert.riskScore}/10</span>
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
        </div>

        {/* Recent Intelligence Section */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">📊 Recent Intelligence</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {recentResearch.map((research) => (
              <div
                key={research.id}
                className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all"
              >
                <div className="flex items-start justify-between mb-3">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                  <span className="text-sm text-gray-500">{research.completedAt}</span>
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{research.company}</h3>
                <p className="text-gray-600 text-sm mb-4">{research.summary}</p>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    {research.sources} sources analyzed
                  </span>
                  <div className="flex gap-2">
                    <Link
                      href={`/research/${research.id}`}
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
        </div>

        {/* Business Insights Section */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">💡 Key Insights This Week</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <TrendingUp className="w-8 h-8 text-blue-600" />
                <div className="text-2xl font-bold text-blue-900">+40%</div>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Competitor Activity</h3>
              <p className="text-sm text-gray-700">
                Your competitors' product launches increased this week. 3 major announcements detected.
              </p>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <AlertTriangle className="w-8 h-8 text-purple-600" />
                <div className="text-2xl font-bold text-purple-900">8.8/10</div>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Highest Threat</h3>
              <p className="text-sm text-gray-700">
                OpenAI GPT-4 Turbo poses significant competitive threat. Recommend immediate response strategy.
              </p>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <CheckCircle className="w-8 h-8 text-green-600" />
                <div className="text-2xl font-bold text-green-900">12</div>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Reports Generated</h3>
              <p className="text-sm text-gray-700">
                Comprehensive intelligence reports completed this week. All high-priority competitors covered.
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
