/**
 * Tests for RouteLoadingBoundary component
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { RouteLoadingBoundary } from "../RouteLoadingBoundary";

// Mock the skeleton components
jest.mock("../LoadingSkeleton", () => ({
  LoadingSkeleton: () => (
    <div data-testid="loading-skeleton">Loading Skeleton</div>
  ),
}));

jest.mock("../skeletons/DashboardSkeleton", () => ({
  DashboardSkeleton: () => (
    <div data-testid="dashboard-skeleton">Dashboard Skeleton</div>
  ),
}));

// Mock error boundary
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error("Test error");
  }
  return <div data-testid="success-content">Success Content</div>;
};

const AsyncComponent = ({
  delay = 100,
  shouldReject = false,
}: {
  delay?: number;
  shouldReject?: boolean;
}) => {
  const [isLoaded, setIsLoaded] = React.useState(false);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (shouldReject) {
        throw new Error("Async component failed");
      }
      setIsLoaded(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay, shouldReject]);

  if (!isLoaded) {
    return null; // This will trigger Suspense
  }

  return <div data-testid="async-content">Async Content Loaded</div>;
};

describe("RouteLoadingBoundary", () => {
  beforeEach(() => {
    // Clear console mocks
    jest.clearAllMocks();
  });

  describe("Suspense Functionality", () => {
    it("should show loading skeleton while content is loading", async () => {
      render(
        <RouteLoadingBoundary routeKey="dashboard">
          <AsyncComponent delay={200} />
        </RouteLoadingBoundary>
      );

      // Should show dashboard skeleton initially
      expect(screen.getByTestId("dashboard-skeleton")).toBeInTheDocument();

      // Wait for content to load
      await waitFor(
        () => {
          expect(screen.getByTestId("async-content")).toBeInTheDocument();
        },
        { timeout: 300 }
      );

      // Skeleton should be gone
      expect(
        screen.queryByTestId("dashboard-skeleton")
      ).not.toBeInTheDocument();
    });

    it("should show route-specific skeletons", () => {
      const routes = ["dashboard", "research", "analytics", "monitoring"];

      routes.forEach((route) => {
        const { unmount } = render(
          <RouteLoadingBoundary routeKey={route}>
            <AsyncComponent delay={1000} />
          </RouteLoadingBoundary>
        );

        // Should show appropriate skeleton
        if (route === "dashboard") {
          expect(screen.getByTestId("dashboard-skeleton")).toBeInTheDocument();
        } else {
          // Other routes should show generic loading skeleton
          expect(screen.getByTestId("loading-skeleton")).toBeInTheDocument();
        }

        unmount();
      });
    });

    it("should use custom fallback when provided", () => {
      const customFallback = (
        <div data-testid="custom-fallback">Custom Loading</div>
      );

      render(
        <RouteLoadingBoundary routeKey="dashboard" fallback={customFallback}>
          <AsyncComponent delay={200} />
        </RouteLoadingBoundary>
      );

      expect(screen.getByTestId("custom-fallback")).toBeInTheDocument();
      expect(
        screen.queryByTestId("dashboard-skeleton")
      ).not.toBeInTheDocument();
    });
  });

  describe("Error Boundary Functionality", () => {
    it("should catch and display error fallback", () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      render(
        <RouteLoadingBoundary routeKey="dashboard">
          <ThrowError shouldThrow={true} />
        </RouteLoadingBoundary>
      );

      // Should show error fallback
      expect(screen.getByText(/Failed to Load Dashboard/)).toBeInTheDocument();
      expect(
        screen.getByText(/There was an error loading this page/)
      ).toBeInTheDocument();

      consoleSpy.mockRestore();
    });

    it("should show route-specific error messages", () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      const routes = [
        { key: "dashboard", expected: "Failed to Load Dashboard" },
        { key: "research", expected: "Failed to Load Research" },
        { key: "analytics", expected: "Failed to Load Analytics" },
      ];

      routes.forEach(({ key, expected }) => {
        const { unmount } = render(
          <RouteLoadingBoundary routeKey={key}>
            <ThrowError shouldThrow={true} />
          </RouteLoadingBoundary>
        );

        expect(screen.getByText(expected)).toBeInTheDocument();
        unmount();
      });

      consoleSpy.mockRestore();
    });

    it("should provide error recovery options", () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      render(
        <RouteLoadingBoundary routeKey="dashboard">
          <ThrowError shouldThrow={true} />
        </RouteLoadingBoundary>
      );

      // Should have Try Again button
      expect(screen.getByText("Try Again")).toBeInTheDocument();

      // Should have Go to Dashboard button
      expect(screen.getByText("Go to Dashboard")).toBeInTheDocument();

      consoleSpy.mockRestore();
    });

    it("should show error details in development", () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = "development";

      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      render(
        <RouteLoadingBoundary routeKey="dashboard">
          <ThrowError shouldThrow={true} />
        </RouteLoadingBoundary>
      );

      // Should show error details section
      expect(screen.getByText("Error Details")).toBeInTheDocument();

      process.env.NODE_ENV = originalEnv;
      consoleSpy.mockRestore();
    });

    it("should not show error details in production", () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = "production";

      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      render(
        <RouteLoadingBoundary routeKey="dashboard">
          <ThrowError shouldThrow={true} />
        </RouteLoadingBoundary>
      );

      // Should not show error details section
      expect(screen.queryByText("Error Details")).not.toBeInTheDocument();

      process.env.NODE_ENV = originalEnv;
      consoleSpy.mockRestore();
    });
  });

  describe("Error Reporting", () => {
    it("should log errors to console", () => {
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      render(
        <RouteLoadingBoundary routeKey="dashboard">
          <ThrowError shouldThrow={true} />
        </RouteLoadingBoundary>
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Route loading error for dashboard"),
        expect.any(Error),
        expect.any(Object)
      );

      consoleSpy.mockRestore();
    });

    it("should report errors in production environment", () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = "production";

      // Mock window object
      Object.defineProperty(window, "location", {
        value: { href: "http://localhost" },
        writable: true,
      });

      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      render(
        <RouteLoadingBoundary routeKey="dashboard">
          <ThrowError shouldThrow={true} />
        </RouteLoadingBoundary>
      );

      expect(consoleSpy).toHaveBeenCalledWith(
        "Route error reported:",
        expect.objectContaining({
          routeKey: "dashboard",
          error: "Test error",
        })
      );

      process.env.NODE_ENV = originalEnv;
      consoleSpy.mockRestore();
    });
  });

  describe("Successful Loading", () => {
    it("should render children when no errors occur", async () => {
      render(
        <RouteLoadingBoundary routeKey="dashboard">
          <div data-testid="success-content">Success Content</div>
        </RouteLoadingBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId("success-content")).toBeInTheDocument();
      });
    });

    it("should handle multiple children", async () => {
      render(
        <RouteLoadingBoundary routeKey="dashboard">
          <div data-testid="child-1">Child 1</div>
          <div data-testid="child-2">Child 2</div>
        </RouteLoadingBoundary>
      );

      await waitFor(() => {
        expect(screen.getByTestId("child-1")).toBeInTheDocument();
        expect(screen.getByTestId("child-2")).toBeInTheDocument();
      });
    });
  });

  describe("Route Key Validation", () => {
    it("should handle unknown route keys gracefully", () => {
      render(
        <RouteLoadingBoundary routeKey="unknown-route">
          <AsyncComponent delay={200} />
        </RouteLoadingBoundary>
      );

      // Should fall back to generic loading skeleton
      expect(screen.getByTestId("loading-skeleton")).toBeInTheDocument();
    });

    it("should handle empty route keys", () => {
      render(
        <RouteLoadingBoundary routeKey="">
          <AsyncComponent delay={200} />
        </RouteLoadingBoundary>
      );

      // Should fall back to generic loading skeleton
      expect(screen.getByTestId("loading-skeleton")).toBeInTheDocument();
    });
  });
});
