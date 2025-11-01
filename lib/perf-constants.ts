/**
 * Shared Performance Constants
 * Core Web Vitals thresholds based on Google's "Good" values
 */

export const CORE_WEB_VITALS_THRESHOLDS = {
  // Largest Contentful Paint - "Good" threshold
  LCP: 2500, // milliseconds

  // First Contentful Paint - "Good" threshold
  FCP: 1800, // milliseconds

  // Time to First Byte - "Good" threshold
  TTFB: 800, // milliseconds

  // First Input Delay - "Good" threshold
  FID: 100, // milliseconds

  // Cumulative Layout Shift - "Good" threshold
  CLS: 0.1, // score
} as const;

export const PERFORMANCE_BUDGETS = {
  // Bundle size limits
  INITIAL_BUNDLE_SIZE: 1024 * 1024, // 1MB
  TOTAL_BUNDLE_SIZE: 2 * 1024 * 1024, // 2MB

  // Load time limits
  LOAD_TIME: 3000, // 3 seconds

  // Cache performance
  CACHE_HIT_RATE: 80, // 80%
} as const;
