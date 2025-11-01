"use client";

import React from "react";
import {
  useLoadingStateStore,
  LoadingMetrics,
} from "@/lib/loading-state-manager";
import { Progress } from "@/components/ui/progress";
import { Loader2, CheckCircle, AlertCircle } from "lucide-react";

interface LoadingProgressIndicatorProps {
  showDetails?: boolean;
  className?: string;
  compact?: boolean;
}

/**
 * Visual indicator for overall loading progress
 */
export function LoadingProgressIndicator({
  showDetails = false,
  className = "",
  compact = false,
}: LoadingProgressIndicatorProps) {
  const metrics = useLoadingStateStore((state) => state.metrics);
  const states = useLoadingStateStore((state) => state.states);

  if (!metrics.isLoading && metrics.totalComponents === 0) {
    return null;
  }

  if (compact) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        {metrics.isLoading && (
          <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
        )}
        <div className="text-sm text-gray-600">
          {metrics.loadedComponents}/{metrics.totalComponents} loaded
        </div>
      </div>
    );
  }

  return (
    <div
      className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}
    >
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-gray-900">
          Loading Progress
        </h4>
        <div className="flex items-center space-x-2">
          {metrics.isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
          ) : metrics.failedComponents > 0 ? (
            <AlertCircle className="w-4 h-4 text-red-500" />
          ) : (
            <CheckCircle className="w-4 h-4 text-green-500" />
          )}
          <span className="text-sm text-gray-600">
            {Math.round(metrics.overallProgress)}%
          </span>
        </div>
      </div>

      <Progress value={metrics.overallProgress} className="mb-3" />

      <div className="flex justify-between text-xs text-gray-500 mb-2">
        <span>
          {metrics.loadedComponents}/{metrics.totalComponents} components loaded
        </span>
        {metrics.averageLoadTime > 0 && (
          <span>Avg: {Math.round(metrics.averageLoadTime)}ms</span>
        )}
      </div>

      {metrics.failedComponents > 0 && (
        <div className="text-xs text-red-600 mb-2">
          {metrics.failedComponents} component(s) failed to load
        </div>
      )}

      {showDetails && (
        <div className="mt-3 space-y-1" role="status" aria-live="polite">
          {Array.from(states.entries()).map(([component, state]) => (
            <div
              key={component}
              className="flex items-center justify-between text-xs"
            >
              <span className="text-gray-600 truncate flex-1">{component}</span>
              <div className="flex items-center space-x-2 ml-2">
                {state.status === "loading" && (
                  <>
                    <Loader2
                      className="w-3 h-3 animate-spin text-blue-500"
                      aria-label={`${component} loading`}
                    />
                    <span className="text-blue-600">
                      {state.progress || 0}%
                    </span>
                  </>
                )}
                {state.status === "loaded" && (
                  <CheckCircle
                    className="w-3 h-3 text-green-500"
                    aria-label={`${component} loaded`}
                  />
                )}
                {state.status === "error" && (
                  <AlertCircle
                    className="w-3 h-3 text-red-500"
                    aria-label={`${component} error`}
                  />
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Hook for component-specific loading state
 */
export function useComponentLoadingState(componentName: string) {
  const setLoading = useLoadingStateStore((state) => state.setLoading);
  const setLoaded = useLoadingStateStore((state) => state.setLoaded);
  const setError = useLoadingStateStore((state) => state.setError);
  const setProgress = useLoadingStateStore((state) => state.setProgress);
  const getState = useLoadingStateStore((state) => state.getState);
  const reset = useLoadingStateStore((state) => state.reset);

  const currentState = getState(componentName);

  return {
    state: currentState,
    isLoading: currentState?.status === "loading",
    isLoaded: currentState?.status === "loaded",
    hasError: currentState?.status === "error",
    progress: currentState?.progress || 0,
    setLoading: (progress?: number) => setLoading(componentName, progress),
    setLoaded: () => setLoaded(componentName),
    setError: (error: string) => setError(componentName, error),
    setProgress: (progress: number) => setProgress(componentName, progress),
    reset: () => reset(componentName),
  };
}
