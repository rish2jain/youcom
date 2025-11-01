"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  ChevronDown,
  ChevronRight,
  Brain,
  Target,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  ExternalLink,
  Info,
  Lightbulb,
  Calculator,
  Shield,
} from "lucide-react";

interface ReasoningStep {
  id: number;
  step_order: number;
  step_type: string;
  step_name: string;
  factor_name: string;
  factor_weight: number;
  factor_contribution: number;
  evidence_sources: Array<{
    title?: string;
    url?: string;
    tier?: string;
    weight?: number;
    factor?: string;
    score?: string;
    description?: string;
    relevance?: string;
  }>;
  reasoning_text: string;
  confidence_level: number;
  uncertainty_flags: string[];
  conflicting_evidence: any[];
  created_at: string;
}

interface ReasoningChainVisualizationProps {
  impactCardId: number;
  reasoningSteps: ReasoningStep[];
  riskScore: number;
  onRefresh?: () => void;
}

const ReasoningChainVisualization: React.FC<
  ReasoningChainVisualizationProps
> = ({ impactCardId, reasoningSteps, riskScore, onRefresh }) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set([1])); // Expand first step by default

  const toggleStep = (stepId: number) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const getStepIcon = (stepType: string) => {
    switch (stepType) {
      case "source_assessment":
        return Shield;
      case "impact_analysis":
        return Target;
      case "risk_calculation":
        return Calculator;
      case "confidence_assessment":
        return Brain;
      default:
        return Info;
    }
  };

  const getStepColor = (stepType: string) => {
    switch (stepType) {
      case "source_assessment":
        return "text-blue-600 bg-blue-50 border-blue-200";
      case "impact_analysis":
        return "text-green-600 bg-green-50 border-green-200";
      case "risk_calculation":
        return "text-purple-600 bg-purple-50 border-purple-200";
      case "confidence_assessment":
        return "text-orange-600 bg-orange-50 border-orange-200";
      default:
        return "text-gray-600 bg-gray-50 border-gray-200";
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "text-green-600";
    if (confidence >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return "High";
    if (confidence >= 0.6) return "Medium";
    return "Low";
  };

  const formatStepType = (stepType: string) => {
    return stepType
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  // Calculate total contribution for visualization
  const totalContribution = reasoningSteps.reduce(
    (sum, step) => sum + step.factor_contribution,
    0
  );
  const averageConfidence =
    reasoningSteps.length > 0
      ? reasoningSteps.reduce((sum, step) => sum + step.confidence_level, 0) /
        reasoningSteps.length
      : 0;

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Brain className="w-6 h-6 text-purple-600" />
            <span>AI Reasoning Chain</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">
                {reasoningSteps.length}
              </p>
              <p className="text-sm text-gray-600">Reasoning Steps</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">{riskScore}</p>
              <p className="text-sm text-gray-600">Final Risk Score</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold">
                {totalContribution.toFixed(1)}
              </p>
              <p className="text-sm text-gray-600">Total Contribution</p>
            </div>
            <div className="text-center">
              <p
                className={`text-2xl font-bold ${getConfidenceColor(
                  averageConfidence
                )}`}
              >
                {(averageConfidence * 100).toFixed(0)}%
              </p>
              <p className="text-sm text-gray-600">Avg. Confidence</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Reasoning Steps */}
      <div className="space-y-4">
        {reasoningSteps.map((step, index) => {
          const StepIcon = getStepIcon(step.step_type);
          const isExpanded = expandedSteps.has(step.id);
          const isLastStep = index === reasoningSteps.length - 1;

          return (
            <div key={step.id} className="relative">
              {/* Connection Line */}
              {!isLastStep && (
                <div className="absolute left-6 top-16 w-0.5 h-8 bg-gray-300 z-0"></div>
              )}

              <Card
                className={`relative z-10 ${
                  step.uncertainty_flags.length > 0 ? "border-yellow-300" : ""
                }`}
              >
                <CardHeader
                  className="cursor-pointer hover:bg-gray-50 transition-colors"
                  onClick={() => toggleStep(step.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div
                        className={`p-2 rounded-full border ${getStepColor(
                          step.step_type
                        )}`}
                      >
                        <StepIcon className="w-5 h-5" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">
                          Step {step.step_order}: {step.step_name}
                        </CardTitle>
                        <div className="flex items-center space-x-4 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {formatStepType(step.step_type)}
                          </Badge>
                          <div className="flex items-center space-x-1">
                            <span className="text-sm text-gray-600">
                              Confidence:
                            </span>
                            <span
                              className={`text-sm font-semibold ${getConfidenceColor(
                                step.confidence_level
                              )}`}
                            >
                              {getConfidenceLabel(step.confidence_level)} (
                              {(step.confidence_level * 100).toFixed(0)}%)
                            </span>
                          </div>
                          {step.uncertainty_flags.length > 0 && (
                            <div className="flex items-center space-x-1">
                              <AlertTriangle className="w-4 h-4 text-yellow-500" />
                              <span className="text-sm text-yellow-600">
                                {step.uncertainty_flags.length} warning(s)
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {step.factor_weight > 0 && (
                        <div className="text-right">
                          <p className="text-sm font-semibold">
                            +{step.factor_contribution.toFixed(1)}
                          </p>
                          <p className="text-xs text-gray-500">contribution</p>
                        </div>
                      )}
                      {isExpanded ? (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                </CardHeader>

                {isExpanded && (
                  <CardContent className="pt-0">
                    <div className="space-y-4">
                      {/* Factor Analysis */}
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="font-medium mb-3 flex items-center space-x-2">
                          <Target className="w-4 h-4" />
                          <span>Factor Analysis: {step.factor_name}</span>
                        </h4>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                          <div>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm text-gray-600">
                                Factor Weight
                              </span>
                              <span className="font-semibold">
                                {(step.factor_weight * 100).toFixed(1)}%
                              </span>
                            </div>
                            <Progress
                              value={step.factor_weight * 100}
                              className="h-2"
                            />
                          </div>
                          <div>
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-sm text-gray-600">
                                Contribution to Risk
                              </span>
                              <span className="font-semibold">
                                {step.factor_contribution.toFixed(1)} points
                              </span>
                            </div>
                            <Progress
                              value={(step.factor_contribution / 100) * 100}
                              className="h-2"
                            />
                          </div>
                        </div>

                        <div className="bg-white rounded p-3 border">
                          <h5 className="font-medium mb-2 flex items-center space-x-2">
                            <Lightbulb className="w-4 h-4 text-yellow-500" />
                            <span>Reasoning</span>
                          </h5>
                          <p className="text-sm text-gray-700">
                            {step.reasoning_text}
                          </p>
                        </div>
                      </div>

                      {/* Evidence Sources */}
                      {step.evidence_sources.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-3 flex items-center space-x-2">
                            <CheckCircle className="w-4 h-4 text-green-500" />
                            <span>Supporting Evidence</span>
                          </h4>
                          <div className="space-y-2">
                            {step.evidence_sources.map(
                              (evidence, evidenceIndex) => (
                                <div
                                  key={evidenceIndex}
                                  className="bg-green-50 rounded-lg p-3 border border-green-200"
                                >
                                  {evidence.url ? (
                                    <div className="flex items-start justify-between">
                                      <div className="flex-1">
                                        <p className="font-medium text-sm">
                                          {evidence.title || "Evidence Source"}
                                        </p>
                                        <a
                                          href={evidence.url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="text-blue-600 hover:underline text-xs flex items-center space-x-1 mt-1"
                                        >
                                          <span>{evidence.url}</span>
                                          <ExternalLink className="w-3 h-3" />
                                        </a>
                                        {evidence.tier && (
                                          <Badge
                                            className="mt-1 text-xs"
                                            variant="outline"
                                          >
                                            {evidence.tier}
                                          </Badge>
                                        )}
                                      </div>
                                      {evidence.weight && (
                                        <span className="text-xs text-gray-600 ml-2">
                                          Weight: {evidence.weight}
                                        </span>
                                      )}
                                    </div>
                                  ) : (
                                    <div className="space-y-1">
                                      {evidence.factor && (
                                        <div className="flex justify-between">
                                          <span className="text-sm font-medium">
                                            {evidence.factor}
                                          </span>
                                          <span className="text-sm">
                                            {evidence.score}
                                          </span>
                                        </div>
                                      )}
                                      {evidence.description && (
                                        <p className="text-xs text-gray-600">
                                          {evidence.description}
                                        </p>
                                      )}
                                    </div>
                                  )}
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      )}

                      {/* Uncertainty Flags */}
                      {step.uncertainty_flags.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-3 flex items-center space-x-2">
                            <AlertTriangle className="w-4 h-4 text-yellow-500" />
                            <span>Uncertainty Indicators</span>
                          </h4>
                          <div className="space-y-2">
                            {step.uncertainty_flags.map((flag, flagIndex) => (
                              <div
                                key={flagIndex}
                                className="bg-yellow-50 rounded-lg p-3 border border-yellow-200"
                              >
                                <div className="flex items-center space-x-2">
                                  <AlertTriangle className="w-4 h-4 text-yellow-600" />
                                  <span className="text-sm font-medium text-yellow-800">
                                    {flag.replace(/_/g, " ").toUpperCase()}
                                  </span>
                                </div>
                                <p className="text-xs text-yellow-700 mt-1">
                                  {flag === "low_source_quality" &&
                                    "The quality of sources supporting this factor is below optimal levels."}
                                  {flag === "no_authoritative_sources" &&
                                    "No tier-1 authoritative sources found for this factor."}
                                  {flag === "insufficient_sources" &&
                                    "Limited number of sources available for verification."}
                                  {flag ===
                                    "high_impact_insufficient_evidence" &&
                                    "High impact factor with limited supporting evidence."}
                                  {flag === "insufficient_analysis_detail" &&
                                    "Analysis lacks sufficient detail for confident assessment."}
                                  {flag === "low_average_confidence" &&
                                    "Average confidence across factors is below acceptable threshold."}
                                  {flag === "calculation_discrepancy" &&
                                    "Discrepancy detected between calculated and reported values."}
                                  {flag === "low_overall_confidence" &&
                                    "Overall confidence in the analysis is below recommended levels."}
                                  {flag === "low_model_confidence" &&
                                    "AI model confidence in the analysis is below optimal levels."}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Conflicting Evidence */}
                      {step.conflicting_evidence.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-3 flex items-center space-x-2">
                            <AlertTriangle className="w-4 h-4 text-red-500" />
                            <span>Conflicting Evidence</span>
                          </h4>
                          <div className="space-y-2">
                            {step.conflicting_evidence.map(
                              (conflict, conflictIndex) => (
                                <div
                                  key={conflictIndex}
                                  className="bg-red-50 rounded-lg p-3 border border-red-200"
                                >
                                  <p className="text-sm text-red-800">
                                    {JSON.stringify(conflict)}
                                  </p>
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                )}
              </Card>
            </div>
          );
        })}
      </div>

      {/* Summary Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            <span>Reasoning Summary</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-medium text-blue-800 mb-2">Key Factors</h4>
                <div className="space-y-2">
                  {reasoningSteps
                    .filter((step) => step.factor_weight > 0)
                    .sort(
                      (a, b) => b.factor_contribution - a.factor_contribution
                    )
                    .slice(0, 3)
                    .map((step, index) => (
                      <div
                        key={step.id}
                        className="flex justify-between items-center"
                      >
                        <span className="text-sm text-blue-700">
                          {step.factor_name}
                        </span>
                        <span className="text-sm font-semibold text-blue-800">
                          +{step.factor_contribution.toFixed(1)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-2">
                  Confidence Levels
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-green-700">
                      Average Confidence
                    </span>
                    <span
                      className={`text-sm font-semibold ${getConfidenceColor(
                        averageConfidence
                      )}`}
                    >
                      {(averageConfidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-green-700">
                      High Confidence Steps
                    </span>
                    <span className="text-sm font-semibold text-green-800">
                      {
                        reasoningSteps.filter((s) => s.confidence_level >= 0.8)
                          .length
                      }
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-green-700">
                      Uncertainty Flags
                    </span>
                    <span className="text-sm font-semibold text-green-800">
                      {reasoningSteps.reduce(
                        (sum, s) => sum + s.uncertainty_flags.length,
                        0
                      )}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium mb-2">Analysis Quality Assessment</h4>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  {averageConfidence >= 0.8 ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : averageConfidence >= 0.6 ? (
                    <AlertTriangle className="w-5 h-5 text-yellow-500" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-red-500" />
                  )}
                  <span className="text-sm">
                    {averageConfidence >= 0.8 &&
                      "High quality analysis with strong confidence"}
                    {averageConfidence >= 0.6 &&
                      averageConfidence < 0.8 &&
                      "Moderate quality analysis with some uncertainty"}
                    {averageConfidence < 0.6 &&
                      "Lower confidence analysis - consider additional validation"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Refresh Button */}
      {onRefresh && (
        <div className="flex justify-end">
          <Button onClick={onRefresh} variant="outline">
            <Brain className="w-4 h-4 mr-2" />
            Regenerate Reasoning
          </Button>
        </div>
      )}
    </div>
  );
};

export default ReasoningChainVisualization;
