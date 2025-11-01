/**
 * Progressive Feature Loader Tests
 */

import {
  ProgressiveFeatureLoader,
  progressiveFeatureLoader,
  FeatureDefinition,
} from "../progressive-feature-loader";
import {
  DeviceCapabilities,
  AdaptiveLoadingConfig,
} from "../device-capabilities";

// Mock performance API
Object.defineProperty(global, "performance", {
  value: {
    now: jest.fn(() => Date.now()),
  },
  writable: true,
});

// Mock window for events
const mockWindow = {
  dispatchEvent: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
};

Object.defineProperty(global, "window", {
  value: mockWindow,
  writable: true,
});

describe("ProgressiveFeatureLoader", () => {
  let loader: ProgressiveFeatureLoader;
  let mockCapabilities: DeviceCapabilities;
  let mockConfig: AdaptiveLoadingConfig;

  beforeEach(() => {
    loader = ProgressiveFeatureLoader.getInstance();

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

    // Reset loader state
    (loader as any).features.clear();
    (loader as any).loadedFeatures.clear();
    (loader as any).loadingPromises.clear();
    (loader as any).capabilities = null;
    (loader as any).config = null;
    (loader as any).loadingStrategy = null;
    (loader as any).loadQueue = [];
    (loader as any).isProcessingQueue = false;

    // Reset mocks
    jest.clearAllMocks();
  });

  describe("Initialization", () => {
    it("should initialize with capabilities and config", async () => {
      await loader.initialize(mockCapabilities, mockConfig);

      expect((loader as any).capabilities).toBe(mockCapabilities);
      expect((loader as any).config).toBe(mockConfig);
      expect((loader as any).loadingStrategy).toBeDefined();
    });

    it("should determine aggressive strategy for high-performance devices", async () => {
      await loader.initialize(mockCapabilities, mockConfig);

      const strategy = (loader as any).loadingStrategy;
      expect(strategy.name).toBe("aggressive");
      expect(strategy.maxConcurrentLoads).toBe(4);
      expect(strategy.loadDelay).toBe(100);
    });

    it("should determine conservative strategy for low-performance devices", async () => {
      const lowCapabilities = {
        ...mockCapabilities,
        performanceScore: 45,
        effectiveType: "3g" as const,
      };

      await loader.initialize(lowCapabilities, mockConfig);

      const strategy = (loader as any).loadingStrategy;
      expect(strategy.name).toBe("conservative");
      expect(strategy.maxConcurrentLoads).toBe(1);
      expect(strategy.loadDelay).toBe(500);
    });

    it("should determine minimal strategy for very low-performance devices", async () => {
      const veryLowCapabilities = {
        ...mockCapabilities,
        performanceScore: 30,
        effectiveType: "2g" as const,
        batteryLevel: 0.1,
        charging: false,
      };

      await loader.initialize(veryLowCapabilities, mockConfig);

      const strategy = (loader as any).loadingStrategy;
      expect(strategy.name).toBe("minimal");
      expect(strategy.loadOrder).toEqual(["critical"]);
    });
  });

  describe("Feature Registration", () => {
    const mockFeature: FeatureDefinition = {
      name: "test-feature",
      description: "Test feature",
      priority: "enhancement",
      requirements: {
        minPerformanceScore: 50,
      },
      loader: jest.fn().mockResolvedValue(() => "MockComponent"),
    };

    it("should register single feature", () => {
      loader.registerFeature(mockFeature);

      const features = (loader as any).features;
      expect(features.has("test-feature")).toBe(true);
      expect(features.get("test-feature")).toBe(mockFeature);
    });

    it("should register multiple features", () => {
      const features = [
        mockFeature,
        {
          ...mockFeature,
          name: "test-feature-2",
        },
      ];

      loader.registerFeatures(features);

      const featureMap = (loader as any).features;
      expect(featureMap.size).toBe(2);
      expect(featureMap.has("test-feature")).toBe(true);
      expect(featureMap.has("test-feature-2")).toBe(true);
    });
  });

  describe("Feature Loading", () => {
    const mockComponent = () => "MockComponent";
    const mockFeature: FeatureDefinition = {
      name: "test-feature",
      description: "Test feature",
      priority: "enhancement",
      requirements: {
        minPerformanceScore: 50,
      },
      loader: jest.fn().mockResolvedValue(mockComponent),
    };

    beforeEach(async () => {
      await loader.initialize(mockCapabilities, mockConfig);
      loader.registerFeature(mockFeature);
    });

    it("should load feature successfully", async () => {
      const result = await loader.loadFeature("test-feature");

      expect(result.loaded).toBe(true);
      expect(result.component).toBe(mockComponent);
      expect(result.feature).toBe(mockFeature);
      expect(result.loadTime).toBeGreaterThan(0);
      expect(mockFeature.loader).toHaveBeenCalled();
    });

    it("should cache loaded features", async () => {
      const result1 = await loader.loadFeature("test-feature");
      const result2 = await loader.loadFeature("test-feature");

      expect(result1).toBe(result2);
      expect(mockFeature.loader).toHaveBeenCalledTimes(1);
    });

    it("should handle loading errors", async () => {
      const errorFeature: FeatureDefinition = {
        name: "error-feature",
        description: "Error feature",
        priority: "enhancement",
        requirements: {},
        loader: jest.fn().mockRejectedValue(new Error("Loading failed")),
      };

      loader.registerFeature(errorFeature);

      const result = await loader.loadFeature("error-feature");

      expect(result.loaded).toBe(false);
      expect(result.error).toBeInstanceOf(Error);
      expect(result.error?.message).toBe("Loading failed");
    });

    it("should throw error for unregistered features", async () => {
      await expect(loader.loadFeature("non-existent")).rejects.toThrow(
        "Feature non-existent not registered"
      );
    });

    it("should dispatch load events", async () => {
      await loader.loadFeature("test-feature");

      expect(mockWindow.dispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "progressive-feature-loaded",
        })
      );
    });
  });

  describe("Feature Requirements Checking", () => {
    beforeEach(async () => {
      await loader.initialize(mockCapabilities, mockConfig);
    });

    it("should check performance score requirements", () => {
      const feature: FeatureDefinition = {
        name: "test-feature",
        description: "Test feature",
        priority: "enhancement",
        requirements: {
          minPerformanceScore: 70,
        },
        loader: jest.fn(),
      };

      const shouldLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldLoad).toBe(true);

      feature.requirements.minPerformanceScore = 90;
      const shouldNotLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldNotLoad).toBe(false);
    });

    it("should check memory requirements", () => {
      const feature: FeatureDefinition = {
        name: "test-feature",
        description: "Test feature",
        priority: "enhancement",
        requirements: {
          minMemory: 2,
        },
        loader: jest.fn(),
      };

      const shouldLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldLoad).toBe(true);

      feature.requirements.minMemory = 8;
      const shouldNotLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldNotLoad).toBe(false);
    });

    it("should check CPU core requirements", () => {
      const feature: FeatureDefinition = {
        name: "test-feature",
        description: "Test feature",
        priority: "enhancement",
        requirements: {
          minCores: 2,
        },
        loader: jest.fn(),
      };

      const shouldLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldLoad).toBe(true);

      feature.requirements.minCores = 8;
      const shouldNotLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldNotLoad).toBe(false);
    });

    it("should check feature requirements", () => {
      const feature: FeatureDefinition = {
        name: "test-feature",
        description: "Test feature",
        priority: "enhancement",
        requirements: {
          requiresFeatures: ["webgl", "serviceWorker"],
        },
        loader: jest.fn(),
      };

      const shouldLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldLoad).toBe(true);

      feature.requirements.requiresFeatures = ["avif"]; // Not supported
      const shouldNotLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldNotLoad).toBe(false);
    });

    it("should check network requirements", () => {
      const feature: FeatureDefinition = {
        name: "test-feature",
        description: "Test feature",
        priority: "enhancement",
        requirements: {
          networkRequirement: "3g",
        },
        loader: jest.fn(),
      };

      const shouldLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldLoad).toBe(true);

      feature.requirements.networkRequirement = "wifi";
      const shouldNotLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldNotLoad).toBe(false);
    });

    it("should check battery requirements", () => {
      const feature: FeatureDefinition = {
        name: "test-feature",
        description: "Test feature",
        priority: "enhancement",
        requirements: {
          batteryRequirement: "medium",
        },
        loader: jest.fn(),
      };

      const shouldLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldLoad).toBe(true);

      feature.requirements.batteryRequirement = "high";
      const shouldNotLoad = (loader as any).shouldLoadFeature(feature);
      expect(shouldNotLoad).toBe(false);
    });
  });

  describe("Progressive Loading Strategy", () => {
    beforeEach(async () => {
      await loader.initialize(mockCapabilities, mockConfig);
    });

    it("should build load queue based on priority and dependencies", () => {
      const features: FeatureDefinition[] = [
        {
          name: "feature-a",
          description: "Feature A",
          priority: "critical",
          requirements: {},
          loader: jest.fn(),
        },
        {
          name: "feature-b",
          description: "Feature B",
          priority: "important",
          requirements: {},
          loader: jest.fn(),
          dependencies: ["feature-a"],
        },
        {
          name: "feature-c",
          description: "Feature C",
          priority: "enhancement",
          requirements: {},
          loader: jest.fn(),
        },
      ];

      loader.registerFeatures(features);

      const queue = (loader as any).buildLoadQueue();

      expect(queue).toContain("feature-a");
      expect(queue).toContain("feature-b");
      expect(queue).toContain("feature-c");

      // feature-a should come before feature-b due to dependency
      const indexA = queue.indexOf("feature-a");
      const indexB = queue.indexOf("feature-b");
      expect(indexA).toBeLessThan(indexB);
    });

    it("should respect loading strategy priorities", () => {
      const features: FeatureDefinition[] = [
        {
          name: "critical-feature",
          description: "Critical feature",
          priority: "critical",
          requirements: {},
          loader: jest.fn(),
        },
        {
          name: "optional-feature",
          description: "Optional feature",
          priority: "optional",
          requirements: {},
          loader: jest.fn(),
        },
      ];

      loader.registerFeatures(features);

      const queue = (loader as any).buildLoadQueue();

      // For aggressive strategy, both should be included
      expect(queue).toContain("critical-feature");
      expect(queue).toContain("optional-feature");
    });

    it("should filter features based on requirements", () => {
      const features: FeatureDefinition[] = [
        {
          name: "high-perf-feature",
          description: "High performance feature",
          priority: "enhancement",
          requirements: {
            minPerformanceScore: 90, // Higher than mock score
          },
          loader: jest.fn(),
        },
        {
          name: "low-perf-feature",
          description: "Low performance feature",
          priority: "enhancement",
          requirements: {
            minPerformanceScore: 50,
          },
          loader: jest.fn(),
        },
      ];

      loader.registerFeatures(features);

      const queue = (loader as any).buildLoadQueue();

      expect(queue).not.toContain("high-perf-feature");
      expect(queue).toContain("low-perf-feature");
    });
  });

  describe("Analytics and Monitoring", () => {
    beforeEach(async () => {
      await loader.initialize(mockCapabilities, mockConfig);
    });

    it("should provide loading analytics", async () => {
      const feature: FeatureDefinition = {
        name: "test-feature",
        description: "Test feature",
        priority: "enhancement",
        requirements: {},
        loader: jest.fn().mockResolvedValue(() => "Component"),
      };

      loader.registerFeature(feature);
      await loader.loadFeature("test-feature");

      const analytics = loader.getLoadingAnalytics();

      expect(analytics.totalFeatures).toBe(1);
      expect(analytics.loadedFeatures).toBe(1);
      expect(analytics.failedFeatures).toBe(0);
      expect(analytics.averageLoadTime).toBeGreaterThan(0);
      expect(analytics.strategy).toBeDefined();
    });

    it("should track failed features", async () => {
      const feature: FeatureDefinition = {
        name: "error-feature",
        description: "Error feature",
        priority: "enhancement",
        requirements: {},
        loader: jest.fn().mockRejectedValue(new Error("Failed")),
      };

      loader.registerFeature(feature);
      await loader.loadFeature("error-feature");

      const analytics = loader.getLoadingAnalytics();

      expect(analytics.failedFeatures).toBe(1);
      expect(analytics.loadedFeatures).toBe(0);
    });
  });

  describe("Feature Management", () => {
    beforeEach(async () => {
      await loader.initialize(mockCapabilities, mockConfig);
    });

    it("should get feature status", async () => {
      const feature: FeatureDefinition = {
        name: "test-feature",
        description: "Test feature",
        priority: "enhancement",
        requirements: {},
        loader: jest.fn().mockResolvedValue(() => "Component"),
      };

      loader.registerFeature(feature);

      // Before loading
      expect(loader.getFeatureStatus("test-feature")).toBeNull();

      // After loading
      await loader.loadFeature("test-feature");
      const status = loader.getFeatureStatus("test-feature");
      expect(status?.loaded).toBe(true);
    });

    it("should force load features bypassing capability checks", async () => {
      const feature: FeatureDefinition = {
        name: "high-req-feature",
        description: "High requirement feature",
        priority: "enhancement",
        requirements: {
          minPerformanceScore: 95, // Higher than mock score
        },
        loader: jest.fn().mockResolvedValue(() => "Component"),
      };

      loader.registerFeature(feature);

      const result = await loader.forceLoadFeature("high-req-feature");
      expect(result.loaded).toBe(true);
    });

    it("should unload features", async () => {
      const feature: FeatureDefinition = {
        name: "test-feature",
        description: "Test feature",
        priority: "enhancement",
        requirements: {},
        loader: jest.fn().mockResolvedValue(() => "Component"),
      };

      loader.registerFeature(feature);
      await loader.loadFeature("test-feature");

      expect(loader.getFeatureStatus("test-feature")).toBeDefined();

      loader.unloadFeature("test-feature");

      expect(loader.getFeatureStatus("test-feature")).toBeNull();
      expect(mockWindow.dispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "progressive-feature-unloaded",
        })
      );
    });
  });

  describe("Singleton Pattern", () => {
    it("should return the same instance", () => {
      const instance1 = ProgressiveFeatureLoader.getInstance();
      const instance2 = ProgressiveFeatureLoader.getInstance();

      expect(instance1).toBe(instance2);
    });
  });
});
