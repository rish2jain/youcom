/**
 * Tests for preloading strategies
 */

import {
  preloadingManager,
  userBehaviorTracker,
  usePreloading,
} from "../preloading-strategies";
import { renderHook } from "@testing-library/react";

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

// Mock requestIdleCallback
Object.defineProperty(window, "requestIdleCallback", {
  value: jest.fn((callback) => setTimeout(callback, 0)),
});

// Mock IntersectionObserver
const mockIntersectionObserver = jest.fn();
mockIntersectionObserver.mockReturnValue({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
});
Object.defineProperty(window, "IntersectionObserver", {
  value: mockIntersectionObserver,
});

// Mock performance
Object.defineProperty(window, "performance", {
  value: {
    now: jest.fn(() => Date.now()),
    mark: jest.fn(),
  },
});

describe("PreloadingManager", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    preloadingManager.clearCache();
  });

  it("preloads component immediately", async () => {
    const mockComponent = () => null;
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: mockComponent })
    );

    await preloadingManager.preloadImmediate("TestComponent", mockImportFn);

    expect(mockImportFn).toHaveBeenCalledTimes(1);
    expect(preloadingManager.isPreloaded("TestComponent")).toBe(true);
  });

  it("does not preload same component twice", async () => {
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    await preloadingManager.preloadImmediate("TestComponent", mockImportFn);
    await preloadingManager.preloadImmediate("TestComponent", mockImportFn);

    expect(mockImportFn).toHaveBeenCalledTimes(1);
  });

  it("handles preload failures gracefully", async () => {
    const mockImportFn = jest.fn(() =>
      Promise.reject(new Error("Load failed"))
    );

    // Should not throw
    await expect(
      preloadingManager.preloadImmediate("FailingComponent", mockImportFn)
    ).resolves.toBeUndefined();

    expect(preloadingManager.isPreloaded("FailingComponent")).toBe(false);
  });

  it("sets up hover preloading", () => {
    const element = document.createElement("div");
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    const cleanup = preloadingManager.preloadOnHover(
      element,
      "HoverComponent",
      mockImportFn
    );

    // Simulate mouseenter
    element.dispatchEvent(new Event("mouseenter"));

    expect(mockImportFn).toHaveBeenCalledTimes(1);
    expect(typeof cleanup).toBe("function");

    // Cleanup should remove event listener
    cleanup();
  });

  it("sets up viewport preloading with IntersectionObserver", () => {
    const element = document.createElement("div");
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    const cleanup = preloadingManager.preloadOnViewport(
      element,
      "ViewportComponent",
      mockImportFn
    );

    expect(mockIntersectionObserver).toHaveBeenCalledWith(
      expect.any(Function),
      { threshold: 0.1 }
    );

    expect(typeof cleanup).toBe("function");
  });

  it("falls back to immediate preload when IntersectionObserver not supported", () => {
    // Temporarily remove IntersectionObserver
    const originalIO = window.IntersectionObserver;
    delete (window as any).IntersectionObserver;

    const element = document.createElement("div");
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    preloadingManager.preloadOnViewport(
      element,
      "FallbackComponent",
      mockImportFn
    );

    expect(mockImportFn).toHaveBeenCalledTimes(1);

    // Restore IntersectionObserver
    (window as any).IntersectionObserver = originalIO;
  });

  it("preloads on idle using requestIdleCallback", () => {
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    preloadingManager.preloadOnIdle("IdleComponent", mockImportFn);

    expect(window.requestIdleCallback).toHaveBeenCalledWith(
      expect.any(Function),
      { timeout: 5000 }
    );
  });

  it("falls back to setTimeout when requestIdleCallback not available", () => {
    // Temporarily remove requestIdleCallback
    const originalRIC = window.requestIdleCallback;
    delete (window as any).requestIdleCallback;

    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    jest.spyOn(window, "setTimeout");

    preloadingManager.preloadOnIdle("FallbackIdleComponent", mockImportFn);

    expect(setTimeout).toHaveBeenCalledWith(expect.any(Function), 100);

    // Restore requestIdleCallback
    (window as any).requestIdleCallback = originalRIC;
  });

  it("preloads with priority management", async () => {
    const highPriorityImport = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );
    const mediumPriorityImport = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );
    const lowPriorityImport = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    const components = [
      {
        name: "LowPriority",
        importFn: lowPriorityImport,
        config: { priority: "low" as const },
      },
      {
        name: "HighPriority",
        importFn: highPriorityImport,
        config: { priority: "high" as const },
      },
      {
        name: "MediumPriority",
        importFn: mediumPriorityImport,
        config: { priority: "medium" as const },
      },
    ];

    await preloadingManager.preloadWithPriority(components);

    // High priority should be called immediately
    expect(highPriorityImport).toHaveBeenCalledTimes(1);

    // Medium and low priority are called with delays, so they might not be called yet
    // in this synchronous test
  });

  it("respects conditions in priority preloading", async () => {
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    const components = [
      {
        name: "ConditionalComponent",
        importFn: mockImportFn,
        config: {
          priority: "high" as const,
          condition: () => false, // Should not preload
        },
      },
    ];

    await preloadingManager.preloadWithPriority(components);

    expect(mockImportFn).not.toHaveBeenCalled();
  });

  it("returns preload promise when available", () => {
    const mockPromise = Promise.resolve({ default: () => null });
    const mockImportFn = jest.fn(() => mockPromise);

    preloadingManager.preloadImmediate("PromiseComponent", mockImportFn);

    const promise = preloadingManager.getPreloadPromise("PromiseComponent");
    expect(promise).toBe(mockPromise);
  });

  it("returns undefined for non-existent preload promise", () => {
    const promise = preloadingManager.getPreloadPromise("NonExistent");
    expect(promise).toBeUndefined();
  });

  it("records and retrieves metrics", async () => {
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    await preloadingManager.preloadImmediate("MetricsComponent", mockImportFn);

    const metrics = preloadingManager.getMetrics();
    expect(metrics).toHaveLength(1);
    expect(metrics[0].componentName).toBe("MetricsComponent");
  });

  it("clears cache correctly", async () => {
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    await preloadingManager.preloadImmediate("CacheComponent", mockImportFn);
    expect(preloadingManager.isPreloaded("CacheComponent")).toBe(true);

    preloadingManager.clearCache();
    expect(preloadingManager.isPreloaded("CacheComponent")).toBe(false);
  });
});

