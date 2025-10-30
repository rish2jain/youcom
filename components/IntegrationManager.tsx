"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  CheckCircle,
  XCircle,
  Settings,
  Plus,
  Trash2,
  ExternalLink,
} from "lucide-react";

interface Integration {
  id: number;
  name: string;
  type: string;
  is_active: boolean;
  is_verified: boolean;
  last_sync_at: string | null;
  total_syncs: number;
  successful_syncs: number;
  failed_syncs: number;
  created_at: string;
}

interface NotionDatabase {
  id: string;
  title: string;
  url: string;
}

interface IntegrationManagerProps {
  workspaceId?: string;
}

export function IntegrationManager({
  workspaceId = "1",
}: IntegrationManagerProps) {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);

  // Form states
  const [integrationType, setIntegrationType] = useState<string>("");
  const [integrationName, setIntegrationName] = useState("");
  const [notionToken, setNotionToken] = useState("");
  const [notionDatabases, setNotionDatabases] = useState<NotionDatabase[]>([]);
  const [selectedDatabase, setSelectedDatabase] = useState("");
  const [salesforceUrl, setSalesforceUrl] = useState("");
  const [salesforceToken, setSalesforceToken] = useState("");

  const fetchIntegrations = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/integrations/?workspace_id=${workspaceId}`
      );
      if (!response.ok) throw new Error("Failed to fetch integrations");

      const data = await response.json();
      setIntegrations(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load integrations"
      );
    } finally {
      setLoading(false);
    }
  };

  const testNotionConnection = async () => {
    if (!notionToken) return;

    setLoading(true);
    try {
      const response = await fetch("/api/v1/integrations/notion/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_token: notionToken }),
      });

      if (response.ok) {
        const result = await response.json();
        alert(`✅ Connected to Notion as ${result.user}`);

        // Fetch databases
        const dbResponse = await fetch(
          "/api/v1/integrations/notion/databases",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_token: notionToken }),
          }
        );

        if (dbResponse.ok) {
          const dbResult = await dbResponse.json();
          setNotionDatabases(dbResult.databases);
        }
      } else {
        const error = await response.json();
        alert(`❌ Connection failed: ${error.detail}`);
      }
    } catch (err) {
      alert(`❌ Connection failed: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const testSalesforceConnection = async () => {
    if (!salesforceUrl || !salesforceToken) return;

    setLoading(true);
    try {
      const response = await fetch("/api/v1/integrations/salesforce/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          instance_url: salesforceUrl,
          access_token: salesforceToken,
        }),
      });

      if (response.ok) {
        alert("✅ Connected to Salesforce successfully!");
      } else {
        const error = await response.json();
        alert(`❌ Connection failed: ${error.detail}`);
      }
    } catch (err) {
      alert(`❌ Connection failed: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const createIntegration = async () => {
    if (!integrationName || !integrationType) return;

    let config = {};
    let credentials = {};

    if (integrationType === "notion") {
      if (!notionToken) {
        // TODO: Replace with toast notification
        alert("Please provide Notion API token");
        return;
      }
      config = { database_id: selectedDatabase };
      credentials = { api_token: notionToken };
    } else if (integrationType === "salesforce") {
      if (!salesforceUrl || !salesforceToken) {
        // TODO: Replace with toast notification
        alert("Please provide Salesforce URL and token");
        return;
      }
      config = {};
      credentials = {
        instance_url: salesforceUrl,
        access_token: salesforceToken,
      };
    }

    setLoading(true);
    try {
      const response = await fetch("/api/v1/integrations/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspace_id: workspaceId,
          name: integrationName,
          integration_type: integrationType,
          config,
          credentials,
        }),
      });

      if (response.ok) {
        setShowAddDialog(false);
        resetForm();
        fetchIntegrations();
        // TODO: Replace with toast notification
        alert("✅ Integration created successfully!");
      } else {
        const error = await response.json();
        // TODO: Replace with toast notification
        alert(
          `❌ Failed to create integration: ${error.detail || "Unknown error"}`
        );
      }
    } catch (err) {
      // TODO: Replace with toast notification
      alert(
        `❌ Failed to create integration: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
    } finally {
      setLoading(false);
    }
  };

  const deleteIntegration = async (id: number) => {
    if (!confirm("Are you sure you want to delete this integration?")) return;

    try {
      const response = await fetch(`/api/v1/integrations/${id}`, {
        method: "DELETE",
      });

      if (response.ok) {
        fetchIntegrations();
        alert("✅ Integration deleted successfully!");
      } else {
        alert("❌ Failed to delete integration");
      }
    } catch (err) {
      alert(`❌ Failed to delete integration: ${err}`);
    }
  };

  const resetForm = () => {
    setIntegrationType("");
    setIntegrationName("");
    setNotionToken("");
    setNotionDatabases([]);
    setSelectedDatabase("");
    setSalesforceUrl("");
    setSalesforceToken("");
  };

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const getStatusBadge = (integration: Integration) => {
    if (!integration.is_active) {
      return <Badge variant="secondary">Inactive</Badge>;
    }
    if (!integration.is_verified) {
      return <Badge variant="destructive">Unverified</Badge>;
    }
    return (
      <Badge variant="default" className="bg-green-500">
        Active
      </Badge>
    );
  };

  const getSuccessRate = (integration: Integration) => {
    if (integration.total_syncs === 0) return 0;
    return Math.round(
      (integration.successful_syncs / integration.total_syncs) * 100
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Integration Management</h2>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Add Integration
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Add New Integration</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Integration Name</Label>
                <Input
                  id="name"
                  value={integrationName}
                  onChange={(e) => setIntegrationName(e.target.value)}
                  placeholder="e.g., Marketing Notion Workspace"
                />
              </div>

              <div>
                <Label htmlFor="type">Integration Type</Label>
                <Select
                  value={integrationType}
                  onValueChange={setIntegrationType}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select integration type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="notion">Notion</SelectItem>
                    <SelectItem value="salesforce">Salesforce</SelectItem>
                    <SelectItem value="microsoft_teams">
                      Microsoft Teams
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {integrationType === "notion" && (
                <Tabs defaultValue="setup" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="setup">Setup</TabsTrigger>
                    <TabsTrigger value="database">Database</TabsTrigger>
                  </TabsList>
                  <TabsContent value="setup" className="space-y-4">
                    <div>
                      <Label htmlFor="notion-token">Notion API Token</Label>
                      <Input
                        id="notion-token"
                        type="password"
                        value={notionToken}
                        onChange={(e) => setNotionToken(e.target.value)}
                        placeholder="secret_..."
                      />
                    </div>
                    <Button
                      onClick={testNotionConnection}
                      disabled={!notionToken || loading}
                    >
                      Test Connection
                    </Button>
                  </TabsContent>
                  <TabsContent value="database" className="space-y-4">
                    {notionDatabases.length > 0 ? (
                      <div>
                        <Label htmlFor="database">Select Database</Label>
                        <Select
                          value={selectedDatabase}
                          onValueChange={setSelectedDatabase}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Choose a database" />
                          </SelectTrigger>
                          <SelectContent>
                            {notionDatabases.map((db) => (
                              <SelectItem key={db.id} value={db.id}>
                                {db.title}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500">
                        Test connection first to load available databases
                      </p>
                    )}
                  </TabsContent>
                </Tabs>
              )}

              {integrationType === "salesforce" && (
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="sf-url">Salesforce Instance URL</Label>
                    <Input
                      id="sf-url"
                      value={salesforceUrl}
                      onChange={(e) => setSalesforceUrl(e.target.value)}
                      placeholder="https://your-domain.salesforce.com"
                    />
                  </div>
                  <div>
                    <Label htmlFor="sf-token">Access Token</Label>
                    <Input
                      id="sf-token"
                      type="password"
                      value={salesforceToken}
                      onChange={(e) => setSalesforceToken(e.target.value)}
                      placeholder="Your Salesforce access token"
                    />
                  </div>
                  <Button
                    onClick={testSalesforceConnection}
                    disabled={!salesforceUrl || !salesforceToken || loading}
                  >
                    Test Connection
                  </Button>
                </div>
              )}

              {integrationType === "microsoft_teams" && (
                <div className="p-4 bg-yellow-50 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    Microsoft Teams integration is coming soon. Please check
                    back later.
                  </p>
                </div>
              )}

              <div className="flex justify-end space-x-2">
                <Button
                  variant="outline"
                  onClick={() => setShowAddDialog(false)}
                >
                  Cancel
                </Button>
                <Button onClick={createIntegration} disabled={loading}>
                  Create Integration
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-600">{error}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {integrations.map((integration) => (
          <Card key={integration.id}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {integration.name}
              </CardTitle>
              <div className="flex items-center space-x-2">
                {getStatusBadge(integration)}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => deleteIntegration(integration.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span>Type:</span>
                  <Badge variant="outline">{integration.type}</Badge>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Success Rate:</span>
                  <span className="font-medium">
                    {getSuccessRate(integration)}%
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Total Syncs:</span>
                  <span className="font-medium">{integration.total_syncs}</span>
                </div>
                {integration.last_sync_at && (
                  <div className="text-xs text-gray-500">
                    Last sync:{" "}
                    {new Date(integration.last_sync_at).toLocaleDateString()}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {integrations.length === 0 && !loading && (
        <Card>
          <CardContent className="pt-6 text-center">
            <Settings className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No Integrations Yet</h3>
            <p className="text-gray-500 mb-4">
              Connect your favorite tools to sync competitive intelligence data
              automatically.
            </p>
            <Button onClick={() => setShowAddDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Integration
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
