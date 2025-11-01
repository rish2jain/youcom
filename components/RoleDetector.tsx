"use client";

import React, { useState, useEffect } from "react";
import { useTribeInterface } from "./TribeInterfaceProvider";
import { useUserContext } from "@/contexts/UserContext";
import { tribePersistence } from "@/lib/tribe-persistence";
import {
  User,
  Brain,
  CheckCircle,
  AlertCircle,
  Lightbulb,
  ArrowRight,
  X,
  Settings,
} from "lucide-react";
import { UserRole, InterfaceMode } from "@/lib/types/tribe-interface";

interface RoleDetectorProps {
  onRoleConfirmed?: (role: UserRole) => void;
  onModeSelected?: (mode: InterfaceMode) => void;
}

interface RoleDetectionResult {
  detectedRole: UserRole;
  confidence: number;
  reasoning: string[];
  suggestedMode: InterfaceMode;
}

export function RoleDetector({
  onRoleConfirmed,
  onModeSelected,
}: RoleDetectorProps) {
  const { detectedRole, suggestMode, switchMode, currentMode } =
    useTribeInterface();
  const { userContext } = useUserContext();
  const [showDetection, setShowDetection] = useState(false);
  const [detectionResult, setDetectionResult] =
    useState<RoleDetectionResult | null>(null);
  const [userFeedback, setUserFeedback] = useState<{
    actualRole?: UserRole;
    satisfied: boolean;
    feedback?: string;
  } | null>(null);

  // Auto-detect role on mount
  useEffect(() => {
    if (!detectedRole && userContext.companyName) {
      performRoleDetection();
    }
  }, [userContext, detectedRole]);

  const performRoleDetection = () => {
    // Simulate role detection based on available context
    const detection = detectUserRole();
    setDetectionResult(detection);
    setShowDetection(true);
  };

  const detectUserRole = (): RoleDetectionResult => {
    const reasoning: string[] = [];
    let detectedRole: UserRole = "analyst"; // default
    let confidence = 0.5;

    // Detection based on company context and industry
    if (userContext.industry) {
      reasoning.push(`Industry context: ${userContext.industry}`);
      confidence += 0.1;
    }

    if (userContext.companyName) {
      reasoning.push(`Company context: ${userContext.companyName}`);
      confidence += 0.1;
    }

    // Simulate detection logic (in real implementation, this would use more sophisticated methods)
    const industryRoleMapping: Record<
      string,
      { role: UserRole; confidence: number }
    > = {
      "Artificial Intelligence & ML": { role: "analyst", confidence: 0.8 },
      "SaaS & Cloud Services": { role: "analyst", confidence: 0.7 },
      "Financial Services & Fintech": { role: "executive", confidence: 0.6 },
      "Healthcare & Life Sciences": { role: "team", confidence: 0.7 },
      "Enterprise Software": { role: "analyst", confidence: 0.8 },
    };

    const industryMapping = industryRoleMapping[userContext.industry];
    if (industryMapping) {
      detectedRole = industryMapping.role;
      confidence = Math.max(confidence, industryMapping.confidence);
      reasoning.push(
        `Industry ${userContext.industry} typically uses ${detectedRole} mode`
      );
    }

    // Check for executive indicators in company name
    const executiveIndicators = [
      "CEO",
      "CTO",
      "VP",
      "Director",
      "Chief",
      "Head of",
    ];
    const hasExecutiveIndicator = executiveIndicators.some((indicator) =>
      userContext.companyName.toLowerCase().includes(indicator.toLowerCase())
    );

    if (hasExecutiveIndicator) {
      detectedRole = "executive";
      confidence = Math.max(confidence, 0.9);
      reasoning.push("Executive role indicators detected");
    }

    // Time-based detection (executives often use system during business hours)
    const currentHour = new Date().getHours();
    if (currentHour >= 9 && currentHour <= 17) {
      if (detectedRole === "executive") {
        confidence += 0.1;
        reasoning.push("Business hours usage pattern");
      }
    }

    const suggestedMode = suggestMode(detectedRole);

    return {
      detectedRole,
      confidence: Math.min(confidence, 1.0),
      reasoning,
      suggestedMode,
    };
  };

  const handleRoleConfirmation = (
    confirmedRole: UserRole,
    isCorrect: boolean
  ) => {
    if (detectionResult) {
      // Save detection accuracy for learning
      tribePersistence().saveRoleDetection(
        detectionResult.detectedRole,
        confirmedRole,
        detectionResult.confidence
      );

      setUserFeedback({
        actualRole: confirmedRole,
        satisfied: isCorrect,
      });

      // Switch to appropriate mode
      const appropriateMode = suggestMode(confirmedRole);
      switchMode(appropriateMode);

      onRoleConfirmed?.(confirmedRole);
      onModeSelected?.(appropriateMode);

      if (isCorrect) {
        setShowDetection(false);
      }
    }
  };

  const handleModeSelection = (mode: InterfaceMode) => {
    switchMode(mode);
    onModeSelected?.(mode);
    setShowDetection(false);
  };

  const handleDismiss = () => {
    setShowDetection(false);

    if (detectionResult) {
      // Record dismissal as neutral feedback
      tribePersistence().saveRoleDetection(
        detectionResult.detectedRole,
        "analyst", // default assumption
        0.5
      );
    }
  };

  const getRoleDescription = (role: UserRole): string => {
    const descriptions = {
      executive:
        "Senior leadership focused on strategic decisions and high-level insights",
      analyst:
        "Technical professional requiring detailed analysis and full context",
      team: "Collaborative team member working on shared projects and coordination",
    };
    return descriptions[role];
  };

  const getModeDescription = (mode: InterfaceMode): string => {
    const descriptions = {
      executive: "Simplified interface with key insights and actions only",
      analyst: "Full technical depth with detailed analysis and metrics",
      team: "Collaborative features with moderate detail level",
    };
    return descriptions[mode];
  };

  if (!showDetection || !detectionResult) {
    return (
      <button
        onClick={performRoleDetection}
        className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
      >
        <Brain className="w-4 h-4" />
        Detect My Role
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="w-6 h-6 text-blue-600" />
              <h2 className="text-xl font-bold text-gray-900">
                Role Detection
              </h2>
            </div>
            <button
              onClick={handleDismiss}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <p className="text-gray-600 mt-2">
            We've analyzed your context to suggest the best interface mode for
            you.
          </p>
        </div>

        {/* Detection Results */}
        <div className="p-6">
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-4">
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  detectionResult.confidence > 0.8
                    ? "bg-green-100 text-green-600"
                    : detectionResult.confidence > 0.6
                    ? "bg-yellow-100 text-yellow-600"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                <User className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Detected Role:{" "}
                  {detectionResult.detectedRole.charAt(0).toUpperCase() +
                    detectionResult.detectedRole.slice(1)}
                </h3>
                <p className="text-sm text-gray-600">
                  Confidence: {Math.round(detectionResult.confidence * 100)}%
                </p>
              </div>
            </div>

            <p className="text-gray-700 mb-4">
              {getRoleDescription(detectionResult.detectedRole)}
            </p>

            {/* Detection Reasoning */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <h4 className="font-medium text-gray-900 mb-2">
                Detection Reasoning:
              </h4>
              <ul className="space-y-1">
                {detectionResult.reasoning.map((reason, index) => (
                  <li
                    key={index}
                    className="flex items-start gap-2 text-sm text-gray-700"
                  >
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    {reason}
                  </li>
                ))}
              </ul>
            </div>

            {/* Suggested Mode */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="w-5 h-5 text-blue-600" />
                <h4 className="font-medium text-blue-900">
                  Suggested Interface Mode
                </h4>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-semibold text-blue-900 capitalize">
                  {detectionResult.suggestedMode}
                </span>
                <ArrowRight className="w-4 h-4 text-blue-600" />
                <span className="text-blue-800 text-sm">
                  {getModeDescription(detectionResult.suggestedMode)}
                </span>
              </div>
            </div>
          </div>

          {/* Role Confirmation */}
          {!userFeedback && (
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Is this correct?</h4>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(["executive", "analyst", "team"] as UserRole[]).map(
                  (role) => (
                    <button
                      key={role}
                      onClick={() =>
                        handleRoleConfirmation(
                          role,
                          role === detectionResult.detectedRole
                        )
                      }
                      className={`p-4 border-2 rounded-lg text-left transition-all ${
                        role === detectionResult.detectedRole
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                      }`}
                    >
                      <div className="font-medium text-gray-900 capitalize mb-1">
                        {role}
                      </div>
                      <div className="text-sm text-gray-600">
                        {getRoleDescription(role)}
                      </div>
                      {role === detectionResult.detectedRole && (
                        <div className="mt-2 flex items-center gap-1 text-xs text-blue-600">
                          <CheckCircle className="w-3 h-3" />
                          Detected
                        </div>
                      )}
                    </button>
                  )
                )}
              </div>
            </div>
          )}

          {/* Mode Selection */}
          {userFeedback && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-green-700 bg-green-50 p-3 rounded-lg">
                <CheckCircle className="w-5 h-5" />
                <span>
                  {userFeedback.satisfied
                    ? "Great! Role detection was accurate."
                    : "Thanks for the correction. We'll improve our detection."}
                </span>
              </div>

              <h4 className="font-medium text-gray-900">
                Choose your interface mode:
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(["executive", "analyst", "team"] as InterfaceMode[]).map(
                  (mode) => (
                    <button
                      key={mode}
                      onClick={() => handleModeSelection(mode)}
                      className={`p-4 border-2 rounded-lg text-left transition-all ${
                        mode === detectionResult.suggestedMode
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                      }`}
                    >
                      <div className="font-medium text-gray-900 capitalize mb-1">
                        {mode}
                      </div>
                      <div className="text-sm text-gray-600">
                        {getModeDescription(mode)}
                      </div>
                      {mode === detectionResult.suggestedMode && (
                        <div className="mt-2 flex items-center gap-1 text-xs text-blue-600">
                          <Lightbulb className="w-3 h-3" />
                          Suggested
                        </div>
                      )}
                    </button>
                  )
                )}
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span>You can change your mode anytime in settings</span>
              <button
                onClick={handleDismiss}
                className="flex items-center gap-1 text-blue-600 hover:text-blue-800"
              >
                <Settings className="w-3 h-3" />
                Skip for now
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
