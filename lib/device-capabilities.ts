/**
 * Device Capabilities Detection and Adaptive Loading System
 * Implements progressive enhancement based on device performance and network conditions
 */

import React from "react";

export interface DeviceCapabilities {
  // Hardware capabilities
  memory: number; // GB
  cores: number;
  gpu: boolean;

  // Network capabilities
  connectionType: "slow-2g" | "2g" | "3g" | "4g" | "wifi" | "unknown";
  effectiveType: "slow-2g" | "2g" | "3g" | "4g";
  downlink: number; // Mbps
  rtt: number; // ms
  saveData: boolean;

  // Browser capabilities
  webp: boolean;
  avif: boolean;
  webgl: boolean;
  serviceWorker: boolean;
  intersectionObserver: boolean;

  // Performance characteristics
  performanceScore: number; // 0-100
  batteryLevel?: number; // 0-1
  charging?: boolean;

  // User preferences
  reducedMotion: boolean;
  highContrast: boolean;

  // Calculated capabilities
  canHandleAnimations: boolean;
  canHandleHeavyComponents: boolean;
  shouldPreload: boolean;
  maxConcurrentRequests: number;
}

export interface AdaptiveLoadingConfig {
  // Component loading strategies
  lazyLoadThreshold: number; // pixels
  preloadDistance: number; // pixels
  maxConcurrentLoads: number;

  // Animation settings
  enableAnimations: boolean;
  animationDuration: number; // ms

  // Image optimization
  imageQuality: "low" | "medium" | "high";
  imageFormat: "webp" | "avif" | "jpeg";

  // Bundle loading
  enableCodeSplitting: boolean;
  prefetchStrategy: "aggressive" | "conservative" | "disabled";

  // Performance budgets
  maxBundleSize: number; // bytes
  maxLoadTime: number; // ms
}

/**
 * Device capabilities detector with comprehensive analysis
 */
export class DeviceCapabilitiesDetector {
  private static instance: DeviceCapabilitiesDetector;
  private capabilities: DeviceCapabilities | null = null;
  private config: AdaptiveLoadingConfig | null = null;

  static getInstance(): DeviceCapabilitiesDetector {
    if (!DeviceCapabilitiesDetector.instance) {
      DeviceCapabilitiesDetector.instance = new DeviceCapabilitiesDetector();
    }
    return DeviceCapabilitiesDetector.instance;
  }

  /**
   * Detect comprehensive device capabilities
   */
  async detectCapabilities(): Promise<DeviceCapabilities> {
    if (this.capabilities) {
      return this.capabilities;
    }

    const capabilities: DeviceCapabilities = {
      // Hardware detection
      memory: this.detectMemory(),
      cores: this.detectCores(),
      gpu: this.detectGPU(),

      // Network detection
      connectionType: this.detectConnectionType(),
      effectiveType: this.detectEffectiveConnectionType(),
      downlink: this.detectDownlink(),
      rtt: this.detectRTT(),
      saveData: this.detectSaveData(),

      // Browser capabilities
      webp: await this.detectWebPSupport(),
      avif: await this.detectAVIFSupport(),
      webgl: this.detectWebGLSupport(),
      serviceWorker: this.detectServiceWorkerSupport(),
      intersectionObserver: this.detectIntersectionObserverSupport(),

      // Performance characteristics
      performanceScore: await this.calculatePerformanceScore(),
      batteryLevel: await this.detectBatteryLevel(),
      charging: await this.detectChargingStatus(),

      // User preferences
      reducedMotion: this.detectReducedMotion(),
      highContrast: this.detectHighContrast(),

      // Calculated capabilities (will be set below)
      canHandleAnimations: false,
      canHandleHeavyComponents: false,
      shouldPreload: false,
      maxConcurrentRequests: 2,
    };

    // Calculate derived capabilities
    capabilities.canHandleAnimations =
      this.calculateAnimationCapability(capabilities);
    capabilities.canHandleHeavyComponents =
      this.calculateHeavyComponentCapability(capabilities);
    capabilities.shouldPreload = this.calculatePreloadCapability(capabilities);
    capabilities.maxConcurrentRequests =
      this.calculateMaxConcurrentRequests(capabilities);

    this.capabilities = capabilities;
    return capabilities;
  }

