"use client";

import React, { useState, useEffect } from "react";
import { useTribeInterface } from "./TribeInterfaceProvider";
import { tribePersistence } from "@/lib/tribe-persistence";
import {
  Settings,
  Save,
  RotateCcw,
  Download,
  Upload,
  Trash2,
  BarChart3,
  Clock,
  Star,
  TrendingUp,
  User,
  Bell,
  Shield,
} from "lucide-react";
import { TribePreferences, InterfaceMode } from "@/lib/types/tribe-interface";

interface ModePreferencesProps {
  onClose?: () => void;
}

interface PreferencesSectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

export function ModePreferences({ onClose }: ModePreferencesProps) {
  const { user, currentMode, switchMode, state } = useTribeInterface();
  const [preferences, setPreferences] = useState<TribePreferences>({
    defaultMode: "analyst",
    maxInsights: 5,
    showTechnicalDetails: true,
    enableCollaboration: true,
    summaryLevel: "medium",
    thresholds: {
      riskScore: 70,
      confidenceScore: 80,
      sourceCount: 10,
    },
    notifications: {
      email: true,
      inApp: true,
      slack: false,
      frequency: "immediate",
    },
  });

  const [analytics, setAnalytics] = useState<any>(null);
  const [satisfactionScores, setSatisfactionScores] = useState<any[]>([]);
  const [hasChanges, setHasChanges] = useState(false);
  const [saveStatus, setSaveStatus] = useState<
    "idle" | "saving" | "saved" | "error"
  >("idle");

  // Load preferences on mount
  useEffect(() => {
    const loadedPreferences = tribePersistence().loadUserPreferences();
    if (loadedPreferences) {
      setPreferences(loadedPreferences);
    } else if (user?.preferences) {
      setPreferences(user.preferences);
    }

    // Load analytics
    const usageAnalytics = tribePersistence().getUsageAnalytics();
    setAnalytics(usageAnalytics);

    // Load satisfaction scores
    const scores = tribePersistence().loadSatisfactionScores();
    setSatisfactionScores(scores);
  }, [user]);

  const handlePreferenceChange = (key: string, value: any) => {
    setPreferences((prev) => {
      const updated = { ...prev };

      // Handle nested keys
      if (key.includes(".")) {
        const [parent, child] = key.split(".");
        (updated as any)[parent] = {
          ...((updated as any)[parent] || {}),
          [child]: value,
        };
      } else {
        (updated as any)[key] = value;
      }

      return updated;
    });
    setHasChanges(true);
  };

  const handleSave = async () => {
    setSaveStatus("saving");

    try {
      // Save to localStorage
      tribePersistence().saveUserPreferences(preferences);

      // Switch to default mode if different
      if (preferences.defaultMode !== currentMode) {
        switchMode(preferences.defaultMode);
      }

      setSaveStatus("saved");
      setHasChanges(false);

      setTimeout(() => setSaveStatus("idle"), 2000);
    } catch (error) {
      console.error("Failed to save preferences:", error);
      setSaveStatus("error");
      setTimeout(() => setSaveStatus("idle"), 3000);
    }
  };

  const handleReset = () => {
    const defaultPreferences: TribePreferences = {
      defaultMode: "analyst",
      maxInsights: 5,
      showTechnicalDetails: true,
      enableCollaboration: true,
      summaryLevel: "medium",
      thresholds: {
        riskScore: 70,
        confidenceScore: 80,
        sourceCount: 10,
      },
      notifications: {
        email: true,
        inApp: true,
        slack: false,
        frequency: "immediate",
      },
    };

    setPreferences(defaultPreferences);
    setHasChanges(true);
  };

  const handleExport = () => {
    const data = tribePersistence().exportData();
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tribe-preferences-${
      new Date().toISOString().split("T")[0]
    }.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target?.result as string);
        const success = tribePersistence().importData(data);

        if (success) {
          // Reload preferences
          const loadedPreferences = tribePersistence().loadUserPreferences();
          if (loadedPreferences) {
            setPreferences(loadedPreferences);
            setHasChanges(false);
          }
        } else {
          alert("Failed to import preferences. Please check the file format.");
        }
      } catch (error) {
        alert("Invalid file format. Please select a valid preferences file.");
      }
    };
    reader.readAsText(file);
  };

  const handleClearData = () => {
    if (
      confirm(
        "Are you sure you want to clear all stored preferences and data? This cannot be undone."
      )
    ) {
      tribePersistence().clearAllData();
      handleReset();
    }
  };

  const getSaveButtonText = () => {
    switch (saveStatus) {
      case "saving":
        return "Saving...";
      case "saved":
        return "Saved!";
      case "error":
        return "Error";
      default:
        return "Save Preferences";
    }
  };

  const getSaveButtonColor = () => {
    switch (saveStatus) {
      case "saved":
        return "bg-green-600 hover:bg-green-700";
      case "error":
        return "bg-red-600 hover:bg-red-700";
      default:
        return "bg-blue-600 hover:bg-blue-700";
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Settings className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">
            Interface Preferences
          </h2>
        </div>

        <div className="flex items-center gap-2">
          {hasChanges && (
            <span className="text-sm text-orange-600 bg-orange-50 px-2 py-1 rounded">
              Unsaved changes
            </span>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Preferences */}
        <div className="lg:col-span-2 space-y-6">
          {/* Interface Mode Preferences */}
          <PreferencesSection
            title="Interface Mode"
            icon={<User className="w-5 h-5 text-blue-600" />}
          >
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Default Mode
                </label>
                <select
                  value={preferences.defaultMode}
                  onChange={(e) =>
                    handlePreferenceChange(
                      "defaultMode",
                      e.target.value as InterfaceMode
                    )
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="executive">
                    Executive - Simplified insights and actions
                  </option>
                  <option value="analyst">
                    Analyst - Full technical depth
                  </option>
                  <option value="team">
                    Team - Collaborative features enabled
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Maximum Insights per View
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={preferences.maxInsights}
                  onChange={(e) =>
                    handlePreferenceChange(
                      "maxInsights",
                      parseInt(e.target.value)
                    )
                  }
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>1</span>
                  <span className="font-medium">{preferences.maxInsights}</span>
                  <span>10</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Summary Level
                </label>
                <div className="flex gap-2">
                  {["high", "medium", "detailed"].map((level) => (
                    <button
                      key={level}
                      onClick={() =>
                        handlePreferenceChange("summaryLevel", level)
                      }
                      className={`px-3 py-2 text-sm rounded-md transition-colors ${
                        preferences.summaryLevel === level
                          ? "bg-blue-600 text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Show Technical Details
                </span>
                <button
                  onClick={() =>
                    handlePreferenceChange(
                      "showTechnicalDetails",
                      !preferences.showTechnicalDetails
                    )
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    preferences.showTechnicalDetails
                      ? "bg-blue-600"
                      : "bg-gray-200"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      preferences.showTechnicalDetails
                        ? "translate-x-6"
                        : "translate-x-1"
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Enable Collaboration
                </span>
                <button
                  onClick={() =>
                    handlePreferenceChange(
                      "enableCollaboration",
                      !preferences.enableCollaboration
                    )
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    preferences.enableCollaboration
                      ? "bg-blue-600"
                      : "bg-gray-200"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      preferences.enableCollaboration
                        ? "translate-x-6"
                        : "translate-x-1"
                    }`}
                  />
                </button>
              </div>
            </div>
          </PreferencesSection>

          {/* Alert Thresholds */}
          <PreferencesSection
            title="Alert Thresholds"
            icon={<Bell className="w-5 h-5 text-orange-600" />}
          >
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Risk Score Threshold ({preferences.thresholds.riskScore}/100)
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={preferences.thresholds.riskScore}
                  onChange={(e) =>
                    handlePreferenceChange(
                      "thresholds.riskScore",
                      parseInt(e.target.value)
                    )
                  }
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Only show alerts above this risk score
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Confidence Score Threshold (
                  {preferences.thresholds.confidenceScore}%)
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={preferences.thresholds.confidenceScore}
                  onChange={(e) =>
                    handlePreferenceChange(
                      "thresholds.confidenceScore",
                      parseInt(e.target.value)
                    )
                  }
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Minimum AI confidence level for alerts
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Minimum Source Count ({preferences.thresholds.sourceCount})
                </label>
                <input
                  type="range"
                  min="1"
                  max="50"
                  value={preferences.thresholds.sourceCount}
                  onChange={(e) =>
                    handlePreferenceChange(
                      "thresholds.sourceCount",
                      parseInt(e.target.value)
                    )
                  }
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Minimum number of sources required for alerts
                </p>
              </div>
            </div>
          </PreferencesSection>

          {/* Notification Preferences */}
          <PreferencesSection
            title="Notifications"
            icon={<Bell className="w-5 h-5 text-green-600" />}
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Email Notifications
                </span>
                <button
                  onClick={() =>
                    handlePreferenceChange(
                      "notifications.email",
                      !preferences.notifications.email
                    )
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    preferences.notifications.email
                      ? "bg-blue-600"
                      : "bg-gray-200"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      preferences.notifications.email
                        ? "translate-x-6"
                        : "translate-x-1"
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  In-App Notifications
                </span>
                <button
                  onClick={() =>
                    handlePreferenceChange(
                      "notifications.inApp",
                      !preferences.notifications.inApp
                    )
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    preferences.notifications.inApp
                      ? "bg-blue-600"
                      : "bg-gray-200"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      preferences.notifications.inApp
                        ? "translate-x-6"
                        : "translate-x-1"
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Slack Notifications
                </span>
                <button
                  onClick={() =>
                    handlePreferenceChange(
                      "notifications.slack",
                      !preferences.notifications.slack
                    )
                  }
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    preferences.notifications.slack
                      ? "bg-blue-600"
                      : "bg-gray-200"
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      preferences.notifications.slack
                        ? "translate-x-6"
                        : "translate-x-1"
                    }`}
                  />
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notification Frequency
                </label>
                <select
                  value={preferences.notifications.frequency}
                  onChange={(e) =>
                    handlePreferenceChange(
                      "notifications.frequency",
                      e.target.value
                    )
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="immediate">Immediate</option>
                  <option value="hourly">Hourly Digest</option>
                  <option value="daily">Daily Summary</option>
                </select>
              </div>
            </div>
          </PreferencesSection>
        </div>

        {/* Analytics and Actions */}
        <div className="space-y-6">
          {/* Usage Analytics */}
          {analytics && (
            <PreferencesSection
              title="Usage Analytics"
              icon={<BarChart3 className="w-5 h-5 text-purple-600" />}
            >
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Total Sessions</span>
                  <span className="font-medium">{analytics.totalSessions}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Mode Switches</span>
                  <span className="font-medium">{analytics.modeSwitches}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Most Used Mode</span>
                  <span className="font-medium capitalize">
                    {analytics.mostUsedMode || "N/A"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">
                    Avg. Satisfaction
                  </span>
                  <div className="flex items-center gap-1">
                    <Star className="w-3 h-3 text-yellow-500" />
                    <span className="font-medium">
                      {analytics.averageSatisfaction.toFixed(1)}/5
                    </span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Avg. Session</span>
                  <span className="font-medium">
                    {Math.round(analytics.sessionDuration / 1000 / 60)}m
                  </span>
                </div>
              </div>
            </PreferencesSection>
          )}

          {/* Actions */}
          <PreferencesSection
            title="Actions"
            icon={<Shield className="w-5 h-5 text-gray-600" />}
          >
            <div className="space-y-3">
              <button
                onClick={handleSave}
                disabled={!hasChanges || saveStatus === "saving"}
                className={`w-full flex items-center justify-center gap-2 px-4 py-2 text-white rounded-md transition-colors disabled:opacity-50 ${getSaveButtonColor()}`}
              >
                <Save className="w-4 h-4" />
                {getSaveButtonText()}
              </button>

              <button
                onClick={handleReset}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                Reset to Defaults
              </button>

              <div className="flex gap-2">
                <button
                  onClick={handleExport}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors text-sm"
                >
                  <Download className="w-3 h-3" />
                  Export
                </button>

                <label className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors text-sm cursor-pointer">
                  <Upload className="w-3 h-3" />
                  Import
                  <input
                    type="file"
                    accept=".json"
                    onChange={handleImport}
                    className="hidden"
                  />
                </label>
              </div>

              <button
                onClick={handleClearData}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors text-sm"
              >
                <Trash2 className="w-4 h-4" />
                Clear All Data
              </button>
            </div>
          </PreferencesSection>

          {/* Current State */}
          <PreferencesSection
            title="Current State"
            icon={<Clock className="w-5 h-5 text-blue-600" />}
          >
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Current Mode</span>
                <span className="font-medium capitalize">{currentMode}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Content Filtered</span>
                <span className="font-medium">
                  {state.adaptationMetrics.contentFiltered}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Complexity Reduced</span>
                <span className="font-medium">
                  {state.adaptationMetrics.complexityReduced}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">User Satisfaction</span>
                <span className="font-medium">
                  {state.adaptationMetrics.userSatisfaction.toFixed(1)}/5
                </span>
              </div>
            </div>
          </PreferencesSection>
        </div>
      </div>
    </div>
  );
}

function PreferencesSection({
  title,
  icon,
  children,
}: PreferencesSectionProps) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-4">
        {icon}
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      {children}
    </div>
  );
}
