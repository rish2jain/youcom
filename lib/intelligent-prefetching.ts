/**
 * Intelligent route prefetching system with predictive analytics
 * Implements advanced prefetching strategies based on user behavior patterns
 */

import { getRouteKey, navigationPatterns, preloadRoute } from "./route-config";
import { sharedComponentOptimizer } from "./shared-components";

interface UserBehaviorData {
  visitedRoutes: string[];
  routeTransitions: Record<string, Record<string, number>>;
  timeSpentOnRoutes: Record<string, number>;
  sessionStartTime: number;
  lastActivity: number;
}

interface PrefetchStrategy {
  name: string;
  priority: number;
  execute: (
    currentRoute: string,
    behaviorData: UserBehaviorData
  ) => Promise<string[]>;
}

/**
 * Intelligent prefetching manager with machine learning-like behavior prediction
 */
export class IntelligentPrefetcher {
  private static instance: IntelligentPrefetcher;
  private behaviorData: UserBehaviorData;
  private prefetchedRoutes = new Set<string>();
  private prefetchQueue: Array<{
    route: string;
    priority: number;
    timestamp: number;
  }> = [];
  private isProcessingQueue = false;
  private strategies: PrefetchStrategy[] = [];

  constructor() {
    this.behaviorData = {
      visitedRoutes: [],
      routeTransitions: {},
      timeSpentOnRoutes: {},
      sessionStartTime: Date.now(),
      lastActivity: Date.now(),
    };

    this.initializeStrategies();
    this.loadBehaviorData();
  }

  static getInstance(): IntelligentPrefetcher {
    if (!IntelligentPrefetcher.instance) {
      IntelligentPrefetcher.instance = new IntelligentPrefetcher();
    }
    return IntelligentPrefetcher.instance;
  }

  /**
   * Initialize prefetching strategies
   */
  private initializeStrategies(): void {
    this.strategies = [
      {
        name: "navigation-patterns",
        priority: 10,
        execute: this.navigationPatternStrategy.bind(this),
      },
      {
        name: "user-history",
        priority: 8,
        execute: this.userHistoryStrategy.bind(this),
      },
      {
        name: "time-based",
        priority: 6,
        execute: this.timeBasedStrategy.bind(this),
      },
      {
        name: "session-context",
        priority: 7,
        execute: this.sessionContextStrategy.bind(this),
      },
      {
        name: "predictive-ml",
        priority: 9,
        execute: this.predictiveMLStrategy.bind(this),
      },
    ];

    // Sort strategies by priority (highest first)
    this.strategies.sort((a, b) => b.priority - a.priority);
  }

  /**
   * Track route visit for behavior analysis
   */
  trackRouteVisit(route: string, previousRoute?: string): void {
    const now = Date.now();

    // Update visited routes
    if (!this.behaviorData.visitedRoutes.includes(route)) {
      this.behaviorData.visitedRoutes.push(route);
    }

    // Track route transitions
    if (previousRoute) {
      if (!this.behaviorData.routeTransitions[previousRoute]) {
        this.behaviorData.routeTransitions[previousRoute] = {};
      }
      this.behaviorData.routeTransitions[previousRoute][route] =
        (this.behaviorData.routeTransitions[previousRoute][route] || 0) + 1;

      // Update time spent on previous route
      const timeSpent = now - this.behaviorData.lastActivity;
      this.behaviorData.timeSpentOnRoutes[previousRoute] =
        (this.behaviorData.timeSpentOnRoutes[previousRoute] || 0) + timeSpent;
    }

    this.behaviorData.lastActivity = now;
    this.saveBehaviorData();

    // Trigger intelligent prefetching
    this.executePrefetchingStrategies(route);
  }

  /**
   * Execute all prefetching strategies
   */
  private async executePrefetchingStrategies(
    currentRoute: string
  ): Promise<void> {
    const allPredictions: Array<{
      route: string;
      priority: number;
      strategy: string;
    }> = [];

    // Execute each strategy
    for (const strategy of this.strategies) {
      try {
        const predictions = await strategy.execute(
          currentRoute,
          this.behaviorData
        );
        predictions.forEach((route) => {
          allPredictions.push({
            route,
            priority: strategy.priority,
            strategy: strategy.name,
          });
        });
      } catch (error) {
        console.warn(`Prefetching strategy ${strategy.name} failed:`, error);
      }
    }

    // Aggregate and prioritize predictions
    const routePriorities = new Map<string, number>();
    allPredictions.forEach(({ route, priority }) => {
      const currentPriority = routePriorities.get(route) || 0;
      routePriorities.set(route, Math.max(currentPriority, priority));
    });

    // Add to prefetch queue
    Array.from(routePriorities.entries())
      .filter(
        ([route]) => !this.prefetchedRoutes.has(route) && route !== currentRoute
      )
      .forEach(([route, priority]) => {
        this.addToPrefetchQueue(route, priority);
      });

    // Process queue
    this.processPrefetchQueue();
  }

