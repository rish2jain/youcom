"use client";

import { useState, useEffect, ReactNode } from "react";
import {
  Brain,
  AlertTriangle,
  CheckCircle,
  Info,
  Settings,
} from "lucide-react";
import {
  CognitiveLoadManager,
  ContentSection,
  CognitiveElement,
  useCognitiveLoadManager,
} from "@/lib/cognitive-load-manager";

interface CognitiveLoadOptimizerProps {
  sections: ContentSection[];
  userRole?: "executive" | "analyst" | "technical";
  onOptimizationChange?: (optimizedSections: ContentSection[]) => void;
  showDebugInfo?: boolean;
  children?: ReactNode;
}

export function CognitiveLoadOptimizer({
  sections,
  userRole = "analyst",
  onOptimizationChange,
  showDebugInfo = false,
  children,
}: CognitiveLoadOptimizerProps) {
  const [currentRole, setCurrentRole] = useState(userRole);
  const [showOptimizer, setShowOptimizer] = useState(false);

  const {
    optimizedSections,
    totalLoad,
    recommendations,
    complexity,
    level1Summary,
    isOverloaded,
    roleConfig,
  } = useCognitiveLoadManager(sections, currentRole);

  // Notify parent of optimization changes
  useEffect(() => {
    onOptimizationChange?.(optimizedSections);
  }, [optimizedSections, onOptimizationChange]);

  const getLoadColor = (load: number, maxLoad: number) => {
    const percentage = (load / maxLoad) * 100;
    if (percentage > 100) return "text-red-600 bg-red-50";
    if (percentage > 80) return "text-orange-600 bg-orange-50";
    if (percentage > 60) return "text-yellow-600 bg-yellow-50";
    return "text-green-600 bg-green-50";
  };

  const getComplexityIcon = (complexity: string) => {
    switch (complexity) {
      case "low":
        return "🟢";
      case "medium":
        return "🟡";
      case "high":
        return "🔴";
      default:
        return "⚪";
    }
  };

  return (
    <div className="space-y-4">
      {/* Cognitive Load Indicator */}
      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
        <div className="flex items-center gap-3">
          <Brain className="w-5 h-5 text-gray-600" />
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-900">
                Cognitive Load
              </span>
              <span
                className={`px-2 py-1 text-xs rounded-full font-medium ${getLoadColor(
                  totalLoad,
                  roleConfig.maxCognitiveLoad
                )}`}
              >
                {totalLoad}/{roleConfig.maxCognitiveLoad}
              </span>
            </div>
            <div className="text-xs text-gray-600">
              {getComplexityIcon(complexity.overallComplexity)}{" "}
              {complexity.overallComplexity} complexity
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isOverloaded && (
            <div className="flex items-center gap-1 text-red-600">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-xs font-medium">Overloaded</span>
            </div>
          )}

          <button
            onClick={() => setShowOptimizer(!showOptimizer)}
            className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
          >
            <Settings className="w-4 h-4" />
            {showOptimizer ? "Hide" : "Optimize"}
          </button>
        </div>
      </div>

      {/* Optimization Panel */}
      {showOptimizer && (
        <div className="p-4 bg-white border border-gray-200 rounded-lg space-y-4">
          {/* Role Selector */}
          <div>
            <label className="text-sm font-medium text-gray-900 mb-2 block">
              User Role
            </label>
            <div className="flex gap-2">
              {(["executive", "analyst", "technical"] as const).map((role) => (
                <button
                  key={role}
                  onClick={() => setCurrentRole(role)}
                  className={`px-3 py-2 text-sm rounded-md transition-colors ${
                    currentRole === role
                      ? "bg-blue-100 text-blue-800 border border-blue-200"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {role.charAt(0).toUpperCase() + role.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center gap-2">
                <Info className="w-4 h-4" />
                Optimization Recommendations
              </h4>
              <ul className="space-y-1">
                {recommendations.map((rec, index) => (
                  <li
                    key={index}
                    className="text-sm text-gray-600 flex items-start gap-2"
                  >
                    <CheckCircle className="w-3 h-3 text-green-600 mt-0.5 flex-shrink-0" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Complexity Analysis */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">
              Content Analysis
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(complexity.elementBreakdown).map(
                ([type, count]) => (
                  <div
                    key={type}
                    className="text-center p-2 bg-gray-50 rounded"
                  >
                    <div className="text-lg font-bold text-gray-900">
                      {count}
                    </div>
                    <div className="text-xs text-gray-600 capitalize">
                      {type}s
                    </div>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Suggestions */}
          {complexity.suggestions.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">
                Improvement Suggestions
              </h4>
              <ul className="space-y-1">
                {complexity.suggestions.map((suggestion, index) => (
                  <li
                    key={index}
                    className="text-sm text-gray-600 flex items-start gap-2"
                  >
                    <span className="text-yellow-500 mt-0.5">💡</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Debug Information */}
          {showDebugInfo && (
            <div className="border-t pt-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">
                Debug Information
              </h4>
              <div className="text-xs text-gray-600 space-y-1">
                <div>Original sections: {sections.length}</div>
                <div>Optimized sections: {optimizedSections.length}</div>
                <div>Max cognitive load: {roleConfig.maxCognitiveLoad}</div>
                <div>Current load: {totalLoad}</div>
                <div>Attention span: {roleConfig.attentionSpan}s</div>
                <div>
                  Preferred complexity: {roleConfig.preferredComplexity}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Level 1 Summary (for executive mode) */}
      {currentRole === "executive" && level1Summary.elements.length > 0 && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="text-sm font-medium text-blue-900 mb-2 flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Executive Summary (Auto-generated)
          </h3>
          <div className="space-y-2">
            {level1Summary.elements.slice(0, 3).map((element, index) => (
              <div key={element.id} className="text-sm text-blue-800">
                <span className="font-medium">
                  {element.type.charAt(0).toUpperCase() + element.type.slice(1)}
                  :
                </span>{" "}
                {element.priority} priority element
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Render children with optimized context */}
      {children}
    </div>
  );
}

/**
 * Higher-order component for automatic cognitive load optimization
 */
export function withCognitiveOptimization<T extends object>(
  WrappedComponent: React.ComponentType<T>,
  defaultSections: ContentSection[] = []
) {
  return function CognitiveOptimizedComponent(
    props: T & {
      userRole?: "executive" | "analyst" | "technical";
      sections?: ContentSection[];
    }
  ) {
    const {
      userRole = "analyst",
      sections = defaultSections,
      ...restProps
    } = props;

    const { optimizedSections, totalLoad, isOverloaded } =
      useCognitiveLoadManager(sections, userRole);

    return (
      <div className="space-y-4">
        {isOverloaded && (
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-600" />
            <span className="text-sm text-yellow-800">
              Content optimized for better readability (cognitive load:{" "}
              {totalLoad})
            </span>
          </div>
        )}
        <WrappedComponent {...(restProps as T)} sections={optimizedSections} />
      </div>
    );
  };
}

/**
 * Utility function to create cognitive elements from content
 */
export function createCognitiveElement(
  id: string,
  type: CognitiveElement["type"],
  complexity: CognitiveElement["complexity"] = "medium",
  priority: CognitiveElement["priority"] = "important"
): CognitiveElement {
  return { id, type, complexity, priority };
}

/**
 * Utility function to create content sections
 */
export function createContentSection(
  id: string,
  title: string,
  elements: CognitiveElement[],
  level: 1 | 2 | 3 = 1
): ContentSection {
  return { id, title, elements, level };
}
