/**
 * Shared component optimization system
 * Identifies and optimizes components used across multiple routes
 */

import { ComponentType } from "react";

export interface SharedComponentConfig {
  name: string;
  component: () => Promise<{ default: ComponentType<any> }>;
  usedInRoutes: string[];
  priority: "critical" | "high" | "medium" | "low";
  preload: boolean;
  size: "small" | "medium" | "large";
}

// Shared components configuration
export const sharedComponents: Record<string, SharedComponentConfig> = {
  // Critical UI components used everywhere
  LoadingSkeleton: {
    name: "LoadingSkeleton",
    component: () =>
      import("@/components/LoadingSkeleton").then((m) => ({
        default: m.LoadingSkeleton,
      })),
    usedInRoutes: [
      "dashboard",
      "research",
      "analytics",
      "monitoring",
      "integrations",
      "settings",
    ],
    priority: "critical",
    preload: true,
    size: "small",
  },

  ErrorBoundary: {
    name: "ErrorBoundary",
    component: () =>
      import("@/components/LazyComponentErrorBoundary").then((m) => ({
        default: m.LazyComponentErrorBoundary,
      })),
    usedInRoutes: [
      "dashboard",
      "research",
      "analytics",
      "monitoring",
      "integrations",
      "settings",
    ],
    priority: "critical",
    preload: true,
    size: "small",
  },

  // High-priority shared components
  NotificationSystem: {
    name: "NotificationSystem",
    component: () =>
      import("@/components/NotificationSystem").then((m) => ({
        default: m.NotificationCenter,
      })),
    usedInRoutes: ["dashboard", "research", "analytics", "monitoring"],
    priority: "high",
    preload: true,
    size: "medium",
  },

  Header: {
    name: "Header",
    component: () => import("@/components/Header"),
    usedInRoutes: [
      "dashboard",
      "research",
      "analytics",
      "monitoring",
      "integrations",
      "settings",
    ],
    priority: "high",
    preload: true,
    size: "medium",
  },

  Sidebar: {
    name: "Sidebar",
    component: () => import("@/components/Sidebar"),
    usedInRoutes: [
      "dashboard",
      "research",
      "analytics",
      "monitoring",
      "integrations",
      "settings",
    ],
    priority: "high",
    preload: true,
    size: "medium",
  },

  // Medium-priority shared components
  ImpactCardDisplay: {
    name: "ImpactCardDisplay",
    component: () =>
      import("@/components/ImpactCardDisplay").then((m) => ({
        default: m.ImpactCardDisplay,
      })),
    usedInRoutes: ["dashboard", "research", "monitoring"],
    priority: "medium",
    preload: false,
    size: "large",
  },

  ComparisonTable: {
    name: "ComparisonTable",
    component: () =>
      import("@/components/ComparisonTable").then((m) => ({
        default: m.ComparisonTable,
      })),
    usedInRoutes: ["research", "analytics"],
    priority: "medium",
    preload: false,
    size: "medium",
  },

  SuccessAnimation: {
    name: "SuccessAnimation",
    component: () =>
      import("@/components/SuccessAnimation").then((m) => ({
        default: m.SuccessAnimation,
      })),
    usedInRoutes: ["dashboard", "monitoring", "integrations"],
    priority: "medium",
    preload: false,
    size: "small",
  },

  // Low-priority shared components
  FloatingChatWidget: {
    name: "FloatingChatWidget",
    component: () =>
      import("@/components/FloatingChatWidget").then((m) => ({
        default: m.FloatingChatWidget,
      })),
    usedInRoutes: ["dashboard", "research", "analytics"],
    priority: "low",
    preload: false,
    size: "medium",
  },

  OnboardingModal: {
    name: "OnboardingModal",
    component: () =>
      import("@/components/OnboardingModal").then((m) => ({
        default: m.OnboardingModal,
      })),
    usedInRoutes: ["dashboard", "research"],
    priority: "low",
    preload: false,
    size: "medium",
  },
};

// Route-specific component usage analysis
export const routeComponentUsage = {
  dashboard: [
    "LoadingSkeleton",
    "ErrorBoundary",
    "NotificationSystem",
    "Header",
    "Sidebar",
    "ImpactCardDisplay",
    "SuccessAnimation",
    "FloatingChatWidget",
    "OnboardingModal",
  ],
  research: [
    "LoadingSkeleton",
    "ErrorBoundary",
    "NotificationSystem",
    "Header",
    "Sidebar",
    "ImpactCardDisplay",
    "ComparisonTable",
    "FloatingChatWidget",
    "OnboardingModal",
  ],
  analytics: [
    "LoadingSkeleton",
    "ErrorBoundary",
    "NotificationSystem",
    "Header",
    "Sidebar",
    "ComparisonTable",
    "FloatingChatWidget",
  ],
  monitoring: [
    "LoadingSkeleton",
    "ErrorBoundary",
    "NotificationSystem",
    "Header",
    "Sidebar",
    "ImpactCardDisplay",
    "SuccessAnimation",
  ],
  integrations: [
    "LoadingSkeleton",
    "ErrorBoundary",
    "Header",
    "Sidebar",
    "SuccessAnimation",
  ],
  settings: ["LoadingSkeleton", "ErrorBoundary", "Header", "Sidebar"],
};

/**
 * Shared component optimization manager
 */
export class SharedComponentOptimizer {
  private static instance: SharedComponentOptimizer;
  private preloadedComponents = new Set<string>();
  private componentCache = new Map<string, ComponentType<any>>();

  static getInstance(): SharedComponentOptimizer {
    if (!SharedComponentOptimizer.instance) {
      SharedComponentOptimizer.instance = new SharedComponentOptimizer();
    }
    return SharedComponentOptimizer.instance;
  }

