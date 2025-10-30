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
  BarChart,
  Bar,
} from "recharts";
import {
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  Zap,
  RefreshCw,
  Settings,
  ExternalLink,
} from "lucide-react";
import { api } from "@/lib/api";
import { getSocket } from "@/lib/socket";

interface IntegrationHealth {
  integration_type: "hubspot" | "obsidian";
  status: "healthy" | "degraded" | "down";
  last_sync: string;
  sync_success_rate: number;
  avg_response_time: number;
  error_count: number;
  uptime_percentage: number;
  last_error?: string;
  next_sync?: string;
}

interface HealthMetric {
  timestamp: string;
  hubspot_status: number; // 1 = healthy, 0.5 = degraded, 0 = down
  obsidian_status: number;
  hubspot_response_time: number;
  obsidian_response_time: number;
  total_errors: number;
}

interface IntegrationAlert {
  id: string;
  integration_type: string;
  alert_type: "sync_failure" | "high_latency" | "auth_error" | "quota_exceeded";
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  timestamp: string;
  resolved: boolean;
}

export function IntegrationHealthMonitor() {
  const [selectedTimeRange, setSelectedTimeRange] = useState<
    "1h" | "24h" | "7d"
  >("24h");
  const [realtimeAlerts, setRealtimeAlerts] = useState<IntegrationAlert[]>([]);

  const {
    data: healthData,
    isLoading: healthLoading,
    refetch: refetchHealth,
  } = useQuery({
    queryKey: ["integrationHealth"],
    queryFn: () =>
      api.get("/api/v1/integrations/health").then((res) => res.data),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // 1 minute
  });

  const { data: healthMetrics, isLoading: metricsLoading } = useQuery({
    queryKey: ["integrationHealthMetrics", selectedTimeRange],
    queryFn: () =>
      api
        .get("/api/v1/integrations/health/metrics", {
          params: { time_range: selectedTimeRange },
        })
        .then((res) => res.data.metrics),
    staleTime: 60000,
  });

  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ["integrationAlerts"],
    queryFn: () =>
      api.get("/api/v1/integrations/alerts").then((res) => res.data.alerts),
    staleTime: 30000,
  });

  // Real-time alert updates
  useEffect(() => {
    const socket = getSocket();
    socket.emit("join_room", { room: "integration_health" });

    const handleHealthUpdate = (data: IntegrationHealth) => {
      refetchHealth();
    };

    const handleAlert = (alert: IntegrationAlert) => {
      setRealtimeAlerts((prev) => [alert, ...prev.slice(0, 4)]); // Keep 5 total alerts (1 new + 4 previous)
    };

    socket.on("integration_health_update", handleHealthUpdate);
    socket.on("integration_alert", handleAlert);

    return () => {
      socket.off("integration_health_update", handleHealthUpdate);
      socket.off("integration_alert", handleAlert);
    };
  }, [refetchHealth]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "text-green-600 bg-green-100";
      case "degraded":
        return "text-yellow-600 bg-yellow-100";
      case "down":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "degraded":
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      case "down":
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Activity className="w-5 h-5 text-gray-600" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "text-red-600 bg-red-100 border-red-200";
      case "high":
        return "text-orange-600 bg-orange-100 border-orange-200";
      case "medium":
        return "text-yellow-600 bg-yellow-100 border-yellow-200";
      case "low":
        return "text-blue-600 bg-blue-100 border-blue-200";
      default:
        return "text-gray-600 bg-gray-100 border-gray-200";
    }
  };

  const getIntegrationIcon = (type: string) => {
    switch (type) {
      case "hubspot":
        return (
          <div className="w-6 h-6 bg-orange-500 rounded flex items-center justify-center">
            <span className="text-white font-bold text-xs">H</span>
          </div>
        );
      case "obsidian":
        return (
          <div className="w-6 h-6 bg-purple-600 rounded flex items-center justify-center text-white text-xs">
            O
          </div>
        );
      default:
        return <Settings className="w-6 h-6 text-gray-600" />;
    }
  };

  if (healthLoading || metricsLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const health = healthData?.integrations || [];
  const metrics = healthMetrics || [];
  const alertsList = alerts || [];

  // Calculate overall health
  const overallHealth =
    health.length > 0
      ? health.every((h: IntegrationHealth) => h.status === "healthy")
        ? "healthy"
        : health.some((h: IntegrationHealth) => h.status === "down")
        ? "down"
        : "degraded"
      : "unknown";

  const activeAlerts = alertsList.filter(
    (alert: IntegrationAlert) => !alert.resolved
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-blue-600" />
            Integration Health Monitor
          </h3>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              {getStatusIcon(overallHealth)}
              <span
                className={`px-3 py-1 text-sm rounded-full ${getStatusColor(
                  overallHealth
                )}`}
              >
                {overallHealth.toUpperCase()}
              </span>
            </div>
            <button
              onClick={() => refetchHealth()}
              className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Real-time Alerts Banner */}
        {realtimeAlerts.length > 0 && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-red-900">
                New Integration Alerts
              </h4>
              <button
                onClick={() => setRealtimeAlerts([])}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Clear
              </button>
            </div>
            <div className="space-y-1">
              {realtimeAlerts.map((alert) => (
                <div key={alert.id} className="text-sm text-red-800">
                  <strong>{alert.integration_type.toUpperCase()}:</strong>{" "}
                  {alert.message}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Integration Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {health.map((integration: IntegrationHealth) => (
            <div
              key={integration.integration_type}
              className="p-6 border border-gray-200 rounded-lg"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {getIntegrationIcon(integration.integration_type)}
                  <div>
                    <h4 className="font-semibold text-gray-900 capitalize">
                      {integration.integration_type}
                    </h4>
                    <div className="text-sm text-gray-600">
                      Last sync:{" "}
                      {integration.last_sync
                        ? new Date(integration.last_sync).toLocaleString()
                        : "Never"}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(integration.status)}
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${getStatusColor(
                      integration.status
                    )}`}
                  >
                    {integration.status.toUpperCase()}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-lg font-bold text-blue-600">
                    {Math.round(integration.sync_success_rate * 100)}%
                  </div>
                  <div className="text-xs text-gray-600">Success Rate</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-lg font-bold text-green-600">
                    {integration.avg_response_time.toFixed(0)}ms
                  </div>
                  <div className="text-xs text-gray-600">Avg Response</div>
                </div>
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <div className="text-lg font-bold text-purple-600">
                    {Math.round(integration.uptime_percentage)}%
                  </div>
                  <div className="text-xs text-gray-600">Uptime</div>
                </div>
                <div className="text-center p-3 bg-orange-50 rounded-lg">
                  <div className="text-lg font-bold text-orange-600">
                    {integration.error_count}
                  </div>
                  <div className="text-xs text-gray-600">Errors (24h)</div>
                </div>
              </div>

              {integration.last_error && (
                <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                  <div className="text-sm font-medium text-red-900 mb-1">
                    Last Error:
                  </div>
                  <div className="text-sm text-red-700">
                    {integration.last_error}
                  </div>
                </div>
              )}

              {integration.next_sync && (
                <div className="mt-3 flex items-center text-sm text-gray-600">
                  <Clock className="w-4 h-4 mr-1" />
                  <span>
                    Next sync:{" "}
                    {new Date(integration.next_sync).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>

        {health.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <Settings className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg mb-2">No integrations configured</p>
            <p className="text-sm">
              Set up HubSpot or Obsidian integrations to monitor their health.
            </p>
          </div>
        )}
      </div>

      {/* Health Metrics Chart */}
      {metrics.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h4 className="font-semibold text-gray-900">Health Metrics</h4>
            <select
              value={selectedTimeRange}
              onChange={(e) =>
                setSelectedTimeRange(e.target.value as "1h" | "24h" | "7d")
              }
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
            </select>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Status Timeline */}
            <div>
              <h5 className="font-medium text-gray-900 mb-3">
                Integration Status
              </h5>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={metrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleTimeString()
                      }
                    />
                    <YAxis domain={[0, 1]} />
                    <Tooltip
                      labelFormatter={(value) =>
                        new Date(value).toLocaleString()
                      }
                      formatter={(value, name) => [
                        Number(value) === 1
                          ? "Healthy"
                          : Number(value) === 0.5
                          ? "Degraded"
                          : "Down",
                        name === "hubspot_status" ? "HubSpot" : "Obsidian",
                      ]}
                    />
                    <Line
                      type="stepAfter"
                      dataKey="hubspot_status"
                      stroke="#f97316"
                      strokeWidth={2}
                      name="HubSpot"
                      dot={{ fill: "#f97316", strokeWidth: 2, r: 3 }}
                    />
                    <Line
                      type="stepAfter"
                      dataKey="obsidian_status"
                      stroke="#8b5cf6"
                      strokeWidth={2}
                      name="Obsidian"
                      dot={{ fill: "#8b5cf6", strokeWidth: 2, r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Response Time */}
            <div>
              <h5 className="font-medium text-gray-900 mb-3">Response Time</h5>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={metrics}>
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
                        new Date(value).toLocaleString()
                      }
                      formatter={(value, name) => [
                        `${value}ms`,
                        name === "hubspot_response_time"
                          ? "HubSpot"
                          : "Obsidian",
                      ]}
                    />
                    <Bar
                      dataKey="hubspot_response_time"
                      fill="#f97316"
                      name="HubSpot"
                    />
                    <Bar
                      dataKey="obsidian_response_time"
                      fill="#8b5cf6"
                      name="Obsidian"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Active Alerts */}
      {activeAlerts.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="w-4 h-4 mr-2 text-red-600" />
            Active Alerts ({activeAlerts.length})
          </h4>
          <div className="space-y-3">
            {activeAlerts.map((alert: IntegrationAlert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border ${getSeverityColor(
                  alert.severity
                )}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    {getIntegrationIcon(alert.integration_type)}
                    <div>
                      <div className="font-medium text-sm capitalize">
                        {alert.integration_type} -{" "}
                        {alert.alert_type.replace("_", " ")}
                      </div>
                      <div className="text-sm mt-1">{alert.message}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span
                      className={`px-2 py-1 text-xs rounded-full font-medium ${getSeverityColor(
                        alert.severity
                      )}`}
                    >
                      {alert.severity.toUpperCase()}
                    </span>
                    <div className="text-xs text-gray-500 mt-1">
                      {new Date(alert.timestamp).toLocaleString()}
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
