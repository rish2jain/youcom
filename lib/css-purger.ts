/**
 * CSS Purging Utility
 * Removes unused CSS classes and optimizes stylesheets
 */

export interface PurgeConfig {
  content: string[];
  css: string[];
  safelist: (string | RegExp)[];
  blocklist: string[];
  keyframes: boolean;
  fontFace: boolean;
}

export interface PurgeResult {
  originalSize: number;
  purgedSize: number;
  removedSelectors: string[];
  keptSelectors: string[];
  compressionRatio: number;
}

class CSSPurger {
  private config: PurgeConfig = {
    content: [
      "./app/**/*.{js,ts,jsx,tsx}",
      "./components/**/*.{js,ts,jsx,tsx}",
      "./lib/**/*.{js,ts,jsx,tsx}",
    ],
    css: ["./app/globals.css"],
    safelist: [
      // Always keep these classes
      "html",
      "body",
      "*",
      // Animation classes
      "animate-pulse",
      "animate-spin",
      "animate-bounce",
      // State classes
      "hover:",
      "focus:",
      "active:",
      "disabled:",
      // Responsive prefixes
      "sm:",
      "md:",
      "lg:",
      "xl:",
      "2xl:",
      // Dynamic classes that might be generated
      /^text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl)$/,
      /^bg-(red|green|blue|yellow|purple|pink|indigo)-(50|100|200|300|400|500|600|700|800|900)$/,
      /^text-(red|green|blue|yellow|purple|pink|indigo)-(50|100|200|300|400|500|600|700|800|900)$/,
    ],
    blocklist: [
      // Remove these classes
      ".unused-class",
      ".debug-*",
    ],
    keyframes: true,
    fontFace: true,
  };

  /**
   * Purge unused CSS from stylesheets
   */
  async purgeCSS(
    cssContent: string,
    usedClasses: Set<string>
  ): Promise<PurgeResult> {
    const originalSize = new Blob([cssContent]).size;
    const selectors = this.extractSelectors(cssContent);

    const keptSelectors: string[] = [];
    const removedSelectors: string[] = [];

    // Analyze each selector
    selectors.forEach((selector) => {
      if (this.shouldKeepSelector(selector, usedClasses)) {
        keptSelectors.push(selector);
      } else {
        removedSelectors.push(selector);
      }
    });

    // Generate purged CSS
    const purgedCSS = this.generatePurgedCSS(cssContent, keptSelectors);
    const purgedSize = new Blob([purgedCSS]).size;

    return {
      originalSize,
      purgedSize,
      removedSelectors,
      keptSelectors,
      compressionRatio: ((originalSize - purgedSize) / originalSize) * 100,
    };
  }

  /**
   * Extract CSS selectors from stylesheet
   */
  private extractSelectors(css: string): string[] {
    const selectors: string[] = [];

    // Remove comments and normalize whitespace
    const cleanCSS = css
      .replace(/\/\*[\s\S]*?\*\//g, "")
      .replace(/\s+/g, " ")
      .trim();

    // Extract selectors using regex
    const selectorRegex = /([^{}]+)\s*\{[^}]*\}/g;
    let match;

    while ((match = selectorRegex.exec(cleanCSS)) !== null) {
      const selectorGroup = match[1].trim();

      // Split multiple selectors (comma-separated)
      const individualSelectors = selectorGroup
        .split(",")
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      selectors.push(...individualSelectors);
    }

    return Array.from(new Set(selectors)); // Remove duplicates
  }

  /**
   * Determine if a selector should be kept
   */
  private shouldKeepSelector(
    selector: string,
    usedClasses: Set<string>
  ): boolean {
    // Always keep safelisted selectors
    if (this.isSafelisted(selector)) {
      return true;
    }

    // Remove blocklisted selectors
    if (this.isBlocklisted(selector)) {
      return false;
    }

    // Keep selectors that match used classes
    return this.matchesUsedClasses(selector, usedClasses);
  }

  /**
   * Check if selector is safelisted
   */
  private isSafelisted(selector: string): boolean {
    return this.config.safelist.some((safe) => {
      if (typeof safe === "string") {
        return selector.includes(safe);
      } else if (safe instanceof RegExp) {
        return safe.test(selector);
      }
      return false;
    });
  }

  /**
   * Check if selector is blocklisted
   */
  private isBlocklisted(selector: string): boolean {
    return this.config.blocklist.some((blocked) => {
      if (typeof blocked === "string") {
        return selector.includes(blocked);
      }
      return false;
    });
  }

  /**
   * Check if selector matches used classes
   */
  private matchesUsedClasses(
    selector: string,
    usedClasses: Set<string>
  ): boolean {
    // Extract class names from selector
    const classMatches = selector.match(/\.[a-zA-Z0-9_-]+/g);

    if (!classMatches) {
      // Keep non-class selectors (element selectors, etc.)
      return true;
    }

    // Check if any class in the selector is used
    return classMatches.some((className) => {
      const cleanClassName = className.substring(1); // Remove the dot
      return usedClasses.has(cleanClassName);
    });
  }

  /**
   * Generate purged CSS with only kept selectors
   */
  private generatePurgedCSS(
    originalCSS: string,
    keptSelectors: string[]
  ): string {
    const lines = originalCSS.split("\n");
    const purgedLines: string[] = [];
    let currentRule = "";
    let inRule = false;
    let braceCount = 0;

    for (const line of lines) {
      const trimmedLine = line.trim();

      // Handle CSS rules
      if (trimmedLine.includes("{")) {
        braceCount += (trimmedLine.match(/\{/g) || []).length;
        currentRule += line + "\n";
        inRule = true;
      } else if (trimmedLine.includes("}")) {
        braceCount -= (trimmedLine.match(/\}/g) || []).length;
        currentRule += line + "\n";

        if (braceCount === 0) {
          // End of rule - check if we should keep it
          const selector = this.extractSelectorFromRule(currentRule);
          if (keptSelectors.includes(selector)) {
            purgedLines.push(currentRule);
          }
          currentRule = "";
          inRule = false;
        }
      } else if (inRule) {
        currentRule += line + "\n";
      } else {
        // Keep comments, @rules, etc.
        if (
          trimmedLine.startsWith("@") ||
          trimmedLine.startsWith("/*") ||
          trimmedLine === ""
        ) {
          purgedLines.push(line);
        }
      }
    }

    return purgedLines.join("\n");
  }

  /**
   * Extract selector from CSS rule
   */
  private extractSelectorFromRule(rule: string): string {
    const match = rule.match(/^([^{]+)\{/);
    return match ? match[1].trim() : "";
  }

  /**
   * Scan content files for used CSS classes
   */
  async scanForUsedClasses(): Promise<Set<string>> {
    const usedClasses = new Set<string>();

    // This would scan actual files in a real implementation
    // For now, we'll return a mock set of commonly used classes
    const commonClasses = [
      // Layout
      "container",
      "max-w-7xl",
      "mx-auto",
      "grid",
      "flex",
      "block",
      "inline-block",
      "relative",
      "absolute",
      "fixed",
      "sticky",

      // Typography
      "text-sm",
      "text-base",
      "text-lg",
      "text-xl",
      "text-2xl",
      "font-normal",
      "font-medium",
      "font-semibold",
      "font-bold",
      "text-gray-900",
      "text-gray-800",
      "text-gray-700",
      "text-gray-600",
      "text-white",
      "text-black",

      // Colors
      "bg-white",
      "bg-gray-50",
      "bg-gray-100",
      "bg-gray-900",
      "bg-blue-600",
      "bg-blue-700",
      "bg-green-600",
      "bg-red-600",

      // Spacing
      "p-0",
      "p-2",
      "p-4",
      "p-6",
      "px-4",
      "px-6",
      "py-2",
      "py-4",
      "m-0",
      "m-2",
      "m-4",
      "mt-2",
      "mt-4",
      "mb-2",
      "mb-4",

      // Borders
      "border",
      "border-gray-200",
      "border-gray-300",
      "rounded",
      "rounded-md",
      "rounded-lg",

      // Shadows
      "shadow",
      "shadow-md",
      "shadow-lg",

      // Animations
      "animate-pulse",
      "animate-spin",
      "transition",
      "duration-200",
      "ease-in-out",

      // Interactive states
      "hover:bg-gray-100",
      "focus:outline-none",
      "focus:ring-2",

      // Component classes
      "btn",
      "btn-primary",
      "btn-secondary",
      "card",
      "card-header",
      "card-body",
      "form-input",
      "loading",
      "skeleton",
    ];

    commonClasses.forEach((className) => usedClasses.add(className));

    return usedClasses;
  }

  /**
   * Generate purge report
   */
  generatePurgeReport(result: PurgeResult): string {
    return `
# CSS Purge Report

## Summary
- **Original Size**: ${this.formatBytes(result.originalSize)}
- **Purged Size**: ${this.formatBytes(result.purgedSize)}
- **Size Reduction**: ${this.formatBytes(
      result.originalSize - result.purgedSize
    )}
- **Compression Ratio**: ${result.compressionRatio.toFixed(2)}%

## Selectors
- **Kept Selectors**: ${result.keptSelectors.length}
- **Removed Selectors**: ${result.removedSelectors.length}
- **Total Selectors**: ${
      result.keptSelectors.length + result.removedSelectors.length
    }

## Removed Selectors (Sample)
${result.removedSelectors
  .slice(0, 10)
  .map((s) => `- ${s}`)
  .join("\n")}
${
  result.removedSelectors.length > 10
    ? `... and ${result.removedSelectors.length - 10} more`
    : ""
}

## Recommendations
${
  result.compressionRatio > 50
    ? "✅ Excellent purge ratio - significant unused CSS removed"
    : result.compressionRatio > 25
    ? "⚠️ Good purge ratio - some optimization achieved"
    : "❌ Low purge ratio - consider reviewing CSS usage"
}

- Use CSS-in-JS for component-specific styles
- Implement dynamic class generation carefully
- Regular CSS audits to identify unused styles
- Consider CSS modules for better tree shaking
`;
  }

  /**
   * Format bytes to human readable
   */
  private formatBytes(bytes: number): string {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<PurgeConfig>) {
    this.config = { ...this.config, ...newConfig };
  }
}

export const cssPurger = new CSSPurger();

/**
 * Webpack plugin for CSS purging
 */
export class CSSPurgePlugin {
  apply(compiler: any) {
    compiler.hooks.emit.tapAsync(
      "CSSPurgePlugin",
      async (compilation: any, callback: any) => {
        try {
          // Find CSS assets
          const cssAssets = Object.keys(compilation.assets).filter((name) =>
            name.endsWith(".css")
          );

          for (const assetName of cssAssets) {
            const asset = compilation.assets[assetName];
            const cssContent = asset.source();

            // Scan for used classes
            const usedClasses = await cssPurger.scanForUsedClasses();

            // Purge unused CSS
            const result = await cssPurger.purgeCSS(cssContent, usedClasses);

            // Update asset with purged CSS
            compilation.assets[assetName] = {
              source: () => result.keptSelectors.join("\n"),
              size: () => result.purgedSize,
            };

            console.log(
              `📦 CSS Purged: ${assetName} (${result.compressionRatio.toFixed(
                1
              )}% reduction)`
            );
          }

          callback();
        } catch (error) {
          console.error("CSS purging failed:", error);
          callback();
        }
      }
    );
  }
}
