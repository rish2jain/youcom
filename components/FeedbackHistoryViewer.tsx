"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  History,
  Filter,
  ThumbsUp,
  ThumbsDown,
  Star,
  Calendar,
} from "lucide-react";
import { api } from "@/lib/api";

interface FeedbackRecord {
  id: number;
  user_id: string;
  impact_card_id: number;
  competitor_name: string;
  feedback_type: "accuracy" | "relevance" | "severity";
  original_value: number | string;
  corrected_value: number | string;
  confidence: number;
  feedback_timestamp: string;
  processed: boolean;
}

export function FeedbackHistoryViewer() {
  const [filterType, setFilterType] = useState<string>("all");
  const [filterProcessed, setFilterProcessed] = useState<string>("all");

  const { data: feedbackHistory, isLoading } = useQuery({
    queryKey: ["feedbackHistory", filterType, filterProcessed],
    queryFn: () => {
      const params: any = {};
      if (filterType !== "all") params.feedback_type = filterType;
      if (filterProcessed !== "all")
        params.processed = filterProcessed === "processed";

      return api
        .get("/api/v1/ml_feedback/history", { params })
        .then((res) => res.data.items);
    },
    staleTime: 30000,
  });

  const getFeedbackTypeIcon = (type: string) => {
    switch (type) {
      case "accuracy":
        return <Star className="w-4 h-4 text-blue-600" />;
      case "relevance":
        return <ThumbsUp className="w-4 h-4 text-green-600" />;
      case "severity":
        return <ThumbsDown className="w-4 h-4 text-orange-600" />;
      default:
        return <History className="w-4 h-4 text-gray-600" />;
    }
  };

  const getFeedbackTypeColor = (type: string) => {
    switch (type) {
      case "accuracy":
        return "bg-blue-100 text-blue-700";
      case "relevance":
        return "bg-green-100 text-green-700";
      case "severity":
        return "bg-orange-100 text-orange-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const formatValue = (value: number | string, type: string) => {
    if (type === "severity") return String(value).toUpperCase();
    if (typeof value === "number")
      return `${value}${
        type === "accuracy" || type === "relevance" ? "/100" : ""
      }`;
    return String(value);
  };

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <History className="w-5 h-5 mr-2 text-blue-600" />
          Feedback History
        </h3>
        <div className="text-sm text-gray-600">
          {feedbackHistory?.length || 0} feedback records
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">Filters:</span>
        </div>

        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Types</option>
          <option value="accuracy">Accuracy</option>
          <option value="relevance">Relevance</option>
          <option value="severity">Severity</option>
        </select>

        <select
          value={filterProcessed}
          onChange={(e) => setFilterProcessed(e.target.value)}
          className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Status</option>
          <option value="processed">Processed</option>
          <option value="pending">Pending</option>
        </select>
      </div>

      {/* Feedback List */}
      {feedbackHistory && feedbackHistory.length > 0 ? (
        <div className="space-y-3">
          {feedbackHistory.map((feedback: FeedbackRecord) => (
            <div
              key={feedback.id}
              className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  {getFeedbackTypeIcon(feedback.feedback_type)}
                  <div>
                    <div className="font-medium text-gray-900">
                      {feedback.competitor_name}
                    </div>
                    <div className="text-sm text-gray-600">
                      Impact Card #{feedback.impact_card_id}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${getFeedbackTypeColor(
                      feedback.feedback_type
                    )}`}
                  >
                    {feedback.feedback_type.toUpperCase()}
                  </span>
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      feedback.processed
                        ? "bg-green-100 text-green-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}
                  >
                    {feedback.processed ? "PROCESSED" : "PENDING"}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                <div className="text-sm">
                  <span className="font-medium text-gray-700">Original:</span>
                  <div className="text-gray-600">
                    {formatValue(
                      feedback.original_value,
                      feedback.feedback_type
                    )}
                  </div>
                </div>
                <div className="text-sm">
                  <span className="font-medium text-gray-700">Corrected:</span>
                  <div className="text-gray-600">
                    {formatValue(
                      feedback.corrected_value,
                      feedback.feedback_type
                    )}
                  </div>
                </div>
                <div className="text-sm">
                  <span className="font-medium text-gray-700">Confidence:</span>
                  <div className="text-gray-600">
                    {Math.round(feedback.confidence * 100)}%
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center space-x-1">
                  <Calendar className="w-3 h-3" />
                  <span>
                    {new Date(feedback.feedback_timestamp).toLocaleString()}
                  </span>
                </div>
                <div>User: {feedback.user_id.substring(0, 8)}...</div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <History className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg mb-2">No feedback history found</p>
          <p className="text-sm">
            {filterType !== "all" || filterProcessed !== "all"
              ? "Try adjusting your filters to see more results."
              : "Feedback will appear here as users provide corrections to ML predictions."}
          </p>
        </div>
      )}
    </div>
  );
}
