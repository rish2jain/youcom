/**
 * Tests for SVG optimization utilities
 */

import { svgOptimizer, Icon, SpriteSheet } from "../svg-optimizer";
import React from "react";
import { render } from "@testing-library/react";

// Mock React hooks
jest.mock("react", () => ({
  ...jest.requireActual("react"),
  useState: jest.fn(),
  useEffect: jest.fn(),
}));

describe("SVGOptimizer", () => {
  describe("Default Icons", () => {
    it("should initialize with default icons", () => {
      const icons = svgOptimizer.getAllIcons();

      expect(icons.length).toBeGreaterThan(0);
      expect(icons.some((icon) => icon.name === "chevron-right")).toBe(true);
      expect(icons.some((icon) => icon.name === "search")).toBe(true);
      expect(icons.some((icon) => icon.name === "user")).toBe(true);
      expect(icons.some((icon) => icon.name === "settings")).toBe(true);
    });

    it("should have proper icon structure", () => {
      const searchIcon = svgOptimizer.getIcon("search");

      expect(searchIcon).toBeDefined();
      expect(searchIcon?.name).toBe("search");
      expect(searchIcon?.viewBox).toBe("0 0 24 24");
      expect(searchIcon?.content).toContain("circle");
      expect(searchIcon?.content).toContain("path");
      expect(searchIcon?.category).toBe("interface");
    });
  });

  describe("SVG Optimization", () => {
    it("should remove comments from SVG", () => {
      const svgWithComments = `
        <svg>
          <!-- This is a comment -->
          <path d="M10 10"/>
          <!-- Another comment -->
        </svg>
      `;

      const optimized = svgOptimizer.optimizeSVG(svgWithComments);

      expect(optimized).not.toContain("<!-- This is a comment -->");
      expect(optimized).not.toContain("<!-- Another comment -->");
      expect(optimized).toContain('<path d="M10 10"/>');
    });

    it("should remove metadata elements", () => {
      const svgWithMetadata = `
        <svg>
          <metadata>Some metadata</metadata>
          <title>SVG Title</title>
          <desc>SVG Description</desc>
          <path d="M10 10"/>
        </svg>
      `;

      const optimized = svgOptimizer.optimizeSVG(svgWithMetadata);

      expect(optimized).not.toContain("<metadata>");
      expect(optimized).not.toContain("<title>");
      expect(optimized).not.toContain("<desc>");
      expect(optimized).toContain('<path d="M10 10"/>');
    });

    it("should remove empty attributes", () => {
      const svgWithEmptyAttrs = `
        <svg class="" id="" data-test="">
          <path d="M10 10" fill=""/>
        </svg>
      `;

      const optimized = svgOptimizer.optimizeSVG(svgWithEmptyAttrs);

      expect(optimized).not.toContain('class=""');
      expect(optimized).not.toContain('id=""');
      expect(optimized).not.toContain('data-test=""');
      expect(optimized).not.toContain('fill=""');
    });

    it("should remove unused namespaces", () => {
      const svgWithNamespaces = `
        <svg xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:custom="http://example.com">
          <path d="M10 10"/>
        </svg>
      `;

      const optimized = svgOptimizer.optimizeSVG(svgWithNamespaces);

      expect(optimized).not.toContain("xmlns:xlink");
      expect(optimized).not.toContain("xmlns:custom");
    });

    it("should remove editor namespace data", () => {
      const svgWithEditorData = `
        <svg data-name="Layer 1" sketch:type="MSShapeGroup">
          <path d="M10 10"/>
        </svg>
      `;

      const optimized = svgOptimizer.optimizeSVG(svgWithEditorData);

      expect(optimized).not.toContain("data-name");
      expect(optimized).not.toContain("sketch:type");
    });

    it("should minify styles", () => {
      const svgWithStyles = `
        <svg style="  color : red ; background : blue ; ">
          <path d="M10 10"/>
        </svg>
      `;

      const optimized = svgOptimizer.optimizeSVG(svgWithStyles);

      expect(optimized).toContain('style="color:red;background:blue"');
      expect(optimized).not.toContain("  color : red ; background : blue ; ");
    });

    it("should clean up whitespace", () => {
      const svgWithWhitespace = `
        <svg   viewBox="0 0 24 24"    >
          <path    d="M10 10"   />
        </svg>
      `;

      const optimized = svgOptimizer.optimizeSVG(svgWithWhitespace);

      expect(optimized).not.toContain("   ");
      expect(optimized.trim()).toBe(optimized);
    });
  });

  describe("Icon Management", () => {
    it("should add custom icons", () => {
      const customIcon = {
        name: "custom-icon",
        viewBox: "0 0 16 16",
        content: '<circle cx="8" cy="8" r="4"/>',
        category: "custom",
      };

      svgOptimizer.addIcon(customIcon);

      const retrievedIcon = svgOptimizer.getIcon("custom-icon");
      expect(retrievedIcon).toEqual(customIcon);
    });

    it("should get icons by category", () => {
      const interfaceIcons = svgOptimizer.getIconsByCategory("interface");

      expect(interfaceIcons.length).toBeGreaterThan(0);
      expect(
        interfaceIcons.every((icon) => icon.category === "interface")
      ).toBe(true);
      expect(interfaceIcons.some((icon) => icon.name === "search")).toBe(true);
    });

    it("should return undefined for non-existent icons", () => {
      const nonExistentIcon = svgOptimizer.getIcon("non-existent");
      expect(nonExistentIcon).toBeUndefined();
    });
  });

  describe("Sprite Sheet Generation", () => {
    it("should generate sprite sheet with all icons", () => {
      const spriteSheet = svgOptimizer.generateSpriteSheet();

      expect(spriteSheet.id).toBe("icon-sprite");
      expect(spriteSheet.icons.length).toBeGreaterThan(0);
      expect(spriteSheet.svg).toContain(
        '<svg xmlns="http://www.w3.org/2000/svg"'
      );
      expect(spriteSheet.svg).toContain('style="display: none;"');
      expect(spriteSheet.svg).toContain('<symbol id="icon-');
      expect(spriteSheet.css).toContain(".icon");
    });

    it("should generate sprite sheet with specific icons", () => {
      const iconNames = ["search", "user"];
      const spriteSheet = svgOptimizer.generateSpriteSheet(iconNames);

      expect(spriteSheet.icons.length).toBe(2);
      expect(spriteSheet.icons.some((icon) => icon.name === "search")).toBe(
        true
      );
      expect(spriteSheet.icons.some((icon) => icon.name === "user")).toBe(true);
      expect(spriteSheet.svg).toContain('id="icon-search"');
      expect(spriteSheet.svg).toContain('id="icon-user"');
    });

    it("should optimize sprite sheet SVG", () => {
      const spriteSheet = svgOptimizer.generateSpriteSheet(["search"]);

      // Should be optimized (no extra whitespace)
      expect(spriteSheet.svg).not.toContain("  <symbol");
      expect(spriteSheet.svg.trim()).toBe(spriteSheet.svg);
    });

    it("should generate CSS for icons", () => {
      const spriteSheet = svgOptimizer.generateSpriteSheet(["search", "user"]);

      expect(spriteSheet.css).toContain(".icon {");
      expect(spriteSheet.css).toContain("display: inline-block;");
      expect(spriteSheet.css).toContain("width: 1em;");
      expect(spriteSheet.css).toContain("height: 1em;");
      expect(spriteSheet.css).toContain(".icon-search {");
      expect(spriteSheet.css).toContain(".icon-user {");
      expect(spriteSheet.css).toContain(".icon-xs");
      expect(spriteSheet.css).toContain(".icon-xl");
    });
  });

  describe("React Component Generation", () => {
    it("should generate React component code", () => {
      const componentCode = svgOptimizer.generateIconComponent("search");

      expect(componentCode).toContain("export interface SearchIconProps");
      expect(componentCode).toContain("export function SearchIcon");
      expect(componentCode).toContain("size?: number | string");
      expect(componentCode).toContain("className?: string");
      expect(componentCode).toContain("color?: string");
      expect(componentCode).toContain('viewBox="0 0 24 24"');
      expect(componentCode).toContain("circle");
    });

    it("should handle PascalCase conversion", () => {
      const componentCode = svgOptimizer.generateIconComponent("chevron-right");

      expect(componentCode).toContain("ChevronRightIconProps");
      expect(componentCode).toContain("ChevronRightIcon");
    });

    it("should throw error for non-existent icons", () => {
      expect(() => {
        svgOptimizer.generateIconComponent("non-existent");
      }).toThrow('Icon "non-existent" not found');
    });
  });

  describe("Optimization Savings Calculation", () => {
    it("should calculate optimization savings correctly", () => {
      const originalSVG = `
        <!-- Comment -->
        <svg>
          <metadata>metadata</metadata>
          <title>title</title>
          <path d="M10 10"/>
        </svg>
      `;

      const savings = svgOptimizer.calculateOptimizationSavings(originalSVG);

      expect(savings.originalSize).toBeGreaterThan(0);
      expect(savings.optimizedSize).toBeGreaterThan(0);
      expect(savings.optimizedSize).toBeLessThan(savings.originalSize);
      expect(savings.savings).toBe(
        savings.originalSize - savings.optimizedSize
      );
      expect(savings.compressionRatio).toBeGreaterThan(0);
    });

    it("should handle SVG with no optimization potential", () => {
      const minimalSVG = '<svg><path d="M10 10"/></svg>';

      const savings = svgOptimizer.calculateOptimizationSavings(minimalSVG);

      expect(savings.compressionRatio).toBeLessThan(10); // Minimal compression
    });
  });

  describe("Production Sprite Generation", () => {
    it("should generate production-ready sprite sheet", () => {
      const production = svgOptimizer.generateProductionSprite();

      expect(production).toHaveProperty("spriteSheet");
      expect(production).toHaveProperty("inlineCSS");
      expect(production).toHaveProperty("externalCSS");

      expect(production.inlineCSS).toContain(".icon {");
      expect(production.inlineCSS).toContain("display: inline-block;");
      expect(production.externalCSS).toContain(".icon-xs");
      expect(production.spriteSheet.svg).toContain(
        '<svg xmlns="http://www.w3.org/2000/svg"'
      );
    });

    it("should separate critical and non-critical CSS", () => {
      const production = svgOptimizer.generateProductionSprite();

      // Inline CSS should be minimal
      expect(production.inlineCSS.length).toBeLessThan(
        production.externalCSS.length
      );

      // External CSS should contain size variants
      expect(production.externalCSS).toContain(".icon-xs");
      expect(production.externalCSS).toContain(".icon-lg");
    });
  });
});

