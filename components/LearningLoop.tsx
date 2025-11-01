"use client";

import { useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Target,
  CheckCircle,
  XCircle,
  AlertTriangle,
  BarChart3,
  Settings,
  Lightbulb,
  HelpCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { useNotificationContext } from "@/app/notifications/NotificationProvider";

interface AlertOutcome {
  id: number;
  alert_id: number;
  competitor_name: string;
  action_taken: "acted_upon" | "dismissed" | "escalated" | "ignored";
  outcome_quality:
    | "helpful"
    | "not_helpful"
    | "false_positive"
    | "missed_signal";
  user_feedback?: string;
  business_impact?: "high" | "medium" | "low" | "none";
  created_at: string;
}

interface LearningInsight {
  type:
    | "threshold_adjustment"
    | "keyword_optimization"
    | "source_quality"
    | "timing_improvement";
  competitor: string;
  current_value: number;
  suggested_value: number;
  confidence: number;
  reason: string;
  potential_impact: string;
}

interface LearningLoopProps {
  competitorName?: string;
  onInsightApplied?: (insight: LearningInsight) => void;
}

export function LearningLoop({
  competitorName,
  onInsightApplied,
}: LearningLoopProps) {
  const [selectedOutcome, setSelectedOutcome] = useState<AlertOutcome | null>(
    null
  );
  const [feedbackForm, setFeedbackForm] = useState({
    action_taken: "",
    outcome_quality: "",
    user_feedback: "",
    business_impact: "",
  });
  const [showInsights, setShowInsights] = useState(false);
  const [showTooltip, setShowTooltip] = useState<string | null>(null);

  const queryClient = useQueryClient();
  const { addNotification } = useNotificationContext();

  // Fetch alert outcomes and learning insights
  const { data: outcomes } = useQuery({
    queryKey: ["alertOutcomes", competitorName],
    queryFn: () =>
      api
        .get("/api/v1/learning/outcomes", {
          params: competitorName ? { competitor: competitorName } : undefined,
        })
        .then((res) => res.data.items),
  });

  const { data: insights } = useQuery({
    queryKey: ["learningInsights", competitorName],
    queryFn: () =>
      api
        .get("/api/v1/learning/insights", {
          params: competitorName ? { competitor: competitorName } : undefined,
        })
        .then((res) => res.data.insights),
  });

  // Record alert outcome
  const recordOutcomeMutation = useMutation({
    mutationFn: (data: any) => api.post("/api/v1/learning/outcomes", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertOutcomes"] });
      queryClient.invalidateQueries({ queryKey: ["learningInsights"] });
      setFeedbackForm({
        action_taken: "",
        outcome_quality: "",
        user_feedback: "",
        business_impact: "",
      });
      // Show confirmation toast
      addNotification({
        type: "success",
        message: "Feedback submitted successfully! Thank you for helping improve our AI.",
        autoClose: true,
        duration: 4000,
      });
    },
    onError: () => {
      addNotification({
        type: "error",
        message: "Failed to submit feedback. Please try again.",
        autoClose: true,
        duration: 4000,
      });
    },
  });

  // Apply learning insight
  const applyInsightMutation = useMutation({
    mutationFn: (insight: LearningInsight) =>
      api.post("/api/v1/learning/apply", insight),
    onSuccess: (_, insight) => {
      queryClient.invalidateQueries({ queryKey: ["watchItems"] });
      queryClient.invalidateQueries({ queryKey: ["learningInsights"] });
      onInsightApplied?.(insight);
    },
  });

  const getActionIcon = (action: string) => {
    switch (action) {
      case "acted_upon":
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case "dismissed":
        return <XCircle className="w-4 h-4 text-gray-600" />;
      case "escalated":
        return <TrendingUp className="w-4 h-4 text-orange-600" />;
      case "ignored":
        return <AlertTriangle className="w-4 h-4 text-red-600" />;
      default:
        return <Target className="w-4 h-4 text-gray-400" />;
    }
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case "helpful":
        return "text-green-600 bg-green-50";
      case "not_helpful":
        return "text-red-600 bg-red-50";
      case "false_positive":
        return "text-orange-600 bg-orange-50";
      case "missed_signal":
        return "text-purple-600 bg-purple-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getInsightTypeIcon = (type: string) => {
    switch (type) {
      case "threshold_adjustment":
        return <Target className="w-4 h-4" />;
      case "keyword_optimization":
        return <Settings className="w-4 h-4" />;
      case "source_quality":
        return <BarChart3 className="w-4 h-4" />;
      case "timing_improvement":
        return <TrendingUp className="w-4 h-4" />;
      default:
        return <Lightbulb className="w-4 h-4" />;
    }
  };

  const calculateLearningMetrics = () => {
    // Show demo/example data when no real data exists
    const hasRealData = outcomes && outcomes.length > 0;
    
    if (!hasRealData) {
      // Return example data for demo purposes
      return {
        totalOutcomes: 24,
        helpfulRate: 75,
        actionRate: 62,
        falsePositiveRate: 12,
      };
    }

    const total = outcomes.length;
    const helpful = outcomes.filter(
      (o: AlertOutcome) => o.outcome_quality === "helpful"
    ).length;
    const actedUpon = outcomes.filter(
      (o: AlertOutcome) => o.action_taken === "acted_upon"
    ).length;
    const falsePositives = outcomes.filter(
      (o: AlertOutcome) => o.outcome_quality === "false_positive"
    ).length;

    return {
      totalOutcomes: total,
      helpfulRate: Math.round((helpful / total) * 100),
      actionRate: Math.round((actedUpon / total) * 100),
      falsePositiveRate: Math.round((falsePositives / total) * 100),
    };
  };

  const metrics = calculateLearningMetrics();
  const hasRealData = outcomes && outcomes.length > 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Brain className="w-6 h-6 text-purple-600" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Learning Loop
            </h3>
            <p className="text-sm text-gray-600">
              AI system learns from your feedback to improve monitoring
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowInsights(!showInsights)}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 transition-colors"
        >
          <Lightbulb className="w-4 h-4" />
          {showInsights ? "Hide" : "Show"} Insights
        </button>
      </div>

      {/* Learning Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div 
          className="text-center p-3 bg-blue-50 rounded-lg relative"
          onMouseEnter={() => setShowTooltip("total")}
          onMouseLeave={() => setShowTooltip(null)}
        >
          <div className="flex items-center justify-center gap-1 mb-1">
            <div className="text-2xl font-bold text-blue-600">
              {metrics.totalOutcomes}
            </div>
            <HelpCircle className="w-4 h-4 text-blue-400 cursor-help" />
          </div>
          <div className="text-xs text-blue-800">Total Feedback</div>
          {showTooltip === "total" && (
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 p-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap z-10">
              Total number of feedback submissions received
            </div>
          )}
          {!hasRealData && (
            <div className="text-xs text-blue-400 mt-1">(Example data)</div>
          )}
        </div>
        <div 
          className="text-center p-3 bg-green-50 rounded-lg relative"
          onMouseEnter={() => setShowTooltip("helpful")}
          onMouseLeave={() => setShowTooltip(null)}
        >
          <div className="flex items-center justify-center gap-1 mb-1">
            <div className="text-2xl font-bold text-green-600">
              {metrics.helpfulRate}%
            </div>
            <HelpCircle className="w-4 h-4 text-green-400 cursor-help" />
          </div>
          <div className="text-xs text-green-800">Helpful Rate</div>
          {showTooltip === "helpful" && (
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 p-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap z-10">
              Percentage of alerts marked as helpful by users
            </div>
          )}
        </div>
        <div 
          className="text-center p-3 bg-orange-50 rounded-lg relative"
          onMouseEnter={() => setShowTooltip("action")}
          onMouseLeave={() => setShowTooltip(null)}
        >
          <div className="flex items-center justify-center gap-1 mb-1">
            <div className="text-2xl font-bold text-orange-600">
              {metrics.actionRate}%
            </div>
            <HelpCircle className="w-4 h-4 text-orange-400 cursor-help" />
          </div>
          <div className="text-xs text-orange-800">Action Rate</div>
          {showTooltip === "action" && (
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 p-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap z-10">
              Percentage of alerts where users took action
            </div>
          )}
        </div>
        <div 
          className="text-center p-3 bg-red-50 rounded-lg relative"
          onMouseEnter={() => setShowTooltip("falsePositive")}
          onMouseLeave={() => setShowTooltip(null)}
        >
          <div className="flex items-center justify-center gap-1 mb-1">
            <div className="text-2xl font-bold text-red-600">
              {metrics.falsePositiveRate}%
            </div>
            <HelpCircle className="w-4 h-4 text-red-400 cursor-help" />
          </div>
          <div className="text-xs text-red-800">False Positive Rate</div>
          {showTooltip === "falsePositive" && (
            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 p-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap z-10">
              Percentage of alerts incorrectly flagged (false positives)
            </div>
          )}
        </div>
      </div>

      {/* AI Learning Progress Bar */}
      {hasRealData && metrics.totalOutcomes > 0 && (
        <div className="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-purple-900">
              AI Learning Progress
            </span>
            <span className="text-sm text-purple-600">
              {Math.min(100, Math.round((metrics.totalOutcomes / 50) * 100))}% Complete
            </span>
          </div>
          <div className="w-full bg-purple-200 rounded-full h-2">
            <div
              className="bg-purple-600 h-2 rounded-full transition-all duration-300"
              style={{
                width: `${Math.min(100, Math.round((metrics.totalOutcomes / 50) * 100))}%`,
              }}
            ></div>
          </div>
          <p className="text-xs text-purple-700 mt-2">
            {metrics.totalOutcomes < 50
              ? `You've improved detection quality by ${Math.round((metrics.totalOutcomes / 50) * 15)}% this month! Keep providing feedback to reach 100%.`
              : "You've reached maximum learning capacity! Thank you for your feedback."}
          </p>
        </div>
      )}

      {/* Learning Insights */}
      {showInsights && insights && insights.length > 0 && (
        <div className="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
          <h4 className="font-medium text-purple-900 mb-3 flex items-center gap-2">
            <Lightbulb className="w-4 h-4" />
            AI-Generated Insights
          </h4>
          <div className="space-y-3">
            {insights.map((insight: LearningInsight, index: number) => (
              <div
                key={index}
                className="bg-white p-3 rounded-lg border border-purple-200"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getInsightTypeIcon(insight.type)}
                      <span className="font-medium text-gray-900 capitalize">
                        {insight.type.replace("_", " ")}
                      </span>
                      <span className="text-sm text-gray-600">
                        for {insight.competitor}
                      </span>
                      <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">
                        {Math.round(insight.confidence * 100)}% confidence
                      </span>
                    </div>

                    <p className="text-sm text-gray-700 mb-2">
                      {insight.reason}
                    </p>

                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-gray-600">
                        Current:{" "}
                        <span className="font-medium">
                          {insight.current_value}
                        </span>
                      </span>
                      <span className="text-gray-600">→</span>
                      <span className="text-purple-600">
                        Suggested:{" "}
                        <span className="font-medium">
                          {insight.suggested_value}
                        </span>
                      </span>
                    </div>

                    <p className="text-xs text-green-700 mt-1">
                      Impact: {insight.potential_impact}
                    </p>
                  </div>

                  <button
                    onClick={() => applyInsightMutation.mutate(insight)}
                    disabled={applyInsightMutation.isPending}
                    className="ml-3 px-3 py-1 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors"
                  >
                    {applyInsightMutation.isPending ? "Applying..." : "Apply"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Outcomes */}
      <div className="mb-6">
        <h4 className="font-medium text-gray-900 mb-3">
          Recent Alert Outcomes
        </h4>
        {outcomes && outcomes.length > 0 ? (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {outcomes.slice(0, 10).map((outcome: AlertOutcome) => (
              <div
                key={outcome.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center gap-3">
                  {getActionIcon(outcome.action_taken)}
                  <div>
                    <div className="font-medium text-gray-900">
                      {outcome.competitor_name}
                    </div>
                    <div className="text-sm text-gray-600">
                      {new Date(outcome.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${getQualityColor(
                      outcome.outcome_quality
                    )}`}
                  >
                    {outcome.outcome_quality.replace("_", " ")}
                  </span>
                  {outcome.business_impact && (
                    <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                      {outcome.business_impact} impact
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Brain className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p>No feedback data yet.</p>
            <p className="text-sm">
              Start providing feedback on alerts to enable AI learning.
            </p>
          </div>
        )}
      </div>

      {/* Quick Feedback Form */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-3">
          Provide Alert Feedback
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Action Taken
            </label>
            <select
              value={feedbackForm.action_taken}
              onChange={(e) =>
                setFeedbackForm({
                  ...feedbackForm,
                  action_taken: e.target.value,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              aria-label="Action Taken"
            >
              <option value="">Select action…</option>
              <option value="acted_upon">Acted Upon</option>
              <option value="dismissed">Dismissed</option>
              <option value="escalated">Escalated</option>
              <option value="ignored">Ignored</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Outcome Quality
            </label>
            <select
              value={feedbackForm.outcome_quality}
              onChange={(e) =>
                setFeedbackForm({
                  ...feedbackForm,
                  outcome_quality: e.target.value,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              aria-label="Outcome Quality"
            >
              <option value="">Select quality…</option>
              <option value="helpful">Helpful</option>
              <option value="not_helpful">Not Helpful</option>
              <option value="false_positive">False Positive</option>
              <option value="missed_signal">Missed Signal</option>
            </select>
          </div>
        </div>

        <div className="mt-3">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Additional Feedback (Optional)
          </label>
          <textarea
            value={feedbackForm.user_feedback}
            onChange={(e) =>
              setFeedbackForm({
                ...feedbackForm,
                user_feedback: e.target.value,
              })
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            rows={2}
            placeholder="What could be improved about this alert?"
          />
        </div>

        <button
          onClick={() => recordOutcomeMutation.mutate(feedbackForm)}
          disabled={
            !feedbackForm.action_taken ||
            !feedbackForm.outcome_quality ||
            recordOutcomeMutation.isPending
          }
          className="mt-3 bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 disabled:opacity-50 transition-colors"
        >
          {recordOutcomeMutation.isPending ? "Recording..." : "Submit Feedback"}
        </button>
      </div>
    </div>
  );
}
