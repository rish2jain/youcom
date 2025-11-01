/**
 * Asset Optimization Pipeline
 * Handles optimization of images, fonts, and SVGs for web delivery
 */

export interface AssetOptimizationConfig {
  images: {
    quality: number;
    formats: string[];
    sizes: number[];
    placeholder: boolean;
  };
  fonts: {
    preload: string[];
    subset: boolean;
    display: string;
  };
  svg: {
    optimize: boolean;
    removeComments: boolean;
    removeMetadata: boolean;
  };
}

export interface OptimizedAsset {
  originalPath: string;
  optimizedPath: string;
  originalSize: number;
  optimizedSize: number;
  compressionRatio: number;
  format: string;
}

class AssetOptimizer {
  private config: AssetOptimizationConfig = {
    images: {
      quality: 85,
      formats: ["webp", "avif", "jpeg"],
      sizes: [640, 750, 828, 1080, 1200, 1920],
      placeholder: true,
    },
    fonts: {
      preload: ["Inter", "system-ui"],
      subset: true,
      display: "swap",
    },
    svg: {
      optimize: true,
      removeComments: true,
      removeMetadata: true,
    },
  };

  /**
   * Generate responsive image configuration
   */
  generateImageConfig(src: string, alt: string, priority = false) {
    return {
      src,
      alt,
      priority,
      quality: this.config.images.quality,
      placeholder: this.config.images.placeholder ? "blur" : "empty",
      sizes: "(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw",
      style: {
        width: "100%",
        height: "auto",
      },
    };
  }

  /**
   * Generate font optimization configuration
   */
  generateFontConfig() {
    return {
      preload: this.config.fonts.preload,
      display: this.config.fonts.display,
      subset: this.config.fonts.subset,
      // Font face CSS for optimized loading
      fontFace: `
        @font-face {
          font-family: 'Inter';
          font-style: normal;
          font-weight: 400 700;
          font-display: ${this.config.fonts.display};
          src: url('/fonts/inter-var.woff2') format('woff2');
          unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
        }
      `,
    };
  }

  /**
   * Optimize SVG content
   */
  optimizeSVG(svgContent: string): string {
    if (!this.config.svg.optimize) {
      return svgContent;
    }

    let optimized = svgContent;

    // Remove comments
    if (this.config.svg.removeComments) {
      optimized = optimized.replace(/<!--[\s\S]*?-->/g, "");
    }

    // Remove metadata
    if (this.config.svg.removeMetadata) {
      optimized = optimized.replace(/<metadata[\s\S]*?<\/metadata>/g, "");
      optimized = optimized.replace(/<title[\s\S]*?<\/title>/g, "");
      optimized = optimized.replace(/<desc[\s\S]*?<\/desc>/g, "");
    }

    // Remove unnecessary whitespace
    optimized = optimized.replace(/\s+/g, " ").trim();

    // Remove empty attributes
    optimized = optimized.replace(/\s*=\s*""/g, "");

    return optimized;
  }

  /**
   * Generate icon sprite sheet configuration
   */
  generateIconSpriteConfig(icons: string[]) {
    return {
      icons,
      spriteId: "icon-sprite",
      className: "icon",
      // SVG sprite template
      template: (icons: string[]) => `
        <svg xmlns="http://www.w3.org/2000/svg" style="display: none;">
          ${icons
            .map(
              (icon) =>
                `<symbol id="icon-${icon}" viewBox="0 0 24 24">${this.getIconContent(
                  icon
                )}</symbol>`
            )
            .join("")}
        </svg>
      `,
    };
  }

