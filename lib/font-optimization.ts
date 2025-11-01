/**
 * Font Optimization Configuration
 * Handles font loading, subsetting, and performance optimization
 */

export interface FontConfig {
  family: string;
  weights: number[];
  styles: string[];
  display: "auto" | "block" | "swap" | "fallback" | "optional";
  preload: boolean;
  subset?: string;
}

export interface FontOptimizationResult {
  originalSize: number;
  optimizedSize: number;
  compressionRatio: number;
  loadTime: number;
  renderTime: number;
}

class FontOptimizer {
  private fonts: Map<string, FontConfig> = new Map();
  private loadedFonts: Set<string> = new Set();

  constructor() {
    this.initializeDefaultFonts();
  }

  /**
   * Initialize default font configurations
   */
  private initializeDefaultFonts() {
    // System fonts for fallback
    this.addFont({
      family: "system-ui",
      weights: [400, 500, 600, 700],
      styles: ["normal"],
      display: "swap",
      preload: false,
    });

    // Inter font for primary text
    this.addFont({
      family: "Inter",
      weights: [400, 500, 600, 700],
      styles: ["normal"],
      display: "swap",
      preload: true,
      subset: "latin",
    });

    // Monospace font for code
    this.addFont({
      family: "JetBrains Mono",
      weights: [400, 500],
      styles: ["normal"],
      display: "swap",
      preload: false,
      subset: "latin",
    });
  }

  /**
   * Add font configuration
   */
  addFont(config: FontConfig) {
    this.fonts.set(config.family, config);
  }

  /**
   * Generate font face CSS with optimization
   */
  generateFontFaceCSS(): string {
    let css = "";

    this.fonts.forEach((config, family) => {
      config.weights.forEach((weight) => {
        config.styles.forEach((style) => {
          const fontFileName = this.generateFontFileName(family, weight, style);

          css += `
@font-face {
  font-family: '${family}';
  font-style: ${style};
  font-weight: ${weight};
  font-display: ${config.display};
  src: url('/fonts/${fontFileName}.woff2') format('woff2'),
       url('/fonts/${fontFileName}.woff') format('woff');
  ${
    config.subset
      ? `unicode-range: ${this.getUnicodeRange(config.subset)};`
      : ""
  }
}
`;
        });
      });
    });

    return css;
  }

  /**
   * Generate font preload links
   */
  generatePreloadLinks(): Array<{
    rel: string;
    href: string;
    as: string;
    type: string;
    crossOrigin: string;
  }> {
    const preloadLinks: Array<{
      rel: string;
      href: string;
      as: string;
      type: string;
      crossOrigin: string;
    }> = [];

    this.fonts.forEach((config, family) => {
      if (config.preload) {
        // Preload the most common weight (usually 400)
        const primaryWeight = config.weights.includes(400)
          ? 400
          : config.weights[0];
        const fontFileName = this.generateFontFileName(
          family,
          primaryWeight,
          "normal"
        );

        preloadLinks.push({
          rel: "preload",
          href: `/fonts/${fontFileName}.woff2`,
          as: "font",
          type: "font/woff2",
          crossOrigin: "anonymous",
        });
      }
    });

    return preloadLinks;
  }

  /**
   * Generate optimized font stack
   */
  generateFontStack(primaryFont: string): string {
    const fallbacks = [
      "system-ui",
      "-apple-system",
      "BlinkMacSystemFont",
      '"Segoe UI"',
      "Roboto",
      '"Helvetica Neue"',
      "Arial",
      '"Noto Sans"',
      "sans-serif",
      '"Apple Color Emoji"',
      '"Segoe UI Emoji"',
      '"Segoe UI Symbol"',
      '"Noto Color Emoji"',
    ];

    return `"${primaryFont}", ${fallbacks.join(", ")}`;
  }

  /**
   * Generate font file name
   */
  private generateFontFileName(
    family: string,
    weight: number,
    style: string
  ): string {
    const familySlug = family.toLowerCase().replace(/\s+/g, "-");
    const styleSlug = style === "normal" ? "" : `-${style}`;
    return `${familySlug}-${weight}${styleSlug}`;
  }

  /**
   * Get unicode range for font subsetting
   */
  private getUnicodeRange(subset: string): string {
    const ranges: Record<string, string> = {
      latin:
        "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
      "latin-ext":
        "U+0100-024F, U+0259, U+1E00-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, U+2113, U+2C60-2C7F, U+A720-A7FF",
      cyrillic: "U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116",
      greek: "U+0370-03FF",
      vietnamese:
        "U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+1EA0-1EF9, U+20AB",
    };

    return ranges[subset] || ranges.latin;
  }

