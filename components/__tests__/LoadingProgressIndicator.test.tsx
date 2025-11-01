/**
 * Tests for LoadingProgressIndicator and useComponentLoadingState
 */

import React from "react";
import { render, screen, act } from "@testing-library/react";
import { renderHook } from "@testing-library/react";
import {
  LoadingProgressIndicator,
  useComponentLoadingState,
} from "../LoadingProgressIndicator";
import { useLoadingStateStore } from "@/lib/loading-state-manager";

// Mock the Progress component
jest.mock("@/components/ui/progress", () => ({
  Progress: ({ value, className }: { value: number; className?: string }) => (
    <div className={className} data-testid="progress-bar" data-value={value}>
      Progress: {value}%
    </div>
  ),
}));

describe("LoadingProgressIndicator", () => {
  beforeEach(() => {
    // Reset store state
    useLoadingStateStore.getState().reset();
  });

  it("renders nothing when no components are loading", () => {
    const { container } = render(<LoadingProgressIndicator />);
    expect(container.firstChild).toBeNull();
  });

  it("renders compact indicator when components are loading", () => {
    // Set up loading state
    act(() => {
      useLoadingStateStore.getState().setLoading("TestComponent", 50);
    });

    render(<LoadingProgressIndicator compact />);

    expect(screen.getByText("1/1 loaded")).toBeInTheDocument();
  });

  it("renders full progress indicator", () => {
    act(() => {
      useLoadingStateStore.getState().setLoading("Component1", 30);
      useLoadingStateStore.getState().setLoaded("Component2");
    });

    render(<LoadingProgressIndicator />);

    expect(screen.getByText("Loading Progress")).toBeInTheDocument();
    expect(screen.getByText("1/2 components loaded")).toBeInTheDocument();
    expect(screen.getByTestId("progress-bar")).toBeInTheDocument();
  });

  it("shows correct progress percentage", () => {
    act(() => {
      useLoadingStateStore.getState().setLoading("Component1", 60);
      useLoadingStateStore.getState().setLoaded("Component2");
    });

    render(<LoadingProgressIndicator />);

    const progressBar = screen.getByTestId("progress-bar");
    expect(progressBar).toHaveAttribute("data-value", "80"); // (60 + 100) / 2
    expect(screen.getByText("80%")).toBeInTheDocument();
  });

  it("displays failed components count", () => {
    act(() => {
      useLoadingStateStore.getState().setLoading("Component1");
      useLoadingStateStore.getState().setError("Component2", "Failed to load");
    });

    render(<LoadingProgressIndicator />);

    expect(
      screen.getByText("1 component(s) failed to load")
    ).toBeInTheDocument();
  });

  it("shows loading spinner when components are loading", () => {
    act(() => {
      useLoadingStateStore.getState().setLoading("TestComponent");
    });

    render(<LoadingProgressIndicator />);

    // Should show loading spinner (Loader2 icon)
    const spinner = document.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("shows success icon when all components loaded", () => {
    act(() => {
      useLoadingStateStore.getState().setLoaded("Component1");
      useLoadingStateStore.getState().setLoaded("Component2");
    });

    render(<LoadingProgressIndicator />);

    // Should show CheckCircle icon (not loading)
    const spinner = document.querySelector(".animate-spin");
    expect(spinner).not.toBeInTheDocument();
  });

  it("shows error icon when components failed", () => {
    act(() => {
      useLoadingStateStore.getState().setError("Component1", "Error");
    });

    render(<LoadingProgressIndicator />);

    // Should show error state
    expect(
      screen.getByText("1 component(s) failed to load")
    ).toBeInTheDocument();
  });

  it("displays average load time when available", () => {
    act(() => {
      // Simulate components with load times
      const store = useLoadingStateStore.getState();
      store.setLoading("Component1");
      store.setLoaded("Component1");
    });

    render(<LoadingProgressIndicator />);

    // Should show average load time
    expect(screen.getByText(/Avg:/)).toBeInTheDocument();
  });

  it("shows detailed component states when showDetails is true", () => {
    act(() => {
      useLoadingStateStore.getState().setLoading("Component1", 75);
      useLoadingStateStore.getState().setLoaded("Component2");
      useLoadingStateStore.getState().setError("Component3", "Failed");
    });

    render(<LoadingProgressIndicator showDetails />);

    expect(screen.getByText("Component1")).toBeInTheDocument();
    expect(screen.getByText("Component2")).toBeInTheDocument();
    expect(screen.getByText("Component3")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    act(() => {
      useLoadingStateStore.getState().setLoading("TestComponent");
    });

    render(<LoadingProgressIndicator className="custom-class" />);

    const container = screen.getByText("Loading Progress").closest("div");
    expect(container).toHaveClass("custom-class");
  });
});

describe("useComponentLoadingState", () => {
  beforeEach(() => {
    useLoadingStateStore.getState().reset();
  });

  it("returns initial state for new component", () => {
    const { result } = renderHook(() =>
      useComponentLoadingState("NewComponent")
    );

    expect(result.current.state).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isLoaded).toBe(false);
    expect(result.current.hasError).toBe(false);
    expect(result.current.progress).toBe(0);
  });

  it("sets component to loading state", () => {
    const { result } = renderHook(() =>
      useComponentLoadingState("TestComponent")
    );

    act(() => {
      result.current.setLoading(50);
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.progress).toBe(50);
    expect(result.current.state?.status).toBe("loading");
  });

  it("sets component to loaded state", () => {
    const { result } = renderHook(() =>
      useComponentLoadingState("TestComponent")
    );

    act(() => {
      result.current.setLoading();
      result.current.setLoaded();
    });

    expect(result.current.isLoaded).toBe(true);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.progress).toBe(100);
    expect(result.current.state?.status).toBe("loaded");
  });

  it("sets component to error state", () => {
    const { result } = renderHook(() =>
      useComponentLoadingState("TestComponent")
    );

    act(() => {
      result.current.setLoading();
      result.current.setError("Load failed");
    });

    expect(result.current.hasError).toBe(true);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.state?.error).toBe("Load failed");
    expect(result.current.state?.status).toBe("error");
  });

  it("updates progress", () => {
    const { result } = renderHook(() =>
      useComponentLoadingState("TestComponent")
    );

    act(() => {
      result.current.setLoading(25);
      result.current.setProgress(75);
    });

    expect(result.current.progress).toBe(75);
  });

  it("resets component state", () => {
    const { result } = renderHook(() =>
      useComponentLoadingState("TestComponent")
    );

    act(() => {
      result.current.setLoading(50);
      result.current.reset();
    });

    expect(result.current.state).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.progress).toBe(0);
  });

  it("tracks multiple components independently", () => {
    const { result: result1 } = renderHook(() =>
      useComponentLoadingState("Component1")
    );
    const { result: result2 } = renderHook(() =>
      useComponentLoadingState("Component2")
    );

    act(() => {
      result1.current.setLoading(30);
      result2.current.setLoaded();
    });

    expect(result1.current.isLoading).toBe(true);
    expect(result1.current.progress).toBe(30);
    expect(result2.current.isLoaded).toBe(true);
    expect(result2.current.progress).toBe(100);
  });

  it("provides all necessary state management functions", () => {
    const { result } = renderHook(() =>
      useComponentLoadingState("TestComponent")
    );

    expect(typeof result.current.setLoading).toBe("function");
    expect(typeof result.current.setLoaded).toBe("function");
    expect(typeof result.current.setError).toBe("function");
    expect(typeof result.current.setProgress).toBe("function");
    expect(typeof result.current.reset).toBe("function");
  });
});
