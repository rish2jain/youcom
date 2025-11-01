/**
 * Progressive Feature Loader
 * Manages intelligent loading of features based on device capabilities
 */

import React from "react";
import { adaptiveLoadingManager } from "./adaptive-loading-manager";
import {
  deviceCapabilitiesDetector,
  DeviceCapabilities,
  AdaptiveLoadingConfig,
} from "./device-capabilities";
import { loadingStateManager } from "./loading-state-manager";

export interface FeatureDefinition {
  name: string;
  description?: string;
  loader: () => Promise<any>;
  dependencies?: string[];
  priority?: "critical" | "important" | "enhancement" | "optional";
  requirements?: any;
  fallback?: any;
}

interface FeatureLoadResult {
  name: string;
  success: boolean;
  component?: any;
  error?: Error;
  loadTime: number;
}

// Using AdaptiveLoadingConfig from device-capabilities module

interface ProgressiveLoadingStrategy {
  name: string;
  description: string;
  loadOrder: string[];
  maxConcurrentLoads: number;
  loadDelay: number;
  enablePreloading: boolean;
}

export class ProgressiveFeatureLoader {
  private static instance: ProgressiveFeatureLoader;
  private features = new Map<string, FeatureDefinition>();
  private loadedFeatures = new Map<string, FeatureLoadResult>();
  private loadingPromises = new Map<string, Promise<FeatureLoadResult>>();
  private capabilities: DeviceCapabilities | null = null;
  private config: AdaptiveLoadingConfig | null = null;
  private loadingStrategy: ProgressiveLoadingStrategy | null = null;
  private loadQueue: string[] = [];
  private isProcessingQueue = false;

  static getInstance(): ProgressiveFeatureLoader {
    if (!ProgressiveFeatureLoader.instance) {
      ProgressiveFeatureLoader.instance = new ProgressiveFeatureLoader();
    }
    return ProgressiveFeatureLoader.instance;
  }

  /**
   * Initialize with device capabilities
   */
  async initialize(
    capabilities: DeviceCapabilities,
    config: AdaptiveLoadingConfig
  ): Promise<void> {
    this.capabilities = capabilities;
    this.config = config;
    this.loadingStrategy = this.determineLoadingStrategy(capabilities, config);
  }

  /**
   * Register a progressive feature
   */
  registerFeature(feature: FeatureDefinition): void {
    this.features.set(feature.name, feature);
  }

  /**
   * Register multiple features
   */
  registerFeatures(features: FeatureDefinition[]): void {
    features.forEach((feature) => this.registerFeature(feature));
  }

  /**
   * Determine optimal loading strategy based on capabilities
   */
  private determineLoadingStrategy(
    capabilities: DeviceCapabilities,
    config: AdaptiveLoadingConfig
  ): ProgressiveLoadingStrategy {
    const performanceScore = capabilities?.performanceScore || 0;
    const isSlowNetwork = ["slow-2g", "2g", "3g"].includes(
      capabilities?.effectiveType || "unknown"
    );
    const isLowBattery =
      capabilities.batteryLevel !== undefined &&
      capabilities.batteryLevel < 0.3 &&
      !capabilities.charging;

    if (performanceScore > 80 && !isSlowNetwork && !isLowBattery) {
      return {
        name: "aggressive",
        description: "Load all features quickly for high-performance devices",
        loadOrder: ["critical", "important", "enhancement", "optional"],
        maxConcurrentLoads: 4,
        loadDelay: 100,
        enablePreloading: true,
      };
    } else if (performanceScore > 60 && !isSlowNetwork) {
      return {
        name: "balanced",
        description: "Load features progressively with moderate concurrency",
        loadOrder: ["critical", "important", "enhancement"],
        maxConcurrentLoads: 2,
        loadDelay: 300,
        enablePreloading: true,
      };
    } else if (performanceScore > 40) {
      return {
        name: "conservative",
        description: "Load essential features only with low concurrency",
        loadOrder: ["critical", "important"],
        maxConcurrentLoads: 1,
        loadDelay: 500,
        enablePreloading: false,
      };
    } else {
      return {
        name: "minimal",
        description: "Load only critical features for low-performance devices",
        loadOrder: ["critical"],
        maxConcurrentLoads: 1,
        loadDelay: 1000,
        enablePreloading: false,
      };
    }
  }

  /**
   * Start progressive loading based on strategy
   */
  async startProgressiveLoading(): Promise<void> {
    if (!this.capabilities || !this.config || !this.loadingStrategy) {
      throw new Error("Progressive loader not initialized");
    }

    // Build load queue based on strategy and feature priorities
    this.loadQueue = this.buildLoadQueue();

    // Start processing queue
    this.processLoadQueue();
  }

