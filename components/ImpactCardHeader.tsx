"use client";

import React, { memo } from "react";
import { AlertTriangle, Clock } from "lucide-react";

interface ImpactCard {
  id: number;
  competitor_name: string;
  risk_score: number;
  risk_level: string;
  confidence_score: number;
  total_sources: number;
  created_at: string;
  requires_review: boolean;
  key_insights: string[];
}

interface ImpactCardHeaderProps {
  card: ImpactCard;
  onClick: () => void;
  isSelected: boolean;
  viewMode: "compact" | "detailed" | "technical";
}

const ImpactCardHeader = memo<ImpactCardHeaderProps>(
  ({ card, onClick, isSelected, viewMode }) => {
    const getRiskColor = (riskLevel: string) => {
      const normalizedLevel = riskLevel.toLowerCase();
      switch (normalizedLevel) {
        case "critical":
          return "text-red-600 bg-red-100";
        case "high":
          return "text-orange-600 bg-orange-100";
        case "medium":
          return "text-yellow-600 bg-yellow-100";
        case "low":
          return "text-green-600 bg-green-100";
        default:
          return "text-gray-600 bg-gray-100";
      }
    };

    const getRiskGaugeColor = (score: number) => {
      if (score >= 80) return "#ef4444"; // red
      if (score >= 60) return "#f97316"; // orange
      if (score >= 40) return "#eab308"; // yellow
      return "#22c55e"; // green
    };

    const formatTimestamp = (timestamp: string) => {
      try {
        return new Date(timestamp).toLocaleString();
      } catch {
        return "Unknown time";
      }
    };

    return (
      <div
        onClick={onClick}
        className={`relative p-4 border rounded-lg cursor-pointer transition-all duration-200 ${
          isSelected
            ? "border-blue-500 bg-blue-50 shadow-md"
            : "border-gray-200 bg-white hover:shadow-md hover:border-gray-300"
        }`}
      >
        {/* Header Section */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1">
            <h4 className="font-medium text-gray-900 text-lg">
              {card.competitor_name}
            </h4>

            {/* Risk Level and Score */}
            <div className="flex items-center space-x-3 mt-2">
              <span
                className={`px-3 py-1 text-xs font-medium rounded-full ${getRiskColor(
                  card.risk_level
                )}`}
              >
                {card.risk_level.toUpperCase()} RISK
              </span>
              <span className="text-sm text-gray-600">
                Score: {card.risk_score}/100
              </span>
              <span className="text-sm text-gray-500">
                Confidence: {card.confidence_score}%
              </span>
            </div>

            {/* Review Required Badge */}
            {card.requires_review && (
              <div className="mt-2 inline-flex items-center space-x-2 rounded-full bg-red-50 px-3 py-1 text-xs text-red-600">
                <AlertTriangle className="w-3 h-3" />
                <span>Analyst review requested</span>
              </div>
            )}
          </div>

          {/* Risk Score Display */}
          <div className="text-right ml-4">
            <div
              className="text-3xl font-bold mb-1"
              style={{
                color: getRiskGaugeColor(card.risk_score),
              }}
            >
              {card.risk_score}
            </div>
            <div className="text-xs text-gray-500">
              {card.total_sources} sources
            </div>
          </div>
        </div>

        {/* Key Insight Preview (for detailed and technical modes) */}
        {viewMode !== "compact" && card.key_insights.length > 0 && (
          <div className="mb-3">
            <div className="text-sm text-gray-700">
              <strong>Key Insight:</strong> {card.key_insights[0]}
            </div>
            {viewMode === "technical" && card.key_insights.length > 1 && (
              <div className="text-xs text-gray-600 mt-1">
                +{card.key_insights.length - 1} more insights
              </div>
            )}
          </div>
        )}

        {/* Timestamp and Expand Indicator */}
        <div className="flex justify-between items-center">
          <div className="flex items-center text-xs text-gray-500">
            <Clock className="w-3 h-3 mr-1" />
            {formatTimestamp(card.created_at)}
          </div>

          <div className="flex items-center space-x-2">
            {isSelected && (
              <span className="text-xs text-blue-600 font-medium">
                Expanded
              </span>
            )}
            <div
              className={`transform transition-transform duration-200 ${
                isSelected ? "rotate-180" : ""
              }`}
            >
              <svg
                className="w-4 h-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Technical Mode: Additional Metrics */}
        {viewMode === "technical" && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-sm font-medium text-gray-900">
                  {card.risk_score}
                </div>
                <div className="text-xs text-gray-500">Risk Score</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-900">
                  {card.confidence_score}%
                </div>
                <div className="text-xs text-gray-500">Confidence</div>
              </div>
              <div>
                <div className="text-sm font-medium text-gray-900">
                  {card.total_sources}
                </div>
                <div className="text-xs text-gray-500">Sources</div>
              </div>
            </div>
          </div>
        )}

        {/* Hover State Indicator */}
        <div className="absolute inset-0 rounded-lg border-2 border-transparent hover:border-blue-200 transition-colors duration-200 pointer-events-none" />
      </div>
    );
  }
);

ImpactCardHeader.displayName = "ImpactCardHeader";

export default ImpactCardHeader;