  /**
   * Generate adaptive loading configuration based on capabilities
   */
  generateAdaptiveConfig(
    capabilities: DeviceCapabilities
  ): AdaptiveLoadingConfig {
    if (this.config) {
      return this.config;
    }

    const config: AdaptiveLoadingConfig = {
      // Lazy loading thresholds based on performance
      lazyLoadThreshold:
        capabilities.performanceScore > 70
          ? 200
          : capabilities.performanceScore > 40
          ? 400
          : 800,
      preloadDistance: capabilities.shouldPreload ? 1000 : 0,
      maxConcurrentLoads: capabilities.maxConcurrentRequests,

      // Animation settings
      enableAnimations:
        capabilities.canHandleAnimations && !capabilities.reducedMotion,
      animationDuration:
        capabilities.performanceScore > 70
          ? 300
          : capabilities.performanceScore > 40
          ? 200
          : 100,

      // Image optimization
      imageQuality:
        capabilities.connectionType === "wifi" &&
        capabilities.performanceScore > 70
          ? "high"
          : capabilities.performanceScore > 40
          ? "medium"
          : "low",
      imageFormat: capabilities.avif
        ? "avif"
        : capabilities.webp
        ? "webp"
        : "jpeg",

      // Bundle loading
      enableCodeSplitting: capabilities.performanceScore > 30,
      prefetchStrategy: capabilities.shouldPreload
        ? "aggressive"
        : capabilities.performanceScore > 50
        ? "conservative"
        : "disabled",

      // Performance budgets
      maxBundleSize:
        capabilities.performanceScore > 70
          ? 800000 // 800KB
          : capabilities.performanceScore > 40
          ? 500000 // 500KB
          : 300000, // 300KB
      maxLoadTime:
        capabilities.connectionType === "wifi"
          ? 2000
          : capabilities.effectiveType === "4g"
          ? 3000
          : capabilities.effectiveType === "3g"
          ? 5000
          : 8000,
    };

    this.config = config;
    return config;
  }

  // Hardware detection methods
  private detectMemory(): number {
    if (typeof navigator !== "undefined" && "deviceMemory" in navigator) {
      return (navigator as any).deviceMemory || 4;
    }

    // Fallback estimation based on user agent and performance
    const userAgent = navigator?.userAgent || "";
    if (userAgent.includes("Mobile") || userAgent.includes("Android")) {
      return 2; // Assume mobile has less memory
    }
    return 4; // Default assumption for desktop
  }

  private detectCores(): number {
    if (
      typeof navigator !== "undefined" &&
      "hardwareConcurrency" in navigator
    ) {
      return navigator.hardwareConcurrency || 2;
    }
    return 2; // Conservative default
  }

  private detectGPU(): boolean {
    if (typeof window === "undefined") return false;

    try {
      const canvas = document.createElement("canvas");
      const gl =
        canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
      return !!gl;
    } catch {
      return false;
    }
  }

  // Network detection methods
  private detectConnectionType(): DeviceCapabilities["connectionType"] {
    if (typeof navigator !== "undefined" && "connection" in navigator) {
      const connection = (navigator as any).connection;
      return connection?.type || "unknown";
    }
    return "unknown";
  }

  private detectEffectiveConnectionType(): DeviceCapabilities["effectiveType"] {
    if (typeof navigator !== "undefined" && "connection" in navigator) {
      const connection = (navigator as any).connection;
      return connection?.effectiveType || "4g";
    }
    return "4g"; // Optimistic default
  }

  private detectDownlink(): number {
    if (typeof navigator !== "undefined" && "connection" in navigator) {
      const connection = (navigator as any).connection;
      return connection?.downlink || 10;
    }
    return 10; // Default 10 Mbps
  }

  private detectRTT(): number {
    if (typeof navigator !== "undefined" && "connection" in navigator) {
      const connection = (navigator as any).connection;
      return connection?.rtt || 100;
    }
    return 100; // Default 100ms
  }

  private detectSaveData(): boolean {
    if (typeof navigator !== "undefined" && "connection" in navigator) {
      const connection = (navigator as any).connection;
      return connection?.saveData || false;
    }
    return false;
  }

  // Browser capability detection
  private async detectWebPSupport(): Promise<boolean> {
    if (typeof window === "undefined") return false;

    return new Promise((resolve) => {
      const webP = new Image();
      webP.onload = webP.onerror = () => {
        resolve(webP.height === 2);
      };
      webP.src =
        "data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA";
    });
  }

  private async detectAVIFSupport(): Promise<boolean> {
    if (typeof window === "undefined") return false;

    return new Promise((resolve) => {
      const avif = new Image();
      avif.onload = avif.onerror = () => {
        resolve(avif.height === 2);
      };
      avif.src =
        "data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAIAAAACAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKCBgABogQEAwgMg8f8D///8WfhwB8+ErK42A=";
    });
  }

  private detectWebGLSupport(): boolean {
    if (typeof window === "undefined") return false;

    try {
      const canvas = document.createElement("canvas");
      const gl =
        canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
      return !!gl;
    } catch {
      return false;
    }
  }

  private detectServiceWorkerSupport(): boolean {
    return typeof navigator !== "undefined" && "serviceWorker" in navigator;
  }

  private detectIntersectionObserverSupport(): boolean {
    return typeof window !== "undefined" && "IntersectionObserver" in window;
  }

