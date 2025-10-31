"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ExternalLink,
  CheckCircle,
  AlertTriangle,
  Settings,
  RefreshCw,
  Key,
  Users,
  Workflow,
} from "lucide-react";
import { api } from "@/lib/api";

interface HubSpotIntegration {
  id: number;
  workspace_id: string;
  hubspot_portal_id: string;
  sync_enabled: boolean;
  last_sync: string;
  sync_status: "active" | "error" | "pending";
  custom_properties_created: string[];
  workflow_mappings: Record<string, any>;
  created_at: string;
  error_message?: string;
}

interface HubSpotOAuthState {
  auth_url: string;
  state: string;
}

interface SyncStats {
  contacts_synced: number;
  companies_synced: number;
  deals_synced: number;
  last_sync_duration: number;
  sync_errors: number;
}

export function HubSpotIntegrationSetup() {
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [customProperties, setCustomProperties] = useState<string[]>([
    "competitive_risk_score",
    "market_position",
    "intelligence_alerts",
  ]);
  const [workflowMappings, setWorkflowMappings] = useState<
    Record<string, string>
  >({
    high_risk_competitor: "",
    new_product_launch: "",
    pricing_change: "",
  });

  const queryClient = useQueryClient();

  const { data: integration, isLoading: integrationLoading } = useQuery({
    queryKey: ["hubspotIntegration"],
    queryFn: () =>
      api.get("/api/v1/hubspot_integration/").then((res) => res.data),
    staleTime: 60000, // 1 minute
  });

  const { data: syncStats, isLoading: statsLoading } = useQuery({
    queryKey: ["hubspotSyncStats"],
    queryFn: () =>
      api.get("/api/v1/hubspot_integration/stats").then((res) => res.data),
    enabled: !!integration,
    staleTime: 30000,
  });

  const { data: oauthState, isLoading: oauthLoading } = useQuery({
    queryKey: ["hubspotOAuth"],
    queryFn: () =>
      api.get("/api/v1/hubspot_integration/oauth/init").then((res) => res.data),
    enabled: !integration,
    staleTime: 300000, // 5 minutes
  });

  const setupMutation = useMutation({
    mutationFn: (data: {
      custom_properties: string[];
      workflow_mappings: Record<string, string>;
    }) => api.post("/api/v1/hubspot_integration/setup", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hubspotIntegration"] });
    },
  });

  const syncMutation = useMutation({
    mutationFn: () => api.post("/api/v1/hubspot_integration/sync"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hubspotSyncStats"] });
      queryClient.invalidateQueries({ queryKey: ["hubspotIntegration"] });
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: () => api.delete("/api/v1/hubspot_integration/"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hubspotIntegration"] });
    },
  });

  const toggleSyncMutation = useMutation({
    mutationFn: (enabled: boolean) =>
      api.put("/api/v1/hubspot_integration/", { sync_enabled: enabled }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hubspotIntegration"] });
    },
  });

  const addCustomProperty = () => {
    const newProperty = prompt("Enter custom property name:");
    if (newProperty && !customProperties.includes(newProperty)) {
      setCustomProperties([...customProperties, newProperty]);
    }
  };

  const removeCustomProperty = (property: string) => {
    setCustomProperties(customProperties.filter((p) => p !== property));
  };

  const handleWorkflowMappingChange = (trigger: string, workflowId: string) => {
    setWorkflowMappings((prev) => ({
      ...prev,
      [trigger]: workflowId,
    }));
  };

  const handleSetup = () => {
    setupMutation.mutate({
      custom_properties: customProperties,
      workflow_mappings: workflowMappings,
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

  if (integrationLoading || oauthLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  // Safe handling of potentially undefined data
  if (!integration || !syncStats || !oauthState) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="text-center text-gray-500">
          Integration data not available
        </div>
      </div>
    );
  }

  const integrationData = integration;
  const stats = syncStats;
  const oauth = oauthState;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <div className="w-8 h-8 mr-3 bg-orange-500 rounded flex items-center justify-center">
              <span className="text-white font-bold text-sm">H</span>
            </div>
            HubSpot CRM Integration
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
              <div className="w-16 h-16 mx-auto mb-4 bg-orange-100 rounded-full flex items-center justify-center">
                <div className="w-8 h-8 bg-orange-500 rounded flex items-center justify-center">
                  <span className="text-white font-bold">H</span>
                </div>
              </div>
              <h4 className="text-xl font-semibold text-gray-900 mb-2">
                Connect HubSpot CRM
              </h4>
              <p className="text-gray-600 mb-6">
                Sync competitive intelligence data with your HubSpot contacts
                and companies. Automatically enrich leads and trigger workflows
                based on competitive events.
              </p>
            </div>

            {/* Benefits */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <Users className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                <h5 className="font-semibold text-gray-900 mb-1">
                  Lead Enrichment
                </h5>
                <p className="text-sm text-gray-600">
                  Automatically add competitive intelligence to new leads
                </p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <Workflow className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <h5 className="font-semibold text-gray-900 mb-1">
                  Workflow Automation
                </h5>
                <p className="text-sm text-gray-600">
                  Trigger actions when competitive events affect prospects
                </p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <RefreshCw className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                <h5 className="font-semibold text-gray-900 mb-1">
                  Real-time Sync
                </h5>
                <p className="text-sm text-gray-600">
                  Bidirectional sync within 5 minutes of updates
                </p>
              </div>
            </div>

            {/* Configuration */}
            <div className="space-y-6">
              <div>
                <h5 className="font-semibold text-gray-900 mb-4">
                  Custom Properties
                </h5>
                <p className="text-sm text-gray-600 mb-4">
                  These properties will be created in your HubSpot account to
                  store competitive intelligence data.
                </p>
                <div className="space-y-2">
                  {customProperties.map((property) => (
                    <div
                      key={property}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <span className="font-medium text-gray-900">
                        {property}
                      </span>
                      <button
                        onClick={() => removeCustomProperty(property)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={addCustomProperty}
                    className="w-full p-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-800"
                  >
                    + Add Custom Property
                  </button>
                </div>
              </div>

              <div>
                <button
                  onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                  className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-800"
                >
                  <Settings className="w-4 h-4" />
                  <span>Advanced Settings</span>
                </button>

                {showAdvancedSettings && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h6 className="font-semibold text-gray-900 mb-3">
                      Workflow Mappings
                    </h6>
                    <p className="text-sm text-gray-600 mb-4">
                      Map competitive intelligence events to HubSpot workflow
                      IDs.
                    </p>
                    <div className="space-y-3">
                      {Object.entries(workflowMappings).map(
                        ([trigger, workflowId]) => (
                          <div
                            key={trigger}
                            className="flex items-center space-x-3"
                          >
                            <label className="flex-1 text-sm font-medium text-gray-700 capitalize">
                              {trigger.replace("_", " ")}:
                            </label>
                            <input
                              type="text"
                              value={workflowId}
                              onChange={(e) =>
                                handleWorkflowMappingChange(
                                  trigger,
                                  e.target.value
                                )
                              }
                              placeholder="Workflow ID (optional)"
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* OAuth Button */}
            <div className="text-center">
              {oauth?.auth_url ? (
                <a
                  href={oauth.auth_url}
                  className="inline-flex items-center space-x-2 px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-medium"
                >
                  <Key className="w-5 h-5" />
                  <span>Connect to HubSpot</span>
                  <ExternalLink className="w-4 h-4" />
                </a>
              ) : (
                <button
                  onClick={handleSetup}
                  disabled={setupMutation.isPending}
                  className="inline-flex items-center space-x-2 px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-medium disabled:opacity-50"
                >
                  {setupMutation.isPending ? (
                    <>
                      <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
                      <span>Setting up...</span>
                    </>
                  ) : (
                    <>
                      <Key className="w-5 h-5" />
                      <span>Setup Integration</span>
                    </>
                  )}
                </button>
              )}
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
                <div className="text-sm text-gray-600">
                  Portal: {integrationData.hubspot_portal_id}
                </div>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {stats?.contacts_synced || 0}
                </div>
                <div className="text-sm text-gray-600">Contacts Synced</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {stats?.companies_synced || 0}
                </div>
                <div className="text-sm text-gray-600">Companies Synced</div>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <div className="text-2xl font-bold text-orange-600">
                  {stats?.deals_synced || 0}
                </div>
                <div className="text-sm text-gray-600">Deals Synced</div>
              </div>
            </div>

            {/* Sync Controls */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium text-gray-900">Automatic Sync</div>
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
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
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

            {/* Custom Properties */}
            <div>
              <h5 className="font-semibold text-gray-900 mb-3">
                Custom Properties Created
              </h5>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {integrationData.custom_properties_created.map(
                  (property: string) => (
                    <div
                      key={property}
                      className="p-3 bg-green-50 rounded-lg border border-green-200"
                    >
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-gray-900">
                          {property}
                        </span>
                      </div>
                    </div>
                  )
                )}
              </div>
            </div>

            {/* Workflow Mappings */}
            {Object.keys(integrationData.workflow_mappings).length > 0 && (
              <div>
                <h5 className="font-semibold text-gray-900 mb-3">
                  Active Workflow Mappings
                </h5>
                <div className="space-y-2">
                  {Object.entries(integrationData.workflow_mappings).map(
                    ([trigger, workflowId]) => (
                      <div
                        key={trigger}
                        className="flex items-center justify-between p-3 bg-blue-50 rounded-lg"
                      >
                        <span className="font-medium text-gray-900 capitalize">
                          {trigger.replace("_", " ")}
                        </span>
                        <span className="text-sm text-gray-600">
                          Workflow ID: {String(workflowId)}
                        </span>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

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
                  <div>
                    <span className="font-medium text-gray-700">
                      Success Rate:
                    </span>
                    <span className="ml-2 text-green-600">
                      {stats.sync_errors === 0
                        ? "100%"
                        : `${Math.round(
                            (1 -
                              stats.sync_errors /
                                (stats.contacts_synced +
                                  stats.companies_synced +
                                  stats.deals_synced)) *
                              100
                          )}%`}
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
