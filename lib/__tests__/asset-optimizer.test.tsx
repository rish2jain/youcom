/**
 * Tests for asset optimization utilities
 */

import {
  assetOptimizer,
  fontOptimization,
  OptimizedIcon,
} from "../asset-optimizer";
import React from "react";
import { render } from "@testing-library/react";

describe("AssetOptimizer", () => {
  describe("Image Configuration", () => {
    it("should generate correct image configuration", () => {
      const config = assetOptimizer.generateImageConfig(
        "/test.jpg",
        "Test image",
        true
      );

      expect(config).toEqual({
        src: "/test.jpg",
        alt: "Test image",
        priority: true,
        quality: 85,
        placeholder: "blur",
        sizes: "(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw",
        style: {
          width: "100%",
          height: "auto",
        },
      });
    });

    it("should handle non-priority images", () => {
      const config = assetOptimizer.generateImageConfig(
        "/test.jpg",
        "Test image"
      );

      expect(config.priority).toBe(false);
    });
  });

  describe("Font Configuration", () => {
    it("should generate font configuration with preload settings", () => {
      const config = assetOptimizer.generateFontConfig();

      expect(config.preload).toEqual(["Inter", "system-ui"]);
      expect(config.display).toBe("swap");
      expect(config.subset).toBe(true);
      expect(config.fontFace).toContain("font-family: 'Inter'");
      expect(config.fontFace).toContain("font-display: swap");
    });
  });

  describe("SVG Optimization", () => {
    it("should optimize SVG content by removing comments", () => {
      const svgWithComments = `
        <svg>
          <!-- This is a comment -->
          <path d="M10 10"/>
          <!-- Another comment -->
        </svg>
      `;

      const optimized = assetOptimizer.optimizeSVG(svgWithComments);

      expect(optimized).not.toContain("<!-- This is a comment -->");
      expect(optimized).not.toContain("<!-- Another comment -->");
      expect(optimized).toContain('<path d="M10 10"/>');
    });

    it("should remove metadata from SVG", () => {
      const svgWithMetadata = `
        <svg>
          <metadata>Some metadata</metadata>
          <title>SVG Title</title>
          <desc>SVG Description</desc>
          <path d="M10 10"/>
        </svg>
      `;

      const optimized = assetOptimizer.optimizeSVG(svgWithMetadata);

      expect(optimized).not.toContain("<metadata>");
      expect(optimized).not.toContain("<title>");
      expect(optimized).not.toContain("<desc>");
      expect(optimized).toContain('<path d="M10 10"/>');
    });

    it("should remove unnecessary whitespace", () => {
      const svgWithWhitespace = `
        <svg   viewBox="0 0 24 24"    >
          <path    d="M10 10"   />
        </svg>
      `;

      const optimized = assetOptimizer.optimizeSVG(svgWithWhitespace);

      expect(optimized).not.toContain("   ");
      expect(optimized.trim()).toBe(optimized);
    });
  });

  describe("Icon Sprite Configuration", () => {
    it("should generate icon sprite configuration", () => {
      const icons = ["chevron-right", "search", "user"];
      const config = assetOptimizer.generateIconSpriteConfig(icons);

      expect(config.icons).toEqual(icons);
      expect(config.spriteId).toBe("icon-sprite");
      expect(config.className).toBe("icon");
      expect(typeof config.template).toBe("function");
    });

    it("should generate sprite template with symbols", () => {
      const icons = ["chevron-right", "search"];
      const config = assetOptimizer.generateIconSpriteConfig(icons);
      const template = config.template(icons);

      expect(template).toContain('<svg xmlns="http://www.w3.org/2000/svg"');
      expect(template).toContain('id="icon-chevron-right"');
      expect(template).toContain('id="icon-search"');
      expect(template).toContain('viewBox="0 0 24 24"');
    });
  });

  describe("Compression Metrics", () => {
    it("should calculate compression metrics correctly", () => {
      const metrics = assetOptimizer.calculateCompressionMetrics(1000, 700);

      expect(metrics.originalSize).toBe(1000);
      expect(metrics.optimizedSize).toBe(700);
      expect(metrics.compressionRatio).toBe(30);
      expect(metrics.savings).toBe(300);
      expect(metrics.savingsFormatted).toBe("300 Bytes");
    });

    it("should handle zero compression", () => {
      const metrics = assetOptimizer.calculateCompressionMetrics(1000, 1000);

      expect(metrics.compressionRatio).toBe(0);
      expect(metrics.savings).toBe(0);
    });

    it("should handle perfect compression", () => {
      const metrics = assetOptimizer.calculateCompressionMetrics(1000, 0);

      expect(metrics.compressionRatio).toBe(100);
      expect(metrics.savings).toBe(1000);
    });
  });

  describe("Optimization Report", () => {
    it("should generate comprehensive optimization report", () => {
      const assets = [
        {
          originalPath: "/image1.jpg",
          optimizedPath: "/image1.webp",
          originalSize: 1000,
          optimizedSize: 700,
          compressionRatio: 30,
          format: "image/webp",
        },
        {
          originalPath: "/image2.png",
          optimizedPath: "/image2.avif",
          originalSize: 2000,
          optimizedSize: 1200,
          compressionRatio: 40,
          format: "image/avif",
        },
      ];

      const report = assetOptimizer.generateOptimizationReport(assets);

      expect(report.summary.totalAssets).toBe(2);
      expect(report.summary.totalOriginalSize).toBe("2.93 KB");
      expect(report.summary.totalOptimizedSize).toBe("1.86 KB");
      expect(report.summary.averageCompression).toBe(35);
      expect(report.assets).toHaveLength(2);
      expect(report.recommendations).toContain(
        "Use WebP/AVIF formats for better compression"
      );
    });

    it("should generate recommendations for large images", () => {
      const assets = [
        {
          originalPath: "/large-image.jpg",
          optimizedPath: "/large-image.webp",
          originalSize: 2000000,
          optimizedSize: 600000, // Still large after optimization
          compressionRatio: 70,
          format: "image/webp",
        },
      ];

      const report = assetOptimizer.generateOptimizationReport(assets);

      expect(report.recommendations).toContain(
        "Consider further compression for 1 large image"
      );
    });

    it("should recommend lazy loading for many assets", () => {
      const assets = Array.from({ length: 25 }, (_, i) => ({
        originalPath: `/image${i}.jpg`,
        optimizedPath: `/image${i}.webp`,
        originalSize: 1000,
        optimizedSize: 700,
        compressionRatio: 30,
        format: "image/webp",
      }));

      const report = assetOptimizer.generateOptimizationReport(assets);

      expect(report.recommendations).toContain(
        "Consider implementing lazy loading for non-critical images"
      );
    });
  });
});

