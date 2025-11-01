"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertTriangle,
  AlertCircle,
  XCircle,
  CheckCircle,
  User,
  Clock,
  Target,
  Brain,
  Shield,
  TrendingDown,
  HelpCircle,
  Zap,
  FileText,
  Users,
} from "lucide-react";

interface UncertaintyDetection {
  id: number;
  uncertainty_type: string;
  uncertainty_level: string;
  confidence_threshold: number;
  affected_components: string[];
  uncertainty_description: string;
  human_validation_required: boolean;
  recommended_actions: string[];
  validation_priority: string;
  is_resolved: boolean;
  resolution_method?: string;
  resolved_by?: string;
  resolved_at?: string;
  created_at: string;
}

interface UncertaintyDetectionPanelProps {
  impactCardId: number;
  uncertaintyDetections: UncertaintyDetection[];
  onRequestValidation?: (
    uncertaintyIds: number[],
    priority: string,
    notes?: string
  ) => void;
  onResolveUncertainty?: (uncertaintyId: number, resolution: any) => void;
  onRefresh?: () => void;
}

const UncertaintyDetectionPanel: React.FC<UncertaintyDetectionPanelProps> = ({
  impactCardId,
  uncertaintyDetections,
  onRequestValidation,
  onResolveUncertainty,
  onRefresh,
}) => {
  const [selectedUncertainties, setSelectedUncertainties] = useState<
    Set<number>
  >(new Set());
  const [validationNotes, setValidationNotes] = useState("");
  const [activeTab, setActiveTab] = useState("overview");

  // Group uncertainties by level and status
  const unresolvedUncertainties = uncertaintyDetections.filter(
    (u) => !u.is_resolved
  );
  const resolvedUncertainties = uncertaintyDetections.filter(
    (u) => u.is_resolved
  );
  const criticalUncertainties = unresolvedUncertainties.filter(
    (u) => u.uncertainty_level === "critical"
  );
  const highUncertainties = unresolvedUncertainties.filter(
    (u) => u.uncertainty_level === "high"
  );
  const mediumUncertainties = unresolvedUncertainties.filter(
    (u) => u.uncertainty_level === "medium"
  );
  const lowUncertainties = unresolvedUncertainties.filter(
    (u) => u.uncertainty_level === "low"
  );

  const requiresValidation = unresolvedUncertainties.filter(
    (u) => u.human_validation_required
  );

  const getUncertaintyLevelColor = (level: string) => {
    switch (level) {
      case "critical":
        return "text-red-600 bg-red-50 border-red-200";
      case "high":
        return "text-orange-600 bg-orange-50 border-orange-200";
      case "medium":
        return "text-yellow-600 bg-yellow-50 border-yellow-200";
      case "low":
        return "text-blue-600 bg-blue-50 border-blue-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getUncertaintyIcon = (type: string) => {
    switch (type) {
      case "low_confidence":
        return Brain;
      case "conflicting_evidence":
        return AlertTriangle;
      case "insufficient_data":
        return FileText;
      case "high_impact_low_evidence":
        return Target;
      case "data_quality":
        return Shield;
      default:
        return HelpCircle;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "urgent":
        return "text-red-600 bg-red-100 border-red-300";
      case "high":
        return "text-orange-600 bg-orange-100 border-orange-300";
      case "medium":
        return "text-yellow-600 bg-yellow-100 border-yellow-300";
      case "low":
        return "text-blue-600 bg-blue-100 border-blue-300";
      default:
        return "text-gray-600 bg-gray-100 border-gray-300";
    }
  };

  const formatUncertaintyType = (type: string) => {
    return type
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const toggleUncertaintySelection = (uncertaintyId: number) => {
    const newSelected = new Set(selectedUncertainties);
    if (newSelected.has(uncertaintyId)) {
      newSelected.delete(uncertaintyId);
    } else {
      newSelected.add(uncertaintyId);
    }
    setSelectedUncertainties(newSelected);
  };

  const handleRequestValidation = () => {
    if (selectedUncertainties.size === 0) return;

    const selectedArray = Array.from(selectedUncertainties);
    const highestPriority = selectedArray.reduce((highest, id) => {
      const uncertainty = uncertaintyDetections.find((u) => u.id === id);
      if (!uncertainty) return highest;

      const priorities = ["low", "medium", "high", "urgent"];
      const currentIndex = priorities.indexOf(uncertainty.validation_priority);
      const highestIndex = priorities.indexOf(highest);

      return currentIndex > highestIndex
        ? uncertainty.validation_priority
        : highest;
    }, "low");

    onRequestValidation?.(selectedArray, highestPriority, validationNotes);
    setSelectedUncertainties(new Set());
    setValidationNotes("");
  };

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <AlertTriangle className="w-6 h-6 text-orange-600" />
            <span>Uncertainty Detection & Validation</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">
                {criticalUncertainties.length}
              </p>
              <p className="text-sm text-gray-600">Critical</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">
                {highUncertainties.length}
              </p>
              <p className="text-sm text-gray-600">High</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-600">
                {mediumUncertainties.length}
              </p>
              <p className="text-sm text-gray-600">Medium</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">
                {lowUncertainties.length}
              </p>
              <p className="text-sm text-gray-600">Low</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {resolvedUncertainties.length}
              </p>
              <p className="text-sm text-gray-600">Resolved</p>
            </div>
          </div>

          {requiresValidation.length > 0 && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <User className="w-5 h-5 text-red-600" />
                <span className="font-medium text-red-800">
                  Human Validation Required
                </span>
              </div>
              <p className="text-sm text-red-700">
                {requiresValidation.length} uncertainty detection(s) require
                human validation for reliable analysis.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="unresolved">
            Unresolved ({unresolvedUncertainties.length})
          </TabsTrigger>
          <TabsTrigger value="validation">Validation</TabsTrigger>
          <TabsTrigger value="resolved">
            Resolved ({resolvedUncertainties.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Uncertainty Types Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Uncertainty Types</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(
                  unresolvedUncertainties.reduce((acc, u) => {
                    acc[u.uncertainty_type] =
                      (acc[u.uncertainty_type] || 0) + 1;
                    return acc;
                  }, {} as Record<string, number>)
                ).map(([type, count]) => {
                  const UncertaintyIcon = getUncertaintyIcon(type);
                  return (
                    <div
                      key={type}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <UncertaintyIcon className="w-5 h-5 text-gray-600" />
                        <div>
                          <p className="font-medium">
                            {formatUncertaintyType(type)}
                          </p>
                          <p className="text-sm text-gray-600">
                            {type === "low_confidence" &&
                              "Analysis confidence below acceptable thresholds"}
                            {type === "conflicting_evidence" &&
                              "Sources provide contradictory information"}
                            {type === "insufficient_data" &&
                              "Limited data available for reliable analysis"}
                            {type === "high_impact_low_evidence" &&
                              "High-impact factors with insufficient evidence"}
                            {type === "data_quality" &&
                              "Quality of underlying data is questionable"}
                          </p>
                        </div>
                      </div>
                      <Badge variant="outline">{count}</Badge>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Priority Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Validation Priority Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {["urgent", "high", "medium", "low"].map((priority) => {
                  const count = unresolvedUncertainties.filter(
                    (u) => u.validation_priority === priority
                  ).length;
                  return (
                    <div
                      key={priority}
                      className={`text-center p-4 rounded-lg border ${getPriorityColor(
                        priority
                      )}`}
                    >
                      <p className="text-2xl font-bold">{count}</p>
                      <p className="text-sm capitalize">{priority} Priority</p>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="unresolved" className="space-y-4">
          {unresolvedUncertainties.length > 0 ? (
            <div className="space-y-4">
              {unresolvedUncertainties
                .sort((a, b) => {
                  const priorities = ["low", "medium", "high", "urgent"];
                  return (
                    priorities.indexOf(b.validation_priority) -
                    priorities.indexOf(a.validation_priority)
                  );
                })
                .map((uncertainty) => {
                  const UncertaintyIcon = getUncertaintyIcon(
                    uncertainty.uncertainty_type
                  );
                  const isSelected = selectedUncertainties.has(uncertainty.id);

                  return (
                    <Card
                      key={uncertainty.id}
                      className={`${
                        isSelected ? "border-blue-500 bg-blue-50" : ""
                      }`}
                    >
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() =>
                                toggleUncertaintySelection(uncertainty.id)
                              }
                              className="mt-1"
                            />
                            <UncertaintyIcon className="w-5 h-5 text-gray-600 mt-1" />
                            <div>
                              <CardTitle className="text-lg">
                                {formatUncertaintyType(
                                  uncertainty.uncertainty_type
                                )}
                              </CardTitle>
                              <div className="flex items-center space-x-2 mt-1">
                                <Badge
                                  className={getUncertaintyLevelColor(
                                    uncertainty.uncertainty_level
                                  )}
                                >
                                  {uncertainty.uncertainty_level.toUpperCase()}
                                </Badge>
                                <Badge
                                  className={getPriorityColor(
                                    uncertainty.validation_priority
                                  )}
                                >
                                  {uncertainty.validation_priority.toUpperCase()}{" "}
                                  PRIORITY
                                </Badge>
                                {uncertainty.human_validation_required && (
                                  <Badge className="bg-red-100 text-red-800 border-red-200">
                                    <User className="w-3 h-3 mr-1" />
                                    VALIDATION REQUIRED
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="text-right text-sm text-gray-500">
                            <p>
                              Threshold:{" "}
                              {(uncertainty.confidence_threshold * 100).toFixed(
                                0
                              )}
                              %
                            </p>
                            <p>
                              {new Date(
                                uncertainty.created_at
                              ).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div>
                            <h4 className="font-medium mb-2">Description</h4>
                            <p className="text-sm text-gray-700">
                              {uncertainty.uncertainty_description}
                            </p>
                          </div>

                          {uncertainty.affected_components.length > 0 && (
                            <div>
                              <h4 className="font-medium mb-2">
                                Affected Components
                              </h4>
                              <div className="flex flex-wrap gap-1">
                                {uncertainty.affected_components.map(
                                  (component, index) => (
                                    <Badge
                                      key={index}
                                      variant="outline"
                                      className="text-xs"
                                    >
                                      {component}
                                    </Badge>
                                  )
                                )}
                              </div>
                            </div>
                          )}

                          {uncertainty.recommended_actions.length > 0 && (
                            <div>
                              <h4 className="font-medium mb-2">
                                Recommended Actions
                              </h4>
                              <ul className="space-y-1">
                                {uncertainty.recommended_actions.map(
                                  (action, index) => (
                                    <li
                                      key={index}
                                      className="text-sm text-gray-700 flex items-start space-x-2"
                                    >
                                      <Zap className="w-3 h-3 text-yellow-500 mt-0.5 flex-shrink-0" />
                                      <span>{action.replace(/_/g, " ")}</span>
                                    </li>
                                  )
                                )}
                              </ul>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Unresolved Uncertainties
                </h3>
                <p className="text-gray-600">
                  All uncertainty detections have been resolved or are within
                  acceptable thresholds.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="validation" className="space-y-4">
          {/* Validation Request Panel */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Users className="w-5 h-5" />
                <span>Request Human Validation</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {selectedUncertainties.size > 0 ? (
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium mb-2">
                      Selected Uncertainties ({selectedUncertainties.size})
                    </h4>
                    <div className="space-y-2">
                      {Array.from(selectedUncertainties).map((id) => {
                        const uncertainty = uncertaintyDetections.find(
                          (u) => u.id === id
                        );
                        if (!uncertainty) return null;

                        return (
                          <div
                            key={id}
                            className="flex items-center justify-between p-2 bg-gray-50 rounded"
                          >
                            <span className="text-sm">
                              {formatUncertaintyType(
                                uncertainty.uncertainty_type
                              )}
                            </span>
                            <Badge
                              className={getUncertaintyLevelColor(
                                uncertainty.uncertainty_level
                              )}
                            >
                              {uncertainty.uncertainty_level}
                            </Badge>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">
                      Validation Notes (Optional)
                    </label>
                    <textarea
                      value={validationNotes}
                      onChange={(e) => setValidationNotes(e.target.value)}
                      placeholder="Add any additional context or specific questions for the validator..."
                      className="w-full p-3 border border-gray-300 rounded-lg resize-none"
                      rows={3}
                    />
                  </div>

                  <Button onClick={handleRequestValidation} className="w-full">
                    <User className="w-4 h-4 mr-2" />
                    Request Human Validation
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8">
                  <User className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Select Uncertainties for Validation
                  </h3>
                  <p className="text-gray-600">
                    Go to the "Unresolved" tab and select the uncertainties
                    you'd like to have validated by a human expert.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Validation Guidelines */}
          <Card>
            <CardHeader>
              <CardTitle>Validation Guidelines</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">
                    When to Request Validation
                  </h4>
                  <ul className="space-y-1 text-sm text-gray-700">
                    <li>
                      • Critical or high-level uncertainties affecting key
                      decisions
                    </li>
                    <li>
                      • Conflicting evidence from multiple authoritative sources
                    </li>
                    <li>• Low confidence scores on high-impact factors</li>
                    <li>• Insufficient data for reliable automated analysis</li>
                  </ul>
                </div>

                <div>
                  <h4 className="font-medium mb-2">Validation Process</h4>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                    <div className="text-center p-3 bg-blue-50 rounded">
                      <Clock className="w-6 h-6 text-blue-600 mx-auto mb-1" />
                      <p className="font-medium">1. Request</p>
                      <p className="text-gray-600">Submit validation request</p>
                    </div>
                    <div className="text-center p-3 bg-yellow-50 rounded">
                      <User className="w-6 h-6 text-yellow-600 mx-auto mb-1" />
                      <p className="font-medium">2. Review</p>
                      <p className="text-gray-600">Expert reviews analysis</p>
                    </div>
                    <div className="text-center p-3 bg-green-50 rounded">
                      <CheckCircle className="w-6 h-6 text-green-600 mx-auto mb-1" />
                      <p className="font-medium">3. Validate</p>
                      <p className="text-gray-600">Expert provides feedback</p>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded">
                      <Zap className="w-6 h-6 text-purple-600 mx-auto mb-1" />
                      <p className="font-medium">4. Update</p>
                      <p className="text-gray-600">Analysis is updated</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="resolved" className="space-y-4">
          {resolvedUncertainties.length > 0 ? (
            <div className="space-y-4">
              {resolvedUncertainties.map((uncertainty) => {
                const UncertaintyIcon = getUncertaintyIcon(
                  uncertainty.uncertainty_type
                );

                return (
                  <Card
                    key={uncertainty.id}
                    className="border-green-200 bg-green-50"
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-3">
                          <CheckCircle className="w-5 h-5 text-green-600 mt-1" />
                          <div>
                            <CardTitle className="text-lg text-green-800">
                              {formatUncertaintyType(
                                uncertainty.uncertainty_type
                              )}
                            </CardTitle>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge className="bg-green-100 text-green-800 border-green-200">
                                RESOLVED
                              </Badge>
                              {uncertainty.resolution_method && (
                                <Badge variant="outline" className="text-xs">
                                  {uncertainty.resolution_method.replace(
                                    /_/g,
                                    " "
                                  )}
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-right text-sm text-gray-600">
                          {uncertainty.resolved_by && (
                            <p>Resolved by: {uncertainty.resolved_by}</p>
                          )}
                          {uncertainty.resolved_at && (
                            <p>
                              {new Date(
                                uncertainty.resolved_at
                              ).toLocaleDateString()}
                            </p>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-green-700">
                        {uncertainty.uncertainty_description}
                      </p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <HelpCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No Resolved Uncertainties
                </h3>
                <p className="text-gray-600">
                  Resolved uncertainties will appear here once validation is
                  complete.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Refresh Button */}
      {onRefresh && (
        <div className="flex justify-end">
          <Button onClick={onRefresh} variant="outline">
            <AlertTriangle className="w-4 h-4 mr-2" />
            Refresh Detection
          </Button>
        </div>
      )}
    </div>
  );
};

export default UncertaintyDetectionPanel;
