/**
 * Adaptive Loading Manager
 * Implements progressive enhancement strategies based on device capabilities
 */

import React from "react";
import {
  DeviceCapabilities,
  AdaptiveLoadingConfig,
  deviceCapabilitiesDetector,
} from "./device-capabilities";

export interface AdaptiveComponentConfig {
  component: React.ComponentType<any>;
  fallback?: React.ComponentType<any>;
  loadingComponent?: React.ComponentType<any>;
  minPerformanceScore?: number;
  requiresFeatures?: Array<keyof DeviceCapabilities>;
  networkRequirement?: "wifi" | "4g" | "3g" | "any";
}

export interface LoadingStrategy {
  name: string;
  shouldLoad: (
    capabilities: DeviceCapabilities,
    config: AdaptiveLoadingConfig
  ) => boolean;
  loadComponent: () => Promise<React.ComponentType<any>>;
  priority: number;
}

/**
 * Adaptive loading manager with progressive enhancement
 */
export class AdaptiveLoadingManager {
  private static instance: AdaptiveLoadingManager;
  private componentRegistry = new Map<string, AdaptiveComponentConfig>();
  private loadedComponents = new Map<string, React.ComponentType<any>>();
  private loadingPromises = new Map<
    string,
    Promise<React.ComponentType<any>>
  >();
  private capabilities: DeviceCapabilities | null = null;
  private config: AdaptiveLoadingConfig | null = null;

  static getInstance(): AdaptiveLoadingManager {
    if (!AdaptiveLoadingManager.instance) {
      AdaptiveLoadingManager.instance = new AdaptiveLoadingManager();
    }
    return AdaptiveLoadingManager.instance;
  }

  /**
   * Initialize with device capabilities
   */
  async initialize(): Promise<void> {
    this.capabilities = await deviceCapabilitiesDetector.detectCapabilities();
    this.config = deviceCapabilitiesDetector.generateAdaptiveConfig(
      this.capabilities
    );
  }

  /**
   * Register an adaptive component
   */
  registerComponent(name: string, config: AdaptiveComponentConfig): void {
    this.componentRegistry.set(name, config);
  }

  /**
   * Load component adaptively based on capabilities
   */
  async loadComponent(name: string): Promise<React.ComponentType<any>> {
    // Return cached component if available
    if (this.loadedComponents.has(name)) {
      return this.loadedComponents.get(name)!;
    }

    // Return existing loading promise if in progress
    if (this.loadingPromises.has(name)) {
      return this.loadingPromises.get(name)!;
    }

    const componentConfig = this.componentRegistry.get(name);
    if (!componentConfig) {
      throw new Error(`Component ${name} not registered`);
    }

    // Ensure capabilities are loaded
    if (!this.capabilities || !this.config) {
      await this.initialize();
    }

    const shouldLoadFullComponent = this.shouldLoadFullComponent(
      componentConfig,
      this.capabilities!,
      this.config!
    );

    let loadingPromise: Promise<React.ComponentType<any>>;

    if (shouldLoadFullComponent) {
      // Load full component
      loadingPromise = Promise.resolve(componentConfig.component);
    } else if (componentConfig.fallback) {
      // Load fallback component
      loadingPromise = Promise.resolve(componentConfig.fallback);
    } else {
      // Create minimal fallback
      loadingPromise = Promise.resolve(this.createMinimalFallback(name));
    }

    this.loadingPromises.set(name, loadingPromise);

    try {
      const component = await loadingPromise;
      this.loadedComponents.set(name, component);
      this.loadingPromises.delete(name);
      return component;
    } catch (error) {
      this.loadingPromises.delete(name);
      console.error(`Failed to load component ${name}:`, error);

      // Return fallback or minimal component on error
      if (componentConfig.fallback) {
        return componentConfig.fallback;
      }
      return this.createMinimalFallback(name);
    }
  }

  /**
   * Determine if full component should be loaded
   */
  private shouldLoadFullComponent(
    componentConfig: AdaptiveComponentConfig,
    capabilities: DeviceCapabilities,
    config: AdaptiveLoadingConfig
  ): boolean {
    // Check minimum performance score
    if (
      componentConfig.minPerformanceScore &&
      capabilities.performanceScore < componentConfig.minPerformanceScore
    ) {
      return false;
    }

    // Check required features
    if (componentConfig.requiresFeatures) {
      for (const feature of componentConfig.requiresFeatures) {
        if (!capabilities[feature]) {
          return false;
        }
      }
    }

    // Check network requirements
    if (componentConfig.networkRequirement) {
      const networkMeetsRequirement = this.checkNetworkRequirement(
        componentConfig.networkRequirement,
        capabilities
      );
      if (!networkMeetsRequirement) {
        return false;
      }
    }

    // Check save data preference
    if (capabilities.saveData) {
      return false;
    }

    // Check battery level (if available)
    if (
      capabilities.batteryLevel !== undefined &&
      capabilities.batteryLevel < 0.2 &&
      !capabilities.charging
    ) {
      return false;
    }

    return true;
  }

