/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765",
  },
  // Set the correct workspace root to silence warnings
  outputFileTracingRoot: __dirname,
  // Configure webpack to handle CSS properly and prevent source map 404s
  webpack: (config, { dev, isServer }) => {
    // Only modify CSS loader options to prevent source map 404s
    if (dev) {
      // Find CSS-related rules and disable source maps
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

    return config;
  },
  // Disable CSS optimization in development
  experimental: {
    optimizeCss: false,
  },
};

module.exports = nextConfig;
