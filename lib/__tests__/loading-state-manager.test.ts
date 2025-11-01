/**
 * Tests for loading state management system
 */

import { renderHook, act } from "@testing-library/react";
import {
  useLoadingStateStore,
  LoadingStateManager,
  loadingStateManager,
} from "../loading-state-manager";

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
});

describe("useLoadingStateStore", () => {
  beforeEach(() => {
    // Reset store state
    useLoadingStateStore.getState().reset();
    jest.clearAllMocks();
  });

  it("initializes with empty state", () => {
    const { result } = renderHook(() => useLoadingStateStore());

    expect(result.current.states.size).toBe(0);
    expect(result.current.metrics.totalComponents).toBe(0);
    expect(result.current.metrics.isLoading).toBe(false);
  });

  it("sets component to loading state", () => {
    const { result } = renderHook(() => useLoadingStateStore());

    act(() => {
      result.current.setLoading("TestComponent", 50);
    });

    const state = result.current.getState("TestComponent");
    expect(state?.status).toBe("loading");
    expect(state?.progress).toBe(50);
    expect(result.current.metrics.isLoading).toBe(true);
  });

  it("sets component to loaded state", () => {
    const { result } = renderHook(() => useLoadingStateStore());

    act(() => {
      result.current.setLoading("TestComponent");
      result.current.setLoaded("TestComponent");
    });

    const state = result.current.getState("TestComponent");
    expect(state?.status).toBe("loaded");
    expect(state?.progress).toBe(100);
    expect(result.current.metrics.isLoading).toBe(false);
  });

  it("sets component to error state", () => {
    const { result } = renderHook(() => useLoadingStateStore());

    act(() => {
      result.current.setLoading("TestComponent");
      result.current.setError("TestComponent", "Failed to load");
    });

    const state = result.current.getState("TestComponent");
    expect(state?.status).toBe("error");
    expect(state?.error).toBe("Failed to load");
    expect(result.current.metrics.isLoading).toBe(false);
  });

  it("updates progress for loading component", () => {
    const { result } = renderHook(() => useLoadingStateStore());

    act(() => {
      result.current.setLoading("TestComponent", 25);
      result.current.setProgress("TestComponent", 75);
    });

    const state = result.current.getState("TestComponent");
    expect(state?.progress).toBe(75);
  });

  it("does not update progress for non-loading component", () => {
    const { result } = renderHook(() => useLoadingStateStore());

    act(() => {
      result.current.setLoaded("TestComponent");
      result.current.setProgress("TestComponent", 50);
    });

    const state = result.current.getState("TestComponent");
    expect(state?.progress).toBe(100); // Should remain at loaded state
  });

  it("calculates metrics correctly", () => {
    const { result } = renderHook(() => useLoadingStateStore());

    act(() => {
      result.current.setLoading("Component1", 50);
      result.current.setLoaded("Component2");
      result.current.setError("Component3", "Error");
    });

    const metrics = result.current.metrics;
    expect(metrics.totalComponents).toBe(3);
    expect(metrics.loadedComponents).toBe(1);
    expect(metrics.failedComponents).toBe(1);
    expect(metrics.isLoading).toBe(true);
    expect(metrics.overallProgress).toBeCloseTo(50); // (50 + 100 + 0) / 3
  });

  it("resets specific component state", () => {
    const { result } = renderHook(() => useLoadingStateStore());

    act(() => {
      result.current.setLoading("Component1");
      result.current.setLoading("Component2");
      result.current.reset("Component1");
    });

    expect(result.current.getState("Component1")).toBeUndefined();
    expect(result.current.getState("Component2")).toBeDefined();
    expect(result.current.metrics.totalComponents).toBe(1);
  });

  it("resets all component states", () => {
    const { result } = renderHook(() => useLoadingStateStore());

    act(() => {
      result.current.setLoading("Component1");
      result.current.setLoading("Component2");
      result.current.reset();
    });

    expect(result.current.states.size).toBe(0);
    expect(result.current.metrics.totalComponents).toBe(0);
  });

  it("checks if component is loading", () => {
    const { result } = renderHook(() => useLoadingStateStore());

    act(() => {
      result.current.setLoading("TestComponent");
    });

    expect(result.current.isComponentLoading("TestComponent")).toBe(true);
    expect(result.current.isComponentLoading("NonExistent")).toBe(false);
  });

  it("checks if any component is loading", () => {
    const { result } = renderHook(() => useLoadingStateStore());

    expect(result.current.isAnyLoading()).toBe(false);

    act(() => {
      result.current.setLoading("TestComponent");
    });

    expect(result.current.isAnyLoading()).toBe(true);

    act(() => {
      result.current.setLoaded("TestComponent");
    });

    expect(result.current.isAnyLoading()).toBe(false);
  });
});

