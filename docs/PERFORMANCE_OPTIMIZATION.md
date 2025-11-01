# Performance Optimization Infrastructure

This document describes the performance monitoring and optimization infrastructure implemented for the Enterprise CIA frontend.

## Overview

The performance optimization infrastructure provides comprehensive monitoring, analysis, and validation of frontend performance metrics. It includes:

- **Performance Monitoring**: Real-time Core Web Vitals tracking
- **Bundle Analysis**: Detailed bundle size analysis and optimization recommendations
- **Performance Budgets**: Configurable performance budgets with CI/CD integration
- **Automated Validation**: CI/CD pipeline integration for performance regression detection

## Components

### 1. Performance Monitor (`lib/performance-monitor.ts`)

Tracks Core Web Vitals and provides performance metrics:

```typescript
import { performanceMonitor } from "@/lib/performance-monitor";

// Measure Core Web Vitals
const vitals = await performanceMonitor.measureCoreWebVitals();

// Generate performance report
const report = await performanceMonitor.generateReport();

// Validate against budgets
const validation = await performanceMonitor.validateBudgets();
```

**Metrics Tracked:**

- **LCP (Largest Contentful Paint)**: Time to render the largest content element
- **FID (First Input Delay)**: Time from first user interaction to browser response
- **CLS (Cumulative Layout Shift)**: Visual stability score
- **FCP (First Contentful Paint)**: Time to first content render
- **TTFB (Time to First Byte)**: Server response time
- **Bundle Size**: Total JavaScript bundle size
- **Load Time**: Complete page load time

### 2. Bundle Analyzer (`lib/bundle-analyzer.ts`)

Analyzes bundle composition and provides optimization recommendations:

```typescript
import { bundleAnalyzer } from "@/lib/bundle-analyzer";

// Analyze current bundles
const analysis = await bundleAnalyzer.analyzeBundles();

// Track bundle size over time
bundleAnalyzer.trackBundleSize(bundleSize, commitHash);

// Get bundle size trends
const trend = bundleAnalyzer.getBundleTrend(30); // Last 30 days
```

**Features:**

- Chunk size analysis
- Asset optimization recommendations
- Bundle size history tracking
- Dependency analysis
- Compression status monitoring

### 3. Performance Budgets (`lib/performance-budgets.ts`)

Configurable performance budgets with validation:

```typescript
import { performanceBudgetManager } from "@/lib/performance-budgets";

// Validate against environment-specific budgets
const result = await performanceBudgetManager.validateBudget(
  metrics,
  "production"
);

// Get CI/CD exit code
const exitCode = performanceBudgetManager.getCIExitCode(result);

// Generate CI report
const report = performanceBudgetManager.generateCIReport(result, "production");
```

**Budget Configuration:**

| Environment | Bundle Size | Load Time | LCP  | FID   | CLS  |
| ----------- | ----------- | --------- | ---- | ----- | ---- |
| Development | 1MB         | 5s        | 4s   | 300ms | 0.25 |
| Staging     | 750KB       | 4s        | 3s   | 200ms | 0.15 |
| Production  | 500KB       | 3s        | 2.5s | 100ms | 0.1  |

### 4. Performance Monitoring Dashboard

React component for visualizing performance metrics:

```typescript
import { PerformanceMonitoringDashboard } from "@/components/PerformanceMonitoringDashboard";

<PerformanceMonitoringDashboard
  environment="production"
  autoRefresh={true}
  refreshInterval={30000}
/>;
```

**Features:**

- Real-time metrics display
- Budget violation alerts
- Performance score calculation
- Trend analysis
- Optimization recommendations

### 5. React Hooks

Performance monitoring hooks for React components:

```typescript
import {
  usePerformanceMonitoring,
  useComponentPerformance,
} from "@/lib/hooks/usePerformanceMonitoring";

// Component-level monitoring
function MyComponent() {
  const { performanceScore, recommendations } = usePerformanceMonitoring({
    autoRefresh: true,
    environment: "production",
  });

  const { renderTime, renderCount } = useComponentPerformance("MyComponent");

  return <div>Performance Score: {performanceScore}</div>;
}
```

## Usage

### Development

1. **Start monitoring during development:**

```bash
npm run dev
```

2. **Access performance dashboard:**
   Navigate to `/monitoring` in your application to view real-time performance metrics.

3. **Check bundle analysis:**

```bash
npm run build
npm run perf:validate:dev
```

### CI/CD Integration

The performance budget validation is automatically run in CI/CD pipelines:

