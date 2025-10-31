"use client";

import { useState } from "react";
import { EnhancedAnalytics } from "@/components/EnhancedAnalytics";
import { Activity, CheckCircle, AlertTriangle, Clock } from "lucide-react";
import { APIOrchestrationStory } from "@/components/APIOrchestrationStory";
import { LiveAPITracker } from "@/components/LiveAPITracker";
import { HowItWorksSection } from "@/components/HowItWorksSection";
import { ValidationSection } from "@/components/ValidationSection";
import { ErrorStateDemo } from "@/components/ErrorStates";

interface APIActivity {
  apiName: string;
  calls24h: number;
  successRate: number;
  avgResponseTime: string;
  status: "healthy" | "warning" | "error";
}

export default function AnalyticsPage() {
  const [apiActivity] = useState<APIActivity[]>([
    {
      apiName: "News API",
      calls24h: 15,
      successRate: 100,
      avgResponseTime: "1.2s",
      status: "healthy",
    },
    {
      apiName: "Search API",
      calls24h: 14,
      successRate: 100,
      avgResponseTime: "0.8s",
      status: "healthy",
    },
    {
      apiName: "Chat API",
      calls24h: 9,
      successRate: 100,
      avgResponseTime: "2.5s",
      status: "healthy",
    },
    {
      apiName: "ARI API",
      calls24h: 9,
      successRate: 98.5,
      avgResponseTime: "3.1s",
      status: "warning",
    },
  ]);

  const totalCalls = apiActivity.reduce((sum, api) => sum + api.calls24h, 0);
  const avgSuccessRate = (
    apiActivity.reduce((sum, api) => sum + api.successRate, 0) /
    apiActivity.length
  ).toFixed(1);

  const getStatusIcon = (status: string) => {
    if (status === "healthy") return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (status === "warning") return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
    return <AlertTriangle className="w-5 h-5 text-red-600" />;
  };

  const getStatusColor = (status: string) => {
    if (status === "healthy") return "bg-green-50 border-green-200";
    if (status === "warning") return "bg-yellow-50 border-yellow-200";
    return "bg-red-50 border-red-200";
  };

  return (
    <div className="space-y-8">
      {/* Value Proposition Header */}
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 py-4 px-6 rounded-lg text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold mb-1">🔧 For Technical Teams</h2>
            <p className="text-purple-50 text-sm">
              <strong>So what?</strong> Monitor API performance, validate data quality, and understand system architecture in real-time.
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">{avgSuccessRate}%</div>
            <div className="text-purple-100 text-xs">Average Success Rate</div>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Predictive Analytics & API Performance
        </h1>
        <p className="text-gray-600 mb-4">
          Advanced analytics and real-time API performance monitoring powered by
          competitive intelligence data from You.com APIs.
        </p>
      </div>

      {/* Live API Activity Section */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Activity className="w-6 h-6 text-blue-600" />
              Live API Activity (24h)
            </h2>
            <p className="text-gray-600 text-sm mt-1">
              Real-time monitoring of You.com API performance and health
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-blue-600">{totalCalls}</div>
            <div className="text-sm text-gray-600">Total API Calls</div>
            <div className="text-sm font-medium text-green-600 mt-1">
              {avgSuccessRate}% Success Rate
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {apiActivity.map((api, index) => (
            <div
              key={index}
              className={`border-2 rounded-lg p-4 transition-all hover:shadow-md ${getStatusColor(
                api.status
              )}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  {getStatusIcon(api.status)}
                  <h3 className="font-bold text-gray-900">{api.apiName}</h3>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Calls (24h):</span>
                  <span className="font-semibold text-gray-900">{api.calls24h}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Success Rate:</span>
                  <span
                    className={`font-semibold ${
                      api.successRate === 100
                        ? "text-green-600"
                        : api.successRate >= 95
                        ? "text-yellow-600"
                        : "text-red-600"
                    }`}
                  >
                    {api.successRate}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Avg Response:
                  </span>
                  <span className="font-semibold text-gray-900">
                    {api.avgResponseTime}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-gray-600">Healthy</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <span className="text-gray-600">Warning</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span className="text-gray-600">Error</span>
              </div>
            </div>
            <span className="text-gray-500">Last updated: 2 minutes ago</span>
          </div>
        </div>
      </div>

      <EnhancedAnalytics />

      {/* Technical Deep Dive Sections */}
      <div className="space-y-8">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 rounded-lg text-white">
          <h2 className="text-2xl font-bold mb-2">🔧 Technical Deep Dive</h2>
          <p className="text-blue-50">
            Explore how our 4-API orchestration works under the hood with live tracking,
            validation, and error handling demonstrations.
          </p>
        </div>

        {/* API Orchestration Story */}
        <APIOrchestrationStory />

        {/* Live API Tracker */}
        <LiveAPITracker />

        {/* How It Works Section */}
        <HowItWorksSection />

        {/* Validation Section */}
        <ValidationSection />

        {/* Error Handling Demo */}
        <ErrorStateDemo />
      </div>
    </div>
  );
}
