"use client";

import React, { memo, useState, useMemo } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  ChevronDown,
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  Clock,
  User,
  Target,
  ExternalLink,
  Filter,
  CheckCircle,
  X,
} from "lucide-react";
import { api } from "@/lib/api";

interface RankedAction {
  action: string;
  priority: string;
  timeline: string;
  owner: string;
  okr_goal: string;
  impact_score: number;
  effort_score: number;
  score: number;
  evidence: Array<{ title?: string; url: string }>;
  index: number;
}

interface ImpactCard {
  id: number;
  competitor_name: string;
  recommended_actions?: RankedAction[];
  next_steps_plan?: RankedAction[];
}

interface ActionRecommendationsProps {
  card: ImpactCard;
  isExpanded: boolean;
  onToggle: () => void;
}

type UserRole =
  | "product_manager"
  | "strategy"
  | "marketing"
  | "executive"
  | "all";

const ActionRecommendations = memo<ActionRecommendationsProps>(
  ({ card, isExpanded, onToggle }) => {
    const [roleFilter, setRoleFilter] = useState<UserRole>("all");
    const [priorityFilter, setPriorityFilter] = useState<string>("all");
    const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
    const [dismissedActions, setDismissedActions] = useState<Set<number>>(
      new Set()
    );

    // Normalize actions from either recommended_actions or next_steps_plan
    const normalizedActions = useMemo(() => {
      const actions = card.next_steps_plan ?? card.recommended_actions ?? [];
      return actions.map((action, idx) => ({
        ...action,
        owner: action.owner ?? "Strategy Team",
        okr_goal: action.okr_goal ?? "Drive competitive differentiation",
        impact_score: action.impact_score ?? 60,
        effort_score: action.effort_score ?? 60,
        score:
          action.score ??
          (action.impact_score ?? 60) - (action.effort_score ?? 60) / 2,
        evidence: action.evidence ?? [],
        index: action.index ?? idx,
      }));
    }, [card]);

    // Filter actions based on role and priority
    const filteredActions = useMemo(() => {
      let filtered = normalizedActions.filter(
        (action) => !dismissedActions.has(action.index)
      );

      // Filter by role
      if (roleFilter !== "all") {
        filtered = filtered.filter((action) => {
          const owner = action.owner.toLowerCase();
          switch (roleFilter) {
            case "product_manager":
              return owner.includes("product") || owner.includes("pm");
            case "strategy":
              return owner.includes("strategy") || owner.includes("strategic");
            case "marketing":
              return owner.includes("marketing") || owner.includes("brand");
            case "executive":
              return (
                owner.includes("executive") ||
                owner.includes("ceo") ||
                owner.includes("leadership")
              );
            default:
              return true;
          }
        });
      }

      // Filter by priority
      if (priorityFilter !== "all") {
        filtered = filtered.filter(
          (action) =>
            action.priority.toLowerCase() === priorityFilter.toLowerCase()
        );
      }

      // Sort by priority score (highest first)
      return filtered.sort((a, b) => b.score - a.score);
    }, [normalizedActions, roleFilter, priorityFilter, dismissedActions]);

    // Feedback mutation
    const feedbackMutation = useMutation({
      mutationFn: (payload: {
        impact_card_id: number;
        action_index: number;
        sentiment: "up" | "down";
      }) => api.post("/api/v1/feedback/impact", payload),
      onSuccess: () => {
        setFeedbackMessage("Thanks for the feedback!");
        setTimeout(() => setFeedbackMessage(null), 3000);
      },
      onError: (error: unknown) => {
        const message =
          error instanceof Error
            ? error.message
            : "Unable to record feedback right now.";
        setFeedbackMessage(message);
        setTimeout(() => setFeedbackMessage(null), 3000);
      },
    });

    const handleFeedback = (actionIndex: number, sentiment: "up" | "down") => {
      feedbackMutation.mutate({
        impact_card_id: card.id,
        action_index: actionIndex,
        sentiment,
      });
    };

    const handleDismissAction = (actionIndex: number) => {
      setDismissedActions(
        (prev) => new Set(Array.from(prev).concat(actionIndex))
      );
    };

    const getPriorityColor = (priority: string) => {
      switch (priority.toLowerCase()) {
        case "critical":
        case "high":
          return "bg-red-100 text-red-800 border-red-200";
        case "medium":
          return "bg-yellow-100 text-yellow-800 border-yellow-200";
        case "low":
          return "bg-green-100 text-green-800 border-green-200";
        default:
          return "bg-gray-100 text-gray-800 border-gray-200";
      }
    };

    const getTimelineIcon = (timeline: string) => {
      const timelineLower = timeline.toLowerCase();
      if (
        timelineLower.includes("immediate") ||
        timelineLower.includes("urgent")
      ) {
        return <Clock className="w-4 h-4 text-red-500" />;
      } else if (
        timelineLower.includes("week") ||
        timelineLower.includes("short")
      ) {
        return <Clock className="w-4 h-4 text-orange-500" />;
      } else if (
        timelineLower.includes("month") ||
        timelineLower.includes("medium")
      ) {
        return <Clock className="w-4 h-4 text-yellow-500" />;
      } else {
        return <Clock className="w-4 h-4 text-green-500" />;
      }
    };

    const getScoreColor = (score: number) => {
      if (score >= 70) return "text-green-600";
      if (score >= 40) return "text-yellow-600";
      return "text-red-600";
    };

    return (
      <div className="mb-6 border border-gray-200 rounded-lg">
        {/* Header */}
        <div
          className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={onToggle}
        >
          <div className="flex justify-between items-center">
            <h5 className="font-semibold text-gray-900 flex items-center space-x-2">
              <span>Action Recommendations</span>
              <span className="text-sm text-gray-500">
                ({filteredActions.length} actions)
              </span>
            </h5>
            <div className="flex items-center space-x-2">
              {normalizedActions.length > 0 && (
                <span className="text-sm text-blue-600">
                  {filteredActions.length} prioritized
                </span>
              )}
              {isExpanded ? (
                <ChevronUp className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              )}
            </div>
          </div>
        </div>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-100">
            {/* Filters */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mt-4 mb-4">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Filter className="w-4 h-4 text-gray-500" />
                  <label className="text-sm text-gray-700">Role:</label>
                  <select
                    value={roleFilter}
                    onChange={(e) => setRoleFilter(e.target.value as UserRole)}
                    className="text-sm border border-gray-300 rounded px-2 py-1"
                  >
                    <option value="all">All Roles</option>
                    <option value="product_manager">Product Manager</option>
                    <option value="strategy">Strategy Team</option>
                    <option value="marketing">Marketing</option>
                    <option value="executive">Executive</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <label className="text-sm text-gray-700">Priority:</label>
                  <select
                    value={priorityFilter}
                    onChange={(e) => setPriorityFilter(e.target.value)}
                    className="text-sm border border-gray-300 rounded px-2 py-1"
                  >
                    <option value="all">All Priorities</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Feedback Message */}
            {feedbackMessage && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
                {feedbackMessage}
              </div>
            )}

            {/* Actions List */}
            <div className="space-y-4">
              {filteredActions.length > 0 ? (
                filteredActions.map((action) => (
                  <div
                    key={action.index}
                    className="p-4 border border-gray-200 rounded-lg bg-white hover:shadow-sm transition-shadow"
                  >
                    {/* Action Header */}
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <h6 className="font-medium text-gray-900 mb-2">
                          {action.action}
                        </h6>

                        <div className="flex flex-wrap items-center gap-2 mb-2">
                          <span
                            className={`px-2 py-1 text-xs rounded border ${getPriorityColor(
                              action.priority
                            )}`}
                          >
                            {action.priority.toUpperCase()}
                          </span>

                          <div className="flex items-center space-x-1 text-xs text-gray-600">
                            {getTimelineIcon(action.timeline)}
                            <span>{action.timeline}</span>
                          </div>

                          <div className="flex items-center space-x-1 text-xs text-gray-600">
                            <User className="w-3 h-3" />
                            <span>{action.owner}</span>
                          </div>

                          <div className="flex items-center space-x-1 text-xs text-gray-600">
                            <Target className="w-3 h-3" />
                            <span className="truncate max-w-32">
                              {action.okr_goal}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="text-right ml-4">
                        <div
                          className={`text-lg font-bold ${getScoreColor(
                            action.score
                          )}`}
                        >
                          {action.score.toFixed(1)}
                        </div>
                        <div className="text-xs text-gray-500">
                          Priority Score
                        </div>
                        <button
                          onClick={() => handleDismissAction(action.index)}
                          className="mt-1 text-xs text-gray-400 hover:text-red-500"
                          title="Dismiss action"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    </div>

                    {/* Metrics */}
                    <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Impact Score:</span>
                        <span className="font-medium">
                          {action.impact_score}/100
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Effort Score:</span>
                        <span className="font-medium">
                          {action.effort_score}/100
                        </span>
                      </div>
                    </div>

                    {/* Evidence */}
                    {action.evidence.length > 0 && (
                      <div className="mb-3">
                        <h6 className="text-xs font-medium text-gray-700 mb-2">
                          Supporting Evidence:
                        </h6>
                        <ul className="space-y-1">
                          {action.evidence.map((item, idx) => (
                            <li key={`${item.url}-${idx}`} className="text-xs">
                              <a
                                href={item.url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-blue-600 hover:underline flex items-center space-x-1"
                              >
                                <ExternalLink className="w-3 h-3" />
                                <span className="truncate">
                                  {item.title ??
                                    (() => {
                                      try {
                                        return new URL(item.url).hostname;
                                      } catch {
                                        return item.url;
                                      }
                                    })()}
                                </span>
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={() => handleFeedback(action.index, "up")}
                          disabled={feedbackMutation.isPending}
                          className="flex items-center space-x-1 text-sm text-green-600 hover:text-green-700 disabled:opacity-50"
                        >
                          <ThumbsUp className="w-4 h-4" />
                          <span>Helpful</span>
                        </button>
                        <button
                          onClick={() => handleFeedback(action.index, "down")}
                          disabled={feedbackMutation.isPending}
                          className="flex items-center space-x-1 text-sm text-red-600 hover:text-red-700 disabled:opacity-50"
                        >
                          <ThumbsDown className="w-4 h-4" />
                          <span>Not relevant</span>
                        </button>
                      </div>

                      <button
                        className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-700"
                        onClick={() => {
                          // Mark as completed (could integrate with task management)
                          console.log(
                            "Mark action as completed:",
                            action.action
                          );
                        }}
                      >
                        <CheckCircle className="w-4 h-4" />
                        <span>Mark Complete</span>
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-gray-500">
                  <div className="text-sm">
                    {dismissedActions.size > 0
                      ? "All actions have been dismissed or filtered out."
                      : normalizedActions.length === 0
                      ? "No action recommendations available."
                      : "No actions match the current filters."}
                  </div>
                  {(roleFilter !== "all" || priorityFilter !== "all") && (
                    <button
                      onClick={() => {
                        setRoleFilter("all");
                        setPriorityFilter("all");
                      }}
                      className="text-xs text-blue-600 hover:underline mt-1"
                    >
                      Reset filters
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Dismissed Actions Recovery */}
            {dismissedActions.size > 0 && (
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">
                    {dismissedActions.size} action(s) dismissed
                  </span>
                  <button
                    onClick={() => setDismissedActions(new Set())}
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Restore all
                  </button>
                </div>
              </div>
            )}

            {/* Action Priority Guide */}
            <div className="mt-6 p-3 bg-gray-50 rounded-lg">
              <h6 className="text-xs font-semibold text-gray-900 mb-2">
                Priority Scoring Guide
              </h6>
              <div className="text-xs text-gray-600 space-y-1">
                <div>
                  • <strong>Priority Score:</strong> Impact Score - (Effort
                  Score ÷ 2)
                </div>
                <div>
                  • <strong>High Impact, Low Effort:</strong> Best ROI actions
                </div>
                <div>
                  • <strong>Timeline:</strong> Immediate → Week → Month →
                  Quarter
                </div>
                <div>
                  • <strong>Owner:</strong> Recommended team or role for
                  execution
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }
);

ActionRecommendations.displayName = "ActionRecommendations";

export default ActionRecommendations;