```bash
# Validate performance budgets
npm run perf:validate:prod

# Build with performance analysis
npm run build:analyze
```

**GitHub Actions Workflow:**

- Validates performance budgets on every PR
- Generates bundle analysis reports
- Runs Lighthouse CI for comprehensive performance testing
- Comments on PRs with performance results

### Performance Budget Enforcement

Performance budgets are enforced at build time:

1. **Critical violations** (>100% of budget): Build fails with exit code 1
2. **Warning violations** (80-100% of budget): Build succeeds with warnings
3. **Passing metrics** (<80% of budget): Build succeeds

### Monitoring in Production

1. **Real-time monitoring:**

```typescript
// Track page performance
const { trackPageView } = usePerformanceMonitoring();
trackPageView("dashboard");

// Track component render performance
const { measureRender } = usePerformanceMonitoring();
const endMeasure = measureRender("ImpactCard");
// ... component logic
endMeasure();
```

2. **Performance alerts:**
   The system automatically creates alerts for budget violations and stores them locally for review.

## Configuration

### Environment Variables

```bash
# Performance monitoring settings
NEXT_PUBLIC_PERFORMANCE_MONITORING=true
NEXT_PUBLIC_PERFORMANCE_ENVIRONMENT=production

# Performance budget webhook (optional)
PERFORMANCE_WEBHOOK_URL=https://your-webhook-url.com
```

### Next.js Configuration

The `next.config.js` includes performance optimizations:

- Bundle splitting with size limits
- Tree shaking enabled
- Image optimization with modern formats
- Compression enabled
- Cache headers for static assets

### Custom Budget Configuration

Override default budgets by updating the configuration:

```typescript
import { performanceBudgetManager } from "@/lib/performance-budgets";

performanceBudgetManager.updateBudgets({
  production: {
    maxBundleSize: 400000, // 400KB - stricter limit
    maxLCP: 2000, // 2s - stricter LCP
    // ... other metrics
  },
});
```

## Performance Optimization Strategies

### 1. Code Splitting

- **Route-based splitting**: Separate bundles for each major route
- **Component-based splitting**: Lazy load heavy components
- **Vendor splitting**: Separate third-party libraries

### 2. Bundle Optimization

- **Tree shaking**: Remove unused code
- **Minification**: Compress JavaScript and CSS
- **Compression**: Enable gzip/brotli compression

### 3. Asset Optimization

- **Image optimization**: WebP/AVIF formats with fallbacks
- **Font optimization**: Subset fonts and preload critical fonts
- **CSS optimization**: Critical CSS inlining

### 4. Caching Strategy

- **Static asset caching**: Long-term caching for immutable assets
- **API response caching**: Cache API responses with appropriate TTL
- **Service worker**: Offline functionality and cache management

## Troubleshooting

### Common Issues

1. **High bundle size:**

   - Check bundle analysis for large dependencies
   - Implement code splitting for heavy components
   - Remove unused dependencies

2. **Poor LCP scores:**

   - Preload critical resources
   - Optimize server response times
   - Use responsive images

3. **High CLS scores:**
   - Set explicit dimensions for images
   - Avoid inserting content above existing content
   - Use CSS aspect-ratio for dynamic content

### Debug Commands

```bash
# Analyze bundle composition
npm run build && ls -la .next/static/chunks/

# Check performance budget violations
npm run perf:validate:prod

# Generate detailed bundle report
npm install -g webpack-bundle-analyzer
npx webpack-bundle-analyzer .next/static/chunks/
```

## Monitoring and Alerts

### Performance Alerts

The system creates alerts for:

- Bundle size violations
- Core Web Vitals degradation
- Performance budget violations
- Trend analysis (increasing bundle sizes)

### Reporting

Performance reports are generated in multiple formats:

- **Markdown reports**: For CI/CD integration
- **JSON data**: For programmatic access
- **Dashboard UI**: For visual monitoring

## Best Practices

1. **Set realistic budgets**: Based on your user base and network conditions
2. **Monitor trends**: Track performance over time, not just point-in-time metrics
3. **Automate validation**: Integrate performance checks into CI/CD pipelines
4. **Regular reviews**: Review performance reports and optimization opportunities
5. **User-centric metrics**: Focus on metrics that impact user experience

## Future Enhancements

- **Real User Monitoring (RUM)**: Collect performance data from real users
- **Performance regression detection**: Automated detection of performance regressions
- **A/B testing integration**: Performance impact analysis for feature flags
- **Advanced analytics**: Machine learning-based performance optimization recommendations
