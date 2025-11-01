/**
 * Hook for optimized shared component loading and management
 * Provides intelligent loading strategies for shared components
 */

import React, { useEffect, useCallback, useState } from "react";
import { usePathname } from "next/navigation";
import {
  sharedComponentOptimizer,
  sharedComponents,
} from "../shared-components";
import { getRouteKey } from "../route-config";

interface SharedComponentState {
  isLoading: boolean;
  isLoaded: boolean;
  error: Error | null;
}

export const useSharedComponents = () => {
  const pathname = usePathname();
  const currentRoute = getRouteKey(pathname);
  const [componentStates, setComponentStates] = useState<
    Record<string, SharedComponentState>
  >({});

  // Initialize component states
  useEffect(() => {
    const initialStates: Record<string, SharedComponentState> = {};
    Object.keys(sharedComponents).forEach((name) => {
      initialStates[name] = {
        isLoading: false,
        isLoaded: sharedComponentOptimizer.isPreloaded(name),
        error: null,
      };
    });
    setComponentStates(initialStates);
  }, []);

  // Preload critical components on mount
  useEffect(() => {
    const preloadCritical = async () => {
      try {
        await sharedComponentOptimizer.preloadCriticalComponents();

        // Update states for preloaded components
        setComponentStates((prev) => {
          const updated = { ...prev };
          Object.entries(sharedComponents).forEach(([name, config]) => {
            if (config.priority === "critical" && config.preload) {
              updated[name] = {
                isLoading: false,
                isLoaded: true,
                error: null,
              };
            }
          });
          return updated;
        });
      } catch (error) {
        console.error("Failed to preload critical components:", error);
      }
    };

    preloadCritical();
  }, []);

  // Preload route-specific components when route changes
  useEffect(() => {
    const preloadRouteComponents = async () => {
      try {
        await sharedComponentOptimizer.preloadRouteComponents(currentRoute);

        // Update states for route components
        const routeBundle =
          sharedComponentOptimizer.getRouteComponentBundle(currentRoute);
        const allRouteComponents = [
          ...routeBundle.critical,
          ...routeBundle.high,
          ...routeBundle.medium,
          ...routeBundle.low,
        ];

        setComponentStates((prev) => {
          const updated = { ...prev };
          allRouteComponents.forEach((name) => {
            const config = sharedComponents[name];
            if (config && config.preload) {
              updated[name] = {
                isLoading: false,
                isLoaded: true,
                error: null,
              };
            }
          });
          return updated;
        });
      } catch (error) {
        console.error(
          `Failed to preload components for route ${currentRoute}:`,
          error
        );
      }
    };

    preloadRouteComponents();
  }, [currentRoute]);

  // Load specific component on demand
  const loadComponent = useCallback(async (componentName: string) => {
    const config = sharedComponents[componentName];
    if (!config) {
      throw new Error(
        `Component ${componentName} not found in shared components`
      );
    }

    // Check if already loaded
    if (sharedComponentOptimizer.isPreloaded(componentName)) {
      return sharedComponentOptimizer.getCachedComponent(componentName);
    }

    // Set loading state
    setComponentStates((prev) => ({
      ...prev,
      [componentName]: {
        isLoading: true,
        isLoaded: false,
        error: null,
      },
    }));

    try {
      const componentModule = await config.component();
      const component = componentModule.default;

      // Update loaded state
      setComponentStates((prev) => ({
        ...prev,
        [componentName]: {
          isLoading: false,
          isLoaded: true,
          error: null,
        },
      }));

      return component;
    } catch (error) {
      // Update error state
      setComponentStates((prev) => ({
        ...prev,
        [componentName]: {
          isLoading: false,
          isLoaded: false,
          error: error as Error,
        },
      }));

      throw error;
    }
  }, []);

  // Get component loading state
  const getComponentState = useCallback(
    (componentName: string): SharedComponentState => {
      return (
        componentStates[componentName] || {
          isLoading: false,
          isLoaded: false,
          error: null,
        }
      );
    },
    [componentStates]
  );

  // Check if all critical components are loaded
  const areCriticalComponentsLoaded = useCallback((): boolean => {
    const criticalComponents = Object.entries(sharedComponents)
      .filter(([_, config]) => config.priority === "critical")
      .map(([name]) => name);

    return criticalComponents.every(
      (name) =>
        componentStates[name]?.isLoaded ||
        sharedComponentOptimizer.isPreloaded(name)
    );
  }, [componentStates]);

  // Get route-specific component bundle
  const getRouteBundle = useCallback(() => {
    return sharedComponentOptimizer.getRouteComponentBundle(currentRoute);
  }, [currentRoute]);

  // Preload components for a specific route (for prefetching)
  const preloadForRoute = useCallback(async (routeName: string) => {
    try {
      await sharedComponentOptimizer.preloadRouteComponents(routeName);
    } catch (error) {
      console.warn(
        `Failed to preload components for route ${routeName}:`,
        error
      );
    }
  }, []);

  return {
    loadComponent,
    getComponentState,
    areCriticalComponentsLoaded,
    getRouteBundle,
    preloadForRoute,
    currentRoute,
    componentStates,
  };
};

// HOC for shared component optimization
// Note: This should be moved to a separate .tsx file for proper JSX support
export const createWithSharedComponentOptimization = () => {
  // This is a factory function that returns the HOC
  // The actual JSX HOC should be implemented in a .tsx file
  return null;
};
