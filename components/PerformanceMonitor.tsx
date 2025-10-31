"use client";

import { useEffect, useState } from "react";
import { Activity, Clock, Zap } from "lucide-react";

interface PerformanceMetrics {
  apiResponseTime: number;
  totalRequests: number;
  successRate: number;
  lastUpdated: string;
}

export function PerformanceMonitor() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    apiResponseTime: 0,
    successRate: 0,
    totalRequests: 0,
    lastUpdated: new Date().toISOString(),
  });

  useEffect(() => {
    // Fetch real performance metrics from usage tracker
    const fetchMetrics = async () => {
      try {
        const response = await fetch("/api/v1/metrics/api-usage?range=24h");
        const data = await response.json();

        setMetrics({
          apiResponseTime: data.average_latency_ms || 0,
          successRate: data.success_rate || 100,
          totalRequests: data.total_calls || 0,
          lastUpdated: new Date().toISOString(),
        });
      } catch (error) {
        console.warn("Failed to fetch performance metrics:", error);
        // Keep previous metrics on error
      }
    };

    // Initial fetch
    fetchMetrics();

    // Update every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);

    return () => clearInterval(interval);
  }, []);

  const getResponseTimeColor = (time: number) => {
    if (time < 1000) return "text-green-600";
    if (time < 2000) return "text-yellow-600";
    return "text-red-600";
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 98) return "text-green-600";
    if (rate >= 95) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border">
      <div className="flex items-center space-x-2 mb-3">
        <Activity className="w-4 h-4 text-blue-600" />
        <h4 className="font-medium text-gray-900">Performance Monitor</h4>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div
            className={`text-lg font-bold ${getResponseTimeColor(
              metrics.apiResponseTime
            )}`}
          >
            {Math.round(metrics.apiResponseTime)}ms
          </div>
          <div className="text-xs text-gray-500 flex items-center justify-center space-x-1">
            <Clock className="w-3 h-3" />
            <span>Response Time</span>
          </div>
        </div>

        <div className="text-center">
          <div
            className={`text-lg font-bold ${getSuccessRateColor(
              metrics.successRate
            )}`}
          >
            {metrics.successRate.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500 flex items-center justify-center space-x-1">
            <Zap className="w-3 h-3" />
            <span>Success Rate</span>
          </div>
        </div>

        <div className="text-center">
          <div className="text-lg font-bold text-blue-600">
            {metrics.totalRequests}
          </div>
          <div className="text-xs text-gray-500">Total Requests</div>
        </div>
      </div>

      <div className="mt-2 text-xs text-gray-400 text-center">
        Last updated: {new Date(metrics.lastUpdated).toLocaleTimeString()}
      </div>
    </div>
  );
}
