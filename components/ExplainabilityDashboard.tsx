"use client";

import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Brain,
  Shield,
  AlertTriangle,
  TrendingUp,
  RefreshCw,
  CheckCircle,
  XCircle,
  Info,
  Zap,
  Eye,
  Download,
} from "lucide-react";

import ReasoningChainVisualization from "./ReasoningChainVisualization";
import SourceQualityVisualization from "./SourceQualityVisualization";
import UncertaintyDetectionPanel from "./UncertaintyDetectionPanel";
import { backendApi } from "@/lib/api";

interface ExplainabilityDashboardProps {
  impactCardId: number;
  riskScore: number;
  onGenerateExplainability?: () => void;
  onRequestValidation?: (
    uncertaintyIds: number[],
    priority: string,
    notes?: string
  ) => void;
}

const ExplainabilityDashboard: React.FC<ExplainabilityDashboardProps> = ({
  impactCardId,
  riskScore,
  onGenerateExplainability,
  onRequestValidation,
}) => {
  const [activeTab, setActiveTab] = useState("overview");

  // Fetch explainability data from API
  const {
    data: explainabilityData,
    isLoading: loading,
    error: explainabilityError,
    refetch: refetchExplainability,
  } = useQuery({
    queryKey: ["explainability", impactCardId],
    queryFn: async () => {
      try {
        const response = await backendApi.get(
          `/api/v1/explainability/${impactCardId}`
        );
        return response.data;
      } catch (error: any) {
        // If explainability doesn't exist yet, return null instead of throwing
        if (error?.response?.status === 404) {
          return null;
        }
        throw error;
      }
    },
    enabled: !!impactCardId,
    staleTime: 60 * 1000, // 1 minute
    retry: 1,
  });


  const handleGenerateExplainability = async () => {
    try {
      // Call API to generate explainability
      await backendApi.post(`/api/v1/explainability/${impactCardId}/generate`);
      // Refetch the data after generation
      await refetchExplainability();
      onGenerateExplainability?.();
    } catch (error) {
      console.error("Failed to generate explainability:", error);
      // Show error to user
      alert("Failed to generate explainability. Please try again.");
    }
  };

  const handleRefresh = () => {
    refetchExplainability();
  };

  const handleRequestValidation = (
    uncertaintyIds: number[],
    priority: string,
    notes?: string
  ) => {
    console.log(
      "Requesting validation for uncertainties:",
      uncertaintyIds,
      "Priority:",
      priority,
      "Notes:",
      notes
    );
    onRequestValidation?.(uncertaintyIds, priority, notes);
  };

  // Note: Explainability data is now fetched via useQuery, so we don't need to auto-generate on mount
  // Users can manually trigger generation if needed

  if (loading && !explainabilityData) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">
              Generating Explainability Analysis
            </h3>
            <p className="text-gray-600">
              Creating reasoning chains, analyzing source quality, and detecting
              uncertainties...
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!loading && !explainabilityData && !explainabilityError) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <Brain className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Explainability Analysis Not Available
          </h3>
          <p className="text-gray-600 mb-4">
            Generate detailed reasoning chains and source analysis to understand
            how this risk score was calculated.
          </p>
          <Button onClick={handleGenerateExplainability} disabled={loading}>
            <Brain className="w-4 h-4 mr-2" />
            Generate Explainability Analysis
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (explainabilityError) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Error Loading Explainability Data
          </h3>
          <p className="text-gray-600 mb-4">
            {explainabilityError instanceof Error
              ? explainabilityError.message
              : "Failed to load explainability data"}
          </p>
          <Button onClick={() => refetchExplainability()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!explainabilityData) {
    return null; // Still loading
  }

  const {
    reasoning_chain: reasoning_steps = [],
    source_analyses = [],
    uncertainty_detections = [],
    overall_confidence = 0,
    source_quality_score = 0,
    uncertainty_level = "unknown",
    human_validation_recommended = false,
  } = explainabilityData;

  return (
    <div className="space-y-6">
      {/* Header with Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center space-x-2">
              <Eye className="w-6 h-6 text-blue-600" />
              <span>AI Explainability Dashboard</span>
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                onClick={handleRefresh}
                variant="outline"
                size="sm"
                disabled={loading}
              >
                <RefreshCw
                  className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
                />
                Refresh
              </Button>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <Brain className="w-8 h-8 text-blue-600 mx-auto mb-2" />
              <p className="text-2xl font-bold text-blue-600">
                {(overall_confidence * 100).toFixed(0)}%
              </p>
              <p className="text-sm text-gray-600">Overall Confidence</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <Shield className="w-8 h-8 text-green-600 mx-auto mb-2" />
              <p className="text-2xl font-bold text-green-600">
                {(source_quality_score * 100).toFixed(0)}%
              </p>
              <p className="text-sm text-gray-600">Source Quality</p>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <AlertTriangle className="w-8 h-8 text-yellow-600 mx-auto mb-2" />
              <p className="text-2xl font-bold text-yellow-600 capitalize">
                {uncertainty_level}
              </p>
              <p className="text-sm text-gray-600">Uncertainty Level</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              {human_validation_recommended ? (
                <XCircle className="w-8 h-8 text-red-600 mx-auto mb-2" />
              ) : (
                <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
              )}
              <p className="text-2xl font-bold text-purple-600">
                {human_validation_recommended ? "Required" : "Not Needed"}
              </p>
              <p className="text-sm text-gray-600">Human Validation</p>
            </div>
          </div>

          {human_validation_recommended && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                <span className="font-medium text-red-800">
                  Human Validation Recommended
                </span>
              </div>
              <p className="text-sm text-red-700 mt-1">
                This analysis contains uncertainties that may benefit from
                expert review. Check the "Uncertainty Detection" tab for
                details.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="reasoning">Reasoning Chain</TabsTrigger>
          <TabsTrigger value="sources">Source Quality</TabsTrigger>
          <TabsTrigger value="uncertainty">Uncertainty Detection</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Quick Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center space-x-2">
                  <Brain className="w-5 h-5 text-purple-600" />
                  <span>Reasoning Steps</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-purple-600 mb-2">
                  {reasoning_steps.length}
                </p>
                <p className="text-sm text-gray-600 mb-3">
                  Detailed steps explaining the risk calculation
                </p>
                <div className="space-y-1">
                  {reasoning_steps.slice(0, 3).map((step: any) => (
                    <div
                      key={step.id}
                      className="flex items-center justify-between text-xs"
                    >
                      <span className="truncate">{step.step_name}</span>
                      <Badge variant="outline" className="text-xs">
                        {(step.confidence_level * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center space-x-2">
                  <Shield className="w-5 h-5 text-green-600" />
                  <span>Source Analysis</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-green-600 mb-2">
                  {source_analyses.length}
                </p>
                <p className="text-sm text-gray-600 mb-3">
                  Sources analyzed for credibility and quality
                </p>
                <div className="space-y-1">
                  {["tier1", "tier2", "tier3"].map((tier) => {
                    const count = source_analyses.filter(
                      (s: any) => s.tier_level === tier
                    ).length;
                    return (
                      <div
                        key={tier}
                        className="flex items-center justify-between text-xs"
                      >
                        <span className="capitalize">
                          {tier.replace("tier", "Tier ")}
                        </span>
                        <span className="font-semibold">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center space-x-2">
                  <AlertTriangle className="w-5 h-5 text-orange-600" />
                  <span>Uncertainties</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-orange-600 mb-2">
                  {uncertainty_detections.length}
                </p>
                <p className="text-sm text-gray-600 mb-3">
                  Potential issues requiring attention
                </p>
                <div className="space-y-1">
                  {["critical", "high", "medium", "low"].map((level) => {
                    const count = uncertainty_detections.filter(
                      (u: any) => u.uncertainty_level === level
                    ).length;
                    if (count === 0) return null;
                    return (
                      <div
                        key={level}
                        className="flex items-center justify-between text-xs"
                      >
                        <span className="capitalize">{level}</span>
                        <span className="font-semibold">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Key Insights */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                <span>Key Insights</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-blue-800">
                      Risk Score Composition
                    </p>
                    <p className="text-sm text-blue-700">
                      The risk score of {riskScore} is primarily driven by
                      product launch impact (24.0 points) and source credibility
                      assessment (18.5 points).
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-green-800">Source Quality</p>
                    <p className="text-sm text-green-700">
                      Analysis includes{" "}
                      {
                        source_analyses.filter(
                          (s: any) => s.tier_level === "tier1"
                        ).length
                      }{" "}
                      authoritative sources and{" "}
                      {
                        source_analyses.filter(
                          (s: any) => s.tier_level === "tier2"
                        ).length
                      }{" "}
                      reputable sources, providing good foundation for the
                      assessment.
                    </p>
                  </div>
                </div>

                {uncertainty_detections.length > 0 && (
                  <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                    <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-yellow-800">
                        Attention Required
                      </p>
                      <p className="text-sm text-yellow-700">
                        {uncertainty_detections.length} uncertainty detection(s)
                        identified.
                        {human_validation_recommended &&
                          " Human validation is recommended for optimal accuracy."}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reasoning">
          <ReasoningChainVisualization
            impactCardId={impactCardId}
            reasoningSteps={reasoning_steps}
            riskScore={riskScore}
            onRefresh={handleRefresh}
          />
        </TabsContent>

        <TabsContent value="sources">
          <SourceQualityVisualization
            impactCardId={impactCardId}
            sourceAnalyses={source_analyses}
            onRefresh={handleRefresh}
          />
        </TabsContent>

        <TabsContent value="uncertainty">
          <UncertaintyDetectionPanel
            impactCardId={impactCardId}
            uncertaintyDetections={uncertainty_detections}
            onRequestValidation={handleRequestValidation}
            onRefresh={handleRefresh}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ExplainabilityDashboard;
