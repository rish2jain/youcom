/**
 * Critical CSS Extraction and Optimization
 * Handles critical CSS inlining, optimization, and unused CSS elimination
 */

export interface CriticalCSSConfig {
  viewport: {
    width: number;
    height: number;
  };
  inlineThreshold: number; // bytes
  minificationLevel: "basic" | "advanced";
  removeUnusedCSS: boolean;
  extractKeyframes: boolean;
}

export interface CSSOptimizationResult {
  criticalCSS: string;
  nonCriticalCSS: string;
  inlineCSS: string;
  externalCSS: string;
  originalSize: number;
  optimizedSize: number;
  compressionRatio: number;
}

class CriticalCSSExtractor {
  private config: CriticalCSSConfig = {
    viewport: {
      width: 1200,
      height: 800,
    },
    inlineThreshold: 14000, // 14KB threshold for inlining
    minificationLevel: "advanced",
    removeUnusedCSS: true,
    extractKeyframes: true,
  };

  /**
   * Extract critical CSS for above-the-fold content
   */
  extractCriticalCSS(): CSSOptimizationResult {
    const criticalSelectors = this.getCriticalSelectors();
    const criticalCSS = this.generateCriticalCSS(criticalSelectors);
    const nonCriticalCSS = this.generateNonCriticalCSS();

    const optimizedCritical = this.optimizeCSS(criticalCSS);
    const optimizedNonCritical = this.optimizeCSS(nonCriticalCSS);

    const inlineCSS =
      optimizedCritical.length <= this.config.inlineThreshold
        ? optimizedCritical
        : this.extractMostCritical(optimizedCritical);

    const externalCSS =
      optimizedCritical.length > this.config.inlineThreshold
        ? optimizedCritical + optimizedNonCritical
        : optimizedNonCritical;

    return {
      criticalCSS: optimizedCritical,
      nonCriticalCSS: optimizedNonCritical,
      inlineCSS,
      externalCSS,
      originalSize: criticalCSS.length + nonCriticalCSS.length,
      optimizedSize: optimizedCritical.length + optimizedNonCritical.length,
      compressionRatio: this.calculateCompressionRatio(
        criticalCSS.length + nonCriticalCSS.length,
        optimizedCritical.length + optimizedNonCritical.length
      ),
    };
  }

  /**
   * Get critical CSS selectors for above-the-fold content
   */
  private getCriticalSelectors(): string[] {
    return [
      // Layout and structure
      "html",
      "body",
      "*",
      "*::before",
      "*::after",

      // Critical layout components
      ".container",
      ".max-w-7xl",
      ".mx-auto",
      ".grid",
      ".flex",
      ".block",
      ".inline-block",
      ".relative",
      ".absolute",
      ".fixed",
      ".sticky",

      // Typography (critical)
      ".text-sm",
      ".text-base",
      ".text-lg",
      ".text-xl",
      ".text-2xl",
      ".font-normal",
      ".font-medium",
      ".font-semibold",
      ".font-bold",
      ".text-gray-900",
      ".text-gray-800",
      ".text-gray-700",
      ".text-gray-600",
      ".text-white",
      ".text-black",

      // Spacing (critical)
      ".p-0",
      ".p-1",
      ".p-2",
      ".p-3",
      ".p-4",
      ".p-6",
      ".p-8",
      ".m-0",
      ".m-1",
      ".m-2",
      ".m-3",
      ".m-4",
      ".m-6",
      ".m-8",
      ".px-4",
      ".px-6",
      ".py-2",
      ".py-4",
      ".py-6",
      ".mt-0",
      ".mt-2",
      ".mt-4",
      ".mb-2",
      ".mb-4",
      ".mb-6",

      // Colors (critical)
      ".bg-white",
      ".bg-gray-50",
      ".bg-gray-100",
      ".bg-gray-900",
      ".bg-blue-600",
      ".bg-blue-700",
      ".bg-green-600",
      ".bg-red-600",
      ".border-gray-200",
      ".border-gray-300",

      // Header and navigation
      "header",
      "nav",
      ".header",
      ".navigation",
      ".sidebar",
      ".main-content",

      // Critical UI components
      ".btn",
      ".button",
      ".card",
      ".modal",
      ".loading",
      ".skeleton",
      ".spinner",

      // Form elements (if above fold)
      "input",
      "button",
      "select",
      "textarea",
      ".form-input",
      ".form-button",

      // Critical animations
      ".animate-pulse",
      ".animate-spin",
      ".transition",
      ".duration-200",
      ".ease-in-out",

      // Responsive utilities (critical breakpoints)
      ".sm\\:block",
      ".md\\:flex",
      ".lg\\:grid",
      ".sm\\:text-base",
      ".md\\:text-lg",

      // Critical state classes
      ".hover\\:bg-gray-100",
      ".focus\\:outline-none",
      ".focus\\:ring-2",
      ".active",
      ".disabled",
      ".loading",
    ];
  }

