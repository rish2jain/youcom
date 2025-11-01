"use client";

import { Play, Settings, ArrowRight, HelpCircle, Info } from "lucide-react";

interface SampleDataBannerProps {
  onAddApiKey?: () => void;
  onContinueDemo?: () => void;
}

export function SampleDataBanner({
  onAddApiKey,
  onContinueDemo,
}: SampleDataBannerProps) {
  return (
    <div className="bg-gradient-to-r from-amber-50 to-yellow-50 border-l-4 border-amber-500 rounded-xl p-6 shadow-lg mb-8">
      <div className="flex items-start gap-6">
        <div className="w-16 h-16 bg-amber-500 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
          <Play className="w-8 h-8 text-white" />
        </div>
        <div className="flex-1">
          <h3 className="font-bold text-gray-900 mb-3 text-xl">
            🚀 Interactive Demo Platform
          </h3>
          <p className="text-gray-800 leading-relaxed mb-6">
            Experience the full Enterprise CIA platform with curated
            intelligence data for{" "}
            <strong className="text-amber-700">OpenAI</strong>,{" "}
            <strong className="text-amber-700">Anthropic</strong>, and{" "}
            <strong className="text-amber-700">Google AI</strong>. All You.com
            API orchestration is fully functional—intelligent caching optimizes
            costs while demonstrating real-time capabilities.
          </p>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <button
              onClick={onAddApiKey}
              className="flex items-center gap-3 px-6 py-3 bg-amber-600 text-white rounded-lg font-semibold hover:bg-amber-700 transition-all duration-200 shadow-sm min-h-[44px]"
              aria-label="Add your You.com API key to use live data instead of sample data"
            >
              <Settings className="w-5 h-5" />
              <span>Add Your API Key for Live Data</span>
            </button>

            <div className="flex items-center gap-3 text-sm text-gray-700">
              <span>or</span>
              <button
                onClick={onContinueDemo}
                className="flex items-center gap-2 text-amber-700 font-semibold hover:text-amber-800 transition-colors underline min-h-[44px]"
                aria-label="Continue exploring the demo with sample data"
              >
                <span>continue exploring with sample data</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-amber-200">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
              <div className="flex items-start gap-2">
                <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="font-semibold text-blue-900 mb-1">
                    Demo vs Live Data
                  </div>
                  <div className="text-sm text-blue-800">
                    <strong>Sample Data:</strong> Curated examples that showcase all features without using API credits. 
                    <strong> Live Data:</strong> Add your API key to use real-time You.com API calls with intelligent caching to optimize costs.
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-gray-700">All 4 APIs Active</span>
                <div className="group relative">
                  <HelpCircle className="w-4 h-4 text-gray-400 cursor-help" />
                  <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 p-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-10">
                    News, Search, Chat, and ARI APIs are operational
                  </div>
                </div>
              </div>
              <div className="w-px h-4 bg-amber-300"></div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-gray-700">Sample data includes:</span>
                <span className="px-2 py-1 bg-amber-100 text-amber-800 rounded text-xs font-medium">
                  4 Impact Cards
                </span>
                <span className="px-2 py-1 bg-amber-100 text-amber-800 rounded text-xs font-medium">
                  35 API Calls
                </span>
                <span className="px-2 py-1 bg-amber-100 text-amber-800 rounded text-xs font-medium">
                  400+ Sources
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
