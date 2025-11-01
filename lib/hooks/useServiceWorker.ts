import { useEffect, useState, useCallback } from "react";
import serviceWorkerManager, {
  type CacheStatus,
  getCriticalResources,
  warmCacheForUser,
} from "../service-worker";

export interface ServiceWorkerState {
  isSupported: boolean;
  isRegistered: boolean;
  isUpdateAvailable: boolean;
  isInstalling: boolean;
  cacheStatus: CacheStatus;
  error: string | null;
}

export interface ServiceWorkerActions {
  register: () => Promise<void>;
  unregister: () => Promise<void>;
  update: () => Promise<void>;
  skipWaiting: () => Promise<void>;
  clearCache: (cacheName?: string) => Promise<void>;
  warmCache: (urls: string[]) => Promise<void>;
  refreshCacheStatus: () => Promise<void>;
}

export const useServiceWorker = (): [
  ServiceWorkerState,
  ServiceWorkerActions
] => {
  const [state, setState] = useState<ServiceWorkerState>({
    isSupported: false,
    isRegistered: false,
    isUpdateAvailable: false,
    isInstalling: false,
    cacheStatus: {},
    error: null,
  });

  // Initialize service worker support check
  useEffect(() => {
    setState((prev) => ({
      ...prev,
      isSupported: serviceWorkerManager.isSupported(),
      isRegistered: serviceWorkerManager.isRegistered(),
    }));
  }, []);

  // Listen for service worker updates
  useEffect(() => {
    const handleUpdateAvailable = () => {
      setState((prev) => ({ ...prev, isUpdateAvailable: true }));
    };

    const handleInstalling = () => {
      setState((prev) => ({ ...prev, isInstalling: true }));
    };

    const handleInstalled = () => {
      setState((prev) => ({ ...prev, isInstalling: false }));
    };

    window.addEventListener("sw-update-available", handleUpdateAvailable);

    // Listen for service worker state changes
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.addEventListener("message", (event) => {
        const { type } = event.data;

        switch (type) {
          case "installing":
            handleInstalling();
            break;
          case "installed":
            handleInstalled();
            break;
        }
      });
    }

    return () => {
      window.removeEventListener("sw-update-available", handleUpdateAvailable);
    };
  }, []);

  // Actions
  const register = useCallback(async () => {
    try {
      setState((prev) => ({ ...prev, error: null, isInstalling: true }));

      const registration = await serviceWorkerManager.register();

      setState((prev) => ({
        ...prev,
        isRegistered: !!registration,
        isInstalling: false,
        error: registration ? null : "Registration failed",
      }));

      // Warm cache with critical resources after registration
      if (registration) {
        const criticalResources = getCriticalResources();
        await serviceWorkerManager.warmCache(criticalResources);
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : "Registration failed",
        isInstalling: false,
      }));
    }
  }, []);

  const unregister = useCallback(async () => {
    try {
      setState((prev) => ({ ...prev, error: null }));

      const success = await serviceWorkerManager.unregister();

      setState((prev) => ({
        ...prev,
        isRegistered: !success,
        error: success ? null : "Unregistration failed",
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : "Unregistration failed",
      }));
    }
  }, []);

  const update = useCallback(async () => {
    try {
      setState((prev) => ({ ...prev, error: null }));
      await serviceWorkerManager.update();
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : "Update failed",
      }));
    }
  }, []);

  const skipWaiting = useCallback(async () => {
    try {
      setState((prev) => ({ ...prev, error: null, isUpdateAvailable: false }));
      await serviceWorkerManager.skipWaiting();
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : "Skip waiting failed",
      }));
    }
  }, []);

  const clearCache = useCallback(async (cacheName?: string) => {
    try {
      setState((prev) => ({ ...prev, error: null }));
      await serviceWorkerManager.clearCache(cacheName);

      // Refresh cache status after clearing
      const newCacheStatus = await serviceWorkerManager.getCacheStatus();
      setState((prev) => ({ ...prev, cacheStatus: newCacheStatus }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : "Cache clearing failed",
      }));
    }
  }, []);

  const warmCache = useCallback(async (urls: string[]) => {
    try {
      setState((prev) => ({ ...prev, error: null }));
      await serviceWorkerManager.warmCache(urls);

      // Refresh cache status after warming
      const newCacheStatus = await serviceWorkerManager.getCacheStatus();
      setState((prev) => ({ ...prev, cacheStatus: newCacheStatus }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: error instanceof Error ? error.message : "Cache warming failed",
      }));
    }
  }, []);

  const refreshCacheStatus = useCallback(async () => {
    try {
      const cacheStatus = await serviceWorkerManager.getCacheStatus();
      setState((prev) => ({ ...prev, cacheStatus, error: null }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error:
          error instanceof Error ? error.message : "Failed to get cache status",
      }));
    }
  }, []);

  // Auto-refresh cache status periodically
  useEffect(() => {
    if (state.isRegistered) {
      refreshCacheStatus();

      const interval = setInterval(refreshCacheStatus, 30000); // Every 30 seconds
      return () => clearInterval(interval);
    }
  }, [state.isRegistered]); // Remove refreshCacheStatus from deps to prevent infinite loop

  const actions: ServiceWorkerActions = {
    register,
    unregister,
    update,
    skipWaiting,
    clearCache,
    warmCache,
    refreshCacheStatus,
  };

  return [state, actions];
};

