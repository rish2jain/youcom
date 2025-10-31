import React from "react";
import { useState } from "react";
import {
  ChartBarIcon,
  ClockIcon,
  PlayIcon,
  InformationCircleIcon,
  ShareIcon,
  ArrowDownTrayIcon,
} from "@heroicons/react/24/outline";

interface ImpactCardProps {
  data: {
    title: string;
    riskScore: number;
    riskLevel: "low" | "medium" | "high" | "critical";
    impactAreas: string[];
    timeline: string;
    confidence: number;
    sources: number;
    lastUpdated: string;
    keyInsights?: string;
    timelineEvents?: Array<{
      title: string;
      time: string;
      status: "completed" | "pending";
    }>;
    recommendedActions?: Array<{
      title: string;
      description: string;
      priority: "high" | "medium" | "low";
      timeline: string;
    }>;
    sourceBreakdown?: {
      tier1: number;
      tier2: number;
      tier3: number;
    };
    processingDetails?: {
      completedAt: string;
      processingTime: string;
      apisUsed: string[];
    };
  };
}

interface TabConfig {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const ImpactCard: React.FC<ImpactCardProps> = ({ data }) => {
  const [activeTab, setActiveTab] = useState("overview");
  const [showExportMenu, setShowExportMenu] = useState(false);

  const tabs: TabConfig[] = [
    {
      id: "overview",
      label: "Overview",
      icon: ChartBarIcon,
      description: "Impact areas, key insights, and confidence scores",
    },
    {
      id: "timeline",
      label: "Timeline",
      icon: ClockIcon,
      description: "When did this happen and trend analysis",
    },
    {
      id: "actions",
      label: "Actions",
      icon: PlayIcon,
      description: "Recommended actions and next steps",
    },
    {
      id: "details",
      label: "Details",
      icon: InformationCircleIcon,
      description: "Sources, metadata, and technical details",
    },
  ];

