/**
 * Cognitive Load Management System
 *
 * Implements cognitive load calculation and optimization algorithms
 * based on user role and content complexity as per Requirements 2.6, 2.3
 */

export interface CognitiveElement {
  id: string;
  type: "text" | "metric" | "chart" | "action" | "image" | "list" | "table";
  complexity: "low" | "medium" | "high";
  priority: "critical" | "important" | "supplementary";
  weight?: number; // Custom weight override
}

export interface UserRole {
  type: "executive" | "analyst" | "technical";
  maxCognitiveLoad: number;
  preferredComplexity: "low" | "medium" | "high";
  attentionSpan: number; // in seconds
}

export interface ContentSection {
  id: string;
  title: string;
  elements: CognitiveElement[];
  level: 1 | 2 | 3; // Progressive disclosure level
}

export class CognitiveLoadManager {
  private static readonly ELEMENT_WEIGHTS = {
    // Base weights by element type
    text: 1,
    metric: 2,
    chart: 4,
    action: 3,
    image: 2,
    list: 2,
    table: 5,
  };

  private static readonly COMPLEXITY_MULTIPLIERS = {
    low: 1,
    medium: 1.5,
    high: 2.5,
  };

  private static readonly PRIORITY_WEIGHTS = {
    critical: 1.5,
    important: 1.2,
    supplementary: 0.8,
  };

  private static readonly USER_ROLE_CONFIGS: Record<string, UserRole> = {
    executive: {
      type: "executive",
      maxCognitiveLoad: 15,
      preferredComplexity: "low",
      attentionSpan: 30,
    },
    analyst: {
      type: "analyst",
      maxCognitiveLoad: 25,
      preferredComplexity: "medium",
      attentionSpan: 120,
    },
    technical: {
      type: "technical",
      maxCognitiveLoad: 40,
      preferredComplexity: "high",
      attentionSpan: 300,
    },
  };

  /**
   * Calculate cognitive load for a single element
   */
  static calculateElementLoad(element: CognitiveElement): number {
    const baseWeight =
      element.weight || this.ELEMENT_WEIGHTS[element.type] || 1;
    const complexityMultiplier =
      this.COMPLEXITY_MULTIPLIERS[element.complexity];
    const priorityWeight = this.PRIORITY_WEIGHTS[element.priority];

    return baseWeight * complexityMultiplier * priorityWeight;
  }

  /**
   * Calculate total cognitive load for a content section
   */
  static calculateSectionLoad(section: ContentSection): number {
    return section.elements.reduce((total, element) => {
      return total + this.calculateElementLoad(element);
    }, 0);
  }

  /**
   * Calculate total cognitive load for multiple sections
   */
  static calculateTotalLoad(sections: ContentSection[]): number {
    return sections.reduce((total, section) => {
      return total + this.calculateSectionLoad(section);
    }, 0);
  }

  /**
   * Get user role configuration
   */
  static getUserRoleConfig(roleType: string): UserRole {
    return this.USER_ROLE_CONFIGS[roleType] || this.USER_ROLE_CONFIGS.analyst;
  }

  /**
   * Optimize content sections based on user role and cognitive load limits
   */
  static optimizeForRole(
    sections: ContentSection[],
    userRole: string
  ): {
    optimizedSections: ContentSection[];
    totalLoad: number;
    recommendations: string[];
  } {
    const roleConfig = this.getUserRoleConfig(userRole);
    const recommendations: string[] = [];
    let optimizedSections = [...sections];

    // Calculate initial load
    let totalLoad = this.calculateTotalLoad(optimizedSections);

    // If load exceeds limit, apply optimization strategies
    if (totalLoad > roleConfig.maxCognitiveLoad) {
      recommendations.push(
        `Initial cognitive load (${totalLoad}) exceeds recommended limit (${roleConfig.maxCognitiveLoad})`
      );

      // Strategy 1: Remove supplementary elements
      optimizedSections = this.removeSupplementaryElements(optimizedSections);
      totalLoad = this.calculateTotalLoad(optimizedSections);

      if (totalLoad > roleConfig.maxCognitiveLoad) {
        recommendations.push(
          "Removed supplementary elements to reduce cognitive load"
        );

        // Strategy 2: Simplify complex elements
        optimizedSections = this.simplifyComplexElements(optimizedSections);
        totalLoad = this.calculateTotalLoad(optimizedSections);

        if (totalLoad > roleConfig.maxCognitiveLoad) {
          recommendations.push("Simplified complex elements");

          // Strategy 3: Keep only critical elements
          optimizedSections = this.keepOnlyCriticalElements(optimizedSections);
          totalLoad = this.calculateTotalLoad(optimizedSections);
          recommendations.push(
            "Showing only critical elements due to high cognitive load"
          );
        }
      }
    }

    // Add role-specific recommendations
    if (userRole === "executive") {
      recommendations.push(
        "Executive view: Showing key insights and actions only"
      );
    } else if (userRole === "analyst") {
      recommendations.push(
        "Analyst view: Showing detailed analysis with supporting evidence"
      );
    } else if (userRole === "technical") {
      recommendations.push(
        "Technical view: Showing all available data and metrics"
      );
    }

    return {
      optimizedSections,
      totalLoad,
      recommendations,
    };
  }

