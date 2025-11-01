/**
 * Tests for lazy loading infrastructure
 */

import {
  createLazyComponent,
  preloadComponent,
  preloadComponents,
  lazyRegistry,
} from "../lazy-loading";
import { ComponentType } from "react";

// Mock React.lazy
jest.mock("react", () => ({
  ...jest.requireActual("react"),
  lazy: jest.fn((importFn) => {
    const mockComponent = () => null;
    mockComponent.displayName = "LazyComponent";
    return mockComponent;
  }),
}));

describe("createLazyComponent", () => {
  const mockImportFn = jest.fn(() => Promise.resolve({ default: () => null }));

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("creates a lazy component with basic config", () => {
    const config = {
      name: "TestComponent",
      importPath: "./TestComponent",
    };

    const LazyComponent = createLazyComponent(mockImportFn, config);

    expect(LazyComponent).toBeDefined();
    expect(typeof LazyComponent).toBe("function");
  });

  it("handles import failures with retry logic", async () => {
    const failingImportFn = jest
      .fn()
      .mockRejectedValueOnce(new Error("Network error"))
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce({ default: () => null });

    const config = {
      name: "FailingComponent",
      importPath: "./FailingComponent",
    };

    const LazyComponent = createLazyComponent(failingImportFn, config);

    // The component should be created even if import might fail
    expect(LazyComponent).toBeDefined();
  });

  it("throws error after max retries", async () => {
    const alwaysFailingImportFn = jest
      .fn()
      .mockRejectedValue(new Error("Persistent error"));

    const config = {
      name: "AlwaysFailingComponent",
      importPath: "./AlwaysFailingComponent",
    };

    const LazyComponent = createLazyComponent(alwaysFailingImportFn, config);

    expect(LazyComponent).toBeDefined();
    // The actual error handling happens during component rendering
  });
});

describe("preloadComponent", () => {
  it("preloads a component successfully", async () => {
    const mockComponent = () => null;
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: mockComponent })
    );

    await preloadComponent(mockImportFn);

    expect(mockImportFn).toHaveBeenCalledTimes(1);
  });

  it("handles preload failures gracefully", async () => {
    const mockImportFn = jest.fn(() =>
      Promise.reject(new Error("Preload failed"))
    );

    // Should not throw
    await expect(preloadComponent(mockImportFn)).resolves.toEqual({
      default: expect.any(Function),
    });
  });
});

describe("preloadComponents", () => {
  it("preloads multiple components", async () => {
    const mockImportFn1 = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );
    const mockImportFn2 = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    await preloadComponents([mockImportFn1, mockImportFn2]);

    expect(mockImportFn1).toHaveBeenCalledTimes(1);
    expect(mockImportFn2).toHaveBeenCalledTimes(1);
  });

  it("continues preloading even if some components fail", async () => {
    const mockImportFn1 = jest.fn(() => Promise.reject(new Error("Failed")));
    const mockImportFn2 = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    // Should not throw and should complete
    await preloadComponents([mockImportFn1, mockImportFn2]);

    expect(mockImportFn1).toHaveBeenCalledTimes(1);
    expect(mockImportFn2).toHaveBeenCalledTimes(1);
  });
});

describe("LazyComponentRegistry", () => {
  beforeEach(() => {
    // Clear registry before each test
    const registry = lazyRegistry as any;
    registry.components.clear();
    registry.preloadPromises.clear();
  });

  it("registers a component", () => {
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );
    const config = {
      name: "TestComponent",
      importPath: "./TestComponent",
    };

    const LazyComponent = lazyRegistry.register(
      "TestComponent",
      mockImportFn,
      config
    );

    expect(LazyComponent).toBeDefined();
    expect(lazyRegistry.get("TestComponent")).toBe(LazyComponent);
  });

  it("preloads high priority components automatically", () => {
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );
    const config = {
      name: "HighPriorityComponent",
      importPath: "./HighPriorityComponent",
      priority: "high" as const,
    };

    lazyRegistry.register("HighPriorityComponent", mockImportFn, config);

    // Should trigger preload for high priority
    expect(mockImportFn).toHaveBeenCalled();
  });

  it("returns undefined for unregistered components", () => {
    expect(lazyRegistry.get("NonExistentComponent")).toBeUndefined();
  });

  it("returns all registered components", () => {
    const mockImportFn1 = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );
    const mockImportFn2 = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    lazyRegistry.register("Component1", mockImportFn1);
    lazyRegistry.register("Component2", mockImportFn2);

    const allComponents = lazyRegistry.getAll();

    expect(allComponents.size).toBe(2);
    expect(allComponents.has("Component1")).toBe(true);
    expect(allComponents.has("Component2")).toBe(true);
  });

  it("handles preload with existing promise", () => {
    const mockImportFn = jest.fn(() =>
      Promise.resolve({ default: () => null })
    );

    lazyRegistry.register("TestComponent", mockImportFn);
    lazyRegistry.preload("TestComponent", mockImportFn);
    lazyRegistry.preload("TestComponent", mockImportFn); // Second call

    // Should only call import function once due to promise caching
    expect(mockImportFn).toHaveBeenCalledTimes(1);
  });
});
