/**
 * Bundle Analyzer - Monitors and reports on bundle sizes for vendor libraries
 * Provides insights into bundle optimization and performance budgets
 */

export interface BundleMetrics {
  name: string;
  size: number;
  gzipSize: number;
  type: "vendor" | "route" | "shared" | "core";
  lastModified: Date;
  cacheHit?: boolean;
}

export interface BundleReport {
  totalSize: number;
  totalGzipSize: number;
  bundles: BundleMetrics[];
  performanceBudget: {
    maxTotalSize: number;
    maxVendorSize: number;
    maxRouteSize: number;
    violations: string[];
  };
  recommendations: string[];
}

class BundleAnalyzer {
  private performanceBudgets = {
    maxTotalSize: 500000, // 500KB total initial bundle
    maxVendorSize: 200000, // 200KB max vendor bundle
    maxRouteSize: 150000, // 150KB max route bundle
    maxChartSize: 250000, // 250KB max chart bundle
    maxUISize: 150000, // 150KB max UI bundle
  };

  /**
   * Analyze bundle sizes from webpack stats
   */
  analyzeBundles(webpackStats: any): BundleReport {
    const bundles: BundleMetrics[] = [];
    let totalSize = 0;
    let totalGzipSize = 0;

    // Process webpack chunks
    if (webpackStats?.chunks) {
      webpackStats.chunks.forEach((chunk: any) => {
        const bundleMetric: BundleMetrics = {
          name: chunk.names?.[0] || chunk.id,
          size: chunk.size || 0,
          gzipSize: this.estimateGzipSize(chunk.size || 0),
          type: this.determineBundleType(chunk.names?.[0] || ""),
          lastModified: new Date(),
        };

        bundles.push(bundleMetric);
        totalSize += bundleMetric.size;
        totalGzipSize += bundleMetric.gzipSize;
      });
    }

    const violations = this.checkBudgetViolations(bundles, totalSize);
    const recommendations = this.generateRecommendations(bundles, violations);

    return {
      totalSize,
      totalGzipSize,
      bundles,
      performanceBudget: {
        maxTotalSize: this.performanceBudgets.maxTotalSize,
        maxVendorSize: this.performanceBudgets.maxVendorSize,
        maxRouteSize: this.performanceBudgets.maxRouteSize,
        violations,
      },
      recommendations,
    };
  }

  /**
   * Determine bundle type based on chunk name
   */
  private determineBundleType(chunkName: string): BundleMetrics["type"] {
    if (
      chunkName.includes("vendor") ||
      chunkName.includes("react") ||
      chunkName.includes("charts") ||
      chunkName.includes("ui")
    ) {
      return "vendor";
    }
    if (
      chunkName.includes("dashboard") ||
      chunkName.includes("research") ||
      chunkName.includes("analytics") ||
      chunkName.includes("monitoring")
    ) {
      return "route";
    }
    if (chunkName.includes("shared") || chunkName.includes("common")) {
      return "shared";
    }
    return "core";
  }

  /**
   * Estimate gzip size (typically 70% compression for JS)
   */
  private estimateGzipSize(originalSize: number): number {
    return Math.round(originalSize * 0.3);
  }

  /**
   * Check for performance budget violations
   */
  private checkBudgetViolations(
    bundles: BundleMetrics[],
    totalSize: number
  ): string[] {
    const violations: string[] = [];

    // Check total size
    if (totalSize > this.performanceBudgets.maxTotalSize) {
      violations.push(
        `Total bundle size (${this.formatBytes(
          totalSize
        )}) exceeds budget (${this.formatBytes(
          this.performanceBudgets.maxTotalSize
        )})`
      );
    }

    // Check individual bundle sizes
    bundles.forEach((bundle) => {
      if (
        bundle.type === "vendor" &&
        bundle.size > this.performanceBudgets.maxVendorSize
      ) {
        violations.push(
          `Vendor bundle "${bundle.name}" (${this.formatBytes(
            bundle.size
          )}) exceeds budget (${this.formatBytes(
            this.performanceBudgets.maxVendorSize
          )})`
        );
      }
      if (
        bundle.type === "route" &&
        bundle.size > this.performanceBudgets.maxRouteSize
      ) {
        violations.push(
          `Route bundle "${bundle.name}" (${this.formatBytes(
            bundle.size
          )}) exceeds budget (${this.formatBytes(
            this.performanceBudgets.maxRouteSize
          )})`
        );
      }
    });

    return violations;
  }

