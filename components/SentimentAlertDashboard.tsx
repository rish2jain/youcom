"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  BellOff,
  AlertTriangle,
  CheckCircle,
  Clock,
  Settings,
  Filter,
  Trash2,
  Eye,
  EyeOff,
} from "lucide-react";
import { api } from "@/lib/api";
import { getSocket } from "@/lib/socket";

interface SentimentAlert {
  id: string;
  entity_name: string;
  entity_type: "company" | "product" | "market";
  alert_type: "sentiment_shift" | "volume_spike" | "negative_trend";
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  current_value: number;
  previous_value: number;
  threshold: number;
  change_percent: number;
  triggered_at: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  source_mentions: Array<{
    content: string;
    source: string;
    sentiment: number;
    timestamp: string;
  }>;
}

interface AlertRule {
  id: string;
  entity_name?: string;
  entity_type?: "company" | "product" | "market";
  alert_type: "sentiment_shift" | "volume_spike" | "negative_trend";
  threshold: number;
  enabled: boolean;
  notification_channels: string[];
  created_at: string;
}

export function SentimentAlertDashboard() {
  const [selectedSeverity, setSelectedSeverity] = useState<string>("all");
  const [selectedType, setSelectedType] = useState<string>("all");
  const [showAcknowledged, setShowAcknowledged] = useState(false);
  const [showRulesModal, setShowRulesModal] = useState(false);
  const [newAlerts, setNewAlerts] = useState<SentimentAlert[]>([]);

  const queryClient = useQueryClient();

  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: [
      "sentimentAlerts",
      selectedSeverity,
      selectedType,
      showAcknowledged,
    ],
    queryFn: () => {
      const params: any = {};
      if (selectedSeverity !== "all") params.severity = selectedSeverity;
      if (selectedType !== "all") params.alert_type = selectedType;
      if (!showAcknowledged) params.acknowledged = false;

      return api
        .get("/api/v1/sentiment/alerts", { params })
        .then((res) => res.data.alerts);
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // 1 minute
  });

  const { data: alertRules, isLoading: rulesLoading } = useQuery({
    queryKey: ["sentimentAlertRules"],
    queryFn: () =>
      api.get("/api/v1/sentiment/alert-rules").then((res) => res.data.rules),
    staleTime: 300000, // 5 minutes
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (alertId: string) =>
      api.post(`/api/v1/sentiment/alerts/${alertId}/acknowledge`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sentimentAlerts"] });
    },
  });

  const deleteAlertMutation = useMutation({
    mutationFn: (alertId: string) =>
      api.delete(`/api/v1/sentiment/alerts/${alertId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sentimentAlerts"] });
    },
  });

  const toggleRuleMutation = useMutation({
    mutationFn: ({ ruleId, enabled }: { ruleId: string; enabled: boolean }) =>
      api.patch(`/api/v1/sentiment/alert-rules/${ruleId}`, { enabled }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sentimentAlertRules"] });
    },
  });

  // Request notification permission on mount
  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
  }, []);

  // Real-time alert updates
  useEffect(() => {
    const socket = getSocket();
    socket.emit("join_room", { room: "sentiment_alerts" });

    const handleNewAlert = (alert: SentimentAlert) => {
      setNewAlerts((prev) => [alert, ...prev.slice(0, 4)]); // Keep last 5 new alerts

      // Show browser notification for high/critical alerts
      if (
        (alert.severity === "high" || alert.severity === "critical") &&
        "Notification" in window
      ) {
        if (Notification.permission === "granted") {
          new Notification(`Sentiment Alert: ${alert.entity_name}`, {
            body: alert.message,
            icon: "/favicon.ico",
          });
        }
      }

      queryClient.invalidateQueries({ queryKey: ["sentimentAlerts"] });
    };

    socket.on("sentiment_alert", handleNewAlert);

    return () => {
      socket.emit("leave_room", { room: "sentiment_alerts" });
      socket.off("sentiment_alert", handleNewAlert);
    };
  }, [queryClient]);

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

  const getAlertTypeIcon = (type: string) => {
    switch (type) {
      case "sentiment_shift":
        return <AlertTriangle className="w-4 h-4" />;
      case "volume_spike":
        return <Bell className="w-4 h-4" />;
      case "negative_trend":
        return <Clock className="w-4 h-4" />;
      default:
        return <Bell className="w-4 h-4" />;
    }
  };

  const formatAlertType = (type: string) => {
    return type.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const formatSentimentScore = (score: number) => {
    if (score > 0) return `+${(score * 100).toFixed(1)}%`;
    return `${(score * 100).toFixed(1)}%`;
  };

  if (alertsLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const alertsList = alerts || [];
  const rules = alertRules || [];
  const unacknowledgedCount = alertsList.filter(
    (alert: SentimentAlert) => !alert.acknowledged
  ).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Bell className="w-5 h-5 mr-2 text-blue-600" />
            Sentiment Alert Dashboard
            {unacknowledgedCount > 0 && (
              <span className="ml-2 px-2 py-1 bg-red-100 text-red-600 text-xs rounded-full">
                {unacknowledgedCount} new
              </span>
            )}
          </h3>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowRulesModal(true)}
              className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              <Settings className="w-4 h-4" />
              <span>Manage Rules</span>
            </button>
            <div className="text-sm text-gray-600">
              {alertsList.length} total alerts
            </div>
          </div>
        </div>

        {/* New Alerts Banner */}
        {newAlerts.length > 0 && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-blue-900">New Alerts Received</h4>
              <button
                onClick={() => setNewAlerts([])}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                Clear
              </button>
            </div>
            <div className="space-y-2">
              {newAlerts.map((alert) => (
                <div key={alert.id} className="text-sm text-blue-800">
                  <strong>{alert.entity_name}:</strong> {alert.message}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Severity:</span>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Type:</span>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="sentiment_shift">Sentiment Shift</option>
              <option value="volume_spike">Volume Spike</option>
              <option value="negative_trend">Negative Trend</option>
            </select>
          </div>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showAcknowledged}
              onChange={(e) => setShowAcknowledged(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Show Acknowledged</span>
          </label>
        </div>

        {/* Alerts List */}
        {alertsList.length > 0 ? (
          <div className="space-y-4">
            {alertsList.map((alert: SentimentAlert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border ${
                  alert.acknowledged
                    ? "bg-gray-50 border-gray-200"
                    : `${getSeverityColor(alert.severity)}`
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    {getAlertTypeIcon(alert.alert_type)}
                    <div>
                      <div className="font-medium text-gray-900">
                        {alert.entity_name}
                        <span className="ml-2 text-sm text-gray-600 capitalize">
                          ({alert.entity_type})
                        </span>
                      </div>
                      <div className="text-sm text-gray-600">
                        {formatAlertType(alert.alert_type)}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2 py-1 text-xs rounded-full font-medium ${getSeverityColor(
                        alert.severity
                      )}`}
                    >
                      {alert.severity.toUpperCase()}
                    </span>
                    <div className="text-xs text-gray-500">
                      {new Date(alert.triggered_at).toLocaleString()}
                    </div>
                  </div>
                </div>

                <div className="mb-3">
                  <p className="text-sm text-gray-700 mb-2">{alert.message}</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">
                        Current:
                      </span>
                      <span className="ml-1">
                        {alert.alert_type === "volume_spike"
                          ? alert.current_value.toLocaleString()
                          : formatSentimentScore(alert.current_value)}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">
                        Previous:
                      </span>
                      <span className="ml-1">
                        {alert.alert_type === "volume_spike"
                          ? alert.previous_value.toLocaleString()
                          : formatSentimentScore(alert.previous_value)}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Change:</span>
                      <span
                        className={`ml-1 ${
                          alert.change_percent > 0
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {alert.change_percent > 0 ? "+" : ""}
                        {alert.change_percent.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Source Mentions */}
                {alert.source_mentions && alert.source_mentions.length > 0 && (
                  <div className="mb-3">
                    <div className="text-sm font-medium text-gray-700 mb-2">
                      Recent Mentions ({alert.source_mentions.length})
                    </div>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                      {alert.source_mentions
                        .slice(0, 3)
                        .map((mention, index) => (
                          <div
                            key={index}
                            className="text-xs text-gray-600 p-2 bg-white rounded border"
                          >
                            <div className="flex items-start justify-between">
                              <span className="flex-1 mr-2">
                                {mention.content}
                              </span>
                              <span className="font-medium">
                                {formatSentimentScore(mention.sentiment)}
                              </span>
                            </div>
                            <div className="flex items-center justify-between mt-1">
                              <span>{mention.source}</span>
                              <span>
                                {new Date(mention.timestamp).toLocaleString()}
                              </span>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {!alert.acknowledged ? (
                      <button
                        onClick={() => acknowledgeMutation.mutate(alert.id)}
                        disabled={acknowledgeMutation.isPending}
                        className="flex items-center space-x-1 text-sm text-green-600 hover:text-green-800"
                      >
                        <CheckCircle className="w-4 h-4" />
                        <span>Acknowledge</span>
                      </button>
                    ) : (
                      <div className="flex items-center space-x-1 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4" />
                        <span>
                          Acknowledged by {alert.acknowledged_by} at{" "}
                          {alert.acknowledged_at
                            ? new Date(alert.acknowledged_at).toLocaleString()
                            : ""}
                        </span>
                      </div>
                    )}

                    <button
                      onClick={() => deleteAlertMutation.mutate(alert.id)}
                      disabled={deleteAlertMutation.isPending}
                      className="flex items-center space-x-1 text-sm text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span>Delete</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <Bell className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg mb-2">No sentiment alerts</p>
            <p className="text-sm">
              {selectedSeverity !== "all" ||
              selectedType !== "all" ||
              showAcknowledged
                ? "Try adjusting your filters to see more alerts."
                : "Sentiment alerts will appear here when thresholds are exceeded."}
            </p>
          </div>
        )}
      </div>

      {/* Alert Rules Modal */}
      {showRulesModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-96 overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h4 className="text-lg font-semibold text-gray-900">
                Alert Rules
              </h4>
              <button
                onClick={() => setShowRulesModal(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            {rules.length > 0 ? (
              <div className="space-y-4">
                {rules.map((rule: AlertRule) => (
                  <div
                    key={rule.id}
                    className="p-4 border border-gray-200 rounded-lg"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900">
                          {formatAlertType(rule.alert_type)}
                          {rule.entity_name && (
                            <span className="ml-2 text-sm text-gray-600">
                              for {rule.entity_name}
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-600">
                          Threshold: {rule.threshold}
                          {rule.entity_type && (
                            <span className="ml-2 capitalize">
                              ({rule.entity_type})
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          Channels: {rule.notification_channels.join(", ")}
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() =>
                            toggleRuleMutation.mutate({
                              ruleId: rule.id,
                              enabled: !rule.enabled,
                            })
                          }
                          className={`flex items-center space-x-1 text-sm ${
                            rule.enabled ? "text-green-600" : "text-gray-600"
                          }`}
                        >
                          {rule.enabled ? (
                            <Eye className="w-4 h-4" />
                          ) : (
                            <EyeOff className="w-4 h-4" />
                          )}
                          <span>{rule.enabled ? "Enabled" : "Disabled"}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Settings className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No alert rules configured</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
