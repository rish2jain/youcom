/**
 * Prefetching performance monitor component
 * Displays real-time prefetching analytics and performance metrics
 */

import React, { useState, useEffect } from "react";
import {
  Activity,
  Zap,
  Target,
  BarChart3,
  Settings,
  RefreshCw,
} from "lucide-react";
import { useIntelligentPrefetching } from "@/lib/hooks/useIntelligentPrefetching";

interface PrefetchingMonitorProps {
  isVisible?: boolean;
  position?: "top-right" | "bottom-right" | "bottom-left" | "top-left";
  compact?: boolean;
}

export const PrefetchingMonitor: React.FC<PrefetchingMonitorProps> = ({
  isVisible = false,
  position = "bottom-right",
  compact = false,
}) => {
  const {
    prefetchingState,
    getPrefetchRecommendations,
    getDetailedAnalytics,
    togglePrefetching,
    resetBehaviorData,
    currentRoute,
  } = useIntelligentPrefetching();

  const [isExpanded, setIsExpanded] = useState(false);
  const [analytics, setAnalytics] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);

  // Update analytics periodically
  useEffect(() => {
    const updateAnalytics = () => {
      setAnalytics(getDetailedAnalytics());
      setRecommendations(getPrefetchRecommendations());
    };

    updateAnalytics();
    const interval = setInterval(updateAnalytics, 2000);

    return () => clearInterval(interval);
  }, [getDetailedAnalytics, getPrefetchRecommendations]);

  if (!isVisible) return null;

  const positionClasses = {
    "top-right": "top-4 right-4",
    "bottom-right": "bottom-4 right-4",
    "bottom-left": "bottom-4 left-4",
    "top-left": "top-4 left-4",
  };

  const formatHitRate = (rate: number) => `${(rate * 100).toFixed(1)}%`;
  const formatRoute = (route: string) =>
    route.charAt(0).toUpperCase() + route.slice(1);

  return (
    <div className={`fixed ${positionClasses[position]} z-50 max-w-sm`}>
      {/* Compact View */}
      {compact && !isExpanded && (
        <div
          className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 cursor-pointer hover:shadow-xl transition-shadow"
          onClick={() => setIsExpanded(true)}
        >
          <div className="flex items-center space-x-2">
            <div
              className={`w-3 h-3 rounded-full ${
                prefetchingState.isActive ? "bg-green-500" : "bg-gray-400"
              }`}
            ></div>
            <span className="text-sm font-medium">Prefetch</span>
            <div className="text-xs text-gray-500">
              {prefetchingState.prefetchedRoutes.length} cached
            </div>
          </div>
        </div>
      )}

      {/* Expanded View */}
      {(!compact || isExpanded) && (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Zap className="w-5 h-5" />
                <span className="font-semibold">Route Prefetching</span>
              </div>
              {compact && (
                <button
                  onClick={() => setIsExpanded(false)}
                  className="text-white hover:text-gray-200"
                >
                  ×
                </button>
              )}
            </div>
            <div className="text-sm opacity-90 mt-1">
              Current: {formatRoute(currentRoute)}
            </div>
          </div>

          {/* Status */}
          <div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div
                  className={`w-3 h-3 rounded-full ${
                    prefetchingState.isActive ? "bg-green-500" : "bg-red-500"
                  }`}
                ></div>
                <span className="text-sm font-medium">
                  {prefetchingState.isActive ? "Active" : "Inactive"}
                </span>
              </div>
              <button
                onClick={() => togglePrefetching(!prefetchingState.isActive)}
                className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
              >
                {prefetchingState.isActive ? "Disable" : "Enable"}
              </button>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-blue-50 p-2 rounded">
                <div className="flex items-center space-x-1">
                  <Target className="w-4 h-4 text-blue-600" />
                  <span className="text-xs text-blue-800">Hit Rate</span>
                </div>
                <div className="text-lg font-bold text-blue-900">
                  {formatHitRate(prefetchingState.hitRate)}
                </div>
              </div>

              <div className="bg-green-50 p-2 rounded">
                <div className="flex items-center space-x-1">
                  <Activity className="w-4 h-4 text-green-600" />
                  <span className="text-xs text-green-800">Cached</span>
                </div>
                <div className="text-lg font-bold text-green-900">
                  {prefetchingState.prefetchedRoutes.length}
                </div>
              </div>
            </div>

            {/* Queue Status */}
            {prefetchingState.queueLength > 0 && (
              <div className="bg-yellow-50 p-2 rounded">
                <div className="flex items-center space-x-1">
                  <RefreshCw className="w-4 h-4 text-yellow-600" />
                  <span className="text-xs text-yellow-800">Queue</span>
                </div>
                <div className="text-sm text-yellow-900">
                  {prefetchingState.queueLength} routes pending
                </div>
              </div>
            )}

            {/* Prefetched Routes */}
            {prefetchingState.prefetchedRoutes.length > 0 && (
              <div>
                <div className="text-xs font-medium text-gray-700 mb-2">
                  Prefetched Routes
                </div>
                <div className="flex flex-wrap gap-1">
                  {prefetchingState.prefetchedRoutes
                    .slice(0, 6)
                    .map((route) => (
                      <span
                        key={route}
                        className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded"
                      >
                        {formatRoute(route)}
                      </span>
                    ))}
                  {prefetchingState.prefetchedRoutes.length > 6 && (
                    <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                      +{prefetchingState.prefetchedRoutes.length - 6}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {recommendations.length > 0 && (
              <div>
                <div className="text-xs font-medium text-gray-700 mb-2">
                  Next Likely Routes
                </div>
                <div className="space-y-1">
                  {recommendations.slice(0, 3).map(({ route, probability }) => (
                    <div
                      key={route}
                      className="flex items-center justify-between text-xs"
                    >
                      <span className="text-gray-800">
                        {formatRoute(route)}
                      </span>
                      <div className="flex items-center space-x-1">
                        <div className="w-8 bg-gray-200 rounded-full h-1">
                          <div
                            className="bg-blue-500 h-1 rounded-full"
                            style={{
                              width: `${Math.min(probability * 20, 100)}%`,
                            }}
                          ></div>
                        </div>
                        <span className="text-gray-500">{probability}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Analytics Summary */}
            {analytics && (
              <div className="border-t pt-3">
                <div className="text-xs font-medium text-gray-700 mb-2">
                  Session Analytics
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-600">Routes Visited:</span>
                    <span className="ml-1 font-medium">
                      {new Set(analytics.behaviorData.visitedRoutes).size}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Total Visits:</span>
                    <span className="ml-1 font-medium">
                      {analytics.behaviorData.visitedRoutes.length}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Controls */}
            <div className="border-t pt-3 flex space-x-2">
              <button
                onClick={resetBehaviorData}
                className="flex-1 text-xs px-2 py-1 bg-red-50 text-red-700 hover:bg-red-100 rounded transition-colors"
              >
                Reset Data
              </button>
              <button
                onClick={() => window.location.reload()}
                className="flex-1 text-xs px-2 py-1 bg-gray-50 text-gray-700 hover:bg-gray-100 rounded transition-colors"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Development-only prefetching monitor
export const DevPrefetchingMonitor: React.FC = () => {
  const [isVisible, setIsVisible] = useState(false);

  // Only show in development
  useEffect(() => {
    setIsVisible(process.env.NODE_ENV === "development");
  }, []);

  // Keyboard shortcut to toggle (Ctrl/Cmd + Shift + P)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "P") {
        e.preventDefault();
        setIsVisible((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <PrefetchingMonitor
      isVisible={isVisible}
      position="bottom-right"
      compact={true}
    />
  );
};
