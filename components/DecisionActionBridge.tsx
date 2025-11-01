"use client";

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Users,
  Target,
  TrendingUp,
  Calendar,
  ArrowRight,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";

interface RankedAction {
  action: string;
  priority: "critical" | "high" | "medium" | "low";
  timeline: string;
  owner: string;
  okr_goal: string;
  impact_score: number;
  effort_score: number;
  score: number;
  evidence: Array<{ title?: string; url: string }>;
  index: number;
}

interface DecisionActionBridgeProps {
  riskScore: number;
  riskLevel: string;
  competitorName: string;
  actions?: RankedAction[];
  onActionFeedback?: (actionIndex: number, sentiment: "up" | "down") => void;
  onActionTaken?: (
    actionIndex: number,
    status: "started" | "completed" | "dismissed"
  ) => void;
}

export function DecisionActionBridge({
  riskScore,
  riskLevel,
  competitorName,
  actions = [],
  onActionFeedback,
  onActionTaken,
}: DecisionActionBridgeProps) {
  const [expandedActions, setExpandedActions] = useState<Set<number>>(
    new Set()
  );
  const [actionStatuses, setActionStatuses] = useState<Record<number, string>>(
    {}
  );

  // Generate default actions based on risk level if none provided
  const defaultActions = generateDefaultActions(
    riskScore,
    riskLevel,
    competitorName
  );
  const displayActions = actions.length > 0 ? actions : defaultActions;

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical":
        return "bg-red-100 text-red-800 border-red-200";
      case "high":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case "critical":
        return <AlertTriangle className="w-4 h-4" />;
      case "high":
        return <TrendingUp className="w-4 h-4" />;
      case "medium":
        return <Clock className="w-4 h-4" />;
      case "low":
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <Target className="w-4 h-4" />;
    }
  };

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedActions);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedActions(newExpanded);
  };

  const handleActionStatus = (actionIndex: number, status: string) => {
    setActionStatuses((prev) => ({ ...prev, [actionIndex]: status }));
    onActionTaken?.(actionIndex, status as any);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Recommended Actions
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Strategic responses to {competitorName}'s {riskLevel} risk (Score:{" "}
            {riskScore}/100)
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-blue-600">
            {displayActions.length}
          </div>
          <div className="text-xs text-gray-500">Actions</div>
        </div>
      </div>

      {/* Risk Context */}
      <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
        <div className="flex items-center gap-3 mb-2">
          <AlertTriangle className="w-5 h-5 text-blue-600" />
          <span className="font-medium text-blue-900">Strategic Context</span>
        </div>
        <p className="text-sm text-blue-800">
          {getRiskContextMessage(riskScore, riskLevel, competitorName)}
        </p>
      </div>

      {/* Actions List */}
      <div className="space-y-4">
        {displayActions.map((action, index) => (
          <div
            key={action.index || index}
            className={`border rounded-lg transition-all ${
              expandedActions.has(action.index || index)
                ? "border-blue-200 bg-blue-50"
                : "border-gray-200 hover:border-gray-300"
            }`}
          >
            {/* Action Header */}
            <div className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span
                      className={`px-2 py-1 text-xs rounded-full border ${getPriorityColor(
                        action.priority
                      )}`}
                    >
                      {getPriorityIcon(action.priority)}
                      <span className="ml-1 font-medium">
                        {action.priority.toUpperCase()}
                      </span>
                    </span>
                    <span className="text-sm text-gray-600">
                      {action.timeline}
                    </span>
                  </div>

                  <h4 className="font-medium text-gray-900 mb-2">
                    {action.action}
                  </h4>

                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      <span>{action.owner}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Target className="w-4 h-4" />
                      <span>{action.okr_goal}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 ml-4">
                  <div className="text-right text-sm">
                    <div className="font-semibold text-blue-600">
                      Score: {action.score.toFixed(1)}
                    </div>
                    <div className="text-xs text-gray-500">
                      Impact: {action.impact_score} | Effort:{" "}
                      {action.effort_score}
                    </div>
                  </div>

                  <button
                    onClick={() => toggleExpanded(action.index || index)}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
                  >
                    <ArrowRight
                      className={`w-4 h-4 transition-transform ${
                        expandedActions.has(action.index || index)
                          ? "rotate-90"
                          : ""
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Quick Action Buttons */}
              <div className="flex items-center gap-2 mt-3">
                <button
                  onClick={() =>
                    handleActionStatus(action.index || index, "started")
                  }
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    actionStatuses[action.index || index] === "started"
                      ? "bg-blue-600 text-white"
                      : "bg-blue-100 text-blue-700 hover:bg-blue-200"
                  }`}
                >
                  {actionStatuses[action.index || index] === "started"
                    ? "✓ Started"
                    : "Start Action"}
                </button>

                <button
                  onClick={() =>
                    handleActionStatus(action.index || index, "dismissed")
                  }
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    actionStatuses[action.index || index] === "dismissed"
                      ? "bg-gray-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {actionStatuses[action.index || index] === "dismissed"
                    ? "✓ Dismissed"
                    : "Not Relevant"}
                </button>

                {/* Feedback Buttons */}
                <div className="flex items-center gap-1 ml-auto">
                  <button
                    onClick={() =>
                      onActionFeedback?.(action.index || index, "up")
                    }
                    className="p-1 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                    title="Helpful recommendation"
                  >
                    <ThumbsUp className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() =>
                      onActionFeedback?.(action.index || index, "down")
                    }
                    className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Not helpful"
                  >
                    <ThumbsDown className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedActions.has(action.index || index) && (
              <div className="border-t border-blue-200 bg-white p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Impact Analysis */}
                  <div>
                    <h5 className="font-medium text-gray-900 mb-2">
                      Impact Analysis
                    </h5>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Business Impact:</span>
                        <span className="font-medium">
                          {action.impact_score}/100
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-500 h-2 rounded-full"
                          style={{ width: `${action.impact_score}%` }}
                        ></div>
                      </div>

                      <div className="flex justify-between text-sm">
                        <span>Implementation Effort:</span>
                        <span className="font-medium">
                          {action.effort_score}/100
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-orange-500 h-2 rounded-full"
                          style={{ width: `${action.effort_score}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>

                  {/* Supporting Evidence */}
                  <div>
                    <h5 className="font-medium text-gray-900 mb-2">
                      Supporting Evidence
                    </h5>
                    {action.evidence.length > 0 ? (
                      <ul className="space-y-1 text-sm">
                        {action.evidence.slice(0, 3).map((item, idx) => (
                          <li key={idx}>
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline flex items-center gap-1"
                            >
                              <span className="truncate">
                                {item.title || item.url}
                              </span>
                              <ArrowRight className="w-3 h-3 flex-shrink-0" />
                            </a>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-gray-500">
                        Based on competitive intelligence analysis and industry
                        best practices.
                      </p>
                    )}
                  </div>
                </div>

                {/* Timeline Breakdown */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h5 className="font-medium text-gray-900 mb-2">
                    Implementation Timeline
                  </h5>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Calendar className="w-4 h-4" />
                    <span>
                      {getTimelineBreakdown(action.timeline, action.priority)}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium text-gray-900">Next Steps Summary</h4>
            <p className="text-sm text-gray-600 mt-1">
              {
                displayActions.filter(
                  (a) => a.priority === "critical" || a.priority === "high"
                ).length
              }{" "}
              high-priority actions require immediate attention
            </p>
          </div>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
            Export Action Plan
          </button>
        </div>
      </div>
    </div>
  );
}

// Helper functions
function generateDefaultActions(
  riskScore: number,
  riskLevel: string,
  competitorName: string
): RankedAction[] {
  const baseActions: Partial<RankedAction>[] = [];

  if (riskScore >= 80) {
    baseActions.push(
      {
        action: `Accelerate competitive response to ${competitorName}'s market position`,
        priority: "critical",
        timeline: "This week",
        owner: "Product & Strategy Teams",
        okr_goal: "Maintain competitive differentiation",
        impact_score: 90,
        effort_score: 70,
      },
      {
        action: `Brief executive team on ${competitorName} threat assessment`,
        priority: "critical",
        timeline: "Next 2 days",
        owner: "Strategy Team",
        okr_goal: "Executive alignment on competitive strategy",
        impact_score: 85,
        effort_score: 30,
      }
    );
  }

  if (riskScore >= 60) {
    baseActions.push(
      {
        action: `Monitor ${competitorName} pricing and feature announcements`,
        priority: "high",
        timeline: "Ongoing",
        owner: "Competitive Intelligence Team",
        okr_goal: "Early threat detection",
        impact_score: 75,
        effort_score: 40,
      },
      {
        action: `Analyze ${competitorName}'s customer acquisition strategy`,
        priority: "high",
        timeline: "Next 2 weeks",
        owner: "Marketing Team",
        okr_goal: "Improve customer acquisition efficiency",
        impact_score: 70,
        effort_score: 50,
      }
    );
  }

  baseActions.push({
    action: `Update competitive positioning against ${competitorName}`,
    priority: "medium",
    timeline: "Next month",
    owner: "Product Marketing",
    okr_goal: "Strengthen market positioning",
    impact_score: 60,
    effort_score: 45,
  });

  return baseActions.map((action, index) => ({
    action: action.action!,
    priority: action.priority as any,
    timeline: action.timeline!,
    owner: action.owner!,
    okr_goal: action.okr_goal!,
    impact_score: action.impact_score!,
    effort_score: action.effort_score!,
    score: action.impact_score! - action.effort_score! / 2,
    evidence: [],
    index,
  }));
}

function getRiskContextMessage(
  riskScore: number,
  riskLevel: string,
  competitorName: string
): string {
  if (riskScore >= 80) {
    return `${competitorName} poses a critical competitive threat requiring immediate strategic response. High-impact actions should be prioritized to maintain market position.`;
  } else if (riskScore >= 60) {
    return `${competitorName} represents a significant competitive challenge. Proactive measures recommended to address potential market impact.`;
  } else if (riskScore >= 40) {
    return `${competitorName} shows moderate competitive activity. Monitor closely and prepare defensive strategies as needed.`;
  } else {
    return `${competitorName} currently poses low competitive risk. Continue standard monitoring and maintain awareness of market changes.`;
  }
}

function getTimelineBreakdown(timeline: string, priority: string): string {
  const urgencyMap: Record<string, string> = {
    "This week": "7 days - Immediate action required",
    "Next 2 days": "48 hours - Urgent response needed",
    "Next 2 weeks": "14 days - Plan and execute",
    "Next month": "30 days - Strategic planning phase",
    Ongoing: "Continuous monitoring and adjustment",
  };

  return urgencyMap[timeline] || timeline;
}
