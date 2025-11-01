// Cache Warming and Preloading Strategies
import { warmAPICache, getCriticalEndpoints } from "./api-cache";
import serviceWorkerManager, {
  getCriticalResources,
  getRouteResources,
} from "./service-worker";

export interface UserBehaviorPattern {
  frequentRoutes: string[];
  recentActions: string[];
  timeOfDay: "morning" | "afternoon" | "evening";
  dayOfWeek: "weekday" | "weekend";
  sessionDuration: number; // in minutes
  lastVisit: Date;
}

export interface CacheWarmingStrategy {
  name: string;
  priority: "high" | "medium" | "low";
  trigger: "immediate" | "idle" | "scheduled" | "user-action";
  resources: string[];
  condition?: () => boolean;
}

export interface PreloadingConfig {
  enableIntelligentPreloading: boolean;
  enableRoutePreloading: boolean;
  enableResourcePreloading: boolean;
  maxConcurrentPreloads: number;
  preloadThreshold: number; // Probability threshold for preloading
}

class CacheWarmingManager {
  private strategies: CacheWarmingStrategy[] = [];
  private isWarming = false;
  private warmingQueue: CacheWarmingStrategy[] = [];
  private config: PreloadingConfig;
  private userBehavior: UserBehaviorPattern | null = null;

  constructor(
    config: PreloadingConfig = {
      enableIntelligentPreloading: true,
      enableRoutePreloading: true,
      enableResourcePreloading: true,
      maxConcurrentPreloads: 3,
      preloadThreshold: 0.7,
    }
  ) {
    this.config = config;
    this.initializeStrategies();
    this.loadUserBehavior();
  }

  private initializeStrategies(): void {
    this.strategies = [
      // Critical resources - highest priority
      {
        name: "critical-resources",
        priority: "high",
        trigger: "immediate",
        resources: getCriticalResources(),
        condition: () => true,
      },

      // API endpoints - high priority
      {
        name: "critical-api-endpoints",
        priority: "high",
        trigger: "immediate",
        resources: getCriticalEndpoints().map((e) => e.url),
        condition: () => true,
      },

      // Dashboard resources - medium priority
      {
        name: "dashboard-resources",
        priority: "medium",
        trigger: "idle",
        resources: getRouteResources("/dashboard"),
        condition: () => this.isLikelyToVisitDashboard(),
      },

      // Research resources - medium priority
      {
        name: "research-resources",
        priority: "medium",
        trigger: "idle",
        resources: getRouteResources("/research"),
        condition: () => this.isLikelyToVisitResearch(),
      },

      // Analytics resources - low priority
      {
        name: "analytics-resources",
        priority: "low",
        trigger: "idle",
        resources: getRouteResources("/analytics"),
        condition: () => this.isLikelyToVisitAnalytics(),
      },

      // Monitoring resources - low priority
      {
        name: "monitoring-resources",
        priority: "low",
        trigger: "idle",
        resources: getRouteResources("/monitoring"),
        condition: () => this.isLikelyToVisitMonitoring(),
      },
    ];
  }

  private loadUserBehavior(): void {
    if (typeof window === "undefined") {
      return; // Skip in SSR environment
    }
    try {
      const stored = localStorage.getItem("userBehaviorPattern");
      if (stored) {
        this.userBehavior = JSON.parse(stored);
      }
    } catch (error) {
      console.warn("[Cache Warming] Failed to load user behavior:", error);
    }
  }

  private saveUserBehavior(): void {
    if (typeof window === "undefined" || !this.userBehavior) {
      return; // Skip in SSR environment
    }
    try {
      localStorage.setItem(
        "userBehaviorPattern",
        JSON.stringify(this.userBehavior)
      );
    } catch (error) {
      console.warn("[Cache Warming] Failed to save user behavior:", error);
    }
  }

  updateUserBehavior(pattern: Partial<UserBehaviorPattern>): void {
    this.userBehavior = {
      ...this.userBehavior,
      ...pattern,
      lastVisit: new Date(),
    } as UserBehaviorPattern;

    this.saveUserBehavior();

    // Re-evaluate strategies based on new behavior
    this.scheduleIntelligentWarming();
  }

