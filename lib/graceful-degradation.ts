/**
 * Graceful Degradation System
 * Implements fallback experiences for users with limited capabilities or JavaScript disabled
 */

/* eslint-disable react/no-children-prop */

import React from "react";
import {
  DeviceCapabilities,
  AdaptiveLoadingConfig,
} from "./device-capabilities";

export interface DegradationLevel {
  name: string;
  description: string;
  features: {
    animations: boolean;
    interactivity: boolean;
    dynamicContent: boolean;
    heavyComponents: boolean;
    realTimeUpdates: boolean;
    advancedCharts: boolean;
  };
  fallbacks: {
    chartsFallback: "static" | "simple" | "text";
    animationsFallback: "none" | "reduced" | "css-only";
    interactionFallback: "basic" | "enhanced" | "full";
  };
}

export interface FallbackComponent {
  original: React.ComponentType<any>;
  fallback: React.ComponentType<any>;
  noJSFallback?: string; // HTML string for no-JS scenarios
  minRequirements: {
    performanceScore?: number;
    features?: string[];
    network?: string;
  };
}

/**
 * Graceful degradation manager
 */
export class GracefulDegradationManager {
  private static instance: GracefulDegradationManager;
  private degradationLevels: DegradationLevel[] = [];
  private fallbackComponents = new Map<string, FallbackComponent>();
  private currentLevel: DegradationLevel | null = null;

  static getInstance(): GracefulDegradationManager {
    if (!GracefulDegradationManager.instance) {
      GracefulDegradationManager.instance = new GracefulDegradationManager();
    }
    return GracefulDegradationManager.instance;
  }

  constructor() {
    this.initializeDegradationLevels();
  }

  /**
   * Initialize degradation levels from high to low capability
   */
  private initializeDegradationLevels(): void {
    this.degradationLevels = [
      {
        name: "full",
        description: "Full experience with all features enabled",
        features: {
          animations: true,
          interactivity: true,
          dynamicContent: true,
          heavyComponents: true,
          realTimeUpdates: true,
          advancedCharts: true,
        },
        fallbacks: {
          chartsFallback: "simple",
          animationsFallback: "css-only",
          interactionFallback: "full",
        },
      },
      {
        name: "enhanced",
        description: "Enhanced experience with reduced animations",
        features: {
          animations: false,
          interactivity: true,
          dynamicContent: true,
          heavyComponents: true,
          realTimeUpdates: true,
          advancedCharts: true,
        },
        fallbacks: {
          chartsFallback: "simple",
          animationsFallback: "reduced",
          interactionFallback: "enhanced",
        },
      },
      {
        name: "standard",
        description: "Standard experience with essential features",
        features: {
          animations: false,
          interactivity: true,
          dynamicContent: true,
          heavyComponents: false,
          realTimeUpdates: false,
          advancedCharts: false,
        },
        fallbacks: {
          chartsFallback: "simple",
          animationsFallback: "none",
          interactionFallback: "enhanced",
        },
      },
      {
        name: "basic",
        description: "Basic experience with minimal JavaScript",
        features: {
          animations: false,
          interactivity: false,
          dynamicContent: false,
          heavyComponents: false,
          realTimeUpdates: false,
          advancedCharts: false,
        },
        fallbacks: {
          chartsFallback: "text",
          animationsFallback: "none",
          interactionFallback: "basic",
        },
      },
      {
        name: "minimal",
        description: "Minimal experience for very limited devices",
        features: {
          animations: false,
          interactivity: false,
          dynamicContent: false,
          heavyComponents: false,
          realTimeUpdates: false,
          advancedCharts: false,
        },
        fallbacks: {
          chartsFallback: "text",
          animationsFallback: "none",
          interactionFallback: "basic",
        },
      },
    ];
  }

