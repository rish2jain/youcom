/**
 * Feature Registry
 * Defines and registers advanced features for progressive loading
 */

import React from "react";
import { FeatureDefinition } from "./progressive-feature-loader";

/**
 * Advanced chart features
 */
export const advancedChartFeatures: FeatureDefinition[] = [
  {
    name: "advanced-charts",
    description:
      "Interactive charts with animations and advanced visualizations",
    priority: "enhancement",
    requirements: {
      minPerformanceScore: 60,
      minMemory: 2,
      requiresFeatures: ["webgl"],
      networkRequirement: "3g",
      batteryRequirement: "medium",
    },
    loader: () =>
      import("recharts").then((module) => module.ResponsiveContainer),
    fallback: React.lazy(() =>
      import("../components/fallbacks/ChartFallback").then((module) => ({
        default: module.SimpleChartFallback,
      }))
    ),
  },
  {
    name: "3d-charts",
    description: "3D charts and visualizations using WebGL",
    priority: "optional",
    requirements: {
      minPerformanceScore: 80,
      minMemory: 4,
      minCores: 4,
      requiresFeatures: ["webgl"],
      networkRequirement: "4g",
      batteryRequirement: "high",
    },
    loader: () => Promise.resolve(() => null), // Three.js not installed
    dependencies: ["advanced-charts"],
  },
  {
    name: "real-time-charts",
    description: "Real-time updating charts with WebSocket integration",
    priority: "important",
    requirements: {
      minPerformanceScore: 50,
      minMemory: 2,
      networkRequirement: "3g",
    },
    loader: () =>
      import("../components/LiveMetricsDashboard").then(
        (module) => module.LiveMetricsDashboard
      ),
    dependencies: ["advanced-charts"],
  },
];

/**
 * Animation and interaction features
 */
export const animationFeatures: FeatureDefinition[] = [
  {
    name: "smooth-animations",
    description: "Smooth CSS and JavaScript animations",
    priority: "enhancement",
    requirements: {
      minPerformanceScore: 50,
      batteryRequirement: "medium",
    },
    loader: () => Promise.resolve(() => null), // Framer Motion not installed
  },
  {
    name: "complex-animations",
    description: "Complex animations and transitions",
    priority: "optional",
    requirements: {
      minPerformanceScore: 70,
      minMemory: 2,
      batteryRequirement: "high",
    },
    loader: () => Promise.resolve(() => null), // Lottie not installed
    dependencies: ["smooth-animations"],
  },
  {
    name: "gesture-controls",
    description: "Touch and gesture-based interactions",
    priority: "enhancement",
    requirements: {
      minPerformanceScore: 60,
    },
    loader: () => Promise.resolve(() => null), // Use-gesture not installed
  },
];

/**
 * Real-time and collaboration features
 */
export const collaborationFeatures: FeatureDefinition[] = [
  {
    name: "real-time-collaboration",
    description: "Real-time collaborative features with WebSocket",
    priority: "important",
    requirements: {
      minPerformanceScore: 40,
      networkRequirement: "3g",
    },
    loader: () => import("socket.io-client").then((module) => module.io),
  },
  {
    name: "video-calls",
    description: "Video calling and screen sharing",
    priority: "optional",
    requirements: {
      minPerformanceScore: 80,
      minMemory: 4,
      minCores: 4,
      networkRequirement: "4g",
      batteryRequirement: "high",
    },
    loader: () => Promise.resolve(() => null), // WebRTC adapter not installed
    dependencies: ["real-time-collaboration"],
  },
  {
    name: "voice-commands",
    description: "Voice recognition and commands",
    priority: "optional",
    requirements: {
      minPerformanceScore: 70,
      minMemory: 2,
      requiresFeatures: ["serviceWorker"],
      batteryRequirement: "medium",
    },
    loader: () => {
      if (typeof window === "undefined") {
        return Promise.resolve(null);
      }

      const SpeechRecognition =
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition;

      return Promise.resolve(SpeechRecognition || null);
    },
  },
];

/**
 * Advanced UI features
 */
export const advancedUIFeatures: FeatureDefinition[] = [
  // Temporarily disabled to fix build issues
  /*
  {
    name: "virtual-scrolling",
    description: "Virtual scrolling for large lists",
    priority: "enhancement",
    requirements: {
      minPerformanceScore: 50,
      minMemory: 2,
    },
    loader: () => import("react-window").then((module) => module.FixedSizeList),
  },
  {
    name: "drag-and-drop",
    description: "Advanced drag and drop interactions",
    priority: "enhancement",
    requirements: {
      minPerformanceScore: 60,
    },
    loader: () =>
      import("react-beautiful-dnd").then((module) => module.DragDropContext),
  },
  {
    name: "rich-text-editor",
    description: "Rich text editing capabilities",
    priority: "optional",
    requirements: {
      minPerformanceScore: 70,
      minMemory: 2,
      networkRequirement: "3g",
    },
    loader: () => import("@tiptap/react").then((module) => module.useEditor),
  },
  {
    name: "code-editor",
    description: "Advanced code editing with syntax highlighting",
    priority: "optional",
    requirements: {
      minPerformanceScore: 80,
      minMemory: 4,
      networkRequirement: "3g",
    },
    loader: () =>
      import("@monaco-editor/react").then((module) => module.default),
  },
  */
];

/**
 * Performance and analytics features
 */
