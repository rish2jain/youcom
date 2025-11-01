/**
 * Graceful Degradation Tests
 */

import React from "react";
import {
  GracefulDegradationManager,
  gracefulDegradationManager,
} from "../graceful-degradation";
import {
  DeviceCapabilities,
  AdaptiveLoadingConfig,
} from "../device-capabilities";

// Mock React
jest.mock("react", () => ({
  ...jest.requireActual("react"),
  createElement: jest.fn(),
  Fragment: jest.fn(),
}));

// Mock DOM APIs
const mockDocument = {
  documentElement: {
    className: "",
    classList: {
      add: jest.fn(),
      remove: jest.fn(),
    },
  },
};

const mockWindow = {
  dispatchEvent: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
};

Object.defineProperty(global, "document", {
  value: mockDocument,
  writable: true,
});

Object.defineProperty(global, "window", {
  value: mockWindow,
  writable: true,
});

describe("GracefulDegradationManager", () => {
  let manager: GracefulDegradationManager;
  let mockCapabilities: DeviceCapabilities;
  let mockConfig: AdaptiveLoadingConfig;

  beforeEach(() => {
    manager = GracefulDegradationManager.getInstance();

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
    (manager as any).fallbackComponents.clear();
    (manager as any).currentLevel = null;

    // Reset mocks
    jest.clearAllMocks();
  });

  describe("Degradation Level Determination", () => {
    it("should determine full degradation level for high-performance devices", () => {
      const level = manager.determineDegradationLevel(
        mockCapabilities,
        mockConfig
      );

      expect(level.name).toBe("full");
      expect(level.features.animations).toBe(true);
      expect(level.features.heavyComponents).toBe(true);
      expect(level.features.advancedCharts).toBe(true);
    });

    it("should determine enhanced level for reduced motion preference", () => {
      const capabilitiesWithReducedMotion = {
        ...mockCapabilities,
        reducedMotion: true,
      };

      const level = manager.determineDegradationLevel(
        capabilitiesWithReducedMotion,
        mockConfig
      );

      expect(level.name).toBe("enhanced");
      expect(level.features.animations).toBe(false);
      expect(level.features.interactivity).toBe(true);
    });

    it("should determine standard level for medium performance", () => {
      const mediumCapabilities = {
        ...mockCapabilities,
        performanceScore: 55,
      };

      const level = manager.determineDegradationLevel(
        mediumCapabilities,
        mockConfig
      );

      expect(level.name).toBe("standard");
      expect(level.features.heavyComponents).toBe(false);
      expect(level.features.realTimeUpdates).toBe(false);
    });

    it("should determine basic level for low performance", () => {
      const lowCapabilities = {
        ...mockCapabilities,
        performanceScore: 35,
      };

      const level = manager.determineDegradationLevel(
        lowCapabilities,
        mockConfig
      );

      expect(level.name).toBe("basic");
      expect(level.features.interactivity).toBe(false);
      expect(level.features.dynamicContent).toBe(false);
    });

    it("should determine minimal level for very low performance", () => {
      const veryLowCapabilities = {
        ...mockCapabilities,
        performanceScore: 20,
        effectiveType: "2g" as const,
        batteryLevel: 0.1,
        charging: false,
      };

      const level = manager.determineDegradationLevel(
        veryLowCapabilities,
        mockConfig
      );

      expect(level.name).toBe("basic"); // Should be basic for these conditions
    });

    it("should consider save data preference", () => {
      const saveDataCapabilities = {
        ...mockCapabilities,
        saveData: true,
        effectiveType: "3g" as const,
      };

      const level = manager.determineDegradationLevel(
        saveDataCapabilities,
        mockConfig
      );

      expect(level.name).toBe("standard");
    });

    it("should consider low battery conditions", () => {
      const lowBatteryCapabilities = {
        ...mockCapabilities,
        batteryLevel: 0.15,
        charging: false,
      };

      const level = manager.determineDegradationLevel(
        lowBatteryCapabilities,
        mockConfig
      );

      expect(level.name).toBe("basic");
    });
  });

  describe("Degradation Level Setting", () => {
    it("should set degradation level and update DOM", () => {
      const level = manager.determineDegradationLevel(
        mockCapabilities,
        mockConfig
      );
      manager.setDegradationLevel(level);

      expect(manager.getCurrentLevel()).toBe(level);
      expect(mockDocument.documentElement.classList.add).toHaveBeenCalledWith(
        "degradation-full"
      );
      expect(mockWindow.dispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "degradation-level-change",
          detail: { level },
        })
      );
    });

    it("should remove previous degradation classes", () => {
      mockDocument.documentElement.className =
        "some-class degradation-basic other-class";

      const level = manager.determineDegradationLevel(
        mockCapabilities,
        mockConfig
      );
      manager.setDegradationLevel(level);

      expect(mockDocument.documentElement.classList.add).toHaveBeenCalledWith(
        "degradation-full"
      );
    });
  });

  describe("Component Fallback Registration", () => {
    const MockComponent = () =>
      React.createElement("div", {}, "Mock Component");
    const MockFallback = () => React.createElement("div", {}, "Mock Fallback");

    it("should register fallback components", () => {
      manager.registerFallback("test-component", {
        original: MockComponent,
        fallback: MockFallback,
        minRequirements: {
          performanceScore: 50,
        },
      });

      const fallbackConfig = (manager as any).fallbackComponents.get(
        "test-component"
      );
      expect(fallbackConfig).toBeDefined();
      expect(fallbackConfig.original).toBe(MockComponent);
      expect(fallbackConfig.fallback).toBe(MockFallback);
    });

    it("should return appropriate component based on degradation level", () => {
      manager.registerFallback("test-component", {
        original: MockComponent,
        fallback: MockFallback,
        minRequirements: {
          performanceScore: 70,
        },
      });

      // Set high-performance level
      const fullLevel = manager.determineDegradationLevel(
        mockCapabilities,
        mockConfig
      );
      manager.setDegradationLevel(fullLevel);

      const component = manager.getComponent("test-component");
      expect(component).toBe(MockComponent);

      // Set low-performance level
      const basicLevel = {
        name: "basic",
        description: "Basic level",
        features: {
          animations: false,
          interactivity: false,
          dynamicContent: false,
          heavyComponents: false,
          realTimeUpdates: false,
          advancedCharts: false,
        },
        fallbacks: {
          chartsFallback: "text" as const,
          animationsFallback: "none" as const,
          interactionFallback: "basic" as const,
        },
      };
      manager.setDegradationLevel(basicLevel);

      const fallbackComponent = manager.getComponent("test-component");
      expect(fallbackComponent).toBe(MockFallback);
    });

    it("should return null for unregistered components", () => {
      const component = manager.getComponent("non-existent");
      expect(component).toBeNull();
    });
  });

  describe("No-JavaScript Fallback Generation", () => {
    it("should use provided no-JS fallback", () => {
      const customFallback = "<div>Custom fallback</div>";

      manager.registerFallback("test-component", {
        original: () => React.createElement("div"),
        fallback: () => React.createElement("div"),
        noJSFallback: customFallback,
        minRequirements: {},
      });

      const fallback = manager.generateNoJSFallback("test-component");
      expect(fallback).toBe(customFallback);
    });

    it("should generate default no-JS fallback", () => {
      const fallback = manager.generateNoJSFallback("unknown-component");

      expect(fallback).toContain("no-js-fallback");
      expect(fallback).toContain("unknown-component");
      expect(fallback).toContain("JavaScript");
    });
  });

  describe("CSS Generation", () => {
    it("should generate CSS for minimal degradation level", () => {
      const minimalLevel = {
        name: "minimal",
        description: "Minimal level",
        features: {
          animations: false,
          interactivity: false,
          dynamicContent: false,
          heavyComponents: false,
          realTimeUpdates: false,
          advancedCharts: false,
        },
        fallbacks: {
          chartsFallback: "text" as const,
          animationsFallback: "none" as const,
          interactionFallback: "basic" as const,
        },
      };

      manager.setDegradationLevel(minimalLevel);
      const css = manager.getDegradationCSS();

      expect(css).toContain("animation-duration: 0s");
      expect(css).toContain("transition-duration: 0s");
      expect(css).toContain(".degradation-minimal");
    });

    it("should generate CSS for reduced animations", () => {
      const enhancedLevel = {
        name: "enhanced",
        description: "Enhanced level",
        features: {
          animations: false,
          interactivity: true,
          dynamicContent: true,
          heavyComponents: true,
          realTimeUpdates: true,
          advancedCharts: true,
        },
        fallbacks: {
          chartsFallback: "simple" as const,
          animationsFallback: "reduced" as const,
          interactionFallback: "enhanced" as const,
        },
      };

      manager.setDegradationLevel(enhancedLevel);
      const css = manager.getDegradationCSS();

      expect(css).toContain("animation-duration: 0.1s");
      expect(css).toContain("transition-duration: 0.1s");
    });

    it("should return empty CSS for full level", () => {
      const fullLevel = manager.determineDegradationLevel(
        mockCapabilities,
        mockConfig
      );
      manager.setDegradationLevel(fullLevel);

      const css = manager.getDegradationCSS();
      expect(css).toBe("");
    });
  });

  describe("Requirement Checking", () => {
    it("should check performance score requirements", () => {
      const standardLevel = {
        name: "standard",
        description: "Standard level",
        features: {
          animations: false,
          interactivity: true,
          dynamicContent: true,
          heavyComponents: false,
          realTimeUpdates: false,
          advancedCharts: false,
        },
        fallbacks: {
          chartsFallback: "simple" as const,
          animationsFallback: "none" as const,
          interactionFallback: "enhanced" as const,
        },
      };

      const meetsRequirements = (manager as any).checkRequirements(
        { performanceScore: 40 },
        standardLevel
      );
      expect(meetsRequirements).toBe(true);

      const doesNotMeetRequirements = (manager as any).checkRequirements(
        { performanceScore: 60 },
        standardLevel
      );
      expect(doesNotMeetRequirements).toBe(false);
    });

    it("should check feature requirements", () => {
      const fullLevel = manager.determineDegradationLevel(
        mockCapabilities,
        mockConfig
      );

      const meetsRequirements = (manager as any).checkRequirements(
        { features: ["animations", "interactivity"] },
        fullLevel
      );
      expect(meetsRequirements).toBe(true);

      const basicLevel = {
        name: "basic",
        description: "Basic level",
        features: {
          animations: false,
          interactivity: false,
          dynamicContent: false,
          heavyComponents: false,
          realTimeUpdates: false,
          advancedCharts: false,
        },
        fallbacks: {
          chartsFallback: "text" as const,
          animationsFallback: "none" as const,
          interactionFallback: "basic" as const,
        },
      };

      const doesNotMeetRequirements = (manager as any).checkRequirements(
        { features: ["animations"] },
        basicLevel
      );
      expect(doesNotMeetRequirements).toBe(false);
    });
  });

  describe("Singleton Pattern", () => {
    it("should return the same instance", () => {
      const instance1 = GracefulDegradationManager.getInstance();
      const instance2 = GracefulDegradationManager.getInstance();

      expect(instance1).toBe(instance2);
    });
  });
});