  async warmCache(strategyName?: string): Promise<void> {
    if (this.isWarming) {
      // Suppress repeated log messages for better UX
      return;
    }

    this.isWarming = true;

    try {
      const strategiesToExecute = strategyName
        ? this.strategies.filter((s) => s.name === strategyName)
        : this.strategies.filter((s) => !s.condition || s.condition());

      // Sort by priority
      strategiesToExecute.sort((a, b) => {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      });

      console.log(
        `[Cache Warming] Executing ${strategiesToExecute.length} strategies`
      );

      for (const strategy of strategiesToExecute) {
        await this.executeStrategy(strategy);
      }

      console.log("[Cache Warming] Cache warming completed");
    } catch (error) {
      console.error("[Cache Warming] Cache warming failed:", error);
    } finally {
      this.isWarming = false;
    }
  }

  private async executeStrategy(strategy: CacheWarmingStrategy): Promise<void> {
    // Only log in development or when debugging
    if (process.env.NODE_ENV === "development") {
      console.log(`[Cache Warming] Executing strategy: ${strategy.name}`);
    }

    try {
      // Check if service worker is ready before attempting to warm cache
      if (!serviceWorkerManager.isRegistered() || !navigator.serviceWorker?.controller) {
        // Service worker not ready yet - skip warming for now
        return;
      }

      // Warm service worker cache
      if (
        strategy.resources.some(
          (r) => r.startsWith("/_next/") || r.startsWith("/")
        )
      ) {
        const swResources = strategy.resources.filter(
          (r) => r.startsWith("/_next/") || r.startsWith("/")
        );
        if (swResources.length > 0) {
          await serviceWorkerManager.warmCache(swResources);
        }
      }

      // Warm API cache
      const apiEndpoints = strategy.resources
        .filter((r) => r.startsWith("/api/"))
        .map((url) => ({ url }));

      if (apiEndpoints.length > 0) {
        await warmAPICache(apiEndpoints);
      }

      console.log(`[Cache Warming] Strategy ${strategy.name} completed`);
    } catch (error) {
      console.error(`[Cache Warming] Strategy ${strategy.name} failed:`, error);
    }
  }

  scheduleIntelligentWarming(): void {
    if (!this.config.enableIntelligentPreloading) {
      return;
    }

    // Schedule warming based on user behavior
    const delay = this.calculateOptimalWarmingDelay();

    setTimeout(() => {
      this.warmCache();
    }, delay);
  }

  private calculateOptimalWarmingDelay(): number {
    if (!this.userBehavior) {
      return 2000; // Default 2 seconds
    }

    const now = new Date();
    const hour = now.getHours();

    // Warm cache more aggressively during business hours
    if (hour >= 9 && hour <= 17) {
      return 1000; // 1 second
    }

    // Less aggressive during off-hours
    return 5000; // 5 seconds
  }

  // Predictive methods based on user behavior
  private isLikelyToVisitDashboard(): boolean {
    if (!this.userBehavior) return true; // Default to true for new users

    return (
      this.userBehavior.frequentRoutes.includes("/dashboard") ||
      this.userBehavior.frequentRoutes.includes("/")
    );
  }

  private isLikelyToVisitResearch(): boolean {
    if (!this.userBehavior) return false;

    return (
      this.userBehavior.frequentRoutes.includes("/research") ||
      this.userBehavior.recentActions.includes("research")
    );
  }

  private isLikelyToVisitAnalytics(): boolean {
    if (!this.userBehavior) return false;

    return (
      this.userBehavior.frequentRoutes.includes("/analytics") ||
      this.userBehavior.recentActions.includes("analytics")
    );
  }

  private isLikelyToVisitMonitoring(): boolean {
    if (!this.userBehavior) return false;

    return (
      this.userBehavior.frequentRoutes.includes("/monitoring") ||
      this.userBehavior.recentActions.includes("monitoring")
    );
  }

  // Route-based preloading
  async preloadRoute(route: string): Promise<void> {
    if (!this.config.enableRoutePreloading) {
      return;
    }

    try {
      const resources = getRouteResources(route);
      await serviceWorkerManager.warmCache(resources);

      console.log(`[Cache Warming] Preloaded route: ${route}`);
    } catch (error) {
      console.error(`[Cache Warming] Failed to preload route ${route}:`, error);
    }
  }

