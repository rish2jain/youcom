import { useEffect, useCallback, useState } from "react";
import { usePathname } from "next/navigation";
import {
  warmCache,
  preloadRoute,
  updateUserBehavior,
  getWarmingStatus,
  type UserBehaviorPattern,
} from "../cache-warming";

export interface CacheWarmingState {
  isWarming: boolean;
  queueLength: number;
  strategiesCount: number;
  userBehavior: UserBehaviorPattern | null;
}

export const useCacheWarming = () => {
  const pathname = usePathname();
  const [state, setState] = useState<CacheWarmingState>({
    isWarming: false,
    queueLength: 0,
    strategiesCount: 0,
    userBehavior: null,
  });

  // Update state periodically
  useEffect(() => {
    const updateState = () => {
      const status = getWarmingStatus();
      setState(status);
    };

    updateState();
    const interval = setInterval(updateState, 5000); // Every 5 seconds

    return () => clearInterval(interval);
  }, []); // Empty dependency array is correct here

  // Track route changes for user behavior
  useEffect(() => {
    const now = new Date();
    const hour = now.getHours();
    const dayOfWeek = now.getDay();

    // Update user behavior pattern
    updateUserBehavior({
      frequentRoutes: [pathname],
      timeOfDay: hour < 12 ? "morning" : hour < 18 ? "afternoon" : "evening",
      dayOfWeek: dayOfWeek === 0 || dayOfWeek === 6 ? "weekend" : "weekday",
      lastVisit: now,
    });
  }, [pathname]);

  const warmCacheManually = useCallback(async (strategyName?: string) => {
    try {
      await warmCache(strategyName);
    } catch (error) {
      console.error("Manual cache warming failed:", error);
    }
  }, []);

  const preloadRouteManually = useCallback(async (route: string) => {
    try {
      await preloadRoute(route);
    } catch (error) {
      console.error("Manual route preloading failed:", error);
    }
  }, []);

  return {
    state,
    warmCache: warmCacheManually,
    preloadRoute: preloadRouteManually,
  };
};

// Hook for intelligent link preloading
export const useIntelligentPreloading = () => {
  const [preloadedRoutes, setPreloadedRoutes] = useState<Set<string>>(
    new Set()
  );
  const [isPreloading, setIsPreloading] = useState(false);

  const preloadOnHover = useCallback(
    async (route: string) => {
      if (preloadedRoutes.has(route) || isPreloading) {
        return;
      }

      setIsPreloading(true);
      try {
        await preloadRoute(route);
        setPreloadedRoutes((prev) => {
          const newSet = new Set(prev);
          newSet.add(route);
          return newSet;
        });
      } catch (error) {
        console.error("Hover preloading failed:", error);
      } finally {
        setIsPreloading(false);
      }
    },
    [preloadedRoutes, isPreloading]
  );

  const preloadOnIntersection = useCallback(
    async (route: string) => {
      if (preloadedRoutes.has(route)) {
        return;
      }

      try {
        await preloadRoute(route);
        setPreloadedRoutes((prev) => {
          const newSet = new Set(prev);
          newSet.add(route);
          return newSet;
        });
      } catch (error) {
        console.error("Intersection preloading failed:", error);
      }
    },
    [preloadedRoutes]
  );

  return {
    preloadOnHover,
    preloadOnIntersection,
    preloadedRoutes: Array.from(preloadedRoutes),
    isPreloading,
  };
};

// Hook for user behavior tracking
export const useUserBehaviorTracking = () => {
  const pathname = usePathname();
  const [sessionStart] = useState(new Date());
  const [actions, setActions] = useState<string[]>([]);

  // Track user actions
  const trackAction = useCallback(
    (action: string) => {
      setActions((prev) => {
        const updated = [...prev, action].slice(-10); // Keep last 10 actions

        // Update user behavior
        updateUserBehavior({
          recentActions: updated,
          sessionDuration: Math.round(
            (Date.now() - sessionStart.getTime()) / 60000
          ), // in minutes
        });

        return updated;
      });
    },
    [sessionStart]
  );

  // Track page views
  useEffect(() => {
    trackAction(`view:${pathname}`);
  }, [pathname, trackAction]);

  // Track session duration on unmount
  useEffect(() => {
    const handleBeforeUnload = () => {
      const sessionDuration = Math.round(
        (Date.now() - sessionStart.getTime()) / 60000
      );
      updateUserBehavior({ sessionDuration });
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [sessionStart]);

  return {
    trackAction,
    actions,
    sessionDuration: Math.round((Date.now() - sessionStart.getTime()) / 60000),
  };
};

// Hook for cache performance monitoring
export const useCachePerformanceMonitoring = () => {
  const [metrics, setMetrics] = useState({
    cacheHitRate: 0,
    averageLoadTime: 0,
    preloadSuccessRate: 0,
    memoryUsage: 0,
  });

  useEffect(() => {
    const measurePerformance = () => {
      // Measure cache performance
      const navigationEntries = performance.getEntriesByType(
        "navigation"
      ) as PerformanceNavigationTiming[];
      const resourceEntries = performance.getEntriesByType(
        "resource"
      ) as PerformanceResourceTiming[];

      // Calculate cache hit rate
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

      // Estimate memory usage
      let memoryUsage = 0;
      if ("memory" in performance) {
        const memory = (performance as any).memory;
        memoryUsage = memory.usedJSHeapSize / (1024 * 1024); // MB
      }

      setMetrics({
        cacheHitRate,
        averageLoadTime,
        preloadSuccessRate: 0.9, // This would be tracked separately
        memoryUsage,
      });
    };

    measurePerformance();
    const interval = setInterval(measurePerformance, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return metrics;
};