  /**
   * Check if network meets requirements
   */
  private checkNetworkRequirement(
    requirement: "wifi" | "4g" | "3g" | "any",
    capabilities: DeviceCapabilities
  ): boolean {
    switch (requirement) {
      case "wifi":
        return capabilities.connectionType === "wifi";
      case "4g":
        return (
          capabilities.effectiveType === "4g" ||
          capabilities.connectionType === "wifi"
        );
      case "3g":
        return (
          ["3g", "4g"].includes(capabilities.effectiveType) ||
          capabilities.connectionType === "wifi"
        );
      case "any":
        return true;
      default:
        return true;
    }
  }

  /**
   * Create minimal fallback component
   */
  private createMinimalFallback(name: string): React.ComponentType<any> {
    return function MinimalFallback(props: any) {
      return React.createElement(
        "div",
        {
          className:
            "adaptive-fallback p-4 border border-gray-200 rounded-lg bg-gray-50",
          "data-component": name,
        },
        React.createElement(
          "p",
          { className: "text-sm text-gray-600" },
          `${name} (simplified view)`
        )
      );
    };
  }

  /**
   * Get adaptive image props based on capabilities
   */
  getAdaptiveImageProps(
    src: string,
    alt: string,
    options: {
      sizes?: string;
      priority?: boolean;
      quality?: number;
    } = {}
  ): {
    src: string;
    alt: string;
    loading: "lazy" | "eager";
    decoding: "async" | "sync";
    sizes?: string;
    quality?: number;
  } {
    if (!this.capabilities || !this.config) {
      return {
        src,
        alt,
        loading: "lazy",
        decoding: "async",
        ...options,
      };
    }

    const loading =
      options.priority || this.capabilities.performanceScore > 70
        ? "eager"
        : "lazy";

    const decoding = this.capabilities.performanceScore > 50 ? "async" : "sync";

    const quality =
      options.quality ||
      (this.config.imageQuality === "high"
        ? 90
        : this.config.imageQuality === "medium"
        ? 75
        : 60);

    return {
      src,
      alt,
      loading,
      decoding,
      sizes: options.sizes,
      quality,
    };
  }

  /**
   * Get adaptive animation props
   */
  getAdaptiveAnimationProps(): {
    enableAnimations: boolean;
    duration: number;
    easing: string;
  } {
    if (!this.capabilities || !this.config) {
      return {
        enableAnimations: true,
        duration: 300,
        easing: "ease-in-out",
      };
    }

    return {
      enableAnimations: this.config.enableAnimations,
      duration: this.config.animationDuration,
      easing:
        this.capabilities.performanceScore > 70
          ? "cubic-bezier(0.4, 0, 0.2, 1)"
          : "ease-in-out",
    };
  }

  /**
   * Get adaptive loading strategy for lists/grids
   */
  getAdaptiveListConfig(itemCount: number): {
    initialItems: number;
    loadMoreThreshold: number;
    batchSize: number;
    enableVirtualization: boolean;
  } {
    if (!this.capabilities) {
      return {
        initialItems: 10,
        loadMoreThreshold: 5,
        batchSize: 10,
        enableVirtualization: false,
      };
    }

    const performanceScore = this.capabilities.performanceScore;

    if (performanceScore > 80) {
      return {
        initialItems: Math.min(itemCount, 50),
        loadMoreThreshold: 10,
        batchSize: 25,
        enableVirtualization: itemCount > 100,
      };
    } else if (performanceScore > 60) {
      return {
        initialItems: Math.min(itemCount, 25),
        loadMoreThreshold: 8,
        batchSize: 15,
        enableVirtualization: itemCount > 50,
      };
    } else if (performanceScore > 40) {
      return {
        initialItems: Math.min(itemCount, 15),
        loadMoreThreshold: 5,
        batchSize: 10,
        enableVirtualization: itemCount > 30,
      };
    } else {
      return {
        initialItems: Math.min(itemCount, 10),
        loadMoreThreshold: 3,
        batchSize: 5,
        enableVirtualization: itemCount > 20,
      };
    }
  }

  /**
   * Get current capabilities
   */
  getCapabilities(): DeviceCapabilities | null {
    return this.capabilities;
  }

  /**
   * Get current config
   */
  getConfig(): AdaptiveLoadingConfig | null {
    return this.config;
  }

  /**
   * Check if feature should be enabled
   */
  shouldEnableFeature(
    featureName: string,
    requirements: {
      minPerformanceScore?: number;
      requiresFeatures?: Array<keyof DeviceCapabilities>;
      networkRequirement?: "wifi" | "4g" | "3g" | "any";
    }
  ): boolean {
    if (!this.capabilities) {
      return false;
    }

    return this.shouldLoadFullComponent(
      {
        component: () => null,
        ...requirements,
      },
      this.capabilities,
      this.config!
    );
  }

