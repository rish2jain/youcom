/**
 * Chrome DevTools MCP Test Utilities
 * 
 * Helper functions for test implementations
 */

export interface TestResult {
  success: boolean;
  message: string;
  steps: string[];
  duration?: number;
  error?: string;
  data?: any;
}

export interface PerformanceMetrics {
  lcp?: number;
  fid?: number;
  cls?: number;
  fcp?: number;
  tti?: number;
}

export interface NetworkRequest {
  url: string;
  method: string;
  status: number;
  duration: number;
}

/**
 * Create a test result object
 */
export function createTestResult(
  success: boolean,
  message: string,
  steps: string[] = [],
  error?: string,
  data?: any,
  duration?: number
): TestResult {
  return {
    success,
    message,
    steps,
    error,
    data,
    duration,
  };
}

/**
 * Format duration in milliseconds to human-readable string
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

/**
 * Check if performance metrics meet thresholds
 */
export function checkPerformanceThresholds(
  metrics: PerformanceMetrics,
  thresholds: PerformanceMetrics
): { passed: boolean; failures: string[] } {
  const failures: string[] = [];

  if (metrics.lcp !== undefined && thresholds.lcp !== undefined) {
    if (metrics.lcp > thresholds.lcp) {
      failures.push(`LCP ${metrics.lcp}ms exceeds threshold ${thresholds.lcp}ms`);
    }
  }

  if (metrics.fid !== undefined && thresholds.fid !== undefined) {
    if (metrics.fid > thresholds.fid) {
      failures.push(`FID ${metrics.fid}ms exceeds threshold ${thresholds.fid}ms`);
    }
  }

  if (metrics.cls !== undefined && thresholds.cls !== undefined) {
    if (metrics.cls > thresholds.cls) {
      failures.push(`CLS ${metrics.cls} exceeds threshold ${thresholds.cls}`);
    }
  }

  if (metrics.fcp !== undefined && thresholds.fcp !== undefined) {
    if (metrics.fcp > thresholds.fcp) {
      failures.push(`FCP ${metrics.fcp}ms exceeds threshold ${thresholds.fcp}ms`);
    }
  }

  if (metrics.tti !== undefined && thresholds.tti !== undefined) {
    if (metrics.tti > thresholds.tti) {
      failures.push(`TTI ${metrics.tti}ms exceeds threshold ${thresholds.tti}ms`);
    }
  }

  return {
    passed: failures.length === 0,
    failures,
  };
}

/**
 * Validate network request status
 */
export function validateNetworkRequest(
  requests: any[],
  endpoint: string,
  expectedStatus: number = 200
): { found: boolean; valid: boolean; request?: any; error?: string } {
  const request = requests.find((req: any) => 
    req.url && req.url.includes(endpoint)
  );

  if (!request) {
    return {
      found: false,
      valid: false,
      error: `Request for ${endpoint} not found`,
    };
  }

  const valid = request.status === expectedStatus;
  
  return {
    found: true,
    valid,
    request,
    error: valid ? undefined : `Expected status ${expectedStatus}, got ${request.status}`,
  };
}

/**
 * Extract accessibility issues from snapshot
 */
export function extractAccessibilityIssues(snapshot: any[]): string[] {
  const issues: string[] = [];

  snapshot.forEach((element, index) => {
    // Check for missing labels on interactive elements
    const interactiveRoles = ['button', 'textbox', 'checkbox', 'radio', 'combobox', 'link'];
    if (
      interactiveRoles.includes(element.role) &&
      !element.label &&
      !element.name &&
      !element.value
    ) {
      issues.push(
        `Element at index ${index} (${element.role}) missing accessible label or name`
      );
    }

    // Check for images without alt text
    if (element.role === 'img' && !element.name && !element.label) {
      issues.push(`Image at index ${index} missing alt text`);
    }

    // Check for form inputs without labels
    if (
      (element.role === 'textbox' || element.role === 'combobox') &&
      !element.labeledBy
    ) {
      issues.push(`Form input at index ${index} missing label association`);
    }
  });

  return issues;
}

/**
 * Wait with timeout
 */
export function wait(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry a function with exponential backoff
 */
export async function retry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      if (i < maxRetries - 1) {
        await wait(delay * Math.pow(2, i));
      }
    }
  }

  throw lastError!;
}

