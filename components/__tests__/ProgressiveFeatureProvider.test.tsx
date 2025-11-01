/**
 * Progressive Feature Provider Tests
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import {
  ProgressiveFeatureProvider,
  useProgressiveFeatureContext,
  ProgressiveFeature,
} from "../ProgressiveFeatureProvider";

// Mock the hooks and dependencies
jest.mock("../../lib/device-capabilities", () => ({
  useDeviceCapabilities: jest.fn(),
}));

jest.mock("../../lib/graceful-degradation", () => ({
  useGracefulDegradation: jest.fn(),
}));

jest.mock("../../lib/progressive-feature-loader", () => ({
  useProgressiveFeatures: jest.fn(),
  progressiveFeatureLoader: {
    registerFeatures: jest.fn(),
  },
}));

jest.mock("../../lib/feature-registry", () => ({
  getAllFeatures: jest.fn(() => []),
  getFeaturePreset: jest.fn(() => []),
}));

const mockUseDeviceCapabilities =
  require("../../lib/device-capabilities").useDeviceCapabilities;
const mockUseGracefulDegradation =
  require("../../lib/graceful-degradation").useGracefulDegradation;
const mockUseProgressiveFeatures =
  require("../../lib/progressive-feature-loader").useProgressiveFeatures;
const mockProgressiveFeatureLoader =
  require("../../lib/progressive-feature-loader").progressiveFeatureLoader;
const mockGetFeaturePreset =
  require("../../lib/feature-registry").getFeaturePreset;

describe("ProgressiveFeatureProvider", () => {
  const mockCapabilities = {
    performanceScore: 80,
    memory: 4,
    cores: 4,
    effectiveType: "4g",
    connectionType: "4g",
  };

  const mockConfig = {
    enableAnimations: true,
    maxBundleSize: 800000,
  };

  const mockDegradationLevel = {
    name: "full",
    features: {
      animations: true,
      interactivity: true,
    },
  };

  const mockProgressiveFeatures = {
    isInitialized: true,
    loadedFeatures: new Map(),
    loadFeature: jest.fn(),
    getFeatureComponent: jest.fn(),
    isFeatureLoaded: jest.fn(),
    startProgressiveLoading: jest.fn().mockResolvedValue(undefined),
    getAnalytics: jest.fn(() => ({ totalFeatures: 0, loadedFeatures: 0 })),
  };

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseDeviceCapabilities.mockReturnValue({
      capabilities: mockCapabilities,
      config: mockConfig,
      isLoading: false,
    });

    mockUseGracefulDegradation.mockReturnValue({
      degradationLevel: mockDegradationLevel,
    });

    mockUseProgressiveFeatures.mockReturnValue(mockProgressiveFeatures);

    mockGetFeaturePreset.mockReturnValue([
      {
        name: "test-feature",
        description: "Test feature",
        priority: "enhancement",
        requirements: {},
        loader: jest.fn(),
      },
    ]);
  });

  describe("Provider Initialization", () => {
    it("should render children when initialized", async () => {
      render(
        <ProgressiveFeatureProvider>
          <div data-testid="child">Child content</div>
        </ProgressiveFeatureProvider>
      );

      expect(screen.getByTestId("child")).toBeInTheDocument();
    });

    it("should register features based on auto preset", async () => {
      render(
        <ProgressiveFeatureProvider featurePreset="auto">
          <div>Content</div>
        </ProgressiveFeatureProvider>
      );

      await waitFor(() => {
        expect(mockGetFeaturePreset).toHaveBeenCalledWith("desktop");
        expect(
          mockProgressiveFeatureLoader.registerFeatures
        ).toHaveBeenCalled();
      });
    });

    it("should register features based on specific preset", async () => {
      render(
        <ProgressiveFeatureProvider featurePreset="mobile">
          <div>Content</div>
        </ProgressiveFeatureProvider>
      );

      await waitFor(() => {
        expect(mockGetFeaturePreset).toHaveBeenCalledWith("mobile");
      });
    });

    it("should start progressive loading automatically", async () => {
      render(
        <ProgressiveFeatureProvider autoStart={true}>
          <div>Content</div>
        </ProgressiveFeatureProvider>
      );

      await waitFor(() => {
        expect(
          mockProgressiveFeatures.startProgressiveLoading
        ).toHaveBeenCalled();
      });
    });

    it("should not start progressive loading when autoStart is false", async () => {
      render(
        <ProgressiveFeatureProvider autoStart={false}>
          <div>Content</div>
        </ProgressiveFeatureProvider>
      );

      await waitFor(() => {
        expect(
          mockProgressiveFeatures.startProgressiveLoading
        ).not.toHaveBeenCalled();
      });
    });

    it("should call onInitialized callback", async () => {
      const onInitialized = jest.fn();

      render(
        <ProgressiveFeatureProvider onInitialized={onInitialized}>
          <div>Content</div>
        </ProgressiveFeatureProvider>
      );

      await waitFor(() => {
        expect(onInitialized).toHaveBeenCalledWith({
          totalFeatures: 0,
          loadedFeatures: 0,
        });
      });
    });
  });

  describe("Context Value", () => {
    const TestComponent = () => {
      const context = useProgressiveFeatureContext();
      return (
        <div>
          <div data-testid="initialized">
            {context.isInitialized.toString()}
          </div>
          <div data-testid="performance-score">
            {context.capabilities?.performanceScore}
          </div>
        </div>
      );
    };

    it("should provide correct context values", () => {
      render(
        <ProgressiveFeatureProvider>
          <TestComponent />
        </ProgressiveFeatureProvider>
      );

      expect(screen.getByTestId("initialized")).toHaveTextContent("true");
      expect(screen.getByTestId("performance-score")).toHaveTextContent("80");
    });

    it("should throw error when used outside provider", () => {
      // Suppress console.error for this test
      const consoleSpy = jest
        .spyOn(console, "error")
        .mockImplementation(() => {});

      expect(() => {
        render(<TestComponent />);
      }).toThrow(
        "useProgressiveFeatureContext must be used within a ProgressiveFeatureProvider"
      );

      consoleSpy.mockRestore();
    });
  });

  describe("Feature Enablement Logic", () => {
    const TestComponent = () => {
      const { shouldEnableFeature } = useProgressiveFeatureContext();
      return (
        <div>
          <div data-testid="feature-enabled">
            {shouldEnableFeature("test-feature").toString()}
          </div>
        </div>
      );
    };

    it("should enable features when loaded and requirements met", () => {
      mockProgressiveFeatures.isFeatureLoaded.mockReturnValue(true);

      render(
        <ProgressiveFeatureProvider>
          <TestComponent />
        </ProgressiveFeatureProvider>
      );

      expect(screen.getByTestId("feature-enabled")).toHaveTextContent("true");
    });

    it("should disable features when not loaded", () => {
      mockProgressiveFeatures.isFeatureLoaded.mockReturnValue(false);

      render(
        <ProgressiveFeatureProvider>
          <TestComponent />
        </ProgressiveFeatureProvider>
      );

      expect(screen.getByTestId("feature-enabled")).toHaveTextContent("false");
    });

    it("should disable features based on degradation level", () => {
      mockProgressiveFeatures.isFeatureLoaded.mockReturnValue(true);
      mockUseGracefulDegradation.mockReturnValue({
        degradationLevel: {
          name: "basic",
          features: { animations: false },
        },
      });

      // Mock getAllFeatures to return a feature with optional priority
      require("../../lib/feature-registry").getAllFeatures.mockReturnValue([
        {
          name: "test-feature",
          priority: "optional",
        },
      ]);

      render(
        <ProgressiveFeatureProvider>
          <TestComponent />
        </ProgressiveFeatureProvider>
      );

      expect(screen.getByTestId("feature-enabled")).toHaveTextContent("false");
    });
  });

  describe("ProgressiveFeature Component", () => {
    const TestFeatureComponent = () => {
      return (
        <ProgressiveFeature
          name="test-feature"
          fallback={<div data-testid="fallback">Fallback content</div>}
          loadingComponent={<div data-testid="loading">Loading...</div>}
        >
          <div data-testid="feature-content">Feature content</div>
        </ProgressiveFeature>
      );
    };

    it("should show loading component when not initialized", () => {
      mockUseProgressiveFeatures.mockReturnValue({
        ...mockProgressiveFeatures,
        isInitialized: false,
      });

      render(
        <ProgressiveFeatureProvider>
          <TestFeatureComponent />
        </ProgressiveFeatureProvider>
      );

      expect(screen.getByTestId("loading")).toBeInTheDocument();
    });

    it("should show feature content when enabled", () => {
      mockProgressiveFeatures.isFeatureLoaded.mockReturnValue(true);

      render(
        <ProgressiveFeatureProvider>
          <TestFeatureComponent />
        </ProgressiveFeatureProvider>
      );

      expect(screen.getByTestId("feature-content")).toBeInTheDocument();
    });

    it("should show fallback when feature not enabled", () => {
      mockProgressiveFeatures.isFeatureLoaded.mockReturnValue(false);

      render(
        <ProgressiveFeatureProvider>
          <TestFeatureComponent />
        </ProgressiveFeatureProvider>
      );

      expect(screen.getByTestId("fallback")).toBeInTheDocument();
    });

    it("should show default loading when no loading component provided", () => {
      mockUseProgressiveFeatures.mockReturnValue({
        ...mockProgressiveFeatures,
        isInitialized: false,
      });

      render(
        <ProgressiveFeatureProvider>
          <ProgressiveFeature name="test-feature">
            <div>Content</div>
          </ProgressiveFeature>
        </ProgressiveFeatureProvider>
      );

      const { container } = render(
        <ProgressiveFeatureProvider>
          <ProgressiveFeature name="test-feature">
            <div>Content</div>
          </ProgressiveFeature>
        </ProgressiveFeatureProvider>
      );

      expect(
        container.querySelector(".progressive-loading")
      ).toBeInTheDocument();
    });
  });

  describe("Custom Features", () => {
    it("should register custom features", async () => {
      const customFeatures = [
        {
          name: "custom-feature",
          description: "Custom feature",
          priority: "enhancement" as const,
          requirements: {},
          loader: jest.fn(),
        },
      ];

      render(
        <ProgressiveFeatureProvider customFeatures={customFeatures}>
          <div>Content</div>
        </ProgressiveFeatureProvider>
      );

      await waitFor(() => {
        expect(
          mockProgressiveFeatureLoader.registerFeatures
        ).toHaveBeenCalledWith(expect.arrayContaining(customFeatures));
      });
    });
  });

  describe("Event Handling", () => {
    it("should handle feature loaded events", async () => {
      const onFeatureLoaded = jest.fn();

      // Mock window.addEventListener to capture the event handler
      const eventHandlers: { [key: string]: EventListener } = {};
      const mockAddEventListener = jest.fn((event, handler) => {
        eventHandlers[event] = handler;
      });

      Object.defineProperty(window, "addEventListener", {
        value: mockAddEventListener,
        writable: true,
      });

      render(
        <ProgressiveFeatureProvider onFeatureLoaded={onFeatureLoaded}>
          <div>Content</div>
        </ProgressiveFeatureProvider>
      );

      // Simulate feature loaded event
      const mockEvent = new CustomEvent("progressive-feature-loaded", {
        detail: {
          feature: { name: "test-feature" },
          loaded: true,
        },
      });

      if (eventHandlers["progressive-feature-loaded"]) {
        eventHandlers["progressive-feature-loaded"](mockEvent);
      }

      expect(onFeatureLoaded).toHaveBeenCalledWith("test-feature", {
        feature: { name: "test-feature" },
        loaded: true,
      });
    });
  });

  describe("Performance Score Based Preset Selection", () => {
    it("should select tablet preset for medium performance", async () => {
      mockUseDeviceCapabilities.mockReturnValue({
        capabilities: { ...mockCapabilities, performanceScore: 65 },
        config: mockConfig,
        isLoading: false,
      });

      render(
        <ProgressiveFeatureProvider featurePreset="auto">
          <div>Content</div>
        </ProgressiveFeatureProvider>
      );

      await waitFor(() => {
        expect(mockGetFeaturePreset).toHaveBeenCalledWith("tablet");
      });
    });

    it("should select mobile preset for low performance", async () => {
      mockUseDeviceCapabilities.mockReturnValue({
        capabilities: { ...mockCapabilities, performanceScore: 45 },
        config: mockConfig,
        isLoading: false,
      });

      render(
        <ProgressiveFeatureProvider featurePreset="auto">
          <div>Content</div>
        </ProgressiveFeatureProvider>
      );

      await waitFor(() => {
        expect(mockGetFeaturePreset).toHaveBeenCalledWith("mobile");
      });
    });

    it("should select minimal preset for very low performance", async () => {
      mockUseDeviceCapabilities.mockReturnValue({
        capabilities: { ...mockCapabilities, performanceScore: 30 },
        config: mockConfig,
        isLoading: false,
      });

      render(
        <ProgressiveFeatureProvider featurePreset="auto">
          <div>Content</div>
        </ProgressiveFeatureProvider>
      );

      await waitFor(() => {
        expect(mockGetFeaturePreset).toHaveBeenCalledWith("minimal");
      });
    });
  });
});
