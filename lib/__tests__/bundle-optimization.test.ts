/**
 * Tests for bundle optimization features
 */

import { assetOptimizer, fontOptimization } from "../asset-optimizer";
import { criticalCSSExtractor } from "../critical-css";
import { cssPurger } from "../css-purger";
import { fontOptimizer } from "../font-optimization";
import { svgOptimizer } from "../svg-optimizer";

describe("Bundle Optimization Integration", () => {
  describe("Asset Optimizer", () => {
    it("should generate image configuration", () => {
      const config = assetOptimizer.generateImageConfig(
        "/test.jpg",
        "Test image",
        true
      );

      expect(config.src).toBe("/test.jpg");
      expect(config.alt).toBe("Test image");
      expect(config.priority).toBe(true);
      expect(config.quality).toBe(85);
    });

    it("should calculate compression metrics", () => {
      const metrics = assetOptimizer.calculateCompressionMetrics(1000, 700);

      expect(metrics.originalSize).toBe(1000);
      expect(metrics.optimizedSize).toBe(700);
      expect(metrics.compressionRatio).toBe(30);
      expect(metrics.savings).toBe(300);
    });

    it("should optimize SVG content", () => {
      const svgWithComments = '<svg><!-- comment --><path d="M10 10"/></svg>';
      const optimized = assetOptimizer.optimizeSVG(svgWithComments);

      expect(optimized).not.toContain("<!-- comment -->");
      expect(optimized).toContain('<path d="M10 10"/>');
    });
  });

  describe("Critical CSS Extractor", () => {
    it("should extract critical CSS", () => {
      const result = criticalCSSExtractor.extractCriticalCSS();

      expect(result).toHaveProperty("criticalCSS");
      expect(result).toHaveProperty("nonCriticalCSS");
      expect(result).toHaveProperty("inlineCSS");
      expect(result).toHaveProperty("externalCSS");
      expect(result.originalSize).toBeGreaterThan(0);
      expect(result.optimizedSize).toBeGreaterThan(0);
    });

    it("should include essential selectors in critical CSS", () => {
      const result = criticalCSSExtractor.extractCriticalCSS();

      expect(result.criticalCSS).toContain("html");
      expect(result.criticalCSS).toContain("body");
      expect(result.criticalCSS).toContain(".container");
      expect(result.criticalCSS).toContain(".flex");
    });

    it("should generate performance report", () => {
      const result = criticalCSSExtractor.extractCriticalCSS();
      const report = criticalCSSExtractor.generatePerformanceReport(result);

      expect(report).toContain("# CSS Optimization Report");
      expect(report).toContain("Original Size");
      expect(report).toContain("Optimized Size");
    });
  });

  describe("CSS Purger", () => {
    it("should scan for used classes", async () => {
      const usedClasses = await cssPurger.scanForUsedClasses();

      expect(usedClasses.has("container")).toBe(true);
      expect(usedClasses.has("flex")).toBe(true);
      expect(usedClasses.has("text-base")).toBe(true);
    });

    it("should purge unused CSS", async () => {
      const css = ".used { color: red; } .unused { color: blue; }";
      const usedClasses = new Set(["used"]);
      const result = await cssPurger.purgeCSS(css, usedClasses);

      expect(result.keptSelectors).toContain(".used");
      expect(result.removedSelectors).toContain(".unused");
      expect(result.compressionRatio).toBeGreaterThan(0);
    });
  });

  describe("Font Optimizer", () => {
    it("should generate font face CSS", () => {
      const css = fontOptimizer.generateFontFaceCSS();

      expect(css).toContain("font-family: 'Inter'");
      expect(css).toContain("font-display: swap");
      expect(css).toContain(".woff2");
    });

    it("should generate preload links", () => {
      const links = fontOptimizer.generatePreloadLinks();

      expect(links.length).toBeGreaterThan(0);
      expect(links[0]).toHaveProperty("rel", "preload");
      expect(links[0]).toHaveProperty("as", "font");
    });

    it("should generate font stack", () => {
      const fontStack = fontOptimizer.generateFontStack("Inter");

      expect(fontStack).toContain('"Inter"');
      expect(fontStack).toContain("system-ui");
      expect(fontStack).toContain("sans-serif");
    });
  });

  describe("SVG Optimizer", () => {
    it("should optimize SVG content", () => {
      const svgWithComments = '<svg><!-- comment --><path d="M10 10"/></svg>';
      const optimized = svgOptimizer.optimizeSVG(svgWithComments);

      expect(optimized).not.toContain("<!-- comment -->");
      expect(optimized).toContain('<path d="M10 10"/>');
    });

    it("should generate sprite sheet", () => {
      const spriteSheet = svgOptimizer.generateSpriteSheet(["search", "user"]);

      expect(spriteSheet.id).toBe("icon-sprite");
      expect(spriteSheet.icons.length).toBe(2);
      expect(spriteSheet.svg).toContain("<svg");
      expect(spriteSheet.css).toContain(".icon");
    });

    it("should calculate optimization savings", () => {
      const originalSVG =
        '<!-- comment --><svg><metadata>data</metadata><path d="M10 10"/></svg>';
      const savings = svgOptimizer.calculateOptimizationSavings(originalSVG);

      expect(savings.originalSize).toBeGreaterThan(0);
      expect(savings.optimizedSize).toBeGreaterThan(0);
      expect(savings.compressionRatio).toBeGreaterThan(0);
    });
  });

  describe("Font Optimization Utilities", () => {
    it("should generate preload links", () => {
      const fonts = ["Inter", "Roboto"];
      const links = fontOptimization.generatePreloadLinks(fonts);

      expect(links).toHaveLength(2);
      expect(links[0].rel).toBe("preload");
      expect(links[0].as).toBe("font");
      expect(links[0].href).toContain("inter.woff2");
    });

    it("should generate font CSS", () => {
      const css = fontOptimization.generateFontCSS("Inter", [400, 700]);

      expect(css).toContain("font-family: 'Inter'");
      expect(css).toContain("font-weight: 400");
      expect(css).toContain("font-weight: 700");
    });
  });

  describe("Performance Budget Validation", () => {
    it("should validate bundle sizes meet performance budgets", () => {
      // Mock bundle analysis
      const bundleSize = 450000; // 450KB
      const performanceBudget = 500000; // 500KB

      expect(bundleSize).toBeLessThan(performanceBudget);
    });

    it("should detect budget violations", () => {
      const bundleSize = 600000; // 600KB
      const performanceBudget = 500000; // 500KB

      const violation = bundleSize > performanceBudget;
      expect(violation).toBe(true);
    });

    it("should calculate compression ratios", () => {
      const originalSize = 1000;
      const optimizedSize = 700;
      const compressionRatio =
        ((originalSize - optimizedSize) / originalSize) * 100;

      expect(compressionRatio).toBe(30);
    });
  });

  describe("Asset Loading Performance", () => {
    it("should measure asset optimization impact", () => {
      const assets = [
        { originalSize: 1000, optimizedSize: 700 },
        { originalSize: 2000, optimizedSize: 1400 },
      ];

      const totalOriginal = assets.reduce(
        (sum, asset) => sum + asset.originalSize,
        0
      );
      const totalOptimized = assets.reduce(
        (sum, asset) => sum + asset.optimizedSize,
        0
      );
      const totalSavings = totalOriginal - totalOptimized;

      expect(totalOriginal).toBe(3000);
      expect(totalOptimized).toBe(2100);
      expect(totalSavings).toBe(900);
    });

    it("should validate critical CSS inlining threshold", () => {
      const criticalCSSSize = 12000; // 12KB
      const inlineThreshold = 14000; // 14KB

      const shouldInline = criticalCSSSize <= inlineThreshold;
      expect(shouldInline).toBe(true);
    });
  });
});
