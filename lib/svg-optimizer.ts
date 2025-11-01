/**
 * SVG Optimization and Icon Sprite Generation
 * Handles SVG optimization, sprite sheet creation, and icon management
 */

export interface SVGOptimizationConfig {
  removeComments: boolean;
  removeMetadata: boolean;
  removeEmptyAttrs: boolean;
  removeUnusedNS: boolean;
  removeEditorsNSData: boolean;
  cleanupAttrs: boolean;
  minifyStyles: boolean;
  convertStyleToAttrs: boolean;
}

export interface IconDefinition {
  name: string;
  viewBox: string;
  content: string;
  category?: string;
}

export interface SpriteSheet {
  id: string;
  icons: IconDefinition[];
  svg: string;
  css: string;
}

class SVGOptimizer {
  private config: SVGOptimizationConfig = {
    removeComments: true,
    removeMetadata: true,
    removeEmptyAttrs: true,
    removeUnusedNS: true,
    removeEditorsNSData: true,
    cleanupAttrs: true,
    minifyStyles: true,
    convertStyleToAttrs: true,
  };

  private icons: Map<string, IconDefinition> = new Map();

  constructor() {
    this.initializeDefaultIcons();
  }

  /**
   * Initialize default icon set
   */
  private initializeDefaultIcons() {
    const defaultIcons: IconDefinition[] = [
      {
        name: "chevron-right",
        viewBox: "0 0 24 24",
        content:
          '<path d="m9 18 6-6-6-6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        category: "navigation",
      },
      {
        name: "chevron-down",
        viewBox: "0 0 24 24",
        content:
          '<path d="m6 9 6 6 6-6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        category: "navigation",
      },
      {
        name: "search",
        viewBox: "0 0 24 24",
        content:
          '<circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2" fill="none"/><path d="m21 21-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
        category: "interface",
      },
      {
        name: "user",
        viewBox: "0 0 24 24",
        content:
          '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" fill="none"/>',
        category: "user",
      },
      {
        name: "settings",
        viewBox: "0 0 24 24",
        content:
          '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" fill="none"/>',
        category: "interface",
      },
      {
        name: "bell",
        viewBox: "0 0 24 24",
        content:
          '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M13.73 21a2 2 0 0 1-3.46 0" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
        category: "interface",
      },
      {
        name: "menu",
        viewBox: "0 0 24 24",
        content:
          '<line x1="4" x2="20" y1="6" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="4" x2="20" y1="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="4" x2="20" y1="18" y2="18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
        category: "interface",
      },
      {
        name: "x",
        viewBox: "0 0 24 24",
        content:
          '<path d="m18 6-12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="m6 6 12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
        category: "interface",
      },
      {
        name: "external-link",
        viewBox: "0 0 24 24",
        content:
          '<path d="M15 3h6v6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 14 21 3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        category: "interface",
      },
      {
        name: "loading",
        viewBox: "0 0 24 24",
        content:
          '<path d="M21 12a9 9 0 1 1-6.219-8.56" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        category: "status",
      },
    ];

    defaultIcons.forEach((icon) => {
      this.icons.set(icon.name, icon);
    });
  }