  /**
   * Generate optimization recommendations
   */
  private generateRecommendations(
    bundles: BundleMetrics[],
    violations: string[]
  ): string[] {
    const recommendations: string[] = [];

    // Analyze vendor bundles
    const vendorBundles = bundles.filter((b) => b.type === "vendor");
    const largestVendor = vendorBundles.reduce(
      (prev, current) => (prev.size > current.size ? prev : current),
      vendorBundles[0]
    );

    if (largestVendor && largestVendor.size > 150000) {
      recommendations.push(
        `Consider splitting large vendor bundle "${
          largestVendor.name
        }" (${this.formatBytes(largestVendor.size)})`
      );
    }

    // Analyze route bundles
    const routeBundles = bundles.filter((b) => b.type === "route");
    routeBundles.forEach((bundle) => {
      if (bundle.size > 100000) {
        recommendations.push(
          `Route bundle "${
            bundle.name
          }" could benefit from lazy loading (${this.formatBytes(bundle.size)})`
        );
      }
    });

    // Check for duplicate dependencies
    const duplicateCheck = this.checkForDuplicates(bundles);
    if (duplicateCheck.length > 0) {
      recommendations.push(...duplicateCheck);
    }

    // General recommendations
    if (violations.length > 0) {
      recommendations.push("Enable tree shaking for unused exports");
      recommendations.push(
        "Consider dynamic imports for non-critical features"
      );
      recommendations.push("Implement component-level code splitting");
    }

    return recommendations;
  }

  /**
   * Check for potential duplicate dependencies across bundles
   */
  private checkForDuplicates(bundles: BundleMetrics[]): string[] {
    const recommendations: string[] = [];

    // Simple heuristic: if we have multiple vendor bundles, suggest consolidation
    const vendorBundles = bundles.filter((b) => b.type === "vendor");
    if (vendorBundles.length > 4) {
      recommendations.push(
        `Consider consolidating ${vendorBundles.length} vendor bundles to reduce HTTP requests`
      );
    }

    return recommendations;
  }

  /**
   * Format bytes to human readable format
   */
  private formatBytes(bytes: number): string {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  /**
   * Generate bundle size report for CI/CD
   */
  generateCIReport(report: BundleReport): string {
    let output = "# Bundle Size Report\n\n";

    output += `**Total Size:** ${this.formatBytes(
      report.totalSize
    )} (gzipped: ${this.formatBytes(report.totalGzipSize)})\n\n`;

    if (report.performanceBudget.violations.length > 0) {
      output += "## ⚠️ Performance Budget Violations\n\n";
      report.performanceBudget.violations.forEach((violation) => {
        output += `- ${violation}\n`;
      });
      output += "\n";
    }

    output += "## Bundle Breakdown\n\n";
    output += "| Bundle | Type | Size | Gzipped |\n";
    output += "|--------|------|------|----------|\n";

    report.bundles
      .sort((a, b) => b.size - a.size)
      .forEach((bundle) => {
        output += `| ${bundle.name} | ${bundle.type} | ${this.formatBytes(
          bundle.size
        )} | ${this.formatBytes(bundle.gzipSize)} |\n`;
      });

    if (report.recommendations.length > 0) {
      output += "\n## 💡 Optimization Recommendations\n\n";
      report.recommendations.forEach((rec) => {
        output += `- ${rec}\n`;
      });
    }

    return output;
  }
}

export const bundleAnalyzer = new BundleAnalyzer();

/**
 * Webpack plugin to analyze bundles during build
 */
export class BundleAnalyzerPlugin {
  apply(compiler: any) {
    compiler.hooks.done.tap("BundleAnalyzerPlugin", (stats: any) => {
      const report = bundleAnalyzer.analyzeBundles(stats.toJson());

      // Log to console
      console.log("\n📊 Bundle Analysis Report:");
      console.log(
        `Total Size: ${bundleAnalyzer["formatBytes"](report.totalSize)}`
      );
      console.log(
        `Gzipped: ${bundleAnalyzer["formatBytes"](report.totalGzipSize)}`
      );

      if (report.performanceBudget.violations.length > 0) {
        console.log("\n⚠️ Performance Budget Violations:");
        report.performanceBudget.violations.forEach((violation) => {
          console.log(`  - ${violation}`);
        });
      }

      if (report.recommendations.length > 0) {
        console.log("\n💡 Recommendations:");
        report.recommendations.slice(0, 3).forEach((rec) => {
          console.log(`  - ${rec}`);
        });
      }

      // Write detailed report to file in CI environments
      if (process.env.CI) {
        const fs = require("fs");
        const path = require("path");
        const reportPath = path.join(
          process.cwd(),
          "bundle-analysis-report.md"
        );
        fs.writeFileSync(reportPath, bundleAnalyzer.generateCIReport(report));
        console.log(`\n📄 Detailed report written to: ${reportPath}`);
      }
    });
  }
}