  /**
   * Get performance-aware timeout values
   */
  getAdaptiveTimeouts(): {
    apiTimeout: number;
    debounceDelay: number;
    animationTimeout: number;
  } {
    if (!this.capabilities) {
      return {
        apiTimeout: 10000,
        debounceDelay: 300,
        animationTimeout: 500,
      };
    }

    const performanceScore = this.capabilities.performanceScore;
    const networkMultiplier =
      this.capabilities.effectiveType === "slow-2g"
        ? 3
        : this.capabilities.effectiveType === "2g"
        ? 2
        : this.capabilities.effectiveType === "3g"
        ? 1.5
        : 1;

    return {
      apiTimeout: Math.min(
        30000,
        5000 + (100 - performanceScore) * 100 * networkMultiplier
      ),
      debounceDelay:
        performanceScore > 70 ? 150 : performanceScore > 40 ? 300 : 500,
      animationTimeout: this.config?.animationDuration || 300,
    };
  }
}

// Export singleton instance
export const adaptiveLoadingManager = AdaptiveLoadingManager.getInstance();

/**
 * React hook for adaptive loading
 */
export function useAdaptiveLoading() {
  const [isInitialized, setIsInitialized] = React.useState(false);
  const [capabilities, setCapabilities] =
    React.useState<DeviceCapabilities | null>(null);
  const [config, setConfig] = React.useState<AdaptiveLoadingConfig | null>(
    null
  );

  React.useEffect(() => {
    let mounted = true;

    const initialize = async () => {
      try {
        await adaptiveLoadingManager.initialize();

        if (mounted) {
          setCapabilities(adaptiveLoadingManager.getCapabilities());
          setConfig(adaptiveLoadingManager.getConfig());
          setIsInitialized(true);
        }
      } catch (error) {
        console.error("Failed to initialize adaptive loading:", error);
        if (mounted) {
          setIsInitialized(true); // Still set to true to prevent infinite loading
        }
      }
    };

    initialize();

    return () => {
      mounted = false;
    };
  }, []);

  return {
    isInitialized,
    capabilities,
    config,
    loadComponent: (name: string) => adaptiveLoadingManager.loadComponent(name),
    getAdaptiveImageProps: (src: string, alt: string, options?: any) =>
      adaptiveLoadingManager.getAdaptiveImageProps(src, alt, options),
    getAdaptiveAnimationProps: () =>
      adaptiveLoadingManager.getAdaptiveAnimationProps(),
    getAdaptiveListConfig: (itemCount: number) =>
      adaptiveLoadingManager.getAdaptiveListConfig(itemCount),
    shouldEnableFeature: (featureName: string, requirements: any) =>
      adaptiveLoadingManager.shouldEnableFeature(featureName, requirements),
    getAdaptiveTimeouts: () => adaptiveLoadingManager.getAdaptiveTimeouts(),
  };
}

/**
 * Higher-order component for adaptive loading
 */
export function withAdaptiveLoading<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  config: {
    fallback?: React.ComponentType<P>;
    minPerformanceScore?: number;
    requiresFeatures?: Array<keyof DeviceCapabilities>;
    networkRequirement?: "wifi" | "4g" | "3g" | "any";
  } = {}
) {
  return function AdaptiveComponent(props: P) {
    const { isInitialized, loadComponent } = useAdaptiveLoading();
    const [Component, setComponent] =
      React.useState<React.ComponentType<P> | null>(null);
    const [isLoading, setIsLoading] = React.useState(true);

    React.useEffect(() => {
      if (!isInitialized) return;

      const componentName =
        WrappedComponent.displayName || WrappedComponent.name || "Component";

      // Register component if not already registered
      adaptiveLoadingManager.registerComponent(componentName, {
        component: WrappedComponent,
        fallback: config.fallback,
        minPerformanceScore: config.minPerformanceScore,
        requiresFeatures: config.requiresFeatures,
        networkRequirement: config.networkRequirement,
      });

      // Load component
      loadComponent(componentName)
        .then((LoadedComponent) => {
          setComponent(() => LoadedComponent);
          setIsLoading(false);
        })
        .catch((error) => {
          console.error(
            `Failed to load adaptive component ${componentName}:`,
            error
          );
          setComponent(() => config.fallback || WrappedComponent);
          setIsLoading(false);
        });
    }, [isInitialized, loadComponent]);

    if (isLoading || !Component) {
      return React.createElement(
        "div",
        { className: "adaptive-loading animate-pulse" },
        React.createElement("div", {
          className: "h-4 bg-gray-200 rounded w-3/4 mb-2",
        }),
        React.createElement("div", {
          className: "h-4 bg-gray-200 rounded w-1/2",
        })
      );
    }

    return React.createElement(Component, props);
  };
}
