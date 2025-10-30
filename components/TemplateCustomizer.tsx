"use client";

import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Settings,
  Plus,
  X,
  Eye,
  Save,
  RotateCcw,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { api } from "@/lib/api";

interface IndustryTemplate {
  id: number;
  name: string;
  industry_sector: string;
  description: string;
  template_config: {
    default_competitors: string[];
    default_keywords: string[];
    risk_categories: string[];
    kpi_metrics: string[];
  };
  usage_count: number;
  rating: number;
}

interface TemplateCustomization {
  competitors: string[];
  keywords: string[];
  risk_categories: string[];
  kpi_metrics: string[];
  custom_settings: {
    notification_threshold: number;
    update_frequency: string;
    include_social_media: boolean;
    include_financial_data: boolean;
  };
}

interface TemplateCustomizerProps {
  template: IndustryTemplate;
  workspaceId: string;
  onSave: (customization: TemplateCustomization) => void;
  onCancel: () => void;
}

export function TemplateCustomizer({
  template,
  workspaceId,
  onSave,
  onCancel,
}: TemplateCustomizerProps) {
  const [customization, setCustomization] = useState<TemplateCustomization>({
    competitors: [...(template.template_config.default_competitors || [])],
    keywords: [...(template.template_config.default_keywords || [])],
    risk_categories: [...(template.template_config.risk_categories || [])],
    kpi_metrics: [...(template.template_config.kpi_metrics || [])],
    custom_settings: {
      notification_threshold: 70,
      update_frequency: "daily",
      include_social_media: true,
      include_financial_data: true,
    },
  });

  const [newCompetitor, setNewCompetitor] = useState("");
  const [newKeyword, setNewKeyword] = useState("");
  const [newRiskCategory, setNewRiskCategory] = useState("");
  const [newKpiMetric, setNewKpiMetric] = useState("");
  const [showPreview, setShowPreview] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const applyTemplateMutation = useMutation({
    mutationFn: (data: {
      template_id: number;
      workspace_id: string;
      customizations: TemplateCustomization;
    }) => api.post("/api/v1/industry_templates/apply", data),
    onSuccess: () => {
      setSaveMessage("Template applied successfully!");
      queryClient.invalidateQueries({ queryKey: ["workspaceTemplates"] });
      setTimeout(() => {
        setSaveMessage(null);
        onSave(customization);
      }, 2000);
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Failed to apply template";
      setSaveMessage(message);
      setTimeout(() => setSaveMessage(null), 5000);
    },
  });

  const addItem = (
    type: keyof TemplateCustomization,
    value: string,
    setter: (value: string) => void
  ) => {
    if (!value.trim()) return;

    const currentItems = customization[type] as string[];
    if (!currentItems.includes(value.trim())) {
      setCustomization((prev) => ({
        ...prev,
        [type]: [...currentItems, value.trim()],
      }));
    }
    setter("");
  };

  const removeItem = (type: keyof TemplateCustomization, index: number) => {
    const currentItems = customization[type] as string[];
    setCustomization((prev) => ({
      ...prev,
      [type]: currentItems.filter((_, i) => i !== index),
    }));
  };

  const resetToDefaults = () => {
    setCustomization({
      competitors: [...(template.template_config.default_competitors || [])],
      keywords: [...(template.template_config.default_keywords || [])],
      risk_categories: [...(template.template_config.risk_categories || [])],
      kpi_metrics: [...(template.template_config.kpi_metrics || [])],
      custom_settings: {
        notification_threshold: 70,
        update_frequency: "daily",
        include_social_media: true,
        include_financial_data: true,
      },
    });
  };

  const handleSave = () => {
    applyTemplateMutation.mutate({
      template_id: template.id,
      workspace_id: workspaceId,
      customizations: customization,
    });
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <Settings className="w-5 h-5 mr-2 text-blue-600" />
          Customize Template: {template.name}
        </h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            <Eye className="w-4 h-4" />
            <span>{showPreview ? "Hide" : "Show"} Preview</span>
          </button>
          <button
            onClick={resetToDefaults}
            className="flex items-center space-x-2 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {saveMessage && (
        <div
          className={`mb-6 p-4 rounded-lg ${
            saveMessage.includes("successfully")
              ? "bg-green-100 text-green-700 border border-green-200"
              : "bg-red-100 text-red-700 border border-red-200"
          }`}
        >
          <div className="flex items-center">
            {saveMessage.includes("successfully") ? (
              <CheckCircle className="w-4 h-4 mr-2" />
            ) : (
              <AlertCircle className="w-4 h-4 mr-2" />
            )}
            {saveMessage}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Customization Form */}
        <div className="space-y-6">
          {/* Competitors */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Competitors to Monitor
            </label>
            <div className="flex space-x-2 mb-3">
              <input
                type="text"
                value={newCompetitor}
                onChange={(e) => setNewCompetitor(e.target.value)}
                onKeyPress={(e) =>
                  e.key === "Enter" &&
                  addItem("competitors", newCompetitor, setNewCompetitor)
                }
                placeholder="Add competitor..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() =>
                  addItem("competitors", newCompetitor, setNewCompetitor)
                }
                className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {customization.competitors.map((competitor, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                >
                  {competitor}
                  <button
                    onClick={() => removeItem("competitors", index)}
                    className="ml-2 text-blue-500 hover:text-blue-700"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Keywords */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Keywords & Topics
            </label>
            <div className="flex space-x-2 mb-3">
              <input
                type="text"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyPress={(e) =>
                  e.key === "Enter" &&
                  addItem("keywords", newKeyword, setNewKeyword)
                }
                placeholder="Add keyword..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => addItem("keywords", newKeyword, setNewKeyword)}
                className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {customization.keywords.map((keyword, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm"
                >
                  {keyword}
                  <button
                    onClick={() => removeItem("keywords", index)}
                    className="ml-2 text-green-500 hover:text-green-700"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Risk Categories */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Risk Categories
            </label>
            <div className="flex space-x-2 mb-3">
              <input
                type="text"
                value={newRiskCategory}
                onChange={(e) => setNewRiskCategory(e.target.value)}
                onKeyPress={(e) =>
                  e.key === "Enter" &&
                  addItem(
                    "risk_categories",
                    newRiskCategory,
                    setNewRiskCategory
                  )
                }
                placeholder="Add risk category..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() =>
                  addItem(
                    "risk_categories",
                    newRiskCategory,
                    setNewRiskCategory
                  )
                }
                className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {customization.risk_categories.map((category, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm"
                >
                  {category}
                  <button
                    onClick={() => removeItem("risk_categories", index)}
                    className="ml-2 text-orange-500 hover:text-orange-700"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Custom Settings */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-4">
              Monitoring Settings
            </label>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-600 mb-2">
                  Notification Threshold (
                  {customization.custom_settings.notification_threshold}%)
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={customization.custom_settings.notification_threshold}
                  onChange={(e) =>
                    setCustomization((prev) => ({
                      ...prev,
                      custom_settings: {
                        ...prev.custom_settings,
                        notification_threshold: parseInt(e.target.value),
                      },
                    }))
                  }
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-600 mb-2">
                  Update Frequency
                </label>
                <select
                  value={customization.custom_settings.update_frequency}
                  onChange={(e) =>
                    setCustomization((prev) => ({
                      ...prev,
                      custom_settings: {
                        ...prev.custom_settings,
                        update_frequency: e.target.value,
                      },
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={customization.custom_settings.include_social_media}
                    onChange={(e) =>
                      setCustomization((prev) => ({
                        ...prev,
                        custom_settings: {
                          ...prev.custom_settings,
                          include_social_media: e.target.checked,
                        },
                      }))
                    }
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">
                    Include Social Media Monitoring
                  </span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={
                      customization.custom_settings.include_financial_data
                    }
                    onChange={(e) =>
                      setCustomization((prev) => ({
                        ...prev,
                        custom_settings: {
                          ...prev.custom_settings,
                          include_financial_data: e.target.checked,
                        },
                      }))
                    }
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">
                    Include Financial Data
                  </span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Preview Panel */}
        {showPreview && (
          <div className="bg-gray-50 p-6 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-4">
              Configuration Preview
            </h4>
            <div className="space-y-4 text-sm">
              <div>
                <span className="font-medium text-gray-700">Monitoring:</span>
                <div className="text-gray-600 mt-1">
                  {customization.competitors.length} competitors,{" "}
                  {customization.keywords.length} keywords
                </div>
              </div>
              <div>
                <span className="font-medium text-gray-700">
                  Risk Categories:
                </span>
                <div className="text-gray-600 mt-1">
                  {customization.risk_categories.join(", ") || "None"}
                </div>
              </div>
              <div>
                <span className="font-medium text-gray-700">
                  Notifications:
                </span>
                <div className="text-gray-600 mt-1">
                  Threshold:{" "}
                  {customization.custom_settings.notification_threshold}%,
                  Frequency: {customization.custom_settings.update_frequency}
                </div>
              </div>
              <div>
                <span className="font-medium text-gray-700">Data Sources:</span>
                <div className="text-gray-600 mt-1">
                  News, Search
                  {customization.custom_settings.include_social_media
                    ? ", Social Media"
                    : ""}
                  {customization.custom_settings.include_financial_data
                    ? ", Financial Data"
                    : ""}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-8 flex justify-end space-x-4">
        <button
          onClick={onCancel}
          className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={applyTemplateMutation.isPending}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
        >
          {applyTemplateMutation.isPending ? (
            <>
              <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
              <span>Applying...</span>
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              <span>Apply Template</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
