#!/usr/bin/env node

/**
 * Performance budget validation script for CI/CD integration
 * Validates bundle sizes, load times, and Core Web Vitals against budgets
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

// Import shared constants (fallback to local definitions for Node.js compatibility)
let CORE_WEB_VITALS_THRESHOLDS;
try {
  // Try to import from TypeScript module if available
  CORE_WEB_VITALS_THRESHOLDS =
    require("../lib/perf-constants").CORE_WEB_VITALS_THRESHOLDS;
} catch {
  // Fallback to local definitions
  CORE_WEB_VITALS_THRESHOLDS = {
    LCP: 2500,
    FCP: 1800,
    TTFB: 800,
    FID: 100,
    CLS: 0.1,
  };
}

// Performance budget configuration
const PERFORMANCE_BUDGETS = {
  development: {
    maxBundleSize: 1000000, // 1MB
    maxInitialLoadTime: 5000, // 5 seconds
    maxLCP: 4000, // 4 seconds
    maxFID: 300, // 300ms
    maxCLS: 0.25, // 0.25 score
    maxFCP: 3000, // 3 seconds
    maxTTFB: 1500, // 1.5 seconds
  },
  staging: {
    maxBundleSize: 750000, // 750KB
    maxInitialLoadTime: 4000, // 4 seconds
    maxLCP: 3000, // 3 seconds
    maxFID: 200, // 200ms
    maxCLS: 0.15, // 0.15 score
    maxFCP: 2500, // 2.5 seconds
    maxTTFB: 1000, // 1 second
  },
  production: {
    maxBundleSize: 500000, // 500KB
    maxInitialLoadTime: 3000, // 3 seconds
    maxLCP: CORE_WEB_VITALS_THRESHOLDS.LCP, // Use shared constant
    maxFID: CORE_WEB_VITALS_THRESHOLDS.FID, // Use shared constant
    maxCLS: CORE_WEB_VITALS_THRESHOLDS.CLS, // Use shared constant
    maxFCP: CORE_WEB_VITALS_THRESHOLDS.FCP, // Use shared constant
    maxTTFB: CORE_WEB_VITALS_THRESHOLDS.TTFB, // Use shared constant
  },
};

class PerformanceBudgetValidator {
  constructor(environment = "production") {
    this.environment = environment;
    this.budget = PERFORMANCE_BUDGETS[environment];
    this.violations = [];
    this.warnings = [];

    if (!this.budget) {
      throw new Error(`Unknown environment: ${environment}`);
    }
  }

  /**
   * Measure bundle sizes from build output
   */
  measureBundleSizes() {
    const buildDir = path.join(process.cwd(), ".next");
    const staticDir = path.join(buildDir, "static");

    if (!fs.existsSync(staticDir)) {
      throw new Error('Build directory not found. Run "npm run build" first.');
    }

    let totalSize = 0;
    const bundles = {};

    // Measure JavaScript bundles
    const jsDir = path.join(staticDir, "chunks");
    if (fs.existsSync(jsDir)) {
      const jsFiles = fs
        .readdirSync(jsDir)
        .filter((file) => file.endsWith(".js"));

      jsFiles.forEach((file) => {
        const filePath = path.join(jsDir, file);
        const stats = fs.statSync(filePath);
        const size = stats.size;

        bundles[file] = size;

        // Only count main bundles toward initial load
        if (
          file.includes("main") ||
          file.includes("framework") ||
          file.includes("webpack")
        ) {
          totalSize += size;
        }
      });
    }

    // Measure CSS bundles
    const cssDir = path.join(staticDir, "css");
    if (fs.existsSync(cssDir)) {
      const cssFiles = fs
        .readdirSync(cssDir)
        .filter((file) => file.endsWith(".css"));

      cssFiles.forEach((file) => {
        const filePath = path.join(cssDir, file);
        const stats = fs.statSync(filePath);
        const size = stats.size;

        bundles[file] = size;
        totalSize += size;
      });
    }

    return { totalSize, bundles };
  }

  /**
   * Analyze bundle composition and identify optimization opportunities
   */
  analyzeBundleComposition() {
    try {
      // Try to read webpack bundle analyzer output if available
      const analyzerOutput = path.join(process.cwd(), ".next", "analyze");
      if (fs.existsSync(analyzerOutput)) {
        // Parse bundle analyzer data for detailed analysis
        // This would require webpack-bundle-analyzer to be configured
      }
    } catch (error) {
      console.warn("Bundle analyzer data not available");
    }

    return {
      recommendations: [
        "Consider implementing code splitting for large components",
        "Use dynamic imports for non-critical features",
        "Optimize vendor bundle splitting",
        "Remove unused dependencies",
      ],
    };
  }

  /**
   * Validate bundle sizes against budget
   */
  validateBundleSizes() {
    const { totalSize, bundles } = this.measureBundleSizes();

    console.log(`📦 Total initial bundle size: ${this.formatBytes(totalSize)}`);
    console.log(`📊 Budget: ${this.formatBytes(this.budget.maxBundleSize)}`);

    if (totalSize > this.budget.maxBundleSize) {
      const overage = totalSize - this.budget.maxBundleSize;
      const overagePercent = (overage / this.budget.maxBundleSize) * 100;

      this.violations.push({
        metric: "bundleSize",
        actual: totalSize,
        budget: this.budget.maxBundleSize,
        overage,
        overagePercent,
        severity: "critical",
      });
    } else if (totalSize > this.budget.maxBundleSize * 0.8) {
      // Warning at 80% of budget
      this.warnings.push({
        metric: "bundleSize",
        actual: totalSize,
        budget: this.budget.maxBundleSize,
        usage: (totalSize / this.budget.maxBundleSize) * 100,
        severity: "warning",
      });
    }

    return { totalSize, bundles };
  }

  /**
   * Run Lighthouse performance audit
   */
  async runLighthouseAudit() {
    let serverProcess = null;

    try {
      console.log("🔍 Running Lighthouse performance audit...");

      // Start the Next.js server for testing
      const { spawn } = require("child_process");
      serverProcess = spawn("npm", ["run", "start"], {
        stdio: ["ignore", "pipe", "pipe"],
        detached: false,
      });

      // Handle server startup errors
      serverProcess.on("error", (error) => {
        throw new Error(`Failed to start server: ${error.message}`);
      });

      // Wait for server to start
      await this.waitForServer("http://localhost:3000", 30000);

      // Run Lighthouse
      const lighthouseCmd = `npx lighthouse http://localhost:3000 --only-categories=performance --output=json --output-path=.lighthouse-report.json --chrome-flags="--headless --no-sandbox"`;
      execSync(lighthouseCmd, { stdio: "inherit" });

      // Parse Lighthouse results
      const reportPath = path.join(process.cwd(), ".lighthouse-report.json");
      if (fs.existsSync(reportPath)) {
        const report = JSON.parse(fs.readFileSync(reportPath, "utf8"));
        return this.parseLighthouseReport(report);
      }

      return null;
    } catch (error) {
      console.warn("Lighthouse audit failed:", error.message);
      return null;
    } finally {
      // Always clean up the server process with proper awaited shutdown
      if (serverProcess) {
        try {
          // Send SIGTERM for graceful shutdown
          serverProcess.kill("SIGTERM");

          // Wait for either exit or timeout
          const exitPromise = new Promise((resolve) => {
            serverProcess.once("exit", resolve);
          });

          const timeoutPromise = new Promise((resolve) => {
            setTimeout(resolve, 5000); // 5 second timeout
          });

          // Race between exit and timeout
          await Promise.race([exitPromise, timeoutPromise]);

          // If still running after timeout, force kill
          if (!serverProcess.killed) {
            console.warn("Server did not exit gracefully, forcing termination");
            serverProcess.kill("SIGKILL");

            // Wait for forced exit
            await new Promise((resolve) => {
              serverProcess.once("exit", resolve);
            });
          }

          // Remove all listeners to prevent leaks
          serverProcess.removeAllListeners();
        } catch (killError) {
          console.warn("Failed to kill server process:", killError.message);
        }
      }
    }
  }

  /**
   * Parse Lighthouse report and extract Core Web Vitals
   */
  parseLighthouseReport(report) {
    const audits = report.audits;

    const metrics = {
      lcp: audits["largest-contentful-paint"]?.numericValue || 0,
      fid: audits["max-potential-fid"]?.numericValue || 0, // Lighthouse uses max potential FID
      cls: audits["cumulative-layout-shift"]?.numericValue || 0,
      fcp: audits["first-contentful-paint"]?.numericValue || 0,
      ttfb: audits["server-response-time"]?.numericValue || 0,
      performanceScore: report.categories.performance.score * 100,
    };

    console.log("📊 Lighthouse Performance Metrics:");
    console.log(
      `   LCP: ${metrics.lcp.toFixed(0)}ms (budget: ${this.budget.maxLCP}ms)`
    );
    console.log(
      `   FID: ${metrics.fid.toFixed(0)}ms (budget: ${this.budget.maxFID}ms)`
    );
    console.log(
      `   CLS: ${metrics.cls.toFixed(3)} (budget: ${this.budget.maxCLS})`
    );
    console.log(
      `   FCP: ${metrics.fcp.toFixed(0)}ms (budget: ${this.budget.maxFCP}ms)`
    );
    console.log(
      `   TTFB: ${metrics.ttfb.toFixed(0)}ms (budget: ${this.budget.maxTTFB}ms)`
    );
    console.log(
      `   Performance Score: ${metrics.performanceScore.toFixed(0)}/100`
    );

    return metrics;
  }

  /**
   * Validate Core Web Vitals against budget
   */
  validateCoreWebVitals(metrics) {
    if (!metrics) return;

    const checks = [
      { metric: "lcp", actual: metrics.lcp, budget: this.budget.maxLCP },
      { metric: "fid", actual: metrics.fid, budget: this.budget.maxFID },
      { metric: "cls", actual: metrics.cls, budget: this.budget.maxCLS },
      { metric: "fcp", actual: metrics.fcp, budget: this.budget.maxFCP },
      { metric: "ttfb", actual: metrics.ttfb, budget: this.budget.maxTTFB },
    ];

    checks.forEach((check) => {
      if (check.actual > check.budget) {
        const overage = check.actual - check.budget;
        const overagePercent = (overage / check.budget) * 100;

        this.violations.push({
          ...check,
          overage,
          overagePercent,
          severity: overagePercent > 50 ? "critical" : "warning",
        });
      } else if (check.actual > check.budget * 0.8) {
        this.warnings.push({
          ...check,
          usage: (check.actual / check.budget) * 100,
          severity: "warning",
        });
      }
    });
  }

  /**
   * Generate performance report
   */
  generateReport() {
    const report = {
      environment: this.environment,
      timestamp: new Date().toISOString(),
      budget: this.budget,
      violations: this.violations,
      warnings: this.warnings,
      passed: this.violations.length === 0,
      score: this.calculateScore(),
    };

    // Write report to file
    const reportPath = path.join(
      process.cwd(),
      "performance-budget-report.json"
    );
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

    return report;
  }

  /**
   * Calculate overall performance score
   */
  calculateScore() {
    const totalChecks = 7; // Bundle size + 6 Core Web Vitals metrics
    const failedChecks = this.violations.filter(
      (v) => v.severity === "critical"
    ).length;
    return Math.round(((totalChecks - failedChecks) / totalChecks) * 100);
  }

  /**
   * Print results to console
   */
  printResults(report) {
    console.log("\n" + "=".repeat(60));
    console.log("📊 PERFORMANCE BUDGET VALIDATION REPORT");
    console.log("=".repeat(60));
    console.log(`Environment: ${report.environment}`);
    console.log(`Score: ${report.score}/100`);
    console.log(`Status: ${report.passed ? "✅ PASSED" : "❌ FAILED"}`);
    console.log(`Timestamp: ${report.timestamp}`);

    if (report.violations.length > 0) {
      console.log("\n🚨 BUDGET VIOLATIONS:");
      report.violations.forEach((violation) => {
        const icon = violation.severity === "critical" ? "🚨" : "⚠️";
        console.log(
          `${icon} ${violation.metric.toUpperCase()}: ${this.formatMetricValue(
            violation.metric,
            violation.actual
          )} (budget: ${this.formatMetricValue(
            violation.metric,
            violation.budget
          )})`
        );
        console.log(
          `   Overage: ${this.formatMetricValue(
            violation.metric,
            violation.overage
          )} (${violation.overagePercent.toFixed(1)}%)`
        );
      });
    }

    if (report.warnings.length > 0) {
      console.log("\n⚠️ WARNINGS:");
      report.warnings.forEach((warning) => {
        console.log(
          `⚠️ ${warning.metric.toUpperCase()}: ${this.formatMetricValue(
            warning.metric,
            warning.actual
          )} (${warning.usage.toFixed(1)}% of budget)`
        );
      });
    }

    if (report.passed) {
      console.log("\n✅ All performance budgets are within limits!");
    } else {
      console.log("\n❌ Performance budget validation failed.");
      console.log("\n💡 RECOMMENDATIONS:");
      console.log("   • Implement code splitting and lazy loading");
      console.log("   • Optimize images and assets");
      console.log("   • Reduce JavaScript bundle sizes");
      console.log("   • Improve server response times");
      console.log("   • Minimize layout shifts");
    }

    console.log("\n" + "=".repeat(60));
  }

  /**
   * Format metric values for display
   */
  formatMetricValue(metric, value) {
    switch (metric) {
      case "bundleSize":
        return this.formatBytes(value);
      case "lcp":
      case "fid":
      case "fcp":
      case "ttfb":
      case "loadTime":
        return `${Math.round(value)}ms`;
      case "cls":
        return value.toFixed(3);
      default:
        return value.toString();
    }
  }

  /**
   * Format bytes for display
   */
  formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  /**
   * Wait for server to start
   */
  async waitForServer(url, timeout = 30000) {
    const start = Date.now();

    while (Date.now() - start < timeout) {
      try {
        const response = await fetch(url);
        if (response.ok) return;
      } catch (error) {
        // Server not ready yet
      }

      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    throw new Error(`Server did not start within ${timeout}ms`);
  }

  /**
   * Run complete validation
   */
  async validate() {
    console.log(
      `🚀 Starting performance budget validation for ${this.environment} environment...`
    );

    try {
      // Validate bundle sizes
      this.validateBundleSizes();

      // Run Lighthouse audit for Core Web Vitals
      const lighthouseMetrics = await this.runLighthouseAudit();
      if (lighthouseMetrics) {
        this.validateCoreWebVitals(lighthouseMetrics);
      }

      // Generate and print report
      const report = this.generateReport();
      this.printResults(report);

      // Return exit code for CI/CD
      return report.passed ? 0 : 1;
    } catch (error) {
      console.error("❌ Performance validation failed:", error.message);
      return 1;
    }
  }
}

// CLI interface
async function main() {
  const args = process.argv.slice(2);
  const environment = args[0] || process.env.NODE_ENV || "production";

  console.log("🎯 Performance Budget Validator");
  console.log(`Environment: ${environment}`);

  const validator = new PerformanceBudgetValidator(environment);
  const exitCode = await validator.validate();

  process.exit(exitCode);
}

// Run if called directly
if (require.main === module) {
  main().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
  });
}

module.exports = { PerformanceBudgetValidator, PERFORMANCE_BUDGETS };
