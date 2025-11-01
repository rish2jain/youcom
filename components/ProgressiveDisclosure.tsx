"use client";

import { useState, ReactNode, useEffect, useMemo } from "react";
import {
  ChevronDown,
  ChevronRight,
  Info,
  Settings,
  Eye,
  EyeOff,
  Layers,
  Brain,
} from "lucide-react";

interface DisclosureLevel {
  id: string;
  title: string;
  content: ReactNode;
  defaultExpanded?: boolean;
  badge?: string;
  description?: string;
  cognitiveWeight?: number; // Weight for cognitive load calculation
  priority?: "critical" | "important" | "supplementary";
}

interface ProgressiveDisclosureProps {
  title: string;
  subtitle?: string;
  levels: DisclosureLevel[];
  mode?: "executive" | "analyst" | "technical";
  onModeChange?: (mode: string) => void;
  maxCognitiveLoad?: number; // Maximum cognitive elements for Level 1
  userRole?: "executive" | "analyst" | "technical";
  onCognitiveLoadChange?: (load: number) => void;
}

export function ProgressiveDisclosure({
  title,
  subtitle,
  levels,
  mode = "executive",
  onModeChange,
  maxCognitiveLoad = 15,
  userRole,
  onCognitiveLoadChange,
}: ProgressiveDisclosureProps) {
  const [expandedLevels, setExpandedLevels] = useState<Set<string>>(
    new Set(
      levels.filter((level) => level.defaultExpanded).map((level) => level.id)
    )
  );
  const [viewMode, setViewMode] = useState(mode);
  const [animatingLevels, setAnimatingLevels] = useState<Set<string>>(
    new Set()
  );

  // Calculate cognitive load for current view
  const cognitiveLoad = useMemo(() => {
    let totalLoad = 0;
    const visibleLevels = getVisibleLevels();

    visibleLevels.forEach((level) => {
      if (expandedLevels.has(level.id)) {
        // Base cognitive weight for expanded content
        totalLoad += level.cognitiveWeight || 5;

        // Additional weight based on priority
        if (level.priority === "critical") totalLoad += 2;
        else if (level.priority === "important") totalLoad += 1;
      } else {
        // Collapsed sections have minimal cognitive load
        totalLoad += 1;
      }
    });

    return totalLoad;
  }, [expandedLevels, viewMode, levels]);

  // Notify parent of cognitive load changes
  useEffect(() => {
    onCognitiveLoadChange?.(cognitiveLoad);
  }, [cognitiveLoad, onCognitiveLoadChange]);

  // Auto-optimize cognitive load for executive mode
  useEffect(() => {
    if (viewMode === "executive" && cognitiveLoad > maxCognitiveLoad) {
      // Keep only critical priority levels expanded
      const criticalLevels = levels
        .filter((level) => level.priority === "critical")
        .map((level) => level.id);
      setExpandedLevels(new Set(criticalLevels.slice(0, 1))); // Max 1 critical section
    }
  }, [viewMode, cognitiveLoad, maxCognitiveLoad, levels]);

  const toggleLevel = (levelId: string) => {
    // Add animation state
    setAnimatingLevels((prev) => new Set(Array.from(prev).concat(levelId)));

    // Remove animation state after transition
    setTimeout(() => {
      setAnimatingLevels((prev) => {
        const newSet = new Set(Array.from(prev));
        newSet.delete(levelId);
        return newSet;
      });
    }, 300);

    const newExpanded = new Set(expandedLevels);
    if (newExpanded.has(levelId)) {
      newExpanded.delete(levelId);
    } else {
      newExpanded.add(levelId);
    }
    setExpandedLevels(newExpanded);
  };

  const getVisibleLevels = () => {
    switch (viewMode) {
      case "executive":
        return levels.slice(0, 1); // Only critical insights
      case "analyst":
        return levels.slice(0, 2); // Insights + supporting details
      case "technical":
        return levels; // All levels
      default:
        return levels;
    }
  };

  const handleModeChange = (newMode: string) => {
    const validMode = newMode as "executive" | "analyst" | "technical";
    setViewMode(validMode);
    onModeChange?.(newMode);

    // Auto-expand levels based on mode
    if (newMode === "executive") {
      setExpandedLevels(new Set([levels[0]?.id].filter(Boolean)));
    } else if (newMode === "analyst") {
      setExpandedLevels(new Set(levels.slice(0, 2).map((l) => l.id)));
    } else if (newMode === "technical") {
      setExpandedLevels(new Set(levels.map((l) => l.id)));
    }
  };

  const getModeConfig = (mode: string) => {
    switch (mode) {
      case "executive":
        return {
          icon: <Eye className="w-4 h-4" />,
          label: "Executive",
          description: "Key insights and actions only",
          color: "bg-blue-100 text-blue-800",
        };
      case "analyst":
        return {
          icon: <Layers className="w-4 h-4" />,
          label: "Analyst",
          description: "Detailed analysis with evidence",
          color: "bg-purple-100 text-purple-800",
        };
      case "technical":
        return {
          icon: <Settings className="w-4 h-4" />,
          label: "Technical",
          description: "Full technical details and metrics",
          color: "bg-gray-100 text-gray-800",
        };
      default:
        return {
          icon: <Info className="w-4 h-4" />,
          label: mode,
          description: "",
          color: "bg-gray-100 text-gray-800",
        };
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      {/* Header with Mode Selector */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            {subtitle && (
              <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
            )}
          </div>

          {/* View Mode Selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">View:</span>
            <div className="flex bg-gray-100 rounded-lg p-1">
              {["executive", "analyst", "technical"].map((modeOption) => {
                const config = getModeConfig(modeOption);
                return (
                  <button
                    key={modeOption}
                    onClick={() => handleModeChange(modeOption)}
                    className={`px-3 py-1 text-sm rounded-md transition-colors flex items-center gap-1 ${
                      viewMode === modeOption
                        ? config.color
                        : "text-gray-600 hover:text-gray-800 hover:bg-gray-200"
                    }`}
                    title={config.description}
                  >
                    {config.icon}
                    <span className="hidden sm:inline">{config.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Mode Description and Cognitive Load */}
        <div className="mt-2 flex items-center justify-between">
          <div className="text-xs text-gray-500">
            {getModeConfig(viewMode).description}
          </div>

          {/* Cognitive Load Indicator */}
          <div className="flex items-center gap-2 text-xs">
            <Brain className="w-3 h-3 text-gray-400" />
            <span
              className={`font-medium ${
                cognitiveLoad > maxCognitiveLoad
                  ? "text-red-600"
                  : cognitiveLoad > maxCognitiveLoad * 0.8
                  ? "text-orange-600"
                  : "text-green-600"
              }`}
            >
              {cognitiveLoad}/{maxCognitiveLoad} elements
            </span>
            {cognitiveLoad > maxCognitiveLoad && (
              <span className="text-red-500 text-xs">
                ⚠️ High cognitive load
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Disclosure Levels */}
      <div className="divide-y divide-gray-200">
        {getVisibleLevels().map((level, index) => {
          const isExpanded = expandedLevels.has(level.id);
          const isFirst = index === 0;

          return (
            <div key={level.id} className={isFirst ? "bg-blue-50" : ""}>
              {/* Level Header */}
              <button
                onClick={() => toggleLevel(level.id)}
                className="w-full p-4 text-left hover:bg-gray-50 transition-colors flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-500" />
                    )}
                    <span className="font-medium text-gray-900">
                      {level.title}
                    </span>
                  </div>

                  {level.badge && (
                    <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                      {level.badge}
                    </span>
                  )}
                </div>

                {level.description && (
                  <span className="text-sm text-gray-500 hidden md:block">
                    {level.description}
                  </span>
                )}
              </button>

              {/* Level Content with Animation */}
              {isExpanded && (
                <div
                  className={`px-4 pb-4 transition-all duration-300 ease-in-out ${
                    animatingLevels.has(level.id)
                      ? "animate-pulse"
                      : "animate-fadeIn"
                  }`}
                >
                  <div className="pl-7 transform transition-transform duration-200">
                    {level.content}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer with Quick Actions */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>
              Showing {expandedLevels.size} of {getVisibleLevels().length}{" "}
              sections
            </span>
            {viewMode !== "technical" && (
              <button
                onClick={() => handleModeChange("technical")}
                className="text-blue-600 hover:underline flex items-center gap-1"
              >
                <EyeOff className="w-3 h-3" />
                Show all details
              </button>
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setExpandedLevels(new Set())}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Collapse All
            </button>
            <button
              onClick={() =>
                setExpandedLevels(new Set(getVisibleLevels().map((l) => l.id)))
              }
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Expand All
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Utility component for creating disclosure content sections
export function DisclosureSection({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`space-y-4 ${className}`}>{children}</div>;
}

// Utility component for metric displays
export function MetricDisplay({
  label,
  value,
  unit = "",
  trend,
  color = "text-gray-900",
}: {
  label: string;
  value: string | number;
  unit?: string;
  trend?: "up" | "down" | "neutral";
  color?: string;
}) {
  const getTrendIcon = () => {
    switch (trend) {
      case "up":
        return "↗️";
      case "down":
        return "↘️";
      case "neutral":
        return "→";
      default:
        return "";
    }
  };

  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-gray-600">{label}:</span>
      <div className="flex items-center gap-1">
        <span className={`font-medium ${color}`}>
          {value}
          {unit}
        </span>
        {trend && <span className="text-xs">{getTrendIcon()}</span>}
      </div>
    </div>
  );
}
