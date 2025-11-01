/**
 * Tests for Cache Warming React hooks
 */

import { renderHook, act } from "@testing-library/react";
import { usePathname } from "next/navigation";
import {
  useCacheWarming,
  useIntelligentPreloading,
  useUserBehaviorTracking,
  useCachePerformanceMonitoring,
} from "../useCacheWarming";

// Mock Next.js navigation
jest.mock("next/navigation", () => ({
  usePathname: jest.fn(),
}));

// Mock cache warming utilities
const mockWarmCache = jest.fn();
const mockPreloadRoute = jest.fn();
const mockUpdateUserBehavior = jest.fn();
const mockGetWarmingStatus = jest.fn();

jest.mock("../cache-warming", () => ({
  warmCache: mockWarmCache,
  preloadRoute: mockPreloadRoute,
  updateUserBehavior: mockUpdateUserBehavior,
  getWarmingStatus: mockGetWarmingStatus,
}));

// Mock window events
const mockAddEventListener = jest.fn();
const mockRemoveEventListener = jest.fn();
Object.defineProperty(global, "window", {
  value: {
    addEventListener: mockAddEventListener,
    removeEventListener: mockRemoveEventListener,
  },
  writable: true,
});

describe("useCacheWarming", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (usePathname as jest.Mock).mockReturnValue("/dashboard");
    mockGetWarmingStatus.mockReturnValue({
      isWarming: false,
      queueLength: 0,
      strategiesCount: 5,
      userBehavior: null,
    });
  });

  it("should initialize with warming status", () => {
    const { result } = renderHook(() => useCacheWarming());

    expect(result.current.state.isWarming).toBe(false);
    expect(result.current.state.queueLength).toBe(0);
    expect(result.current.state.strategiesCount).toBe(5);
    expect(result.current.state.userBehavior).toBeNull();
  });

  it("should update user behavior on pathname change", () => {
    renderHook(() => useCacheWarming());

    expect(mockUpdateUserBehavior).toHaveBeenCalledWith(
      expect.objectContaining({
        frequentRoutes: ["/dashboard"],
        timeOfDay: expect.any(String),
        dayOfWeek: expect.any(String),
        lastVisit: expect.any(Date),
      })
    );
  });

  it("should provide warmCache function", async () => {
    mockWarmCache.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useCacheWarming());

    await act(async () => {
      await result.current.warmCache("critical-resources");
    });

    expect(mockWarmCache).toHaveBeenCalledWith("critical-resources");
  });

  it("should provide preloadRoute function", async () => {
    mockPreloadRoute.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useCacheWarming());

    await act(async () => {
      await result.current.preloadRoute("/research");
    });

    expect(mockPreloadRoute).toHaveBeenCalledWith("/research");
  });

  it("should handle warming errors gracefully", async () => {
    mockWarmCache.mockRejectedValueOnce(new Error("Warming failed"));
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    const { result } = renderHook(() => useCacheWarming());

    await act(async () => {
      await result.current.warmCache();
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      "Manual cache warming failed:",
      expect.any(Error)
    );
    consoleSpy.mockRestore();
  });

  it("should update state periodically", () => {
    jest.useFakeTimers();

    renderHook(() => useCacheWarming());

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(5000);
    });

    expect(mockGetWarmingStatus).toHaveBeenCalledTimes(2); // Initial + interval

    jest.useRealTimers();
  });
});

describe("useIntelligentPreloading", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPreloadRoute.mockResolvedValue(undefined);
  });

  it("should initialize with empty preloaded routes", () => {
    const { result } = renderHook(() => useIntelligentPreloading());

    expect(result.current.preloadedRoutes).toEqual([]);
    expect(result.current.isPreloading).toBe(false);
  });

  it("should preload route on hover", async () => {
    const { result } = renderHook(() => useIntelligentPreloading());

    await act(async () => {
      await result.current.preloadOnHover("/research");
    });

    expect(mockPreloadRoute).toHaveBeenCalledWith("/research");
    expect(result.current.preloadedRoutes).toContain("/research");
  });

  it("should not preload same route twice", async () => {
    const { result } = renderHook(() => useIntelligentPreloading());

    await act(async () => {
      await result.current.preloadOnHover("/research");
      await result.current.preloadOnHover("/research"); // Second call
    });

    expect(mockPreloadRoute).toHaveBeenCalledTimes(1);
  });

  it("should not preload while already preloading", async () => {
    mockPreloadRoute.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    const { result } = renderHook(() => useIntelligentPreloading());

    // Start first preload
    const preload1 = act(async () => {
      await result.current.preloadOnHover("/research");
    });

    // Try second preload while first is in progress
    await act(async () => {
      await result.current.preloadOnHover("/analytics");
    });

    await preload1;

    expect(mockPreloadRoute).toHaveBeenCalledTimes(1); // Only first call
  });

  it("should handle preload errors gracefully", async () => {
    mockPreloadRoute.mockRejectedValueOnce(new Error("Preload failed"));
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    const { result } = renderHook(() => useIntelligentPreloading());

    await act(async () => {
      await result.current.preloadOnHover("/research");
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      "Hover preloading failed:",
      expect.any(Error)
    );
    expect(result.current.preloadedRoutes).not.toContain("/research");
    consoleSpy.mockRestore();
  });

  it("should preload on intersection", async () => {
    const { result } = renderHook(() => useIntelligentPreloading());

    await act(async () => {
      await result.current.preloadOnIntersection("/analytics");
    });

    expect(mockPreloadRoute).toHaveBeenCalledWith("/analytics");
    expect(result.current.preloadedRoutes).toContain("/analytics");
  });
});

