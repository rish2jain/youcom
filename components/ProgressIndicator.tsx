"use client";

import { useState, useEffect } from "react";
import { CheckCircle, Clock, Zap } from "lucide-react";

interface ProgressStep {
  id: string;
  label: string;
  description: string;
  estimatedTime: number; // in seconds
  status: "pending" | "active" | "completed" | "error";
}

interface ProgressIndicatorProps {
  steps: ProgressStep[];
  currentStep: string;
  onComplete?: () => void;
}

export function ProgressIndicator({
  steps,
  currentStep,
  onComplete,
}: ProgressIndicatorProps) {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [startTime] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  const currentStepIndex = steps.findIndex((step) => step.id === currentStep);
  const totalEstimatedTime = steps.reduce(
    (sum, step) => sum + step.estimatedTime,
    0
  );
  const completedTime = steps
    .slice(0, currentStepIndex)
    .reduce((sum, step) => sum + step.estimatedTime, 0);
  const progressPercentage = Math.min(
    ((completedTime + elapsedTime) / totalEstimatedTime) * 100,
    100
  );

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-blue-200">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-semibold text-gray-900">
            Processing Request
          </h3>
          <span className="text-sm text-gray-600">
            {formatTime(elapsedTime)} / ~{formatTime(totalEstimatedTime)}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div
            className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          >
            <div className="h-full bg-white bg-opacity-30 rounded-full animate-pulse"></div>
          </div>
        </div>

        <div className="text-center text-sm text-gray-600">
          {Math.round(progressPercentage)}% complete
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-4">
        {steps.map((step, index) => {
          const isActive = step.id === currentStep;
          const isCompleted = index < currentStepIndex;
          const isPending = index > currentStepIndex;

          return (
            <div key={step.id} className="flex items-start space-x-3">
              <div className="flex-shrink-0 mt-1">
                {isCompleted ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : isActive ? (
                  <div className="w-5 h-5 border-2 border-blue-500 rounded-full flex items-center justify-center">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  </div>
                ) : (
                  <Clock className="w-5 h-5 text-gray-400" />
                )}
              </div>

              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <h4
                    className={`font-medium ${
                      isCompleted
                        ? "text-green-700"
                        : isActive
                        ? "text-blue-700"
                        : "text-gray-500"
                    }`}
                  >
                    {step.label}
                  </h4>

                  {isActive && (
                    <div className="flex items-center space-x-1 text-xs text-blue-600">
                      <Zap className="w-3 h-3" />
                      <span>~{step.estimatedTime}s</span>
                    </div>
                  )}
                </div>

                <p
                  className={`text-sm mt-1 ${
                    isCompleted
                      ? "text-green-600"
                      : isActive
                      ? "text-blue-600"
                      : "text-gray-500"
                  }`}
                >
                  {step.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Current Activity */}
      {currentStepIndex >= 0 && currentStepIndex < steps.length && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-blue-900">
              Currently Processing
            </span>
          </div>
          <p className="text-sm text-blue-800">
            {steps[currentStepIndex]?.description}
          </p>
        </div>
      )}
    </div>
  );
}

// Preset configurations for common operations
export const RESEARCH_STEPS: ProgressStep[] = [
  {
    id: "search",
    label: "Gathering Context",
    description: "Using You.com Search API to collect background information",
    estimatedTime: 15,
    status: "pending",
  },
  {
    id: "news",
    label: "Monitoring News",
    description: "Scanning recent news and announcements via News API",
    estimatedTime: 10,
    status: "pending",
  },
  {
    id: "analysis",
    label: "AI Analysis",
    description: "Processing data with Custom Agents for impact extraction",
    estimatedTime: 20,
    status: "pending",
  },
  {
    id: "report",
    label: "Generating Report",
    description: "Creating comprehensive research report via ARI API",
    estimatedTime: 45,
    status: "pending",
  },
  {
    id: "complete",
    label: "Finalizing",
    description: "Assembling final report with recommendations",
    estimatedTime: 10,
    status: "pending",
  },
];

export const IMPACT_ANALYSIS_STEPS: ProgressStep[] = [
  {
    id: "fetch",
    label: "Fetching Data",
    description: "Retrieving latest competitive intelligence",
    estimatedTime: 5,
    status: "pending",
  },
  {
    id: "analyze",
    label: "Impact Analysis",
    description: "Analyzing competitive implications and risk factors",
    estimatedTime: 15,
    status: "pending",
  },
  {
    id: "score",
    label: "Risk Scoring",
    description: "Calculating impact scores and confidence levels",
    estimatedTime: 8,
    status: "pending",
  },
  {
    id: "recommendations",
    label: "Generating Actions",
    description: "Creating actionable recommendations",
    estimatedTime: 12,
    status: "pending",
  },
];
