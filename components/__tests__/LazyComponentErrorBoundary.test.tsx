/**
 * Tests for LazyComponentErrorBoundary
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  LazyComponentErrorBoundary,
  withLazyErrorBoundary,
} from "../LazyComponentErrorBoundary";

// Mock component that throws an error
const ThrowingComponent = ({
  shouldThrow = true,
}: {
  shouldThrow?: boolean;
}) => {
  if (shouldThrow) {
    throw new Error("Test error");
  }
  return <div>Working component</div>;
};

// Mock component that works
const WorkingComponent = () => <div>Working component</div>;

describe("LazyComponentErrorBoundary", () => {
  // Suppress console.error for these tests
  const originalError = console.error;
  beforeAll(() => {
    console.error = jest.fn();
  });
  afterAll(() => {
    console.error = originalError;
  });

  it("renders children when no error occurs", () => {
    render(
      <LazyComponentErrorBoundary>
        <WorkingComponent />
      </LazyComponentErrorBoundary>
    );

    expect(screen.getByText("Working component")).toBeInTheDocument();
  });

  it("renders error UI when child component throws", () => {
    render(
      <LazyComponentErrorBoundary>
        <ThrowingComponent />
      </LazyComponentErrorBoundary>
    );

    expect(screen.getByText("Component Failed to Load")).toBeInTheDocument();
    expect(screen.getByText("Test error")).toBeInTheDocument();
  });

  it("shows retry button when error occurs", () => {
    render(
      <LazyComponentErrorBoundary>
        <ThrowingComponent />
      </LazyComponentErrorBoundary>
    );

    const retryButton = screen.getByRole("button", { name: /retry/i });
    expect(retryButton).toBeInTheDocument();
    expect(retryButton).toHaveTextContent("Retry (3 attempts left)");
  });

  it("decreases retry attempts when retry is clicked", () => {
    render(
      <LazyComponentErrorBoundary>
        <ThrowingComponent />
      </LazyComponentErrorBoundary>
    );

    const retryButton = screen.getByRole("button", { name: /retry/i });
    fireEvent.click(retryButton);

    // After first retry, should show 2 attempts left
    expect(screen.getByText(/2 attempts left/)).toBeInTheDocument();
  });

  it("shows max retry message when retries exhausted", () => {
    const { rerender } = render(
      <LazyComponentErrorBoundary>
        <ThrowingComponent />
      </LazyComponentErrorBoundary>
    );

    const retryButton = screen.getByRole("button", { name: /retry/i });

    // Click retry 3 times to exhaust attempts
    fireEvent.click(retryButton);
    fireEvent.click(retryButton);
    fireEvent.click(retryButton);

    expect(
      screen.getByText(/Maximum retry attempts reached/)
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /retry/i })
    ).not.toBeInTheDocument();
  });

  it("calls onError callback when error occurs", () => {
    const onError = jest.fn();

    render(
      <LazyComponentErrorBoundary onError={onError}>
        <ThrowingComponent />
      </LazyComponentErrorBoundary>
    );

    expect(onError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String),
      })
    );
  });

  it("renders custom fallback when provided", () => {
    const customFallback = <div>Custom error message</div>;

    render(
      <LazyComponentErrorBoundary fallback={customFallback}>
        <ThrowingComponent />
      </LazyComponentErrorBoundary>
    );

    expect(screen.getByText("Custom error message")).toBeInTheDocument();
    expect(
      screen.queryByText("Component Failed to Load")
    ).not.toBeInTheDocument();
  });

  it("resets error state on successful retry", () => {
    let shouldThrow = true;

    const ConditionalThrowingComponent = () => {
      if (shouldThrow) {
        throw new Error("Test error");
      }
      return <div>Component recovered</div>;
    };

    const { rerender } = render(
      <LazyComponentErrorBoundary>
        <ConditionalThrowingComponent />
      </LazyComponentErrorBoundary>
    );

    // Should show error initially
    expect(screen.getByText("Component Failed to Load")).toBeInTheDocument();

    // Change component to not throw
    shouldThrow = false;

    const retryButton = screen.getByRole("button", { name: /retry/i });
    fireEvent.click(retryButton);

    // Re-render with non-throwing component
    rerender(
      <LazyComponentErrorBoundary>
        <ConditionalThrowingComponent />
      </LazyComponentErrorBoundary>
    );

    expect(screen.getByText("Component recovered")).toBeInTheDocument();
  });

  it("has proper accessibility attributes", () => {
    render(
      <LazyComponentErrorBoundary>
        <ThrowingComponent />
      </LazyComponentErrorBoundary>
    );

    const retryButton = screen.getByRole("button", { name: /retry/i });
    expect(retryButton).toBeInTheDocument();

    // Should have proper button role and be focusable
    expect(retryButton.tagName).toBe("BUTTON");
  });
});

describe("withLazyErrorBoundary HOC", () => {
  it("wraps component with error boundary", () => {
    const WrappedComponent = withLazyErrorBoundary(WorkingComponent);

    render(<WrappedComponent />);

    expect(screen.getByText("Working component")).toBeInTheDocument();
  });

  it("handles errors in wrapped component", () => {
    const WrappedComponent = withLazyErrorBoundary(ThrowingComponent);

    render(<WrappedComponent />);

    expect(screen.getByText("Component Failed to Load")).toBeInTheDocument();
  });

  it("uses custom fallback when provided", () => {
    const customFallback = <div>HOC custom fallback</div>;
    const WrappedComponent = withLazyErrorBoundary(
      ThrowingComponent,
      customFallback
    );

    render(<WrappedComponent />);

    expect(screen.getByText("HOC custom fallback")).toBeInTheDocument();
  });

  it("sets correct display name", () => {
    const TestComponent = () => <div>Test</div>;
    TestComponent.displayName = "TestComponent";

    const WrappedComponent = withLazyErrorBoundary(TestComponent);

    expect(WrappedComponent.displayName).toBe(
      "withLazyErrorBoundary(TestComponent)"
    );
  });

  it("handles component without display name", () => {
    const WrappedComponent = withLazyErrorBoundary(WorkingComponent);

    expect(WrappedComponent.displayName).toBe(
      "withLazyErrorBoundary(WorkingComponent)"
    );
  });

  it("passes props to wrapped component", () => {
    const PropsComponent = ({ message }: { message: string }) => (
      <div>{message}</div>
    );
    const WrappedComponent = withLazyErrorBoundary(PropsComponent);

    render(<WrappedComponent message="Test message" />);

    expect(screen.getByText("Test message")).toBeInTheDocument();
  });
});