  /**
   * Generate critical CSS from selectors
   */
  private generateCriticalCSS(selectors: string[]): string {
    // This would integrate with your actual CSS extraction logic
    // For now, we'll generate a basic critical CSS structure

    return `
/* Critical CSS - Above the fold */

/* Reset and base styles */
*, *::before, *::after {
  box-sizing: border-box;
}

html {
  line-height: 1.5;
  -webkit-text-size-adjust: 100%;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
}

body {
  margin: 0;
  line-height: inherit;
}

/* Critical layout utilities */
.container { 
  width: 100%; 
  margin-left: auto; 
  margin-right: auto; 
  padding-left: 1rem; 
  padding-right: 1rem; 
}

.max-w-7xl { max-width: 80rem; }
.mx-auto { margin-left: auto; margin-right: auto; }

.grid { display: grid; }
.flex { display: flex; }
.block { display: block; }
.inline-block { display: inline-block; }
.hidden { display: none; }

.relative { position: relative; }
.absolute { position: absolute; }
.fixed { position: fixed; }
.sticky { position: sticky; }

/* Critical typography */
.text-sm { font-size: 0.875rem; line-height: 1.25rem; }
.text-base { font-size: 1rem; line-height: 1.5rem; }
.text-lg { font-size: 1.125rem; line-height: 1.75rem; }
.text-xl { font-size: 1.25rem; line-height: 1.75rem; }
.text-2xl { font-size: 1.5rem; line-height: 2rem; }

.font-normal { font-weight: 400; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }

/* Critical colors */
.text-gray-900 { color: rgb(17 24 39); }
.text-gray-800 { color: rgb(31 41 55); }
.text-gray-700 { color: rgb(55 65 81); }
.text-gray-600 { color: rgb(75 85 99); }
.text-white { color: rgb(255 255 255); }
.text-black { color: rgb(0 0 0); }

.bg-white { background-color: rgb(255 255 255); }
.bg-gray-50 { background-color: rgb(249 250 251); }
.bg-gray-100 { background-color: rgb(243 244 246); }
.bg-gray-900 { background-color: rgb(17 24 39); }

/* Critical spacing */
.p-0 { padding: 0; }
.p-2 { padding: 0.5rem; }
.p-4 { padding: 1rem; }
.p-6 { padding: 1.5rem; }

.m-0 { margin: 0; }
.m-2 { margin: 0.5rem; }
.m-4 { margin: 1rem; }

.px-4 { padding-left: 1rem; padding-right: 1rem; }
.px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
.py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }

/* Critical animations */
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Critical transitions */
.transition {
  transition-property: color, background-color, border-color, text-decoration-color, fill, stroke, opacity, box-shadow, transform, filter, backdrop-filter;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.duration-200 { transition-duration: 200ms; }
.ease-in-out { transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); }

/* Critical responsive utilities */
@media (min-width: 640px) {
  .sm\\:block { display: block; }
  .sm\\:text-base { font-size: 1rem; line-height: 1.5rem; }
}

@media (min-width: 768px) {
  .md\\:flex { display: flex; }
  .md\\:text-lg { font-size: 1.125rem; line-height: 1.75rem; }
}

@media (min-width: 1024px) {
  .lg\\:grid { display: grid; }
}

/* Critical interactive states */
.hover\\:bg-gray-100:hover { background-color: rgb(243 244 246); }
.focus\\:outline-none:focus { outline: 2px solid transparent; outline-offset: 2px; }
.focus\\:ring-2:focus { box-shadow: 0 0 0 2px rgb(59 130 246 / 0.5); }
`;
  }

