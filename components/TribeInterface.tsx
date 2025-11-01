"use client";

import React, { ReactNode, useMemo } from "react";
import { useTribeInterface } from "./TribeInterfaceProvider";
import { TribeModeSelector } from "./TribeModeSelector";
import {
  Eye,
  EyeOff,
  Settings,
  Users,
  Brain,
  Filter,
  Zap,
  AlertCircle,
} from "lucide-react";

interface TribeInterfaceProps {
  children: ReactNode;
  content?: any;
  showModeSelector?: boolean;
  showCognitiveLoad?: boolean;
  className?: string;
}

interface AdaptiveContentProps {
  content: any;
  children?: (adaptedContent: any) => ReactNode;
}

interface FeatureGateProps {
  feature: string;
  children: ReactNode;
  fallback?: ReactNode;
}

/**
 * Main TribeInterface component that wraps content with role-based adaptations
 */
export function TribeInterface({
  children,
  content,
  showModeSelector = true,
  showCognitiveLoad = true,
  className = "",
}: TribeInterfaceProps) {
  const { currentMode, modeConfig, adaptContent, state } = useTribeInterface();

  const adaptedContent = useMemo(() => {
    if (content) {
      return adaptContent(content);
    }
    return null;
  }, [content, adaptContent, currentMode]);

  return (
    <div className={`tribe-interface ${className}`}>
      {/* Mode Selector */}
      {showModeSelector && (
        <div className="mb-6">
          <TribeModeSelector compact />
        </div>
      )}

      {/* Cognitive Load Indicator */}
      {showCognitiveLoad && (
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Brain className="w-4 h-4" />
            <span>
              Interface optimized for <strong>{currentMode}</strong> users
            </span>
          </div>

          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">Complexity:</span>
            <div className="flex items-center gap-1">
              <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    adaptedContent?.metadata.adaptedComplexity >
                    modeConfig.cognitiveLoadLimit
                      ? "bg-red-500"
                      : adaptedContent?.metadata.adaptedComplexity >
                        modeConfig.cognitiveLoadLimit * 0.8
                      ? "bg-yellow-500"
                      : "bg-green-500"
                  }`}
                  style={{
                    width: `${Math.min(
                      100,
                      ((adaptedContent?.metadata.adaptedComplexity || 0) /
                        modeConfig.cognitiveLoadLimit) *
                        100
                    )}%`,
                  }}
                />
              </div>
              <span className="text-xs text-gray-500">
                {adaptedContent?.metadata.adaptedComplexity || 0}/
                {modeConfig.cognitiveLoadLimit}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Content Adaptation Notice */}
      {adaptedContent?.metadata.filteringApplied.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2 text-sm text-blue-800">
            <Filter className="w-4 h-4" />
            <span>
              Content adapted for {currentMode} mode:{" "}
              {adaptedContent.metadata.filteringApplied.join(", ")}
            </span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className={`tribe-content mode-${currentMode}`}>{children}</div>

      {/* Mode-specific Footer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-4">
            <span>Mode: {currentMode}</span>
            {state.adaptationMetrics.contentFiltered > 0 && (
              <span>
                {state.adaptationMetrics.contentFiltered} items adapted
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {modeConfig.features.apiMetrics && (
              <span className="flex items-center gap-1">
                <Zap className="w-3 h-3" />
                API metrics enabled
              </span>
            )}
            {modeConfig.enableCollaboration && (
              <span className="flex items-center gap-1">
                <Users className="w-3 h-3" />
                Collaboration enabled
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Component for adaptive content rendering
 */
export function AdaptiveContent({ content, children }: AdaptiveContentProps) {
  const { adaptContent } = useTribeInterface();

  const adaptedContent = useMemo(() => {
    return adaptContent(content);
  }, [content, adaptContent]);

  if (children) {
    return <>{children(adaptedContent)}</>;
  }

  return (
    <div className="adaptive-content">
      {adaptedContent.title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {adaptedContent.title}
        </h3>
      )}

      {adaptedContent.summary && (
        <p className="text-gray-700 mb-4">{adaptedContent.summary}</p>
      )}

      {adaptedContent.insights.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-900 mb-2">Key Insights</h4>
          <ul className="space-y-2">
            {adaptedContent.insights.map((insight: string, index: number) => (
              <li key={index} className="flex items-start gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                <span className="text-gray-700">{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {adaptedContent.actions.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-900 mb-2">
            Recommended Actions
          </h4>
          <ul className="space-y-2">
            {adaptedContent.actions.map((action: string, index: number) => (
              <li key={index} className="flex items-start gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                <span className="text-gray-700">{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/**
 * Feature gate component that shows/hides content based on current mode
 */
export function FeatureGate({ feature, children, fallback }: FeatureGateProps) {
  const { isFeatureEnabled } = useTribeInterface();

  if (isFeatureEnabled(feature as any)) {
    return <>{children}</>;
  }

  return fallback ? <>{fallback}</> : null;
}

/**
 * Executive-specific simplified card component
 */
export function ExecutiveCard({
  title,
  riskScore,
  actions,
  insight,
}: {
  title: string;
  riskScore: number;
  actions: string[];
  insight: string;
}) {
  const getRiskColor = (score: number) => {
    if (score >= 80) return "text-red-600 bg-red-50 border-red-200";
    if (score >= 60) return "text-orange-600 bg-orange-50 border-orange-200";
    if (score >= 40) return "text-yellow-600 bg-yellow-50 border-yellow-200";
    return "text-green-600 bg-green-50 border-green-200";
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-900">{title}</h3>
        <div
          className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(
            riskScore
          )}`}
        >
          Risk: {riskScore}/100
        </div>
      </div>

      <div className="mb-4 p-4 bg-blue-50 border-l-4 border-blue-500">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <p className="text-blue-900 font-medium">{insight}</p>
        </div>
      </div>

      <div>
        <h4 className="font-semibold text-gray-900 mb-3">
          Immediate Actions Required
        </h4>
        <div className="space-y-2">
          {actions.slice(0, 3).map((action, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
            >
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                {index + 1}
              </div>
              <span className="text-gray-900">{action}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Analyst-specific detailed card component
 */
export function AnalystCard({
  data,
  showTechnicalDetails = true,
}: {
  data: any;
  showTechnicalDetails?: boolean;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-bold text-gray-900">{data.title}</h3>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              Confidence: {data.confidence}%
            </span>
            <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm">
              {data.sources} sources
            </span>
          </div>
        </div>
      </div>

      <div className="p-6">
        <AdaptiveContent content={data} />

        {showTechnicalDetails && (
          <FeatureGate feature="apiMetrics">
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Technical Metrics
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center">
                  <div className="font-bold text-blue-600">
                    {data.apiUsage?.news || 0}
                  </div>
                  <div className="text-gray-600">News API</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-green-600">
                    {data.apiUsage?.search || 0}
                  </div>
                  <div className="text-gray-600">Search API</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-purple-600">
                    {data.apiUsage?.chat || 0}
                  </div>
                  <div className="text-gray-600">Chat API</div>
                </div>
                <div className="text-center">
                  <div className="font-bold text-orange-600">
                    {data.apiUsage?.ari || 0}
                  </div>
                  <div className="text-gray-600">ARI API</div>
                </div>
              </div>
            </div>
          </FeatureGate>
        )}
      </div>
    </div>
  );
}

/**
 * Team-specific collaborative card component
 */
export function TeamCard({
  data,
  onAnnotate,
  onShare,
}: {
  data: any;
  onAnnotate?: () => void;
  onShare?: () => void;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-900">{data.title}</h3>

          <FeatureGate feature="annotations">
            <div className="flex items-center gap-2">
              <button
                onClick={onAnnotate}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200 transition-colors"
              >
                Add Note
              </button>
              <button
                onClick={onShare}
                className="px-3 py-1 text-sm bg-green-100 text-green-800 rounded-lg hover:bg-green-200 transition-colors"
              >
                Share
              </button>
            </div>
          </FeatureGate>
        </div>

        <AdaptiveContent content={data} />

        <FeatureGate feature="annotations">
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-yellow-800">
              <Users className="w-4 h-4" />
              <span>
                Team collaboration enabled - add annotations and share insights
              </span>
            </div>
          </div>
        </FeatureGate>
      </div>
    </div>
  );
}
