/**
 * Tests for Service Worker React hooks
 */

import { renderHook, act } from "@testing-library/react";
import {
  useServiceWorker,
  useAutoServiceWorker,
  useCachePerformance,
} from "../useServiceWorker";

// Mock service worker manager
const mockServiceWorkerManager = {
  isSupported: jest.fn(() => true),
  isRegistered: jest.fn(() => false),
  register: jest.fn(),
  unregister: jest.fn(),
  update: jest.fn(),
  clearCache: jest.fn(),
  warmCache: jest.fn(),
  getCacheStatus: jest.fn(() => ({})),
  skipWaiting: jest.fn(),
};

jest.mock("../service-worker", () => ({
  default: mockServiceWorkerManager,
  getCriticalResources: jest.fn(() => ["/", "/dashboard"]),
  warmCacheForUser: jest.fn(),
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

// Mock navigator
Object.defineProperty(global, "navigator", {
  value: {
    serviceWorker: {
      addEventListener: jest.fn(),
    },
  },
  writable: true,
});

describe("useServiceWorker", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockServiceWorkerManager.isSupported.mockReturnValue(true);
    mockServiceWorkerManager.isRegistered.mockReturnValue(false);
  });

  it("should initialize with correct default state", () => {
    const { result } = renderHook(() => useServiceWorker());
    const [state] = result.current;

    expect(state.isSupported).toBe(true);
    expect(state.isRegistered).toBe(false);
    expect(state.isUpdateAvailable).toBe(false);
    expect(state.isInstalling).toBe(false);
    expect(state.cacheStatus).toEqual({});
    expect(state.error).toBeNull();
  });

  it("should register service worker successfully", async () => {
    mockServiceWorkerManager.register.mockResolvedValueOnce({});
    mockServiceWorkerManager.warmCache.mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useServiceWorker());
    const [, actions] = result.current;

    await act(async () => {
      await actions.register();
    });

    expect(mockServiceWorkerManager.register).toHaveBeenCalled();
    expect(mockServiceWorkerManager.warmCache).toHaveBeenCalled();
  });

  it("should handle registration failure", async () => {
    mockServiceWorkerManager.register.mockResolvedValueOnce(null);

    const { result } = renderHook(() => useServiceWorker());
    const [, actions] = result.current;

    await act(async () => {
      await actions.register();
    });

    const [state] = result.current;
    expect(state.error).toBe("Registration failed");
    expect(state.isRegistered).toBe(false);
  });

  it("should unregister service worker", async () => {
    mockServiceWorkerManager.unregister.mockResolvedValueOnce(true);

    const { result } = renderHook(() => useServiceWorker());
    const [, actions] = result.current;

    await act(async () => {
      await actions.unregister();
    });

    expect(mockServiceWorkerManager.unregister).toHaveBeenCalled();
  });

  it("should clear cache and refresh status", async () => {
    const mockCacheStatus = { "test-cache": { entryCount: 5, urls: [] } };
    mockServiceWorkerManager.clearCache.mockResolvedValueOnce(undefined);
    mockServiceWorkerManager.getCacheStatus.mockResolvedValueOnce(
      mockCacheStatus
    );

    const { result } = renderHook(() => useServiceWorker());
    const [, actions] = result.current;

    await act(async () => {
      await actions.clearCache("test-cache");
    });

    expect(mockServiceWorkerManager.clearCache).toHaveBeenCalledWith(
      "test-cache"
    );
    expect(mockServiceWorkerManager.getCacheStatus).toHaveBeenCalled();
  });

  it("should warm cache and refresh status", async () => {
    const urls = ["/page1", "/page2"];
    const mockCacheStatus = { "runtime-cache": { entryCount: 2, urls } };
    mockServiceWorkerManager.warmCache.mockResolvedValueOnce(undefined);
    mockServiceWorkerManager.getCacheStatus.mockResolvedValueOnce(
      mockCacheStatus
    );

    const { result } = renderHook(() => useServiceWorker());
    const [, actions] = result.current;

    await act(async () => {
      await actions.warmCache(urls);
    });

    expect(mockServiceWorkerManager.warmCache).toHaveBeenCalledWith(urls);
    expect(mockServiceWorkerManager.getCacheStatus).toHaveBeenCalled();
  });

  it("should handle errors gracefully", async () => {
    mockServiceWorkerManager.register.mockRejectedValueOnce(
      new Error("Network error")
    );

    const { result } = renderHook(() => useServiceWorker());
    const [, actions] = result.current;

    await act(async () => {
      await actions.register();
    });

    const [state] = result.current;
    expect(state.error).toBe("Network error");
  });
});

describe("useAutoServiceWorker", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockServiceWorkerManager.isSupported.mockReturnValue(true);
    mockServiceWorkerManager.isRegistered.mockReturnValue(false);
  });

  it("should auto-register when enabled and supported", () => {
    mockServiceWorkerManager.register.mockResolvedValueOnce({});

    renderHook(() => useAutoServiceWorker({ autoRegister: true }));

    expect(mockServiceWorkerManager.register).toHaveBeenCalled();
  });

  it("should not auto-register when disabled", () => {
    renderHook(() => useAutoServiceWorker({ autoRegister: false }));

    expect(mockServiceWorkerManager.register).not.toHaveBeenCalled();
  });

  it("should not auto-register when not supported", () => {
    mockServiceWorkerManager.isSupported.mockReturnValue(false);

    renderHook(() => useAutoServiceWorker({ autoRegister: true }));

    expect(mockServiceWorkerManager.register).not.toHaveBeenCalled();
  });

  it("should warm cache based on user behavior when registered", () => {
    const userBehavior = {
      frequentRoutes: ["/dashboard", "/research"],
      recentActions: ["view", "export"],
    };

    mockServiceWorkerManager.isRegistered.mockReturnValue(true);
    const { warmCacheForUser } = require("../service-worker");

    renderHook(() =>
      useAutoServiceWorker({
        warmCacheOnRegister: true,
        userBehavior,
      })
    );

    expect(warmCacheForUser).toHaveBeenCalledWith(userBehavior);
  });
});

describe("useCachePerformance", () => {
  beforeEach(() => {
    // Mock performance API
    Object.defineProperty(global, "performance", {
      value: {
        getEntriesByType: jest.fn(),
        measurePerformance: jest.fn(),
      },
      writable: true,
    });
  });

  it("should initialize with default performance metrics", () => {
    const { result } = renderHook(() => useCachePerformance());

    expect(result.current.performance.cacheHitRate).toBe(0);
    expect(result.current.performance.averageLoadTime).toBe(0);
    expect(result.current.performance.offlineCapability).toBe(false);
    expect(result.current.performance.lastUpdated).toBeInstanceOf(Date);
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

    const { result } = renderHook(() => useCachePerformance());

    // Should calculate 2/3 = 0.67 cache hit rate
    expect(result.current.performance.cacheHitRate).toBeCloseTo(0.67, 2);
  });

  it("should calculate average load time from navigation entries", () => {
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

    const { result } = renderHook(() => useCachePerformance());

    expect(result.current.performance.averageLoadTime).toBe(2000);
  });

  it("should handle missing performance entries gracefully", () => {
    global.performance.getEntriesByType = jest.fn().mockReturnValue([]); // No entries

    const { result } = renderHook(() => useCachePerformance());

    expect(result.current.performance.cacheHitRate).toBe(0);
    expect(result.current.performance.averageLoadTime).toBe(0);
  });

  it("should provide measurePerformance function", () => {
    const { result } = renderHook(() => useCachePerformance());

    expect(typeof result.current.measurePerformance).toBe("function");
  });
});
