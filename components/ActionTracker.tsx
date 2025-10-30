"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import {
  Plus,
  Calendar,
  User,
  Flag,
  CheckCircle,
  Clock,
  AlertTriangle,
  MoreHorizontal,
  Kanban,
  List,
  Filter,
  SortAsc,
  Play,
  Pause,
  Square,
  X,
} from "lucide-react";

interface ActionItem {
  id: number;
  impact_card_id: number;
  title: string;
  description?: string;
  category?: string;
  status: "planned" | "in_progress" | "done" | "cancelled";
  priority: "low" | "medium" | "high" | "urgent";
  assigned_to?: string;
  owner_type: string;
  created_at: string;
  updated_at: string;
  due_date?: string;
  completed_at?: string;
  progress_percentage: number;
  estimated_hours?: number;
  actual_hours?: number;
  source_insight?: string;
  evidence_links?: string[];
  success_criteria?: string[];
  notes?: string;
  ai_generated: boolean;
  user_modified: boolean;
  is_overdue: boolean;
  days_until_due?: number;
}

interface ActionSummary {
  total_actions: number;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  overdue_count: number;
  completed_this_week: number;
  estimated_total_hours: number;
  actual_total_hours: number;
}

interface ActionBoard {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  board_type: string;
  columns: Array<{
    id: string;
    name: string;
    color?: string;
  }>;
  created_at: string;
  updated_at: string;
}

interface ActionBoardItem {
  id: number;
  board_id: number;
  action_item_id: number;
  column_id: string;
  position: number;
  custom_title?: string;
  custom_color?: string;
  tags?: string[];
  added_at: string;
  moved_at?: string;
  action_item: ActionItem;
}

interface ActionBoardView {
  board: ActionBoard;
  items_by_column: Record<string, ActionBoardItem[]>;
  summary: ActionSummary;
}

interface ActionTrackerProps {
  impactCardId?: number;
  userId: number;
  viewMode?: "list" | "kanban";
  showSummary?: boolean;
  onActionUpdate?: (action: ActionItem) => void;
}

