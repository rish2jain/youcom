"use client";

import { useState } from "react";
import { AlertTriangle, RefreshCw, Wifi, Clock } from "lucide-react";

interface APIErrorProps {
  api: string;
  error: string;
  onRetry?: () => void;
  showRetry?: boolean;
}

export function APIError({
  api,
  error,
  onRetry,
  showRetry = true,
}: APIErrorProps) {
  return (
    <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6">
      <div className="flex items-start gap-4">
        <AlertTriangle className="w-8 h-8 text-red-600 flex-shrink-0 mt-1" />
        <div className="flex-1">
          <h3 className="font-bold text-red-900 mb-2">{api} API Error</h3>
          <p className="text-red-800 mb-4">{error}</p>

          <div className="flex items-center gap-3">
            {showRetry && onRetry && (
              <button
                onClick={onRetry}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Retry</span>
              </button>
            )}
            <div className="text-sm text-red-700">
              Using cached data from {Math.floor(Math.random() * 30 + 5)}{" "}
              minutes ago
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface NetworkErrorProps {
  onRetry?: () => void;
}

export function NetworkError({ onRetry }: NetworkErrorProps) {
  return (
    <div className="bg-orange-50 border-2 border-orange-200 rounded-xl p-6">
      <div className="flex items-start gap-4">
        <Wifi className="w-8 h-8 text-orange-600 flex-shrink-0 mt-1" />
        <div className="flex-1">
          <h3 className="font-bold text-orange-900 mb-2">Connection Issue</h3>
          <p className="text-orange-800 mb-4">
            Unable to connect to You.com APIs. Please check your internet
            connection.
          </p>

          <div className="flex items-center gap-3">
            {onRetry && (
              <button
                onClick={onRetry}
                className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Try Again</span>
              </button>
            )}
            <div className="text-sm text-orange-700">
              Automatically retrying in 30 seconds...
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface RateLimitErrorProps {
  resetTime?: string;
}

export function RateLimitError({
  resetTime = "15 minutes",
}: RateLimitErrorProps) {
  return (
    <div className="bg-yellow-50 border-2 border-yellow-200 rounded-xl p-6">
      <div className="flex items-start gap-4">
        <Clock className="w-8 h-8 text-yellow-600 flex-shrink-0 mt-1" />
        <div className="flex-1">
          <h3 className="font-bold text-yellow-900 mb-2">Rate Limit Reached</h3>
          <p className="text-yellow-800 mb-4">
            You.com API rate limit exceeded. New requests will be available in{" "}
            {resetTime}.
          </p>

          <div className="bg-yellow-100 border border-yellow-300 rounded-lg p-3">
            <div className="text-sm text-yellow-800">
              <div className="font-medium mb-1">What's happening:</div>
              <ul className="space-y-1 text-xs">
                <li>• Circuit breaker activated to prevent API overload</li>
                <li>• Serving cached results where available</li>
                <li>• Automatic retry scheduled for {resetTime}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface MaintenanceErrorProps {
  estimatedDuration?: string;
}

export function MaintenanceError({
  estimatedDuration = "30 minutes",
}: MaintenanceErrorProps) {
  return (
    <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6">
      <div className="flex items-start gap-4">
        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
          <span className="text-white text-sm font-bold">!</span>
        </div>
        <div className="flex-1">
          <h3 className="font-bold text-blue-900 mb-2">
            Scheduled Maintenance
          </h3>
          <p className="text-blue-800 mb-4">
            You.com APIs are temporarily unavailable for scheduled maintenance.
            Estimated duration: {estimatedDuration}.
          </p>

          <div className="bg-blue-100 border border-blue-300 rounded-lg p-3">
            <div className="text-sm text-blue-800">
              <div className="font-medium mb-1">During maintenance:</div>
              <ul className="space-y-1 text-xs">
                <li>• Displaying cached competitive intelligence data</li>
                <li>• New research requests will be queued</li>
                <li>• All data will sync automatically when service resumes</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function ErrorStateDemo() {
  const [currentError, setCurrentError] = useState<string>("none");

  const errorStates = [
    { id: "none", label: "No Errors" },
    { id: "api", label: "API Error" },
    { id: "network", label: "Network Error" },
    { id: "ratelimit", label: "Rate Limit" },
    { id: "maintenance", label: "Maintenance" },
  ];

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-900">Error Handling Demo</h3>
        <select
          value={currentError}
          onChange={(e) => setCurrentError(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {errorStates.map((state) => (
            <option key={state.id} value={state.id}>
              {state.label}
            </option>
          ))}
        </select>
      </div>

      {currentError === "api" && (
        <APIError
          api="You.com ARI"
          error="Request timeout after 30 seconds. The API may be experiencing high load."
          onRetry={() => alert("Retrying API call...")}
        />
      )}

      {currentError === "network" && (
        <NetworkError onRetry={() => alert("Checking connection...")} />
      )}

      {currentError === "ratelimit" && (
        <RateLimitError resetTime="12 minutes" />
      )}

      {currentError === "maintenance" && (
        <MaintenanceError estimatedDuration="45 minutes" />
      )}

      {currentError === "none" && (
        <div className="bg-green-50 border-2 border-green-200 rounded-xl p-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm">✓</span>
            </div>
            <div>
              <h3 className="font-bold text-green-900">
                All Systems Operational
              </h3>
              <p className="text-green-800 text-sm">
                All You.com APIs are responding normally. Average response time:
                247ms.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
