"use client";

import React, { useState } from "react";
import {
  Eye,
  Layers,
  Users,
  Settings,
  ChevronDown,
  Brain,
  Lightbulb,
  Target,
  Info,
} from "lucide-react";
import { useTribeInterface } from "./TribeInterfaceProvider";
import { InterfaceMode } from "@/lib/types/tribe-interface";

interface TribeModeSelectorProps {
  showDescription?: boolean;
  compact?: boolean;
  onModeChange?: (mode: InterfaceMode) => void;
}

export function TribeModeSelector({
  showDescription = true,
  compact = false,
  onModeChange,
}: TribeModeSelectorProps) {
  const { currentMode, modeConfig, switchMode, detectedRole, suggestMode } =
    useTribeInterface();
  const [showDropdown, setShowDropdown] = useState(false);

  const modeConfigs = {
    executive: {
      icon: <Eye className="w-4 h-4" />,
      label: "Executive",
      description:
        "Key insights and actions only - simplified for decision makers",
      color: "bg-blue-100 text-blue-800 border-blue-200",
      hoverColor: "hover:bg-blue-200",
      features: ["3 insights max", "No technical details", "Action-focused"],
      audience: "C-level, VPs, Directors",
    },
    analyst: {
      icon: <Layers className="w-4 h-4" />,
      label: "Analyst",
      description: "Detailed analysis with full technical depth and evidence",
      color: "bg-purple-100 text-purple-800 border-purple-200",
      hoverColor: "hover:bg-purple-200",
      features: [
        "Full technical details",
        "API metrics",
        "Source breakdown",
        "Explainability",
      ],
      audience: "Analysts, Researchers, Technical leads",
    },
    team: {
      icon: <Users className="w-4 h-4" />,
      label: "Team",
      description: "Collaborative features with moderate detail level",
      color: "bg-green-100 text-green-800 border-green-200",
      hoverColor: "hover:bg-green-200",
      features: ["Team annotations", "Shared context", "Collaborative tools"],
      audience: "Product teams, Strategy teams, Cross-functional groups",
    },
  };

  const handleModeChange = (mode: InterfaceMode) => {
    switchMode(mode);
    setShowDropdown(false);
    onModeChange?.(mode);
  };

  const currentConfig = modeConfigs[currentMode];
  const suggestedMode = detectedRole ? suggestMode(detectedRole) : null;

  if (compact) {
    return (
      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${currentConfig.color} ${currentConfig.hoverColor}`}
        >
          {currentConfig.icon}
          <span className="font-medium">{currentConfig.label}</span>
          <ChevronDown className="w-3 h-3" />
        </button>

        {showDropdown && (
          <div className="absolute top-full left-0 mt-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
            <div className="p-3 border-b border-gray-100">
              <h4 className="font-medium text-gray-900 mb-1">Interface Mode</h4>
              <p className="text-xs text-gray-600">
                Choose your preferred view
              </p>
            </div>

            {Object.entries(modeConfigs).map(([mode, config]) => (
              <button
                key={mode}
                onClick={() => handleModeChange(mode as InterfaceMode)}
                className={`w-full p-3 text-left hover:bg-gray-50 transition-colors border-l-4 ${
                  currentMode === mode
                    ? "border-blue-500 bg-blue-50"
                    : "border-transparent"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  {config.icon}
                  <span className="font-medium text-gray-900">
                    {config.label}
                  </span>
                  {suggestedMode === mode && (
                    <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                      Suggested
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-600 mb-2">
                  {config.description}
                </p>
                <div className="flex flex-wrap gap-1">
                  {config.features.slice(0, 2).map((feature, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-600" />
            Interface Mode
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Customize your experience based on your role and needs
          </p>
        </div>

        {detectedRole && suggestedMode && suggestedMode !== currentMode && (
          <div className="flex items-center gap-2 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg">
            <Lightbulb className="w-4 h-4 text-yellow-600" />
            <span className="text-sm text-yellow-800">
              <strong>{modeConfigs[suggestedMode].label}</strong> mode suggested
              for {detectedRole}s
            </span>
            <button
              onClick={() => handleModeChange(suggestedMode)}
              className="text-sm text-yellow-700 hover:text-yellow-900 underline"
            >
              Switch
            </button>
          </div>
        )}
      </div>

      {/* Mode Selection */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {Object.entries(modeConfigs).map(([mode, config]) => (
          <button
            key={mode}
            onClick={() => handleModeChange(mode as InterfaceMode)}
            className={`p-4 border-2 rounded-lg text-left transition-all ${
              currentMode === mode
                ? `${config.color} border-current shadow-md transform scale-105`
                : "border-gray-200 hover:border-gray-300 hover:shadow-sm"
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              {config.icon}
              <span className="font-semibold">{config.label}</span>
              {currentMode === mode && (
                <span className="px-2 py-1 text-xs bg-white bg-opacity-50 rounded-full">
                  Active
                </span>
              )}
            </div>

            <p className="text-sm mb-3 opacity-90">{config.description}</p>

            <div className="space-y-1">
              <div className="text-xs font-medium opacity-75">
                Key Features:
              </div>
              {config.features.slice(0, 3).map((feature, idx) => (
                <div
                  key={idx}
                  className="text-xs opacity-75 flex items-center gap-1"
                >
                  <div className="w-1 h-1 bg-current rounded-full"></div>
                  {feature}
                </div>
              ))}
            </div>

            <div className="mt-3 pt-3 border-t border-current border-opacity-20">
              <div className="text-xs opacity-75">
                <strong>Best for:</strong> {config.audience}
              </div>
            </div>
          </button>
        ))}
      </div>

      {/* Current Mode Details */}
      {showDescription && (
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-gray-600" />
            <span className="font-medium text-gray-900">
              Current Mode: {currentConfig.label}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-700">
            <div>
              <div className="font-medium mb-1">Configuration:</div>
              <ul className="space-y-1">
                <li>• Max insights: {modeConfig.maxInsights}</li>
                <li>
                  • Technical details:{" "}
                  {modeConfig.showTechnicalDetails ? "Enabled" : "Disabled"}
                </li>
                <li>
                  • Collaboration:{" "}
                  {modeConfig.enableCollaboration ? "Enabled" : "Disabled"}
                </li>
                <li>• Summary level: {modeConfig.summaryLevel}</li>
              </ul>
            </div>

            <div>
              <div className="font-medium mb-1">Enabled Features:</div>
              <div className="flex flex-wrap gap-1">
                {Object.entries(modeConfig.features)
                  .filter(([, enabled]) => enabled)
                  .map(([feature]) => (
                    <span
                      key={feature}
                      className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                    >
                      {feature.replace(/([A-Z])/g, " $1").toLowerCase()}
                    </span>
                  ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mode Switch History */}
      <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center gap-1">
          <Info className="w-3 h-3" />
          <span>Mode preferences are saved automatically</span>
        </div>

        <div className="flex items-center gap-2">
          <span>
            Cognitive load limit: {modeConfig.cognitiveLoadLimit} elements
          </span>
        </div>
      </div>
    </div>
  );
}