  // Performance calculation
  private async calculatePerformanceScore(): Promise<number> {
    let score = 50; // Base score

    // Memory score (0-20 points)
    const memory = this.detectMemory();
    score += Math.min(memory * 5, 20);

    // CPU score (0-15 points)
    const cores = this.detectCores();
    score += Math.min(cores * 3, 15);

    // Network score (0-15 points)
    const effectiveType = this.detectEffectiveConnectionType();
    const networkScore =
      {
        "slow-2g": 0,
        "2g": 3,
        "3g": 8,
        "4g": 15,
      }[effectiveType] || 10;
    score += networkScore;

    // Performance timing score (0-10 points)
    if (typeof window !== "undefined" && "performance" in window) {
      try {
        const navigation = performance.getEntriesByType(
          "navigation"
        )[0] as PerformanceNavigationTiming;
        if (navigation) {
          const loadTime = navigation.loadEventEnd - navigation.fetchStart;
          if (loadTime < 1000) score += 10;
          else if (loadTime < 2000) score += 7;
          else if (loadTime < 3000) score += 4;
          else if (loadTime < 5000) score += 2;
        }
      } catch {
        // Ignore performance timing errors
      }
    }

    return Math.min(Math.max(score, 0), 100);
  }

  // Battery detection
  private async detectBatteryLevel(): Promise<number | undefined> {
    if (typeof navigator !== "undefined" && "getBattery" in navigator) {
      try {
        const battery = await (navigator as any).getBattery();
        return battery.level;
      } catch {
        return undefined;
      }
    }
    return undefined;
  }

  private async detectChargingStatus(): Promise<boolean | undefined> {
    if (typeof navigator !== "undefined" && "getBattery" in navigator) {
      try {
        const battery = await (navigator as any).getBattery();
        return battery.charging;
      } catch {
        return undefined;
      }
    }
    return undefined;
  }

  // User preference detection
  private detectReducedMotion(): boolean {
    if (typeof window === "undefined") return false;

    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  private detectHighContrast(): boolean {
    if (typeof window === "undefined") return false;

    return window.matchMedia("(prefers-contrast: high)").matches;
  }

  // Capability calculations
  private calculateAnimationCapability(
    capabilities: DeviceCapabilities
  ): boolean {
    return (
      capabilities.performanceScore > 40 &&
      !capabilities.reducedMotion &&
      !capabilities.saveData &&
      (capabilities.batteryLevel === undefined ||
        capabilities.batteryLevel > 0.2)
    );
  }

  private calculateHeavyComponentCapability(
    capabilities: DeviceCapabilities
  ): boolean {
    return (
      capabilities.performanceScore > 60 &&
      capabilities.memory >= 4 &&
      capabilities.cores >= 2 &&
      !capabilities.saveData
    );
  }

  private calculatePreloadCapability(
    capabilities: DeviceCapabilities
  ): boolean {
    return (
      capabilities.performanceScore > 50 &&
      capabilities.effectiveType !== "slow-2g" &&
      capabilities.effectiveType !== "2g" &&
      !capabilities.saveData &&
      (capabilities.batteryLevel === undefined ||
        capabilities.batteryLevel > 0.3)
    );
  }

  private calculateMaxConcurrentRequests(
    capabilities: DeviceCapabilities
  ): number {
    if (capabilities.performanceScore > 80) return 6;
    if (capabilities.performanceScore > 60) return 4;
    if (capabilities.performanceScore > 40) return 3;
    return 2;
  }

  /**
   * Get current capabilities (cached)
   */
  getCurrentCapabilities(): DeviceCapabilities | null {
    return this.capabilities;
  }

  /**
   * Get current config (cached)
   */
  getCurrentConfig(): AdaptiveLoadingConfig | null {
    return this.config;
  }

  /**
   * Reset cached capabilities (for testing or when conditions change)
   */
  resetCapabilities(): void {
    this.capabilities = null;
    this.config = null;
  }
}

// Export singleton instance
export const deviceCapabilitiesDetector =
  DeviceCapabilitiesDetector.getInstance();

/**
 * React hook for device capabilities
 */
export function useDeviceCapabilities() {
  const [capabilities, setCapabilities] =
    React.useState<DeviceCapabilities | null>(null);
  const [config, setConfig] = React.useState<AdaptiveLoadingConfig | null>(
    null
  );
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    let mounted = true;

    const detectCapabilities = async () => {
      try {
        const caps = await deviceCapabilitiesDetector.detectCapabilities();
        const conf = deviceCapabilitiesDetector.generateAdaptiveConfig(caps);

        if (mounted) {
          setCapabilities(caps);
          setConfig(conf);
          setIsLoading(false);
        }
      } catch (error) {
        console.error("Failed to detect device capabilities:", error);
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    detectCapabilities();

    return () => {
      mounted = false;
    };
  }, []);

  return {
    capabilities,
    config,
    isLoading,
    refresh: () => {
      deviceCapabilitiesDetector.resetCapabilities();
      setIsLoading(true);
      return deviceCapabilitiesDetector.detectCapabilities().then((caps) => {
        const conf = deviceCapabilitiesDetector.generateAdaptiveConfig(caps);
        setCapabilities(caps);
        setConfig(conf);
        setIsLoading(false);
        return { capabilities: caps, config: conf };
      });
    },
  };
}
