/**
 * Adaptive Loading Manager Tests
 */

import React from "react";
import {
  AdaptiveLoadingManager,
  adaptiveLoadingManager,
} from "../adaptive-loading-manager";
import {
  DeviceCapabilities,
  AdaptiveLoadingConfig,
} from "../device-capabilities";

// Mock React
jest.mock("react", () => ({
  ...jest.requireActual("react"),
  createElement: jest.fn(),
  memo: jest.fn((component) => component),
}));

// Mock device capabilities detector
jest.mock("../device-capabilities", () => ({
  deviceCapabilitiesDetector: {
    detectCapabilities: jest.fn(),
    generateAdaptiveConfig: jest.fn(),
  },
}));

describe("AdaptiveLoadingManager", () => {
  let manager: AdaptiveLoadingManager;
  let mockCapabilities: DeviceCapabilities;
  let mockConfig: AdaptiveLoadingConfig;

  beforeEach(() => {
    manager = AdaptiveLoadingManager.getInstance();

    mockCapabilities = {
      memory: 4,
      cores: 4,
      gpu: true,
      connectionType: "4g",
      effectiveType: "4g",
      downlink: 10,
      rtt: 100,
      saveData: false,
      webp: true,
      avif: false,
      webgl: true,
      serviceWorker: true,
      intersectionObserver: true,
      performanceScore: 80,
      batteryLevel: 0.8,
      charging: false,
      reducedMotion: false,
      highContrast: false,
      canHandleAnimations: true,
      canHandleHeavyComponents: true,
      shouldPreload: true,
      maxConcurrentRequests: 4,
    };

    mockConfig = {
      lazyLoadThreshold: 200,
      preloadDistance: 1000,
      maxConcurrentLoads: 4,
      enableAnimations: true,
      animationDuration: 300,
      imageQuality: "high",
      imageFormat: "webp",
      enableCodeSplitting: true,
      prefetchStrategy: "aggressive",
      maxBundleSize: 800000,
      maxLoadTime: 2000,
    };

    // Reset manager state
    (manager as any).componentRegistry.clear();
    (manager as any).loadedComponents.clear();
    (manager as any).loadingPromises.clear();
    (manager as any).capabilities = null;
    (manager as any).config = null;
  });

  describe("Initialization", () => {
    it("should initialize with device capabilities", async () => {
      const mockDetectCapabilities = jest
        .fn()
        .mockResolvedValue(mockCapabilities);
      const mockGenerateConfig = jest.fn().mockReturnValue(mockConfig);

      require("../device-capabilities").deviceCapabilitiesDetector.detectCapabilities =
        mockDetectCapabilities;
      require("../device-capabilities").deviceCapabilitiesDetector.generateAdaptiveConfig =
        mockGenerateConfig;

      await manager.initialize();

      expect(mockDetectCapabilities).toHaveBeenCalled();
      expect(mockGenerateConfig).toHaveBeenCalledWith(mockCapabilities);
      expect(manager.getCapabilities()).toEqual(mockCapabilities);
      expect(manager.getConfig()).toEqual(mockConfig);
    });
  });

  describe("Component Registration and Loading", () => {
    const MockComponent = () =>
      React.createElement("div", {}, "Mock Component");
    const MockFallback = () => React.createElement("div", {}, "Mock Fallback");

    beforeEach(async () => {
      // Initialize manager
      (manager as any).capabilities = mockCapabilities;
      (manager as any).config = mockConfig;
    });

    it("should register components correctly", () => {
      manager.registerComponent("test-component", {
        component: MockComponent,
        fallback: MockFallback,
        minPerformanceScore: 50,
      });

      const registry = (manager as any).componentRegistry;
      expect(registry.has("test-component")).toBe(true);
      expect(registry.get("test-component").component).toBe(MockComponent);
    });

    it("should load full component when requirements are met", async () => {
      manager.registerComponent("test-component", {
        component: MockComponent,
        fallback: MockFallback,
        minPerformanceScore: 50,
      });

      const loadedComponent = await manager.loadComponent("test-component");
      expect(loadedComponent).toBe(MockComponent);
    });

    it("should load fallback when requirements are not met", async () => {
      manager.registerComponent("test-component", {
        component: MockComponent,
        fallback: MockFallback,
        minPerformanceScore: 90, // Higher than mock performance score
      });

      const loadedComponent = await manager.loadComponent("test-component");
      expect(loadedComponent).toBe(MockFallback);
    });

    it("should create minimal fallback when no fallback is provided", async () => {
      manager.registerComponent("test-component", {
        component: MockComponent,
        minPerformanceScore: 90,
      });

      const loadedComponent = await manager.loadComponent("test-component");
      expect(typeof loadedComponent).toBe("function");
    });

    it("should cache loaded components", async () => {
      manager.registerComponent("test-component", {
        component: MockComponent,
        fallback: MockFallback,
      });

      const component1 = await manager.loadComponent("test-component");
      const component2 = await manager.loadComponent("test-component");

      expect(component1).toBe(component2);
    });

    it("should handle loading errors gracefully", async () => {
      const ErrorComponent = () => {
        throw new Error("Component loading failed");
      };

      manager.registerComponent("error-component", {
        component: ErrorComponent,
        fallback: MockFallback,
      });

      const loadedComponent = await manager.loadComponent("error-component");
      expect(loadedComponent).toBe(MockFallback);
    });
  });

  describe("Requirement Checking", () => {
    beforeEach(async () => {
      (manager as any).capabilities = mockCapabilities;
      (manager as any).config = mockConfig;
    });

    it("should check performance score requirements", () => {
      const shouldLoad = (manager as any).shouldLoadFullComponent(
        { component: () => {}, minPerformanceScore: 70 },
        mockCapabilities,
        mockConfig
      );
      expect(shouldLoad).toBe(true);

      const shouldNotLoad = (manager as any).shouldLoadFullComponent(
        { component: () => {}, minPerformanceScore: 90 },
        mockCapabilities,
        mockConfig
      );
      expect(shouldNotLoad).toBe(false);
    });

    it("should check feature requirements", () => {
      const shouldLoad = (manager as any).shouldLoadFullComponent(
        { component: () => {}, requiresFeatures: ["webgl", "serviceWorker"] },
        mockCapabilities,
        mockConfig
      );
      expect(shouldLoad).toBe(true);

      const shouldNotLoad = (manager as any).shouldLoadFullComponent(
        { component: () => {}, requiresFeatures: ["avif"] }, // Not supported in mock
        mockCapabilities,
        mockConfig
      );
      expect(shouldNotLoad).toBe(false);
    });

    it("should check network requirements", () => {
      const shouldLoad = (manager as any).shouldLoadFullComponent(
        { component: () => {}, networkRequirement: "3g" },
        mockCapabilities,
        mockConfig
      );
      expect(shouldLoad).toBe(true);

      const shouldNotLoad = (manager as any).shouldLoadFullComponent(
        { component: () => {}, networkRequirement: "wifi" },
        { ...mockCapabilities, connectionType: "4g" },
        mockConfig
      );
      expect(shouldNotLoad).toBe(false);
    });

    it("should respect save data preference", () => {
      const shouldNotLoad = (manager as any).shouldLoadFullComponent(
        { component: () => {} },
        { ...mockCapabilities, saveData: true },
        mockConfig
      );
      expect(shouldNotLoad).toBe(false);
    });

    it("should respect low battery conditions", () => {
      const shouldNotLoad = (manager as any).shouldLoadFullComponent(
        { component: () => {} },
        { ...mockCapabilities, batteryLevel: 0.1, charging: false },
        mockConfig
      );
      expect(shouldNotLoad).toBe(false);
    });
  });

  describe("Adaptive Configurations", () => {
    beforeEach(() => {
      (manager as any).capabilities = mockCapabilities;
      (manager as any).config = mockConfig;
    });

    it("should provide adaptive image props", () => {
      const imageProps = manager.getAdaptiveImageProps(
        "test.jpg",
        "Test image",
        {
          priority: true,
          quality: 85,
        }
      );

      expect(imageProps.src).toBe("test.jpg");
      expect(imageProps.alt).toBe("Test image");
      expect(imageProps.loading).toBe("eager"); // Priority image
      expect(imageProps.quality).toBe(85);
    });

    it("should provide adaptive animation props", () => {
      const animationProps = manager.getAdaptiveAnimationProps();

      expect(animationProps.enableAnimations).toBe(true);
      expect(animationProps.duration).toBe(300);
      expect(animationProps.easing).toBe("cubic-bezier(0.4, 0, 0.2, 1)");
    });

    it("should provide adaptive list configuration", () => {
      const listConfig = manager.getAdaptiveListConfig(100);

      expect(listConfig.initialItems).toBe(50);
      expect(listConfig.enableVirtualization).toBe(false); // 100 items, threshold is 100
      expect(listConfig.batchSize).toBe(25);
    });

    it("should adjust list config for large item counts", () => {
      const listConfig = manager.getAdaptiveListConfig(200);

      expect(listConfig.enableVirtualization).toBe(true); // Above threshold
    });

    it("should provide adaptive timeouts", () => {
      const timeouts = manager.getAdaptiveTimeouts();

      expect(timeouts.apiTimeout).toBeGreaterThan(0);
      expect(timeouts.debounceDelay).toBeGreaterThan(0);
      expect(timeouts.animationTimeout).toBe(300);
    });
  });

  describe("Feature Enablement", () => {
    beforeEach(() => {
      (manager as any).capabilities = mockCapabilities;
      (manager as any).config = mockConfig;
    });

    it("should enable features when requirements are met", () => {
      const shouldEnable = manager.shouldEnableFeature("test-feature", {
        minPerformanceScore: 70,
        requiresFeatures: ["webgl"],
      });

      expect(shouldEnable).toBe(true);
    });

    it("should disable features when requirements are not met", () => {
      const shouldEnable = manager.shouldEnableFeature("test-feature", {
        minPerformanceScore: 90,
      });

      expect(shouldEnable).toBe(false);
    });
  });

  describe("Error Handling", () => {
    it("should handle unregistered components", async () => {
      await expect(manager.loadComponent("non-existent")).rejects.toThrow(
        "Component non-existent not registered"
      );
    });

    it("should handle initialization without capabilities", () => {
      const imageProps = manager.getAdaptiveImageProps("test.jpg", "Test");
      expect(imageProps.loading).toBe("lazy"); // Default fallback
    });
  });

  describe("Singleton Pattern", () => {
    it("should return the same instance", () => {
      const instance1 = AdaptiveLoadingManager.getInstance();
      const instance2 = AdaptiveLoadingManager.getInstance();

      expect(instance1).toBe(instance2);
    });
  });
});
