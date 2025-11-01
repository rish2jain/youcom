/**
 * Intelligent Preloading Strategies
 * Implements various preloading patterns based on user behavior and priorities
 */

import { ComponentType } from "react";

export interface PreloadConfig {
  priority: "high" | "medium" | "low";
  delay?: number;
  condition?: () => boolean;
  trigger?: "immediate" | "hover" | "viewport" | "idle" | "user-behavior";
  dependencies?: string[];
}

export interface UserBehaviorPattern {
  route: string;
  component: string;
  frequency: number;
  lastAccessed: number;
  averageTimeSpent: number;
}

export interface PreloadMetrics {
  componentName: string;
  preloadTime: number;
  actualLoadTime: number;
  wasCacheHit: boolean;
  userBenefit: number; // Time saved in ms
}

/**
 * User Behavior Tracker for intelligent preloading
 */
class UserBehaviorTracker {
  private patterns = new Map<string, UserBehaviorPattern>();
  private currentRoute = "";
  private routeStartTime = 0;

  constructor() {
    if (typeof window !== "undefined") {
      this.loadPatterns();
      this.trackRouteChanges();
    }
  }

  trackRouteAccess(route: string, component?: string): void {
    const now = Date.now();

    // Track time spent on previous route
    if (this.currentRoute && this.routeStartTime) {
      const timeSpent = now - this.routeStartTime;
      this.updatePattern(this.currentRoute, timeSpent);
    }

    // Set new route
    this.currentRoute = route;
    this.routeStartTime = now;

    if (component) {
      this.updatePattern(`${route}:${component}`, 0);
    }
  }

  private updatePattern(key: string, timeSpent: number): void {
    const existing = this.patterns.get(key);

    if (existing) {
      existing.frequency += 1;
      existing.lastAccessed = Date.now();
      existing.averageTimeSpent = (existing.averageTimeSpent + timeSpent) / 2;
    } else {
      this.patterns.set(key, {
        route: key.split(":")[0],
        component: key.split(":")[1] || "",
        frequency: 1,
        lastAccessed: Date.now(),
        averageTimeSpent: timeSpent,
      });
    }

    this.savePatterns();
  }

  getPredictedComponents(currentRoute: string, limit = 3): string[] {
    const now = Date.now();
    const oneWeek = 7 * 24 * 60 * 60 * 1000;

    return Array.from(this.patterns.values())
      .filter(
        (pattern) =>
          pattern.lastAccessed > now - oneWeek && // Recent access
          pattern.frequency > 1 && // Accessed more than once
          pattern.route !== currentRoute // Not current route
      )
      .sort((a, b) => {
        // Score based on frequency and recency
        const scoreA = a.frequency * (1 / (now - a.lastAccessed + 1));
        const scoreB = b.frequency * (1 / (now - b.lastAccessed + 1));
        return scoreB - scoreA;
      })
      .slice(0, limit)
      .map((pattern) => pattern.component)
      .filter(Boolean);
  }

  private loadPatterns(): void {
    try {
      const stored = localStorage.getItem("userBehaviorPatterns");
      if (stored) {
        const patterns = JSON.parse(stored);
        this.patterns = new Map(patterns);
      }
    } catch (error) {
      console.warn("Failed to load user behavior patterns:", error);
    }
  }

  private savePatterns(): void {
    try {
      const patterns = Array.from(this.patterns.entries());
      localStorage.setItem("userBehaviorPatterns", JSON.stringify(patterns));
    } catch (error) {
      console.warn("Failed to save user behavior patterns:", error);
    }
  }

  private trackRouteChanges(): void {
    // Track initial route
    this.trackRouteAccess(window.location.pathname);

    // Track route changes (for SPA navigation)
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;

    history.pushState = function (...args) {
      originalPushState.apply(history, args);
      userBehaviorTracker.trackRouteAccess(window.location.pathname);
    };

    history.replaceState = function (...args) {
      originalReplaceState.apply(history, args);
      userBehaviorTracker.trackRouteAccess(window.location.pathname);
    };

    window.addEventListener("popstate", () => {
      this.trackRouteAccess(window.location.pathname);
    });
  }
}

/**
 * Preloading Strategy Manager
 */
class PreloadingManager {
  private preloadPromises = new Map<string, Promise<any>>();
  private preloadedComponents = new Set<string>();
  private metrics: PreloadMetrics[] = [];
  private behaviorTracker = new UserBehaviorTracker();

  /**
   * Preload component immediately
   */
  async preloadImmediate(
    name: string,
    importFn: () => Promise<{ default: ComponentType<any> }>
  ): Promise<void> {
    if (this.preloadedComponents.has(name)) return;

    const startTime = performance.now();

    try {
      const promise = importFn();
      this.preloadPromises.set(name, promise);

      await promise;

      const endTime = performance.now();
      this.preloadedComponents.add(name);

      this.recordMetrics(name, endTime - startTime, 0, true, 0);
    } catch (error) {
      console.warn(`Failed to preload component ${name}:`, error);
    }
  }

  /**
   * Preload component on hover
   */
  preloadOnHover(
    element: HTMLElement,
    name: string,
    importFn: () => Promise<{ default: ComponentType<any> }>
  ): () => void {
    let preloadTriggered = false;

    const handleMouseEnter = () => {
      if (!preloadTriggered && !this.preloadedComponents.has(name)) {
        preloadTriggered = true;
        this.preloadImmediate(name, importFn);
      }
    };

    element.addEventListener("mouseenter", handleMouseEnter);

    // Return cleanup function
    return () => {
      element.removeEventListener("mouseenter", handleMouseEnter);
    };
  }

