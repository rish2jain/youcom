"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import {
  useAutoServiceWorker,
  ServiceWorkerState,
  ServiceWorkerActions,
} from "@/lib/hooks/useServiceWorker";
import {
  useCacheWarming,
  useUserBehaviorTracking,
} from "@/lib/hooks/useCacheWarming";
import { usePathname } from "next/navigation";

interface ServiceWorkerContextType {
  isSupported: boolean;
  isRegistered: boolean;
  isUpdateAvailable: boolean;
  cacheStatus: any;
  clearCache: (cacheName?: string) => Promise<void>;
  refreshCacheStatus: () => Promise<void>;
}

const ServiceWorkerContext = createContext<ServiceWorkerContextType | null>(
  null
);

export const useServiceWorkerContext = () => {
  const context = useContext(ServiceWorkerContext);
  if (!context) {
    throw new Error(
      "useServiceWorkerContext must be used within ServiceWorkerProvider"
    );
  }
  return context;
};

interface ServiceWorkerProviderProps {
  children: React.ReactNode;
}

export const ServiceWorkerProvider: React.FC<ServiceWorkerProviderProps> = ({
  children,
}) => {
  const pathname = usePathname();
  const [userBehavior, setUserBehavior] = useState({
    frequentRoutes: ["/dashboard", "/research"],
    recentActions: ["view", "export"],
  });

  // Use cache warming hooks
  const { state: warmingState, warmCache } = useCacheWarming();
  const { trackAction } = useUserBehaviorTracking();

  // Track user behavior for intelligent caching
  useEffect(() => {
    // Only run on client
    if (typeof window === "undefined") return;

    try {
      const routes = JSON.parse(localStorage.getItem("frequentRoutes") || "[]");
      const actions = JSON.parse(localStorage.getItem("recentActions") || "[]");

      setUserBehavior({
        frequentRoutes:
          routes.length > 0 ? routes : ["/dashboard", "/research"],
        recentActions: actions.length > 0 ? actions : ["view", "export"],
      });
    } catch (error) {
      console.error("Failed to read user behavior from localStorage:", error);
      setUserBehavior({
        frequentRoutes: ["/dashboard", "/research"],
        recentActions: ["view", "export"],
      });
    }
  }, []);

  // Update user behavior tracking
  useEffect(() => {
    // Only run on client
    if (typeof window === "undefined") return;

    const updateFrequentRoutes = () => {
      try {
        const routes = JSON.parse(
          localStorage.getItem("frequentRoutes") || "[]"
        );
        const updatedRoutes = [
          pathname,
          ...routes.filter((r: string) => r !== pathname),
        ].slice(0, 5);
        localStorage.setItem("frequentRoutes", JSON.stringify(updatedRoutes));

        setUserBehavior((prev) => ({
          ...prev,
          frequentRoutes: updatedRoutes,
        }));
      } catch (error) {
        console.error("Failed to update frequent routes:", error);
        setUserBehavior((prev) => ({
          ...prev,
          frequentRoutes: [pathname],
        }));
      }
    };

    updateFrequentRoutes();
    trackAction(`navigate:${pathname}`);
  }, [pathname, trackAction]);

  const [swState, swActions]: [ServiceWorkerState, ServiceWorkerActions] =
    useAutoServiceWorker({
      autoRegister: true,
      warmCacheOnRegister: true,
      userBehavior,
    });

  // Warm cache after service worker registration
  useEffect(() => {
    if (swState.isRegistered && !warmingState.isWarming) {
      // Warm cache with a slight delay to avoid blocking initial page load
      setTimeout(() => {
        warmCache("critical-resources");
      }, 2000);
    }
  }, [swState.isRegistered, warmingState.isWarming, warmCache]);

  const contextValue: ServiceWorkerContextType = {
    isSupported: swState.isSupported,
    isRegistered: swState.isRegistered,
    isUpdateAvailable: swState.isUpdateAvailable,
    cacheStatus: swState.cacheStatus,
    clearCache: swActions.clearCache,
    refreshCacheStatus: swActions.refreshCacheStatus,
  };

  return (
    <ServiceWorkerContext.Provider value={contextValue}>
      {children}
      {swState.isUpdateAvailable && (
        <ServiceWorkerUpdateNotification onUpdate={swActions.skipWaiting} />
      )}
    </ServiceWorkerContext.Provider>
  );
};

// Update notification component
interface ServiceWorkerUpdateNotificationProps {
  onUpdate: () => Promise<void>;
}

const ServiceWorkerUpdateNotification: React.FC<
  ServiceWorkerUpdateNotificationProps
> = ({ onUpdate }) => {
  const [isVisible, setIsVisible] = useState(true);

  const handleUpdate = async () => {
    try {
      await onUpdate();
      setIsVisible(false);
    } catch (error) {
      console.error("Failed to update service worker:", error);
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-blue-600 text-white p-4 rounded-lg shadow-lg z-50 max-w-sm">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-semibold">Update Available</h4>
          <p className="text-sm opacity-90">
            A new version of the app is ready.
          </p>
        </div>
        <div className="flex space-x-2 ml-4">
          <button
            onClick={handleUpdate}
            className="bg-white text-blue-600 px-3 py-1 rounded text-sm font-medium hover:bg-gray-100 transition-colors"
          >
            Update
          </button>
          <button
            onClick={() => setIsVisible(false)}
            className="text-white opacity-70 hover:opacity-100 transition-opacity"
          >
            ×
          </button>
        </div>
      </div>
    </div>
  );
};