  /**
   * Build load queue based on strategy and dependencies
   */
  private buildLoadQueue(): string[] {
    if (!this.loadingStrategy) return [];

    const queue: string[] = [];
    const processed = new Set<string>();

    // Process features by priority order defined in strategy
    for (const priority of this.loadingStrategy.loadOrder) {
      const featuresInPriority = Array.from(this.features.values())
        .filter((feature) => feature.priority === priority)
        .filter((feature) => this.shouldLoadFeature(feature))
        .sort(
          (a, b) =>
            (a.dependencies?.length || 0) - (b.dependencies?.length || 0)
        );

      for (const feature of featuresInPriority) {
        this.addFeatureToQueue(feature.name, queue, processed);
      }
    }

    return queue;
  }

  /**
   * Add feature to queue, ensuring dependencies are loaded first
   */
  private addFeatureToQueue(
    featureName: string,
    queue: string[],
    processed: Set<string>
  ): void {
    if (processed.has(featureName)) return;

    const feature = this.features.get(featureName);
    if (!feature) return;

    // Add dependencies first
    if (feature.dependencies) {
      for (const dependency of feature.dependencies) {
        this.addFeatureToQueue(dependency, queue, processed);
      }
    }

    // Add feature to queue
    queue.push(featureName);
    processed.add(featureName);
  }

  /**
   * Check if feature should be loaded based on capabilities
   */
  private shouldLoadFeature(feature: FeatureDefinition): boolean {
    if (!this.capabilities) return false;

    const requirements = feature.requirements;

    // Check performance score
    if (
      requirements.minPerformanceScore &&
      this.capabilities.performanceScore < requirements.minPerformanceScore
    ) {
      return false;
    }

    // Check memory
    if (
      requirements.minMemory &&
      this.capabilities.memory < requirements.minMemory
    ) {
      return false;
    }

    // Check CPU cores
    if (
      requirements.minCores &&
      this.capabilities.cores < requirements.minCores
    ) {
      return false;
    }

    // Check required features
    if (requirements.requiresFeatures) {
      for (const requiredFeature of requirements.requiresFeatures) {
        if (!(this.capabilities as any)?.[requiredFeature]) {
          return false;
        }
      }
    }

    // Check network requirements
    if (requirements.networkRequirement) {
      const networkMeetsRequirement = this.checkNetworkRequirement(
        requirements.networkRequirement
      );
      if (!networkMeetsRequirement) {
        return false;
      }
    }

    // Check battery requirements
    if (requirements.batteryRequirement) {
      const batteryMeetsRequirement = this.checkBatteryRequirement(
        requirements.batteryRequirement
      );
      if (!batteryMeetsRequirement) {
        return false;
      }
    }

    return true;
  }

  /**
   * Check network requirements
   */
  private checkNetworkRequirement(requirement: string): boolean {
    if (!this.capabilities) return false;

    switch (requirement) {
      case "wifi":
        return this.capabilities.connectionType === "wifi";
      case "4g":
        return (
          this.capabilities.effectiveType === "4g" ||
          this.capabilities.connectionType === "wifi"
        );
      case "3g":
        return (
          ["3g", "4g"].includes(this.capabilities.effectiveType) ||
          this.capabilities.connectionType === "wifi"
        );
      case "any":
        return true;
      default:
        return true;
    }
  }

  /**
   * Check battery requirements
   */
  private checkBatteryRequirement(requirement: string): boolean {
    if (!this.capabilities) return true;

    const batteryLevel = this.capabilities.batteryLevel;
    const charging = this.capabilities.charging;

    switch (requirement) {
      case "charging":
        return charging === true;
      case "high":
        return (
          batteryLevel === undefined || batteryLevel > 0.7 || charging === true
        );
      case "medium":
        return (
          batteryLevel === undefined || batteryLevel > 0.3 || charging === true
        );
      case "any":
        return true;
      default:
        return true;
    }
  }

