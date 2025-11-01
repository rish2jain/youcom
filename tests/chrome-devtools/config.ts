/**
 * Chrome DevTools MCP Test Configuration
 * 
 * Centralized configuration for all Chrome DevTools MCP tests
 */

export interface TestConfig {
  baseUrl: string;
  backendUrl: string;
  timeout: number;
  performance: {
    thresholds: {
      lcp: number;  // Largest Contentful Paint (ms)
      fid: number;  // First Input Delay (ms)
      cls: number;  // Cumulative Layout Shift
      fcp: number;  // First Contentful Paint (ms)
      tti: number;  // Time to Interactive (ms)
    };
  };
  testData: {
    watchlist: {
      competitor_name: string;
      keywords: string[];
      description: string;
    };
    impactCard: {
      competitor_name: string;
      keywords: string[];
    };
  };
}

export const TEST_CONFIG: TestConfig = {
  baseUrl: process.env.FRONTEND_URL || 'http://localhost:3456',
  backendUrl: process.env.BACKEND_URL || 'http://localhost:8765',
  timeout: 30000, // 30 seconds default timeout
  performance: {
    thresholds: {
      lcp: 2500,  // 2.5 seconds
      fid: 100,   // 100 milliseconds
      cls: 0.1,   // 0.1 score
      fcp: 1800,  // 1.8 seconds
      tti: 3500,  // 3.5 seconds
    },
  },
  testData: {
    watchlist: {
      competitor_name: 'TestCorp',
      keywords: ['AI', 'ML', 'SaaS'],
      description: 'Test competitor for automated testing',
    },
    impactCard: {
      competitor_name: 'TestCorp',
      keywords: ['AI', 'Machine Learning'],
    },
  },
};

export const TEST_PAGES = {
  dashboard: '/dashboard',
  research: '/research',
  analytics: '/analytics',
  settings: '/settings',
  integrations: '/integrations',
  monitoring: '/monitoring',
} as const;

export const API_ENDPOINTS = {
  health: '/api/health',
  watch: '/api/v1/watch',
  impact: '/api/v1/impact',
  impactGenerate: '/api/v1/impact/generate',
  metrics: '/api/v1/metrics/api-usage',
  research: '/api/v1/research/company',
} as const;

