"use client";

import React, { useState, useEffect, useRef } from "react";
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
  MessageSquare,
  Plus,
  Check,
  X,
  Edit,
  Trash2,
  Eye,
  EyeOff,
} from "lucide-react";

interface AnnotationPosition {
  x: number;
  y: number;
  width?: number;
  height?: number;
}

interface Annotation {
  id: number;
  user_id: number;
  impact_card_id: number;
  content: string;
  annotation_type: "insight" | "question" | "concern" | "action";
  position?: AnnotationPosition;
  target_element?: string;
  target_text?: string;
  created_at: string;
  updated_at?: string;
  is_resolved: number;
  resolved_by?: number;
  resolved_at?: string;
  user_name: string;
  user_email: string;
  resolver_name?: string;
}

interface AnnotationSystemProps {
  impactCardId: number;
  className?: string;
}

const ANNOTATION_TYPES = [
  { value: "insight", label: "Insight", color: "bg-blue-100 text-blue-800" },
  {
    value: "question",
    label: "Question",
    color: "bg-yellow-100 text-yellow-800",
  },
  { value: "concern", label: "Concern", color: "bg-red-100 text-red-800" },
  { value: "action", label: "Action", color: "bg-green-100 text-green-800" },
];

export default function AnnotationSystem({
  impactCardId,
  className = "",
}: AnnotationSystemProps) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [showResolved, setShowResolved] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New annotation form state
  const [newAnnotation, setNewAnnotation] = useState({
    content: "",
    annotation_type: "insight" as const,
    target_text: "",
  });

  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch annotations
  const fetchAnnotations = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/v1/annotations/impact-card/${impactCardId}?include_resolved=${showResolved}`
      );
      if (!response.ok) throw new Error("Failed to fetch annotations");
      const data = await response.json();
      setAnnotations(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load annotations"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnnotations();
  }, [impactCardId, showResolved]);

  // Create annotation
  const handleCreateAnnotation = async () => {
    if (!newAnnotation.content.trim()) return;

    try {
      const response = await fetch(
        `/api/v1/annotations/?impact_card_id=${impactCardId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: newAnnotation.content,
            annotation_type: newAnnotation.annotation_type,
            target_text: newAnnotation.target_text || null,
          }),
        }
      );

      if (!response.ok) throw new Error("Failed to create annotation");

      setNewAnnotation({
        content: "",
        annotation_type: "insight",
        target_text: "",
      });
      setIsCreating(false);
      await fetchAnnotations();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create annotation"
      );
    }
  };

  // Update annotation
  const handleUpdateAnnotation = async (
    id: number,
    updates: Partial<Annotation>
  ) => {
    try {
      const response = await fetch(`/api/v1/annotations/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });

      if (!response.ok) throw new Error("Failed to update annotation");

      setEditingId(null);
      await fetchAnnotations();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update annotation"
      );
    }
  };

  // Delete annotation
  const handleDeleteAnnotation = async (id: number) => {
    if (!confirm("Are you sure you want to delete this annotation?")) return;

    try {
      const response = await fetch(`/api/v1/annotations/${id}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Failed to delete annotation");
      await fetchAnnotations();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete annotation"
      );
    }
  };

  // Toggle resolved status
  const handleToggleResolved = async (annotation: Annotation) => {
    await handleUpdateAnnotation(annotation.id, {
      is_resolved: annotation.is_resolved ? 0 : 1,
    });
  };

  const getTypeConfig = (type: string) => {
    return (
      ANNOTATION_TYPES.find((t) => t.value === type) || ANNOTATION_TYPES[0]
    );
  };

  const filteredAnnotations = annotations.filter(
    (annotation) => showResolved || annotation.is_resolved === 0
  );

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
    <Card className={className} ref={containerRef}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Annotations ({filteredAnnotations.length})
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowResolved(!showResolved)}
              className="flex items-center gap-1"
            >
              {showResolved ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
              {showResolved ? "Hide Resolved" : "Show Resolved"}
            </Button>
            <Button
              onClick={() => setIsCreating(true)}
              size="sm"
              className="flex items-center gap-1"
            >
              <Plus className="h-4 w-4" />
              Add Annotation
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

        {/* Create new annotation form */}
        {isCreating && (
          <Card className="border-dashed">
            <CardContent className="p-4 space-y-3">
              <div className="flex items-center gap-2">
                <Select
                  value={newAnnotation.annotation_type}
                  onValueChange={(value: any) =>
                    setNewAnnotation((prev) => ({
                      ...prev,
                      annotation_type: value,
                    }))
                  }
                >
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ANNOTATION_TYPES.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  placeholder="Referenced text (optional)"
                  value={newAnnotation.target_text}
                  onChange={(e) =>
                    setNewAnnotation((prev) => ({
                      ...prev,
                      target_text: e.target.value,
                    }))
                  }
                  className="flex-1"
                />
              </div>
              <Textarea
                placeholder="Enter your annotation..."
                value={newAnnotation.content}
                onChange={(e) =>
                  setNewAnnotation((prev) => ({
                    ...prev,
                    content: e.target.value,
                  }))
                }
                rows={3}
              />
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setIsCreating(false);
                    setNewAnnotation({
                      content: "",
                      annotation_type: "insight",
                      target_text: "",
                    });
                  }}
                >
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleCreateAnnotation}
                  disabled={!newAnnotation.content.trim()}
                >
                  Add Annotation
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Annotations list */}
        <div className="space-y-3">
          {filteredAnnotations.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No annotations yet</p>
              <p className="text-sm">
                Add the first annotation to start collaborating
              </p>
            </div>
          ) : (
            filteredAnnotations.map((annotation) => {
              const typeConfig = getTypeConfig(annotation.annotation_type);
              const isEditing = editingId === annotation.id;

              return (
                <Card
                  key={annotation.id}
                  className={`${annotation.is_resolved ? "opacity-60" : ""}`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge className={typeConfig.color}>
                          {typeConfig.label}
                        </Badge>
                        {annotation.is_resolved === 1 && (
                          <Badge variant="outline" className="text-green-600">
                            <Check className="h-3 w-3 mr-1" />
                            Resolved
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleToggleResolved(annotation)}
                          className="h-8 w-8 p-0"
                        >
                          {annotation.is_resolved ? (
                            <X className="h-4 w-4" />
                          ) : (
                            <Check className="h-4 w-4" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setEditingId(isEditing ? null : annotation.id)
                          }
                          className="h-8 w-8 p-0"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteAnnotation(annotation.id)}
                          className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {annotation.target_text && (
                      <div className="mb-2 p-2 bg-gray-50 rounded text-sm italic">
                        "{annotation.target_text}"
                      </div>
                    )}

                    {isEditing ? (
                      <div className="space-y-2">
                        <Textarea
                          defaultValue={annotation.content}
                          rows={3}
                          onBlur={(e) => {
                            if (e.target.value !== annotation.content) {
                              handleUpdateAnnotation(annotation.id, {
                                content: e.target.value,
                              });
                            }
                          }}
                        />
                      </div>
                    ) : (
                      <p className="text-sm text-gray-700 mb-2">
                        {annotation.content}
                      </p>
                    )}

                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>
                        by {annotation.user_name} •{" "}
                        {new Date(annotation.created_at).toLocaleDateString()}
                      </span>
                      {annotation.resolved_by && annotation.resolver_name && (
                        <span>Resolved by {annotation.resolver_name}</span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
}
