/**
 * Hook for intelligent route prefetching with advanced behavior prediction
 * Integrates with the IntelligentPrefetcher for optimal user experience
 */

import { useEffect, useCallback, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { intelligentPrefetcher } from "../intelligent-prefetching";
import { getRouteKey } from "../route-config";

interface PrefetchingState {
  isActive: boolean;
  prefetchedRoutes: string[];
  queueLength: number;
  hitRate: number;
}

interface HoverTrackingData {
  startTime: number;
  element: HTMLElement | null;
  route: string;
}

export const useIntelligentPrefetching = () => {
  const pathname = usePathname();
  const currentRoute = getRouteKey(pathname);
  const previousRoute = useRef<string | null>(null);
  const [prefetchingState, setPrefetchingState] = useState<PrefetchingState>({
    isActive: true,
    prefetchedRoutes: [],
    queueLength: 0,
    hitRate: 0,
  });

  const hoverTracking = useRef<HoverTrackingData | null>(null);
  const hoverTimerRef = useRef<NodeJS.Timeout | null>(null);
  const intersectionObserver = useRef<IntersectionObserver | null>(null);

  // Track route changes and update behavior data
  useEffect(() => {
    if (previousRoute.current && previousRoute.current !== currentRoute) {
      intelligentPrefetcher.trackRouteVisit(
        currentRoute,
        previousRoute.current
      );
    } else if (!previousRoute.current) {
      intelligentPrefetcher.trackRouteVisit(currentRoute);
    }

    previousRoute.current = currentRoute;
  }, [currentRoute]);

  // Update prefetching state periodically
  useEffect(() => {
    const updateState = () => {
      const analytics = intelligentPrefetcher.getAnalytics();
      setPrefetchingState({
        isActive: true,
        prefetchedRoutes: analytics.prefetchedRoutes,
        queueLength: analytics.queueLength,
        hitRate: analytics.hitRate,
      });
    };

    updateState();
    const interval = setInterval(updateState, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  // Set up intersection observer for viewport-based prefetching
  useEffect(() => {
    if (typeof window === "undefined") return;

    intersectionObserver.current = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const link = entry.target as HTMLAnchorElement;
            const href = link.getAttribute("href");
            if (href) {
              const route = getRouteKey(href);
              // Prefetch with lower priority for viewport-based prefetching
              intelligentPrefetcher.prefetchOnHover(route, 0);
            }
          }
        });
      },
      {
        rootMargin: "50px", // Start prefetching when link is 50px from viewport
        threshold: 0.1,
      }
    );

    return () => {
      if (intersectionObserver.current) {
        intersectionObserver.current.disconnect();
      }
    };
  }, []);

  // Enhanced hover-based prefetching with duration tracking
  const handleLinkHover = useCallback((href: string, element?: HTMLElement) => {
    const route = getRouteKey(href);
    const now = Date.now();

    // Clear any existing timer
    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current);
      hoverTimerRef.current = null;
    }

    // Start tracking hover
    hoverTracking.current = {
      startTime: now,
      element: element || null,
      route,
    };

    // Set element only if provided
    if (element) {
      hoverTracking.current.element = element;
    }

    // Immediate prefetch for high-priority routes
    const analytics = intelligentPrefetcher.getAnalytics();
    const isHighPriority = analytics.behaviorData.visitedRoutes.includes(route);

    if (isHighPriority) {
      intelligentPrefetcher.prefetchOnHover(route, 0);
    } else {
      // Delayed prefetch for other routes
      hoverTimerRef.current = setTimeout(() => {
        if (hoverTracking.current && hoverTracking.current.route === route) {
          const hoverDuration = Date.now() - hoverTracking.current.startTime;
          intelligentPrefetcher.prefetchOnHover(route, hoverDuration);
        }
      }, 200);
    }
  }, []);

  // Handle hover leave
  const handleLinkLeave = useCallback((href: string) => {
    const route = getRouteKey(href);

    // Clear timer on leave
    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current);
      hoverTimerRef.current = null;
    }

    if (hoverTracking.current && hoverTracking.current.route === route) {
      const hoverDuration = Date.now() - hoverTracking.current.startTime;

      // If hover was long enough, still prefetch
      if (hoverDuration > 500) {
        intelligentPrefetcher.prefetchOnHover(route, hoverDuration);
      }

      hoverTracking.current = null;
    }
  }, []);

  // Observe links for viewport-based prefetching
  const observeLink = useCallback((element: HTMLElement) => {
    if (intersectionObserver.current && element) {
      intersectionObserver.current.observe(element);
    }
  }, []);

  // Unobserve links
  const unobserveLink = useCallback((element: HTMLElement) => {
    if (intersectionObserver.current && element) {
      intersectionObserver.current.unobserve(element);
    }
  }, []);

  // Manual prefetch trigger
  const prefetchRoute = useCallback((route: string, priority: number = 5) => {
    intelligentPrefetcher.prefetchOnHover(route, 1000); // Simulate long hover
  }, []);

  // Get prefetching recommendations for current route
  const getPrefetchRecommendations = useCallback(() => {
    const analytics = intelligentPrefetcher.getAnalytics();
    const currentTransitions =
      analytics.behaviorData.routeTransitions[currentRoute] || {};

    return Object.entries(currentTransitions)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([route, count]) => ({ route, probability: count }));
  }, [currentRoute]);

  // Check if route is prefetched
  const isPrefetched = useCallback(
    (route: string) => {
      return prefetchingState.prefetchedRoutes.includes(route);
    },
    [prefetchingState.prefetchedRoutes]
  );

  // Toggle prefetching on/off
  const togglePrefetching = useCallback((enabled: boolean) => {
    setPrefetchingState((prev) => ({ ...prev, isActive: enabled }));
  }, []);

  // Reset behavior data
  const resetBehaviorData = useCallback(() => {
    intelligentPrefetcher.resetBehaviorData();
    setPrefetchingState((prev) => ({
      ...prev,
      prefetchedRoutes: [],
      queueLength: 0,
      hitRate: 0,
    }));
  }, []);

  // Get detailed analytics
  const getDetailedAnalytics = useCallback(() => {
    return intelligentPrefetcher.getAnalytics();
  }, []);

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (hoverTimerRef.current) {
        clearTimeout(hoverTimerRef.current);
        hoverTimerRef.current = null;
      }
    };
  }, []);

  return {
    // Core prefetching functions
    handleLinkHover,
    handleLinkLeave,
    observeLink,
    unobserveLink,
    prefetchRoute,

    // State and analytics
    prefetchingState,
    isPrefetched,
    getPrefetchRecommendations,
    getDetailedAnalytics,

    // Controls
    togglePrefetching,
    resetBehaviorData,

    // Current route info
    currentRoute,
  };
};

// Enhanced Link component with intelligent prefetching
// Note: This should be moved to a separate .tsx file for proper JSX support
export const createIntelligentLink = () => {
  // This is a factory function that returns the component
  // The actual JSX component should be implemented in a .tsx file
  return null;
};
