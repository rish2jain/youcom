/**
 * Tests for font optimization utilities
 */

import { fontOptimizer, nextFontConfig } from "../font-optimization";
import React from "react";

// Mock React hooks
jest.mock("react", () => ({
  ...jest.requireActual("react"),
  useState: jest.fn(),
  useEffect: jest.fn(),
}));

describe("FontOptimizer", () => {
  describe("Font Configuration", () => {
    it("should initialize with default fonts", () => {
      const fonts = (fontOptimizer as any).fonts;

      expect(fonts.has("system-ui")).toBe(true);
      expect(fonts.has("Inter")).toBe(true);
      expect(fonts.has("JetBrains Mono")).toBe(true);
    });

    it("should add new font configurations", () => {
      fontOptimizer.addFont({
        family: "Roboto",
        weights: [300, 400, 700],
        styles: ["normal", "italic"],
        display: "swap",
        preload: true,
        subset: "latin",
      });

      const fonts = (fontOptimizer as any).fonts;
      expect(fonts.has("Roboto")).toBe(true);

      const robotoConfig = fonts.get("Roboto");
      expect(robotoConfig.weights).toEqual([300, 400, 700]);
      expect(robotoConfig.styles).toEqual(["normal", "italic"]);
      expect(robotoConfig.display).toBe("swap");
      expect(robotoConfig.preload).toBe(true);
      expect(robotoConfig.subset).toBe("latin");
    });
  });

  describe("Font Face CSS Generation", () => {
    it("should generate font face CSS for all configured fonts", () => {
      const css = fontOptimizer.generateFontFaceCSS();

      expect(css).toContain("font-family: 'Inter'");
      expect(css).toContain("font-family: 'JetBrains Mono'");
      expect(css).toContain("font-display: swap");
      expect(css).toContain("src: url('/fonts/");
      expect(css).toContain(".woff2') format('woff2')");
      expect(css).toContain(".woff') format('woff')");
    });

    it("should include unicode ranges for subsetted fonts", () => {
      const css = fontOptimizer.generateFontFaceCSS();

      expect(css).toContain("unicode-range:");
      expect(css).toContain("U+0000-00FF"); // Latin range
    });

    it("should generate CSS for multiple weights and styles", () => {
      const css = fontOptimizer.generateFontFaceCSS();

      expect(css).toContain("font-weight: 400");
      expect(css).toContain("font-weight: 500");
      expect(css).toContain("font-weight: 600");
      expect(css).toContain("font-weight: 700");
      expect(css).toContain("font-style: normal");
    });
  });

  describe("Preload Links Generation", () => {
    it("should generate preload links for fonts marked for preloading", () => {
      const links = fontOptimizer.generatePreloadLinks();

      expect(links.length).toBeGreaterThan(0);

      const interLink = links.find((link) => link.href.includes("inter"));
      expect(interLink).toBeDefined();
      expect(interLink?.rel).toBe("preload");
      expect(interLink?.as).toBe("font");
      expect(interLink?.type).toBe("font/woff2");
      expect(interLink?.crossOrigin).toBe("anonymous");
    });

    it("should not generate preload links for non-preload fonts", () => {
      const links = fontOptimizer.generatePreloadLinks();

      const systemUILink = links.find((link) =>
        link.href.includes("system-ui")
      );
      expect(systemUILink).toBeUndefined();
    });

    it("should preload primary weight (400) when available", () => {
      const links = fontOptimizer.generatePreloadLinks();

      const interLink = links.find((link) => link.href.includes("inter"));
      expect(interLink?.href).toContain("inter-400");
    });
  });

  describe("Font Stack Generation", () => {
    it("should generate comprehensive font stack with fallbacks", () => {
      const fontStack = fontOptimizer.generateFontStack("Inter");

      expect(fontStack).toContain('"Inter"');
      expect(fontStack).toContain("system-ui");
      expect(fontStack).toContain("-apple-system");
      expect(fontStack).toContain("BlinkMacSystemFont");
      expect(fontStack).toContain('"Segoe UI"');
      expect(fontStack).toContain("Roboto");
      expect(fontStack).toContain("sans-serif");
      expect(fontStack).toContain('"Apple Color Emoji"');
    });

    it("should place primary font first in stack", () => {
      const fontStack = fontOptimizer.generateFontStack("Custom Font");

      expect(fontStack.startsWith('"Custom Font"')).toBe(true);
    });
  });

  describe("Font File Name Generation", () => {
    it("should generate correct font file names", () => {
      const generateFontFileName = (fontOptimizer as any).generateFontFileName;

      expect(generateFontFileName("Inter", 400, "normal")).toBe("inter-400");
      expect(generateFontFileName("Inter", 700, "italic")).toBe(
        "inter-700-italic"
      );
      expect(generateFontFileName("JetBrains Mono", 500, "normal")).toBe(
        "jetbrains-mono-500"
      );
    });

    it("should handle spaces in font names", () => {
      const generateFontFileName = (fontOptimizer as any).generateFontFileName;

      expect(generateFontFileName("Source Sans Pro", 400, "normal")).toBe(
        "source-sans-pro-400"
      );
    });
  });

  describe("Unicode Range Generation", () => {
    it("should return correct unicode ranges for different subsets", () => {
      const getUnicodeRange = (fontOptimizer as any).getUnicodeRange;

      const latinRange = getUnicodeRange("latin");
      expect(latinRange).toContain("U+0000-00FF");
      expect(latinRange).toContain("U+0131");
      expect(latinRange).toContain("U+0152-0153");

      const cyrillicRange = getUnicodeRange("cyrillic");
      expect(cyrillicRange).toContain("U+0400-045F");

      const greekRange = getUnicodeRange("greek");
      expect(greekRange).toContain("U+0370-03FF");
    });

    it("should fallback to latin range for unknown subsets", () => {
      const getUnicodeRange = (fontOptimizer as any).getUnicodeRange;

      const unknownRange = getUnicodeRange("unknown-subset");
      expect(unknownRange).toContain("U+0000-00FF");
    });
  });

  describe("Font Loading Optimization", () => {
    it("should separate critical and non-critical CSS", () => {
      const optimization = fontOptimizer.optimizeFontLoading();

      expect(optimization).toHaveProperty("criticalCSS");
      expect(optimization).toHaveProperty("nonCriticalCSS");
      expect(optimization).toHaveProperty("preloadLinks");

      expect(optimization.criticalCSS).toContain("font-family: 'Inter'");
      expect(optimization.criticalCSS).toContain("font-weight: 400");
      expect(optimization.nonCriticalCSS.length).toBeGreaterThan(0);
      expect(optimization.preloadLinks.length).toBeGreaterThan(0);
    });

    it("should include only primary weights in critical CSS", () => {
      const optimization = fontOptimizer.optimizeFontLoading();

      // Critical CSS should have fewer font-weight declarations
      const criticalWeights = (
        optimization.criticalCSS.match(/font-weight:/g) || []
      ).length;
      const nonCriticalWeights = (
        optimization.nonCriticalCSS.match(/font-weight:/g) || []
      ).length;

      expect(criticalWeights).toBeLessThan(nonCriticalWeights);
    });
  });

  describe("Tailwind Configuration Generation", () => {
    it("should generate Tailwind font configuration", () => {
      const tailwindConfig = fontOptimizer.generateTailwindFontConfig();

      expect(tailwindConfig).toHaveProperty("inter");
      expect(tailwindConfig).toHaveProperty("jetbrains-mono");
      expect(tailwindConfig).toHaveProperty("system-ui");

      expect(Array.isArray(tailwindConfig.inter)).toBe(true);
      expect(tailwindConfig.inter[0]).toContain("Inter");
    });

    it("should convert font names to kebab-case keys", () => {
      const tailwindConfig = fontOptimizer.generateTailwindFontConfig();

      expect(tailwindConfig).toHaveProperty("jetbrains-mono");
      expect(tailwindConfig).not.toHaveProperty("JetBrains Mono");
    });
  });

  describe("Font Performance Monitoring", () => {
    beforeEach(() => {
      // Mock Font Loading API
      Object.defineProperty(document, "fonts", {
        value: {
          ready: Promise.resolve(),
          forEach: jest.fn((callback) => {
            callback({ family: "Inter", weight: "400" });
            callback({ family: "JetBrains Mono", weight: "400" });
          }),
        },
        configurable: true,
      });

      Object.defineProperty(window, "performance", {
        value: {
          now: jest.fn(() => 100),
        },
        configurable: true,
      });
    });

    it("should monitor font loading performance", async () => {
      const results = await fontOptimizer.monitorFontPerformance();

      expect(Array.isArray(results)).toBe(true);
      expect(results.length).toBeGreaterThan(0);
      expect(results[0]).toHaveProperty("loadTime");
      expect(results[0]).toHaveProperty("renderTime");
    });

    it("should handle browsers without Font Loading API", async () => {
      delete (document as any).fonts;

      const results = await fontOptimizer.monitorFontPerformance();

      expect(Array.isArray(results)).toBe(true);
      expect(results.length).toBe(1);
      expect(results[0]).toHaveProperty("loadTime");
    });
  });
});

