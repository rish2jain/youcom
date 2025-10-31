"use client";

import { useState } from "react";
import { AlertTriangle, RefreshCw, Home, ExternalLink } from "lucide-react";

interface ErrorDisplayProps {
  error: Error | string;
  onRetry?: () => void;
  context?: string;
}

export function ErrorDisplay({ error, onRetry, context }: ErrorDisplayProps) {
  const [isRetrying, setIsRetrying] = useState(false);

  const errorMessage = typeof error === "string" ? error : error.message;

  const getErrorType = (message: string) => {
    if (message.includes("Network") || message.includes("fetch"))
      return "network";
    if (message.includes("timeout")) return "timeout";
    if (message.includes("API") || message.includes("rate limit")) return "api";
    return "general";
  };

  const getRecoveryActions = (errorType: string) => {
    switch (errorType) {
      case "network":
        return [
          "Check your internet connection",
          "Try refreshing the page",
          "Contact support if the issue persists",
        ];
      case "timeout":
        return [
          "The request took too long to complete",
          "Try again in a few moments",
          "Consider reducing the scope of your request",
        ];
      case "api":
        return [
          "You.com API may be temporarily unavailable",
          "Check API status at status.you.com",
          "Try again in 30 seconds",
        ];
      default:
        return [
          "An unexpected error occurred",
          "Try refreshing the page",
          "Contact support if the problem continues",
        ];
    }
  };

  const handleRetry = async () => {
    if (!onRetry) return;

    setIsRetrying(true);
    try {
      await onRetry();
    } finally {
      setIsRetrying(false);
    }
  };

  const errorType = getErrorType(errorMessage);
  const recoveryActions = getRecoveryActions(errorType);

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-6">
      <div className="flex items-start space-x-3">
        <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-red-900 mb-2">
            {context ? `${context} Error` : "Something went wrong"}
          </h3>

          <p className="text-red-800 mb-4">{errorMessage}</p>

          <div className="mb-4">
            <h4 className="font-medium text-red-900 mb-2">What you can do:</h4>
            <ul className="space-y-1">
              {recoveryActions.map((action, index) => (
                <li
                  key={index}
                  className="flex items-start space-x-2 text-sm text-red-700"
                >
                  <span className="w-1.5 h-1.5 bg-red-400 rounded-full mt-2 flex-shrink-0"></span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex items-center space-x-3">
            {onRetry && (
              <button
                onClick={handleRetry}
                disabled={isRetrying}
                className="flex items-center space-x-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                <RefreshCw
                  className={`w-4 h-4 ${isRetrying ? "animate-spin" : ""}`}
                />
                <span>{isRetrying ? "Retrying..." : "Try Again"}</span>
              </button>
            )}

            <button
              onClick={() => window.location.reload()}
              className="flex items-center space-x-2 bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
            >
              <Home className="w-4 h-4" />
              <span>Refresh Page</span>
            </button>

            {errorType === "api" && (
              <a
                href="https://status.you.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-2 text-red-600 hover:text-red-700 text-sm font-medium"
              >
                <ExternalLink className="w-4 h-4" />
                <span>Check API Status</span>
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
