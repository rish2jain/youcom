"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Eye, EyeOff, Trash2, Play } from "lucide-react";
import { api } from "@/lib/api";

interface WatchItem {
  id: number;
  competitor_name: string;
  keywords: string[];
  description?: string;
  is_active: boolean;
  created_at: string;
  last_checked?: string;
}

export function WatchList() {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newItem, setNewItem] = useState({
    competitor_name: "",
    keywords: "",
    description: "",
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Fetch watchlist items
  const {
    data: watchItems,
    isLoading,
    error: watchError,
  } = useQuery({
    queryKey: ["watchItems"],
    queryFn: () => api.get("/api/v1/watch/").then((res) => res.data.items),
  });

  const watchErrorMessage = watchError
    ? watchError instanceof Error
      ? watchError.message
      : "Unable to load watchlist."
    : null;

  // Create new watch item
  const createMutation = useMutation({
    mutationFn: (data: any) =>
      api.post("/api/v1/watch/", {
        ...data,
        keywords: data.keywords
          .split(",")
          .map((k: string) => k.trim())
          .filter(Boolean),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchItems"] });
      setShowAddForm(false);
      setNewItem({ competitor_name: "", keywords: "", description: "" });
      setFormError(null);
      setActionError(null);
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to add competitor. Please try again.";
      setFormError(message);
    },
  });

  // Toggle active status
  const toggleMutation = useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) =>
      api.post(`/api/v1/watch/${id}/${active ? "activate" : "deactivate"}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchItems"] });
      setActionError(null);
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to update competitor status.";
      setActionError(message);
    },
  });

  // Delete watch item
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/watch/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchItems"] });
      setActionError(null);
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to remove competitor.";
      setActionError(message);
    },
  });

  // Generate Impact Card
  const generateMutation = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/impact/watch/${id}/generate`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["impactCards"] });
      setActionError(null);
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to trigger Impact Card generation.";
      setActionError(message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const competitor = newItem.competitor_name.trim();
    if (competitor.length < 2) {
      setFormError("Competitor name must be at least 2 characters.");
      return;
    }

    setFormError(null);
    createMutation.mutate({ ...newItem, competitor_name: competitor });
  };

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Competitor Watchlist
        </h3>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Competitor</span>
        </button>
      </div>

      {watchErrorMessage && (
        <div className="mb-4 p-3 border border-red-200 bg-red-50 text-sm text-red-700 rounded-lg">
          {watchErrorMessage}
        </div>
      )}

      {actionError && (
        <div className="mb-4 p-3 border border-yellow-200 bg-yellow-50 text-sm text-yellow-800 rounded-lg">
          {actionError}
        </div>
      )}

      {/* Add Form */}
      {showAddForm && (
        <form
          onSubmit={handleSubmit}
          className="mb-6 p-4 bg-gray-50 rounded-lg"
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Competitor Name *
              </label>
              <input
                type="text"
                value={newItem.competitor_name}
                onChange={(e) =>
                  setNewItem({ ...newItem, competitor_name: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., OpenAI, Anthropic, Google"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Keywords (comma-separated)
              </label>
              <input
                type="text"
                value={newItem.keywords}
                onChange={(e) =>
                  setNewItem({ ...newItem, keywords: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., GPT, ChatGPT, AI model, announcement"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={newItem.description}
                onChange={(e) =>
                  setNewItem({ ...newItem, description: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={2}
                placeholder="Why are you monitoring this competitor?"
              />
            </div>
            {formError && (
              <div className="text-sm text-red-600" role="alert">
                {formError}
              </div>
            )}
            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {createMutation.isPending ? "Adding..." : "Add Competitor"}
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Watch Items List */}
      <div className="space-y-4">
        {watchItems?.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No competitors being monitored yet.</p>
            <p className="text-sm">Add your first competitor to get started!</p>
          </div>
        ) : (
          watchItems?.map((item: WatchItem) => (
            <div
              key={item.id}
              className={`p-4 border rounded-lg transition-colors ${
                item.is_active
                  ? "border-green-200 bg-green-50"
                  : "border-gray-200 bg-gray-50"
              }`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="font-medium text-gray-900">
                      {item.competitor_name}
                    </h4>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        item.is_active
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {item.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>

                  {item.keywords.length > 0 && (
                    <div className="mb-2">
                      <span className="text-sm text-gray-600">Keywords: </span>
                      <div className="inline-flex flex-wrap gap-1">
                        {item.keywords.map((keyword, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                          >
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {item.description && (
                    <p className="text-sm text-gray-600 mb-2">
                      {item.description}
                    </p>
                  )}

                  <div className="text-xs text-gray-500">
                    Created: {new Date(item.created_at).toLocaleDateString()}
                    {item.last_checked && (
                      <span className="ml-4">
                        Last checked:{" "}
                        {new Date(item.last_checked).toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => generateMutation.mutate(item.id)}
                    disabled={generateMutation.isPending}
                    className="p-2 text-blue-600 hover:bg-blue-100 rounded-md transition-colors"
                    title="Generate Impact Card"
                  >
                    <Play className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() =>
                      toggleMutation.mutate({
                        id: item.id,
                        active: !item.is_active,
                      })
                    }
                    className="p-2 text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
                    title={item.is_active ? "Deactivate" : "Activate"}
                  >
                    {item.is_active ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>

                  <button
                    onClick={() => deleteMutation.mutate(item.id)}
                    className="p-2 text-red-600 hover:bg-red-100 rounded-md transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Demo Suggestions */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-2">💡 Demo Suggestions</h4>
        <p className="text-sm text-blue-800 mb-3">
          Try adding these competitors to showcase the You.com API integration:
        </p>
        <div className="flex flex-wrap gap-2">
          {["OpenAI", "Anthropic", "Google AI", "Mistral AI"].map((name) => (
            <button
              key={name}
              onClick={() =>
                setNewItem({
                  ...newItem,
                  competitor_name: name,
                  keywords:
                    name === "OpenAI"
                      ? "GPT, ChatGPT, API"
                      : name === "Anthropic"
                      ? "Claude, AI assistant"
                      : name === "Google AI"
                      ? "Gemini, Bard, AI"
                      : "AI model, LLM",
                })
              }
              className="px-3 py-1 text-sm bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200 transition-colors"
            >
              + {name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
