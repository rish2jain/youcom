import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorBoundary, ComponentErrorBoundary } from "../ErrorBoundary";

// Component that throws an error for testing
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error("Test error");
  }
  return <div>Working Component</div>;
};

// Suppress console.error for cleaner test output
const originalError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalError;
});

describe("ErrorBoundary Component", () => {
  it("renders children when there is no error", () => {
    render(
      <ErrorBoundary>
        <div>Test Child Component</div>
      </ErrorBoundary>
    );

    expect(screen.getByText("Test Child Component")).toBeInTheDocument();
  });

  it("renders error UI when child component throws", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("An unexpected error occurred in the application")).toBeInTheDocument();
  });

  it("displays Try Again and Reload Page buttons in error state", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText("Try Again")).toBeInTheDocument();
    expect(screen.getByText("Reload Page")).toBeInTheDocument();
  });

  it("displays Go to Home link in error state", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const homeLink = screen.getByText("Go to Home");
    expect(homeLink).toBeInTheDocument();
    expect(homeLink.closest("a")).toHaveAttribute("href", "/");
  });

  it("resets error state when Try Again is clicked", () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const tryAgainButton = screen.getByText("Try Again");
    fireEvent.click(tryAgainButton);

    // After reset, re-render with non-throwing component
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByText("Working Component")).toBeInTheDocument();
  });

  it("calls onError callback when error is caught", () => {
    const onErrorMock = jest.fn();

    render(
      <ErrorBoundary onError={onErrorMock}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(onErrorMock).toHaveBeenCalled();
    expect(onErrorMock).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String),
      })
    );
  });

  it("renders custom fallback when provided", () => {
    const customFallback = <div>Custom Error Message</div>;

    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText("Custom Error Message")).toBeInTheDocument();
    expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
  });

  it("displays error details in development mode", () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = "development";

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText("Error Details (Development Only)")).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  it("renders AlertTriangle icon", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Check for SVG icon
    const icons = document.querySelectorAll("svg");
    expect(icons.length).toBeGreaterThan(0);
  });
});

describe("ComponentErrorBoundary", () => {
  it("renders children when there is no error", () => {
    render(
      <ComponentErrorBoundary componentName="TestComponent">
        <div>Working Component</div>
      </ComponentErrorBoundary>
    );

    expect(screen.getByText("Working Component")).toBeInTheDocument();
  });

  it("renders component-specific error UI when error occurs", () => {
    render(
      <ComponentErrorBoundary componentName="TestComponent">
        <ThrowError shouldThrow={true} />
      </ComponentErrorBoundary>
    );

    expect(screen.getByText("Component Error")).toBeInTheDocument();
    expect(screen.getByText(/The TestComponent component encountered an error/)).toBeInTheDocument();
  });

  it("displays reload button in component error state", () => {
    render(
      <ComponentErrorBoundary componentName="TestComponent">
        <ThrowError shouldThrow={true} />
      </ComponentErrorBoundary>
    );

    expect(screen.getByText("Reload Page")).toBeInTheDocument();
  });

  it("renders with correct styling for component error", () => {
    render(
      <ComponentErrorBoundary componentName="TestComponent">
        <ThrowError shouldThrow={true} />
      </ComponentErrorBoundary>
    );

    const errorContainer = document.querySelector(".bg-red-50");
    expect(errorContainer).toBeInTheDocument();
    expect(errorContainer?.classList.contains("border-red-200")).toBeTruthy();
  });

  it("logs error with component name", () => {
    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    render(
      <ComponentErrorBoundary componentName="TestComponent">
        <ThrowError shouldThrow={true} />
      </ComponentErrorBoundary>
    );

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      "Error in TestComponent:",
      expect.any(Error),
      expect.any(Object)
    );

    consoleErrorSpy.mockRestore();
  });

  it("renders AlertTriangle icon in component error", () => {
    render(
      <ComponentErrorBoundary componentName="TestComponent">
        <ThrowError shouldThrow={true} />
      </ComponentErrorBoundary>
    );

    const redIcons = document.querySelectorAll(".text-red-500");
    expect(redIcons.length).toBeGreaterThan(0);
  });
});