// Hook for automatic service worker registration
export const useAutoServiceWorker = (
  options: {
    autoRegister?: boolean;
    warmCacheOnRegister?: boolean;
    userBehavior?: {
      frequentRoutes: string[];
      recentActions: string[];
    };
  } = {}
): [ServiceWorkerState, ServiceWorkerActions] => {
  const {
    autoRegister = true,
    warmCacheOnRegister = true,
    userBehavior,
  } = options;
  const [state, actions] = useServiceWorker();

  useEffect(() => {
    if (autoRegister && state.isSupported && !state.isRegistered) {
      actions.register();
    }
  }, [autoRegister, state.isSupported, state.isRegistered, actions.register]);

  // Warm cache based on user behavior
  useEffect(() => {
    if (warmCacheOnRegister && state.isRegistered && userBehavior) {
      warmCacheForUser(userBehavior).catch((error) => {
        console.error("Failed to warm cache for user behavior:", error);
      });
    }
  }, [warmCacheOnRegister, state.isRegistered, userBehavior]);

  return [state, actions];
};

// Hook for cache performance monitoring
export const useCachePerformance = () => {
  const [performanceMetrics, setPerformanceMetrics] = useState({
    cacheHitRate: 0,
    averageLoadTime: 0,
    offlineCapability: false,
    lastUpdated: new Date(),
  });

  const measurePerformance = useCallback(async () => {
    try {
      // This would integrate with actual performance monitoring
      // For now, simulate performance metrics
      const navigationEntries = performance.getEntriesByType(
        "navigation"
      ) as PerformanceNavigationTiming[];
      const resourceEntries = performance.getEntriesByType(
        "resource"
      ) as PerformanceResourceTiming[];

      // Calculate cache hit rate based on resource timing
      const cachedResources = resourceEntries.filter(
        (entry) => entry.transferSize === 0 && entry.decodedBodySize > 0
      );
      const cacheHitRate =
        resourceEntries.length > 0
          ? cachedResources.length / resourceEntries.length
          : 0;

      // Calculate average load time
      const averageLoadTime =
        navigationEntries.length > 0
          ? navigationEntries[0].loadEventEnd - navigationEntries[0].fetchStart
          : 0;

      setPerformanceMetrics({
        cacheHitRate,
        averageLoadTime,
        offlineCapability:
          "serviceWorker" in navigator && serviceWorkerManager.isRegistered(),
        lastUpdated: new Date(),
      });
    } catch (error) {
      console.error("Failed to measure cache performance:", error);
    }
  }, []);

  useEffect(() => {
    measurePerformance();

    const interval = setInterval(measurePerformance, 60000); // Every minute
    return () => clearInterval(interval);
  }, []); // Remove measurePerformance from deps to prevent infinite loop

  return { performance: performanceMetrics, measurePerformance };
};
