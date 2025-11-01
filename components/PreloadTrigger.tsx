"use client";

import React, { useEffect, useRef, ComponentType } from "react";
import { usePreloading } from "@/lib/preloading-strategies";

interface PreloadTriggerProps {
  children: React.ReactNode;
  componentName: string;
  importFn: () => Promise<{ default: ComponentType<any> }>;
  trigger?: "hover" | "viewport" | "immediate" | "idle";
  threshold?: number;
  delay?: number;
  className?: string;
}

/**
 * Component that triggers preloading based on user interaction
 */
export function PreloadTrigger({
  children,
  componentName,
  importFn,
  trigger = "hover",
  threshold = 0.1,
  delay = 0,
  className = "",
}: PreloadTriggerProps) {
  const elementRef = useRef<HTMLDivElement>(null);
  const {
    preloadImmediate,
    preloadOnHover,
    preloadOnViewport,
    preloadOnIdle,
    isPreloaded,
  } = usePreloading();

  useEffect(() => {
    if (!elementRef.current || isPreloaded(componentName)) return;

    let cleanup: (() => void) | undefined;

    const executePreload = () => {
      switch (trigger) {
        case "immediate":
          preloadImmediate(componentName, importFn);
          break;

        case "hover":
          cleanup = preloadOnHover(
            elementRef.current!,
            componentName,
            importFn
          );
          break;

        case "viewport":
          cleanup = preloadOnViewport(
            elementRef.current!,
            componentName,
            importFn,
            threshold
          );
          break;

        case "idle":
          preloadOnIdle(componentName, importFn);
          break;
      }
    };

    if (delay > 0) {
      const timer = setTimeout(executePreload, delay);
      return () => {
        clearTimeout(timer);
        cleanup?.();
      };
    } else {
      executePreload();
      return cleanup;
    }
  }, [
    componentName,
    importFn,
    trigger,
    threshold,
    delay,
    preloadImmediate,
    preloadOnHover,
    preloadOnViewport,
    preloadOnIdle,
    isPreloaded,
  ]);

  return (
    <div ref={elementRef} className={className}>
      {children}
    </div>
  );
}

/**
 * Higher-order component for automatic preloading
 */
export function withPreloading<P extends object>(
  Component: ComponentType<P>,
  preloadConfig: {
    componentName: string;
    importFn: () => Promise<{ default: ComponentType<any> }>;
    trigger?: "hover" | "viewport" | "immediate" | "idle";
    threshold?: number;
  }
) {
  const WrappedComponent = (props: P) => (
    <PreloadTrigger {...preloadConfig}>
      <Component {...props} />
    </PreloadTrigger>
  );

  WrappedComponent.displayName = `withPreloading(${
    Component.displayName || Component.name
  })`;

  return WrappedComponent;
}

/**
 * Specialized preload triggers for common use cases
 */
export function PreloadOnHover({
  children,
  componentName,
  importFn,
  className,
}: Omit<PreloadTriggerProps, "trigger">) {
  return (
    <PreloadTrigger
      trigger="hover"
      componentName={componentName}
      importFn={importFn}
      className={className}
    >
      {children}
    </PreloadTrigger>
  );
}

export function PreloadOnViewport({
  children,
  componentName,
  importFn,
  threshold = 0.1,
  className,
}: Omit<PreloadTriggerProps, "trigger">) {
  return (
    <PreloadTrigger
      trigger="viewport"
      componentName={componentName}
      importFn={importFn}
      threshold={threshold}
      className={className}
    >
      {children}
    </PreloadTrigger>
  );
}

export function PreloadImmediate({
  children,
  componentName,
  importFn,
  className,
}: Omit<PreloadTriggerProps, "trigger">) {
  return (
    <PreloadTrigger
      trigger="immediate"
      componentName={componentName}
      importFn={importFn}
      className={className}
    >
      {children}
    </PreloadTrigger>
  );
}
