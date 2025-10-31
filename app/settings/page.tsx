"use client";

import { useState } from "react";
import {
  Eye,
  EyeOff,
  Check,
  X,
  Settings,
  Key,
  Bell,
  Palette,
} from "lucide-react";
import APIToggle from "@/components/APIToggle";
import PersonalPlaybooks from "@/components/PersonalPlaybooks";
import { APIUsageDashboard } from "@/components/APIUsageDashboard";

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<
    "idle" | "success" | "error"
  >("idle");
  const [useLiveData, setUseLiveData] = useState(false);

  // Notification settings
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [slackNotifications, setSlackNotifications] = useState(false);
  const [riskThreshold, setRiskThreshold] = useState(75);

  const handleTestConnection = async () => {
    if (!apiKey.trim()) {
      setConnectionStatus("error");
      return;
    }

    setIsTestingConnection(true);
    setConnectionStatus("idle");

    try {
      // Simulate API test
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Mock success/failure
      if (apiKey.includes("test") || apiKey.length > 10) {
        setConnectionStatus("success");
      } else {
        setConnectionStatus("error");
      }
    } catch (error) {
      setConnectionStatus("error");
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleSaveSettings = () => {
    // Save settings logic here
    alert("Settings saved successfully!");
  };

  return (
    <div className="space-y-8">
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Settings & Configuration
        </h1>
        <p className="text-gray-600 mb-4">
          Configure your You.com API connection, notification preferences, and
          personal playbooks.
        </p>
      </div>

      {/* API Configuration */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center space-x-2 mb-4">
          <Key className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-bold text-gray-900">
            You.com API Configuration
          </h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Key
            </label>
            <div className="relative">
              <input
                type={showApiKey ? "text" : "password"}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 pr-20"
                placeholder="Enter your You.com API key"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-12 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showApiKey ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>

              {connectionStatus === "success" && (
                <Check className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-green-500" />
              )}
              {connectionStatus === "error" && (
                <X className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-red-500" />
              )}
            </div>

            {connectionStatus === "success" && (
              <p className="text-sm text-green-600 mt-2">
                ✅ API key is valid and connected
              </p>
            )}
            {connectionStatus === "error" && (
              <p className="text-sm text-red-600 mt-2">
                ❌ Invalid API key or connection failed
              </p>
            )}
          </div>

          <div className="flex space-x-3">
            <button
              onClick={handleTestConnection}
              disabled={isTestingConnection || !apiKey.trim()}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
            >
              {isTestingConnection ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Testing...</span>
                </>
              ) : (
                <>
                  <Settings className="w-4 h-4" />
                  <span>Test Connection</span>
                </>
              )}
            </button>

            <button
              onClick={handleSaveSettings}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              Save Settings
            </button>
          </div>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">
            How to get your You.com API key:
          </h4>
          <ol className="text-sm text-blue-800 space-y-1">
            <li>
              1. Visit{" "}
              <a
                href="https://api.you.com"
                target="_blank"
                rel="noopener noreferrer"
                className="underline"
              >
                api.you.com
              </a>
            </li>
            <li>2. Sign up or log in to your account</li>
            <li>3. Navigate to API Keys section</li>
            <li>4. Generate a new API key</li>
            <li>5. Copy and paste it above</li>
          </ol>
        </div>
      </div>

      {/* Data Source Toggle */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Data Source</h2>
        <APIToggle
          useLiveData={useLiveData}
          onToggle={setUseLiveData}
          hasApiKey={!!apiKey && connectionStatus === "success"}
        />
      </div>

      {/* Notification Settings */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center space-x-2 mb-4">
          <Bell className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-bold text-gray-900">
            Notification Preferences
          </h2>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-900">Email Notifications</h3>
              <p className="text-sm text-gray-600">Receive alerts via email</p>
            </div>
            <button
              onClick={() => setEmailNotifications(!emailNotifications)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                emailNotifications ? "bg-blue-600" : "bg-gray-300"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  emailNotifications ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-gray-900">Slack Integration</h3>
              <p className="text-sm text-gray-600">
                Send alerts to Slack channels
              </p>
            </div>
            <button
              onClick={() => setSlackNotifications(!slackNotifications)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                slackNotifications ? "bg-blue-600" : "bg-gray-300"
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  slackNotifications ? "translate-x-6" : "translate-x-1"
                }`}
              />
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Risk Threshold for Alerts
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="0"
                max="100"
                value={riskThreshold}
                onChange={(e) => setRiskThreshold(Number(e.target.value))}
                className="flex-1"
              />
              <span className="text-sm font-medium text-gray-900 w-12">
                {riskThreshold}%
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Only send alerts for risks above this threshold
            </p>
          </div>
        </div>
      </div>

      {/* Personal Playbooks */}
      <PersonalPlaybooks
        onSelectPlaybook={(id) => console.log("Selected playbook:", id)}
        onCreatePlaybook={() => console.log("Create playbook")}
      />

      {/* API Usage Metrics */}
      <APIUsageDashboard />
    </div>
  );
}
