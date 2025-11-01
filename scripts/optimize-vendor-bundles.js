#!/usr/bin/env node

/**
 * Vendor Bundle Optimization Script
 * Analyzes and optimizes vendor bundle splitting for better caching
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

class VendorBundleOptimizer {
  constructor() {
    this.projectRoot = process.cwd();
    this.buildDir = path.join(this.projectRoot, ".next");
    this.performanceBudgets = {
      maxVendorSize: 200000, // 200KB
      maxChartSize: 250000, // 250KB
      maxUISize: 150000, // 150KB
      maxReactSize: 150000, // 150KB
    };
  }

  /**
   * Analyze current bundle sizes
   */
  analyzeBundles() {
    console.log("🔍 Analyzing vendor bundle sizes...\n");

    const staticDir = path.join(this.buildDir, "static", "chunks");

    if (!fs.existsSync(staticDir)) {
      console.error('❌ Build directory not found. Run "npm run build" first.');
      process.exit(1);
    }

    const chunks = fs
      .readdirSync(staticDir)
      .filter((file) => file.endsWith(".js"))
      .map((file) => {
        const filePath = path.join(staticDir, file);
        const stats = fs.statSync(filePath);
        return {
          name: file,
          size: stats.size,
          type: this.determineBundleType(file),
        };
      })
      .sort((a, b) => b.size - a.size);

    return chunks;
  }

  /**
   * Determine bundle type from filename
   */
  determineBundleType(filename) {
    if (filename.includes("react")) return "react";
    if (filename.includes("charts")) return "charts";
    if (filename.includes("ui")) return "ui";
    if (filename.includes("vendors")) return "vendor";
    if (filename.includes("dashboard")) return "dashboard";
    if (filename.includes("research")) return "research";
    if (filename.includes("analytics")) return "analytics";
    if (filename.includes("monitoring")) return "monitoring";
    return "other";
  }

  /**
   * Check for budget violations
   */
  checkBudgetViolations(bundles) {
    const violations = [];

    bundles.forEach((bundle) => {
      const budget =
        this.performanceBudgets[
          `max${bundle.type.charAt(0).toUpperCase() + bundle.type.slice(1)}Size`
        ];
      if (budget && bundle.size > budget) {
        violations.push({
          bundle: bundle.name,
          type: bundle.type,
          size: bundle.size,
          budget: budget,
          excess: bundle.size - budget,
        });
      }
    });

    return violations;
  }

  /**
   * Generate optimization recommendations
   */
  generateRecommendations(bundles, violations) {
    const recommendations = [];

    // Check for oversized vendor bundles
    const vendorBundles = bundles.filter((b) => b.type === "vendor");
    if (vendorBundles.length > 0) {
      const largestVendor = vendorBundles[0];
      if (largestVendor.size > 200000) {
        recommendations.push({
          type: "split-vendor",
          message: `Split large vendor bundle: ${
            largestVendor.name
          } (${this.formatBytes(largestVendor.size)})`,
          action: "Consider splitting into React, UI, and utility bundles",
        });
      }
    }

    // Check for chart bundle optimization
    const chartBundles = bundles.filter((b) => b.type === "charts");
    if (chartBundles.length > 0 && chartBundles[0].size > 200000) {
      recommendations.push({
        type: "lazy-load-charts",
        message: `Chart bundle is large: ${
          chartBundles[0].name
        } (${this.formatBytes(chartBundles[0].size)})`,
        action: "Implement lazy loading for chart components",
      });
    }

    // Check for route bundle sizes
    const routeBundles = bundles.filter((b) =>
      ["dashboard", "research", "analytics", "monitoring"].includes(b.type)
    );
    routeBundles.forEach((bundle) => {
      if (bundle.size > 150000) {
        recommendations.push({
          type: "optimize-route",
          message: `Route bundle is large: ${bundle.name} (${this.formatBytes(
            bundle.size
          )})`,
          action: "Consider component-level code splitting",
        });
      }
    });

    // General recommendations
    if (violations.length > 0) {
      recommendations.push({
        type: "general",
        message: "Multiple budget violations detected",
        action: "Enable tree shaking and remove unused dependencies",
      });
    }

    return recommendations;
  }

  /**
   * Format bytes to human readable
   */
  formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  /**
   * Generate optimization report
   */
  generateReport(bundles, violations, recommendations) {
    console.log("📊 Vendor Bundle Analysis Report\n");
    console.log("=".repeat(50));

    // Summary
    const totalSize = bundles.reduce((sum, bundle) => sum + bundle.size, 0);
    console.log(`\n📈 Summary:`);
    console.log(`   Total bundle size: ${this.formatBytes(totalSize)}`);
    console.log(`   Number of chunks: ${bundles.length}`);
    console.log(`   Budget violations: ${violations.length}`);

    // Top bundles
    console.log(`\n🏆 Largest bundles:`);
    bundles.slice(0, 10).forEach((bundle, index) => {
      const status = violations.some((v) => v.bundle === bundle.name)
        ? "❌"
        : "✅";
      console.log(
        `   ${index + 1}. ${status} ${bundle.name} (${
          bundle.type
        }) - ${this.formatBytes(bundle.size)}`
      );
    });

    // Violations
    if (violations.length > 0) {
      console.log(`\n⚠️  Budget Violations:`);
      violations.forEach((violation) => {
        console.log(
          `   - ${violation.bundle}: ${this.formatBytes(
            violation.size
          )} > ${this.formatBytes(
            violation.budget
          )} (excess: ${this.formatBytes(violation.excess)})`
        );
      });
    }

    // Recommendations
    if (recommendations.length > 0) {
      console.log(`\n💡 Optimization Recommendations:`);
      recommendations.forEach((rec, index) => {
        console.log(`   ${index + 1}. ${rec.message}`);
        console.log(`      → ${rec.action}`);
      });
    }

    console.log("\n" + "=".repeat(50));
  }

  /**
   * Run the optimization analysis
   */
  run() {
    try {
      const bundles = this.analyzeBundles();
      const violations = this.checkBudgetViolations(bundles);
      const recommendations = this.generateRecommendations(bundles, violations);

      this.generateReport(bundles, violations, recommendations);

      // Exit with error code if there are violations
      if (violations.length > 0) {
        console.log("\n❌ Performance budget violations detected!");
        if (process.env.CI) {
          process.exit(1);
        }
      } else {
        console.log("\n✅ All vendor bundles within performance budgets!");
      }
    } catch (error) {
      console.error("❌ Error analyzing bundles:", error.message);
      process.exit(1);
    }
  }
}

// Run if called directly
if (require.main === module) {
  const optimizer = new VendorBundleOptimizer();
  optimizer.run();
}

module.exports = VendorBundleOptimizer;
