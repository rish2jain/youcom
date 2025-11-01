/**
 * Component Registry for Lazy Loading and Preloading
 * Central registry for managing lazy-loaded components with intelligent preloading
 */

import { ComponentType, LazyExoticComponent } from "react";
import { createLazyComponent, LazyComponentConfig } from "./lazy-loading";
import { preloadingManager, PreloadConfig } from "./preloading-strategies";

export interface RegisteredComponent {
  name: string;
  lazyComponent: LazyExoticComponent<any>;
  importFn: () => Promise<{ default: ComponentType<any> }>;
  config: LazyComponentConfig & PreloadConfig;
  isPreloaded: boolean;
}

/**
 * Component Registry Class
 */
class ComponentRegistry {
  private components = new Map<string, RegisteredComponent>();
  private preloadQueue: string[] = [];

  /**
   * Register a component for lazy loading with preloading configuration
   */
  register<T extends ComponentType<any>>(
    name: string,
    importFn: () => Promise<{ default: T }>,
    config: Partial<LazyComponentConfig & PreloadConfig> = {}
  ): LazyExoticComponent<T> {
    const fullConfig: LazyComponentConfig & PreloadConfig = {
      name,
      importPath: name,
      priority: "medium",
      trigger: "idle",
      preload: false,
      ...config,
    };

    const lazyComponent = createLazyComponent(importFn, fullConfig);

    const registeredComponent: RegisteredComponent = {
      name,
      lazyComponent,
      importFn,
      config: fullConfig,
      isPreloaded: false,
    };

    this.components.set(name, registeredComponent);

    // Handle immediate preloading
    if (fullConfig.preload || fullConfig.priority === "high") {
      this.preloadComponent(name);
    }

    // Add to preload queue based on priority
    if (fullConfig.priority === "medium") {
      this.preloadQueue.push(name);
    }

    return lazyComponent;
  }

  /**
   * Get a registered component
   */
  get(name: string): LazyExoticComponent<any> | undefined {
    return this.components.get(name)?.lazyComponent;
  }

  /**
   * Preload a specific component
   */
  async preloadComponent(name: string): Promise<void> {
    const component = this.components.get(name);
    if (!component || component.isPreloaded) return;

    try {
      await preloadingManager.preloadImmediate(name, component.importFn);
      component.isPreloaded = true;
    } catch (error) {
      console.warn(`Failed to preload component ${name}:`, error);
    }
  }

  /**
   * Preload components based on current route and user behavior
   */
  preloadForRoute(route: string): void {
    const routeComponents = this.getComponentsForRoute(route);

    // Preload high priority components immediately
    const highPriority = routeComponents.filter(
      (c) => c.config.priority === "high"
    );
    highPriority.forEach((component) => {
      this.preloadComponent(component.name);
    });

    // Preload medium priority components with delay
    const mediumPriority = routeComponents.filter(
      (c) => c.config.priority === "medium"
    );
    setTimeout(() => {
      mediumPriority.forEach((component) => {
        if (!component.config.condition || component.config.condition()) {
          this.preloadComponent(component.name);
        }
      });
    }, 1000);

    // Use behavior-based preloading for other components
    const componentMap = new Map(
      Array.from(this.components.values()).map((c) => [c.name, c.importFn])
    );
    preloadingManager.preloadBasedOnBehavior(componentMap);
  }

  /**
   * Get components that should be preloaded for a specific route
   */
  private getComponentsForRoute(route: string): RegisteredComponent[] {
    // Define route-component mappings
    const routeMappings: Record<string, string[]> = {
      "/dashboard": ["ImpactCardDisplay", "CompanyResearch", "WatchList"],
      "/research": ["CompanyResearch", "APIUsageDashboard", "ComparisonTable"],
      "/analytics": [
        "EnhancedAnalytics",
        "PredictiveAnalytics",
        "LiveMetricsDashboard",
      ],
      "/monitoring": [
        "PerformanceMonitor",
        "IntegrationHealthMonitor",
        "NotificationSystem",
      ],
      "/integrations": [
        "IntegrationManager",
        "HubSpotIntegrationSetup",
        "ObsidianIntegrationSetup",
      ],
      "/settings": [
        "ModePreferences",
        "NotificationRulesManager",
        "PerformanceMonitoringDashboard",
      ],
    };

    const componentNames = routeMappings[route] || [];
    return componentNames
      .map((name) => this.components.get(name))
      .filter(
        (component): component is RegisteredComponent => component !== undefined
      );
  }

  /**
   * Preload components with intelligent priority management
   */
  async preloadWithIntelligentPriority(): Promise<void> {
    const allComponents = Array.from(this.components.values());

    const componentsWithConfig = allComponents.map((component) => ({
      name: component.name,
      importFn: component.importFn,
      config: component.config,
    }));

    await preloadingManager.preloadWithPriority(componentsWithConfig);
  }

  /**
   * Get preloading statistics
   */
  getStats(): {
    total: number;
    preloaded: number;
    highPriority: number;
    mediumPriority: number;
    lowPriority: number;
  } {
    const components = Array.from(this.components.values());

    return {
      total: components.length,
      preloaded: components.filter((c) => c.isPreloaded).length,
      highPriority: components.filter((c) => c.config.priority === "high")
        .length,
      mediumPriority: components.filter((c) => c.config.priority === "medium")
        .length,
      lowPriority: components.filter((c) => c.config.priority === "low").length,
    };
  }

  /**
   * Clear all preloaded components
   */
  clearPreloadCache(): void {
    this.components.forEach((component) => {
      component.isPreloaded = false;
    });
    preloadingManager.clearCache();
  }

  /**
   * Get all registered components (immutable view)
   */
  getAllComponents(): ReadonlyMap<string, Readonly<RegisteredComponent>> {
    const clonedComponents = new Map<string, Readonly<RegisteredComponent>>();
    this.components.forEach((component, key) => {
      clonedComponents.set(key, Object.freeze({ ...component }));
    });
    return clonedComponents;
  }
}

// Global registry instance
export const componentRegistry = new ComponentRegistry();

/**
 * Convenience function to register components
 */
export function registerComponent<T extends ComponentType<any>>(
  name: string,
  importFn: () => Promise<{ default: T }>,
  config?: Partial<LazyComponentConfig & PreloadConfig>
): LazyExoticComponent<T> {
  return componentRegistry.register(name, importFn, config);
}

/**
 * Convenience function to preload components for a route
 */
export function preloadForRoute(route: string): void {
  componentRegistry.preloadForRoute(route);
}

/**
 * Initialize intelligent preloading based on current environment
 */
export function initializeIntelligentPreloading(): void {
  if (typeof window === "undefined") return;

  // Preload based on current route
  const currentRoute = window.location.pathname;
  componentRegistry.preloadForRoute(currentRoute);

  // Set up route change listener for future preloading
  const originalPushState = history.pushState;
  history.pushState = function (...args) {
    originalPushState.apply(history, args);
    componentRegistry.preloadForRoute(window.location.pathname);
  };

  // Preload with intelligent priority after initial load
  setTimeout(() => {
    componentRegistry.preloadWithIntelligentPriority();
  }, 2000);
}