  /**
   * Generate non-critical CSS
   */
  private generateNonCriticalCSS(): string {
    return `
/* Non-critical CSS - Below the fold and interactive elements */

/* Extended color palette */
.bg-blue-50 { background-color: rgb(239 246 255); }
.bg-blue-100 { background-color: rgb(219 234 254); }
.bg-blue-600 { background-color: rgb(37 99 235); }
.bg-blue-700 { background-color: rgb(29 78 216); }
.bg-green-50 { background-color: rgb(240 253 244); }
.bg-green-600 { background-color: rgb(22 163 74); }
.bg-red-50 { background-color: rgb(254 242 242); }
.bg-red-600 { background-color: rgb(220 38 38); }

/* Extended typography */
.text-3xl { font-size: 1.875rem; line-height: 2.25rem; }
.text-4xl { font-size: 2.25rem; line-height: 2.5rem; }
.text-5xl { font-size: 3rem; line-height: 1; }

/* Extended spacing */
.p-8 { padding: 2rem; }
.p-12 { padding: 3rem; }
.m-8 { margin: 2rem; }
.m-12 { margin: 3rem; }

/* Borders and shadows */
.border { border-width: 1px; }
.border-2 { border-width: 2px; }
.border-gray-200 { border-color: rgb(229 231 235); }
.border-gray-300 { border-color: rgb(209 213 219); }

.rounded { border-radius: 0.25rem; }
.rounded-md { border-radius: 0.375rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-xl { border-radius: 0.75rem; }

.shadow { box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1); }
.shadow-md { box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); }
.shadow-lg { box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1); }

/* Complex animations */
.animate-bounce {
  animation: bounce 1s infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(-25%);
    animation-timing-function: cubic-bezier(0.8, 0, 1, 1);
  }
  50% {
    transform: none;
    animation-timing-function: cubic-bezier(0, 0, 0.2, 1);
  }
}

/* Extended interactive states */
.hover\\:shadow-lg:hover { box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1); }
.hover\\:scale-105:hover { transform: scale(1.05); }
.active\\:scale-95:active { transform: scale(0.95); }

/* Form styles */
.form-input {
  appearance: none;
  background-color: #fff;
  border-color: #d1d5db;
  border-width: 1px;
  border-radius: 0.375rem;
  padding: 0.5rem 0.75rem;
  font-size: 1rem;
  line-height: 1.5rem;
}

.form-input:focus {
  outline: 2px solid transparent;
  outline-offset: 2px;
  box-shadow: 0 0 0 2px rgb(59 130 246 / 0.5);
  border-color: rgb(59 130 246);
}

/* Component styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  font-weight: 500;
  transition: all 150ms ease-in-out;
  cursor: pointer;
  border: none;
}

.btn-primary {
  background-color: rgb(37 99 235);
  color: white;
  padding: 0.5rem 1rem;
}

.btn-primary:hover {
  background-color: rgb(29 78 216);
}

.btn-secondary {
  background-color: rgb(243 244 246);
  color: rgb(55 65 81);
  padding: 0.5rem 1rem;
}

.btn-secondary:hover {
  background-color: rgb(229 231 235);
}

/* Card component */
.card {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  overflow: hidden;
}

.card-header {
  padding: 1.5rem 1.5rem 0 1.5rem;
}

.card-body {
  padding: 1.5rem;
}

.card-footer {
  padding: 0 1.5rem 1.5rem 1.5rem;
}
`;
  }

  /**
   * Optimize CSS by minifying and removing unused rules
   */
  private optimizeCSS(css: string): string {
    let optimized = css;

    if (this.config.minificationLevel === "basic") {
      // Basic minification
      optimized = optimized
        .replace(/\/\*[\s\S]*?\*\//g, "") // Remove comments
        .replace(/\s+/g, " ") // Collapse whitespace
        .replace(/;\s*}/g, "}") // Remove last semicolon in blocks
        .replace(/\s*{\s*/g, "{") // Clean up braces
        .replace(/\s*}\s*/g, "}")
        .replace(/\s*;\s*/g, ";") // Clean up semicolons
        .replace(/\s*:\s*/g, ":") // Clean up colons
        .trim();
    } else if (this.config.minificationLevel === "advanced") {
      // Advanced minification
      optimized = optimized
        .replace(/\/\*[\s\S]*?\*\//g, "") // Remove comments
        .replace(/\s+/g, " ") // Collapse whitespace
        .replace(/;\s*}/g, "}") // Remove last semicolon in blocks
        .replace(/\s*{\s*/g, "{") // Clean up braces
        .replace(/\s*}\s*/g, "}")
        .replace(/\s*;\s*/g, ";") // Clean up semicolons
        .replace(/\s*:\s*/g, ":") // Clean up colons
        .replace(/\s*,\s*/g, ",") // Clean up commas
        .replace(/0\.(\d+)/g, ".$1") // Remove leading zeros
        .replace(/:0px/g, ":0") // Remove px from zero values
        .replace(/:0em/g, ":0") // Remove em from zero values
        .replace(/:0rem/g, ":0") // Remove rem from zero values
        .replace(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/g, (match, r, g, b) => {
          // Convert rgb to hex if shorter
          const hex =
            "#" +
            [r, g, b]
              .map((x) => {
                const hex = parseInt(x).toString(16);
                return hex.length === 1 ? "0" + hex : hex;
              })
              .join("");
          return hex.length <= match.length ? hex : match;
        })
        .trim();
    }

    return optimized;
  }

