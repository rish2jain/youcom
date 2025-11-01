/**
 * Hook for intelligent route prefetching based on user behavior
 * Implements hover-based and navigation pattern-based prefetching
 */

import React, { useEffect, useCallback, useRef } from "react";
import { usePathname } from "next/navigation";
import {
  preloadRoute,
  preloadLikelyRoutes,
  getRouteKey,
  navigationPatterns,
} from "../route-config";

interface PrefetchOptions {
  enableHoverPrefetch?: boolean;
  enablePatternPrefetch?: boolean;
  hoverDelay?: number;
  patternDelay?: number;
}

export const useRoutePrefetching = (options: PrefetchOptions = {}) => {
  const {
    enableHoverPrefetch = true,
    enablePatternPrefetch = true,
    hoverDelay = 300,
    patternDelay = 1000,
  } = options;

  const pathname = usePathname();
  const currentRoute = getRouteKey(pathname);
  const prefetchedRoutes = useRef(new Set<string>());
  const hoverTimeouts = useRef(new Map<string, NodeJS.Timeout>());

  // Prefetch routes based on navigation patterns
  useEffect(() => {
    if (!enablePatternPrefetch) return;

    const timer = setTimeout(() => {
      preloadLikelyRoutes(currentRoute);
    }, patternDelay);

    return () => clearTimeout(timer);
  }, [currentRoute, enablePatternPrefetch, patternDelay]);

  // Handle hover-based prefetching
  const handleLinkHover = useCallback(
    (href: string) => {
      if (!enableHoverPrefetch) return;

      const routeKey = getRouteKey(href);
      if (prefetchedRoutes.current.has(routeKey)) return;

      // Clear any existing timeout for this route
      const existingTimeout = hoverTimeouts.current.get(routeKey);
      if (existingTimeout) {
        clearTimeout(existingTimeout);
      }

      // Set new timeout for prefetching
      const timeout = setTimeout(() => {
        preloadRoute(routeKey).then(() => {
          prefetchedRoutes.current.add(routeKey);
        });
      }, hoverDelay);

      hoverTimeouts.current.set(routeKey, timeout);
    },
    [enableHoverPrefetch, hoverDelay]
  );

  // Handle hover leave to cancel prefetching
  const handleLinkLeave = useCallback(
    (href: string) => {
      if (!enableHoverPrefetch) return;

      const routeKey = getRouteKey(href);
      const timeout = hoverTimeouts.current.get(routeKey);

      if (timeout) {
        clearTimeout(timeout);
        hoverTimeouts.current.delete(routeKey);
      }
    },
    [enableHoverPrefetch]
  );

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      hoverTimeouts.current.forEach((timeout) => clearTimeout(timeout));
      hoverTimeouts.current.clear();
    };
  }, []);

  // Prefetch specific route manually
  const prefetchRoute = useCallback(async (routeKey: string) => {
    if (prefetchedRoutes.current.has(routeKey)) return;

    try {
      await preloadRoute(routeKey);
      prefetchedRoutes.current.add(routeKey);
    } catch (error) {
      console.warn(`Failed to prefetch route ${routeKey}:`, error);
    }
  }, []);

  // Get prefetch status
  const isPrefetched = useCallback((routeKey: string) => {
    return prefetchedRoutes.current.has(routeKey);
  }, []);

  return {
    handleLinkHover,
    handleLinkLeave,
    prefetchRoute,
    isPrefetched,
    currentRoute,
  };
};

// HOC for adding prefetch behavior to Link components
// Note: This should be moved to a separate .tsx file for proper JSX support
export const createWithPrefetch = () => {
  // This is a factory function that returns the HOC
  // The actual JSX HOC should be implemented in a .tsx file
  return null;
};