  /**
   * Process load queue with concurrency control
   */
  private async processLoadQueue(): Promise<void> {
    if (this.isProcessingQueue || !this.loadingStrategy) return;

    this.isProcessingQueue = true;
    const maxConcurrent = this.loadingStrategy.maxConcurrentLoads;
    const loadDelay = this.loadingStrategy.loadDelay;

    try {
      while (this.loadQueue.length > 0) {
        // Take batch of features to load
        const batch = this.loadQueue.splice(0, maxConcurrent);

        // Load features in parallel
        const loadPromises = batch.map((featureName) =>
          this.loadFeature(featureName)
        );
        await Promise.allSettled(loadPromises);

        // Delay before next batch (if there are more features)
        if (this.loadQueue.length > 0) {
          await new Promise((resolve) => setTimeout(resolve, loadDelay));
        }
      }
    } finally {
      this.isProcessingQueue = false;
    }
  }

  /**
   * Load a specific feature
   */
  async loadFeature(featureName: string): Promise<FeatureLoadResult> {
    // Return cached result if available
    if (this.loadedFeatures.has(featureName)) {
      return this.loadedFeatures.get(featureName)!;
    }

    // Return existing promise if loading
    if (this.loadingPromises.has(featureName)) {
      return this.loadingPromises.get(featureName)!;
    }

    const feature = this.features.get(featureName);
    if (!feature) {
      throw new Error(`Feature ${featureName} not registered`);
    }

    const loadPromise = this.executeFeatureLoad(feature);
    this.loadingPromises.set(featureName, loadPromise);

    try {
      const result = await loadPromise;
      this.loadedFeatures.set(featureName, result);
      this.loadingPromises.delete(featureName);

      // Dispatch load event
      this.dispatchFeatureLoadEvent(result);

      return result;
    } catch (error) {
      this.loadingPromises.delete(featureName);
      const errorResult: FeatureLoadResult = {
        name: featureName,
        success: false,
        error: error as Error,
        loadTime: 0,
      };
      this.loadedFeatures.set(featureName, errorResult);
      return errorResult;
    }
  }

  /**
   * Execute feature loading with timing
   */
  private async executeFeatureLoad(
    feature: FeatureDefinition
  ): Promise<FeatureLoadResult> {
    const startTime = performance.now();

    try {
      const component = await feature.loader();
      const loadTime = performance.now() - startTime;

      return {
        name: feature.name,
        success: true,
        component,
        loadTime,
      };
    } catch (error) {
      const loadTime = performance.now() - startTime;

      return {
        name: feature.name,
        success: false,
        error: error as Error,
        loadTime,
      };
    }
  }

  /**
   * Dispatch feature load event
   */
  private dispatchFeatureLoadEvent(result: FeatureLoadResult): void {
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("progressive-feature-loaded", {
          detail: result,
        })
      );
    }
  }

  /**
   * Get feature load status
   */
  getFeatureStatus(featureName: string): FeatureLoadResult | null {
    return this.loadedFeatures.get(featureName) || null;
  }

  /**
   * Get all loaded features
   */
  getAllLoadedFeatures(): Map<string, FeatureLoadResult> {
    return new Map(this.loadedFeatures);
  }

  /**
   * Get loading analytics
   */
  getLoadingAnalytics(): {
    totalFeatures: number;
    loadedFeatures: number;
    failedFeatures: number;
    averageLoadTime: number;
    strategy: ProgressiveLoadingStrategy | null;
  } {
    const results = Array.from(this.loadedFeatures.values());
    const loadedCount = results.filter((r) => r.success).length;
    const failedCount = results.filter((r) => !r.success).length;
    const totalLoadTime = results
      .filter((r) => r.loadTime)
      .reduce((sum, r) => sum + (r.loadTime || 0), 0);
    const averageLoadTime =
      results.length > 0 ? totalLoadTime / results.length : 0;

    return {
      totalFeatures: this.features.size,
      loadedFeatures: loadedCount,
      failedFeatures: failedCount,
      averageLoadTime,
      strategy: this.loadingStrategy,
    };
  }

  /**
   * Force load a feature (bypass capability checks)
   */
  async forceLoadFeature(featureName: string): Promise<FeatureLoadResult> {
    const feature = this.features.get(featureName);
    if (!feature) {
      throw new Error(`Feature ${featureName} not registered`);
    }

    return this.executeFeatureLoad(feature);
  }

  /**
   * Unload a feature (for memory management)
   */
  unloadFeature(featureName: string): void {
    this.loadedFeatures.delete(featureName);
    this.loadingPromises.delete(featureName);

    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("progressive-feature-unloaded", {
          detail: { featureName },
        })
      );
    }
  }
}

// Export singleton instance
export const progressiveFeatureLoader = ProgressiveFeatureLoader.getInstance();

/**
 * React hook for progressive feature loading
 */
