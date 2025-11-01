/**
 * Progressive Feature Provider
 * Provides progressive feature loading context and initialization
 */

import React from "react";
import { useDeviceCapabilities } from "../lib/device-capabilities";
import { useGracefulDegradation } from "../lib/graceful-degradation";
import {
  useProgressiveFeatures,
  progressiveFeatureLoader,
} from "../lib/progressive-feature-loader";
import { getAllFeatures, getFeaturePreset } from "../lib/feature-registry";

export interface ProgressiveFeatureContextValue {
  isInitialized: boolean;
  capabilities: any;
  degradationLevel: any;
  loadedFeatures: Map<string, any>;
  loadFeature: (name: string) => Promise<any>;
  getFeatureComponent: (name: string) => React.ComponentType<any> | null;
  isFeatureLoaded: (name: string) => boolean;
  shouldEnableFeature: (name: string) => boolean;
  getAnalytics: () => any;
}

const ProgressiveFeatureContext =
  React.createContext<ProgressiveFeatureContextValue | null>(null);

export interface ProgressiveFeatureProviderProps {
  children: React.ReactNode;
  featurePreset?: "desktop" | "tablet" | "mobile" | "minimal" | "auto";
  customFeatures?: any[];
  autoStart?: boolean;
  onFeatureLoaded?: (featureName: string, result: any) => void;
  onInitialized?: (analytics: any) => void;
}

/**
 * Progressive Feature Provider Component
 */
export function ProgressiveFeatureProvider({
  children,
  featurePreset = "auto",
  customFeatures = [],
  autoStart = true,
  onFeatureLoaded,
  onInitialized,
}: ProgressiveFeatureProviderProps) {
  const {
    capabilities,
    config,
    isLoading: capabilitiesLoading,
  } = useDeviceCapabilities();
  const { degradationLevel } = useGracefulDegradation(
    capabilities || undefined,
    config || undefined
  );
  const {
    isInitialized,
    loadedFeatures,
    loadFeature,
    getFeatureComponent,
    isFeatureLoaded,
    startProgressiveLoading,
    getAnalytics,
  } = useProgressiveFeatures();

  const [hasStarted, setHasStarted] = React.useState(false);

  // Register features when capabilities are available
  React.useEffect(() => {
    if (!capabilities || !config || capabilitiesLoading) return;

    // Determine which features to register
    let featuresToRegister: any[] = [];

    if (featurePreset === "auto") {
      // Auto-select preset based on capabilities
      if (capabilities.performanceScore > 80) {
        featuresToRegister = getFeaturePreset("desktop");
      } else if (capabilities.performanceScore > 60) {
        featuresToRegister = getFeaturePreset("tablet");
      } else if (capabilities.performanceScore > 40) {
        featuresToRegister = getFeaturePreset("mobile");
      } else {
        featuresToRegister = getFeaturePreset("minimal");
      }
    } else {
      featuresToRegister = getFeaturePreset(featurePreset);
    }

    // Add custom features
    featuresToRegister = [...featuresToRegister, ...customFeatures];

    // Register all features
    progressiveFeatureLoader.registerFeatures(featuresToRegister);

    console.log(
      `Registered ${featuresToRegister.length} features for progressive loading`
    );
  }, [
    capabilities,
    config,
    capabilitiesLoading,
    featurePreset,
    customFeatures,
  ]);

  // Start progressive loading when initialized and auto-start is enabled
  React.useEffect(() => {
    if (isInitialized && autoStart && !hasStarted) {
      setHasStarted(true);
      startProgressiveLoading()
        .then(() => {
          const analytics = getAnalytics();
          console.log("Progressive loading completed:", analytics);
          onInitialized?.(analytics);
        })
        .catch((error) => {
          console.error("Progressive loading failed:", error);
        });
    }
  }, [
    isInitialized,
    autoStart,
    hasStarted,
    startProgressiveLoading,
    getAnalytics,
    onInitialized,
  ]);

  // Listen for feature load events
  React.useEffect(() => {
    const handleFeatureLoaded = (event: CustomEvent) => {
      const result = event.detail;
      console.log(`Feature loaded: ${result.feature.name}`, result);
      onFeatureLoaded?.(result.feature.name, result);
    };

    if (typeof window !== "undefined") {
      window.addEventListener(
        "progressive-feature-loaded",
        handleFeatureLoaded as EventListener
      );
      return () => {
        window.removeEventListener(
          "progressive-feature-loaded",
          handleFeatureLoaded as EventListener
        );
      };
    }
  }, [onFeatureLoaded]);

  // Enhanced shouldEnableFeature that considers both capabilities and degradation level
  const shouldEnableFeature = React.useCallback(
    (featureName: string) => {
      if (!capabilities || !degradationLevel) return false;

      // Check if feature is loaded
      if (!isFeatureLoaded(featureName)) return false;

      // Check degradation level restrictions
      const degradationRestrictions = {
        minimal: ["critical"],
        basic: ["critical", "important"],
        standard: ["critical", "important", "enhancement"],
        enhanced: ["critical", "important", "enhancement"],
        full: ["critical", "important", "enhancement", "optional"],
      };

      const allowedPriorities =
        degradationRestrictions[
          degradationLevel.name as keyof typeof degradationRestrictions
        ] || [];

      // Get feature definition to check priority
      const allFeatures = getAllFeatures();
      const feature = allFeatures.find((f) => f.name === featureName);

      if (
        feature &&
        feature.priority &&
        !allowedPriorities.includes(feature.priority)
      ) {
        return false;
      }

      return true;
    },
    [capabilities, degradationLevel, isFeatureLoaded]
  );

  const contextValue: ProgressiveFeatureContextValue = {
    isInitialized: isInitialized && !capabilitiesLoading,
    capabilities,
    degradationLevel,
    loadedFeatures,
    loadFeature,
    getFeatureComponent,
    isFeatureLoaded,
    shouldEnableFeature,
    getAnalytics,
  };

  return (
    <ProgressiveFeatureContext.Provider value={contextValue}>
      {children}
    </ProgressiveFeatureContext.Provider>
  );
}

