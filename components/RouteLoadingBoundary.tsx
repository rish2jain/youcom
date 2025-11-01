/**
 * Route-specific loading boundary with Suspense and error handling
 * Provides optimized loading states for different route types
 */

import React, { Suspense, ReactNode, Component, ErrorInfo } from "react";
import { LoadingSkeleton } from "./LoadingSkeleton";
import { DashboardSkeleton } from "./skeletons/DashboardSkeleton";

interface RouteLoadingBoundaryProps {
  children: ReactNode;
  routeKey: string;
  fallback?: ReactNode;
}

interface ErrorBoundaryProps
  extends Omit<RouteLoadingBoundaryProps, "fallback"> {
  fallback: (error: Error, retry: () => void) => ReactNode;
}

// Route-specific loading skeletons
const getRouteSkeleton = (routeKey: string): ReactNode => {
  switch (routeKey) {
    case "dashboard":
      return <DashboardSkeleton />;
    case "research":
      return (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-2/3 mb-6"></div>
              <div className="h-12 bg-gray-200 rounded mb-4"></div>
            </div>
          </div>
          <LoadingSkeleton />
        </div>
      );
    case "analytics":
      return (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-24 bg-gray-200 rounded"></div>
                ))}
              </div>
              <div className="h-64 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      );
    case "monitoring":
      return (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
              <div className="space-y-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="h-20 bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      );
    default:
      return <LoadingSkeleton />;
  }
};

// Custom Error Boundary implementation
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class CustomErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps | Readonly<ErrorBoundaryProps>) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const routeKey = this.props.routeKey;
    console.error(`Route loading error for ${routeKey}`, error, errorInfo);

    // Error tracking (sanitized for production)
    if (process.env.NODE_ENV === "production") {
      console.error({
        routeKey,
        error: error.message,
        location: window.location.origin + window.location.pathname,
      });

      // TODO: Forward to error tracking service (Sentry/Bugsnag/DataDog)
      // errorTracker.captureException(error, { routeKey, sanitizedLocation });
    }
  }

  render() {
    if (this.state.hasError && this.state.error) {
      return this.props.fallback(this.state.error, () => {
        this.setState({ hasError: false, error: null });
      });
    }

    return this.props.children;
  }
}

// Route-specific error fallback
const RouteErrorFallback = ({
  error,
  resetErrorBoundary,
  routeKey,
}: {
  error: Error;
  resetErrorBoundary: () => void;
  routeKey: string;
}) => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50">
    <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
      <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
        <svg
          className="w-8 h-8 text-red-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
      </div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Failed to Load {routeKey.charAt(0).toUpperCase() + routeKey.slice(1)}
      </h2>
      <p className="text-gray-600 mb-4">
        There was an error loading this page. This might be due to a network
        issue or a temporary problem.
      </p>
      <div className="space-y-2">
        <button
          onClick={resetErrorBoundary}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
        <button
          onClick={() => (window.location.href = "/")}
          className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
        >
          Go to Dashboard
        </button>
      </div>
      {process.env.NODE_ENV === "development" && (
        <details className="mt-4 text-left">
          <summary className="cursor-pointer text-sm text-gray-500">
            Error Details
          </summary>
          <pre className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded overflow-auto">
            {error.message}
          </pre>
        </details>
      )}
    </div>
  </div>
);

export const RouteLoadingBoundary: React.FC<RouteLoadingBoundaryProps> = ({
  children,
  routeKey,
  fallback,
}) => {
  return (
    <CustomErrorBoundary
      routeKey={routeKey}
      fallback={(error, reset) => (
        <RouteErrorFallback
          error={error}
          resetErrorBoundary={reset}
          routeKey={routeKey}
        />
      )}
    >
      <Suspense fallback={fallback || getRouteSkeleton(routeKey)}>
        {children}
      </Suspense>
    </CustomErrorBoundary>
  );
};