describe("LoadingStateManager", () => {
  let manager: LoadingStateManager;

  beforeEach(() => {
    manager = new LoadingStateManager();
    useLoadingStateStore.getState().reset();
    jest.clearAllMocks();
  });

  it("creates manager instance", () => {
    expect(manager).toBeInstanceOf(LoadingStateManager);
  });

  it("sets loading state through manager", () => {
    manager.setLoading("TestComponent", 30);

    const state = manager.getState("TestComponent");
    expect(state?.status).toBe("loading");
    expect(state?.progress).toBe(30);
  });

  it("sets loaded state through manager", () => {
    manager.setLoading("TestComponent");
    manager.setLoaded("TestComponent");

    const state = manager.getState("TestComponent");
    expect(state?.status).toBe("loaded");
  });

  it("sets error state through manager", () => {
    manager.setLoading("TestComponent");
    manager.setError("TestComponent", "Load failed");

    const state = manager.getState("TestComponent");
    expect(state?.status).toBe("error");
    expect(state?.error).toBe("Load failed");
  });

  it("subscribes to metrics changes", () => {
    const callback = jest.fn();
    const unsubscribe = manager.subscribe(callback);

    manager.setLoading("TestComponent");

    expect(callback).toHaveBeenCalled();

    unsubscribe();
    manager.setLoaded("TestComponent");

    // Should not be called after unsubscribe
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it("persists state to localStorage", () => {
    manager.setLoading("TestComponent");
    manager.persistState();

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "loadingStates",
      expect.any(String)
    );
  });

  it("recovers state from localStorage", () => {
    const mockStates = [
      [
        "TestComponent",
        { component: "TestComponent", status: "loaded", progress: 100 },
      ],
    ];

    localStorageMock.getItem.mockReturnValue(JSON.stringify(mockStates));

    manager.recoverState();

    const state = manager.getState("TestComponent");
    expect(state?.status).toBe("loaded");
  });

  it("filters out loading states during recovery", () => {
    const mockStates = [
      [
        "LoadingComponent",
        { component: "LoadingComponent", status: "loading", progress: 50 },
      ],
      [
        "LoadedComponent",
        { component: "LoadedComponent", status: "loaded", progress: 100 },
      ],
    ];

    localStorageMock.getItem.mockReturnValue(JSON.stringify(mockStates));

    manager.recoverState();

    expect(manager.getState("LoadingComponent")).toBeUndefined();
    expect(manager.getState("LoadedComponent")).toBeDefined();
  });

  it("handles localStorage errors gracefully", () => {
    localStorageMock.getItem.mockImplementation(() => {
      throw new Error("localStorage error");
    });

    // Should not throw
    expect(() => manager.recoverState()).not.toThrow();

    localStorageMock.setItem.mockImplementation(() => {
      throw new Error("localStorage error");
    });

    // Should not throw
    expect(() => manager.persistState()).not.toThrow();
  });
});

describe("Global loadingStateManager", () => {
  it("exports global instance", () => {
    expect(loadingStateManager).toBeInstanceOf(LoadingStateManager);
  });

  it("global instance works correctly", () => {
    loadingStateManager.setLoading("GlobalTest");

    const state = loadingStateManager.getState("GlobalTest");
    expect(state?.status).toBe("loading");

    // Cleanup
    loadingStateManager.reset("GlobalTest");
  });
});
