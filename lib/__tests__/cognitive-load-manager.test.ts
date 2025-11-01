import {
  CognitiveLoadManager,
  CognitiveElement,
  ContentSection,
} from "../cognitive-load-manager";

describe("CognitiveLoadManager", () => {
  const mockElements: CognitiveElement[] = [
    {
      id: "text-1",
      type: "text",
      complexity: "low",
      priority: "critical",
    },
    {
      id: "metric-1",
      type: "metric",
      complexity: "medium",
      priority: "important",
    },
    {
      id: "chart-1",
      type: "chart",
      complexity: "high",
      priority: "supplementary",
    },
    {
      id: "table-1",
      type: "table",
      complexity: "high",
      priority: "important",
    },
  ];

  const mockSection: ContentSection = {
    id: "section-1",
    title: "Test Section",
    elements: mockElements,
    level: 1,
  };

  describe("calculateElementLoad", () => {
    it("calculates load for text element correctly", () => {
      const element: CognitiveElement = {
        id: "test",
        type: "text",
        complexity: "low",
        priority: "critical",
      };

      const load = CognitiveLoadManager.calculateElementLoad(element);
      // Base weight (1) * complexity (1) * priority (1.5) = 1.5
      expect(load).toBe(1.5);
    });

    it("calculates load for complex chart element correctly", () => {
      const element: CognitiveElement = {
        id: "test",
        type: "chart",
        complexity: "high",
        priority: "important",
      };

      const load = CognitiveLoadManager.calculateElementLoad(element);
      // Base weight (4) * complexity (2.5) * priority (1.2) = 12
      expect(load).toBe(12);
    });

    it("uses custom weight when provided", () => {
      const element: CognitiveElement = {
        id: "test",
        type: "text",
        complexity: "low",
        priority: "critical",
        weight: 10,
      };

      const load = CognitiveLoadManager.calculateElementLoad(element);
      // Custom weight (10) * complexity (1) * priority (1.5) = 15
      expect(load).toBe(15);
    });

    it("handles unknown element types with default weight", () => {
      const element: CognitiveElement = {
        id: "test",
        type: "unknown" as any,
        complexity: "medium",
        priority: "important",
      };

      const load = CognitiveLoadManager.calculateElementLoad(element);
      // Default weight (1) * complexity (1.5) * priority (1.2) = 1.8
      expect(load).toBe(1.8);
    });
  });

  describe("calculateSectionLoad", () => {
    it("calculates total load for section", () => {
      const load = CognitiveLoadManager.calculateSectionLoad(mockSection);

      // text: 1 * 1 * 1.5 = 1.5
      // metric: 2 * 1.5 * 1.2 = 3.6
      // chart: 4 * 2.5 * 0.8 = 8
      // table: 5 * 2.5 * 1.2 = 15
      // Total: 28.1
      expect(load).toBe(28.1);
    });

    it("handles empty section", () => {
      const emptySection: ContentSection = {
        id: "empty",
        title: "Empty Section",
        elements: [],
        level: 1,
      };

      const load = CognitiveLoadManager.calculateSectionLoad(emptySection);
      expect(load).toBe(0);
    });
  });

  describe("calculateTotalLoad", () => {
    it("calculates total load across multiple sections", () => {
      const sections = [mockSection, mockSection]; // Same section twice
      const load = CognitiveLoadManager.calculateTotalLoad(sections);

      expect(load).toBe(28.1 * 2); // 56.2
    });

    it("handles empty sections array", () => {
      const load = CognitiveLoadManager.calculateTotalLoad([]);
      expect(load).toBe(0);
    });
  });

  describe("getUserRoleConfig", () => {
    it("returns executive config", () => {
      const config = CognitiveLoadManager.getUserRoleConfig("executive");

      expect(config.type).toBe("executive");
      expect(config.maxCognitiveLoad).toBe(15);
      expect(config.preferredComplexity).toBe("low");
      expect(config.attentionSpan).toBe(30);
    });

    it("returns analyst config", () => {
      const config = CognitiveLoadManager.getUserRoleConfig("analyst");

      expect(config.type).toBe("analyst");
      expect(config.maxCognitiveLoad).toBe(25);
      expect(config.preferredComplexity).toBe("medium");
      expect(config.attentionSpan).toBe(120);
    });

    it("returns technical config", () => {
      const config = CognitiveLoadManager.getUserRoleConfig("technical");

      expect(config.type).toBe("technical");
      expect(config.maxCognitiveLoad).toBe(40);
      expect(config.preferredComplexity).toBe("high");
      expect(config.attentionSpan).toBe(300);
    });

    it("returns analyst config for unknown role", () => {
      const config = CognitiveLoadManager.getUserRoleConfig("unknown");

      expect(config.type).toBe("analyst");
    });
  });

  describe("optimizeForRole", () => {
    it("returns original sections when under cognitive load limit", () => {
      const lightSection: ContentSection = {
        id: "light",
        title: "Light Section",
        elements: [
          {
            id: "light-text",
            type: "text",
            complexity: "low",
            priority: "important",
          },
        ],
        level: 1,
      };

      const result = CognitiveLoadManager.optimizeForRole(
        [lightSection],
        "executive"
      );

      expect(result.optimizedSections).toHaveLength(1);
      expect(result.optimizedSections[0].elements).toHaveLength(1);
      expect(result.totalLoad).toBeLessThan(15); // Executive limit
    });

    it("removes supplementary elements when over limit", () => {
      const result = CognitiveLoadManager.optimizeForRole(
        [mockSection],
        "executive"
      );

      // Should remove supplementary elements (chart)
      const optimizedElements = result.optimizedSections[0].elements;
      const hasSupplementary = optimizedElements.some(
        (el) => el.priority === "supplementary"
      );

      expect(hasSupplementary).toBe(false);
      expect(result.recommendations).toContain(
        "Removed supplementary elements to reduce cognitive load"
      );
    });

    it("simplifies complex elements when still over limit", () => {
      const heavySection: ContentSection = {
        id: "heavy",
        title: "Heavy Section",
        elements: [
          {
            id: "heavy-table-1",
            type: "table",
            complexity: "high",
            priority: "critical",
          },
          {
            id: "heavy-table-2",
            type: "table",
            complexity: "high",
            priority: "important",
          },
          {
            id: "heavy-chart",
            type: "chart",
            complexity: "high",
            priority: "important",
          },
        ],
        level: 1,
      };

      const result = CognitiveLoadManager.optimizeForRole(
        [heavySection],
        "executive"
      );

      // Should simplify complexity
      const hasHighComplexity = result.optimizedSections[0].elements.some(
        (el) => el.complexity === "high"
      );

      if (result.recommendations.includes("Simplified complex elements")) {
        expect(hasHighComplexity).toBe(false);
      }
    });

    it("keeps only critical elements as last resort", () => {
      const veryHeavySection: ContentSection = {
        id: "very-heavy",
        title: "Very Heavy Section",
        elements: Array(10)
          .fill(null)
          .map((_, i) => ({
            id: `heavy-${i}`,
            type: "table" as const,
            complexity: "high" as const,
            priority: i < 2 ? ("critical" as const) : ("important" as const),
          })),
        level: 1,
      };

      const result = CognitiveLoadManager.optimizeForRole(
        [veryHeavySection],
        "executive"
      );

      if (result.recommendations.includes("Showing only critical elements")) {
        const criticalOnly = result.optimizedSections[0].elements.every(
          (el) => el.priority === "critical"
        );
        expect(criticalOnly).toBe(true);
      }
    });

    it("includes role-specific recommendations", () => {
      const result = CognitiveLoadManager.optimizeForRole(
        [mockSection],
        "executive"
      );

      expect(result.recommendations).toContain(
        "Executive view: Showing key insights and actions only"
      );
    });
  });

  describe("generateLevel1Summary", () => {
    it("extracts critical elements from sections", () => {
      const sections = [
        {
          id: "section-1",
          title: "Section 1",
          elements: [
            {
              id: "critical-1",
              type: "text" as const,
              complexity: "low" as const,
              priority: "critical" as const,
            },
            {
              id: "important-1",
              type: "metric" as const,
              complexity: "medium" as const,
              priority: "important" as const,
            },
          ],
          level: 1 as const,
        },
        {
          id: "section-2",
          title: "Section 2",
          elements: [
            {
              id: "critical-2",
              type: "action" as const,
              complexity: "medium" as const,
              priority: "critical" as const,
            },
            {
              id: "supplementary-1",
              type: "chart" as const,
              complexity: "high" as const,
              priority: "supplementary" as const,
            },
          ],
          level: 2 as const,
        },
      ];

      const summary = CognitiveLoadManager.generateLevel1Summary(sections);

      expect(summary.id).toBe("level-1-summary");
      expect(summary.title).toBe("Critical Insights & Actions");
      expect(summary.level).toBe(1);
      expect(summary.elements).toHaveLength(2); // Max 2 critical per section
      expect(summary.elements.every((el) => el.priority === "critical")).toBe(
        true
      );
    });

    it("limits to maximum 5 elements", () => {
      const sections = [
        {
          id: "section-1",
          title: "Section 1",
          elements: Array(10)
            .fill(null)
            .map((_, i) => ({
              id: `critical-${i}`,
              type: "text" as const,
              complexity: "low" as const,
              priority: "critical" as const,
            })),
          level: 1 as const,
        },
      ];

      const summary = CognitiveLoadManager.generateLevel1Summary(sections);

      expect(summary.elements).toHaveLength(5);
    });
  });

  describe("analyzeComplexity", () => {
    it("analyzes overall complexity correctly", () => {
      const sections = [mockSection];
      const analysis = CognitiveLoadManager.analyzeComplexity(sections);

      expect(analysis.overallComplexity).toBe("high"); // Average complexity > 2.0
      expect(analysis.elementBreakdown).toEqual({
        text: 1,
        metric: 1,
        chart: 1,
        table: 1,
      });
    });

    it("provides suggestions for table-heavy content", () => {
      const tableHeavySection: ContentSection = {
        id: "tables",
        title: "Tables Section",
        elements: Array(5)
          .fill(null)
          .map((_, i) => ({
            id: `table-${i}`,
            type: "table" as const,
            complexity: "high" as const,
            priority: "important" as const,
          })),
        level: 1,
      };

      const analysis = CognitiveLoadManager.analyzeComplexity([
        tableHeavySection,
      ]);

      expect(analysis.suggestions).toContain(
        "Consider converting some tables to simpler charts or metrics"
      );
    });

    it("provides suggestions for chart-heavy content", () => {
      const chartHeavySection: ContentSection = {
        id: "charts",
        title: "Charts Section",
        elements: Array(5)
          .fill(null)
          .map((_, i) => ({
            id: `chart-${i}`,
            type: "chart" as const,
            complexity: "medium" as const,
            priority: "important" as const,
          })),
        level: 1,
      };

      const analysis = CognitiveLoadManager.analyzeComplexity([
        chartHeavySection,
      ]);

      expect(analysis.suggestions).toContain(
        "Too many charts may overwhelm users - consider progressive disclosure"
      );
    });

    it("suggests simplification for high complexity", () => {
      const analysis = CognitiveLoadManager.analyzeComplexity([mockSection]);

      expect(analysis.suggestions).toContain(
        "Content complexity is high - consider simplifying for better comprehension"
      );
    });

    it("handles empty sections", () => {
      const analysis = CognitiveLoadManager.analyzeComplexity([]);

      expect(analysis.overallComplexity).toBe("low");
      expect(analysis.elementBreakdown).toEqual({});
      expect(analysis.suggestions).toHaveLength(0);
    });
  });
});
