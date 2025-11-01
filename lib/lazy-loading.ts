/**
 * Lazy Loading Infrastructure
 * Provides utilities for React.lazy and Suspense with error handling
 */

import React, { ComponentType, LazyExoticComponent } from "react";

export interface LazyComponentConfig {
  name: string;
  importPath: string;
  preload?: boolean;
  priority?: "high" | "medium" | "low";
  fallback?: ComponentType;
}

export interface LazyLoadError extends Error {
  componentName: string;
  retryCount: number;
}

/**
 * Enhanced React.lazy wrapper with error handling and retry logic
 */
export function createLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  config: LazyComponentConfig
): LazyExoticComponent<T> {
  let retryCount = 0;
  const maxRetries = 3;

  const enhancedImportFn = async (): Promise<{ default: T }> => {
    try {
      const componentModule = await importFn();
      retryCount = 0; // Reset on success
      return componentModule;
    } catch (error) {
      retryCount++;

      const lazyError: LazyLoadError = new Error(
        `Failed to load component ${config.name} (attempt ${retryCount}/${maxRetries})`
      ) as LazyLoadError;
      lazyError.componentName = config.name;
      lazyError.retryCount = retryCount;

      if (retryCount < maxRetries) {
        // Exponential backoff retry
        const delay = Math.pow(2, retryCount) * 1000;
        await new Promise((resolve) => setTimeout(resolve, delay));
        return enhancedImportFn();
      }

      throw lazyError;
    }
  };

  return React.lazy(enhancedImportFn);
}

/**
 * Preload a lazy component
 */
export function preloadComponent(
  importFn: () => Promise<{ default: ComponentType<any> }>
): Promise<{ default: ComponentType<any> }> {
  return importFn();
}

/**
 * Batch preload multiple components
 */
export async function preloadComponents(
  components: Array<() => Promise<{ default: ComponentType<any> }>>
): Promise<void> {
  try {
    await Promise.all(components.map(preloadComponent));
  } catch (error) {
    console.warn("Some components failed to preload:", error);
  }
}

/**
 * Component registry for managing lazy loaded components
 */
class LazyComponentRegistry {
  private components = new Map<string, LazyExoticComponent<any>>();
  private preloadPromises = new Map<string, Promise<any>>();

  register<T extends ComponentType<any>>(
    name: string,
    importFn: () => Promise<{ default: T }>,
    config: Partial<LazyComponentConfig> = {}
  ): LazyExoticComponent<T> {
    const fullConfig: LazyComponentConfig = {
      name,
      importPath: name,
      priority: "medium",
      ...config,
    };

    const lazyComponent = createLazyComponent(importFn, fullConfig);
    this.components.set(name, lazyComponent);

    // Auto-preload high priority components
    if (fullConfig.preload || fullConfig.priority === "high") {
      this.preload(name, importFn);
    }

    return lazyComponent;
  }

  preload(
    name: string,
    importFn: () => Promise<{ default: ComponentType<any> }>
  ): void {
    if (!this.preloadPromises.has(name)) {
      const wrappedPromise = preloadComponent(importFn).catch((error) => {
        console.warn(`Failed to preload component ${name}:`, error);
        // Return undefined on error so the promise resolves
        return undefined;
      });
      this.preloadPromises.set(name, wrappedPromise);
    }
  }

  get(name: string): LazyExoticComponent<any> | undefined {
    return this.components.get(name);
  }

  getAll(): Map<string, LazyExoticComponent<any>> {
    return new Map(this.components);
  }
}

export const lazyRegistry = new LazyComponentRegistry();
