"use client";

import { useState, useEffect } from "react";
import { X, Play, CheckCircle, Clock, Zap, ArrowRight } from "lucide-react";

interface LiveDemoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface DemoStep {
  id: string;
  name: string;
  api: string;
  icon: string;
  status: "pending" | "active" | "completed";
  duration: number;
  description: string;
  result?: string;
}

export function LiveDemoModal({ isOpen, onClose }: LiveDemoModalProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);

  const demoSteps: DemoStep[] = [
    {
      id: "news",
      name: "Real-Time Detection",
      api: "News API",
      icon: "📰",
      status: "pending",
      duration: 2000,
      description: "Scanning news sources for OpenAI mentions...",
      result: "Found 12 articles in last 24 hours",
    },
    {
      id: "search",
      name: "Context Enrichment",
      api: "Search API",
      icon: "🔍",
      status: "pending",
      duration: 1500,
      description: "Gathering market context and competitive data...",
      result: "Enriched with 8 high-quality sources",
    },
    {
      id: "chat",
      name: "Strategic Analysis",
      api: "Chat API (Custom Agent)",
      icon: "🤖",
      status: "pending",
      duration: 2500,
      description: "Analyzing competitive implications and threat level...",
      result: "Threat score: 8.8/10 - High Priority",
    },
    {
      id: "ari",
      name: "Deep Synthesis",
      api: "ARI API",
      icon: "🧠",
      status: "pending",
      duration: 3000,
      description: "Synthesizing insights from 400+ web sources...",
      result: "Comprehensive analysis complete",
    },
  ];

  const [steps, setSteps] = useState(demoSteps);

  const runDemo = async () => {
    setIsRunning(true);
    setIsCompleted(false);
    setCurrentStep(0);

    // Reset all steps
    setSteps(demoSteps.map((step) => ({ ...step, status: "pending" })));

    for (let i = 0; i < demoSteps.length; i++) {
      setCurrentStep(i);

      // Set current step to active
      setSteps((prev) =>
        prev.map((step, index) => ({
          ...step,
          status: index === i ? "active" : index < i ? "completed" : "pending",
        }))
      );

      // Wait for step duration
      await new Promise((resolve) =>
        setTimeout(resolve, demoSteps[i].duration)
      );

      // Mark step as completed
      setSteps((prev) =>
        prev.map((step, index) => ({
          ...step,
          status: index <= i ? "completed" : "pending",
        }))
      );
    }

    setIsRunning(false);
    setIsCompleted(true);
  };

  const resetDemo = () => {
    setIsRunning(false);
    setIsCompleted(false);
    setCurrentStep(0);
    setSteps(demoSteps.map((step) => ({ ...step, status: "pending" })));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              🎬 Live API Orchestration Demo
            </h2>
            <p className="text-gray-600 mt-1">
              Watch all 4 You.com APIs work together in real-time
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* Demo Content */}
        <div className="p-6">
          {/* Demo Target */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200 rounded-xl p-6 mb-8">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-2xl">🎯</span>
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">
                  Demo Target: OpenAI
                </h3>
                <p className="text-gray-700">
                  Generating competitive intelligence for recent OpenAI
                  developments
                </p>
              </div>
            </div>
          </div>

          {/* API Steps */}
          <div className="space-y-4 mb-8">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className={`
                  flex items-start gap-4 p-4 rounded-xl border-2 transition-all duration-300
                  ${
                    step.status === "completed"
                      ? "bg-green-50 border-green-200"
                      : step.status === "active"
                      ? "bg-blue-50 border-blue-200 animate-pulse"
                      : "bg-gray-50 border-gray-200"
                  }
                `}
              >
                <div
                  className={`
                  w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0 shadow-sm
                  ${
                    step.status === "completed"
                      ? "bg-green-100"
                      : step.status === "active"
                      ? "bg-blue-100"
                      : "bg-gray-100"
                  }
                `}
                >
                  {step.status === "completed" ? (
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  ) : step.status === "active" ? (
                    <Clock className="w-6 h-6 text-blue-600 animate-spin" />
                  ) : (
                    <span>{step.icon}</span>
                  )}
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-bold text-lg text-gray-900">
                      {step.name}
                    </h4>
                    <span className="text-sm font-medium text-gray-600">
                      {step.api}
                    </span>
                  </div>

                  <p className="text-gray-700 mb-2">{step.description}</p>

                  {step.status === "completed" && step.result && (
                    <div className="flex items-center gap-2 text-sm font-medium text-green-700">
                      <CheckCircle className="w-4 h-4" />
                      <span>{step.result}</span>
                    </div>
                  )}

                  {step.status === "active" && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm font-medium text-blue-700">
                        <Clock className="w-4 h-4 animate-spin" />
                        <span>
                          Processing... (~{Math.ceil(step.duration / 1000)}s
                          remaining)
                        </span>
                      </div>
                      <div className="w-full bg-blue-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full animate-pulse"
                          style={{ width: "60%" }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="text-sm text-gray-500">Step {index + 1}/4</div>
              </div>
            ))}
          </div>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>Overall Progress</span>
              <span>
                {steps.filter((s) => s.status === "completed").length}/4 APIs
                completed
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500"
                style={{
                  width: `${
                    (steps.filter((s) => s.status === "completed").length / 4) *
                    100
                  }%`,
                }}
              ></div>
            </div>
          </div>

          {/* Result */}
          {isCompleted && (
            <div className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-300 rounded-xl p-6 mb-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-blue-500 rounded-xl flex items-center justify-center shadow-lg">
                  <CheckCircle className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">
                    ✅ Impact Card Generated Successfully!
                  </h3>
                  <p className="text-gray-700">
                    Complete competitive analysis ready in 2 minutes 14 seconds
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-white rounded-lg border border-green-200">
                  <div className="text-2xl font-bold text-green-600">
                    8.8/10
                  </div>
                  <div className="text-xs text-gray-600">Threat Score</div>
                </div>
                <div className="text-center p-3 bg-white rounded-lg border border-green-200">
                  <div className="text-2xl font-bold text-blue-600">412</div>
                  <div className="text-xs text-gray-600">Sources</div>
                </div>
                <div className="text-center p-3 bg-white rounded-lg border border-green-200">
                  <div className="text-2xl font-bold text-purple-600">92%</div>
                  <div className="text-xs text-gray-600">Confidence</div>
                </div>
                <div className="text-center p-3 bg-white rounded-lg border border-green-200">
                  <div className="text-2xl font-bold text-orange-600">3</div>
                  <div className="text-xs text-gray-600">Recommendations</div>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {!isRunning && !isCompleted && (
                <button
                  onClick={runDemo}
                  className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-200 shadow-lg"
                >
                  <Play className="w-5 h-5" />
                  <span>Start Demo</span>
                </button>
              )}

              {isCompleted && (
                <button
                  onClick={resetDemo}
                  className="flex items-center gap-3 px-6 py-3 bg-gray-600 text-white rounded-xl font-semibold hover:bg-gray-700 transition-colors"
                >
                  <span>Run Again</span>
                </button>
              )}

              {isCompleted && (
                <button
                  onClick={() => {
                    onClose();
                    // Scroll to featured impact card
                    setTimeout(() => {
                      document
                        .querySelector('[data-testid="featured-impact-card"]')
                        ?.scrollIntoView({
                          behavior: "smooth",
                        });
                    }, 300);
                  }}
                  className="flex items-center gap-3 px-6 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition-colors"
                >
                  <span>View Full Impact Card</span>
                  <ArrowRight className="w-5 h-5" />
                </button>
              )}
            </div>

            <div className="text-sm text-gray-500">
              {isRunning && (
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-blue-500 animate-pulse" />
                  <span>APIs orchestrating...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
