/**
 * Device Capabilities Detection Tests
 */

import {
  DeviceCapabilitiesDetector,
  deviceCapabilitiesDetector,
} from "../device-capabilities";

// Mock browser APIs
const mockNavigator = {
  deviceMemory: 4,
  hardwareConcurrency: 4,
  connection: {
    effectiveType: "4g",
    downlink: 10,
    rtt: 100,
    saveData: false,
  },
  getBattery: jest.fn().mockResolvedValue({
    level: 0.8,
    charging: false,
  }),
};

const mockWindow = {
  matchMedia: jest.fn().mockReturnValue({
    matches: false,
  }),
  performance: {
    getEntriesByType: jest.fn().mockReturnValue([
      {
        name: "first-contentful-paint",
        startTime: 1000,
      },
    ]),
  },
  PerformanceObserver: jest.fn(),
  IntersectionObserver: jest.fn(),
};

// Mock canvas for WebGL detection
const mockCanvas = {
  getContext: jest.fn().mockReturnValue({}),
};

const mockDocument = {
  createElement: jest.fn().mockReturnValue(mockCanvas),
};

// Setup global mocks
Object.defineProperty(global, "navigator", {
  value: mockNavigator,
  writable: true,
});

Object.defineProperty(global, "window", {
  value: mockWindow,
  writable: true,
});

Object.defineProperty(global, "document", {
  value: mockDocument,
  writable: true,
});