  const getRiskColor = (level: string) => {
    switch (level) {
      case "critical":
        return "bg-red-500 text-white";
      case "high":
        return "bg-orange-500 text-white";
      case "medium":
        return "bg-yellow-500 text-white";
      case "low":
        return "bg-green-500 text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  const getRiskIcon = (level: string) => {
    switch (level) {
      case "critical":
        return "🚨";
      case "high":
        return "⚠️";
      case "medium":
        return "⚡";
      case "low":
        return "✅";
      default:
        return "❓";
    }
  };

  const exportOptions = [
    { label: "Export as PDF", action: "pdf" },
    { label: "Export as JSON", action: "json" },
    { label: "Share via Email", action: "email" },
    { label: "Copy Link", action: "link" },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case "overview":
        return (
          <div className="space-y-6">
            {/* Key Insights */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Key Insights</h4>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <p className="text-gray-800">
                  {data.keyInsights ||
                    `${data.title} represents a ${
                      data.riskLevel
                    } risk competitive development that requires attention across ${data.impactAreas.join(
                      ", "
                    )} areas.`}
                </p>
              </div>
            </div>

            {/* Impact Areas */}
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Impact Areas</h4>
              <div className="grid grid-cols-2 gap-3">
                {data.impactAreas.map((area, index) => (
                  <div key={index} className="bg-gray-50 p-3 rounded-lg">
                    <span className="text-sm font-medium text-gray-800">
                      {area}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Confidence & Sources */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-green-600 font-semibold">
                    {data.confidence}%
                  </span>
                  <span className="text-sm text-gray-600">confident</span>
                </div>
                <p className="text-xs text-gray-500">Based on source quality</p>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <div className="flex items-center space-x-2 mb-1">
                  <span className="text-blue-600 font-semibold">
                    {data.sources}
                  </span>
                  <span className="text-sm text-gray-600">sources</span>
                </div>
                <p className="text-xs text-gray-500">
                  Last updated {data.lastUpdated}
                </p>
              </div>
            </div>
          </div>
        );

      case "timeline":
        return (
          <div className="space-y-4">
            {data.timelineEvents?.map((event, index) => (
              <div
                key={index}
                className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg"
              >
                <div
                  className={`w-3 h-3 rounded-full ${
                    event.status === "completed" ? "bg-blue-500" : "bg-gray-300"
                  }`}
                ></div>
                <div>
                  <p className="font-medium text-gray-900">{event.title}</p>
                  <p className="text-sm text-gray-600">{event.time}</p>
                </div>
              </div>
            )) || (
              <div className="text-center py-8 text-gray-500">
                <p>Timeline data will be populated as events are detected</p>
                <p className="text-sm mt-2">Last updated: {data.lastUpdated}</p>
              </div>
            )}
          </div>
        );

      case "actions":
        return (
          <div className="space-y-4">
            {data.recommendedActions?.map((action, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border ${
                  action.priority === "high"
                    ? "bg-orange-50 border-orange-200"
                    : action.priority === "medium"
                    ? "bg-yellow-50 border-yellow-200"
                    : "bg-green-50 border-green-200"
                }`}
              >
                <div className="flex items-start space-x-3">
                  <span className="text-lg">
                    {action.priority === "high"
                      ? "🎯"
                      : action.priority === "medium"
                      ? "⚡"
                      : "✅"}
                  </span>
                  <div>
                    <h4 className="font-semibold text-gray-900">
                      {action.title}
                    </h4>
                    <p className="text-gray-700 mt-1">{action.description}</p>
                    <div className="mt-3 flex items-center space-x-3">
                      <span className="text-sm text-gray-600">
                        Priority:{" "}
                        {action.priority.charAt(0).toUpperCase() +
                          action.priority.slice(1)}
                      </span>
                      <span className="text-sm text-gray-600">
                        Timeline: {action.timeline}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )) || (
              <div className="text-center py-8 text-gray-500">
                <p>
                  Recommended actions will be generated based on impact analysis
                </p>
              </div>
            )}

            <button className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
              Create Action Item
            </button>
          </div>
        );

      case "details":
        return (
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">
                Source Breakdown
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Tier 1 Sources</span>
                  <span className="text-sm text-gray-600">
                    {data.sourceBreakdown?.tier1 ||
                      Math.floor(data.sources * 0.6)}{" "}
                    sources
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Tier 2 Sources</span>
                  <span className="text-sm text-gray-600">
                    {data.sourceBreakdown?.tier2 ||
                      Math.floor(data.sources * 0.3)}{" "}
                    sources
                  </span>
                </div>
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium">Tier 3 Sources</span>
                  <span className="text-sm text-gray-600">
                    {data.sourceBreakdown?.tier3 ||
                      Math.floor(data.sources * 0.1)}{" "}
                    sources
                  </span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-3">
                Processing Details
              </h4>
              <div className="text-sm text-gray-600 space-y-1">
                <p>
                  Analysis completed:{" "}
                  {data.processingDetails?.completedAt || data.lastUpdated}
                </p>
                <p>
                  Processing time:{" "}
                  {data.processingDetails?.processingTime || "< 5 minutes"}
                </p>
                <p>
                  APIs used:{" "}
                  {data.processingDetails?.apisUsed?.join(", ") ||
                    "News, Search, Custom Agent"}
                </p>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      {/* Card Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {data.title}
            </h3>

            {/* Risk Score Display */}
            <div className="flex items-center space-x-4 mb-3">
              <div
                className={`px-3 py-1.5 rounded-lg flex items-center space-x-2 ${getRiskColor(
                  data.riskLevel
                )}`}
              >
                <span>{getRiskIcon(data.riskLevel)}</span>
                <span className="font-semibold">{data.riskScore}/100</span>
                <span className="capitalize">{data.riskLevel}</span>
              </div>

              <div className="text-sm text-gray-600">
                <span className="font-medium">Affects:</span>{" "}
                {data.impactAreas.join(", ")}
              </div>

              <div className="text-sm text-gray-600">
                <span className="font-medium">Timeline:</span> {data.timeline}
              </div>
            </div>
          </div>

          {/* Export/Share Actions */}
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <ShareIcon className="w-4 h-4" />
              <span className="text-sm font-medium">Share</span>
              <ArrowDownTrayIcon className="w-4 h-4" />
            </button>

            {showExportMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-10">
                <div className="py-1">
                  {exportOptions.map((option, index) => (
                    <button
                      key={index}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      onClick={() => {
                        console.log(`Export action: ${option.action}`);
                        setShowExportMenu(false);
                      }}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-0">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-6 py-4 border-b-2 transition-colors ${
                  isActive
                    ? "border-blue-500 text-blue-600 bg-blue-50"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                }`}
                title={tab.description}
              >
                <Icon className="w-4 h-4" />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">{renderTabContent()}</div>
    </div>
  );
};

export default ImpactCard;