  /**
   * Navigation pattern-based strategy
   */
  private async navigationPatternStrategy(
    currentRoute: string
  ): Promise<string[]> {
    const patterns =
      navigationPatterns[currentRoute as keyof typeof navigationPatterns] || [];
    return patterns;
  }

  /**
   * User history-based strategy
   */
  private async userHistoryStrategy(currentRoute: string): Promise<string[]> {
    const transitions = this.behaviorData.routeTransitions[currentRoute] || {};

    // Sort by frequency and return top 3
    return Object.entries(transitions)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([route]) => route);
  }

  /**
   * Time-based strategy (prefetch based on time spent on current route)
   */
  private async timeBasedStrategy(currentRoute: string): Promise<string[]> {
    const timeOnCurrentRoute = Date.now() - this.behaviorData.lastActivity;
    const avgTimeOnRoute =
      this.behaviorData.timeSpentOnRoutes[currentRoute] || 30000; // 30s default

    // If user has been on route for 70% of average time, prefetch likely next routes
    if (timeOnCurrentRoute > avgTimeOnRoute * 0.7) {
      return this.userHistoryStrategy(currentRoute);
    }

    return [];
  }

  /**
   * Session context strategy
   */
  private async sessionContextStrategy(
    currentRoute: string
  ): Promise<string[]> {
    const sessionDuration = Date.now() - this.behaviorData.sessionStartTime;
    const visitedInSession = this.behaviorData.visitedRoutes;

    // Helper function to ensure leading slash
    const ensureLeadingSlash = (route: string) =>
      route.startsWith("/") ? route : `/${route}`;

    // Early session: suggest common starting points
    if (sessionDuration < 300000) {
      // 5 minutes
      return ["dashboard", "research"].map(ensureLeadingSlash);
    }

    // Mid session: suggest unvisited important routes
    if (sessionDuration < 900000) {
      // 15 minutes
      const importantRoutes = [
        "dashboard",
        "research",
        "analytics",
        "monitoring",
      ];
      return importantRoutes
        .filter((route) => !visitedInSession.includes(route))
        .map(ensureLeadingSlash);
    }

    // Late session: suggest completion routes
    return ["settings", "integrations"].map(ensureLeadingSlash);
  }

  /**
   * Predictive ML-like strategy using simple heuristics
   */
  private async predictiveMLStrategy(currentRoute: string): Promise<string[]> {
    const predictions: string[] = [];

    // Analyze user patterns
    const totalVisits = this.behaviorData.visitedRoutes.length;
    const uniqueRoutes = new Set(this.behaviorData.visitedRoutes).size;

    // Helper function to ensure leading slash
    const ensureLeadingSlash = (route: string) =>
      route.startsWith("/") ? route : `/${route}`;

    // If user explores many routes, they're likely to continue exploring
    if (uniqueRoutes / totalVisits > 0.7) {
      const allRoutes = [
        "dashboard",
        "research",
        "analytics",
        "monitoring",
        "integrations",
        "settings",
      ];
      const unvisited = allRoutes.filter(
        (route) => !this.behaviorData.visitedRoutes.includes(route)
      );
      predictions.push(...unvisited.slice(0, 2).map(ensureLeadingSlash));
    }

    // If user focuses on specific routes, predict related ones
    const routeFrequency = this.behaviorData.visitedRoutes.reduce(
      (acc, route) => {
        acc[route] = (acc[route] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );

    const mostVisited = Object.entries(routeFrequency).sort(
      ([, a], [, b]) => b - a
    )[0];

    if (mostVisited) {
      const relatedRoutes =
        navigationPatterns[mostVisited[0] as keyof typeof navigationPatterns] ||
        [];
      predictions.push(...relatedRoutes.slice(0, 2).map(ensureLeadingSlash));
    }

    return Array.from(new Set(predictions)); // Remove duplicates
  }

  /**
   * Add route to prefetch queue with priority
   */
  private addToPrefetchQueue(route: string, priority: number): void {
    // Remove existing entry for this route
    this.prefetchQueue = this.prefetchQueue.filter(
      (item) => item.route !== route
    );

    // Add new entry
    this.prefetchQueue.push({
      route,
      priority,
      timestamp: Date.now(),
    });

    // Sort by priority (highest first)
    this.prefetchQueue.sort((a, b) => b.priority - a.priority);
  }

  /**
   * Process prefetch queue
   */
  private async processPrefetchQueue(): Promise<void> {
    if (this.isProcessingQueue || this.prefetchQueue.length === 0) {
      return;
    }

    this.isProcessingQueue = true;

    try {
      // Process up to 3 routes at a time to avoid overwhelming the network
      const batch = this.prefetchQueue.splice(0, 3);

      const prefetchPromises = batch.map(async ({ route, priority }) => {
        try {
          // Prefetch route
          await preloadRoute(route);

          // Prefetch shared components for route
          await sharedComponentOptimizer.preloadRouteComponents(route);

          this.prefetchedRoutes.add(route);

          console.log(`Prefetched route ${route} with priority ${priority}`);
        } catch (error) {
          console.warn(`Failed to prefetch route ${route}:`, error);
        }
      });

      await Promise.all(prefetchPromises);

      // Continue processing if there are more items
      if (this.prefetchQueue.length > 0) {
        setTimeout(() => this.processPrefetchQueue(), 1000); // 1 second delay
      }
    } finally {
      this.isProcessingQueue = false;
    }
  }

  /**
   * Prefetch route on hover with intelligent delay
   */
  prefetchOnHover(route: string, hoverDuration: number = 0): void {
    if (this.prefetchedRoutes.has(route)) {
      return;
    }

    // Intelligent delay based on hover duration and route priority
    const baseDelay = 300; // 300ms base delay
    const priorityMultiplier = this.calculateRoutePriority(route);
    const delay = Math.max(
      100,
      baseDelay - hoverDuration * 10 - priorityMultiplier * 50
    );

    setTimeout(() => {
      this.addToPrefetchQueue(route, 5 + priorityMultiplier);
      this.processPrefetchQueue();
    }, delay);
  }

  /**
   * Calculate route priority based on user behavior
   */
  private calculateRoutePriority(route: string): number {
    let priority = 0;

    // Frequently visited routes get higher priority
    const visitCount = this.behaviorData.visitedRoutes.filter(
      (r) => r === route
    ).length;
    priority += Math.min(visitCount * 2, 10);

    // Routes with high transition probability get higher priority
    const currentRoute =
      this.behaviorData.visitedRoutes[
        this.behaviorData.visitedRoutes.length - 1
      ];
    if (currentRoute) {
      const transitions =
        this.behaviorData.routeTransitions[currentRoute] || {};
      const transitionCount = transitions[route] || 0;
      priority += Math.min(transitionCount * 3, 15);
    }

    return priority;
  }

  /**
   * Get prefetching analytics
   */
  getAnalytics(): {
    prefetchedRoutes: string[];
    queueLength: number;
    behaviorData: UserBehaviorData;
    hitRate: number;
  } {
    const totalPrefetched = this.prefetchedRoutes.size;
    const actuallyVisited = Array.from(this.prefetchedRoutes).filter((route) =>
      this.behaviorData.visitedRoutes.includes(route)
    ).length;

    return {
      prefetchedRoutes: Array.from(this.prefetchedRoutes),
      queueLength: this.prefetchQueue.length,
      behaviorData: this.behaviorData,
      hitRate: totalPrefetched > 0 ? actuallyVisited / totalPrefetched : 0,
    };
  }

  /**
   * Load behavior data from localStorage
   */
  private loadBehaviorData(): void {
    if (typeof window === "undefined") return;

    try {
      const stored = localStorage.getItem("route-prefetch-behavior");
      if (stored) {
        const data = JSON.parse(stored);

        // Validate the parsed object structure
        if (
          data &&
          typeof data === "object" &&
          typeof data.sessionStartTime === "number" &&
          Array.isArray(data.visitedRoutes) &&
          typeof data.routeTransitions === "object" &&
          typeof data.timeSpentOnRoutes === "object" &&
          typeof data.lastActivity === "number"
        ) {
          // Only load data from the last 7 days
          if (Date.now() - data.sessionStartTime < 7 * 24 * 60 * 60 * 1000) {
            this.behaviorData = { ...this.behaviorData, ...data };
          }
        } else {
          console.warn("Invalid behavior data structure, skipping load");
        }
      }
    } catch (error) {
      console.warn("Failed to load behavior data:", error);
    }
  }

  /**
   * Save behavior data to localStorage
   */
  private saveBehaviorData(): void {
    if (typeof window === "undefined") return;

    try {
      localStorage.setItem(
        "route-prefetch-behavior",
        JSON.stringify(this.behaviorData)
      );
    } catch (error) {
      console.warn("Failed to save behavior data:", error);
    }
  }

  /**
   * Reset behavior data (for testing or privacy)
   */
  resetBehaviorData(): void {
    this.behaviorData = {
      visitedRoutes: [],
      routeTransitions: {},
      timeSpentOnRoutes: {},
      sessionStartTime: Date.now(),
      lastActivity: Date.now(),
    };

    if (typeof window !== "undefined") {
      localStorage.removeItem("route-prefetch-behavior");
    }
  }
}

// Export singleton instance
export const intelligentPrefetcher = IntelligentPrefetcher.getInstance();
