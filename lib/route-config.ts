/**
 * Route-based code splitting configuration
 * Defines dynamic imports and loading strategies for all major application routes
 */

import { ComponentType } from "react";

export interface RouteConfig {
  path: string;
  component: () => Promise<{ default: ComponentType<any> }>;
  preload?: boolean;
  priority?: "high" | "medium" | "low";
  dependencies?: string[];
}

// Route-specific dynamic imports with optimized loading
export const routeConfigs: Record<string, RouteConfig> = {
  dashboard: {
    path: "/dashboard",
    component: () => import("@/app/dashboard/page"),
    preload: true,
    priority: "high",
    dependencies: ["common-ui"],
  },
  research: {
    path: "/research",
    component: () => import("@/app/research/page"),
    preload: false,
    priority: "medium",
    dependencies: ["company-research", "common-ui"],
  },
  analytics: {
    path: "/analytics",
    component: () => import("@/app/analytics/page"),
    preload: false,
    priority: "medium",
    dependencies: ["charts", "analytics-components"],
  },
  monitoring: {
    path: "/monitoring",
    component: () => import("@/app/monitoring/page"),
    preload: false,
    priority: "medium",
    dependencies: ["watchlist", "common-ui"],
  },
  integrations: {
    path: "/integrations",
    component: () => import("@/app/integrations/page"),
    preload: false,
    priority: "low",
    dependencies: ["integration-components"],
  },
  settings: {
    path: "/settings",
    component: () => import("@/app/settings/page"),
    preload: false,
    priority: "low",
    dependencies: ["settings-components"],
  },
  "api-showcase": {
    path: "/api-showcase",
    component: () => import("@/app/api-showcase/page"),
    preload: false,
    priority: "low",
    dependencies: ["demo-components"],
  },
  demo: {
    path: "/demo",
    component: () => import("@/app/demo/page"),
    preload: false,
    priority: "low",
    dependencies: ["demo-components"],
  },
};

// Navigation patterns for intelligent prefetching
export const navigationPatterns = {
  dashboard: ["research", "monitoring", "analytics"],
  research: ["dashboard", "monitoring"],
  monitoring: ["dashboard", "research"],
  analytics: ["dashboard", "monitoring"],
  integrations: ["settings"],
  settings: ["integrations"],
};

// Preload critical routes based on user behavior
export const preloadRoute = async (routeKey: string): Promise<void> => {
  const config = routeConfigs[routeKey];
  if (!config) return;

  try {
    await config.component();
  } catch (error) {
    console.warn(`Failed to preload route ${routeKey}:`, error);
  }
};

// Preload likely next routes based on current route
export const preloadLikelyRoutes = async (
  currentRoute: string
): Promise<void> => {
  const likelyRoutes =
    navigationPatterns[currentRoute as keyof typeof navigationPatterns] || [];

  // Preload high-priority routes first
  const highPriorityRoutes = likelyRoutes.filter(
    (route) => routeConfigs[route]?.priority === "high"
  );

  for (const route of highPriorityRoutes) {
    await preloadRoute(route);
  }

  // Preload medium-priority routes with delay
  const mediumPriorityRoutes = likelyRoutes.filter(
    (route) => routeConfigs[route]?.priority === "medium"
  );

  setTimeout(() => {
    mediumPriorityRoutes.forEach((route) => preloadRoute(route));
  }, 1000);
};

// Get route key from pathname
export const getRouteKey = (pathname: string): string => {
  if (pathname === "/" || pathname === "/dashboard") return "dashboard";
  const segments = pathname.split("/").filter(Boolean);
  return segments[0] || "dashboard";
};
