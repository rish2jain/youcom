"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Share,
  Download,
  AlertTriangle,
  TrendingUp,
  Clock,
  Target,
} from "lucide-react";

export function FeaturedImpactCard() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      className="border-2 border-orange-200 rounded-xl overflow-hidden shadow-lg bg-white"
      data-testid="featured-impact-card"
    >
      {/* Header - Always Visible */}
      <div
        className="p-6 bg-gradient-to-r from-orange-50 via-red-50 to-pink-50 cursor-pointer hover:from-orange-100 hover:via-red-100 hover:to-pink-100 transition-all duration-200"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center shadow-lg">
                <AlertTriangle className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-bold text-xl text-gray-900">
                  OpenAI GPT-5 Release
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-bold">
                    🚨 HIGH PRIORITY
                  </span>
                  <span className="text-xs text-gray-500">
                    Generated 2 minutes ago
                  </span>
                </div>
              </div>
            </div>

            <p className="text-gray-700 mb-4 leading-relaxed">
              <strong>Existential competitive threat:</strong> GPT-5 achieves
              breakthrough reasoning capabilities with 94.6% AIME performance,
              $300B valuation, and $13B ARR. Represents paradigm shift in AI
              capabilities.
            </p>

            {/* Key Metrics Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="text-center p-3 bg-white/70 rounded-lg border border-orange-200">
                <div className="text-2xl font-bold text-red-600">9.8/10</div>
                <div className="text-xs text-gray-600 font-medium">
                  Threat Score
                </div>
              </div>
              <div className="text-center p-3 bg-white/70 rounded-lg border border-orange-200">
                <div className="text-2xl font-bold text-blue-600">96%</div>
                <div className="text-xs text-gray-600 font-medium">
                  Confidence
                </div>
              </div>
              <div className="text-center p-3 bg-white/70 rounded-lg border border-orange-200">
                <div className="text-2xl font-bold text-green-600">487</div>
                <div className="text-xs text-gray-600 font-medium">Sources</div>
              </div>
              <div className="text-center p-3 bg-white/70 rounded-lg border border-orange-200">
                <div className="text-2xl font-bold text-purple-600">Immed</div>
                <div className="text-xs text-gray-600 font-medium">
                  Timeline
                </div>
              </div>
            </div>

            {/* API Provenance */}
            <div className="flex flex-wrap gap-2 mb-4">
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                📰 News API <span className="font-bold">12 articles</span>
              </span>
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                🔍 Search API <span className="font-bold">8 queries</span>
              </span>
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-xs font-medium">
                🤖 Chat API <span className="font-bold">1 analysis</span>
              </span>
              <span className="inline-flex items-center gap-1 px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-xs font-medium">
                🧠 ARI API <span className="font-bold">400+ sources</span>
              </span>
            </div>
          </div>

          <button className="flex items-center gap-2 px-4 py-2 bg-white/80 hover:bg-white border border-orange-200 rounded-lg text-sm font-medium text-gray-700 hover:text-gray-900 transition-all duration-200 ml-4">
            {isExpanded ? (
              <>
                <ChevronUp className="w-4 h-4" />
                <span>Collapse</span>
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                <span>Expand Full Report</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-6 bg-white border-t border-orange-200">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Key Insights */}
              <div>
                <h4 className="flex items-center gap-2 font-bold text-lg text-gray-900 mb-4">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                  Key Competitive Insights
                </h4>
                <div className="space-y-3">
                  <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-white text-xs font-bold">1</span>
                    </div>
                    <div>
                      <div className="font-semibold text-green-900">
                        Reasoning Breakthrough
                      </div>
                      <div className="text-sm text-green-800">
                        GPT-5 achieves 94.6% on AIME 2025 and 74.9% on SWE-bench
                        - unprecedented reasoning capabilities
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-white text-xs font-bold">2</span>
                    </div>
                    <div>
                      <div className="font-semibold text-blue-900">
                        Market Dominance
                      </div>
                      <div className="text-sm text-blue-800">
                        $300B valuation, $13B ARR, 5M business users -
                        unprecedented scale and market control
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3 p-4 bg-purple-50 border border-purple-200 rounded-lg">
                    <div className="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-white text-xs font-bold">3</span>
                    </div>
                    <div>
                      <div className="font-semibold text-purple-900">
                        Enterprise Adoption
                      </div>
                      <div className="text-sm text-purple-800">
                        Used by Cursor, Vercel, Factory, JetBrains - deep
                        enterprise penetration across developer tools
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Strategic Recommendations */}
              <div>
                <h4 className="flex items-center gap-2 font-bold text-lg text-gray-900 mb-4">
                  <Target className="w-5 h-5 text-red-600" />
                  Strategic Recommendations
                </h4>
                <div className="space-y-3">
                  <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-red-500 text-white rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0">
                        1
                      </div>
                      <div>
                        <div className="font-bold text-red-900 mb-1">
                          Strategic Response Required
                        </div>
                        <div className="text-sm text-red-800 mb-2">
                          GPT-5's reasoning capabilities represent existential
                          threat. Immediate strategic pivot required to compete
                          with breakthrough AI.
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <Clock className="w-3 h-3" />
                          <span className="font-medium">Timeline: 1 week</span>
                          <span className="text-red-600">
                            • Critical Priority
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-orange-50 border-l-4 border-orange-500 rounded-r-lg">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-orange-500 text-white rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0">
                        2
                      </div>
                      <div>
                        <div className="font-bold text-orange-900 mb-1">
                          Accelerate Reasoning Capabilities
                        </div>
                        <div className="text-sm text-orange-800 mb-2">
                          GPT-5's reasoning performance sets new benchmark.
                          Prioritize advanced reasoning model development.
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <Clock className="w-3 h-3" />
                          <span className="font-medium">
                            Timeline: 2-4 weeks
                          </span>
                          <span className="text-orange-600">
                            • High Priority
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-lg">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-blue-500 text-white rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0">
                        3
                      </div>
                      <div>
                        <div className="font-bold text-blue-900 mb-1">
                          Monitor Enterprise Migration
                        </div>
                        <div className="text-sm text-blue-800 mb-2">
                          Track enterprise customers migrating to GPT-5 from
                          competing platforms. Monitor churn risk.
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <Clock className="w-3 h-3" />
                          <span className="font-medium">Timeline: Ongoing</span>
                          <span className="text-blue-600">
                            • Medium Priority
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Impact Areas */}
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 className="font-bold text-gray-900 mb-3">Impact Areas</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">Product Strategy</span>
                    <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-bold">
                      HIGH
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">Pricing Model</span>
                    <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-bold">
                      HIGH
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">Market Position</span>
                    <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs font-bold">
                      MED
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">Customer Retention</span>
                    <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs font-bold">
                      MED
                    </span>
                  </div>
                </div>
              </div>

              {/* Source Quality */}
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h4 className="font-bold text-blue-900 mb-3">
                  Source Quality Breakdown
                </h4>
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-blue-800">Tier 1 Sources</span>
                      <span className="font-bold text-blue-900">68%</span>
                    </div>
                    <div className="w-full bg-blue-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: "68%" }}
                      ></div>
                    </div>
                    <div className="text-xs text-blue-700 mt-1">
                      WSJ, Reuters, Bloomberg, TechCrunch
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-blue-800">Tier 2 Sources</span>
                      <span className="font-bold text-blue-900">22%</span>
                    </div>
                    <div className="w-full bg-blue-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: "22%" }}
                      ></div>
                    </div>
                    <div className="text-xs text-blue-700 mt-1">
                      Industry blogs, verified social
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-blue-800">Tier 3 Sources</span>
                      <span className="font-bold text-blue-900">10%</span>
                    </div>
                    <div className="w-full bg-blue-200 rounded-full h-2">
                      <div
                        className="bg-blue-400 h-2 rounded-full"
                        style={{ width: "10%" }}
                      ></div>
                    </div>
                    <div className="text-xs text-blue-700 mt-1">
                      Community, forums, press releases
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="space-y-3">
                <button className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                  <Share className="w-4 h-4" />
                  Share with Team
                </button>

                <button className="w-full flex items-center justify-center gap-2 bg-gray-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-gray-700 transition-colors">
                  <Download className="w-4 h-4" />
                  Export PDF
                </button>

                <button className="w-full flex items-center justify-center gap-2 border border-gray-300 text-gray-700 px-4 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors">
                  <ExternalLink className="w-4 h-4" />
                  View Full Analysis
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