  /**
   * Generate Level 1 content summary automatically
   */
  static generateLevel1Summary(sections: ContentSection[]): ContentSection {
    const criticalElements: CognitiveElement[] = [];

    // Extract critical elements from all sections
    sections.forEach((section) => {
      const critical = section.elements.filter(
        (el) => el.priority === "critical"
      );
      criticalElements.push(...critical.slice(0, 2)); // Max 2 critical per section
    });

    // Ensure we don't exceed cognitive load for Level 1
    const maxElements = 5; // Maximum elements for Level 1
    const summarizedElements = criticalElements.slice(0, maxElements);

    return {
      id: "level-1-summary",
      title: "Critical Insights & Actions",
      elements: summarizedElements,
      level: 1,
    };
  }

  /**
   * Analyze content complexity and suggest improvements
   */
  static analyzeComplexity(sections: ContentSection[]): {
    overallComplexity: "low" | "medium" | "high";
    suggestions: string[];
    elementBreakdown: Record<string, number>;
  } {
    const elementCounts: Record<string, number> = {};
    let totalComplexity = 0;
    let elementCount = 0;

    sections.forEach((section) => {
      section.elements.forEach((element) => {
        elementCounts[element.type] = (elementCounts[element.type] || 0) + 1;
        totalComplexity += this.COMPLEXITY_MULTIPLIERS[element.complexity];
        elementCount++;
      });
    });

    const averageComplexity = totalComplexity / elementCount;
    const overallComplexity: "low" | "medium" | "high" =
      averageComplexity < 1.3
        ? "low"
        : averageComplexity < 2.0
        ? "medium"
        : "high";

    const suggestions: string[] = [];

    // Generate suggestions based on analysis
    if (elementCounts.table > 2) {
      suggestions.push(
        "Consider converting some tables to simpler charts or metrics"
      );
    }
    if (elementCounts.chart > 3) {
      suggestions.push(
        "Too many charts may overwhelm users - consider progressive disclosure"
      );
    }
    if (overallComplexity === "high") {
      suggestions.push(
        "Content complexity is high - consider simplifying for better comprehension"
      );
    }

    return {
      overallComplexity,
      suggestions,
      elementBreakdown: elementCounts,
    };
  }

  // Private helper methods
  private static removeSupplementaryElements(
    sections: ContentSection[]
  ): ContentSection[] {
    return sections.map((section) => ({
      ...section,
      elements: section.elements.filter(
        (el) => el.priority !== "supplementary"
      ),
    }));
  }

  private static simplifyComplexElements(
    sections: ContentSection[]
  ): ContentSection[] {
    return sections.map((section) => ({
      ...section,
      elements: section.elements.map((el) => ({
        ...el,
        complexity: el.complexity === "high" ? "medium" : el.complexity,
      })),
    }));
  }

  private static keepOnlyCriticalElements(
    sections: ContentSection[]
  ): ContentSection[] {
    return sections.map((section) => ({
      ...section,
      elements: section.elements.filter((el) => el.priority === "critical"),
    }));
  }
}

/**
 * React hook for cognitive load management
 */
export function useCognitiveLoadManager(
  sections: ContentSection[],
  userRole: string = "analyst"
) {
  const optimization = CognitiveLoadManager.optimizeForRole(sections, userRole);
  const complexity = CognitiveLoadManager.analyzeComplexity(sections);
  const level1Summary = CognitiveLoadManager.generateLevel1Summary(sections);

  return {
    ...optimization,
    complexity,
    level1Summary,
    isOverloaded:
      optimization.totalLoad >
      CognitiveLoadManager.getUserRoleConfig(userRole).maxCognitiveLoad,
    roleConfig: CognitiveLoadManager.getUserRoleConfig(userRole),
  };
}
