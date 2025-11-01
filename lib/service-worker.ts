// Service Worker Registration and Management
export interface CacheStatus {
  [cacheName: string]: {
    entryCount: number;
    urls: string[];
  };
}

export interface ServiceWorkerManager {
  register(): Promise<ServiceWorkerRegistration | null>;
  unregister(): Promise<boolean>;
  update(): Promise<void>;
  clearCache(cacheName?: string): Promise<void>;
  warmCache(urls: string[]): Promise<void>;
  getCacheStatus(): Promise<CacheStatus>;
  isSupported(): boolean;
  isRegistered(): boolean;
}

class ServiceWorkerManagerImpl implements ServiceWorkerManager {
  private registration: ServiceWorkerRegistration | null = null;
  private messageChannel: MessageChannel | null = null;

  isSupported(): boolean {
    return (
      typeof window !== "undefined" &&
      "serviceWorker" in navigator &&
      "caches" in window
    );
  }

  isRegistered(): boolean {
    return this.registration !== null;
  }

  async register(): Promise<ServiceWorkerRegistration | null> {
    if (!this.isSupported()) {
      console.warn("[SW Manager] Service Worker not supported");
      return null;
    }

    try {
      // Register service worker
      this.registration = await navigator.serviceWorker.register("/sw.js", {
        scope: "/",
        updateViaCache: "none", // Always check for updates
      });

      console.log(
        "[SW Manager] Service Worker registered:",
        this.registration.scope
      );

      // Handle updates
      this.registration.addEventListener("updatefound", () => {
        const newWorker = this.registration?.installing;
        if (newWorker) {
          console.log("[SW Manager] New service worker installing...");

          newWorker.addEventListener("statechange", () => {
            if (
              newWorker.state === "installed" &&
              navigator.serviceWorker.controller
            ) {
              console.log(
                "[SW Manager] New service worker installed, update available"
              );
              this.notifyUpdateAvailable();
            }
          });
        }
      });

      // Handle controller changes
      navigator.serviceWorker.addEventListener("controllerchange", () => {
        console.log("[SW Manager] Service worker controller changed");
        window.location.reload();
      });

      // Check for existing service worker
      if (this.registration.waiting) {
        console.log("[SW Manager] Service worker waiting, update available");
        this.notifyUpdateAvailable();
      }

      return this.registration;
    } catch (error) {
      console.error("[SW Manager] Service Worker registration failed:", error);
      return null;
    }
  }

  async unregister(): Promise<boolean> {
    if (!this.registration) {
      return false;
    }

    try {
      const result = await this.registration.unregister();
      if (result) {
        this.registration = null;
        console.log("[SW Manager] Service Worker unregistered");
      }
      return result;
    } catch (error) {
      console.error(
        "[SW Manager] Service Worker unregistration failed:",
        error
      );
      return false;
    }
  }

  async update(): Promise<void> {
    if (!this.registration) {
      throw new Error("Service Worker not registered");
    }

    try {
      await this.registration.update();
      console.log("[SW Manager] Service Worker update check completed");
    } catch (error) {
      console.error("[SW Manager] Service Worker update failed:", error);
      throw error;
    }
  }