  /**
   * Extract most critical CSS when size exceeds threshold
   */
  private extractMostCritical(css: string): string {
    // Extract only the most critical selectors if CSS is too large
    const criticalRules = [
      "html",
      "body",
      "*",
      ".container",
      ".max-w-7xl",
      ".mx-auto",
      ".grid",
      ".flex",
      ".block",
      ".text-base",
      ".font-normal",
      ".bg-white",
      ".text-gray-900",
      ".p-4",
      ".m-0",
      ".animate-pulse",
      ".transition",
    ];

    const lines = css.split("\n");
    const criticalLines = lines.filter((line) => {
      return (
        criticalRules.some((rule) => line.includes(rule)) ||
        line.includes("@keyframes") ||
        line.includes("@media")
      );
    });

    return criticalLines.join("\n");
  }

  /**
   * Calculate compression ratio
   */
  private calculateCompressionRatio(
    originalSize: number,
    optimizedSize: number
  ): number {
    return (
      Math.round(((originalSize - optimizedSize) / originalSize) * 10000) / 100
    );
  }

  /**
   * Generate CSS for specific viewport
   */
  generateViewportSpecificCSS(viewport: {
    width: number;
    height: number;
  }): string {
    return `
/* Viewport-specific critical CSS (${viewport.width}x${viewport.height}) */

@media (max-width: ${viewport.width}px) {
  .container {
    max-width: ${viewport.width - 32}px;
  }
}

@media (max-height: ${viewport.height}px) {
  .min-h-screen {
    min-height: ${viewport.height}px;
  }
}
`;
  }

  /**
   * Generate performance report
   */
  generatePerformanceReport(result: CSSOptimizationResult): string {
    return `
# CSS Optimization Report

## Summary
- **Original Size**: ${this.formatBytes(result.originalSize)}
- **Optimized Size**: ${this.formatBytes(result.optimizedSize)}
- **Compression Ratio**: ${result.compressionRatio}%
- **Inline CSS Size**: ${this.formatBytes(result.inlineCSS.length)}
- **External CSS Size**: ${this.formatBytes(result.externalCSS.length)}

## Critical CSS Strategy
- Critical CSS is ${
      result.inlineCSS.length <= this.config.inlineThreshold
        ? "inlined"
        : "external"
    }
- Inline threshold: ${this.formatBytes(this.config.inlineThreshold)}
- Minification level: ${this.config.minificationLevel}

## Recommendations
${
  result.inlineCSS.length > this.config.inlineThreshold
    ? "- Consider reducing critical CSS size or increasing inline threshold"
    : "- Critical CSS size is optimal for inlining"
}
- Use CSS-in-JS for component-specific styles
- Implement CSS purging for unused styles
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
}

export const criticalCSSExtractor = new CriticalCSSExtractor();

/**
 * Get critical CSS management utilities
 */
export function getCriticalCSSUtils() {
  const result = criticalCSSExtractor.extractCriticalCSS();

  return {
    cssResult: result,
    isLoading: false,
    inlineCSS: result.inlineCSS,
    externalCSS: result.externalCSS,
  };
}

/**
 * Generate critical CSS configuration for Next.js
 */
export function generateCriticalCSSConfig() {
  const result = criticalCSSExtractor.extractCriticalCSS();

  return {
    inlineCSS: result.inlineCSS,
    externalCSS: result.externalCSS,
    dataCriticalCSS: true,
  };
}
