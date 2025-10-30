"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  FileText,
  FolderOpen,
  Link,
  Settings,
  Download,
  Upload,
  CheckCircle,
  AlertTriangle,
  Tag,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";

interface ObsidianIntegration {
  id: number;
  user_id: string;
  vault_path: string;
  sync_enabled: boolean;
  note_templates: Record<string, any>;
  tag_hierarchy: Record<string, string[]>;
  last_sync: string;
  sync_status: "active" | "error" | "pending";
  created_at: string;
  error_message?: string;
}

interface NoteTemplate {
  name: string;
  type: "company_profile" | "market_analysis" | "trend_report";
  template: string;
  enabled: boolean;
}

interface SyncStats {
  notes_created: number;
  notes_updated: number;
  backlinks_created: number;
  tags_applied: number;
  last_sync_duration: number;
  sync_errors: number;
}

export function ObsidianIntegrationSetup() {
  const [vaultPath, setVaultPath] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [noteTemplates, setNoteTemplates] = useState<NoteTemplate[]>([
    {
      name: "Company Profile",
      type: "company_profile",
      template:
        "# {{company_name}}\n\n## Overview\n{{description}}\n\n## Competitive Intelligence\n{{intelligence_data}}\n\n## Related Companies\n{{backlinks}}",
      enabled: true,
    },
    {
      name: "Market Analysis",
      type: "market_analysis",
      template:
        "# Market Analysis: {{market_name}}\n\n## Key Players\n{{competitors}}\n\n## Trends\n{{trends}}\n\n## Intelligence Insights\n{{insights}}",
      enabled: true,
    },
    {
      name: "Trend Report",
      type: "trend_report",
      template:
        "# Trend Report: {{trend_name}}\n\n## Summary\n{{summary}}\n\n## Impact Analysis\n{{impact}}\n\n## Related Entities\n{{entities}}",
      enabled: true,
    },
  ]);
  const [tagHierarchy, setTagHierarchy] = useState<Record<string, string[]>>({
    "competitive-intelligence": ["companies", "products", "markets"],
    "risk-assessment": ["high-risk", "medium-risk", "low-risk"],
    industry: ["saas", "fintech", "healthtech", "ecommerce"],
  });

  const queryClient = useQueryClient();

  const { data: integration, isLoading: integrationLoading } = useQuery({
    queryKey: ["obsidianIntegration"],
    queryFn: () =>
      api.get("/api/v1/obsidian_integration/").then((res) => res.data),
    staleTime: 60000, // 1 minute
  });

  const { data: syncStats, isLoading: statsLoading } = useQuery({
    queryKey: ["obsidianSyncStats"],
    queryFn: () =>
      api.get("/api/v1/obsidian_integration/stats").then((res) => res.data),
    enabled: !!integration,
    staleTime: 30000,
  });

  const setupMutation = useMutation({
    mutationFn: (data: {
      vault_path: string;
      api_key?: string;
      note_templates: Record<string, any>;
      tag_hierarchy: Record<string, string[]>;
    }) => api.post("/api/v1/obsidian_integration/setup", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["obsidianIntegration"] });
    },
  });

  const syncMutation = useMutation({
    mutationFn: () => api.post("/api/v1/obsidian_integration/sync"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["obsidianSyncStats"] });
      queryClient.invalidateQueries({ queryKey: ["obsidianIntegration"] });
    },
  });

  const exportMutation = useMutation({
    mutationFn: (data: {
      entity_ids?: string[];
      format: "markdown" | "json";
    }) => api.post("/api/v1/obsidian_integration/export", data),
    onSuccess: (response) => {
      // Handle file download
      const blob = new Blob([response.data], {
        type: "application/octet-stream",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `obsidian-export-${
        new Date().toISOString().split("T")[0]
      }.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: () => api.delete("/api/v1/obsidian_integration/"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["obsidianIntegration"] });
    },
  });

  const toggleSyncMutation = useMutation({
    mutationFn: (enabled: boolean) =>
      api.patch("/api/v1/obsidian_integration/", { sync_enabled: enabled }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["obsidianIntegration"] });
    },
  });

  const updateTemplate = (index: number, updates: Partial<NoteTemplate>) => {
    setNoteTemplates((prev) =>
      prev.map((template, i) =>
        i === index ? { ...template, ...updates } : template
      )
    );
  };

  const addTagCategory = () => {
    const category = prompt("Enter tag category name:");
    if (category && !tagHierarchy[category]) {
      setTagHierarchy((prev) => ({
        ...prev,
        [category]: [],
      }));
    }
  };

  const addTag = (category: string) => {
    const tag = prompt(`Enter tag for ${category}:`);
    if (tag && !tagHierarchy[category].includes(tag)) {
      setTagHierarchy((prev) => ({
        ...prev,
        [category]: [...prev[category], tag],
      }));
    }
  };

  const removeTag = (category: string, tag: string) => {
    setTagHierarchy((prev) => ({
      ...prev,
      [category]: prev[category].filter((t) => t !== tag),
    }));
  };

  const handleSetup = () => {
    if (!vaultPath.trim()) {
      alert("Please enter a vault path");
      return;
    }

    const templatesObj = noteTemplates.reduce(
      (acc, template) => ({
        ...acc,
        [template.type]: {
          name: template.name,
          template: template.template,
          enabled: template.enabled,
        },
      }),
      {}
    );

    setupMutation.mutate({
      vault_path: vaultPath.trim(),
      api_key: apiKey.trim() || undefined,
      note_templates: templatesObj,
      tag_hierarchy: tagHierarchy,
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "text-green-600 bg-green-100";
      case "error":
        return "text-red-600 bg-red-100";
      case "pending":
        return "text-yellow-600 bg-yellow-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  if (integrationLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const integrationData = integration as ObsidianIntegration;
  const stats = syncStats as SyncStats;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <div className="w-8 h-8 mr-3 bg-purple-600 rounded flex items-center justify-center">
              <FileText className="w-4 h-4 text-white" />
            </div>
            Obsidian Knowledge Management
          </h3>
          {integrationData && (
            <div className="flex items-center space-x-4">
              <span
                className={`px-3 py-1 text-sm rounded-full ${getStatusColor(
                  integrationData.sync_status
                )}`}
              >
                {integrationData.sync_status.toUpperCase()}
              </span>
              <button
                onClick={() => disconnectMutation.mutate()}
                disabled={disconnectMutation.isPending}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Disconnect
              </button>
            </div>
          )}
        </div>

        {!integrationData ? (
          /* Setup Flow */
          <div className="space-y-6">
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 bg-purple-100 rounded-full flex items-center justify-center">
                <FileText className="w-8 h-8 text-purple-600" />
              </div>
              <h4 className="text-xl font-semibold text-gray-900 mb-2">
                Connect Obsidian Vault
              </h4>
              <p className="text-gray-600 mb-6">
                Export competitive intelligence insights to your Obsidian vault
                with automatic backlinks, tags, and customizable note templates.
              </p>
            </div>

            {/* Benefits */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <Link className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                <h5 className="font-semibold text-gray-900 mb-1">
                  Smart Linking
                </h5>
                <p className="text-sm text-gray-600">
                  Automatic backlinks between related entities and topics
                </p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <Tag className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <h5 className="font-semibold text-gray-900 mb-1">
                  Organized Tags
                </h5>
                <p className="text-sm text-gray-600">
                  Hierarchical tagging system for competitive intelligence
                </p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <FileText className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                <h5 className="font-semibold text-gray-900 mb-1">
                  Custom Templates
                </h5>
                <p className="text-sm text-gray-600">
                  Tailored note formats for different intelligence types
                </p>
              </div>
            </div>

            {/* Configuration */}
            <div className="space-y-6">
              {/* Basic Settings */}
              <div>
                <h5 className="font-semibold text-gray-900 mb-4">
                  Vault Configuration
                </h5>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Vault Path <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <FolderOpen className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                      <input
                        type="text"
                        value={vaultPath}
                        onChange={(e) => setVaultPath(e.target.value)}
                        placeholder="/path/to/your/obsidian/vault"
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        required
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Absolute path to your Obsidian vault directory
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      API Key (Optional)
                    </label>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Obsidian API key for advanced features"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Required for real-time sync and advanced plugin features
                    </p>
                  </div>
                </div>
              </div>

              {/* Note Templates */}
              <div>
                <h5 className="font-semibold text-gray-900 mb-4">
                  Note Templates
                </h5>
                <div className="space-y-4">
                  {noteTemplates.map((template, index) => (
                    <div
                      key={template.type}
                      className="p-4 border border-gray-200 rounded-lg"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <input
                            type="checkbox"
                            checked={template.enabled}
                            onChange={(e) =>
                              updateTemplate(index, {
                                enabled: e.target.checked,
                              })
                            }
                            className="rounded"
                          />
                          <span className="font-medium text-gray-900">
                            {template.name}
                          </span>
                          <span className="text-xs text-gray-500 capitalize">
                            ({template.type.replace("_", " ")})
                          </span>
                        </div>
                      </div>
                      <textarea
                        value={template.template}
                        onChange={(e) =>
                          updateTemplate(index, { template: e.target.value })
                        }
                        rows={4}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Note template with {{variables}}"
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        Use variables like {{ company_name }}, {{ description }}
                        , {{ intelligence_data }}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Advanced Settings */}
              <div>
                <button
                  onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                  className="flex items-center space-x-2 text-sm text-purple-600 hover:text-purple-800"
                >
                  <Settings className="w-4 h-4" />
                  <span>Advanced Settings</span>
                </button>

                {showAdvancedSettings && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h6 className="font-semibold text-gray-900 mb-3">
                      Tag Hierarchy
                    </h6>
                    <p className="text-sm text-gray-600 mb-4">
                      Define tag categories and their sub-tags for organizing
                      notes.
                    </p>
                    <div className="space-y-4">
                      {Object.entries(tagHierarchy).map(([category, tags]) => (
                        <div
                          key={category}
                          className="p-3 bg-white rounded-lg border"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-gray-900">
                              #{category}
                            </span>
                            <button
                              onClick={() => addTag(category)}
                              className="text-sm text-purple-600 hover:text-purple-800"
                            >
                              Add Tag
                            </button>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {tags.map((tag) => (
                              <span
                                key={tag}
                                className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs"
                              >
                                #{tag}
                                <button
                                  onClick={() => removeTag(category, tag)}
                                  className="ml-1 text-purple-500 hover:text-purple-700"
                                >
                                  ×
                                </button>
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                      <button
                        onClick={addTagCategory}
                        className="w-full p-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-800"
                      >
                        + Add Tag Category
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Setup Button */}
            <div className="text-center">
              <button
                onClick={handleSetup}
                disabled={setupMutation.isPending || !vaultPath.trim()}
                className="inline-flex items-center space-x-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium disabled:opacity-50"
              >
                {setupMutation.isPending ? (
                  <>
                    <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
                    <span>Setting up...</span>
                  </>
                ) : (
                  <>
                    <FileText className="w-5 h-5" />
                    <span>Connect Vault</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          /* Connected State */
          <div className="space-y-6">
            {/* Status Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <div className="font-semibold text-gray-900">Connected</div>
                <div className="text-sm text-gray-600 truncate">
                  {integrationData.vault_path}
                </div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {stats?.notes_created || 0}
                </div>
                <div className="text-sm text-gray-600">Notes Created</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {stats?.backlinks_created || 0}
                </div>
                <div className="text-sm text-gray-600">Backlinks Created</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {stats?.tags_applied || 0}
                </div>
                <div className="text-sm text-gray-600">Tags Applied</div>
              </div>
            </div>

            {/* Sync Controls */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium text-gray-900">Vault Sync</div>
                <div className="text-sm text-gray-600">
                  Last sync:{" "}
                  {integrationData.last_sync
                    ? new Date(integrationData.last_sync).toLocaleString()
                    : "Never"}
                </div>
                {integrationData.error_message && (
                  <div className="text-sm text-red-600 mt-1">
                    Error: {integrationData.error_message}
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={integrationData.sync_enabled}
                    onChange={(e) =>
                      toggleSyncMutation.mutate(e.target.checked)
                    }
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">
                    Enable Auto-sync
                  </span>
                </label>
                <button
                  onClick={() => syncMutation.mutate()}
                  disabled={syncMutation.isPending}
                  className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                >
                  {syncMutation.isPending ? (
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                  ) : (
                    <RefreshCw className="w-4 h-4" />
                  )}
                  <span>Sync Now</span>
                </button>
              </div>
            </div>

            {/* Export Options */}
            <div className="p-4 bg-blue-50 rounded-lg">
              <h5 className="font-semibold text-gray-900 mb-3">
                Export Options
              </h5>
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => exportMutation.mutate({ format: "markdown" })}
                  disabled={exportMutation.isPending}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <Download className="w-4 h-4" />
                  <span>Export as Markdown</span>
                </button>
                <button
                  onClick={() => exportMutation.mutate({ format: "json" })}
                  disabled={exportMutation.isPending}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
                >
                  <Download className="w-4 h-4" />
                  <span>Export as JSON</span>
                </button>
              </div>
            </div>

            {/* Active Templates */}
            <div>
              <h5 className="font-semibold text-gray-900 mb-3">
                Active Note Templates
              </h5>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {Object.entries(integrationData.note_templates).map(
                  ([type, template]: [string, any]) => (
                    <div
                      key={type}
                      className="p-3 bg-green-50 rounded-lg border border-green-200"
                    >
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-gray-900">
                          {template.name}
                        </span>
                      </div>
                      <div className="text-xs text-gray-600 mt-1 capitalize">
                        {type.replace("_", " ")}
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>

            {/* Tag Hierarchy */}
            <div>
              <h5 className="font-semibold text-gray-900 mb-3">
                Tag Hierarchy
              </h5>
              <div className="space-y-2">
                {Object.entries(integrationData.tag_hierarchy).map(
                  ([category, tags]) => (
                    <div key={category} className="p-3 bg-purple-50 rounded-lg">
                      <div className="font-medium text-purple-900 mb-2">
                        #{category}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {tags.map((tag: string) => (
                          <span
                            key={tag}
                            className="inline-block px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>

            {/* Sync Performance */}
            {stats && (
              <div className="p-4 bg-gray-50 rounded-lg">
                <h5 className="font-semibold text-gray-900 mb-3">
                  Sync Performance
                </h5>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">
                      Last Sync Duration:
                    </span>
                    <span className="ml-2">{stats.last_sync_duration}s</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">
                      Notes Updated:
                    </span>
                    <span className="ml-2">{stats.notes_updated}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">
                      Sync Errors:
                    </span>
                    <span
                      className={`ml-2 ${
                        stats.sync_errors > 0
                          ? "text-red-600"
                          : "text-green-600"
                      }`}
                    >
                      {stats.sync_errors}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