  /**
   * Optimize SVG content
   */
  optimizeSVG(svgContent: string): string {
    let optimized = svgContent;

    if (this.config.removeComments) {
      optimized = optimized.replace(/<!--[\s\S]*?-->/g, "");
    }

    if (this.config.removeMetadata) {
      optimized = optimized.replace(/<metadata[\s\S]*?<\/metadata>/gi, "");
      optimized = optimized.replace(/<title[\s\S]*?<\/title>/gi, "");
      optimized = optimized.replace(/<desc[\s\S]*?<\/desc>/gi, "");
    }

    if (this.config.removeEmptyAttrs) {
      optimized = optimized.replace(/\s+[a-zA-Z-]+=""/g, "");
    }

    if (this.config.removeUnusedNS) {
      optimized = optimized.replace(/\s+xmlns:[a-zA-Z0-9-]+="[^"]*"/g, "");
    }

    if (this.config.removeEditorsNSData) {
      optimized = optimized.replace(/\s+data-[a-zA-Z0-9-]+="[^"]*"/g, "");
      optimized = optimized.replace(/\s+sketch:[a-zA-Z0-9-]+="[^"]*"/g, "");
    }

    if (this.config.cleanupAttrs) {
      optimized = optimized.replace(/\s+/g, " ").trim();
    }

    if (this.config.minifyStyles) {
      optimized = optimized.replace(/style="([^"]*)"/g, (match, styles) => {
        const minified = styles
          .replace(/\s*;\s*/g, ";")
          .replace(/\s*:\s*/g, ":")
          .trim();
        return `style="${minified}"`;
      });
    }

    return optimized;
  }

  /**
   * Add custom icon
   */
  addIcon(icon: IconDefinition) {
    this.icons.set(icon.name, icon);
  }

  /**
   * Generate sprite sheet
   */
  generateSpriteSheet(iconNames?: string[]): SpriteSheet {
    const iconsToInclude = iconNames
      ? (iconNames
          .map((name) => this.icons.get(name))
          .filter(Boolean) as IconDefinition[])
      : Array.from(this.icons.values());

    const spriteId = "icon-sprite";

    const svg = `<svg xmlns="http://www.w3.org/2000/svg" style="display: none;" id="${spriteId}">
${iconsToInclude
  .map(
    (icon) => `  <symbol id="icon-${icon.name}" viewBox="${icon.viewBox}">
    ${icon.content}
  </symbol>`
  )
  .join("\n")}
</svg>`;

    const css = this.generateIconCSS(iconsToInclude);

    return {
      id: spriteId,
      icons: iconsToInclude,
      svg: this.optimizeSVG(svg),
      css,
    };
  }

  /**
   * Generate CSS for icons
   */
  private generateIconCSS(icons: IconDefinition[]): string {
    return `
.icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  stroke-width: 0;
  stroke: currentColor;
  fill: currentColor;
  vertical-align: middle;
}

${icons
  .map(
    (icon) => `
.icon-${icon.name} {
  /* Icon: ${icon.name} */
}
`
  )
  .join("")}

/* Icon size variants */
.icon-xs { width: 0.75rem; height: 0.75rem; }
.icon-sm { width: 1rem; height: 1rem; }
.icon-md { width: 1.25rem; height: 1.25rem; }
.icon-lg { width: 1.5rem; height: 1.5rem; }
.icon-xl { width: 2rem; height: 2rem; }
.icon-2xl { width: 2.5rem; height: 2.5rem; }
`;
  }

  /**
   * Generate React icon component
   */
  generateIconComponent(iconName: string): string {
    const icon = this.icons.get(iconName);
    if (!icon) {
      throw new Error(`Icon "${iconName}" not found`);
    }

    return `
import React from 'react';

export interface ${this.toPascalCase(iconName)}IconProps {
  size?: number | string;
  className?: string;
  color?: string;
}

export function ${this.toPascalCase(iconName)}Icon({ 
  size = 24, 
  className = '', 
  color = 'currentColor' 
}: ${this.toPascalCase(iconName)}IconProps) {
  return {
    width: size,
    height: size,
    viewBox: "${icon.viewBox}",
    className: \`icon icon-${iconName} \${className}\`,
    style: { color },
    ariaHidden: true,
    content: \`${icon.content}\`,
  };
}
`;
  }

  /**
   * Convert string to PascalCase
   */
  private toPascalCase(str: string): string {
    return str
      .split("-")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join("");
  }

  /**
   * Get icon by name
   */
  getIcon(name: string): IconDefinition | undefined {
    return this.icons.get(name);
  }

  /**
   * Get all icons by category
   */
  getIconsByCategory(category: string): IconDefinition[] {
    return Array.from(this.icons.values()).filter(
      (icon) => icon.category === category
    );
  }

  /**
   * Get all available icons
   */
  getAllIcons(): IconDefinition[] {
    return Array.from(this.icons.values());
  }

  /**
   * Calculate SVG optimization savings
   */
  calculateOptimizationSavings(originalSVG: string): {
    originalSize: number;
    optimizedSize: number;
    savings: number;
    compressionRatio: number;
  } {
    const optimizedSVG = this.optimizeSVG(originalSVG);
    const originalSize = new Blob([originalSVG]).size;
    const optimizedSize = new Blob([optimizedSVG]).size;
    const savings = originalSize - optimizedSize;
    const compressionRatio = (savings / originalSize) * 100;

    return {
      originalSize,
      optimizedSize,
      savings,
      compressionRatio: Math.round(compressionRatio * 100) / 100,
    };
  }

  /**
   * Generate sprite sheet for production
   */
  generateProductionSprite(): {
    spriteSheet: SpriteSheet;
    inlineCSS: string;
    externalCSS: string;
  } {
    const spriteSheet = this.generateSpriteSheet();

    // Critical CSS (inlined)
    const inlineCSS = `
.icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  stroke: currentColor;
  fill: currentColor;
  vertical-align: middle;
}
`;

    // Non-critical CSS (external)
    const externalCSS = spriteSheet.css;

    return {
      spriteSheet,
      inlineCSS,
      externalCSS,
    };
  }
}

export const svgOptimizer = new SVGOptimizer();

/**
 * React component for optimized icons
 */
export interface IconProps {
  name: string;
  size?: number | string;
  className?: string;
  color?: string;
}

export function generateIconConfig({
  name,
  size = 24,
  className = "",
  color = "currentColor",
}: IconProps) {
  return {
    name,
    size,
    className: `icon icon-${name} ${className}`,
    color,
    href: `#icon-${name}`,
    ariaHidden: true,
  };
}

/**
 * Get sprite sheet utilities
 */
export function getSpriteSheetUtils(iconNames?: string[]) {
  const spriteSheet = svgOptimizer.generateSpriteSheet(iconNames);
  return spriteSheet;
}

/**
 * Generate sprite sheet configuration
 */
export function generateSpriteSheetConfig(iconNames?: string[]) {
  const spriteSheet = svgOptimizer.generateSpriteSheet(iconNames);

  return {
    spriteSheet,
    html: spriteSheet.svg,
    style: { display: "none" },
  };
}