export const analyticsFeatures: FeatureDefinition[] = [
  {
    name: "performance-monitoring",
    description: "Real-time performance monitoring and analytics",
    priority: "important",
    requirements: {
      minPerformanceScore: 40,
    },
    loader: () =>
      import("../lib/performance-monitor").then(
        (module) => module.PerformanceMonitor
      ),
  },
  {
    name: "user-analytics",
    description: "User behavior tracking and analytics",
    priority: "enhancement",
    requirements: {
      minPerformanceScore: 30,
      networkRequirement: "any",
    },
    loader: () =>
      import("../lib/usage-tracker").then((module) => module.getUsageTracker),
  },
  {
    name: "error-tracking",
    description: "Advanced error tracking and reporting",
    priority: "important",
    requirements: {
      minPerformanceScore: 30,
    },
    loader: () => Promise.resolve(() => null), // Sentry not installed
  },
];

/**
 * AI and ML features
 */
export const aiFeatures: FeatureDefinition[] = [
  {
    name: "ai-suggestions",
    description: "AI-powered suggestions and recommendations",
    priority: "enhancement",
    requirements: {
      minPerformanceScore: 60,
      minMemory: 2,
      networkRequirement: "3g",
    },
    loader: () =>
      import("../components/ActionRecommendations").then(
        (module) => module.default
      ),
  },
  {
    name: "natural-language-search",
    description: "Natural language search and query processing",
    priority: "optional",
    requirements: {
      minPerformanceScore: 70,
      minMemory: 4,
      networkRequirement: "4g",
    },
    loader: () => Promise.resolve(() => null), // Fuse.js not installed
  },
  {
    name: "predictive-analytics",
    description: "Predictive analytics and forecasting",
    priority: "optional",
    requirements: {
      minPerformanceScore: 80,
      minMemory: 4,
      minCores: 4,
      networkRequirement: "4g",
      batteryRequirement: "high",
    },
    loader: () =>
      import("../components/PredictiveAnalytics").then(
        (module) => module.PredictiveAnalytics
      ),
  },
];

/**
 * Export and sharing features
 */
export const exportFeatures: FeatureDefinition[] = [
  {
    name: "pdf-export",
    description: "PDF generation and export",
    priority: "enhancement",
    requirements: {
      minPerformanceScore: 50,
      minMemory: 2,
    },
    loader: () => import("jspdf").then((module) => module.jsPDF),
  },
  {
    name: "excel-export",
    description: "Excel file generation and export",
    priority: "enhancement",
    requirements: {
      minPerformanceScore: 60,
      minMemory: 2,
    },
    loader: () => Promise.resolve(() => null), // XLSX not installed
  },
  {
    name: "image-export",
    description: "High-quality image export of charts and dashboards",
    priority: "enhancement",
    requirements: {
      minPerformanceScore: 50,
      requiresFeatures: ["webgl"],
    },
    loader: () => import("html2canvas").then((module) => module.default),
  },
];

/**
 * All feature definitions grouped by category
 */
export const allFeatures = {
  charts: advancedChartFeatures,
  // Temporarily disabled to fix build issues
  // animations: animationFeatures,
  // collaboration: collaborationFeatures,
  // ui: advancedUIFeatures,
  // analytics: analyticsFeatures,
  // ai: aiFeatures,
  // export: exportFeatures,
};

/**
 * Get all features as a flat array
 */
export function getAllFeatures(): FeatureDefinition[] {
  return Object.values(allFeatures).flat();
}

/**
 * Get features by priority
 */
export function getFeaturesByPriority(
  priority: FeatureDefinition["priority"]
): FeatureDefinition[] {
  return getAllFeatures().filter((feature) => feature.priority === priority);
}

/**
 * Get features by category
 */
export function getFeaturesByCategory(
  category: keyof typeof allFeatures
): FeatureDefinition[] {
  return allFeatures[category] || [];
}

/**
 * Create feature definition helper
 */
export function createFeature(
  name: string,
  description: string,
  loader: () => Promise<any>,
  options: Partial<
    Omit<FeatureDefinition, "name" | "description" | "loader">
  > = {}
): FeatureDefinition {
  return {
    name,
    description,
    priority: "enhancement",
    requirements: {},
    loader,
    ...options,
  };
}

/**
 * Feature presets for different device types
 */
export const featurePresets = {
  desktop: {
    name: "desktop",
    description: "Full feature set for desktop devices",
    features: getAllFeatures(),
  },
  tablet: {
    name: "tablet",
    description: "Optimized feature set for tablets",
    features: getAllFeatures().filter(
      (f) =>
        f.priority !== "optional" ||
        (f.requirements.minPerformanceScore || 0) <= 70
    ),
  },
  mobile: {
    name: "mobile",
    description: "Essential features for mobile devices",
    features: getAllFeatures().filter(
      (f) =>
        (f.priority && ["critical", "important"].includes(f.priority)) ||
        (f.priority === "enhancement" &&
          (f.requirements.minPerformanceScore || 0) <= 50)
    ),
  },
  minimal: {
    name: "minimal",
    description: "Critical features only for low-end devices",
    features: getAllFeatures().filter(
      (f) => f.priority && f.priority === "critical"
    ),
  },
};

/**
 * Get feature preset by name
 */
export function getFeaturePreset(
  presetName: keyof typeof featurePresets
): FeatureDefinition[] {
  return featurePresets[presetName]?.features || [];
}