  /**
   * Get icon content (placeholder - would integrate with actual icon library)
   */
  private getIconContent(iconName: string): string {
    // This would integrate with your icon library (Lucide, Heroicons, etc.)
    const iconMap: Record<string, string> = {
      "chevron-right": '<path d="m9 18 6-6-6-6"/>',
      search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>',
      user: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
      settings:
        '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    };

    return iconMap[iconName] || '<circle cx="12" cy="12" r="10"/>';
  }

  /**
   * Calculate asset compression metrics
   */
  calculateCompressionMetrics(originalSize: number, optimizedSize: number) {
    const compressionRatio =
      ((originalSize - optimizedSize) / originalSize) * 100;
    const savings = originalSize - optimizedSize;

    return {
      originalSize,
      optimizedSize,
      compressionRatio: Math.round(compressionRatio * 100) / 100,
      savings,
      savingsFormatted: this.formatBytes(savings),
    };
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
   * Generate asset optimization report
   */
  generateOptimizationReport(assets: OptimizedAsset[]) {
    const totalOriginalSize = assets.reduce(
      (sum, asset) => sum + asset.originalSize,
      0
    );
    const totalOptimizedSize = assets.reduce(
      (sum, asset) => sum + asset.optimizedSize,
      0
    );
    const totalSavings = totalOriginalSize - totalOptimizedSize;
    const averageCompression = (totalSavings / totalOriginalSize) * 100;

    return {
      summary: {
        totalAssets: assets.length,
        totalOriginalSize: this.formatBytes(totalOriginalSize),
        totalOptimizedSize: this.formatBytes(totalOptimizedSize),
        totalSavings: this.formatBytes(totalSavings),
        averageCompression: Math.round(averageCompression * 100) / 100,
      },
      assets: assets.map((asset) => ({
        ...asset,
        originalSizeFormatted: this.formatBytes(asset.originalSize),
        optimizedSizeFormatted: this.formatBytes(asset.optimizedSize),
        savingsFormatted: this.formatBytes(
          asset.originalSize - asset.optimizedSize
        ),
      })),
      recommendations: this.generateAssetRecommendations(assets),
    };
  }

  /**
   * Generate asset optimization recommendations
   */
  private generateAssetRecommendations(assets: OptimizedAsset[]): string[] {
    const recommendations: string[] = [];

    // Check for large images
    const largeImages = assets.filter(
      (asset) => asset.format.includes("image") && asset.optimizedSize > 500000
    );
    if (largeImages.length > 0) {
      const imageText = largeImages.length === 1 ? "image" : "images";
      recommendations.push(
        `Consider further compression for ${largeImages.length} large ${imageText}`
      );
    }

    // Check for poor compression ratios
    const poorCompression = assets.filter(
      (asset) => asset.compressionRatio < 20
    );
    if (poorCompression.length > 0) {
      recommendations.push(
        `${poorCompression.length} assets have low compression ratios - consider different formats`
      );
    }

    // General recommendations
    if (assets.length > 20) {
      recommendations.push(
        "Consider implementing lazy loading for non-critical images"
      );
    }

    recommendations.push("Use WebP/AVIF formats for better compression");
    recommendations.push("Implement responsive images with appropriate sizes");
    recommendations.push("Preload critical images and fonts");

    return recommendations;
  }
}

export const assetOptimizer = new AssetOptimizer();

/**
 * React hook for optimized image loading
 */
export function useOptimizedImage(src: string, alt: string, priority = false) {
  return assetOptimizer.generateImageConfig(src, alt, priority);
}

/**
 * React component for optimized SVG icons
 */
export interface OptimizedIconProps {
  name: string;
  size?: number;
  className?: string;
}

export function generateOptimizedIconConfig({
  name,
  size = 24,
  className = "",
}: OptimizedIconProps) {
  return {
    name,
    size,
    className: `icon icon-${name} ${className}`,
    href: `#icon-${name}`,
    ariaHidden: true,
  };
}

/**
 * Font optimization utilities
 */
export const fontOptimization = {
  /**
   * Generate font preload links
   */
  generatePreloadLinks(fonts: string[]) {
    return fonts.map((font) => ({
      rel: "preload",
      href: `/fonts/${font.toLowerCase().replace(/\s+/g, "-")}.woff2`,
      as: "font",
      type: "font/woff2",
      crossOrigin: "anonymous",
    }));
  },

  /**
   * Generate font display CSS
   */
  generateFontCSS(fontFamily: string, weights: number[] = [400, 700]) {
    return weights
      .map(
        (weight) => `
      @font-face {
        font-family: '${fontFamily}';
        font-style: normal;
        font-weight: ${weight};
        font-display: swap;
        src: url('/fonts/${fontFamily.toLowerCase()}-${weight}.woff2') format('woff2');
      }
    `
      )
      .join("\n");
  },
};

/**
 * Asset optimization middleware for Next.js
 */
export function createAssetOptimizationMiddleware() {
  return {
    // Image optimization headers
    images: {
      "Cache-Control": "public, max-age=31536000, immutable",
      "X-Content-Type-Options": "nosniff",
    },
    // Font optimization headers
    fonts: {
      "Cache-Control": "public, max-age=31536000, immutable",
      "Access-Control-Allow-Origin": "*",
      "X-Content-Type-Options": "nosniff",
    },
    // SVG optimization headers
    svg: {
      "Cache-Control": "public, max-age=2592000", // 30 days
      "Content-Type": "image/svg+xml",
      "X-Content-Type-Options": "nosniff",
    },
  };
}
