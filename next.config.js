/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765",
  },
  // Set the correct workspace root to silence warnings
  outputFileTracingRoot: __dirname,

  // Performance optimization settings
  experimental: {
    optimizeCss: true, // Re-enabled with critical CSS optimization
    optimizePackageImports: [
      "lucide-react",
      "recharts",
      "@radix-ui/react-dialog",
    ],
  },

  // Configure webpack for performance optimization
  webpack: (config, { dev, isServer, webpack }) => {
    // Only modify CSS loader options to prevent source map 404s in development
    if (dev) {
      config.module.rules.forEach((rule) => {
        if (rule.use && Array.isArray(rule.use)) {
          rule.use.forEach((useItem) => {
            if (useItem.loader && useItem.loader.includes("css-loader")) {
              if (useItem.options) {
                useItem.options.sourceMap = false;
              }
            }
          });
        }
      });
    }

    // Production optimizations
    if (!dev && !isServer) {
      // Advanced bundle splitting configuration with size limits
      config.optimization.splitChunks = {
        chunks: "all",
        minSize: 20000,
        maxSize: 200000,
        minChunks: 1,
        maxAsyncRequests: 30,
        maxInitialRequests: 30,
        enforceSizeThreshold: 50000,
        cacheGroups: {
          // React core bundle (highest priority)
          react: {
            test: /[\\/]node_modules[\\/](react|react-dom|scheduler)[\\/]/,
            name: "react",
            chunks: "all",
            priority: 30,
            enforce: true,
            maxSize: 150000,
          },
          // Next.js framework bundle
          nextjs: {
            test: /[\\/]node_modules[\\/]next[\\/]/,
            name: "nextjs",
            chunks: "all",
            priority: 25,
            maxSize: 200000,
          },
          // Chart libraries (heavy dependencies)
          charts: {
            test: /[\\/]node_modules[\\/](recharts|d3|chart\.js|victory)[\\/]/,
            name: "charts",
            chunks: "all",
            priority: 20,
            maxSize: 250000,
          },
          // UI component libraries
          ui: {
            test: /[\\/]node_modules[\\/](@radix-ui|@headlessui|lucide-react)[\\/]/,
            name: "ui",
            chunks: "all",
            priority: 18,
            maxSize: 150000,
          },
          // Utility libraries
          utils: {
            test: /[\\/]node_modules[\\/](lodash|date-fns|clsx|class-variance-authority)[\\/]/,
            name: "utils",
            chunks: "all",
            priority: 16,
            maxSize: 100000,
          },
          // Vendor libraries (remaining node_modules)
          vendors: {
            test: /[\\/]node_modules[\\/]/,
            name: "vendors",
            chunks: "all",
            maxSize: 200000,
            priority: 10,
          },
          // Shared component optimization
          "shared-critical": {
            test: /[\\/]components[\\/](LoadingSkeleton|LazyComponentErrorBoundary|ErrorBoundary)[\\/]/,
            name: "shared-critical",
            chunks: "all",
            priority: 22,
            enforce: true,
            maxSize: 50000,
          },
          "shared-high": {
            test: /[\\/]components[\\/](NotificationSystem|Header|Sidebar|Toast)[\\/]/,
            name: "shared-high",
            chunks: "all",
            priority: 19,
            minChunks: 2,
            maxSize: 80000,
          },
          "shared-common": {
            test: /[\\/]components[\\/]/,
            name: "shared-common",
            chunks: "all",
            priority: 15,
            minChunks: 3,
            maxSize: 100000,
          },
          // Route-specific chunks with size limits
          dashboard: {
            test: /[\\/](dashboard|ImpactCard|WatchList)[\\/]/,
            name: "dashboard",
            chunks: "all",
            priority: 12,
            maxSize: 150000,
          },
          research: {
            test: /[\\/](research|CompanyResearch|SourceCitations)[\\/]/,
            name: "research",
            chunks: "all",
            priority: 12,
            maxSize: 150000,
          },
          analytics: {
            test: /[\\/](analytics|EnhancedAnalytics|PredictiveAnalytics)[\\/]/,
            name: "analytics",
            chunks: "all",
            priority: 12,
            maxSize: 150000,
          },
          monitoring: {
            test: /[\\/](monitoring|PerformanceMonitor|LiveMetrics)[\\/]/,
            name: "monitoring",
            chunks: "all",
            priority: 12,
            maxSize: 150000,
          },
          // Common components shared across routes
          common: {
            name: "common",
            minChunks: 2,
            chunks: "all",
            enforce: true,
            maxSize: 100000,
            priority: 8,
          },
        },
      };

      // Advanced tree shaking and dead code elimination
      config.optimization.usedExports = true;
      config.optimization.providedExports = true;
      config.optimization.innerGraph = true;
      config.optimization.mangleExports = true;

      // Module concatenation for better performance
      config.optimization.concatenateModules = true;

      // Add bundle analyzer for vendor bundle monitoring
      try {
        const { BundleAnalyzerPlugin } = require("./lib/bundle-analyzer");
        config.plugins.push(new BundleAnalyzerPlugin());
      } catch (error) {
        console.warn("Bundle analyzer not available:", error.message);
      }

      // Add module resolution optimizations
      config.resolve.alias = {
        ...config.resolve.alias,
        // Optimize React imports
        "react/jsx-runtime": require.resolve("react/jsx-runtime"),
        "react/jsx-dev-runtime": require.resolve("react/jsx-dev-runtime"),
      };

      // Optimize module resolution
      config.resolve.mainFields = ["browser", "module", "main"];
      config.resolve.extensions = [".js", ".jsx", ".ts", ".tsx", ".json"];
    }

    return config;
  },

  // Compression and optimization
  compress: true,

  // Performance budgets (for build-time warnings)
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },

  // Enhanced image optimization with next-generation formats
  images: {
    formats: ["image/webp", "image/avif"],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 31536000, // 1 year
    dangerouslyAllowSVG: true,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },

  // Headers for performance and vendor bundle caching
  async headers() {
    return [
      {
        // Long-term caching for static assets
        source: "/_next/static/(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
      {
        // Vendor bundle caching with long-term cache headers
        source: "/_next/static/chunks/vendors-(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
          {
            key: "X-Bundle-Type",
            value: "vendor",
          },
        ],
      },
      {
        // React bundle caching
        source: "/_next/static/chunks/react-(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
          {
            key: "X-Bundle-Type",
            value: "react-core",
          },
        ],
      },
      {
        // Chart library bundle caching
        source: "/_next/static/chunks/charts-(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
          {
            key: "X-Bundle-Type",
            value: "charts",
          },
        ],
      },
      {
        // UI component bundle caching
        source: "/_next/static/chunks/ui-(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
          {
            key: "X-Bundle-Type",
            value: "ui-components",
          },
        ],
      },
      {
        // Route-specific bundle caching
        source:
          "/_next/static/chunks/(dashboard|research|analytics|monitoring)-(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=2592000, immutable", // 30 days for route bundles
          },
          {
            key: "X-Bundle-Type",
            value: "route-specific",
          },
        ],
      },
      {
        // API response caching
        source: "/api/(.*)",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=300, s-maxage=300",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
