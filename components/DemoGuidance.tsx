"use client";

import { useState } from "react";
import {
  Play,
  Target,
  Eye,
  BarChart3,
  ArrowRight,
  Sparkles,
  ExternalLink,
  CheckCircle,
  Loader2,
  HelpCircle,
} from "lucide-react";

interface DemoOptionProps {
  number: number;
  title: string;
  description: string;
  action: string;
  featured?: boolean;
  icon: React.ReactNode;
  onAction: () => void;
}

function DemoOption({
  number,
  title,
  description,
  action,
  featured,
  icon,
  onAction,
  isCompleted = false,
  isLoading = false,
}: DemoOptionProps & { isCompleted?: boolean; isLoading?: boolean }) {
  return (
    <div
      className={`
      flex items-center gap-4 p-4 rounded-xl transition-all duration-200 hover:shadow-md
      ${
        featured
          ? "bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-300 shadow-lg"
          : "bg-white border-2 border-gray-200 hover:border-blue-300"
      }
      ${isCompleted ? "opacity-75" : ""}
    `}
    >
      <div
        className={`
        w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg
        ${
          featured
            ? "bg-gradient-to-br from-blue-500 to-purple-500 text-white"
            : "bg-gradient-to-br from-gray-100 to-gray-200 text-gray-600"
        }
      `}
      >
        {icon}
      </div>

      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          {isCompleted ? (
            <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
          ) : (
            <span
              className={`
            w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
            ${featured ? "bg-blue-600 text-white" : "bg-gray-300 text-gray-600"}
          `}
            >
              {number}
            </span>
          )}
          <h3 className="font-bold text-lg text-gray-900">{title}</h3>
          {featured && (
            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-bold">
              ⭐ FEATURED
            </span>
          )}
          {isCompleted && (
            <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-bold">
              ✓ Completed
            </span>
          )}
        </div>
        <p className="text-sm text-gray-600 mb-2">{description}</p>
        <div className="flex items-center gap-2 text-xs text-blue-600">
          <Sparkles className="w-3 h-3" />
          <span>Live You.com API demonstration</span>
        </div>
      </div>

      <button
        onClick={onAction}
        disabled={isLoading || isCompleted}
        className={`
          px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-200 whitespace-nowrap flex items-center gap-2 min-h-[44px] min-w-[120px] justify-center
          ${
            featured
              ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          }
        `}
        aria-label={`${action}: ${title}`}
        aria-busy={isLoading}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Loading...</span>
          </>
        ) : isCompleted ? (
          <>
            <CheckCircle className="w-4 h-4" />
            <span>Completed</span>
          </>
        ) : (
          <>
            <span>{action}</span>
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>
    </div>
  );
}

interface DemoGuidanceProps {
  onGenerateDemo: () => void;
  onNavigateToResearch: () => void;
  onNavigateToAnalytics: () => void;
  onNavigateToDashboard?: () => void;
}

