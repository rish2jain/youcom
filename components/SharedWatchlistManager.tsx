"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Users,
  Plus,
  Share2,
  Settings,
  Eye,
  EyeOff,
  UserPlus,
  UserMinus,
  MessageSquare,
  Activity,
  Trash2,
  Edit,
  Globe,
  Lock,
} from "lucide-react";

interface SharedWatchlist {
  id: number;
  workspace_id: number;
  name: string;
  description?: string;
  is_active: boolean;
  watch_item_id: number;
  created_by: number;
  is_public: boolean;
  created_at: string;
  updated_at?: string;
  creator_name: string;
  creator_email: string;
  watch_item_name: string;
  watch_item_query: string;
  assigned_users_count: number;
  comments_count: number;
}

interface WatchItem {
  id: number;
  name: string;
  query: string;
}

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
}

interface SharedWatchlistManagerProps {
  workspaceId: number;
  className?: string;
}

export default function SharedWatchlistManager({
  workspaceId,
  className = "",
}: SharedWatchlistManagerProps) {
  const [watchlists, setWatchlists] = useState<SharedWatchlist[]>([]);
  const [watchItems, setWatchItems] = useState<WatchItem[]>([]);
  const [workspaceUsers, setWorkspaceUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInactive, setShowInactive] = useState(false);
  const [onlyAssigned, setOnlyAssigned] = useState(false);

  // Create watchlist state
  const [isCreating, setIsCreating] = useState(false);
  const [newWatchlist, setNewWatchlist] = useState({
    name: "",
    description: "",
    watch_item_id: 0,
    is_public: false,
  });

  // Assignment state
  const [assignmentDialog, setAssignmentDialog] = useState<{
    open: boolean;
    watchlistId: number;
    currentAssignments: number[];
  }>({
    open: false,
    watchlistId: 0,
    currentAssignments: [],
  });

  // Fetch data
  const fetchWatchlists = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/v1/shared-watchlists/workspace/${workspaceId}?include_inactive=${showInactive}&only_assigned=${onlyAssigned}`
      );
      if (!response.ok) throw new Error("Failed to fetch watchlists");
      const data = await response.json();
      setWatchlists(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load watchlists"
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchWatchItems = async () => {
    try {
      const response = await fetch("/api/v1/watch");
      if (!response.ok) throw new Error("Failed to fetch watch items");
      const data = await response.json();
      setWatchItems(data);
    } catch (err) {
      console.error("Failed to fetch watch items:", err);
    }
  };

  const fetchWorkspaceUsers = async () => {
    try {
      const response = await fetch(`/api/v1/workspaces/${workspaceId}/members`);
      if (!response.ok) throw new Error("Failed to fetch workspace users");
      const data = await response.json();
      setWorkspaceUsers(
        data.map((member: any) => ({
          id: member.user_id,
          username: member.user_username,
          email: member.user_email,
          full_name: member.user_full_name,
        }))
      );
    } catch (err) {
      console.error("Failed to fetch workspace users:", err);
    }
  };

  useEffect(() => {
    fetchWatchlists();
    fetchWatchItems();
    fetchWorkspaceUsers();
  }, [workspaceId, showInactive, onlyAssigned]);

  // Create watchlist
  const handleCreateWatchlist = async () => {
    if (!newWatchlist.name.trim() || !newWatchlist.watch_item_id) return;

    try {
      const response = await fetch(
        `/api/v1/shared-watchlists/?workspace_id=${workspaceId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(newWatchlist),
        }
      );

      if (!response.ok) throw new Error("Failed to create watchlist");

      setNewWatchlist({
        name: "",
        description: "",
        watch_item_id: 0,
        is_public: false,
      });
      setIsCreating(false);
      await fetchWatchlists();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create watchlist"
      );
    }
  };

  // Toggle watchlist status
  const handleToggleStatus = async (watchlist: SharedWatchlist) => {
    try {
      const response = await fetch(
        `/api/v1/shared-watchlists/${watchlist.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_active: !watchlist.is_active }),
        }
      );

      if (!response.ok) throw new Error("Failed to update watchlist");
      await fetchWatchlists();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update watchlist"
      );
    }
  };

  // Toggle public status
  const handleTogglePublic = async (watchlist: SharedWatchlist) => {
    try {
      const response = await fetch(
        `/api/v1/shared-watchlists/${watchlist.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_public: !watchlist.is_public }),
        }
      );

      if (!response.ok) throw new Error("Failed to update watchlist");
      await fetchWatchlists();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update watchlist"
      );
    }
  };

  // Delete watchlist
  const handleDeleteWatchlist = async (watchlistId: number) => {
    if (!confirm("Are you sure you want to delete this shared watchlist?"))
      return;

    try {
      const response = await fetch(`/api/v1/shared-watchlists/${watchlistId}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Failed to delete watchlist");
      await fetchWatchlists();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete watchlist"
      );
    }
  };

  // Manage assignments
  const handleManageAssignments = async (watchlistId: number) => {
    try {
      const response = await fetch(
        `/api/v1/shared-watchlists/${watchlistId}/assignments`
      );
      if (!response.ok) throw new Error("Failed to fetch assignments");
      const assignments = await response.json();

      setAssignmentDialog({
        open: true,
        watchlistId,
        currentAssignments: assignments.map((a: any) => a.user_id),
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load assignments"
      );
    }
  };

  // Update assignments
  const handleUpdateAssignments = async (userIds: number[]) => {
    try {
      const response = await fetch(
        `/api/v1/shared-watchlists/${assignmentDialog.watchlistId}/assign`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_ids: userIds }),
        }
      );

      if (!response.ok) throw new Error("Failed to update assignments");

      setAssignmentDialog({
        open: false,
        watchlistId: 0,
        currentAssignments: [],
      });
      await fetchWatchlists();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update assignments"
      );
    }
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="space-y-2">
              <div className="h-3 bg-gray-200 rounded"></div>
              <div className="h-3 bg-gray-200 rounded w-5/6"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Share2 className="h-5 w-5" />
            Shared Watchlists ({watchlists.length})
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowInactive(!showInactive)}
              className="flex items-center gap-1"
            >
              {showInactive ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
              {showInactive ? "Hide Inactive" : "Show Inactive"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setOnlyAssigned(!onlyAssigned)}
              className="flex items-center gap-1"
            >
              <Users className="h-4 w-4" />
              {onlyAssigned ? "Show All" : "Only Assigned"}
            </Button>
            <Button
              onClick={() => setIsCreating(true)}
              size="sm"
              className="flex items-center gap-1"
            >
              <Plus className="h-4 w-4" />
              Create Watchlist
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Create watchlist form */}
        {isCreating && (
          <Card className="border-dashed">
            <CardContent className="p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <Input
                  placeholder="Watchlist name"
                  value={newWatchlist.name}
                  onChange={(e) =>
                    setNewWatchlist((prev) => ({
                      ...prev,
                      name: e.target.value,
                    }))
                  }
                />
                <Select
                  value={newWatchlist.watch_item_id.toString()}
                  onValueChange={(value) =>
                    setNewWatchlist((prev) => ({
                      ...prev,
                      watch_item_id: parseInt(value),
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select watch item" />
                  </SelectTrigger>
                  <SelectContent>
                    {watchItems.map((item) => (
                      <SelectItem key={item.id} value={item.id.toString()}>
                        {item.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Textarea
                placeholder="Description (optional)"
                value={newWatchlist.description}
                onChange={(e) =>
                  setNewWatchlist((prev) => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
                rows={2}
              />
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={newWatchlist.is_public}
                    onChange={(e) =>
                      setNewWatchlist((prev) => ({
                        ...prev,
                        is_public: e.target.checked,
                      }))
                    }
                  />
                  Make public within workspace
                </label>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setIsCreating(false);
                      setNewWatchlist({
                        name: "",
                        description: "",
                        watch_item_id: 0,
                        is_public: false,
                      });
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleCreateWatchlist}
                    disabled={
                      !newWatchlist.name.trim() || !newWatchlist.watch_item_id
                    }
                  >
                    Create
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Watchlists list */}
        <div className="space-y-3">
          {watchlists.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Share2 className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No shared watchlists yet</p>
              <p className="text-sm">
                Create the first shared watchlist to start collaborating
              </p>
            </div>
          ) : (
            watchlists.map((watchlist) => (
              <Card
                key={watchlist.id}
                className={`${!watchlist.is_active ? "opacity-60" : ""}`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium">{watchlist.name}</h3>
                        <Badge
                          variant={
                            watchlist.is_active ? "default" : "secondary"
                          }
                        >
                          {watchlist.is_active ? "Active" : "Inactive"}
                        </Badge>
                        <Badge
                          variant="outline"
                          className="flex items-center gap-1"
                        >
                          {watchlist.is_public ? (
                            <Globe className="h-3 w-3" />
                          ) : (
                            <Lock className="h-3 w-3" />
                          )}
                          {watchlist.is_public ? "Public" : "Private"}
                        </Badge>
                      </div>
                      {watchlist.description && (
                        <p className="text-sm text-gray-600 mb-2">
                          {watchlist.description}
                        </p>
                      )}
                      <div className="text-xs text-gray-500">
                        <p>Watching: {watchlist.watch_item_name}</p>
                        <p>
                          Created by: {watchlist.creator_name} •{" "}
                          {new Date(watchlist.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleToggleStatus(watchlist)}
                        className="h-8 w-8 p-0"
                      >
                        <Activity className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleTogglePublic(watchlist)}
                        className="h-8 w-8 p-0"
                      >
                        {watchlist.is_public ? (
                          <Lock className="h-4 w-4" />
                        ) : (
                          <Globe className="h-4 w-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleManageAssignments(watchlist.id)}
                        className="h-8 w-8 p-0"
                      >
                        <UserPlus className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteWatchlist(watchlist.id)}
                        className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <Users className="h-4 w-4" />
                      {watchlist.assigned_users_count} assigned
                    </span>
                    <span className="flex items-center gap-1">
                      <MessageSquare className="h-4 w-4" />
                      {watchlist.comments_count} comments
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Assignment Dialog */}
        <Dialog
          open={assignmentDialog.open}
          onOpenChange={(open) =>
            setAssignmentDialog((prev) => ({ ...prev, open }))
          }
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Manage User Assignments</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Select users to assign to this watchlist:
              </p>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {workspaceUsers.map((user) => (
                  <label
                    key={user.id}
                    className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={assignmentDialog.currentAssignments.includes(
                        user.id
                      )}
                      onChange={(e) => {
                        const newAssignments = e.target.checked
                          ? [...assignmentDialog.currentAssignments, user.id]
                          : assignmentDialog.currentAssignments.filter(
                              (id) => id !== user.id
                            );
                        setAssignmentDialog((prev) => ({
                          ...prev,
                          currentAssignments: newAssignments,
                        }));
                      }}
                    />
                    <div>
                      <p className="text-sm font-medium">
                        {user.full_name || user.username}
                      </p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                    </div>
                  </label>
                ))}
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() =>
                    setAssignmentDialog({
                      open: false,
                      watchlistId: 0,
                      currentAssignments: [],
                    })
                  }
                >
                  Cancel
                </Button>
                <Button
                  onClick={() =>
                    handleUpdateAssignments(assignmentDialog.currentAssignments)
                  }
                >
                  Update Assignments
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