export function useProgressiveFeatures(featureNames?: string[]) {
  const [loadedFeatures, setLoadedFeatures] = React.useState<
    Map<string, FeatureLoadResult>
  >(new Map());
  const [isInitialized, setIsInitialized] = React.useState(false);

  React.useEffect(() => {
    let mounted = true;

    const initialize = async () => {
      try {
        // Initialize with adaptive loading manager capabilities
        await adaptiveLoadingManager.initialize();
        const capabilities = adaptiveLoadingManager.getCapabilities();
        const config = adaptiveLoadingManager.getConfig();

        if (capabilities && config) {
          await progressiveFeatureLoader.initialize(capabilities, config);

          if (mounted) {
            setIsInitialized(true);
          }
        }
      } catch (error) {
        console.error("Failed to initialize progressive features:", error);
        if (mounted) {
          setIsInitialized(true);
        }
      }
    };

    initialize();

    return () => {
      mounted = false;
    };
  }, []);

  React.useEffect(() => {
    if (!isInitialized) return;

    const handleFeatureLoaded = (event: CustomEvent) => {
      const result = event.detail as FeatureLoadResult;
      setLoadedFeatures((prev) => new Map(prev).set(result.name, result));
    };

    const handleFeatureUnloaded = (event: CustomEvent) => {
      const { featureName } = event.detail;
      setLoadedFeatures((prev) => {
        const newMap = new Map(prev);
        newMap.delete(featureName);
        return newMap;
      });
    };

    if (typeof window !== "undefined") {
      window.addEventListener(
        "progressive-feature-loaded",
        handleFeatureLoaded as EventListener
      );
      window.addEventListener(
        "progressive-feature-unloaded",
        handleFeatureUnloaded as EventListener
      );

      return () => {
        window.removeEventListener(
          "progressive-feature-loaded",
          handleFeatureLoaded as EventListener
        );
        window.removeEventListener(
          "progressive-feature-unloaded",
          handleFeatureUnloaded as EventListener
        );
      };
    }
  }, [isInitialized]);

  const loadFeature = React.useCallback(
    async (featureName: string) => {
      if (!isInitialized) return null;
      return progressiveFeatureLoader.loadFeature(featureName);
    },
    [isInitialized]
  );

  const getFeatureComponent = React.useCallback(
    (featureName: string) => {
      const result = loadedFeatures.get(featureName);
      return result?.success ? result.component : null;
    },
    [loadedFeatures]
  );

  const isFeatureLoaded = React.useCallback(
    (featureName: string) => {
      const result = loadedFeatures.get(featureName);
      return result?.success || false;
    },
    [loadedFeatures]
  );

  return {
    isInitialized,
    loadedFeatures,
    loadFeature,
    getFeatureComponent,
    isFeatureLoaded,
    startProgressiveLoading: () =>
      progressiveFeatureLoader.startProgressiveLoading(),
    getAnalytics: () => progressiveFeatureLoader.getLoadingAnalytics(),
  };
}

/**
 * Higher-order component for progressive feature loading
 */
export function withProgressiveLoading<P extends object>(
  featureDefinition: FeatureDefinition
) {
  return function ProgressiveFeatureWrapper(props: P) {
    const { isInitialized, getFeatureComponent, isFeatureLoaded, loadFeature } =
      useProgressiveFeatures();
    const [isLoading, setIsLoading] = React.useState(true);

    React.useEffect(() => {
      if (!isInitialized) return;

      // Register feature
      progressiveFeatureLoader.registerFeature(featureDefinition);

      // Load feature
      loadFeature(featureDefinition.name)
        .then(() => setIsLoading(false))
        .catch(() => setIsLoading(false));
    }, [isInitialized, loadFeature]);

    if (!isInitialized || isLoading) {
      return React.createElement(
        "div",
        { className: "progressive-loading animate-pulse" },
        React.createElement("div", {
          className: "h-4 bg-gray-200 rounded w-3/4 mb-2",
        }),
        React.createElement("div", {
          className: "h-4 bg-gray-200 rounded w-1/2",
        })
      );
    }

    const FeatureComponent = getFeatureComponent(featureDefinition.name);

    if (!FeatureComponent) {
      // Render fallback if available
      if (featureDefinition.fallback) {
        return React.createElement(featureDefinition.fallback, props);
      }

      // Render minimal fallback
      return React.createElement(
        "div",
        {
          className: "progressive-fallback p-4 border border-gray-200 rounded",
        },
        React.createElement(
          "p",
          { className: "text-gray-600" },
          `${featureDefinition.name} not available`
        )
      );
    }

    return React.createElement(FeatureComponent, props);
  };
}