  async clearCache(cacheName?: string): Promise<void> {
    if (!this.isSupported()) {
      throw new Error("Service Worker not supported");
    }

    try {
      if (cacheName) {
        await caches.delete(cacheName);
        console.log(`[SW Manager] Cleared cache: ${cacheName}`);
      } else {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map((name) => caches.delete(name)));
        console.log("[SW Manager] Cleared all caches");
      }

      // Also notify service worker (graceful fallback if not available)
      const result = await this.sendMessage({
        type: "CLEAR_CACHE",
        payload: { cacheName },
      });
      if (!result.success) {
        console.warn(
          "[SW Manager] Could not notify service worker of cache clear:",
          result.reason
        );
      }
    } catch (error) {
      console.error("[SW Manager] Cache clearing failed:", error);
      throw error;
    }
  }

  async warmCache(urls: string[]): Promise<void> {
    if (!urls.length) {
      return;
    }

    // Check if service worker is ready before attempting to warm cache
    if (!navigator.serviceWorker.controller) {
      // Service worker not ready yet - this is expected during initial load
      // Don't log warnings for expected behavior
      return;
    }

    try {
      const result = await this.sendMessage({
        type: "WARM_CACHE",
        payload: { urls },
      });
      if (result.success) {
        console.log(`[SW Manager] Warmed cache for ${urls.length} URLs`);
      } else {
        // Only warn if controller exists (otherwise it's expected)
        if (navigator.serviceWorker.controller) {
          console.warn(`[SW Manager] Cache warming failed: ${result.reason}`);
        }
      }
    } catch (error) {
      // Only log error if controller exists
      if (navigator.serviceWorker.controller) {
        console.error("[SW Manager] Cache warming failed:", error);
      }
    }
  }

  async getCacheStatus(): Promise<CacheStatus> {
    try {
      const response = await this.sendMessage({ type: "GET_CACHE_STATUS" });
      if (response.success) {
        return response.payload || {};
      } else {
        // Only warn if controller exists (otherwise it's expected)
        if (navigator.serviceWorker.controller) {
          console.warn(
            "[SW Manager] Failed to get cache status:",
            response.reason
          );
        }
        return {};
      }
    } catch (error) {
      // Only log error if controller exists
      if (navigator.serviceWorker.controller) {
        console.error("[SW Manager] Failed to get cache status:", error);
      }
      return {};
    }
  }

  private async sendMessage(message: any): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!navigator.serviceWorker.controller) {
        // Gracefully handle missing service worker (expected during initial load)
        // Don't log warnings for expected behavior
        resolve({ success: false, reason: "No service worker controller" });
        return;
      }

      const messageChannel = new MessageChannel();
      let timeoutId: number | undefined;

      messageChannel.port1.onmessage = (event) => {
        if (timeoutId) clearTimeout(timeoutId);
        resolve(event.data);
      };

      messageChannel.port1.addEventListener("messageerror", (error: Event) => {
        if (timeoutId) clearTimeout(timeoutId);
        console.warn("[SW Manager] Message channel error:", error);
        resolve({ success: false, reason: "Message channel error" });
      });

      try {
        navigator.serviceWorker.controller.postMessage(message, [
          messageChannel.port2,
        ]);

        // Timeout after 5 seconds
        timeoutId = setTimeout(() => {
          console.warn("[SW Manager] Service worker message timeout");
          resolve({ success: false, reason: "Service worker message timeout" });
        }, 5000) as unknown as number;
      } catch (error) {
        if (timeoutId) clearTimeout(timeoutId);
        console.warn(
          "[SW Manager] Failed to send message to service worker:",
          error
        );
        resolve({ success: false, reason: `Failed to send message: ${error}` });
      }
    });
  }

  private notifyUpdateAvailable(): void {
    // Dispatch custom event for update notification
    const event = new CustomEvent("sw-update-available", {
      detail: { registration: this.registration },
    });
    window.dispatchEvent(event);
  }

  async skipWaiting(): Promise<void> {
    if (this.registration?.waiting) {
      const result = await this.sendMessage({ type: "SKIP_WAITING" });
      if (!result.success) {
        console.warn("[SW Manager] Could not skip waiting:", result.reason);
      }
    }
  }
}

// Singleton instance
const serviceWorkerManager = new ServiceWorkerManagerImpl();

export default serviceWorkerManager;

// Utility functions for cache warming
export const getCriticalResources = (): string[] => [
  "/",
  "/dashboard",
  "/_next/static/css/app/layout.css",
  "/_next/static/chunks/main.js",
  "/_next/static/chunks/webpack.js",
];

export const getRouteResources = (route: string): string[] => {
  const baseResources = [
    `/_next/static/chunks/pages${route}.js`,
    `/_next/static/css/pages${route}.css`,
  ];

  // Route-specific resources
  switch (route) {
    case "/dashboard":
      return [
        ...baseResources,
        "/_next/static/chunks/dashboard.js",
        "/_next/static/chunks/shared-common.js",
      ];
    case "/research":
      return [
        ...baseResources,
        "/_next/static/chunks/research.js",
        "/_next/static/chunks/charts.js",
      ];
    case "/analytics":
      return [
        ...baseResources,
        "/_next/static/chunks/analytics.js",
        "/_next/static/chunks/charts.js",
      ];
    case "/monitoring":
      return [...baseResources, "/_next/static/chunks/monitoring.js"];
    default:
      return baseResources;
  }
};

// Cache warming strategies
export const warmCacheForUser = async (userBehavior: {
  frequentRoutes: string[];
  recentActions: string[];
}): Promise<void> => {
  const { frequentRoutes, recentActions } = userBehavior;

  // Warm cache for frequently visited routes
  const routeResources = frequentRoutes.flatMap((route) =>
    getRouteResources(route)
  );

  // Add resources based on recent actions
  const actionResources: string[] = [];
  if (recentActions.includes("export")) {
    actionResources.push("/_next/static/chunks/export-modal.js");
  }
  if (recentActions.includes("collaboration")) {
    actionResources.push("/_next/static/chunks/collaboration.js");
  }

  const allResources = Array.from(
    new Set([...routeResources, ...actionResources])
  );

  if (allResources.length > 0) {
    await serviceWorkerManager.warmCache(allResources);
  }
};

// Performance monitoring
export const measureCachePerformance = (): Promise<{
  cacheHitRate: number;
  averageLoadTime: number;
  offlineCapability: boolean;
}> => {
  return new Promise((resolve) => {
    // This would integrate with performance monitoring
    // For now, return mock data
    resolve({
      cacheHitRate: 0.85,
      averageLoadTime: 150,
      offlineCapability: true,
    });
  });
};
