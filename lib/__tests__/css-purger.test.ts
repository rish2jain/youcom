/**
 * Tests for CSS purging utilities
 */

import { cssPurger, CSSPurgePlugin } from "../css-purger";

describe("CSSPurger", () => {
  describe("CSS Selector Extraction", () => {
    it("should extract selectors from CSS", () => {
      const css = `
        .test-class { color: red; }
        .another-class { background: blue; }
        #test-id { margin: 10px; }
        div { padding: 5px; }
      `;

      const extractSelectors = (cssPurger as any).extractSelectors;
      const selectors = extractSelectors(css);

      expect(selectors).toContain(".test-class");
      expect(selectors).toContain(".another-class");
      expect(selectors).toContain("#test-id");
      expect(selectors).toContain("div");
    });

    it("should handle multiple selectors separated by commas", () => {
      const css = `
        .class1, .class2, .class3 { color: red; }
        h1, h2, h3 { font-weight: bold; }
      `;

      const extractSelectors = (cssPurger as any).extractSelectors;
      const selectors = extractSelectors(css);

      expect(selectors).toContain(".class1");
      expect(selectors).toContain(".class2");
      expect(selectors).toContain(".class3");
      expect(selectors).toContain("h1");
      expect(selectors).toContain("h2");
      expect(selectors).toContain("h3");
    });

    it("should remove duplicates from extracted selectors", () => {
      const css = `
        .test { color: red; }
        .test { background: blue; }
        .other { margin: 10px; }
      `;

      const extractSelectors = (cssPurger as any).extractSelectors;
      const selectors = extractSelectors(css);

      expect(selectors.filter((s) => s === ".test")).toHaveLength(1);
      expect(selectors).toContain(".other");
    });

    it("should handle CSS with comments", () => {
      const css = `
        /* Comment */
        .test { color: red; }
        /* Another comment */
        .other { background: blue; }
      `;

      const extractSelectors = (cssPurger as any).extractSelectors;
      const selectors = extractSelectors(css);

      expect(selectors).toContain(".test");
      expect(selectors).toContain(".other");
      expect(selectors).not.toContain("/* Comment */");
    });
  });

  describe("Selector Filtering", () => {
    it("should keep safelisted selectors", () => {
      const usedClasses = new Set(["used-class"]);
      const shouldKeepSelector = (cssPurger as any).shouldKeepSelector;

      // Test safelisted selectors
      expect(shouldKeepSelector("html", usedClasses)).toBe(true);
      expect(shouldKeepSelector("body", usedClasses)).toBe(true);
      expect(shouldKeepSelector("*", usedClasses)).toBe(true);
      expect(shouldKeepSelector(".animate-pulse", usedClasses)).toBe(true);
      expect(shouldKeepSelector(".hover\\:bg-gray-100", usedClasses)).toBe(
        true
      );
    });

    it("should remove blocklisted selectors", () => {
      const usedClasses = new Set(["used-class"]);
      const shouldKeepSelector = (cssPurger as any).shouldKeepSelector;

      expect(shouldKeepSelector(".unused-class", usedClasses)).toBe(false);
      expect(shouldKeepSelector(".debug-something", usedClasses)).toBe(false);
    });

    it("should keep selectors with used classes", () => {
      const usedClasses = new Set(["container", "flex", "text-lg"]);
      const shouldKeepSelector = (cssPurger as any).shouldKeepSelector;

      expect(shouldKeepSelector(".container", usedClasses)).toBe(true);
      expect(shouldKeepSelector(".flex", usedClasses)).toBe(true);
      expect(shouldKeepSelector(".text-lg", usedClasses)).toBe(true);
      expect(shouldKeepSelector(".unused-class", usedClasses)).toBe(false);
    });

    it("should handle complex selectors", () => {
      const usedClasses = new Set(["container", "flex"]);
      const shouldKeepSelector = (cssPurger as any).shouldKeepSelector;

      expect(shouldKeepSelector(".container .flex", usedClasses)).toBe(true);
      expect(shouldKeepSelector(".container:hover", usedClasses)).toBe(true);
      expect(shouldKeepSelector(".unused .also-unused", usedClasses)).toBe(
        false
      );
    });

    it("should keep non-class selectors", () => {
      const usedClasses = new Set(["used-class"]);
      const shouldKeepSelector = (cssPurger as any).shouldKeepSelector;

      expect(shouldKeepSelector("div", usedClasses)).toBe(true);
      expect(shouldKeepSelector("h1", usedClasses)).toBe(true);
      expect(shouldKeepSelector('input[type="text"]', usedClasses)).toBe(true);
      expect(shouldKeepSelector("::before", usedClasses)).toBe(true);
    });
  });

  describe("CSS Purging", () => {
    it("should purge unused CSS classes", async () => {
      const css = `
        .used-class { color: red; }
        .unused-class { color: blue; }
        .another-used { background: green; }
        .another-unused { margin: 10px; }
      `;

      const usedClasses = new Set(["used-class", "another-used"]);
      const result = await cssPurger.purgeCSS(css, usedClasses);

      expect(result.keptSelectors).toContain(".used-class");
      expect(result.keptSelectors).toContain(".another-used");
      expect(result.removedSelectors).toContain(".unused-class");
      expect(result.removedSelectors).toContain(".another-unused");
    });

    it("should calculate compression ratio correctly", async () => {
      const css = `
        .used { color: red; }
        .unused1 { color: blue; }
        .unused2 { color: green; }
        .unused3 { color: yellow; }
      `;

      const usedClasses = new Set(["used"]);
      const result = await cssPurger.purgeCSS(css, usedClasses);

      expect(result.compressionRatio).toBeGreaterThan(0);
      expect(result.purgedSize).toBeLessThan(result.originalSize);
    });

    it("should handle empty used classes set", async () => {
      const css = `
        .class1 { color: red; }
        .class2 { color: blue; }
        html { margin: 0; }
        body { padding: 0; }
      `;

      const usedClasses = new Set<string>();
      const result = await cssPurger.purgeCSS(css, usedClasses);

      // Should keep safelisted selectors like html, body
      expect(result.keptSelectors).toContain("html");
      expect(result.keptSelectors).toContain("body");
      expect(result.removedSelectors).toContain(".class1");
      expect(result.removedSelectors).toContain(".class2");
    });
  });

  describe("Used Classes Scanning", () => {
    it("should return common classes when scanning", async () => {
      const usedClasses = await cssPurger.scanForUsedClasses();

      expect(usedClasses.has("container")).toBe(true);
      expect(usedClasses.has("flex")).toBe(true);
      expect(usedClasses.has("grid")).toBe(true);
      expect(usedClasses.has("text-base")).toBe(true);
      expect(usedClasses.has("bg-white")).toBe(true);
      expect(usedClasses.has("animate-pulse")).toBe(true);
    });

    it("should include component classes", async () => {
      const usedClasses = await cssPurger.scanForUsedClasses();

      expect(usedClasses.has("btn")).toBe(true);
      expect(usedClasses.has("card")).toBe(true);
      expect(usedClasses.has("form-input")).toBe(true);
    });

    it("should include interactive state classes", async () => {
      const usedClasses = await cssPurger.scanForUsedClasses();

      expect(usedClasses.has("hover:bg-gray-100")).toBe(true);
      expect(usedClasses.has("focus:outline-none")).toBe(true);
      expect(usedClasses.has("focus:ring-2")).toBe(true);
    });
  });

  describe("Purge Report Generation", () => {
    it("should generate comprehensive purge report", () => {
      const result = {
        originalSize: 10000,
        purgedSize: 6000,
        removedSelectors: [".unused1", ".unused2", ".unused3"],
        keptSelectors: [".used1", ".used2"],
        compressionRatio: 40,
      };

      const report = cssPurger.generatePurgeReport(result);

      expect(report).toContain("# CSS Purge Report");
      expect(report).toContain("## Summary");
      expect(report).toContain("Original Size: 9.77 KB");
      expect(report).toContain("Purged Size: 5.86 KB");
      expect(report).toContain("Compression Ratio: 40.00%");
      expect(report).toContain("Kept Selectors: 2");
      expect(report).toContain("Removed Selectors: 3");
    });

    it("should include sample of removed selectors", () => {
      const result = {
        originalSize: 10000,
        purgedSize: 6000,
        removedSelectors: Array.from({ length: 15 }, (_, i) => `.unused${i}`),
        keptSelectors: [".used1", ".used2"],
        compressionRatio: 40,
      };

      const report = cssPurger.generatePurgeReport(result);

      expect(report).toContain("## Removed Selectors (Sample)");
      expect(report).toContain("- .unused0");
      expect(report).toContain("- .unused9");
      expect(report).toContain("... and 5 more");
    });

    it("should provide appropriate recommendations based on compression ratio", () => {
      const excellentResult = {
        originalSize: 10000,
        purgedSize: 4000,
        removedSelectors: [".unused"],
        keptSelectors: [".used"],
        compressionRatio: 60,
      };

      const goodResult = {
        originalSize: 10000,
        purgedSize: 7000,
        removedSelectors: [".unused"],
        keptSelectors: [".used"],
        compressionRatio: 30,
      };

      const poorResult = {
        originalSize: 10000,
        purgedSize: 9000,
        removedSelectors: [".unused"],
        keptSelectors: [".used"],
        compressionRatio: 10,
      };

      const excellentReport = cssPurger.generatePurgeReport(excellentResult);
      const goodReport = cssPurger.generatePurgeReport(goodResult);
      const poorReport = cssPurger.generatePurgeReport(poorResult);

      expect(excellentReport).toContain("✅ Excellent purge ratio");
      expect(goodReport).toContain("⚠️ Good purge ratio");
      expect(poorReport).toContain("❌ Low purge ratio");
    });

    it("should include general recommendations", () => {
      const result = {
        originalSize: 10000,
        purgedSize: 6000,
        removedSelectors: [".unused"],
        keptSelectors: [".used"],
        compressionRatio: 40,
      };

      const report = cssPurger.generatePurgeReport(result);

      expect(report).toContain("Use CSS-in-JS for component-specific styles");
      expect(report).toContain("Implement dynamic class generation carefully");
      expect(report).toContain("Regular CSS audits to identify unused styles");
      expect(report).toContain("Consider CSS modules for better tree shaking");
    });
  });

  describe("Configuration Updates", () => {
    it("should update configuration correctly", () => {
      const originalConfig = (cssPurger as any).config;

      cssPurger.updateConfig({
        removeComments: false,
        safelist: ["new-safe-class"],
      });

      const updatedConfig = (cssPurger as any).config;

      expect(updatedConfig.removeComments).toBe(false);
      expect(updatedConfig.safelist).toContain("new-safe-class");
      expect(updatedConfig.css).toEqual(originalConfig.css); // Should keep other properties
    });
  });

  describe("Byte Formatting", () => {
    it("should format bytes correctly", () => {
      const formatBytes = (cssPurger as any).formatBytes;

      expect(formatBytes(0)).toBe("0 Bytes");
      expect(formatBytes(1024)).toBe("1.00 KB");
      expect(formatBytes(1048576)).toBe("1.00 MB");
      expect(formatBytes(500)).toBe("500.00 Bytes");
      expect(formatBytes(1536)).toBe("1.50 KB");
    });
  });
});

