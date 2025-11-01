"use client";

import React, { useMemo } from "react";
import { contentFilterEngine } from "@/lib/content-filter";
import { useTribeInterface } from "./TribeInterfaceProvider";
import {
  Brain,
  Filter,
  Zap,
  Eye,
  Users,
  Settings,
  ChevronRight,
  Info,
} from "lucide-react";

interface ContentSummarizerProps {
  content: any;
  maxLength?: number;
  showMetrics?: boolean;
  className?: string;
}

interface FilteredContentDisplayProps {
  originalContent: any;
  filteredContent: any;
  showComparison?: boolean;
}

interface CollaborativeContentProps {
  content: any;
  enableTeamFeatures?: boolean;
}

/**
 * Content summarizer that adapts content based on current interface mode
 */
export function ContentSummarizer({
  content,
  maxLength = 200,
  showMetrics = true,
  className = "",
}: ContentSummarizerProps) {
  const { currentMode, modeConfig } = useTribeInterface();

  const summary = useMemo(() => {
    return contentFilterEngine().generateSummary(
      content,
      currentMode,
      maxLength
    );
  }, [content, currentMode, maxLength]);

  const filteredContent = useMemo(() => {
    return contentFilterEngine().applyContentFilter(content, currentMode);
  }, [content, currentMode]);

  const complexity = useMemo(() => {
    return (contentFilterEngine() as any)["calculateComplexity"](
      filteredContent
    );
  }, [filteredContent]);

  const getModeIcon = () => {
    switch (currentMode) {
      case "executive":
        return <Eye className="w-4 h-4 text-blue-600" />;
      case "analyst":
        return <Settings className="w-4 h-4 text-purple-600" />;
      case "team":
        return <Users className="w-4 h-4 text-green-600" />;
      default:
        return <Brain className="w-4 h-4 text-gray-600" />;
    }
  };

  return (
    <div className={`content-summarizer ${className}`}>
      {/* Summary Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {getModeIcon()}
          <span className="text-sm font-medium text-gray-700">
            {currentMode.charAt(0).toUpperCase() + currentMode.slice(1)} Summary
          </span>
        </div>

        {showMetrics && (
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Filter className="w-3 h-3" />
              Complexity: {complexity}/{modeConfig.cognitiveLoadLimit}
            </span>
            <span>
              {summary.length}/{maxLength} chars
            </span>
          </div>
        )}
      </div>

      {/* Summary Content */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <p className="text-gray-800 leading-relaxed">{summary}</p>

        {/* Mode-specific indicators */}
        {currentMode === "executive" && (
          <div className="mt-3 flex items-center gap-2 text-xs text-blue-600">
            <Zap className="w-3 h-3" />
            <span>
              Simplified for executive consumption - technical details filtered
            </span>
          </div>
        )}

        {currentMode === "team" && (
          <div className="mt-3 flex items-center gap-2 text-xs text-green-600">
            <Users className="w-3 h-3" />
            <span>Team-focused summary - collaboration features enabled</span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Component to display filtered content with comparison to original
 */
export function FilteredContentDisplay({
  originalContent,
  filteredContent,
  showComparison = false,
}: FilteredContentDisplayProps) {
  const { currentMode } = useTribeInterface();
  const [showOriginal, setShowOriginal] = React.useState(false);

  const filteringApplied = useMemo(() => {
    const changes = [];

    // Check for technical jargon filtering
    if (originalContent.summary !== filteredContent.summary) {
      changes.push("Technical jargon simplified");
    }

    // Check for content reduction
    if (
      originalContent.key_insights?.length >
      filteredContent.key_insights?.length
    ) {
      changes.push("Insights limited");
    }

    if (
      originalContent.recommended_actions?.length >
      filteredContent.recommended_actions?.length
    ) {
      changes.push("Actions prioritized");
    }

    // Check for removed technical details
    if (originalContent.api_usage && !filteredContent.api_usage) {
      changes.push("Technical details hidden");
    }

    return changes;
  }, [originalContent, filteredContent]);

  return (
    <div className="filtered-content-display">
      {/* Filtering Notice */}
      {filteringApplied.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-blue-800">
              <Filter className="w-4 h-4" />
              <span>
                Content adapted for {currentMode} mode:{" "}
                {filteringApplied.join(", ")}
              </span>
            </div>

            {showComparison && (
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className="text-xs text-blue-600 hover:text-blue-800 underline"
              >
                {showOriginal ? "Hide" : "Show"} original
              </button>
            )}
          </div>
        </div>
      )}

      {/* Filtered Content */}
      <div className="space-y-4">
        {filteredContent.title && (
          <h3 className="text-lg font-semibold text-gray-900">
            {filteredContent.title}
          </h3>
        )}

        {filteredContent.executive_summary && (
          <div className="p-4 bg-blue-50 border-l-4 border-blue-500">
            <h4 className="font-medium text-blue-900 mb-2">
              Executive Summary
            </h4>
            <p className="text-blue-800">{filteredContent.executive_summary}</p>
          </div>
        )}

        {filteredContent.summary && !filteredContent.executive_summary && (
          <p className="text-gray-700">{filteredContent.summary}</p>
        )}

        {filteredContent.priority_actions && (
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">Priority Actions</h4>
            {filteredContent.priority_actions.map(
              (action: any, index: number) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg"
                >
                  <div className="w-6 h-6 bg-red-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-900">{action.action}</p>
                    <div className="flex items-center gap-4 mt-1 text-xs text-gray-600">
                      <span>Priority: {action.priority}</span>
                      <span>Timeline: {action.timeline}</span>
                      <span>Owner: {action.owner}</span>
                    </div>
                  </div>
                </div>
              )
            )}
          </div>
        )}

        {filteredContent.key_insights && (
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">Key Insights</h4>
            <ul className="space-y-2">
              {filteredContent.key_insights.map(
                (insight: string, index: number) => (
                  <li key={index} className="flex items-start gap-2">
                    <ChevronRight className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{insight}</span>
                  </li>
                )
              )}
            </ul>
          </div>
        )}

        {filteredContent.evidence_summary && (
          <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-4 h-4 text-gray-600" />
              <span className="font-medium text-gray-900">
                Evidence Summary
              </span>
            </div>
            <p className="text-sm text-gray-700">
              {filteredContent.evidence_summary.summary}
            </p>
          </div>
        )}

        {filteredContent.primary_impact && (
          <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
            <h4 className="font-medium text-orange-900 mb-1">Primary Impact</h4>
            <div className="text-sm text-orange-800">
              <span className="font-medium">
                {filteredContent.primary_impact.area}
              </span>
              <span className="mx-2">•</span>
              <span className="capitalize">
                {filteredContent.primary_impact.severity} severity
              </span>
            </div>
            <p className="text-sm text-orange-700 mt-1">
              {filteredContent.primary_impact.description}
            </p>
          </div>
        )}
      </div>

      {/* Original Content (if shown) */}
      {showOriginal && (
        <div className="mt-6 p-4 bg-gray-100 border border-gray-300 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-3">Original Content</h4>
          <div className="text-sm text-gray-700 space-y-2">
            {originalContent.summary && (
              <p>
                <strong>Summary:</strong> {originalContent.summary}
              </p>
            )}
            {originalContent.key_insights && (
              <div>
                <strong>
                  Insights ({originalContent.key_insights.length}):
                </strong>
                <ul className="list-disc list-inside ml-4 mt-1">
                  {originalContent.key_insights.map(
                    (insight: string, index: number) => (
                      <li key={index}>{insight}</li>
                    )
                  )}
                </ul>
              </div>
            )}
            {originalContent.api_usage && (
              <p>
                <strong>API Usage:</strong>{" "}
                {JSON.stringify(originalContent.api_usage)}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Component for team-mode collaborative content features
 */
export function CollaborativeContent({
  content,
  enableTeamFeatures = true,
}: CollaborativeContentProps) {
  const { currentMode, isFeatureEnabled } = useTribeInterface();
  const [showCollaboration, setShowCollaboration] = React.useState(false);

  if (currentMode !== "team" || !enableTeamFeatures) {
    return null;
  }

  return (
    <div className="collaborative-content mt-4">
      <button
        onClick={() => setShowCollaboration(!showCollaboration)}
        className="flex items-center gap-2 text-sm text-green-600 hover:text-green-800 mb-3"
      >
        <Users className="w-4 h-4" />
        <span>Team Collaboration Features</span>
        <ChevronRight
          className={`w-3 h-3 transition-transform ${
            showCollaboration ? "rotate-90" : ""
          }`}
        />
      </button>

      {showCollaboration && (
        <div className="space-y-3">
          {isFeatureEnabled("annotations") && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <h5 className="font-medium text-green-900 mb-2">
                Team Annotations
              </h5>
              <p className="text-sm text-green-800 mb-3">
                Add team notes and context to this analysis for better
                collaboration.
              </p>
              <button className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700">
                Add Annotation
              </button>
            </div>
          )}

          {isFeatureEnabled("sharing") && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <h5 className="font-medium text-blue-900 mb-2">
                Share with Team
              </h5>
              <p className="text-sm text-blue-800 mb-3">
                Share this analysis with team members and stakeholders.
              </p>
              <div className="flex gap-2">
                <button className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                  Share via Email
                </button>
                <button className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded hover:bg-blue-200">
                  Copy Link
                </button>
              </div>
            </div>
          )}

          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h5 className="font-medium text-yellow-900 mb-2">Team Context</h5>
            <p className="text-sm text-yellow-800">
              This analysis requires cross-functional coordination. Consider
              involving:
            </p>
            <ul className="text-sm text-yellow-700 mt-2 space-y-1">
              <li>• Product team for feature impact assessment</li>
              <li>• Marketing team for competitive positioning</li>
              <li>• Engineering team for technical feasibility</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