  /**
   * Preload component when it enters viewport
   */
  preloadOnViewport(
    element: HTMLElement,
    name: string,
    importFn: () => Promise<{ default: ComponentType<any> }>,
    threshold = 0.1
  ): () => void {
    if (!("IntersectionObserver" in window)) {
      // Fallback: preload immediately if IntersectionObserver not supported
      this.preloadImmediate(name, importFn);
      return () => {};
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !this.preloadedComponents.has(name)) {
            this.preloadImmediate(name, importFn);
            observer.disconnect();
          }
        });
      },
      { threshold }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }

  /**
   * Preload component during browser idle time
   */
  preloadOnIdle(
    name: string,
    importFn: () => Promise<{ default: ComponentType<any> }>,
    timeout = 5000
  ): void {
    if (this.preloadedComponents.has(name)) return;

    if ("requestIdleCallback" in window) {
      (window as any).requestIdleCallback(
        () => {
          this.preloadImmediate(name, importFn);
        },
        { timeout }
      );
    } else {
      // Fallback: use setTimeout
      setTimeout(() => {
        this.preloadImmediate(name, importFn);
      }, 100);
    }
  }

  /**
   * Preload based on user behavior patterns
   */
  preloadBasedOnBehavior(
    components: Map<string, () => Promise<{ default: ComponentType<any> }>>
  ): void {
    const currentRoute =
      typeof window !== "undefined" ? window.location.pathname : "";

    const predictedComponents =
      this.behaviorTracker.getPredictedComponents(currentRoute);

    predictedComponents.forEach((componentName) => {
      const importFn = components.get(componentName);
      if (importFn && !this.preloadedComponents.has(componentName)) {
        this.preloadOnIdle(componentName, importFn);
      }
    });
  }

  /**
   * Preload with priority management
   */
  async preloadWithPriority(
    components: Array<{
      name: string;
      importFn: () => Promise<{ default: ComponentType<any> }>;
      config: PreloadConfig;
    }>
  ): Promise<void> {
    // Sort by priority
    const sortedComponents = components.sort((a, b) => {
      const priorityOrder = { high: 3, medium: 2, low: 1 };
      return (
        priorityOrder[b.config.priority] - priorityOrder[a.config.priority]
      );
    });

    // Process high priority components first
    const highPriority = sortedComponents.filter(
      (c) => c.config.priority === "high"
    );
    await Promise.all(
      highPriority.map(({ name, importFn }) =>
        this.preloadImmediate(name, importFn)
      )
    );

    // Process medium priority with delay
    const mediumPriority = sortedComponents.filter(
      (c) => c.config.priority === "medium"
    );
    setTimeout(() => {
      mediumPriority.forEach(({ name, importFn, config }) => {
        if (!config.condition || config.condition()) {
          this.preloadOnIdle(name, importFn);
        }
      });
    }, 1000);

    // Process low priority with longer delay
    const lowPriority = sortedComponents.filter(
      (c) => c.config.priority === "low"
    );
    setTimeout(() => {
      lowPriority.forEach(({ name, importFn, config }) => {
        if (!config.condition || config.condition()) {
          this.preloadOnIdle(name, importFn, 10000);
        }
      });
    }, 3000);
  }

  /**
   * Check if component is preloaded
   */
  isPreloaded(name: string): boolean {
    return this.preloadedComponents.has(name);
  }

  /**
   * Get preload promise if exists
   */
  getPreloadPromise(name: string): Promise<any> | undefined {
    return this.preloadPromises.get(name);
  }

  /**
   * Record preload metrics
   */
  private recordMetrics(
    componentName: string,
    preloadTime: number,
    actualLoadTime: number,
    wasCacheHit: boolean,
    userBenefit: number
  ): void {
    this.metrics.push({
      componentName,
      preloadTime,
      actualLoadTime,
      wasCacheHit,
      userBenefit,
    });

    // Keep only last 100 metrics
    if (this.metrics.length > 100) {
      this.metrics = this.metrics.slice(-100);
    }
  }

  /**
   * Get preloading metrics
   */
  getMetrics(): PreloadMetrics[] {
    return [...this.metrics];
  }

  /**
   * Clear preload cache
   */
  clearCache(): void {
    this.preloadPromises.clear();
    this.preloadedComponents.clear();
  }
}

// Global instances
export const preloadingManager = new PreloadingManager();
export const userBehaviorTracker = new UserBehaviorTracker();

/**
 * React hook for component preloading
 */
export function usePreloading() {
  return {
    preloadImmediate:
      preloadingManager.preloadImmediate.bind(preloadingManager),
    preloadOnHover: preloadingManager.preloadOnHover.bind(preloadingManager),
    preloadOnViewport:
      preloadingManager.preloadOnViewport.bind(preloadingManager),
    preloadOnIdle: preloadingManager.preloadOnIdle.bind(preloadingManager),
    preloadBasedOnBehavior:
      preloadingManager.preloadBasedOnBehavior.bind(preloadingManager),
    preloadWithPriority:
      preloadingManager.preloadWithPriority.bind(preloadingManager),
    isPreloaded: preloadingManager.isPreloaded.bind(preloadingManager),
    getMetrics: preloadingManager.getMetrics.bind(preloadingManager),
    clearCache: preloadingManager.clearCache.bind(preloadingManager),
  };
}
