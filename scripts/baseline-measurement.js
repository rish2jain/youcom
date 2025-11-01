#!/usr/bin/env node

/**
 * Baseline Measurement and Bundle Size Validation Script
 * Establishes baseline measurements and validates 40% bundle size reduction
 * Requirements: 4.1, 4.5
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

// Industry standard baselines for comparison (if no historical data available)
const INDUSTRY_BASELINES = {
  // Typical enterprise SaaS application baselines
  totalBundleSize: 2800000, // 2.8MB (unoptimized)
  initialLoadTime: 8000, // 8 seconds on 3G
  vendorBundleSize: 1200000, // 1.2MB vendor libraries
  applicationBundleSize: 1600000, // 1.6MB application code

  // Performance targets after optimization
  targetReduction: 0.4, // 40% reduction target
  maxOptimizedSize: 500000, // 500KB performance budget
};

class BaselineMeasurement {
  constructor() {
    this.measurements = {
      timestamp: new Date().toISOString(),
      baseline: null,
      current: null,
      reduction: null,
      budgetCompliance: null,
    };

    this.baselineFile = path.join(process.cwd(), "performance-baseline.json");
    this.reportFile = path.join(process.cwd(), "performance-budget-report.md");
  }

  /**
   * Load existing baseline or create from industry standards
   */
  loadBaseline() {
    if (fs.existsSync(this.baselineFile)) {
      try {
        const baseline = JSON.parse(fs.readFileSync(this.baselineFile, "utf8"));
        console.log("📊 Loaded existing baseline measurements");
        return baseline;
      } catch (error) {
        console.warn(
          "⚠️ Could not load existing baseline, using industry standards"
        );
      }
    }

    console.log("📊 Using industry standard baselines for comparison");
    const baseline = {
      timestamp: new Date().toISOString(),
      source: "industry_standards",
      measurements: INDUSTRY_BASELINES,
      description:
        "Industry standard baselines for enterprise SaaS applications",
    };

    // Save baseline for future reference
    fs.writeFileSync(this.baselineFile, JSON.stringify(baseline, null, 2));
    return baseline;
  }

  /**
   * Measure current bundle sizes after optimization
   */
  measureCurrentBundles() {
    console.log("📦 Measuring current optimized bundle sizes...");

    const buildDir = path.join(process.cwd(), ".next");
    const staticDir = path.join(buildDir, "static");

    if (!fs.existsSync(staticDir)) {
      throw new Error('Build directory not found. Run "npm run build" first.');
    }

    const measurements = {
      totalBundleSize: 0,
      vendorBundleSize: 0,
      applicationBundleSize: 0,
      routeBundleSize: 0,
      sharedBundleSize: 0,
      bundles: {},
      bundleCount: 0,
    };

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

        measurements.bundles[file] = {
          size,
          type: this.categorizeBundleType(file),
          gzipEstimate: Math.round(size * 0.3), // Estimate 70% compression
        };

        measurements.bundleCount++;

        // Categorize bundle sizes
        if (this.isVendorBundle(file)) {
          measurements.vendorBundleSize += size;
        } else if (this.isRouteBundle(file)) {
          measurements.routeBundleSize += size;
        } else if (this.isSharedBundle(file)) {
          measurements.sharedBundleSize += size;
        } else {
          measurements.applicationBundleSize += size;
        }

        // Count toward initial load for main bundles
        if (this.isInitialLoadBundle(file)) {
          measurements.totalBundleSize += size;
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

        measurements.bundles[file] = {
          size,
          type: "css",
          gzipEstimate: Math.round(size * 0.2), // CSS compresses better
        };

        measurements.totalBundleSize += size;
        measurements.bundleCount++;
      });
    }

    return measurements;
  }

  /**
   * Categorize bundle type for analysis
   */
  categorizeBundleType(filename) {
    if (this.isVendorBundle(filename)) return "vendor";
    if (this.isRouteBundle(filename)) return "route";
    if (this.isSharedBundle(filename)) return "shared";
    if (filename.endsWith(".css")) return "css";
    return "application";
  }

  /**
   * Check if bundle is a vendor library
   */
  isVendorBundle(filename) {
    const vendorPatterns = [
      "vendors",
      "react",
      "charts",
      "ui",
      "framework",
      "webpack",
    ];
    return vendorPatterns.some((pattern) => filename.includes(pattern));
  }

  /**
   * Check if bundle is route-specific
   */
  isRouteBundle(filename) {
    const routePatterns = [
      "dashboard",
      "research",
      "analytics",
      "monitoring",
      "integrations",
      "settings",
    ];
    return routePatterns.some((pattern) => filename.includes(pattern));
  }

  /**
   * Check if bundle is shared across routes
   */
  isSharedBundle(filename) {
    const sharedPatterns = ["shared", "common"];
    return sharedPatterns.some((pattern) => filename.includes(pattern));
  }

  /**
   * Check if bundle is part of initial load
   */
  isInitialLoadBundle(filename) {
    const initialPatterns = [
      "main",
      "framework",
      "webpack",
      "runtime",
      "polyfills",
    ];
    return (
      initialPatterns.some((pattern) => filename.includes(pattern)) ||
      filename.endsWith(".css")
    );
  }

  /**
   * Calculate bundle size reduction percentage
   */
  calculateReduction(baseline, current) {
    const baselineSize = baseline.measurements.totalBundleSize;
    const currentSize = current.totalBundleSize;

    const absoluteReduction = baselineSize - currentSize;
    const percentageReduction = (absoluteReduction / baselineSize) * 100;

    return {
      baselineSize,
      currentSize,
      absoluteReduction,
      percentageReduction,
      targetReduction: INDUSTRY_BASELINES.targetReduction * 100, // 40%
      meetsTarget:
        percentageReduction >= INDUSTRY_BASELINES.targetReduction * 100,
    };
  }

  /**
   * Validate performance budget compliance
   */
  validateBudgetCompliance(current) {
    const budget = INDUSTRY_BASELINES.maxOptimizedSize;
    const compliance = {
      budget,
      actual: current.totalBundleSize,
      compliant: current.totalBundleSize <= budget,
      overage: Math.max(0, current.totalBundleSize - budget),
      utilizationPercent: (current.totalBundleSize / budget) * 100,
    };

    return compliance;
  }

  /**
   * Analyze bundle composition and identify optimization opportunities
   */
  analyzeBundleComposition(current) {
    const analysis = {
      bundleDistribution: {
        vendor: current.vendorBundleSize,
        application: current.applicationBundleSize,
        route: current.routeBundleSize,
        shared: current.sharedBundleSize,
      },
      recommendations: [],
      optimizationOpportunities: [],
    };

    // Analyze vendor bundle size
    if (current.vendorBundleSize > 200000) {
      // 200KB
      analysis.recommendations.push(
        `Vendor bundles (${this.formatBytes(
          current.vendorBundleSize
        )}) could be further optimized with tree shaking`
      );
    }

    // Analyze route bundle efficiency
    if (current.routeBundleSize > 300000) {
      // 300KB
      analysis.recommendations.push(
        `Route bundles (${this.formatBytes(
          current.routeBundleSize
        )}) should implement more aggressive lazy loading`
      );
    }

    // Check bundle count efficiency
    if (current.bundleCount > 20) {
      analysis.recommendations.push(
        `High bundle count (${current.bundleCount}) may impact HTTP/2 efficiency`
      );
    }

    // Identify largest bundles for optimization
    const sortedBundles = Object.entries(current.bundles)
      .sort(([, a], [, b]) => b.size - a.size)
      .slice(0, 5);

    analysis.optimizationOpportunities = sortedBundles.map(
      ([name, bundle]) => ({
        name,
        size: bundle.size,
        type: bundle.type,
        recommendation: this.getBundleOptimizationRecommendation(name, bundle),
      })
    );

    return analysis;
  }

  /**
   * Get specific optimization recommendation for a bundle
   */
  getBundleOptimizationRecommendation(name, bundle) {
    if (bundle.type === "vendor" && bundle.size > 150000) {
      return "Consider splitting into smaller vendor chunks";
    }
    if (bundle.type === "route" && bundle.size > 100000) {
      return "Implement component-level lazy loading";
    }
    if (bundle.type === "application" && bundle.size > 80000) {
      return "Review for unused code and implement tree shaking";
    }
    return "Monitor for future optimization opportunities";
  }

  /**
   * Generate comprehensive performance report
   */
  generateReport(baseline, current, reduction, compliance, analysis) {
    const report = {
      title: "Frontend Performance Optimization - Bundle Size Validation",
      timestamp: this.measurements.timestamp,
      summary: {
        baselineSource: baseline.source,
        reductionAchieved: reduction.percentageReduction,
        targetReduction: reduction.targetReduction,
        meetsReductionTarget: reduction.meetsTarget,
        budgetCompliant: compliance.compliant,
        overallStatus:
          reduction.meetsTarget && compliance.compliant
            ? "PASSED"
            : "NEEDS_IMPROVEMENT",
      },
      baseline: {
        totalSize: baseline.measurements.totalBundleSize,
        source: baseline.source,
        timestamp: baseline.timestamp,
      },
      current: {
        totalSize: current.totalBundleSize,
        bundleCount: current.bundleCount,
        distribution: analysis.bundleDistribution,
      },
      reduction,
      compliance,
      analysis,
      recommendations: this.generateActionableRecommendations(
        reduction,
        compliance,
        analysis
      ),
    };

    return report;
  }

  /**
   * Generate actionable recommendations based on analysis
   */
  generateActionableRecommendations(reduction, compliance, analysis) {
    const recommendations = [];

    if (!reduction.meetsTarget) {
      const needed = reduction.targetReduction - reduction.percentageReduction;
      recommendations.push({
        priority: "HIGH",
        action: `Achieve additional ${needed.toFixed(
          1
        )}% bundle size reduction`,
        details: "Current reduction is below the 40% target",
      });
    }

    if (!compliance.compliant) {
      recommendations.push({
        priority: "CRITICAL",
        action: `Reduce bundle size by ${this.formatBytes(compliance.overage)}`,
        details: `Current size exceeds performance budget of ${this.formatBytes(
          compliance.budget
        )}`,
      });
    }

    // Add specific optimization recommendations
    analysis.recommendations.forEach((rec) => {
      recommendations.push({
        priority: "MEDIUM",
        action: rec,
        details: "Bundle composition optimization opportunity",
      });
    });

    return recommendations;
  }

  /**
   * Print results to console
   */
  printResults(report) {
    console.log("\n" + "=".repeat(70));
    console.log(
      "📊 FRONTEND PERFORMANCE OPTIMIZATION - BUNDLE SIZE VALIDATION"
    );
    console.log("=".repeat(70));

    console.log(`\n📈 REDUCTION ANALYSIS:`);
    console.log(
      `   Baseline: ${this.formatBytes(report.baseline.totalSize)} (${
        report.baseline.source
      })`
    );
    console.log(`   Current:  ${this.formatBytes(report.current.totalSize)}`);
    console.log(
      `   Reduction: ${this.formatBytes(
        report.reduction.absoluteReduction
      )} (${report.reduction.percentageReduction.toFixed(1)}%)`
    );
    console.log(`   Target:   ${report.reduction.targetReduction}% reduction`);
    console.log(
      `   Status:   ${
        report.reduction.meetsTarget ? "✅ TARGET MET" : "❌ BELOW TARGET"
      }`
    );

    console.log(`\n💰 BUDGET COMPLIANCE:`);
    console.log(`   Budget:   ${this.formatBytes(report.compliance.budget)}`);
    console.log(`   Actual:   ${this.formatBytes(report.compliance.actual)}`);
    console.log(
      `   Usage:    ${report.compliance.utilizationPercent.toFixed(1)}%`
    );
    console.log(
      `   Status:   ${
        report.compliance.compliant ? "✅ COMPLIANT" : "❌ OVER BUDGET"
      }`
    );

    console.log(`\n📦 BUNDLE COMPOSITION:`);
    Object.entries(report.current.distribution).forEach(([type, size]) => {
      const percent = ((size / report.current.totalSize) * 100).toFixed(1);
      console.log(
        `   ${type.padEnd(12)}: ${this.formatBytes(size).padEnd(
          10
        )} (${percent}%)`
      );
    });

    console.log(`\n🎯 OPTIMIZATION OPPORTUNITIES:`);
    report.analysis.optimizationOpportunities.slice(0, 3).forEach((opp, i) => {
      console.log(
        `   ${i + 1}. ${opp.name} (${this.formatBytes(opp.size)}) - ${
          opp.recommendation
        }`
      );
    });

    if (report.recommendations.length > 0) {
      console.log(`\n💡 RECOMMENDATIONS:`);
      report.recommendations.forEach((rec) => {
        const icon =
          rec.priority === "CRITICAL"
            ? "🚨"
            : rec.priority === "HIGH"
            ? "⚠️"
            : "💡";
        console.log(`   ${icon} ${rec.action}`);
      });
    }

    console.log(`\n📊 OVERALL STATUS: ${report.summary.overallStatus}`);
    console.log("=".repeat(70));
  }

  /**
   * Write detailed markdown report
   */
  writeMarkdownReport(report) {
    let markdown = `# Frontend Performance Optimization - Bundle Size Validation\n\n`;
    markdown += `**Generated:** ${report.timestamp}\n\n`;

    // Executive Summary
    markdown += `## Executive Summary\n\n`;
    markdown += `| Metric | Value | Status |\n`;
    markdown += `|--------|-------|--------|\n`;
    markdown += `| Bundle Size Reduction | ${report.reduction.percentageReduction.toFixed(
      1
    )}% | ${
      report.reduction.meetsTarget ? "✅ Target Met" : "❌ Below Target"
    } |\n`;
    markdown += `| Performance Budget | ${report.compliance.utilizationPercent.toFixed(
      1
    )}% | ${
      report.compliance.compliant ? "✅ Compliant" : "❌ Over Budget"
    } |\n`;
    markdown += `| Overall Status | ${report.summary.overallStatus} | ${
      report.summary.overallStatus === "PASSED" ? "✅" : "❌"
    } |\n\n`;

    // Detailed Analysis
    markdown += `## Detailed Analysis\n\n`;
    markdown += `### Bundle Size Reduction\n\n`;
    markdown += `- **Baseline:** ${this.formatBytes(
      report.baseline.totalSize
    )} (${report.baseline.source})\n`;
    markdown += `- **Current:** ${this.formatBytes(
      report.current.totalSize
    )}\n`;
    markdown += `- **Reduction:** ${this.formatBytes(
      report.reduction.absoluteReduction
    )} (${report.reduction.percentageReduction.toFixed(1)}%)\n`;
    markdown += `- **Target:** ${report.reduction.targetReduction}% reduction\n\n`;

    markdown += `### Performance Budget Compliance\n\n`;
    markdown += `- **Budget:** ${this.formatBytes(report.compliance.budget)}\n`;
    markdown += `- **Actual:** ${this.formatBytes(report.compliance.actual)}\n`;
    markdown += `- **Utilization:** ${report.compliance.utilizationPercent.toFixed(
      1
    )}%\n`;
    if (!report.compliance.compliant) {
      markdown += `- **Overage:** ${this.formatBytes(
        report.compliance.overage
      )}\n`;
    }
    markdown += `\n`;

    // Bundle Composition
    markdown += `### Bundle Composition\n\n`;
    markdown += `| Type | Size | Percentage |\n`;
    markdown += `|------|------|------------|\n`;
    Object.entries(report.current.distribution).forEach(([type, size]) => {
      const percent = ((size / report.current.totalSize) * 100).toFixed(1);
      markdown += `| ${type} | ${this.formatBytes(size)} | ${percent}% |\n`;
    });
    markdown += `\n`;

    // Optimization Opportunities
    if (report.analysis.optimizationOpportunities.length > 0) {
      markdown += `### Top Optimization Opportunities\n\n`;
      markdown += `| Bundle | Size | Type | Recommendation |\n`;
      markdown += `|--------|------|------|----------------|\n`;
      report.analysis.optimizationOpportunities.forEach((opp) => {
        markdown += `| ${opp.name} | ${this.formatBytes(opp.size)} | ${
          opp.type
        } | ${opp.recommendation} |\n`;
      });
      markdown += `\n`;
    }

    // Recommendations
    if (report.recommendations.length > 0) {
      markdown += `### Recommendations\n\n`;
      report.recommendations.forEach((rec) => {
        const icon =
          rec.priority === "CRITICAL"
            ? "🚨"
            : rec.priority === "HIGH"
            ? "⚠️"
            : "💡";
        markdown += `${icon} **${rec.priority}:** ${rec.action}\n`;
        markdown += `   - ${rec.details}\n\n`;
      });
    }

    fs.writeFileSync(this.reportFile, markdown);
    console.log(`\n📄 Detailed report written to: ${this.reportFile}`);
  }

  /**
   * Format bytes to human readable format
   */
  formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  /**
   * Run complete baseline measurement and validation
   */
  async run() {
    try {
      console.log(
        "🚀 Starting baseline measurement and bundle size validation..."
      );

      // Ensure we have a fresh build
      console.log("🔨 Building optimized production bundle...");
      execSync("npm run build", { stdio: "inherit" });

      // Load baseline measurements
      const baseline = this.loadBaseline();

      // Measure current optimized bundles
      const current = this.measureCurrentBundles();

      // Calculate reduction
      const reduction = this.calculateReduction(baseline, current);

      // Validate budget compliance
      const compliance = this.validateBudgetCompliance(current);

      // Analyze bundle composition
      const analysis = this.analyzeBundleComposition(current);

      // Generate comprehensive report
      const report = this.generateReport(
        baseline,
        current,
        reduction,
        compliance,
        analysis
      );

      // Print results
      this.printResults(report);

      // Write detailed markdown report
      this.writeMarkdownReport(report);

      // Save measurements for future reference
      this.measurements.baseline = baseline;
      this.measurements.current = current;
      this.measurements.reduction = reduction;
      this.measurements.budgetCompliance = compliance;

      const measurementsFile = path.join(
        process.cwd(),
        "performance-measurements.json"
      );
      fs.writeFileSync(
        measurementsFile,
        JSON.stringify(this.measurements, null, 2)
      );

      // Return success/failure for CI/CD
      const success = reduction.meetsTarget && compliance.compliant;
      return success ? 0 : 1;
    } catch (error) {
      console.error("❌ Baseline measurement failed:", error.message);
      return 1;
    }
  }
}

// CLI interface
async function main() {
  console.log("🎯 Frontend Performance Optimization - Baseline Measurement");

  const measurement = new BaselineMeasurement();
  const exitCode = await measurement.run();

  process.exit(exitCode);
}

// Run if called directly
if (require.main === module) {
  main().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
  });
}

module.exports = { BaselineMeasurement, INDUSTRY_BASELINES };