  // Resource-based preloading
  async preloadResources(resources: string[]): Promise<void> {
    if (!this.config.enableResourcePreloading) {
      return;
    }

    try {
      // Limit concurrent preloads
      const chunks = this.chunkArray(
        resources,
        this.config.maxConcurrentPreloads
      );

      for (const chunk of chunks) {
        await Promise.all(
          chunk.map((resource) => this.preloadSingleResource(resource))
        );
      }

      console.log(`[Cache Warming] Preloaded ${resources.length} resources`);
    } catch (error) {
      console.error("[Cache Warming] Resource preloading failed:", error);
    }
  }

  private async preloadSingleResource(resource: string): Promise<void> {
    try {
      if (resource.startsWith("/api/")) {
        // Preload API endpoint
        await warmAPICache([{ url: resource }]);
      } else {
        // Preload static resource
        await serviceWorkerManager.warmCache([resource]);
      }
    } catch (error) {
      console.warn(
        `[Cache Warming] Failed to preload resource ${resource}:`,
        error
      );
    }
  }

  private chunkArray<T>(array: T[], size: number): T[][] {
    const chunks: T[][] = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }

  // Memory management
  optimizeMemoryUsage(): void {
    // Clear low-priority cache entries if memory usage is high
    if (this.isMemoryUsageHigh()) {
      console.log("[Cache Warming] High memory usage detected, optimizing...");

      // Clear analytics and monitoring caches (lowest priority)
      serviceWorkerManager.clearCache().catch((error) => {
        console.error(
          "[Cache Warming] Failed to clear cache for memory optimization:",
          error
        );
      });
    }
  }

  private isMemoryUsageHigh(): boolean {
    // Simple heuristic - in a real implementation, you'd use Performance API
    if ("memory" in performance) {
      const memory = (performance as any).memory;
      return memory.usedJSHeapSize / memory.jsHeapSizeLimit > 0.8;
    }
    return false;
  }

  getWarmingStatus(): {
    isWarming: boolean;
    queueLength: number;
    strategiesCount: number;
    userBehavior: UserBehaviorPattern | null;
  } {
    return {
      isWarming: this.isWarming,
      queueLength: this.warmingQueue.length,
      strategiesCount: this.strategies.length,
      userBehavior: this.userBehavior,
    };
  }
}

// Singleton instance
const cacheWarmingManager = new CacheWarmingManager();

// Export utilities
export const warmCache = (strategyName?: string) =>
  cacheWarmingManager.warmCache(strategyName);
export const preloadRoute = (route: string) =>
  cacheWarmingManager.preloadRoute(route);
export const preloadResources = (resources: string[]) =>
  cacheWarmingManager.preloadResources(resources);
export const updateUserBehavior = (pattern: Partial<UserBehaviorPattern>) =>
  cacheWarmingManager.updateUserBehavior(pattern);
export const scheduleIntelligentWarming = () =>
  cacheWarmingManager.scheduleIntelligentWarming();
export const optimizeMemoryUsage = () =>
  cacheWarmingManager.optimizeMemoryUsage();
export const getWarmingStatus = () => cacheWarmingManager.getWarmingStatus();

// Auto-start intelligent warming on module load
if (typeof window !== "undefined") {
  // Wait for initial page load and service worker to be ready
  window.addEventListener("load", () => {
    // Wait longer to ensure service worker is ready
    setTimeout(() => {
      // Only schedule warming if service worker is registered and has controller
      if (
        serviceWorkerManager.isRegistered() &&
        navigator.serviceWorker?.controller
      ) {
        scheduleIntelligentWarming();
      } else {
        // If service worker isn't ready, wait a bit more and try once
        setTimeout(() => {
          if (
            serviceWorkerManager.isRegistered() &&
            navigator.serviceWorker?.controller
          ) {
            scheduleIntelligentWarming();
          }
        }, 2000);
      }
    }, 3000); // Wait 3 seconds after page load
  });

  // Monitor memory usage
  setInterval(() => {
    optimizeMemoryUsage();
  }, 60000); // Check every minute
}

export default cacheWarmingManager;
