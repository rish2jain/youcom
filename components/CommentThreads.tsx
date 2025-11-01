"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  MessageSquare,
  Reply,
  Send,
  Edit,
  Trash2,
  AlertTriangle,
  Bell,
  BellOff,
  User,
  Clock,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

interface Comment {
  id: number;
  user_id: number;
  content: string;
  annotations?: any;
  parent_comment_id?: number;
  created_at: string;
  updated_at?: string;
  is_edited: number;
  user_name: string;
  user_email: string;
  replies_count: number;
  replies?: Comment[];
}

interface Conflict {
  id: number;
  conflict_type: string;
  confidence_score: number;
  description: string;
  is_resolved: boolean;
  detected_at: string;
  comment_1: {
    id: number;
    content: string;
    author: string;
  };
  comment_2: {
    id: number;
    content: string;
    author: string;
  };
}

interface CommentThreadsProps {
  impactCardId?: number;
  sharedWatchlistId?: number;
  companyResearchId?: number;
  className?: string;
}

export default function CommentThreads({
  impactCardId,
  sharedWatchlistId,
  companyResearchId,
  className = "",
}: CommentThreadsProps) {
  const [threads, setThreads] = useState<Comment[]>([]);
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedThreads, setExpandedThreads] = useState<Set<number>>(
    new Set()
  );
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [editingComment, setEditingComment] = useState<number | null>(null);

  // New comment/reply state
  const [newComment, setNewComment] = useState("");
  const [replyContent, setReplyContent] = useState("");
  const [editContent, setEditContent] = useState("");

  // Get context parameters
  const getContextParams = () => {
    if (impactCardId) return { impact_card_id: impactCardId };
    if (sharedWatchlistId) return { shared_watchlist_id: sharedWatchlistId };
    if (companyResearchId) return { company_research_id: companyResearchId };
    return {};
  };

  // Fetch comment threads
  const fetchThreads = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams(getContextParams() as any);
      const response = await fetch(`/api/v1/comments/threads?${params}`);
      if (!response.ok) throw new Error("Failed to fetch comment threads");
      const data = await response.json();
      setThreads(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load comments");
    } finally {
      setLoading(false);
    }
  };

  // Fetch conflicts
  const fetchConflicts = async () => {
    try {
      const params = new URLSearchParams(getContextParams() as any);
      const response = await fetch(`/api/v1/comments/conflicts/?${params}`);
      if (!response.ok) throw new Error("Failed to fetch conflicts");
      const data = await response.json();
      setConflicts(data);
    } catch (err) {
      console.error("Failed to fetch conflicts:", err);
    }
  };

  useEffect(() => {
    fetchThreads();
    fetchConflicts();
  }, [impactCardId, sharedWatchlistId, companyResearchId]);

  // Create new comment
  const handleCreateComment = async () => {
    if (!newComment.trim()) return;

    try {
      const params = new URLSearchParams(getContextParams() as any);
      const response = await fetch(`/api/v1/comments/?${params}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: newComment }),
      });

      if (!response.ok) throw new Error("Failed to create comment");

      setNewComment("");
      await fetchThreads();
      await fetchConflicts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create comment");
    }
  };

  // Create reply
  const handleCreateReply = async (parentId: number) => {
    if (!replyContent.trim()) return;

    try {
      const params = new URLSearchParams(getContextParams() as any);
      const response = await fetch(`/api/v1/comments/?${params}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: replyContent,
          parent_comment_id: parentId,
        }),
      });

      if (!response.ok) throw new Error("Failed to create reply");

      setReplyContent("");
      setReplyingTo(null);
      await fetchThreads();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create reply");
    }
  };

  // Update comment
  const handleUpdateComment = async (commentId: number) => {
    if (!editContent.trim()) return;

    try {
      const response = await fetch(`/api/v1/comments/${commentId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: editContent }),
      });

      if (!response.ok) throw new Error("Failed to update comment");

      setEditContent("");
      setEditingComment(null);
      await fetchThreads();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update comment");
    }
  };

  // Delete comment
  const handleDeleteComment = async (commentId: number) => {
    if (!confirm("Are you sure you want to delete this comment?")) return;

    try {
      const response = await fetch(`/api/v1/comments/${commentId}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Failed to delete comment");
      await fetchThreads();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete comment");
    }
  };

  // Toggle thread expansion
  const toggleThread = (threadId: number) => {
    const newExpanded = new Set(expandedThreads);
    if (newExpanded.has(threadId)) {
      newExpanded.delete(threadId);
    } else {
      newExpanded.add(threadId);
    }
    setExpandedThreads(newExpanded);
  };

  // Render individual comment
  const renderComment = (comment: Comment, isReply = false) => {
    const isEditing = editingComment === comment.id;
    const isReplying = replyingTo === comment.id;
    const hasReplies = comment.replies && comment.replies.length > 0;
    const isExpanded = expandedThreads.has(comment.id);

    return (
      <div
        key={comment.id}
        className={`${isReply ? "ml-6 border-l-2 border-gray-200 pl-4" : ""}`}
      >
        <Card className="mb-3">
          <CardContent className="p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <User className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">{comment.user_name}</p>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Clock className="h-3 w-3" />
                    {new Date(comment.created_at).toLocaleDateString()}
                    {comment.is_edited > 0 && (
                      <Badge variant="outline" className="text-xs">
                        Edited
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1">
                {!isReply && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      setReplyingTo(isReplying ? null : comment.id)
                    }
                    className="h-8 w-8 p-0"
                  >
                    <Reply className="h-4 w-4" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setEditingComment(isEditing ? null : comment.id);
                    setEditContent(comment.content);
                  }}
                  className="h-8 w-8 p-0"
                >
                  <Edit className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteComment(comment.id)}
                  className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {isEditing ? (
              <div className="space-y-2">
                <Textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  rows={3}
                />
                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setEditingComment(null);
                      setEditContent("");
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleUpdateComment(comment.id)}
                    disabled={!editContent.trim()}
                  >
                    Update
                  </Button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-700 mb-2">{comment.content}</p>
            )}

            {/* Reply form */}
            {isReplying && (
              <div className="mt-3 space-y-2">
                <Textarea
                  placeholder="Write a reply..."
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  rows={2}
                />
                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setReplyingTo(null);
                      setReplyContent("");
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleCreateReply(comment.id)}
                    disabled={!replyContent.trim()}
                    className="flex items-center gap-1"
                  >
                    <Send className="h-4 w-4" />
                    Reply
                  </Button>
                </div>
              </div>
            )}

            {/* Replies toggle */}
            {hasReplies && !isReply && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleThread(comment.id)}
                className="mt-2 flex items-center gap-1 text-blue-600"
              >
                {isExpanded ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
                {comment.replies!.length}{" "}
                {comment.replies!.length === 1 ? "reply" : "replies"}
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Render replies */}
        {hasReplies && isExpanded && (
          <div className="ml-4">
            {comment.replies!.map((reply) => renderComment(reply, true))}
          </div>
        )}
      </div>
    );
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
            <MessageSquare className="h-5 w-5" />
            Discussion ({threads.length} threads)
          </CardTitle>
          {conflicts.length > 0 && (
            <Badge variant="destructive" className="flex items-center gap-1">
              <AlertTriangle className="h-4 w-4" />
              {conflicts.length} conflicts detected
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Conflicts section */}
        {conflicts.length > 0 && (
          <Card className="border-orange-200 bg-orange-50">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 text-orange-800">
                <AlertTriangle className="h-4 w-4" />
                Conflicting Interpretations Detected
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {conflicts.map((conflict) => (
                <div key={conflict.id} className="p-3 bg-white rounded border">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant="outline" className="text-orange-700">
                      {conflict.conflict_type} conflict
                    </Badge>
                    <span className="text-xs text-gray-500">
                      {conflict.confidence_score}% confidence
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 mb-2">
                    {conflict.description}
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 bg-gray-50 rounded">
                      <p className="font-medium">
                        {conflict.comment_1.author}:
                      </p>
                      <p className="text-gray-600">
                        {conflict.comment_1.content.substring(0, 100)}...
                      </p>
                    </div>
                    <div className="p-2 bg-gray-50 rounded">
                      <p className="font-medium">
                        {conflict.comment_2.author}:
                      </p>
                      <p className="text-gray-600">
                        {conflict.comment_2.content.substring(0, 100)}...
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* New comment form */}
        <Card className="border-dashed">
          <CardContent className="p-4 space-y-3">
            <Textarea
              placeholder="Start a new discussion..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              rows={3}
            />
            <div className="flex justify-end">
              <Button
                onClick={handleCreateComment}
                disabled={!newComment.trim()}
                className="flex items-center gap-1"
              >
                <Send className="h-4 w-4" />
                Post Comment
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Comment threads */}
        <div className="space-y-4">
          {threads.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No comments yet</p>
              <p className="text-sm">
                Start the discussion by posting the first comment
              </p>
            </div>
          ) : (
            threads.map((thread) => renderComment(thread))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
