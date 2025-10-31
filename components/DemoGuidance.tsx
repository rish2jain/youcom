"use client";

import { useState } from "react";
import {
  Play,
  Target,
  Eye,
  BarChart3,
  ArrowRight,
  Sparkles,
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
}: DemoOptionProps) {
  return (
    <div
      className={`
      flex items-center gap-4 p-4 rounded-xl transition-all duration-200 cursor-pointer hover:shadow-md
      ${
        featured
          ? "bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-300 shadow-lg"
          : "bg-white border-2 border-gray-200 hover:border-blue-300"
      }
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
          <span
            className={`
            w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
            ${featured ? "bg-blue-600 text-white" : "bg-gray-300 text-gray-600"}
          `}
          >
            {number}
          </span>
          <h3 className="font-bold text-lg text-gray-900">{title}</h3>
          {featured && (
            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-bold">
              ⭐ FEATURED
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
        className={`
          px-6 py-3 rounded-xl font-semibold text-sm transition-all duration-200 whitespace-nowrap flex items-center gap-2
          ${
            featured
              ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl"
              : "bg-blue-600 text-white hover:bg-blue-700"
          }
        `}
      >
        <span>{action}</span>
        <ArrowRight className="w-4 h-4" />
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

  const handleAction = (actionNumber: number, callback: () => void) => {
    callback();
    setCompletedActions((prev) => [...prev, actionNumber]);
  };

  return (
    <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border-2 border-blue-200 rounded-2xl p-8 shadow-xl">
      <div className="flex items-start gap-6">
        <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
          <Target className="w-8 h-8 text-white" />
        </div>

        <div className="flex-1">
          <div className="mb-6">
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              🎯 Try These Live Demonstrations
            </h3>
            <p className="text-gray-700 leading-relaxed">
              Experience You.com's API orchestration in action with real
              competitive intelligence scenarios. Each demo showcases different
              aspects of our automated workflow.
            </p>
          </div>

          <div className="space-y-4 mb-6">
            <DemoOption
              number={1}
              title="Generate Impact Card for OpenAI"
              description="Watch all 4 APIs work together in real-time to create actionable intelligence (~2 minutes)"
              action="Start Demo"
              featured={true}
              icon={<Play className="w-6 h-6" />}
              onAction={() => handleAction(1, onGenerateDemo)}
            />

            <DemoOption
              number={2}
              title="Research Any Company"
              description="Use ARI API to generate comprehensive reports with 400+ sources"
              action="Try Research"
              icon={<Eye className="w-6 h-6" />}
              onAction={() => handleAction(2, onNavigateToResearch)}
            />

            <DemoOption
              number={3}
              title="Explore API Analytics"
              description="See detailed metrics on API orchestration, performance, and cost optimization"
              action="View Analytics"
              icon={<BarChart3 className="w-6 h-6" />}
              onAction={() => handleAction(3, onNavigateToAnalytics)}
            />
          </div>

          {/* Progress Indicator */}
          <div className="bg-white/70 backdrop-blur rounded-xl p-4 border border-white/50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                Demo Progress
              </span>
              <span className="text-sm text-gray-600">
                {completedActions.length}/3 completed
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${(completedActions.length / 3) * 100}%` }}
              ></div>
            </div>
            {completedActions.length === 3 && (
              <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center gap-2 text-green-800">
                  <Sparkles className="w-4 h-4" />
                  <span className="text-sm font-medium">
                    🎉 All demos completed! You've seen the full You.com API
                    orchestration.
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
