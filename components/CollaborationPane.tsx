"use client";

import React, { memo, useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ChevronDown,
  ChevronUp,
  MessageCircle,
  Users,
  Bell,
  Zap,
  TrendingUp,
  Eye,
  Clock,
} from "lucide-react";
import { api } from "@/lib/api";
import { MLFeedbackPanel } from "./MLFeedbackPanel";

interface ImpactCard {
  id: number;
  competitor_name: string;
  risk_score: number;
  risk_level: string;
  confidence_score: number;
  impact_areas: Array<{
    area: string;
    impact_score: number;
    description: string;
  }>;
  key_insights: string[];
  explainability?: Explainability;
}

interface Explainability {
  reasoning?: string;
  impact_areas?: ImpactCard["impact_areas"];
  key_insights?: string[];
  source_summary?: Record<string, any>;
}

interface CollaborationPaneProps {
  card: ImpactCard;
  isExpanded: boolean;
  onToggle: () => void;
}

interface NotificationLog {
  id: string;
  competitor_name: string;
  channel: string;
  message: string;
  created_at: string;
}

const CollaborationPane = memo<CollaborationPaneProps>(
  ({ card, isExpanded, onToggle }) => {
    const [showExplainability, setShowExplainability] = useState(false);
    const [activeUsers, setActiveUsers] = useState<string[]>([
      "Alice (PM)",
      "Bob (Strategy)",
    ]);
    const [newComment, setNewComment] = useState("");
    const [comments, setComments] = useState([
      {
        id: "1",
        user: "Alice (PM)",
        message:
          "This looks significant - we should prioritize the product response.",
        timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
        type: "comment" as const,
      },
      {
        id: "2",
        user: "Bob (Strategy)",
        message: "Agreed. I'll coordinate with the competitive analysis team.",
        timestamp: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
        type: "comment" as const,
      },
    ]);

    // Fetch notification logs
    const { data: notificationLogs } = useQuery({
      queryKey: ["notificationLogs"],
      queryFn: () =>
        api.get("/api/v1/notifications/logs").then((res) => res.data.items),
      staleTime: 60_000,
    });

    // Simulate real-time user presence
    useEffect(() => {
      const interval = setInterval(() => {
        const users = [
          "Alice (PM)",
          "Bob (Strategy)",
          "Carol (Marketing)",
          "Dave (Executive)",
        ];
        const activeCount = Math.floor(Math.random() * 3) + 1;
        const shuffled = users.sort(() => 0.5 - Math.random());
        setActiveUsers(shuffled.slice(0, activeCount));
      }, 30000); // Update every 30 seconds

      return () => clearInterval(interval);
    }, []);

    const handleAddComment = () => {
      if (!newComment.trim()) return;

      const comment = {
        id: Date.now().toString(),
        user: "You",
        message: newComment.trim(),
        timestamp: new Date().toISOString(),
        type: "comment" as const,
      };

      setComments((prev) => [...prev, comment]);
      setNewComment("");
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleAddComment();
      }
    };

    const formatTimestamp = (timestamp: string) => {
      try {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / (1000 * 60));

        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
        return date.toLocaleDateString();
      } catch {
        return "Unknown time";
      }
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
              <span>Collaboration & Insights</span>
              <div className="flex items-center space-x-1">
                <Users className="w-4 h-4 text-green-500" />
                <span className="text-sm text-green-600">
                  {activeUsers.length}
                </span>
              </div>
            </h5>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">
                {comments.length} comments
              </span>
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
            {/* Active Users */}
            <div className="mt-4 mb-4 p-3 bg-green-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h6 className="text-sm font-medium text-gray-900 flex items-center space-x-2">
                  <Users className="w-4 h-4 text-green-500" />
                  <span>Active Users</span>
                </h6>
                <div className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-green-600">Live</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {activeUsers.map((user, index) => (
                  <div
                    key={user}
                    className="flex items-center space-x-2 bg-white px-2 py-1 rounded-full border border-green-200"
                  >
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-xs text-gray-700">{user}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Comments Section */}
            <div className="mb-6">
              <h6 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
                <MessageCircle className="w-4 h-4" />
                <span>Team Discussion</span>
              </h6>

              {/* Comments List */}
              <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
                {comments.map((comment) => (
                  <div key={comment.id} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-sm font-medium text-gray-900">
                        {comment.user}
                      </span>
                      <div className="flex items-center space-x-1 text-xs text-gray-500">
                        <Clock className="w-3 h-3" />
                        <span>{formatTimestamp(comment.timestamp)}</span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700">{comment.message}</p>
                  </div>
                ))}
              </div>

              {/* Add Comment */}
              <div className="flex space-x-2">
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Add a comment... (Press Enter to send)"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={2}
                />
                <button
                  onClick={handleAddComment}
                  disabled={!newComment.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  Send
                </button>
              </div>
            </div>

            {/* Notifications */}
            <div className="mb-6">
              <h6 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
                <Bell className="w-4 h-4" />
                <span>Recent Notifications</span>
              </h6>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {(notificationLogs ?? [])
                  .slice(0, 5)
                  .map((log: NotificationLog) => (
                    <div
                      key={log.id}
                      className="p-3 border border-gray-200 rounded-lg bg-white"
                    >
                      <div className="flex justify-between items-start mb-1">
                        <span className="font-medium text-gray-800 text-sm">
                          {log.competitor_name}
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                            {log.channel}
                          </span>
                          <span className="text-xs text-gray-500">
                            {log.created_at
                              ? formatTimestamp(log.created_at)
                              : ""}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">{log.message}</p>
                    </div>
                  ))}
                {(!notificationLogs || notificationLogs.length === 0) && (
                  <div className="text-center py-4 text-gray-500 text-sm">
                    No recent notifications
                  </div>
                )}
              </div>
            </div>

            {/* ML Feedback Panel */}
            <div className="mb-6">
              <MLFeedbackPanel
                impactCardId={card.id}
                currentRiskScore={card.risk_score}
                currentSeverity={card.risk_level}
                currentCategory={card.impact_areas[0]?.area || "general"}
                currentRelevance={Math.round(card.confidence_score)}
              />
            </div>

            {/* Key Insights */}
            {card.key_insights.length > 0 && (
              <div className="mb-6">
                <h6 className="font-medium text-gray-900 mb-3 flex items-center space-x-2">
                  <TrendingUp className="w-4 h-4" />
                  <span>Key Insights</span>
                </h6>
                <ul className="space-y-2">
                  {card.key_insights.map((insight, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <TrendingUp className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-700">{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Explainability Deep Dive */}
            <div className="mb-4">
              <button
                onClick={() => setShowExplainability(!showExplainability)}
                className="flex items-center space-x-2 text-sm text-blue-600 hover:underline"
              >
                <Zap className="w-4 h-4" />
                <span>
                  {showExplainability ? "Hide" : "Show"} AI Explainability Deep
                  Dive
                </span>
              </button>

              {showExplainability && card.explainability && (
                <div className="mt-3 p-4 bg-gray-50 rounded-lg text-sm text-gray-700 space-y-3">
                  {card.explainability.reasoning && (
                    <div>
                      <h6 className="font-medium text-gray-900 mb-1">
                        Model Reasoning:
                      </h6>
                      <p>{card.explainability.reasoning}</p>
                    </div>
                  )}

                  {card.explainability.impact_areas && (
                    <div>
                      <h6 className="font-medium text-gray-900 mb-2">
                        Impact Drivers:
                      </h6>
                      <ul className="list-disc list-inside space-y-1">
                        {card.explainability.impact_areas.map((area, idx) => (
                          <li key={idx}>
                            <strong>{area.area}:</strong> {area.description}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {card.explainability.source_summary && (
                    <div>
                      <h6 className="font-medium text-gray-900 mb-1">
                        Source Analysis:
                      </h6>
                      <p>
                        Analysis based on{" "}
                        {Object.keys(card.explainability.source_summary).length}{" "}
                        source types with comprehensive cross-referencing and
                        credibility scoring.
                      </p>
                    </div>
                  )}

                  <div className="pt-2 border-t border-gray-200">
                    <p className="text-xs text-gray-600">
                      <strong>Confidence Factors:</strong> Source credibility,
                      cross-validation, temporal relevance, and domain expertise
                      alignment.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Collaboration Actions */}
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => {
                  // TODO: Implement watch functionality
                  console.log("Watch for updates clicked");
                }}
                className="flex items-center space-x-1 px-3 py-1 bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100 text-sm"
              >
                <Eye className="w-3 h-3" />
                <span>Watch for Updates</span>
              </button>
              <button
                onClick={() => {
                  // TODO: Implement alert functionality
                  console.log("Set alert clicked");
                }}
                className="flex items-center space-x-1 px-3 py-1 bg-green-50 text-green-700 rounded-md hover:bg-green-100 text-sm"
              >
                <Bell className="w-3 h-3" />
                <span>Set Alert</span>
              </button>
              <button
                onClick={() => {
                  // TODO: Implement share functionality
                  console.log("Share with team clicked");
                }}
                className="flex items-center space-x-1 px-3 py-1 bg-purple-50 text-purple-700 rounded-md hover:bg-purple-100 text-sm"
              >
                <Users className="w-3 h-3" />
                <span>Share with Team</span>
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }
);

CollaborationPane.displayName = "CollaborationPane";

export default CollaborationPane;