  /**
   * Determine appropriate degradation level based on capabilities
   */
  determineDegradationLevel(
    capabilities: DeviceCapabilities,
    config: AdaptiveLoadingConfig
  ): DegradationLevel {
    const performanceScore = capabilities.performanceScore;
    const hasJavaScript = typeof window !== "undefined";
    const isSlowNetwork = ["slow-2g", "2g"].includes(
      capabilities.effectiveType
    );
    const isLowBattery =
      capabilities.batteryLevel !== undefined &&
      capabilities.batteryLevel < 0.2 &&
      !capabilities.charging;
    const hasSaveData = capabilities.saveData;
    const hasReducedMotion = capabilities.reducedMotion;

    // No JavaScript - minimal experience
    if (!hasJavaScript) {
      return this.degradationLevels.find((level) => level.name === "minimal")!;
    }

    // Very low performance or severe constraints - basic experience
    if (
      performanceScore < 30 ||
      isLowBattery ||
      (isSlowNetwork && hasSaveData)
    ) {
      return this.degradationLevels.find((level) => level.name === "basic")!;
    }

    // Low performance or network constraints - standard experience
    if (performanceScore < 50 || isSlowNetwork || hasSaveData) {
      return this.degradationLevels.find((level) => level.name === "standard")!;
    }

    // Medium performance or reduced motion preference - enhanced experience
    if (performanceScore < 70 || hasReducedMotion) {
      return this.degradationLevels.find((level) => level.name === "enhanced")!;
    }

    // High performance - full experience
    return this.degradationLevels.find((level) => level.name === "full")!;
  }

  /**
   * Set current degradation level
   */
  setDegradationLevel(level: DegradationLevel): void {
    this.currentLevel = level;

    // Apply CSS classes for styling adjustments
    if (typeof document !== "undefined") {
      document.documentElement.className = document.documentElement.className
        .replace(/degradation-\w+/g, "")
        .trim();
      document.documentElement.classList.add(`degradation-${level.name}`);
    }

    // Dispatch event for components to react to degradation level changes
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("degradation-level-change", {
          detail: { level },
        })
      );
    }
  }

  /**
   * Register a fallback component
   */
  registerFallback(name: string, config: FallbackComponent): void {
    this.fallbackComponents.set(name, config);
  }

  /**
   * Get appropriate component based on current degradation level
   */
  getComponent(name: string): React.ComponentType<any> | null {
    const fallbackConfig = this.fallbackComponents.get(name);
    if (!fallbackConfig || !this.currentLevel) {
      return null;
    }

    // Check if current level meets minimum requirements
    const meetsRequirements = this.checkRequirements(
      fallbackConfig.minRequirements,
      this.currentLevel
    );

    return meetsRequirements
      ? fallbackConfig.original
      : fallbackConfig.fallback;
  }

  /**
   * Check if degradation level meets component requirements
   */
  private checkRequirements(
    requirements: FallbackComponent["minRequirements"],
    level: DegradationLevel
  ): boolean {
    // Check performance score requirement
    if (
      requirements.performanceScore &&
      level.name === "basic" &&
      requirements.performanceScore > 30
    ) {
      return false;
    }
    if (
      requirements.performanceScore &&
      level.name === "standard" &&
      requirements.performanceScore > 50
    ) {
      return false;
    }

    // Check feature requirements
    if (requirements.features) {
      for (const feature of requirements.features) {
        if (!level.features[feature as keyof typeof level.features]) {
          return false;
        }
      }
    }

    return true;
  }

  /**
   * Get current degradation level
   */
  getCurrentLevel(): DegradationLevel | null {
    return this.currentLevel;
  }

  /**
   * Generate no-JavaScript fallback HTML
   */
  generateNoJSFallback(componentName: string, props: any = {}): string {
    const fallbackConfig = this.fallbackComponents.get(componentName);
    if (fallbackConfig?.noJSFallback) {
      return fallbackConfig.noJSFallback;
    }

    // Generate basic HTML fallback
    return `
      <div class="no-js-fallback" data-component="${componentName}">
        <div class="fallback-content">
          <h3>Content Loading</h3>
          <p>This content requires JavaScript to display properly.</p>
          <p>Please enable JavaScript in your browser for the full experience.</p>
        </div>
      </div>
    `;
  }

  /**
   * Get CSS for current degradation level
   */
  getDegradationCSS(): string {
    if (!this.currentLevel) return "";

    const level = this.currentLevel;
    let css = "";

    // Animation styles
    if (!level.features.animations) {
      css += `
        .degradation-${level.name} * {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
      `;
    } else if (level.fallbacks.animationsFallback === "reduced") {
      css += `
        .degradation-${level.name} * {
          animation-duration: 0.1s !important;
          transition-duration: 0.1s !important;
        }
      `;
    }

    // Heavy component styles
    if (!level.features.heavyComponents) {
      css += `
        .degradation-${level.name} .heavy-component {
          display: none;
        }
        .degradation-${level.name} .heavy-component-fallback {
          display: block;
        }
      `;
    }

    // Chart fallback styles
    if (level.fallbacks.chartsFallback === "text") {
      css += `
        .degradation-${level.name} .chart-container {
          display: none;
        }
        .degradation-${level.name} .chart-text-fallback {
          display: block;
        }
      `;
    }

    return css;
  }
}