describe("UserBehaviorTracker", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  it("tracks route access", () => {
    userBehaviorTracker.trackRouteAccess("/dashboard", "ImpactCard");

    // Should save patterns to localStorage
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "userBehaviorPatterns",
      expect.any(String)
    );
  });

  it("predicts components based on behavior", () => {
    // Mock stored patterns
    const mockPatterns = [
      [
        "/dashboard:ImpactCard",
        {
          route: "/dashboard",
          component: "ImpactCard",
          frequency: 5,
          lastAccessed: Date.now() - 1000,
          averageTimeSpent: 5000,
        },
      ],
      [
        "/research:CompanyResearch",
        {
          route: "/research",
          component: "CompanyResearch",
          frequency: 3,
          lastAccessed: Date.now() - 2000,
          averageTimeSpent: 3000,
        },
      ],
    ];

    localStorageMock.getItem.mockReturnValue(JSON.stringify(mockPatterns));

    const predicted = userBehaviorTracker.getPredictedComponents("/current", 2);

    expect(predicted).toContain("ImpactCard");
    expect(predicted).toContain("CompanyResearch");
  });

  it("filters out old patterns", () => {
    const oldTime = Date.now() - 8 * 24 * 60 * 60 * 1000; // 8 days ago

    const mockPatterns = [
      [
        "/old:OldComponent",
        {
          route: "/old",
          component: "OldComponent",
          frequency: 5,
          lastAccessed: oldTime,
          averageTimeSpent: 5000,
        },
      ],
    ];

    localStorageMock.getItem.mockReturnValue(JSON.stringify(mockPatterns));

    const predicted = userBehaviorTracker.getPredictedComponents("/current");

    expect(predicted).not.toContain("OldComponent");
  });

  it("handles localStorage errors gracefully", () => {
    localStorageMock.getItem.mockImplementation(() => {
      throw new Error("localStorage error");
    });

    // Should not throw
    expect(() => {
      userBehaviorTracker.getPredictedComponents("/test");
    }).not.toThrow();
  });
});

describe("usePreloading hook", () => {
  it("returns preloading functions", () => {
    const { result } = renderHook(() => usePreloading());

    expect(typeof result.current.preloadImmediate).toBe("function");
    expect(typeof result.current.preloadOnHover).toBe("function");
    expect(typeof result.current.preloadOnViewport).toBe("function");
    expect(typeof result.current.preloadOnIdle).toBe("function");
    expect(typeof result.current.isPreloaded).toBe("function");
    expect(typeof result.current.getMetrics).toBe("function");
    expect(typeof result.current.clearCache).toBe("function");
  });

  it("preloading functions work correctly", async () => {
    const { result } = renderHook(() => usePreloading());
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    await result.current.preloadImmediate("HookComponent", mockImportFn);

    expect(mockImportFn).toHaveBeenCalledTimes(1);
    expect(result.current.isPreloaded("HookComponent")).toBe(true);
  });
});
