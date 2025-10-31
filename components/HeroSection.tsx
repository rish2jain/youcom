"use client";

import { useState } from "react";
import { Play, ArrowRight, Zap, Brain, Bell } from "lucide-react";

interface HeroSectionProps {
  onStartDemo?: () => void;
  onViewDashboard?: () => void;
}

export function HeroSection({ onStartDemo, onViewDashboard }: HeroSectionProps) {
  const [isVideoPlaying, setIsVideoPlaying] = useState(false);

  return (
    <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 border-b border-blue-100">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="max-w-4xl">
          {/* Problem Statement */}
          <div className="mb-8">
            <div className="inline-flex items-center px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium mb-6">
              <span className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse"></span>
              Competitive Intelligence Automation
            </div>

            <h1 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
              <span className="text-purple-600">All 4 You.com APIs</span>{" "}
              <span className="text-blue-600">Orchestrated</span>{" "}
              <span className="text-gray-900">
                for Competitive Intelligence
              </span>
            </h1>

            <p className="text-xl text-gray-700 leading-relaxed mb-4">
              Watch{" "}
              <strong className="text-purple-600">
                News → Search → Chat → ARI APIs
              </strong>{" "}
              work together to transform hours of manual research into automated
              insights in under 3 minutes.
            </p>
            <p className="text-lg text-gray-600 leading-relaxed">
              <strong className="text-blue-600">Enterprise CIA</strong> is the
              first platform to demonstrate coordinated API orchestration for
              real-time competitive intelligence.
            </p>
          </div>

          {/* Quick Value Props */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
            <div className="flex items-start gap-4 p-4 bg-white/70 backdrop-blur rounded-xl border border-white/50 shadow-sm hover-lift cursor-pointer">
              <div className="w-12 h-12 bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="font-bold text-lg text-gray-900">
                  2-Minute Reports
                </div>
                <div className="text-sm text-gray-600">
                  End-to-end automation via You.com APIs
                </div>
                <div className="text-xs text-green-600 font-medium mt-1">
                  Fully automated process
                </div>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 bg-white/70 backdrop-blur rounded-xl border border-white/50 shadow-sm hover-lift cursor-pointer">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="font-bold text-lg text-gray-900">
                  400+ Sources
                </div>
                <div className="text-sm text-gray-600">
                  Comprehensive analysis via ARI API
                </div>
                <div className="text-xs text-blue-600 font-medium mt-1">
                  Real market intelligence
                </div>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 bg-white/70 backdrop-blur rounded-xl border border-white/50 shadow-sm hover-lift cursor-pointer">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
                <Bell className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="font-bold text-lg text-gray-900">
                  Real-Time Alerts
                </div>
                <div className="text-sm text-gray-600">
                  Detect competitive moves instantly
                </div>
                <div className="text-xs text-purple-600 font-medium mt-1">
                  &lt;60 second detection
                </div>
              </div>
            </div>
          </div>

          {/* CTA Section */}
          <div className="flex flex-col sm:flex-row items-start gap-6">
            <div className="flex items-center gap-4 flex-wrap">
              <button
                onClick={onStartDemo}
                className="group flex items-center gap-3 px-10 py-5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-bold text-xl shadow-xl hover:shadow-2xl hover-glow scale-on-hover transition-all duration-200 border-2 border-white/20"
              >
                <Play className="w-6 h-6 group-hover:scale-110 transition-transform" />
                <span>Watch 4 APIs Orchestrate</span>
                <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
              </button>

              {onViewDashboard && (
                <button
                  onClick={onViewDashboard}
                  className="flex items-center gap-2 px-6 py-3 bg-white text-blue-600 border-2 border-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
                >
                  <span>View Dashboard</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}

              <button
                onClick={() =>
                  document
                    .getElementById("how-it-works")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
                className="flex items-center gap-2 text-blue-600 font-semibold hover:text-blue-700 transition-colors hover-scale"
              >
                <span>See How It Works</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            {/* Quick Stats */}
            <div className="flex items-center gap-6 text-sm text-gray-600 bg-white/50 backdrop-blur rounded-lg px-4 py-2 border border-white/50">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="font-medium">All 4 APIs Active</span>
              </div>
              <div className="w-px h-4 bg-gray-300"></div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-blue-600">400+</span>
                <span>sources via ARI API</span>
              </div>
            </div>
          </div>

          {/* API Integration Badge */}
          <div className="mt-8 inline-flex items-center gap-3 px-4 py-2 bg-white/60 backdrop-blur rounded-lg border border-white/50">
            <div className="flex -space-x-2">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="w-8 h-8 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full border-2 border-white flex items-center justify-center text-white text-xs font-bold"
                >
                  {String.fromCharCode(64 + i)}
                </div>
              ))}
            </div>
            <div className="text-sm">
              <span className="font-semibold text-gray-900">
                All 4 You.com APIs Integrated
              </span>
              <span className="text-gray-600 ml-2">
                • News, Search, Chat, ARI
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
