"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  Plus,
  Edit,
  Trash2,
  TestTube,
  Mail,
  MessageSquare,
  Webhook,
  AlertTriangle,
  TrendingUp,
  Calendar,
} from "lucide-react";
import { api } from "@/lib/api";

interface NotificationRule {
  id: number;
  competitor_name: string;
  condition_type: string;
  threshold_value: number | null;
  channel: string;
  target: string;
  active: boolean;
  last_triggered_at: string | null;
  created_at: string;
}

interface NotificationLog {
  id: number;
  competitor_name: string;
  message: string;
  channel: string;
  target: string;
  created_at: string;
}

export function NotificationRulesManager() {
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingRule, setEditingRule] = useState<NotificationRule | null>(null);
  const [newRule, setNewRule] = useState({
    competitor_name: "",
    condition_type: "risk_threshold",
    threshold_value: 80,
    channel: "email",
    target: "",
    active: true,
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Fetch notification rules
  const {
    data: rules,
    isLoading: rulesLoading,
    error: rulesError,
  } = useQuery({
    queryKey: ["notificationRules"],
    queryFn: () =>
      api.get("/api/v1/notifications/rules").then((res) => res.data.items),
  });

  // Fetch notification logs
  const { data: logs, isLoading: logsLoading } = useQuery({
    queryKey: ["notificationLogs"],
    queryFn: () =>
      api.get("/api/v1/notifications/logs").then((res) => res.data.items),
  });

  // Create rule mutation
  const createMutation = useMutation({
    mutationFn: (data: any) => api.post("/api/v1/notifications/rules", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notificationRules"] });
      setShowAddForm(false);
      setNewRule({
        competitor_name: "",
        condition_type: "risk_threshold",
        threshold_value: 80,
        channel: "email",
        target: "",
        active: true,
      });
      setFormError(null);
      setActionError(null);
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail || "Failed to create notification rule";
      setFormError(message);
    },
  });

  // Update rule mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      api.put(`/api/v1/notifications/rules/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notificationRules"] });
      setEditingRule(null);
      setFormError(null);
      setActionError(null);
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail || "Failed to update notification rule";
      setActionError(message);
    },
  });

  // Delete rule mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/notifications/rules/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notificationRules"] });
      setActionError(null);
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail || "Failed to delete notification rule";
      setActionError(message);
    },
  });

  // Test rule mutation
  const testMutation = useMutation({
    mutationFn: (id: number) =>
      api.post(`/api/v1/notifications/rules/${id}/test`),
    onSuccess: (data) => {
      alert(data.data.message);
      queryClient.invalidateQueries({ queryKey: ["notificationLogs"] });
    },
    onError: (error: any) => {
      const message =
        error.response?.data?.detail || "Failed to send test alert";
      setActionError(message);
    },
  });

  const validateRule = (rule: typeof newRule): string | null => {
    if (!rule.competitor_name.trim()) {
      return "Competitor name is required";
    }

    if (!rule.target.trim()) {
      return "Target is required";
    }

    // Email validation
    if (rule.channel === "email") {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(rule.target)) {
        return "Please enter a valid email address";
      }
    }

    // Channel-specific validation
    if (rule.channel === "slack" && !rule.target.startsWith("#")) {
      return "Slack channel must start with #";
    }

    if (rule.channel === "webhook") {
      try {
        new URL(rule.target);
      } catch {
        return "Please enter a valid webhook URL";
      }
    }

    // Threshold validation
    if (["risk_threshold", "trend_change"].includes(rule.condition_type)) {
      if (rule.threshold_value == null || rule.threshold_value === undefined) {
        return "Threshold value is required";
      }
      if (!Number.isFinite(Number(rule.threshold_value))) {
        return "Threshold value must be a valid number";
      }
      if (rule.threshold_value < 0 || rule.threshold_value > 100) {
        return "Threshold value must be between 0 and 100";
      }
    }

    return null;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const validationError = validateRule(newRule);
    if (validationError) {
      setFormError(validationError);
      return;
    }

    setFormError(null);
    createMutation.mutate(newRule);
  };

  const handleEdit = (rule: NotificationRule) => {
    setEditingRule(rule);
    setNewRule({
      competitor_name: rule.competitor_name,
      condition_type: rule.condition_type,
      threshold_value: rule.threshold_value || 80,
      channel: rule.channel,
      target: rule.target,
      active: rule.active,
    });
  };

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingRule) return;

    const validationError = validateRule(newRule);
    if (validationError) {
      setFormError(validationError);
      return;
    }

    setFormError(null);
    updateMutation.mutate({
      id: editingRule.id,
      data: newRule,
    });
  };

  const getConditionIcon = (type: string) => {
    switch (type) {
      case "risk_threshold":
        return <AlertTriangle className="w-4 h-4" />;
      case "trend_change":
        return <TrendingUp className="w-4 h-4" />;
      case "daily_digest":
        return <Calendar className="w-4 h-4" />;
      default:
        return <Bell className="w-4 h-4" />;
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case "email":
        return <Mail className="w-4 h-4" />;
      case "slack":
        return <MessageSquare className="w-4 h-4" />;
      case "webhook":
        return <Webhook className="w-4 h-4" />;
      default:
        return <Bell className="w-4 h-4" />;
    }
  };

  const formatConditionType = (type: string) => {
    switch (type) {
      case "risk_threshold":
        return "Risk Threshold";
      case "trend_change":
        return "Trend Change";
      case "daily_digest":
        return "Daily Digest";
      default:
        return type;
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-2">
          <Bell className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Notification Rules
          </h3>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Rule</span>
        </button>
      </div>

      {actionError && (
        <div className="mb-4 p-3 border border-red-200 bg-red-50 text-sm text-red-700 rounded-lg">
          {actionError}
        </div>
      )}

      {/* Add/Edit Form */}
      {(showAddForm || editingRule) && (
        <form
          onSubmit={editingRule ? handleUpdate : handleSubmit}
          className="mb-6 p-4 bg-gray-50 rounded-lg"
        >
          <h4 className="font-medium text-gray-900 mb-4">
            {editingRule ? "Edit Notification Rule" : "Add Notification Rule"}
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Competitor Name *
              </label>
              <input
                type="text"
                value={newRule.competitor_name}
                onChange={(e) =>
                  setNewRule({ ...newRule, competitor_name: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., OpenAI, Anthropic"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Condition Type *
              </label>
              <select
                value={newRule.condition_type}
                onChange={(e) =>
                  setNewRule({ ...newRule, condition_type: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="risk_threshold">Risk Threshold</option>
                <option value="trend_change">Trend Change</option>
                <option value="daily_digest">Daily Digest</option>
              </select>
            </div>

            {newRule.condition_type !== "daily_digest" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Threshold Value
                </label>
                <input
                  type="number"
                  value={newRule.threshold_value}
                  onChange={(e) => {
                    const value = e.target.value;
                    let threshold_value: number | undefined;

                    if (value === "") {
                      threshold_value = undefined;
                    } else {
                      const parsed = parseFloat(value);
                      threshold_value = Number.isNaN(parsed)
                        ? undefined
                        : parsed;
                    }

                    setNewRule({
                      ...newRule,
                      threshold_value: threshold_value || 0,
                    });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  max="100"
                  placeholder="80"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {newRule.condition_type === "risk_threshold"
                    ? "Alert when risk score exceeds this value"
                    : "Alert when risk score changes by this amount"}
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Channel *
              </label>
              <select
                value={newRule.channel}
                onChange={(e) =>
                  setNewRule({ ...newRule, channel: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="email">Email</option>
                <option value="slack" disabled title="Coming soon">
                  Slack (Coming Soon)
                </option>
                <option value="webhook" disabled title="Coming soon">
                  Webhook (Coming Soon)
                </option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target *
              </label>
              <input
                type="text"
                value={newRule.target}
                onChange={(e) =>
                  setNewRule({ ...newRule, target: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={
                  newRule.channel === "email"
                    ? "user@example.com"
                    : newRule.channel === "slack"
                    ? "#channel"
                    : "https://webhook.url"
                }
                required
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="active"
                checked={newRule.active}
                onChange={(e) =>
                  setNewRule({ ...newRule, active: e.target.checked })
                }
                className="mr-2"
              />
              <label htmlFor="active" className="text-sm text-gray-700">
                Active
              </label>
            </div>
          </div>

          {formError && (
            <div className="mt-4 text-sm text-red-600" role="alert">
              {formError}
            </div>
          )}

          <div className="flex space-x-3 mt-4">
            <button
              type="submit"
              disabled={createMutation.isPending || updateMutation.isPending}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {createMutation.isPending || updateMutation.isPending
                ? "Saving..."
                : editingRule
                ? "Update Rule"
                : "Create Rule"}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowAddForm(false);
                setEditingRule(null);
                setFormError(null);
              }}
              className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Rules List */}
      <div className="space-y-4 mb-8">
        <h4 className="font-medium text-gray-900">Active Rules</h4>

        {rulesLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse p-4 border rounded-lg">
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        ) : rules?.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Bell className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p>No notification rules configured yet.</p>
            <p className="text-sm">
              Add your first rule to get automated alerts!
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {rules?.map((rule: NotificationRule) => (
              <div
                key={rule.id}
                className={`p-4 border rounded-lg ${
                  rule.active
                    ? "border-green-200 bg-green-50"
                    : "border-gray-200 bg-gray-50"
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="font-medium text-gray-900">
                        {rule.competitor_name}
                      </h4>
                      <div className="flex items-center space-x-1 text-sm text-gray-600">
                        {getConditionIcon(rule.condition_type)}
                        <span>{formatConditionType(rule.condition_type)}</span>
                        {rule.threshold_value && (
                          <span>({rule.threshold_value})</span>
                        )}
                      </div>
                      <div className="flex items-center space-x-1 text-sm text-gray-600">
                        {getChannelIcon(rule.channel)}
                        <span>{rule.channel}</span>
                      </div>
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          rule.active
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {rule.active ? "Active" : "Inactive"}
                      </span>
                    </div>

                    <div className="text-sm text-gray-600">
                      <span>Target: {rule.target}</span>
                      {rule.last_triggered_at && (
                        <span className="ml-4">
                          Last triggered:{" "}
                          {new Date(rule.last_triggered_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => testMutation.mutate(rule.id)}
                      disabled={testMutation.isPending}
                      className="p-2 text-blue-600 hover:bg-blue-100 rounded-md transition-colors"
                      title="Send Test Alert"
                    >
                      <TestTube className="w-4 h-4" />
                    </button>

                    <button
                      onClick={() => handleEdit(rule)}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
                      title="Edit Rule"
                    >
                      <Edit className="w-4 h-4" />
                    </button>

                    <button
                      onClick={() => {
                        if (
                          window.confirm(
                            `Are you sure you want to delete the notification rule for "${rule.competitor_name}"? This action cannot be undone.`
                          )
                        ) {
                          deleteMutation.mutate(rule.id);
                        }
                      }}
                      className="p-2 text-red-600 hover:bg-red-100 rounded-md transition-colors"
                      title="Delete Rule"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Alerts */}
      <div>
        <h4 className="font-medium text-gray-900 mb-4">Recent Alerts</h4>

        {logsLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse p-3 border rounded-lg">
                <div className="h-3 bg-gray-200 rounded w-1/4 mb-1"></div>
                <div className="h-3 bg-gray-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        ) : logs?.length === 0 ? (
          <div className="text-center py-6 text-gray-500">
            <p className="text-sm">No alerts have been sent yet.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {logs?.slice(0, 5).map((log: NotificationLog) => (
              <div
                key={log.id}
                className="p-3 border border-gray-200 rounded-lg"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-medium text-gray-900">
                        {log.competitor_name}
                      </span>
                      <div className="flex items-center space-x-1 text-sm text-gray-600">
                        {getChannelIcon(log.channel)}
                        <span>{log.channel}</span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mb-1">{log.message}</p>
                    <div className="text-xs text-gray-500">
                      Sent to: {log.target}
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    {new Date(log.created_at).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