  /**
   * Optimize font loading performance
   */
  optimizeFontLoading(): {
    criticalCSS: string;
    nonCriticalCSS: string;
    preloadLinks: Array<any>;
  } {
    const criticalFonts = Array.from(this.fonts.entries())
      .filter(([, config]) => config.preload)
      .map(([family]) => family);

    const criticalCSS = this.generateCriticalFontCSS(criticalFonts);
    const nonCriticalCSS = this.generateNonCriticalFontCSS();
    const preloadLinks = this.generatePreloadLinks();

    return {
      criticalCSS,
      nonCriticalCSS,
      preloadLinks,
    };
  }

  /**
   * Generate critical font CSS (inlined)
   */
  private generateCriticalFontCSS(criticalFonts: string[]): string {
    let css = "";

    criticalFonts.forEach((family) => {
      const config = this.fonts.get(family);
      if (config) {
        // Only include the primary weight for critical CSS
        const primaryWeight = config.weights.includes(400)
          ? 400
          : config.weights[0];
        const fontFileName = this.generateFontFileName(
          family,
          primaryWeight,
          "normal"
        );

        css += `
@font-face {
  font-family: '${family}';
  font-style: normal;
  font-weight: ${primaryWeight};
  font-display: ${config.display};
  src: url('/fonts/${fontFileName}.woff2') format('woff2');
  ${
    config.subset
      ? `unicode-range: ${this.getUnicodeRange(config.subset)};`
      : ""
  }
}
`;
      }
    });

    return css;
  }

  /**
   * Generate non-critical font CSS (loaded asynchronously)
   */
  private generateNonCriticalFontCSS(): string {
    let css = "";

    this.fonts.forEach((config, family) => {
      config.weights.forEach((weight) => {
        config.styles.forEach((style) => {
          // Skip primary weight/style as it's in critical CSS
          if (config.preload && weight === 400 && style === "normal") {
            return;
          }

          const fontFileName = this.generateFontFileName(family, weight, style);

          css += `
@font-face {
  font-family: '${family}';
  font-style: ${style};
  font-weight: ${weight};
  font-display: ${config.display};
  src: url('/fonts/${fontFileName}.woff2') format('woff2'),
       url('/fonts/${fontFileName}.woff') format('woff');
  ${
    config.subset
      ? `unicode-range: ${this.getUnicodeRange(config.subset)};`
      : ""
  }
}
`;
        });
      });
    });

    return css;
  }

  /**
   * Monitor font loading performance
   */
  monitorFontPerformance(): Promise<FontOptimizationResult[]> {
    return new Promise((resolve) => {
      if (typeof window === "undefined") {
        resolve([]);
        return;
      }

      const results: FontOptimizationResult[] = [];
      const startTime = performance.now();

      // Use Font Loading API if available
      if ("fonts" in document) {
        document.fonts.ready.then(() => {
          const loadTime = performance.now() - startTime;

          document.fonts.forEach((font) => {
            results.push({
              originalSize: 0, // Would need actual font file size
              optimizedSize: 0, // Would need optimized font file size
              compressionRatio: 0,
              loadTime,
              renderTime: performance.now() - startTime,
            });
          });

          resolve(results);
        });
      } else {
        // Fallback for browsers without Font Loading API
        setTimeout(() => {
          resolve([
            {
              originalSize: 0,
              optimizedSize: 0,
              compressionRatio: 0,
              loadTime: performance.now() - startTime,
              renderTime: performance.now() - startTime,
            },
          ]);
        }, 100);
      }
    });
  }

  /**
   * Generate Tailwind CSS font configuration
   */
  generateTailwindFontConfig(): Record<string, string[]> {
    const fontConfig: Record<string, string[]> = {};

    this.fonts.forEach((config, family) => {
      const key = family.toLowerCase().replace(/\s+/g, "-");
      fontConfig[key] = this.generateFontStack(family).split(", ");
    });

    return fontConfig;
  }
}

export const fontOptimizer = new FontOptimizer();

/**
 * Get font loading optimization utilities
 */
export async function getFontOptimizationUtils() {
  const fontMetrics = await fontOptimizer.monitorFontPerformance();

  return {
    fontsLoaded: true,
    fontMetrics,
    fontStack: fontOptimizer.generateFontStack("Inter"),
  };
}

/**
 * Font optimization configuration for Next.js
 */
export const nextFontConfig = {
  preload: fontOptimizer.generatePreloadLinks(),
  fontFaceCSS: fontOptimizer.generateFontFaceCSS(),
  criticalCSS: fontOptimizer.optimizeFontLoading().criticalCSS,
  tailwindConfig: fontOptimizer.generateTailwindFontConfig(),
};