const ActionTracker: React.FC<ActionTrackerProps> = ({
  impactCardId,
  userId,
  viewMode = "list",
  showSummary = true,
  onActionUpdate,
}) => {
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [summary, setSummary] = useState<ActionSummary | null>(null);
  const [boardView, setBoardView] = useState<ActionBoardView | null>(null);
  const [currentBoard, setCurrentBoard] = useState<ActionBoard | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentViewMode, setCurrentViewMode] = useState(viewMode);
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterPriority, setFilterPriority] = useState<string>("all");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newAction, setNewAction] = useState({
    title: "",
    description: "",
    category: "",
    priority: "medium" as const,
    assigned_to: "",
    due_date: "",
    estimated_hours: "",
  });

  useEffect(() => {
    loadData();
  }, [impactCardId, userId, filterStatus, filterPriority]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      // Load actions
      const actionsUrl = new URL(
        "/api/v1/enhancements/actions",
        window.location.origin
      );
      if (impactCardId)
        actionsUrl.searchParams.set("impact_card_id", impactCardId.toString());
      if (filterStatus !== "all")
        actionsUrl.searchParams.set("status", filterStatus);

      const actionsResponse = await fetch(actionsUrl.toString());
      if (actionsResponse.ok) {
        const actionsData = await actionsResponse.json();
        setActions(actionsData);
      }

      // Load summary if impact card is specified
      if (impactCardId && showSummary) {
        const summaryResponse = await fetch(
          `/api/v1/enhancements/actions/summary/${impactCardId}`
        );
        if (summaryResponse.ok) {
          const summaryData = await summaryResponse.json();
          setSummary(summaryData);
        }
      }

      // Load board view if in kanban mode
      if (currentViewMode === "kanban") {
        await loadBoardView();
      }
    } catch (error) {
      console.error("Failed to load action data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const [isCreatingBoard, setIsCreatingBoard] = useState(false);
  const [boardError, setBoardError] = useState<string | null>(null);

  const loadBoardView = async () => {
    if (isCreatingBoard) return; // Prevent concurrent creation

    try {
      setBoardError(null);

      // First, ensure we have a board
      if (!currentBoard) {
        setIsCreatingBoard(true);

        const boardResponse = await fetch(
          "/api/v1/enhancements/boards/create",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              name: "My Action Board",
              user_id: userId,
              description: "Personal action tracking board",
              board_type: "personal",
              columns: [],
            }),
          }
        );

        if (!boardResponse.ok) {
          throw new Error(
            `Failed to create board: ${boardResponse.statusText}`
          );
        }

        const board = await boardResponse.json();
        setCurrentBoard(board);

        // Batch add actions to board if any exist
        if (actions.length > 0) {
          const addPromises = actions.map((action) =>
            fetch(`/api/v1/enhancements/boards/${board.id}/add-action`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                action_item_id: action.id,
                column_id:
                  action.status === "planned"
                    ? "planned"
                    : action.status === "in_progress"
                    ? "in_progress"
                    : "done",
              }),
            })
          );

          await Promise.all(addPromises);
        }

        // Load the board view
        const boardViewResponse = await fetch(
          `/api/v1/enhancements/boards/${board.id}/view`
        );
        if (boardViewResponse.ok) {
          const boardViewData = await boardViewResponse.json();
          setBoardView(boardViewData);
        }
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to load board view";
      console.error("Failed to load board view:", error);
      setBoardError(errorMessage);
    } finally {
      setIsCreatingBoard(false);
    }
  };

  const createAction = async () => {
    if (!impactCardId || !newAction.title.trim()) return;

    try {
      const response = await fetch("/api/v1/enhancements/actions/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          impact_card_id: impactCardId,
          title: newAction.title,
          description: newAction.description || undefined,
          category: newAction.category || undefined,
          priority: newAction.priority,
          assigned_to: newAction.assigned_to || undefined,
          due_date: newAction.due_date || undefined,
          estimated_hours: newAction.estimated_hours
            ? parseInt(newAction.estimated_hours)
            : undefined,
        }),
      });

      if (response.ok) {
        const createdAction = await response.json();
        setActions((prev) => [...prev, createdAction]);
        setNewAction({
          title: "",
          description: "",
          category: "",
          priority: "medium",
          assigned_to: "",
          due_date: "",
          estimated_hours: "",
        });
        setShowCreateForm(false);
        onActionUpdate?.(createdAction);
      }
    } catch (error) {
      console.error("Failed to create action:", error);
    }
  };

  const updateActionStatus = async (
    actionId: number,
    newStatus: ActionItem["status"]
  ) => {
    try {
      const response = await fetch(`/api/v1/enhancements/actions/${actionId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });

      if (response.ok) {
        const updatedAction = await response.json();
        setActions((prev) =>
          prev.map((a) => (a.id === actionId ? updatedAction : a))
        );
        onActionUpdate?.(updatedAction);
      }
    } catch (error) {
      console.error("Failed to update action status:", error);
    }
  };

  const generateActionsFromTemplate = async (templateName?: string) => {
    if (!impactCardId) return;

    try {
      const url = `/api/v1/enhancements/actions/generate/${impactCardId}${
        templateName ? `?template_name=${encodeURIComponent(templateName)}` : ""
      }`;
      const response = await fetch(url, { method: "POST" });

      if (response.ok) {
        const generatedActions = await response.json();
        setActions((prev) => [...prev, ...generatedActions]);
        generatedActions.forEach((action: ActionItem) =>
          onActionUpdate?.(action)
        );
      }
    } catch (error) {
      console.error("Failed to generate actions:", error);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "urgent":
        return "bg-red-100 text-red-800 border-red-200";
      case "high":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "medium":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "low":
        return "bg-gray-100 text-gray-800 border-gray-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "planned":
        return <Clock className="w-4 h-4" />;
      case "in_progress":
        return <Play className="w-4 h-4" />;
      case "done":
        return <CheckCircle className="w-4 h-4" />;
      case "cancelled":
        return <X className="w-4 h-4" />;
      default:
        return <Square className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "planned":
        return "text-gray-600";
      case "in_progress":
        return "text-blue-600";
      case "done":
        return "text-green-600";
      case "cancelled":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  const formatDueDate = (dueDateStr?: string, daysUntilDue?: number) => {
    if (!dueDateStr) return null;

    const dueDate = new Date(dueDateStr);
    const isOverdue = daysUntilDue !== undefined && daysUntilDue < 0;
    const isToday = daysUntilDue === 0;
    const isTomorrow = daysUntilDue === 1;

    let displayText = dueDate.toLocaleDateString();
    if (isToday) displayText = "Today";
    else if (isTomorrow) displayText = "Tomorrow";
    else if (
      daysUntilDue !== undefined &&
      daysUntilDue > 0 &&
      daysUntilDue <= 7
    ) {
      displayText = `${daysUntilDue}d`;
    }

    return (
      <span
        className={`text-xs ${
          isOverdue
            ? "text-red-600"
            : isToday
            ? "text-orange-600"
            : "text-gray-500"
        }`}
      >
        {isOverdue && <AlertTriangle className="w-3 h-3 inline mr-1" />}
        {displayText}
      </span>
    );
  };

  const filteredActions = actions.filter((action) => {
    if (filterStatus !== "all" && action.status !== filterStatus) return false;
    if (filterPriority !== "all" && action.priority !== filterPriority)
      return false;
    return true;
  });

  const ActionCard: React.FC<{ action: ActionItem; compact?: boolean }> = ({
    action,
    compact = false,
  }) => (
    <Card
      className={`${compact ? "p-3" : "p-4"} hover:shadow-sm transition-shadow`}
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h4
              className={`font-medium text-gray-900 ${
                compact ? "text-sm" : "text-base"
              } line-clamp-2`}
            >
              {action.title}
            </h4>
            {action.description && !compact && (
              <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                {action.description}
              </p>
            )}
          </div>
          <div className="flex items-center space-x-2 ml-3">
            <Badge
              className={getPriorityColor(action.priority)}
              variant="outline"
            >
              {action.priority}
            </Badge>
            <div className={`${getStatusColor(action.status)}`}>
              {getStatusIcon(action.status)}
            </div>
          </div>
        </div>

        {/* Progress */}
        {action.progress_percentage > 0 && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-gray-500">
              <span>Progress</span>
              <span>{action.progress_percentage}%</span>
            </div>
            <Progress value={action.progress_percentage} className="h-1" />
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center space-x-3">
            {action.category && (
              <Badge variant="secondary" className="text-xs">
                {action.category}
              </Badge>
            )}
            {action.assigned_to && (
              <span className="flex items-center">
                <User className="w-3 h-3 mr-1" />
                {action.assigned_to}
              </span>
            )}
            {action.estimated_hours && (
              <span className="flex items-center">
                <Clock className="w-3 h-3 mr-1" />
                {action.estimated_hours}h
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {formatDueDate(action.due_date, action.days_until_due)}
            {action.ai_generated && (
              <Badge variant="outline" className="text-xs">
                AI
              </Badge>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <div className="flex space-x-1">
            {action.status !== "done" && (
              <Button
                size="sm"
                variant="outline"
                onClick={() =>
                  updateActionStatus(
                    action.id,
                    action.status === "planned" ? "in_progress" : "done"
                  )
                }
              >
                {action.status === "planned" ? (
                  <>
                    <Play className="w-3 h-3 mr-1" />
                    Start
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Complete
                  </>
                )}
              </Button>
            )}
            {action.status === "done" && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => updateActionStatus(action.id, "in_progress")}
              >
                <Pause className="w-3 h-3 mr-1" />
                Reopen
              </Button>
            )}
          </div>
          <Button size="sm" variant="ghost">
            <MoreHorizontal className="w-3 h-3" />
          </Button>
        </div>
      </div>
    </Card>
  );

  const CreateActionForm: React.FC = () => (
    <Card className="p-4 border-dashed border-2 border-gray-300">
      <div className="space-y-4">
        <div>
          <input
            type="text"
            placeholder="Action title..."
            value={newAction.title}
            onChange={(e) =>
              setNewAction((prev) => ({ ...prev, title: e.target.value }))
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <textarea
            placeholder="Description (optional)..."
            value={newAction.description}
            onChange={(e) =>
              setNewAction((prev) => ({ ...prev, description: e.target.value }))
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 h-20 resize-none"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <select
              value={newAction.priority}
              onChange={(e) =>
                setNewAction((prev) => ({
                  ...prev,
                  priority: e.target.value as any,
                }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="low">Low Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="high">High Priority</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>
          <div>
            <input
              type="date"
              value={newAction.due_date}
              onChange={(e) =>
                setNewAction((prev) => ({ ...prev, due_date: e.target.value }))
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <div className="flex space-x-2">
          <Button onClick={createAction} disabled={!newAction.title.trim()}>
            Create Action
          </Button>
          <Button variant="outline" onClick={() => setShowCreateForm(false)}>
            Cancel
          </Button>
        </div>
      </div>
    </Card>
  );

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Action Tracker</h3>
          <p className="text-sm text-gray-500">
            Lightweight task management for your competitive intelligence
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              setCurrentViewMode(currentViewMode === "list" ? "kanban" : "list")
            }
          >
            {currentViewMode === "list" ? (
              <Kanban className="w-4 h-4" />
            ) : (
              <List className="w-4 h-4" />
            )}
          </Button>
          {impactCardId && (
            <Button size="sm" onClick={() => generateActionsFromTemplate()}>
              <Plus className="w-4 h-4 mr-1" />
              Generate Actions
            </Button>
          )}
        </div>
      </div>

      {/* Summary */}
      {summary && showSummary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="text-2xl font-bold text-gray-900">
              {summary.total_actions}
            </div>
            <div className="text-sm text-gray-500">Total Actions</div>
          </Card>
          <Card className="p-4">
            <div className="text-2xl font-bold text-green-600">
              {summary.by_status.done || 0}
            </div>
            <div className="text-sm text-gray-500">Completed</div>
          </Card>
          <Card className="p-4">
            <div className="text-2xl font-bold text-blue-600">
              {summary.by_status.in_progress || 0}
            </div>
            <div className="text-sm text-gray-500">In Progress</div>
          </Card>
          <Card className="p-4">
            <div className="text-2xl font-bold text-red-600">
              {summary.overdue_count}
            </div>
            <div className="text-sm text-gray-500">Overdue</div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Status</option>
            <option value="planned">Planned</option>
            <option value="in_progress">In Progress</option>
            <option value="done">Done</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        <div>
          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Priority</option>
            <option value="urgent">Urgent</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>

      {/* Actions List */}
      <div className="space-y-4">
        {/* Create Form */}
        {showCreateForm ? (
          <CreateActionForm />
        ) : (
          impactCardId && (
            <Button
              variant="outline"
              onClick={() => setShowCreateForm(true)}
              className="w-full border-dashed border-2 border-gray-300 h-12"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add New Action
            </Button>
          )
        )}

        {/* Actions */}
        {filteredActions.length > 0 ? (
          <div className="space-y-3">
            {filteredActions.map((action) => (
              <ActionCard key={action.id} action={action} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <CheckCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-medium mb-2">No actions yet</h3>
            <p>
              Create your first action or generate them from the impact card
              insights
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActionTracker;
