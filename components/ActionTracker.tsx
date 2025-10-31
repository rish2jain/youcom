import React from "react";
import { useState, useEffect } from "react";
import {
  PlusIcon,
  FunnelIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationCircleIcon,
  PlayIcon,
} from "@heroicons/react/24/outline";

interface Action {
  id: number;
  title: string;
  description: string;
  priority: "Low" | "Medium" | "High" | "Critical";
  status: "Pending" | "In Progress" | "Completed" | "Blocked";
  assignee: string;
  dueDate: string;
  source: string;
  tags: string[];
}

interface ActionTrackerProps {
  onGenerateActions: () => Promise<void>;
  onAddCustomAction: () => void;
}

const ActionTracker: React.FC<ActionTrackerProps> = ({
  onGenerateActions,
  onAddCustomAction,
}) => {
  const [statusFilter, setStatusFilter] = useState("All Status");
  const [priorityFilter, setPriorityFilter] = useState("All Priority");
  const [loading, setLoading] = useState(false);

  // Actions will be loaded from API - no more static sample data
  const [actions, setActions] = useState<Action[]>([]);

  const statusOptions = [
    "All Status",
    "Pending",
    "In Progress",
    "Completed",
    "Blocked",
  ];
  const priorityOptions = ["All Priority", "Low", "Medium", "High", "Critical"];

  // Load actions from API
  useEffect(() => {
    const loadActions = async () => {
      try {
        const response = await fetch("/api/v1/actions");
        if (response.ok) {
          const data = await response.json();
          setActions(data);
        }
      } catch (error) {
        console.warn("Failed to load actions:", error);
        // Keep empty array - no fallback to mock data
      }
    };

    loadActions();
  }, []);

  const getFilteredActions = () => {
    return actions.filter((action) => {
      const statusMatch =
        statusFilter === "All Status" || action.status === statusFilter;
      const priorityMatch =
        priorityFilter === "All Priority" || action.priority === priorityFilter;
      return statusMatch && priorityMatch;
    });
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "Critical":
        return "bg-red-100 text-red-700 border-red-200";
      case "High":
        return "bg-orange-100 text-orange-700 border-orange-200";
      case "Medium":
        return "bg-yellow-100 text-yellow-700 border-yellow-200";
      case "Low":
        return "bg-green-100 text-green-700 border-green-200";
      default:
        return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "Completed":
        return <CheckCircleIcon className="w-4 h-4 text-green-600" />;
      case "In Progress":
        return <PlayIcon className="w-4 h-4 text-blue-600" />;
      case "Blocked":
        return <ExclamationCircleIcon className="w-4 h-4 text-red-600" />;
      case "Pending":
        return <ClockIcon className="w-4 h-4 text-gray-600" />;
      default:
        return <ClockIcon className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Completed":
        return "text-green-700 bg-green-50";
      case "In Progress":
        return "text-blue-700 bg-blue-50";
      case "Blocked":
        return "text-red-700 bg-red-50";
      case "Pending":
        return "text-gray-700 bg-gray-50";
      default:
        return "text-gray-700 bg-gray-50";
    }
  };

  const handleGenerateActions = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/v1/actions/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          insights: "Recent competitive intelligence analysis",
          competitors: ["OpenAI", "Anthropic", "Google AI"],
        }),
      });

      if (response.ok) {
        const data = await response.json();
        // Add generated actions to current list
        setActions((prev) => [...prev, ...data.actions]);
        await onGenerateActions(); // Call parent callback for success message
      } else {
        throw new Error("Failed to generate actions");
      }
    } catch (error) {
      console.error("Failed to generate actions:", error);
    } finally {
      setLoading(false);
    }
  };

  const isFilterActive =
    statusFilter !== "All Status" || priorityFilter !== "All Priority";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Action Tracker
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Track and manage actions generated from competitive intelligence
            insights
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleGenerateActions}
            disabled={loading}
            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Generating...</span>
              </>
            ) : (
              <>
                <PlayIcon className="w-4 h-4" />
                <span>Generate Actions from Insights</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <FunnelIcon className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Filters:</span>
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={`px-3 py-1.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            statusFilter !== "All Status"
              ? "bg-blue-50 border-blue-200 text-blue-700"
              : "bg-white border-gray-300 text-gray-700"
          }`}
        >
          {statusOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>

        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className={`px-3 py-1.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
            priorityFilter !== "All Priority"
              ? "bg-blue-50 border-blue-200 text-blue-700"
              : "bg-white border-gray-300 text-gray-700"
          }`}
        >
          {priorityOptions.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>

        {isFilterActive && (
          <button
            onClick={() => {
              setStatusFilter("All Status");
              setPriorityFilter("All Priority");
            }}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Actions List */}
      <div className="space-y-4">
        {getFilteredActions().map((action) => (
          <div
            key={action.id}
            className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-sm transition-shadow"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h4 className="font-semibold text-gray-900">
                    {action.title}
                  </h4>
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded-full border ${getPriorityColor(
                      action.priority
                    )}`}
                  >
                    {action.priority}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-3">
                  {action.description}
                </p>

                <div className="flex items-center space-x-6 text-sm text-gray-500">
                  <div className="flex items-center space-x-1">
                    {getStatusIcon(action.status)}
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                        action.status
                      )}`}
                    >
                      {action.status}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">Assignee:</span>{" "}
                    {action.assignee}
                  </div>
                  <div>
                    <span className="font-medium">Due:</span> {action.dueDate}
                  </div>
                  <div>
                    <span className="font-medium">Source:</span> {action.source}
                  </div>
                </div>
              </div>
            </div>

            {/* Tags */}
            <div className="flex items-center space-x-2">
              {action.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Empty State */}
      {getFilteredActions().length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <PlayIcon className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No actions found
          </h3>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            {isFilterActive
              ? "No actions match your current filters. Try adjusting the filters or clearing them."
              : "Generate actions from your competitive intelligence insights to get started."}
          </p>
          {!isFilterActive && (
            <button
              onClick={handleGenerateActions}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              Generate Actions from Insights
            </button>
          )}
        </div>
      )}

      {/* Floating Action Button */}
      <button
        onClick={onAddCustomAction}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-colors flex items-center justify-center z-40"
        title="Add Custom Action"
      >
        <PlusIcon className="w-6 h-6" />
      </button>
    </div>
  );
};

export default ActionTracker;