describe("DeviceCapabilitiesDetector", () => {
  let detector: DeviceCapabilitiesDetector;

  beforeEach(() => {
    detector = DeviceCapabilitiesDetector.getInstance();
    detector.resetCapabilities();
    jest.clearAllMocks();
  });

  describe("Hardware Detection", () => {
    it("should detect device memory correctly", async () => {
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.memory).toBe(4);
    });

    it("should detect CPU cores correctly", async () => {
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.cores).toBe(4);
    });

    it("should detect GPU support", async () => {
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.gpu).toBe(true);
    });

    it("should fallback to defaults when APIs are unavailable", async () => {
      // Remove hardware APIs
      delete (global.navigator as any).deviceMemory;
      delete (global.navigator as any).hardwareConcurrency;

      const capabilities = await detector.detectCapabilities();
      expect(capabilities.memory).toBe(4); // Default for desktop
      expect(capabilities.cores).toBe(2); // Conservative default
    });
  });

  describe("Network Detection", () => {
    it("should detect network connection type", async () => {
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.effectiveType).toBe("4g");
      expect(capabilities.downlink).toBe(10);
      expect(capabilities.rtt).toBe(100);
      expect(capabilities.saveData).toBe(false);
    });

    it("should handle missing connection API", async () => {
      delete (global.navigator as any).connection;

      const capabilities = await detector.detectCapabilities();
      expect(capabilities.effectiveType).toBe("4g"); // Optimistic default
      expect(capabilities.downlink).toBe(10);
      expect(capabilities.rtt).toBe(100);
      expect(capabilities.saveData).toBe(false);
    });
  });

  describe("Browser Capabilities", () => {
    it("should detect WebGL support", async () => {
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.webgl).toBe(true);
    });

    it("should detect service worker support", async () => {
      (global.navigator as any).serviceWorker = {};
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.serviceWorker).toBe(true);
    });

    it("should detect intersection observer support", async () => {
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.intersectionObserver).toBe(true);
    });
  });

  describe("Performance Score Calculation", () => {
    it("should calculate performance score based on multiple factors", async () => {
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.performanceScore).toBeGreaterThan(50);
      expect(capabilities.performanceScore).toBeLessThanOrEqual(100);
    });

    it("should adjust score based on memory", async () => {
      // Test with low memory
      (global.navigator as any).deviceMemory = 1;
      detector.resetCapabilities();

      const lowMemoryCapabilities = await detector.detectCapabilities();

      // Test with high memory
      (global.navigator as any).deviceMemory = 8;
      detector.resetCapabilities();

      const highMemoryCapabilities = await detector.detectCapabilities();

      expect(highMemoryCapabilities.performanceScore).toBeGreaterThan(
        lowMemoryCapabilities.performanceScore
      );
    });

    it("should adjust score based on network speed", async () => {
      // Test with slow network
      (global.navigator as any).connection.effectiveType = "2g";
      detector.resetCapabilities();

      const slowNetworkCapabilities = await detector.detectCapabilities();

      // Test with fast network
      (global.navigator as any).connection.effectiveType = "4g";
      detector.resetCapabilities();

      const fastNetworkCapabilities = await detector.detectCapabilities();

      expect(fastNetworkCapabilities.performanceScore).toBeGreaterThan(
        slowNetworkCapabilities.performanceScore
      );
    });
  });

  describe("User Preferences", () => {
    it("should detect reduced motion preference", async () => {
      mockWindow.matchMedia.mockReturnValueOnce({ matches: true });

      const capabilities = await detector.detectCapabilities();
      expect(capabilities.reducedMotion).toBe(true);
    });

    it("should detect high contrast preference", async () => {
      mockWindow.matchMedia
        .mockReturnValueOnce({ matches: false }) // reduced motion
        .mockReturnValueOnce({ matches: true }); // high contrast

      const capabilities = await detector.detectCapabilities();
      expect(capabilities.highContrast).toBe(true);
    });
  });

  describe("Capability Calculations", () => {
    it("should determine animation capability correctly", async () => {
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.canHandleAnimations).toBe(true);
    });

    it("should disable animations for reduced motion", async () => {
      mockWindow.matchMedia.mockReturnValueOnce({ matches: true });
      detector.resetCapabilities();

      const capabilities = await detector.detectCapabilities();
      expect(capabilities.canHandleAnimations).toBe(false);
    });

    it("should determine heavy component capability", async () => {
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.canHandleHeavyComponents).toBe(true);
    });

    it("should determine preload capability", async () => {
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.shouldPreload).toBe(true);
    });

    it("should calculate max concurrent requests", async () => {
      const capabilities = await detector.detectCapabilities();
      expect(capabilities.maxConcurrentRequests).toBeGreaterThan(0);
      expect(capabilities.maxConcurrentRequests).toBeLessThanOrEqual(6);
    });
  });

  describe("Adaptive Configuration Generation", () => {
    it("should generate appropriate config for high-performance devices", async () => {
      // Mock high performance
      (global.navigator as any).deviceMemory = 8;
      (global.navigator as any).hardwareConcurrency = 8;
      (global.navigator as any).connection.effectiveType = "4g";
      detector.resetCapabilities();

      const capabilities = await detector.detectCapabilities();
      const config = detector.generateAdaptiveConfig(capabilities);

      expect(config.enableAnimations).toBe(true);
      expect(config.enableCodeSplitting).toBe(true);
      expect(config.prefetchStrategy).toBe("aggressive");
      expect(config.maxBundleSize).toBeGreaterThan(500000);
    });

    it("should generate conservative config for low-performance devices", async () => {
      // Mock low performance
      (global.navigator as any).deviceMemory = 1;
      (global.navigator as any).hardwareConcurrency = 1;
      (global.navigator as any).connection.effectiveType = "2g";
      (global.navigator as any).connection.saveData = true;
      detector.resetCapabilities();

      const capabilities = await detector.detectCapabilities();
      const config = detector.generateAdaptiveConfig(capabilities);

      expect(config.enableAnimations).toBe(false);
      expect(config.prefetchStrategy).toBe("disabled");
      expect(config.maxBundleSize).toBeLessThan(500000);
    });
  });

  describe("Caching and Persistence", () => {
    it("should cache capabilities after first detection", async () => {
      const capabilities1 = await detector.detectCapabilities();
      const capabilities2 = await detector.detectCapabilities();

      expect(capabilities1).toBe(capabilities2); // Same object reference
    });

    it("should reset capabilities when requested", async () => {
      await detector.detectCapabilities();
      detector.resetCapabilities();

      const newCapabilities = await detector.detectCapabilities();
      expect(newCapabilities).toBeDefined();
    });
  });

  describe("Error Handling", () => {
    it("should handle WebP detection errors gracefully", async () => {
      // Mock Image constructor to throw error
      const originalImage = global.Image;
      (global as any).Image = function () {
        throw new Error("Image creation failed");
      };

      const capabilities = await detector.detectCapabilities();
      expect(capabilities.webp).toBe(false);

      // Restore
      (global as any).Image = originalImage;
    });

    it("should handle battery API errors gracefully", async () => {
      mockNavigator.getBattery.mockRejectedValueOnce(
        new Error("Battery API failed")
      );

      const capabilities = await detector.detectCapabilities();
      expect(capabilities.batteryLevel).toBeUndefined();
      expect(capabilities.charging).toBeUndefined();
    });
  });
});