describe("FontOptimization", () => {
  describe("Preload Links Generation", () => {
    it("should generate preload links for fonts", () => {
      const fonts = ["Inter", "JetBrains Mono"];
      const links = fontOptimization.generatePreloadLinks(fonts);

      expect(links).toHaveLength(2);
      expect(links[0]).toEqual({
        rel: "preload",
        href: "/fonts/inter.woff2",
        as: "font",
        type: "font/woff2",
        crossOrigin: "anonymous",
      });
      expect(links[1]).toEqual({
        rel: "preload",
        href: "/fonts/jetbrains-mono.woff2",
        as: "font",
        type: "font/woff2",
        crossOrigin: "anonymous",
      });
    });
  });

  describe("Font CSS Generation", () => {
    it("should generate font CSS for multiple weights", () => {
      const css = fontOptimization.generateFontCSS("Inter", [400, 700]);

      expect(css).toContain("font-family: 'Inter'");
      expect(css).toContain("font-weight: 400");
      expect(css).toContain("font-weight: 700");
      expect(css).toContain("font-display: swap");
      expect(css).toContain("inter-400.woff2");
      expect(css).toContain("inter-700.woff2");
    });

    it("should handle single weight", () => {
      const css = fontOptimization.generateFontCSS("Roboto", [400]);

      expect(css).toContain("font-weight: 400");
      expect(css).not.toContain("font-weight: 700");
    });
  });
});

describe("OptimizedIcon Component", () => {
  it("should render icon with correct attributes", () => {
    const { container } = render(
      <OptimizedIcon name="search" size={24} className="test-class" />
    );

    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveAttribute("width", "24");
    expect(svg).toHaveAttribute("height", "24");
    expect(svg).toHaveClass("icon", "icon-search", "test-class");
    expect(svg).toHaveAttribute("aria-hidden", "true");

    const use = container.querySelector("use");
    expect(use).toBeInTheDocument();
    expect(use).toHaveAttribute("href", "#icon-search");
  });

  it("should use default size when not specified", () => {
    const { container } = render(<OptimizedIcon name="user" />);

    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("width", "24");
    expect(svg).toHaveAttribute("height", "24");
  });

  it("should handle string size values", () => {
    const { container } = render(<OptimizedIcon name="settings" size="32" />);

    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("width", "32");
    expect(svg).toHaveAttribute("height", "32");
  });
});

describe("Asset Optimization Middleware", () => {
  it("should create middleware with correct headers", () => {
    const middleware = assetOptimizer.createAssetOptimizationMiddleware();

    expect(middleware.images["Cache-Control"]).toBe(
      "public, max-age=31536000, immutable"
    );
    expect(middleware.images["X-Content-Type-Options"]).toBe("nosniff");

    expect(middleware.fonts["Cache-Control"]).toBe(
      "public, max-age=31536000, immutable"
    );
    expect(middleware.fonts["Access-Control-Allow-Origin"]).toBe("*");

    expect(middleware.svg["Cache-Control"]).toBe("public, max-age=2592000");
    expect(middleware.svg["Content-Type"]).toBe("image/svg+xml");
  });
});