// Export singleton instance
export const gracefulDegradationManager =
  GracefulDegradationManager.getInstance();

/**
 * React hook for graceful degradation
 */
export function useGracefulDegradation(
  capabilities?: DeviceCapabilities,
  config?: AdaptiveLoadingConfig
) {
  const [degradationLevel, setDegradationLevel] =
    React.useState<DegradationLevel | null>(null);
  const [isInitialized, setIsInitialized] = React.useState(false);

  React.useEffect(() => {
    if (capabilities && config) {
      const level = gracefulDegradationManager.determineDegradationLevel(
        capabilities,
        config
      );
      gracefulDegradationManager.setDegradationLevel(level);
      setDegradationLevel(level);
      setIsInitialized(true);
    }
  }, [capabilities, config]);

  React.useEffect(() => {
    const handleLevelChange = (event: CustomEvent) => {
      setDegradationLevel(event.detail.level);
    };

    if (typeof window !== "undefined") {
      window.addEventListener(
        "degradation-level-change",
        handleLevelChange as EventListener
      );
      return () => {
        window.removeEventListener(
          "degradation-level-change",
          handleLevelChange as EventListener
        );
      };
    }
  }, []);

  return {
    degradationLevel,
    isInitialized,
    getComponent: (name: string) =>
      gracefulDegradationManager.getComponent(name),
    shouldEnableFeature: (featureName: keyof DegradationLevel["features"]) =>
      degradationLevel?.features[featureName] ?? false,
    getFallbackType: (type: keyof DegradationLevel["fallbacks"]) =>
      degradationLevel?.fallbacks[type] ?? "basic",
  };
}

/**
 * Component for rendering fallback content
 */
export function FallbackContent({
  children,
  fallback,
  noJSFallback,
  requirements = {},
}: {
  children: React.ReactNode;
  fallback: React.ReactNode;
  noJSFallback?: string;
  requirements?: {
    performanceScore?: number;
    features?: string[];
  };
}) {
  const { degradationLevel, shouldEnableFeature } = useGracefulDegradation();

  // Check if requirements are met
  const meetsRequirements = React.useMemo(() => {
    if (!degradationLevel) return true;

    if (requirements.performanceScore) {
      const levelScores = {
        minimal: 0,
        basic: 30,
        standard: 50,
        enhanced: 70,
        full: 100,
      };

      const currentScore =
        levelScores[degradationLevel.name as keyof typeof levelScores] || 0;
      if (currentScore < requirements.performanceScore) {
        return false;
      }
    }

    if (requirements.features) {
      for (const feature of requirements.features) {
        if (
          !shouldEnableFeature(feature as keyof DegradationLevel["features"])
        ) {
          return false;
        }
      }
    }

    return true;
  }, [degradationLevel, requirements, shouldEnableFeature]);

  // No JavaScript fallback
  if (typeof window === "undefined" && noJSFallback) {
    return React.createElement("div", {
      dangerouslySetInnerHTML: { __html: noJSFallback },
    });
  }

  return meetsRequirements
    ? React.createElement(React.Fragment, {}, children)
    : React.createElement(React.Fragment, {}, fallback);
}

/**
 * Higher-order component for graceful degradation
 */
export function withGracefulDegradation<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  FallbackComponent: React.ComponentType<P>,
  requirements: {
    performanceScore?: number;
    features?: string[];
    noJSFallback?: string;
  } = {}
) {
  return function GracefulComponent(props: P) {
    const componentName =
      WrappedComponent.displayName || WrappedComponent.name || "Component";

    // Register fallback component
    React.useEffect(() => {
      gracefulDegradationManager.registerFallback(componentName, {
        original: WrappedComponent,
        fallback: FallbackComponent,
        noJSFallback: requirements.noJSFallback,
        minRequirements: {
          performanceScore: requirements.performanceScore,
          features: requirements.features,
        },
      });
    }, []);

    return React.createElement(FallbackContent, {
      fallback: React.createElement(FallbackComponent, props),
      noJSFallback: requirements.noJSFallback,
      requirements,
      children: React.createElement(WrappedComponent, props),
    });
  };
}

/**
 * Utility component for no-JavaScript detection
 */
export function NoScriptFallback({
  children,
  fallback,
}: {
  children: React.ReactNode;
  fallback: string;
}) {
  return React.createElement(
    React.Fragment,
    {},
    children,
    React.createElement("noscript", {
      dangerouslySetInnerHTML: { __html: fallback },
    })
  );
}