export function DemoGuidance({
  onGenerateDemo,
  onNavigateToResearch,
  onNavigateToAnalytics,
  onNavigateToDashboard,
}: DemoGuidanceProps) {
  const [completedActions, setCompletedActions] = useState<number[]>([]);
  const [loadingActions, setLoadingActions] = useState<Set<number>>(new Set());

  const handleAction = async (actionNumber: number, callback: () => void) => {
    setLoadingActions((prev) => new Set(prev).add(actionNumber));
    try {
      await callback();
      // Simulate async action
      await new Promise((resolve) => setTimeout(resolve, 500));
      setCompletedActions((prev) => [...prev, actionNumber]);
    } catch (error) {
      console.error("Demo action failed:", error);
    } finally {
      setLoadingActions((prev) => {
        const next = new Set(prev);
        next.delete(actionNumber);
        return next;
      });
    }
  };

  return (
    <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border-2 border-blue-200 rounded-2xl p-8 shadow-xl">
      <div className="flex items-start gap-6">
        <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
          <Target className="w-8 h-8 text-white" />
        </div>

        <div className="flex-1">
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-2xl font-bold text-gray-900">
                🎯 Try These Live Demonstrations
              </h3>
              <div className="group relative">
                <HelpCircle className="w-5 h-5 text-gray-400 cursor-help" />
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 p-3 bg-gray-900 text-white text-sm rounded-lg whitespace-normal w-64 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                  <strong>First time here?</strong> Start with "Generate Impact Card" to see all 4 APIs work together in real-time. Each demo takes about 2 minutes.
                </div>
              </div>
            </div>
            <p className="text-gray-700 leading-relaxed">
              Experience You.com's API orchestration in action with real
              competitive intelligence scenarios. Each demo showcases different
              aspects of our automated workflow.
            </p>
          </div>

          <div className="space-y-4 mb-6">
            <div className="relative">
              <DemoOption
                number={1}
                title="Generate Impact Card for OpenAI"
                description="Watch all 4 APIs work together in real-time to create actionable intelligence (~2 minutes)"
                action="Start Demo"
                featured={true}
                icon={<Play className="w-6 h-6" />}
                onAction={() => handleAction(1, onGenerateDemo)}
                isCompleted={completedActions.includes(1)}
                isLoading={loadingActions.has(1)}
              />
              <div className="absolute top-2 right-2 flex gap-1">
                <a
                  href="/analytics"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1 bg-white/80 hover:bg-white rounded-lg text-xs text-blue-600 hover:text-blue-700 transition-colors"
                  title="View API analytics"
                  onClick={(e) => e.stopPropagation()}
                >
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>

            <DemoOption
              number={2}
              title="Research Any Company"
              description="Use ARI API to generate comprehensive reports with 400+ sources"
              action="Try Research"
              icon={<Eye className="w-6 h-6" />}
              onAction={() => handleAction(2, onNavigateToResearch)}
              isCompleted={completedActions.includes(2)}
              isLoading={loadingActions.has(2)}
            />

            <DemoOption
              number={3}
              title="Explore API Analytics"
              description="See detailed metrics on API orchestration, performance, and cost optimization"
              action="View Analytics"
              icon={<BarChart3 className="w-6 h-6" />}
              onAction={() => handleAction(3, onNavigateToAnalytics)}
              isCompleted={completedActions.includes(3)}
              isLoading={loadingActions.has(3)}
            />
          </div>

          {/* Enhanced Progress Indicator */}
          <div className="bg-white/70 backdrop-blur rounded-xl p-6 border border-white/50">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="text-base font-semibold text-gray-900">
                  Demo Progress
                </span>
                <div className="group relative">
                  <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 p-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    Complete all 3 demos to see the full API orchestration workflow
                  </div>
                </div>
              </div>
              <span className="text-base font-bold text-gray-900">
                {completedActions.length}/3 completed
              </span>
            </div>
            
            {/* Visual Progress Bar with Steps */}
            <div className="relative mb-4">
              <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                <div
                  className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 h-3 rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${(completedActions.length / 3) * 100}%` }}
                  role="progressbar"
                  aria-valuenow={completedActions.length}
                  aria-valuemin={0}
                  aria-valuemax={3}
                  aria-label={`Demo progress: ${completedActions.length} of 3 completed`}
                ></div>
              </div>
              
              {/* Step Indicators */}
              <div className="flex justify-between items-center relative">
                {[1, 2, 3].map((step) => (
                  <div key={step} className="flex flex-col items-center flex-1">
                    <div
                      className={`
                      w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm transition-all duration-300
                      ${
                        completedActions.includes(step)
                          ? "bg-green-500 text-white shadow-lg scale-110"
                          : completedActions.length >= step
                          ? "bg-blue-500 text-white"
                          : "bg-gray-300 text-gray-600"
                      }
                    `}
                      aria-label={`Step ${step} ${completedActions.includes(step) ? "completed" : "pending"}`}
                    >
                      {completedActions.includes(step) ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : (
                        step
                      )}
                    </div>
                    <div
                      className={`mt-2 text-xs font-medium ${
                        completedActions.includes(step)
                          ? "text-green-700"
                          : "text-gray-500"
                      }`}
                    >
                      Step {step}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {completedActions.length === 3 && (
              <div className="mt-4 p-5 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg shadow-lg">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg">
                    <Sparkles className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="font-bold text-lg text-green-900 mb-2">
                      🎉 All Demos Completed!
                    </div>
                    <div className="text-sm text-green-800 mb-3">
                      You've experienced the full You.com API orchestration workflow. Here's what you explored:
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                      <div className="bg-white/70 rounded-lg p-3 border border-green-200">
                        <div className="font-semibold text-green-900 text-xs mb-1">✓ Impact Card Demo</div>
                        <div className="text-xs text-green-700">4 APIs orchestrated</div>
                      </div>
                      <div className="bg-white/70 rounded-lg p-3 border border-green-200">
                        <div className="font-semibold text-green-900 text-xs mb-1">✓ Research Demo</div>
                        <div className="text-xs text-green-700">400+ sources analyzed</div>
                      </div>
                      <div className="bg-white/70 rounded-lg p-3 border border-green-200">
                        <div className="font-semibold text-green-900 text-xs mb-1">✓ Analytics Demo</div>
                        <div className="text-xs text-green-700">Performance metrics</div>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={onNavigateToDashboard}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg font-semibold text-sm hover:bg-green-700 transition-colors min-h-[44px]"
                        aria-label="View dashboard with all generated insights"
                      >
                        View Dashboard →
                      </button>
                      <button
                        onClick={() => {
                          setCompletedActions([]);
                        }}
                        className="px-4 py-2 bg-white border border-green-300 text-green-700 rounded-lg font-semibold text-sm hover:bg-green-50 transition-colors min-h-[44px]"
                        aria-label="Reset demo progress to start over"
                      >
                        Reset & Start Over
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
