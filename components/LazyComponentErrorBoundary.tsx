"use client";

import React, { Component, ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface LazyComponentErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface LazyComponentErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  retryCount: number;
}

/**
 * Error boundary specifically designed for lazy-loaded components
 * Provides retry functionality and graceful degradation
 */
export class LazyComponentErrorBoundary extends Component<
  LazyComponentErrorBoundaryProps,
  LazyComponentErrorBoundaryState
> {
  private maxRetries = 3;

  constructor(props: LazyComponentErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(
    error: Error
  ): Partial<LazyComponentErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Lazy component loading error:", error, errorInfo);

    // Report to monitoring service if available
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Log to performance monitoring
    if (typeof window !== "undefined" && "performance" in window) {
      performance.mark("lazy-component-error");
    }
  }

  handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState((prevState) => ({
        hasError: false,
        error: null,
        retryCount: prevState.retryCount + 1,
      }));
    }
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI with retry option
      return (
        <div className="flex flex-col items-center justify-center p-6 bg-red-50 border border-red-200 rounded-lg">
          <AlertTriangle className="w-8 h-8 text-red-500 mb-3" />
          <h3 className="text-lg font-semibold text-red-800 mb-2">
            Component Failed to Load
          </h3>
          <p className="text-sm text-red-600 text-center mb-4">
            {this.state.error?.message ||
              "An unexpected error occurred while loading this component."}
          </p>

          {this.state.retryCount < this.maxRetries && (
            <button
              onClick={this.handleRetry}
              className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>
                Retry ({this.maxRetries - this.state.retryCount} attempts left)
              </span>
            </button>
          )}

          {this.state.retryCount >= this.maxRetries && (
            <div className="text-xs text-red-500 text-center">
              Maximum retry attempts reached. Please refresh the page.
            </div>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Higher-order component to wrap lazy components with error boundary
 */
export function withLazyErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode
) {
  const WrappedComponent = (props: P) => (
    <LazyComponentErrorBoundary fallback={fallback}>
      <Component {...props} />
    </LazyComponentErrorBoundary>
  );

  WrappedComponent.displayName = `withLazyErrorBoundary(${
    Component.displayName || Component.name
  })`;

  return WrappedComponent;
}