describe("useUserBehaviorTracking", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (usePathname as jest.Mock).mockReturnValue("/dashboard");
  });

  it("should initialize with session start time", () => {
    const { result } = renderHook(() => useUserBehaviorTracking());

    expect(result.current.actions).toEqual([]);
    expect(result.current.sessionDuration).toBe(0);
  });

  it("should track page view on pathname change", () => {
    renderHook(() => useUserBehaviorTracking());

    expect(mockUpdateUserBehavior).toHaveBeenCalledWith(
      expect.objectContaining({
        recentActions: ["view:/dashboard"],
        sessionDuration: expect.any(Number),
      })
    );
  });

  it("should track custom actions", () => {
    const { result } = renderHook(() => useUserBehaviorTracking());

    act(() => {
      result.current.trackAction("export");
    });

    expect(mockUpdateUserBehavior).toHaveBeenCalledWith(
      expect.objectContaining({
        recentActions: expect.arrayContaining(["export"]),
        sessionDuration: expect.any(Number),
      })
    );
  });

  it("should limit recent actions to 10", () => {
    const { result } = renderHook(() => useUserBehaviorTracking());

    act(() => {
      // Track 15 actions
      for (let i = 0; i < 15; i++) {
        result.current.trackAction(`action-${i}`);
      }
    });

    expect(result.current.actions).toHaveLength(10);
    expect(result.current.actions[0]).toBe("action-5"); // Should keep last 10
  });

  it("should calculate session duration", () => {
    jest.useFakeTimers();
    const startTime = Date.now();
    jest.setSystemTime(startTime);

    const { result } = renderHook(() => useUserBehaviorTracking());

    // Advance time by 5 minutes
    jest.advanceTimersByTime(5 * 60 * 1000);

    expect(result.current.sessionDuration).toBe(5);

    jest.useRealTimers();
  });

  it("should track session duration on beforeunload", () => {
    const { unmount } = renderHook(() => useUserBehaviorTracking());

    expect(mockAddEventListener).toHaveBeenCalledWith(
      "beforeunload",
      expect.any(Function)
    );

    unmount();

    expect(mockRemoveEventListener).toHaveBeenCalledWith(
      "beforeunload",
      expect.any(Function)
    );
  });
});

describe("useCachePerformanceMonitoring", () => {
  beforeEach(() => {
    // Mock performance API
    Object.defineProperty(global, "performance", {
      value: {
        getEntriesByType: jest.fn(),
        memory: {
          usedJSHeapSize: 50 * 1024 * 1024, // 50MB
          jsHeapSizeLimit: 100 * 1024 * 1024, // 100MB
        },
      },
      writable: true,
    });
  });

  it("should initialize with default metrics", () => {
    const { result } = renderHook(() => useCachePerformanceMonitoring());

    expect(result.current.cacheHitRate).toBe(0);
    expect(result.current.averageLoadTime).toBe(0);
    expect(result.current.preloadSuccessRate).toBe(0.9);
    expect(result.current.memoryUsage).toBe(0);
  });

  it("should calculate cache hit rate from performance entries", () => {
    const mockResourceEntries = [
      { transferSize: 0, decodedBodySize: 1000 }, // Cached
      { transferSize: 500, decodedBodySize: 1000 }, // Not cached
      { transferSize: 0, decodedBodySize: 2000 }, // Cached
    ];

    global.performance.getEntriesByType = jest
      .fn()
      .mockReturnValueOnce([]) // navigation entries
      .mockReturnValueOnce(mockResourceEntries); // resource entries

    const { result } = renderHook(() => useCachePerformanceMonitoring());

    // Should calculate 2/3 = 0.67 cache hit rate
    expect(result.current.cacheHitRate).toBeCloseTo(0.67, 2);
  });

  it("should calculate average load time", () => {
    const mockNavigationEntries = [
      {
        fetchStart: 1000,
        loadEventEnd: 3000,
      },
    ];

    global.performance.getEntriesByType = jest
      .fn()
      .mockReturnValueOnce(mockNavigationEntries) // navigation entries
      .mockReturnValueOnce([]); // resource entries

    const { result } = renderHook(() => useCachePerformanceMonitoring());

    expect(result.current.averageLoadTime).toBe(2000);
  });

  it("should calculate memory usage when available", () => {
    const { result } = renderHook(() => useCachePerformanceMonitoring());

    expect(result.current.memoryUsage).toBe(50); // 50MB
  });

  it("should handle missing memory API gracefully", () => {
    const originalMemory = global.performance.memory;
    // @ts-ignore
    delete global.performance.memory;

    const { result } = renderHook(() => useCachePerformanceMonitoring());

    expect(result.current.memoryUsage).toBe(0);

    global.performance.memory = originalMemory;
  });

  it("should update metrics periodically", () => {
    jest.useFakeTimers();

    global.performance.getEntriesByType = jest.fn().mockReturnValue([]);

    renderHook(() => useCachePerformanceMonitoring());

    expect(global.performance.getEntriesByType).toHaveBeenCalledTimes(2); // Initial call

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(30000);
    });

    expect(global.performance.getEntriesByType).toHaveBeenCalledTimes(4); // Interval call

    jest.useRealTimers();
  });
});