/**
 * Hook to use progressive feature context
 */
export function useProgressiveFeatureContext(): ProgressiveFeatureContextValue {
  const context = React.useContext(ProgressiveFeatureContext);
  if (!context) {
    throw new Error(
      "useProgressiveFeatureContext must be used within a ProgressiveFeatureProvider"
    );
  }
  return context;
}

/**
 * Component for conditionally rendering features
 */
export function ProgressiveFeature({
  name,
  children,
  fallback,
  loadingComponent,
}: {
  name: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  loadingComponent?: React.ReactNode;
}) {
  const { isInitialized, shouldEnableFeature, getFeatureComponent } =
    useProgressiveFeatureContext();

  if (!isInitialized) {
    return (
      loadingComponent || (
        <div className="progressive-loading animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      )
    );
  }

  if (!shouldEnableFeature(name)) {
    return fallback || null;
  }

  return <>{children}</>;
}

/**
 * Component for loading features on demand
 */
export function LazyProgressiveFeature({
  name,
  fallback,
  loadingComponent,
  onLoad,
}: {
  name: string;
  fallback?: React.ReactNode;
  loadingComponent?: React.ReactNode;
  onLoad?: (component: React.ComponentType<any>) => void;
}) {
  const { loadFeature, getFeatureComponent, shouldEnableFeature } =
    useProgressiveFeatureContext();
  const [isLoading, setIsLoading] = React.useState(false);
  const [hasLoaded, setHasLoaded] = React.useState(false);

  const handleLoad = React.useCallback(async () => {
    if (isLoading || hasLoaded || !shouldEnableFeature(name)) return;

    setIsLoading(true);
    try {
      const result = await loadFeature(name);
      if (result.loaded && result.component) {
        setHasLoaded(true);
        onLoad?.(result.component);
      }
    } catch (error) {
      console.error(`Failed to load feature ${name}:`, error);
    } finally {
      setIsLoading(false);
    }
  }, [name, loadFeature, shouldEnableFeature, isLoading, hasLoaded, onLoad]);

  React.useEffect(() => {
    handleLoad();
  }, [handleLoad]);

  if (isLoading) {
    return (
      loadingComponent || (
        <div className="progressive-loading animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      )
    );
  }

  if (!hasLoaded || !shouldEnableFeature(name)) {
    return fallback || null;
  }

  const FeatureComponent = getFeatureComponent(name);
  return FeatureComponent ? <FeatureComponent /> : fallback || null;
}

/**
 * Hook for using a specific progressive feature
 */
export function useProgressiveFeature(name: string) {
  const {
    loadFeature,
    getFeatureComponent,
    isFeatureLoaded,
    shouldEnableFeature,
  } = useProgressiveFeatureContext();

  const [component, setComponent] =
    React.useState<React.ComponentType<any> | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  const load = React.useCallback(async () => {
    if (isLoading || component || !shouldEnableFeature(name)) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await loadFeature(name);
      if (result.loaded && result.component) {
        setComponent(result.component);
      } else if (result.error) {
        setError(result.error);
      }
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [name, loadFeature, shouldEnableFeature, isLoading, component]);

  React.useEffect(() => {
    // Check if already loaded
    const existingComponent = getFeatureComponent(name);
    if (existingComponent) {
      setComponent(existingComponent);
    } else if (shouldEnableFeature(name)) {
      load();
    }
  }, [name, getFeatureComponent, shouldEnableFeature, load]);

  return {
    component,
    isLoading,
    error,
    isLoaded: isFeatureLoaded(name),
    isEnabled: shouldEnableFeature(name),
    reload: load,
  };
}