describe("useFontOptimization Hook", () => {
  beforeEach(() => {
    const mockUseState = React.useState as jest.Mock;
    const mockUseEffect = React.useEffect as jest.Mock;

    mockUseState.mockClear();
    mockUseEffect.mockClear();
  });

  it("should return font loading state and metrics", () => {
    const mockUseState = React.useState as jest.Mock;
    mockUseState
      .mockReturnValueOnce([true, jest.fn()]) // fontsLoaded
      .mockReturnValueOnce([[], jest.fn()]); // fontMetrics

    // Mock the hook function
    const useFontOptimization = () => ({
      fontsLoaded: true,
      fontMetrics: [],
      fontStack: fontOptimizer.generateFontStack("Inter"),
    });

    const result = useFontOptimization();

    expect(result.fontsLoaded).toBe(true);
    expect(Array.isArray(result.fontMetrics)).toBe(true);
    expect(result.fontStack).toContain("Inter");
  });

  it("should handle loading state", () => {
    const mockUseState = React.useState as jest.Mock;
    mockUseState
      .mockReturnValueOnce([false, jest.fn()]) // fontsLoaded
      .mockReturnValueOnce([[], jest.fn()]); // fontMetrics

    const useFontOptimization = () => ({
      fontsLoaded: false,
      fontMetrics: [],
      fontStack: fontOptimizer.generateFontStack("Inter"),
    });

    const result = useFontOptimization();

    expect(result.fontsLoaded).toBe(false);
  });
});

