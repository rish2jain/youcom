"use client";

import { ArrowRight, Clock, CheckCircle } from "lucide-react";

export function APIPipelineVisual() {
  return (
    <div className="bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 border-2 border-blue-200 rounded-xl p-8 shadow-lg">
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          🔄 4-API Orchestration Pipeline
        </h3>
        <p className="text-gray-600">
          Watch how Enterprise CIA coordinates all You.com APIs in perfect
          sequence
        </p>
      </div>

      <div className="flex flex-col lg:flex-row items-center justify-between gap-6">
        {/* Step 1: News API */}
        <div className="flex-1 text-center">
          <div className="w-20 h-20 bg-blue-500 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <span className="text-3xl">📰</span>
          </div>
          <h4 className="font-bold text-blue-900 mb-2">1. News API</h4>
          <p className="text-sm text-gray-700 mb-2">Real-time detection</p>
          <div className="bg-blue-100 rounded-lg p-2 text-xs text-blue-800">
            <div className="font-medium">12 articles found</div>
            <div className="flex items-center justify-center gap-1 mt-1">
              <Clock className="w-3 h-3" />
              <span>&lt;60 seconds</span>
            </div>
          </div>
        </div>

        <ArrowRight className="w-8 h-8 text-gray-400 hidden lg:block" />
        <div className="lg:hidden w-full h-px bg-gray-300"></div>

        {/* Step 2: Search API */}
        <div className="flex-1 text-center">
          <div className="w-20 h-20 bg-green-500 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <span className="text-3xl">🔍</span>
          </div>
          <h4 className="font-bold text-green-900 mb-2">2. Search API</h4>
          <p className="text-sm text-gray-700 mb-2">Context enrichment</p>
          <div className="bg-green-100 rounded-lg p-2 text-xs text-green-800">
            <div className="font-medium">8 sources added</div>
            <div className="flex items-center justify-center gap-1 mt-1">
              <Clock className="w-3 h-3" />
              <span>~30 seconds</span>
            </div>
          </div>
        </div>

        <ArrowRight className="w-8 h-8 text-gray-400 hidden lg:block" />
        <div className="lg:hidden w-full h-px bg-gray-300"></div>

        {/* Step 3: Chat API */}
        <div className="flex-1 text-center">
          <div className="w-20 h-20 bg-purple-500 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <span className="text-3xl">🤖</span>
          </div>
          <h4 className="font-bold text-purple-900 mb-2">3. Chat API</h4>
          <p className="text-sm text-gray-700 mb-2">Strategic analysis</p>
          <div className="bg-purple-100 rounded-lg p-2 text-xs text-purple-800">
            <div className="font-medium">Threat: 8.8/10</div>
            <div className="flex items-center justify-center gap-1 mt-1">
              <Clock className="w-3 h-3" />
              <span>~45 seconds</span>
            </div>
          </div>
        </div>

        <ArrowRight className="w-8 h-8 text-gray-400 hidden lg:block" />
        <div className="lg:hidden w-full h-px bg-gray-300"></div>

        {/* Step 4: ARI API */}
        <div className="flex-1 text-center">
          <div className="w-20 h-20 bg-orange-500 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <span className="text-3xl">🧠</span>
          </div>
          <h4 className="font-bold text-orange-900 mb-2">4. ARI API</h4>
          <p className="text-sm text-gray-700 mb-2">Deep synthesis</p>
          <div className="bg-orange-100 rounded-lg p-2 text-xs text-orange-800">
            <div className="font-medium">400+ sources</div>
            <div className="flex items-center justify-center gap-1 mt-1">
              <Clock className="w-3 h-3" />
              <span>~60 seconds</span>
            </div>
          </div>
        </div>
      </div>

      {/* Result */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <div className="bg-green-50 border-2 border-green-300 rounded-xl p-6">
          <div className="flex items-center justify-center gap-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
            <div className="text-center">
              <h4 className="font-bold text-green-900 text-lg">
                Complete Impact Card Generated
              </h4>
              <p className="text-green-800 text-sm">
                Total time: <strong>2 minutes 14 seconds</strong> • Sources:{" "}
                <strong>412</strong> • Confidence: <strong>92%</strong>
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-600 italic">
          This is the only platform demonstrating true 4-API orchestration for
          competitive intelligence
        </p>
      </div>
    </div>
  );
}
