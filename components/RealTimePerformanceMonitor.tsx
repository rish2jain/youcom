"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Bell,
  BellOff,
} from "lucide-react";
import { api } from "@/lib/api";
import { getSocket } from "@/lib/socket";

interface RealTimeMetric {
  timestamp: string;
  response_time: number;
  accuracy: number;
  throughput: number;
  error_rate: number;
  active_connections: number;
}

interface PerformanceAlert {
  id: string;
  type: "warning" | "critical" | "info";
  metric: string;
  message: string;
  value: number;
  threshold: number;
  timestamp: string;
  acknowledged: boolean;
}

interface SystemStatus {
  overall_health: "healthy" | "degraded" | "critical";
  api_status: "operational" | "degraded" | "down";
  ml_pipeline_status: "operational" | "degraded" | "down";
  database_status: "operational" | "degraded" | "down";
  last_updated: string;
}

export function RealTimePerformanceMonitor() {
  const [realtimeData, setRealtimeData] = useState<RealTimeMetric[]>([]);
  const [alerts, setAlerts] = useState<PerformanceAlert[]>([]);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState<string>("response_time");

  const { data: systemStatus, isLoading: statusLoading } = useQuery({
    queryKey: ["systemStatus"],
    queryFn: () => api.get("/api/v1/monitoring/status").then((res) => res.data),
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // 30 seconds
  });

  const { data: currentAlerts, isLoading: alertsLoading } = useQuery({
    queryKey: ["performanceAlerts"],
    queryFn: () =>
      api.get("/api/v1/monitoring/alerts").then((res) => res.data.alerts),
    staleTime: 5000, // 5 seconds
    refetchInterval: 15000, // 15 seconds
  });

  useEffect(() => {
    const socket = getSocket();
    socket.emit("join_room", { room: "performance_monitoring" });

    const handleMetricUpdate = (data: RealTimeMetric) => {
      setRealtimeData((prev) => {
        const newData = [...prev, data].slice(-50); // Keep last 50 data points
        return newData;
      });
    };

    const handleAlert = (alert: PerformanceAlert) => {
      if (alertsEnabled) {
        setAlerts((prev) => [alert, ...prev.slice(0, 9)]); // Keep last 10 alerts

        // Show browser notification for critical alerts
        if (alert.type === "critical" && "Notification" in window) {
          if (Notification.permission === "granted") {
            new Notification(`Critical Alert: ${alert.metric}`, {
              body: alert.message,
              icon: "/favicon.ico",
            });
          }
        }
      }
    };

    socket.on("performance_metric", handleMetricUpdate);
    socket.on("performance_alert", handleAlert);

    return () => {
      socket.emit("leave_room", { room: "performance_monitoring" });
      socket.off("performance_metric", handleMetricUpdate);
      socket.off("performance_alert", handleAlert);
    };
  }, [alertsEnabled]);

  useEffect(() => {
    if (currentAlerts) {
      setAlerts(currentAlerts);
    }
  }, [currentAlerts]);

  const status = systemStatus || {};
  const latestMetric = realtimeData[realtimeData.length - 1];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "operational":
      case "healthy":
        return "text-green-600 bg-green-100";
      case "degraded":
        return "text-yellow-600 bg-yellow-100";
      case "down":
      case "critical":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case "critical":
        return "text-red-600 bg-red-100 border-red-200";
      case "warning":
        return "text-yellow-600 bg-yellow-100 border-yellow-200";
      case "info":
        return "text-blue-600 bg-blue-100 border-blue-200";
      default:
        return "text-gray-600 bg-gray-100 border-gray-200";
    }
  };

  const formatMetricValue = (value: number, metric: string) => {
    if (!value) return "0";

    switch (metric) {
      case "response_time":
        return `${value.toFixed(2)}s`;
      case "accuracy":
        return `${Math.round(value * 100)}%`;
      case "throughput":
        return `${value.toFixed(0)}/min`;
      case "error_rate":
        return `${(value * 100).toFixed(2)}%`;
      case "active_connections":
        return value.toString();
      default:
        return value.toString();
    }
  };

  const requestNotificationPermission = async () => {
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission();
    }
  };

  useEffect(() => {
    requestNotificationPermission();
  }, []);

  if (statusLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* System Status Overview */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-blue-600" />
            Real-Time Performance Monitor
          </h3>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setAlertsEnabled(!alertsEnabled)}
              className={`flex items-center space-x-2 px-3 py-2 text-sm rounded-lg ${
                alertsEnabled
                  ? "bg-blue-100 text-blue-700"
                  : "bg-gray-100 text-gray-700"
              }`}
            >
              {alertsEnabled ? (
                <Bell className="w-4 h-4" />
              ) : (
                <BellOff className="w-4 h-4" />
              )}
              <span>{alertsEnabled ? "Alerts On" : "Alerts Off"}</span>
            </button>
            <div className="text-sm text-gray-600">
              Last updated:{" "}
              {status.last_updated
                ? new Date(status.last_updated).toLocaleTimeString()
                : "Never"}
            </div>
          </div>
        </div>

        {/* System Health Status */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                status.overall_health
              )}`}
            >
              {status.overall_health === "healthy" ? (
                <CheckCircle className="w-4 h-4 mr-1" />
              ) : (
                <AlertTriangle className="w-4 h-4 mr-1" />
              )}
              {status.overall_health?.toUpperCase() || "UNKNOWN"}
            </div>
            <div className="text-xs text-gray-600 mt-2">Overall Health</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                status.api_status
              )}`}
            >
              {status.api_status?.toUpperCase() || "UNKNOWN"}
            </div>
            <div className="text-xs text-gray-600 mt-2">API Status</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                status.ml_pipeline_status
              )}`}
            >
              {status.ml_pipeline_status?.toUpperCase() || "UNKNOWN"}
            </div>
            <div className="text-xs text-gray-600 mt-2">ML Pipeline</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(
                status.database_status
              )}`}
            >
              {status.database_status?.toUpperCase() || "UNKNOWN"}
            </div>
            <div className="text-xs text-gray-600 mt-2">Database</div>
          </div>
        </div>

        {/* Current Metrics */}
        {latestMetric && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-xl font-bold text-blue-600">
                {formatMetricValue(latestMetric.response_time, "response_time")}
              </div>
              <div className="text-xs text-gray-600">Response Time</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-xl font-bold text-green-600">
                {formatMetricValue(latestMetric.accuracy, "accuracy")}
              </div>
              <div className="text-xs text-gray-600">Accuracy</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-xl font-bold text-purple-600">
                {formatMetricValue(latestMetric.throughput, "throughput")}
              </div>
              <div className="text-xs text-gray-600">Throughput</div>
            </div>
            <div className="text-center p-3 bg-orange-50 rounded-lg">
              <div className="text-xl font-bold text-orange-600">
                {formatMetricValue(latestMetric.error_rate, "error_rate")}
              </div>
              <div className="text-xs text-gray-600">Error Rate</div>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <div className="text-xl font-bold text-gray-600">
                {formatMetricValue(
                  latestMetric.active_connections,
                  "active_connections"
                )}
              </div>
              <div className="text-xs text-gray-600">Connections</div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Real-Time Chart */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-semibold text-gray-900">Live Metrics</h4>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="response_time">Response Time</option>
              <option value="accuracy">Accuracy</option>
              <option value="throughput">Throughput</option>
              <option value="error_rate">Error Rate</option>
              <option value="active_connections">Active Connections</option>
            </select>
          </div>

          {realtimeData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={realtimeData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="timestamp"
                    tickFormatter={(value) =>
                      new Date(value).toLocaleTimeString()
                    }
                  />
                  <YAxis />
                  <Tooltip
                    labelFormatter={(value) =>
                      new Date(value).toLocaleTimeString()
                    }
                    formatter={(value) => [
                      formatMetricValue(Number(value), selectedMetric),
                      selectedMetric.replace("_", " "),
                    ]}
                  />
                  <Line
                    type="monotone"
                    dataKey={selectedMetric}
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Clock className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">Waiting for real-time data...</p>
            </div>
          )}
        </div>

        {/* Active Alerts */}
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="w-4 h-4 mr-2" />
            Active Alerts ({alerts.length})
          </h4>

          {alerts.length > 0 ? (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3 rounded-lg border ${getAlertColor(
                    alert.type
                  )}`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-medium text-sm">
                        {alert.metric.replace("_", " ").toUpperCase()}
                      </div>
                      <div className="text-sm mt-1">{alert.message}</div>
                      <div className="text-xs mt-2">
                        Current: {formatMetricValue(alert.value, alert.metric)}{" "}
                        | Threshold:{" "}
                        {formatMetricValue(alert.threshold, alert.metric)}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-400" />
              <p className="text-sm">No active alerts</p>
              <p className="text-xs">System is performing normally</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