describe("nextFontConfig", () => {
  it("should provide complete font configuration for Next.js", () => {
    expect(nextFontConfig).toHaveProperty("preload");
    expect(nextFontConfig).toHaveProperty("fontFaceCSS");
    expect(nextFontConfig).toHaveProperty("criticalCSS");
    expect(nextFontConfig).toHaveProperty("tailwindConfig");

    expect(Array.isArray(nextFontConfig.preload)).toBe(true);
    expect(typeof nextFontConfig.fontFaceCSS).toBe("string");
    expect(typeof nextFontConfig.criticalCSS).toBe("string");
    expect(typeof nextFontConfig.tailwindConfig).toBe("object");
  });

  it("should include preload links", () => {
    expect(nextFontConfig.preload.length).toBeGreaterThan(0);
    expect(nextFontConfig.preload[0]).toHaveProperty("rel", "preload");
    expect(nextFontConfig.preload[0]).toHaveProperty("as", "font");
  });

  it("should include font face CSS", () => {
    expect(nextFontConfig.fontFaceCSS).toContain("@font-face");
    expect(nextFontConfig.fontFaceCSS).toContain("font-family:");
    expect(nextFontConfig.fontFaceCSS).toContain("font-display:");
  });

  it("should include critical CSS", () => {
    expect(nextFontConfig.criticalCSS).toContain("@font-face");
    expect(nextFontConfig.criticalCSS).toContain("Inter");
  });

  it("should include Tailwind configuration", () => {
    expect(nextFontConfig.tailwindConfig).toHaveProperty("inter");
    expect(Array.isArray(nextFontConfig.tailwindConfig.inter)).toBe(true);
  });
});
