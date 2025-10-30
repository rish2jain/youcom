"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ThumbsUp, ThumbsDown, Star, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";

interface MLFeedbackPanelProps {
  impactCardId: number;
  currentRiskScore: number;
  currentSeverity: string;
  currentCategory: string;
  currentRelevance: number;
}

interface FeedbackPayload {
  impact_card_id: number;
  feedback_type: "accuracy" | "relevance" | "severity";
  original_value: number | string;
  corrected_value: number | string;
  confidence: number;
}

export function MLFeedbackPanel({
  impactCardId,
  currentRiskScore,
  currentSeverity,
  currentCategory,
  currentRelevance,
}: MLFeedbackPanelProps) {
  const [feedbackType, setFeedbackType] = useState<
    "accuracy" | "relevance" | "severity" | null
  >(null);
  const [correctedRiskScore, setCorrectedRiskScore] =
    useState(currentRiskScore);
  const [correctedSeverity, setCorrectedSeverity] = useState(currentSeverity);
  const [correctedRelevance, setCorrectedRelevance] =
    useState(currentRelevance);
  const [confidence, setConfidence] = useState(0.8);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const feedbackMutation = useMutation({
    mutationFn: (payload: FeedbackPayload) =>
      api.post("/api/v1/ml_feedback/", payload),
    onSuccess: () => {
      setFeedbackMessage(
        "Thank you! Your feedback will help improve our ML models."
      );
      setShowFeedbackForm(false);
      setFeedbackType(null);
      queryClient.invalidateQueries({ queryKey: ["mlPerformance"] });
      setTimeout(() => setFeedbackMessage(null), 5000);
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Failed to submit feedback";
      setFeedbackMessage(message);
      setTimeout(() => setFeedbackMessage(null), 5000);
    },
  });

  const handleQuickFeedback = (type: "accurate" | "inaccurate") => {
    const payload: FeedbackPayload = {
      impact_card_id: impactCardId,
      feedback_type: "accuracy",
      original_value: currentRiskScore,
      corrected_value: type === "accurate" ? currentRiskScore : -1, // -1 indicates inaccurate
      confidence: type === "accurate" ? 0.9 : 0.8,
    };

    feedbackMutation.mutate(payload);
  };

  const handleDetailedFeedback = () => {
    if (!feedbackType) return;

    let payload: FeedbackPayload | null = null;

    switch (feedbackType) {
      case "accuracy":
        payload = {
          impact_card_id: impactCardId,
          feedback_type: "accuracy",
          original_value: currentRiskScore,
          corrected_value: correctedRiskScore,
          confidence,
        };
        break;
      case "severity":
        payload = {
          impact_card_id: impactCardId,
          feedback_type: "severity",
          original_value: currentSeverity,
          corrected_value: correctedSeverity,
          confidence,
        };
        break;
      case "relevance":
        payload = {
          impact_card_id: impactCardId,
          feedback_type: "relevance",
          original_value: currentRelevance,
          corrected_value: correctedRelevance,
          confidence,
        };
        break;
      default:
        console.error("Invalid feedback type:", feedbackType);
        return;
    }

    if (payload) {
      feedbackMutation.mutate(payload);
    }
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-gray-900 flex items-center">
          <Star className="w-4 h-4 mr-2 text-blue-600" />
          ML Feedback
        </h4>
        <div className="text-xs text-gray-600">
          Help improve our AI accuracy
        </div>
      </div>

      {feedbackMessage && (
        <div
          className={`mb-4 p-3 rounded-lg text-sm ${
            feedbackMessage.includes("Thank you")
              ? "bg-green-100 text-green-700 border border-green-200"
              : "bg-red-100 text-red-700 border border-red-200"
          }`}
        >
          <div className="flex items-center">
            {feedbackMessage.includes("Thank you") ? (
              <ThumbsUp className="w-4 h-4 mr-2" />
            ) : (
              <AlertCircle className="w-4 h-4 mr-2" />
            )}
            {feedbackMessage}
          </div>
        </div>
      )}

      {!showFeedbackForm ? (
        <div className="space-y-3">
          <div className="text-sm text-gray-700 mb-3">
            How accurate is this impact analysis?
          </div>

          {/* Quick Feedback Buttons */}
          <div className="flex space-x-3">
            <button
              onClick={() => handleQuickFeedback("accurate")}
              disabled={feedbackMutation.isPending}
              className="flex items-center space-x-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors disabled:opacity-50"
            >
              <ThumbsUp className="w-4 h-4" />
              <span>Accurate</span>
            </button>

            <button
              onClick={() => handleQuickFeedback("inaccurate")}
              disabled={feedbackMutation.isPending}
              className="flex items-center space-x-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors disabled:opacity-50"
            >
              <ThumbsDown className="w-4 h-4" />
              <span>Needs Improvement</span>
            </button>
          </div>

          <button
            onClick={() => setShowFeedbackForm(true)}
            className="text-sm text-blue-600 hover:underline"
          >
            Provide detailed feedback →
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-sm text-gray-700 mb-3">
            What would you like to correct?
          </div>

          {/* Feedback Type Selection */}
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => setFeedbackType("accuracy")}
              className={`p-2 text-xs rounded-lg border ${
                feedbackType === "accuracy"
                  ? "bg-blue-100 border-blue-300 text-blue-700"
                  : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              Risk Score
            </button>
            <button
              onClick={() => setFeedbackType("severity")}
              className={`p-2 text-xs rounded-lg border ${
                feedbackType === "severity"
                  ? "bg-blue-100 border-blue-300 text-blue-700"
                  : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              Severity Level
            </button>
            <button
              onClick={() => setFeedbackType("relevance")}
              className={`p-2 text-xs rounded-lg border ${
                feedbackType === "relevance"
                  ? "bg-blue-100 border-blue-300 text-blue-700"
                  : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              Relevance
            </button>
          </div>

          {/* Correction Inputs */}
          {feedbackType === "accuracy" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Correct Risk Score (0-100)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={correctedRiskScore}
                onChange={(e) => {
                  const value = parseInt(e.target.value, 10);
                  if (!isNaN(value)) {
                    setCorrectedRiskScore(Math.max(0, Math.min(100, value)));
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          {feedbackType === "severity" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Correct Severity Level
              </label>
              <select
                value={correctedSeverity}
                onChange={(e) => setCorrectedSeverity(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
          )}

          {feedbackType === "relevance" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Relevance Score (0-100)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={correctedRelevance}
                onChange={(e) => {
                  const value = parseInt(e.target.value, 10);
                  if (!isNaN(value)) {
                    setCorrectedRelevance(Math.max(0, Math.min(100, value)));
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          {/* Confidence Slider */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              How confident are you in this correction? (
              {Math.round(confidence * 100)}%)
            </label>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.1"
              value={confidence}
              onChange={(e) => setConfidence(parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-3">
            <button
              onClick={handleDetailedFeedback}
              disabled={!feedbackType || feedbackMutation.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {feedbackMutation.isPending ? "Submitting..." : "Submit Feedback"}
            </button>
            <button
              onClick={() => {
                setShowFeedbackForm(false);
                setFeedbackType(null);
              }}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