  /**
   * Preload critical shared components
   */
  async preloadCriticalComponents(): Promise<void> {
    const criticalComponents = Object.entries(sharedComponents)
      .filter(([_, config]) => config.priority === "critical" && config.preload)
      .map(([name, config]) => ({ name, config }));

    const preloadPromises = criticalComponents.map(async ({ name, config }) => {
      try {
        const componentModule = await config.component();
        this.componentCache.set(name, componentModule.default);
        this.preloadedComponents.add(name);
      } catch (error) {
        console.warn(`Failed to preload critical component ${name}:`, error);
      }
    });

    await Promise.all(preloadPromises);
  }

  /**
   * Preload components for a specific route
   */
  async preloadRouteComponents(routeName: string): Promise<void> {
    const routeComponents =
      routeComponentUsage[routeName as keyof typeof routeComponentUsage] || [];

    const componentsToPreload = routeComponents
      .filter((componentName) => {
        const config = sharedComponents[componentName];
        return (
          config &&
          config.preload &&
          !this.preloadedComponents.has(componentName)
        );
      })
      .map((componentName) => ({
        name: componentName,
        config: sharedComponents[componentName],
      }));

    const preloadPromises = componentsToPreload.map(
      async ({ name, config }) => {
        try {
          const componentModule = await config.component();
          this.componentCache.set(name, componentModule.default);
          this.preloadedComponents.add(name);
        } catch (error) {
          console.warn(
            `Failed to preload component ${name} for route ${routeName}:`,
            error
          );
        }
      }
    );

    await Promise.all(preloadPromises);
  }

  /**
   * Get optimized component bundle for a route
   */
  getRouteComponentBundle(routeName: string): {
    critical: string[];
    high: string[];
    medium: string[];
    low: string[];
  } {
    const routeComponents =
      routeComponentUsage[routeName as keyof typeof routeComponentUsage] || [];

    const bundle = {
      critical: [] as string[],
      high: [] as string[],
      medium: [] as string[],
      low: [] as string[],
    };

    routeComponents.forEach((componentName) => {
      const config = sharedComponents[componentName];
      if (config) {
        bundle[config.priority].push(componentName);
      }
    });

    return bundle;
  }

  /**
   * Analyze shared component usage across routes
   */
  analyzeComponentSharing(): {
    mostShared: Array<{ name: string; routes: string[]; count: number }>;
    routeOverlap: Record<string, string[]>;
    optimizationOpportunities: string[];
  } {
    // Find most shared components
    const componentUsage = Object.entries(sharedComponents).map(
      ([name, config]) => ({
        name,
        routes: config.usedInRoutes,
        count: config.usedInRoutes.length,
      })
    );

    const mostShared = componentUsage
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    // Calculate route overlap
    const routeOverlap: Record<string, string[]> = {};
    const routes = Object.keys(routeComponentUsage);

    routes.forEach((route1) => {
      routeOverlap[route1] = [];
      routes.forEach((route2) => {
        if (route1 !== route2) {
          const components1 = new Set(
            routeComponentUsage[route1 as keyof typeof routeComponentUsage]
          );
          const components2 = new Set(
            routeComponentUsage[route2 as keyof typeof routeComponentUsage]
          );
          const overlap = Array.from(components1).filter((c) =>
            components2.has(c)
          );

          if (overlap.length > 0) {
            routeOverlap[route1].push(`${route2} (${overlap.length} shared)`);
          }
        }
      });
    });

    // Identify optimization opportunities
    const optimizationOpportunities: string[] = [];

    // Large components used in multiple routes
    const largeSharedComponents = componentUsage.filter(
      (comp) => comp.count >= 3 && sharedComponents[comp.name].size === "large"
    );

    if (largeSharedComponents.length > 0) {
      optimizationOpportunities.push(
        `Consider further splitting these large shared components: ${largeSharedComponents
          .map((c) => c.name)
          .join(", ")}`
      );
    }

    // Components with low usage
    const lowUsageComponents = componentUsage.filter(
      (comp) => comp.count === 1
    );
    if (lowUsageComponents.length > 0) {
      optimizationOpportunities.push(
        `Consider inlining these single-use components: ${lowUsageComponents
          .map((c) => c.name)
          .join(", ")}`
      );
    }

    return {
      mostShared,
      routeOverlap,
      optimizationOpportunities,
    };
  }

  /**
   * Get cached component if available
   */
  getCachedComponent(name: string): ComponentType<any> | null {
    return this.componentCache.get(name) || null;
  }

  /**
   * Check if component is preloaded
   */
  isPreloaded(name: string): boolean {
    return this.preloadedComponents.has(name);
  }

  /**
   * Generate shared component bundle configuration for webpack
   */
  generateWebpackConfig(): Record<string, any> {
    const criticalComponents = Object.entries(sharedComponents)
      .filter(([_, config]) => config.priority === "critical")
      .map(([name]) => name);

    const highPriorityComponents = Object.entries(sharedComponents)
      .filter(([_, config]) => config.priority === "high")
      .map(([name]) => name);

    return {
      cacheGroups: {
        "shared-critical": {
          test: new RegExp(`[\\/](${criticalComponents.join("|")})[\\/]`),
          name: "shared-critical",
          chunks: "all",
          priority: 20,
          enforce: true,
        },
        "shared-high": {
          test: new RegExp(`[\\/](${highPriorityComponents.join("|")})[\\/]`),
          name: "shared-high",
          chunks: "all",
          priority: 15,
          minChunks: 2,
        },
        "shared-common": {
          test: /[\\/]components[\\/]/,
          name: "shared-common",
          chunks: "all",
          priority: 10,
          minChunks: 3,
        },
      },
    };
  }
}

// Export singleton instance
export const sharedComponentOptimizer = SharedComponentOptimizer.getInstance();