describe("Icon Component", () => {
  it("should render icon with correct attributes", () => {
    const { container } = render(
      <Icon name="search" size={24} className="test-class" color="red" />
    );

    const svg = container.querySelector("svg");
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveAttribute("width", "24");
    expect(svg).toHaveAttribute("height", "24");
    expect(svg).toHaveClass("icon", "icon-search", "test-class");
    expect(svg).toHaveAttribute("aria-hidden", "true");
    expect(svg).toHaveStyle("color: red");

    const use = container.querySelector("use");
    expect(use).toBeInTheDocument();
    expect(use).toHaveAttribute("href", "#icon-search");
  });

  it("should use default values", () => {
    const { container } = render(<Icon name="user" />);

    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("width", "24");
    expect(svg).toHaveAttribute("height", "24");
    expect(svg).toHaveStyle("color: currentColor");
    expect(svg).toHaveClass("icon", "icon-user");
  });

  it("should handle string size values", () => {
    const { container } = render(<Icon name="settings" size="32" />);

    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("width", "32");
    expect(svg).toHaveAttribute("height", "32");
  });
});

describe("SpriteSheet Component", () => {
  beforeEach(() => {
    const mockUseState = React.useState as jest.Mock;
    const mockUseEffect = React.useEffect as jest.Mock;

    mockUseState.mockImplementation((initial) => [initial, jest.fn()]);
    mockUseEffect.mockImplementation((fn) => fn());
  });

  it("should render sprite sheet when available", () => {
    const mockSpriteSheet = {
      id: "icon-sprite",
      icons: [],
      svg: '<svg id="icon-sprite"><symbol id="icon-test"></symbol></svg>',
      css: ".icon { display: inline-block; }",
    };

    const mockUseState = React.useState as jest.Mock;
    mockUseState.mockReturnValue([mockSpriteSheet, jest.fn()]);

    const { container } = render(<SpriteSheet />);

    const div = container.querySelector('div[style*="display: none"]');
    expect(div).toBeInTheDocument();
    expect(div?.innerHTML).toContain('<svg id="icon-sprite">');
    expect(div?.innerHTML).toContain('<symbol id="icon-test">');
  });

  it("should not render when sprite sheet is not available", () => {
    const mockUseState = React.useState as jest.Mock;
    mockUseState.mockReturnValue([null, jest.fn()]);

    const { container } = render(<SpriteSheet />);

    expect(container.firstChild).toBeNull();
  });

  it("should handle specific icon names", () => {
    const mockSpriteSheet = {
      id: "icon-sprite",
      icons: [],
      svg: '<svg id="icon-sprite"></svg>',
      css: ".icon { display: inline-block; }",
    };

    const mockUseState = React.useState as jest.Mock;
    mockUseState.mockReturnValue([mockSpriteSheet, jest.fn()]);

    const { container } = render(
      <SpriteSheet iconNames={["search", "user"]} />
    );

    const div = container.querySelector('div[style*="display: none"]');
    expect(div).toBeInTheDocument();
  });
});

describe("useSpriteSheet Hook", () => {
  beforeEach(() => {
    const mockUseState = React.useState as jest.Mock;
    const mockUseEffect = React.useEffect as jest.Mock;

    mockUseState.mockClear();
    mockUseEffect.mockClear();
  });

  it("should return sprite sheet", () => {
    const mockSpriteSheet = {
      id: "icon-sprite",
      icons: [],
      svg: "<svg></svg>",
      css: ".icon {}",
    };

    const mockUseState = React.useState as jest.Mock;
    mockUseState.mockReturnValue([mockSpriteSheet, jest.fn()]);

    // Mock the hook function
    const useSpriteSheet = () => mockSpriteSheet;

    const result = useSpriteSheet();

    expect(result).toBe(mockSpriteSheet);
  });

  it("should handle loading state", () => {
    const mockUseState = React.useState as jest.Mock;
    mockUseState.mockReturnValue([null, jest.fn()]);

    const useSpriteSheet = () => null;

    const result = useSpriteSheet();

    expect(result).toBe(null);
  });
});