describe("CSSPurgePlugin", () => {
  it("should create plugin instance", () => {
    const plugin = new CSSPurgePlugin();
    expect(plugin).toBeInstanceOf(CSSPurgePlugin);
    expect(typeof plugin.apply).toBe("function");
  });

  it("should register webpack hook", () => {
    const plugin = new CSSPurgePlugin();
    const mockCompiler = {
      hooks: {
        emit: {
          tapAsync: jest.fn(),
        },
      },
    };

    plugin.apply(mockCompiler);

    expect(mockCompiler.hooks.emit.tapAsync).toHaveBeenCalledWith(
      "CSSPurgePlugin",
      expect.any(Function)
    );
  });

  it("should handle webpack compilation", async () => {
    const plugin = new CSSPurgePlugin();
    const mockAsset = {
      source: () => ".test { color: red; } .unused { color: blue; }",
    };
    const mockCompilation = {
      assets: {
        "main.css": mockAsset,
      },
    };
    const mockCallback = jest.fn();

    const mockCompiler = {
      hooks: {
        emit: {
          tapAsync: jest.fn((name, handler) => {
            // Simulate webpack calling the handler
            handler(mockCompilation, mockCallback);
          }),
        },
      },
    };

    const consoleSpy = jest.spyOn(console, "log").mockImplementation();

    plugin.apply(mockCompiler);

    expect(mockCallback).toHaveBeenCalled();
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining("📦 CSS Purged: main.css")
    );

    consoleSpy.mockRestore();
  });

  it("should handle errors gracefully", async () => {
    const plugin = new CSSPurgePlugin();
    const mockCompilation = {
      assets: {
        "main.css": {
          source: () => {
            throw new Error("Test error");
          },
        },
      },
    };
    const mockCallback = jest.fn();

    const mockCompiler = {
      hooks: {
        emit: {
          tapAsync: jest.fn((name, handler) => {
            handler(mockCompilation, mockCallback);
          }),
        },
      },
    };

    const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

    plugin.apply(mockCompiler);

    expect(mockCallback).toHaveBeenCalled();
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      "CSS purging failed:",
      expect.any(Error)
    );

    consoleErrorSpy.mockRestore();
  });
});
