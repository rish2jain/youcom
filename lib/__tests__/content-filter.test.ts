import { ContentFilterEngine } from "../content-filter";
import { InterfaceMode } from "../types/tribe-interface";

describe("ContentFilterEngine", () => {
  let engine: ContentFilterEngine;

  beforeEach(() => {
    engine = new ContentFilterEngine();
  });

  describe("Content Filtering", () => {
    const mockContent = {
      title: "AI Model Performance Analysis",
      summary:
        "Our ML algorithms utilize advanced neural networks to optimize API performance and enhance user experience.",
      insights: [
        "The neural network architecture leverages deep learning for classification",
        "API response times have been optimized through microservices implementation",
        "Machine learning models show 95% accuracy in regression analysis",
        "The comprehensive framework enables scalable deployment",
        "Advanced algorithms facilitate real-time processing",
      ],
      actions: [
        "Implement new ML model with enhanced neural network architecture",
        "Optimize API endpoints for better performance",
        "Deploy containerized microservices using Kubernetes",
        "Leverage advanced algorithms for data processing",
      ],
      api_usage: {
        news: 3,
        search: 5,
        chat: 2,
        ari: 1,
      },
      confidence_score: 85,
      total_sources: 25,
      source_breakdown: {
        news_articles: 10,
        search_results: 10,
        research_citations: 5,
      },
    };

    it("applies executive mode filtering", () => {
      const filtered = engine.applyContentFilter(mockContent, "executive");

      // Should filter technical jargon
      expect(filtered.summary).not.toContain("ML");
      expect(filtered.summary).toContain("machine learning");
      expect(filtered.summary).not.toContain("API");
      expect(filtered.summary).toContain("data connection");

      // Should prioritize actions
      expect(filtered.priority_actions).toBeDefined();
      expect(filtered.priority_actions.length).toBeLessThanOrEqual(3);

      // Should have executive summary
      expect(filtered.executive_summary).toBeDefined();

      // Should limit insights
      expect(filtered.insights.length).toBeLessThanOrEqual(3);
    });

    it("preserves content for analyst mode", () => {
      const filtered = engine.applyContentFilter(mockContent, "analyst");

      // Should not filter technical jargon
      expect(filtered.summary).toContain("ML");
      expect(filtered.summary).toContain("API");

      // Should preserve all insights
      expect(filtered.insights.length).toBe(mockContent.insights.length);

      // Should not hide implementation details
      expect(filtered.api_usage).toBeDefined();
    });

    it("applies team mode filtering", () => {
      const filtered = engine.applyContentFilter(mockContent, "team");

      // Should filter technical jargon
      expect(filtered.summary).not.toContain("ML");
      expect(filtered.summary).toContain("machine learning");

      // Should add collaborative context
      expect(filtered.summary).toContain("team coordination");

      // Should hide implementation details
      expect(filtered.api_usage).toBeUndefined();
    });
  });

  describe("Technical Jargon Filtering", () => {
    it("replaces technical terms with simpler alternatives", () => {
      const content = {
        summary:
          "Our API utilizes ML algorithms and neural networks for optimization.",
        insights: ["The algorithm leverages advanced ML techniques"],
        actions: ["Implement new API with neural network architecture"],
      };

      const filtered = engine["filterTechnicalJargon"](content);

      expect(filtered.summary).toContain("data connection");
      expect(filtered.summary).toContain("machine learning");
      expect(filtered.summary).toContain("AI system");
      expect(filtered.insights[0]).toContain("automated process");
      expect(filtered.actions[0]).toContain("data connection");
    });

    it("handles nested object filtering", () => {
      const content = {
        insights: [
          { description: "API performance improved with ML optimization" },
          "Direct string insight with neural network details",
        ],
        actions: [
          { action: "Deploy microservices using containerization" },
          "Direct action to implement API changes",
        ],
      };

      const filtered = engine["filterTechnicalJargon"](content);

      expect(filtered.insights[0].description).toContain("data connection");
      expect(filtered.insights[1]).toContain("AI system");
      expect(filtered.actions[0].action).toContain("system components");
      expect(filtered.actions[1]).toContain("data connection");
    });

    it("preserves word boundaries when replacing terms", () => {
      const content = {
        summary:
          "The API call and application programming interface are different.",
      };

      const filtered = engine["filterTechnicalJargon"](content);

      // Should replace "API" but not affect "application"
      expect(filtered.summary).toContain("data connection call");
      expect(filtered.summary).toContain("application programming interface");
    });
  });

  describe("Complexity Reduction", () => {
    it("reduces complexity by limiting array lengths", () => {
      const complexContent = {
        insights: Array(10).fill("Complex insight"),
        actions: Array(8).fill("Complex action"),
        impact_areas: Array(6).fill({ area: "test", description: "test" }),
      };

      const filtered = engine["reduceComplexity"](complexContent, 10);

      expect(filtered.insights.length).toBeLessThan(
        complexContent.insights.length
      );
      expect(filtered.actions.length).toBeLessThan(
        complexContent.actions.length
      );
      expect(filtered.impact_areas.length).toBeLessThanOrEqual(3);
    });

    it("simplifies source breakdown", () => {
      const content = {
        source_breakdown: {
          news_articles: 10,
          search_results: 15,
          research_citations: 5,
        },
      };

      const filtered = engine["reduceComplexity"](content, 5);

      expect(filtered.source_breakdown).toBeUndefined();
      expect(filtered.source_summary).toBe("30 sources analyzed");
    });

    it("preserves content when complexity is within limits", () => {
      const simpleContent = {
        title: "Simple",
        summary: "Short summary",
        insights: ["One insight"],
      };

      const originalComplexity = engine["calculateComplexity"](simpleContent);
      const filtered = engine["reduceComplexity"](
        simpleContent,
        originalComplexity + 5
      );

      expect(filtered).toEqual(simpleContent);
    });
  });

  describe("Action Prioritization", () => {
    it("creates priority actions for executive mode", () => {
      const content = {
        recommended_actions: [
          { action: "Action 1", priority: "high", timeline: "immediate" },
          { action: "Action 2", priority: "medium", timeline: "short-term" },
          { action: "Action 3", priority: "low", timeline: "long-term" },
          { action: "Action 4", priority: "high", timeline: "immediate" },
        ],
      };

      const filtered = engine["prioritizeActions"](content);

      expect(filtered.priority_actions).toBeDefined();
      expect(filtered.priority_actions.length).toBeLessThanOrEqual(3);
      expect(filtered.priority_actions[0]).toHaveProperty("action");
      expect(filtered.priority_actions[0]).toHaveProperty("priority");
      expect(filtered.priority_actions[0]).toHaveProperty("timeline");
      expect(filtered.priority_actions[0]).toHaveProperty("owner");
    });

    it("limits insights when prioritizing actions", () => {
      const content = {
        key_insights: Array(10).fill("Insight"),
        insights: Array(8).fill("Another insight"),
      };

      const filtered = engine["prioritizeActions"](content);

      expect(filtered.key_insights.length).toBeLessThanOrEqual(2);
      expect(filtered.insights.length).toBeLessThanOrEqual(2);
    });

    it("creates executive summary when missing", () => {
      const content = {
        competitor_name: "OpenAI",
        risk_level: "high",
        risk_score: 85,
        key_insights: ["Major product launch detected"],
        recommended_actions: [{ action: "Assess competitive impact" }],
      };

      const filtered = engine["prioritizeActions"](content);

      expect(filtered.executive_summary).toBeDefined();
      expect(filtered.executive_summary).toContain("OpenAI");
      expect(filtered.executive_summary).toContain("high");
      expect(filtered.executive_summary).toContain("85");
    });
  });

  describe("Implementation Details Hiding", () => {
    it("removes technical fields", () => {
      const content = {
        title: "Test",
        api_usage: { news: 1, search: 2 },
        processing_time: "2.3s",
        explainability: { reasoning: "test" },
        source_quality: { score: 0.8 },
        credibility_score: 0.85,
        total_sources: 25,
      };

      const filtered = engine["hideImplementationDetails"](content);

      expect(filtered.api_usage).toBeUndefined();
      expect(filtered.processing_time).toBeUndefined();
      expect(filtered.explainability).toBeUndefined();
      expect(filtered.source_quality).toBeUndefined();
      expect(filtered.credibility_score).toBeUndefined();
      expect(filtered.source_summary).toBe(
        "Analysis based on 25 verified sources"
      );
    });

    it("preserves essential content", () => {
      const content = {
        title: "Test Analysis",
        summary: "Test summary",
        insights: ["Test insight"],
        actions: ["Test action"],
        api_usage: { news: 1 },
      };

      const filtered = engine["hideImplementationDetails"](content);

      expect(filtered.title).toBe(content.title);
      expect(filtered.summary).toBe(content.summary);
      expect(filtered.insights).toEqual(content.insights);
      expect(filtered.actions).toEqual(content.actions);
    });
  });

  describe("Evidence Summarization", () => {
    it("creates evidence summary from source data", () => {
      const content = {
        total_sources: 25,
        credibility_score: 0.87,
        source_quality: {
          score: 0.85,
          tiers: { tier1: 10, tier2: 10, tier3: 5 },
        },
      };

      const filtered = engine["summarizeEvidence"](content);

      expect(filtered.evidence_summary).toBeDefined();
      expect(filtered.evidence_summary.source_count).toBe(25);
      expect(filtered.evidence_summary.credibility_score).toBe(87);
      expect(filtered.evidence_summary.summary).toContain(
        "25 verified sources"
      );
      expect(filtered.evidence_summary.summary).toContain("87% credibility");
    });

    it("summarizes impact areas", () => {
      const content = {
        impact_areas: [
          { area: "product", impact_score: 85, description: "Product impact" },
          { area: "market", impact_score: 70, description: "Market impact" },
          { area: "pricing", impact_score: 90, description: "Pricing impact" },
        ],
      };

      const filtered = engine["summarizeEvidence"](content);

      expect(filtered.primary_impact).toBeDefined();
      expect(filtered.primary_impact.area).toBe("pricing"); // Highest score
      expect(filtered.primary_impact.severity).toBe("critical"); // Score > 80
      expect(filtered.primary_impact.description).toBe("Pricing impact");
    });

    it("removes detailed source information", () => {
      const content = {
        source_quality: { score: 0.8 },
        source_breakdown: { news: 10, search: 10 },
        total_sources: 20,
      };

      const filtered = engine["summarizeEvidence"](content);

      expect(filtered.source_quality).toBeUndefined();
      expect(filtered.source_breakdown).toBeUndefined();
      expect(filtered.evidence_summary).toBeDefined();
    });
  });

  describe("Language Simplification", () => {
    it("simplifies complex sentences", () => {
      const text =
        "In order to facilitate the optimization of our comprehensive infrastructure, we need to leverage advanced algorithms.";

      const simplified = engine["simplifySentences"](text);

      expect(simplified).not.toContain("in order to");
      expect(simplified).toContain("to");
      expect(simplified).not.toContain("facilitate");
      expect(simplified).toContain("help");
      expect(simplified).not.toContain("comprehensive");
      expect(simplified).toContain("complete");
    });

    it("removes parenthetical information", () => {
      const text =
        "The system (which was developed last year) shows good performance.";

      const simplified = engine["simplifySentences"](text);

      expect(simplified).not.toContain("(which was developed last year)");
      expect(simplified).toContain("The system shows good performance");
    });

    it("removes redundant words", () => {
      const text = "This is very extremely important and absolutely critical.";

      const simplified = engine["simplifySentences"](text);

      expect(simplified).not.toContain("very");
      expect(simplified).not.toContain("extremely");
      expect(simplified).not.toContain("absolutely");
      expect(simplified).toContain("important and critical");
    });
  });

  describe("Summary Generation", () => {
    const content = {
      competitor_name: "OpenAI",
      risk_score: 85,
      risk_level: "high",
      confidence_score: 90,
      total_sources: 25,
      key_insights: ["GPT-5 released with advanced capabilities"],
      recommended_actions: [
        { action: "Assess competitive impact immediately" },
      ],
      impact_areas: [
        {
          area: "product",
          impact_score: 80,
          description: "Product differentiation at risk",
        },
      ],
    };

    it("generates executive summary", () => {
      const summary = engine.generateSummary(content, "executive", 200);

      expect(summary).toContain("OpenAI");
      expect(summary).toContain("HIGH THREAT");
      expect(summary).toContain("85/100");
      expect(summary).toContain("ACTION:");
      expect(summary.length).toBeLessThanOrEqual(200);
    });

    it("generates analyst summary", () => {
      const summary = engine.generateSummary(content, "analyst", 300);

      expect(summary).toContain("OpenAI");
      expect(summary).toContain("85/100 risk score");
      expect(summary).toContain("90% confidence");
      expect(summary).toContain("25 sources");
      expect(summary).toContain("Primary impact: product");
      expect(summary.length).toBeLessThanOrEqual(300);
    });

    it("generates team summary", () => {
      const summary = engine.generateSummary(content, "team", 250);

      expect(summary).toContain("Team alert");
      expect(summary).toContain("OpenAI");
      expect(summary).toContain("85/100 risk");
      expect(summary).toContain("Team action needed");
      expect(summary).toContain("Collaboration and coordination required");
      expect(summary.length).toBeLessThanOrEqual(250);
    });

    it("respects maximum length constraint", () => {
      const summary = engine.generateSummary(content, "analyst", 50);

      expect(summary.length).toBeLessThanOrEqual(50);
    });
  });

  describe("Complexity Calculation", () => {
    it("calculates complexity based on text length", () => {
      const shortContent = { summary: "Short" };
      const longContent = { summary: "A".repeat(500) };

      const shortComplexity = engine["calculateComplexity"](shortContent);
      const longComplexity = engine["calculateComplexity"](longContent);

      expect(longComplexity).toBeGreaterThan(shortComplexity);
    });

    it("adds complexity for technical terms", () => {
      const simpleContent = { summary: "Simple analysis of the situation" };
      const technicalContent = {
        summary: "API ML neural network algorithm optimization",
      };

      const simpleComplexity = engine["calculateComplexity"](simpleContent);
      const technicalComplexity =
        engine["calculateComplexity"](technicalContent);

      expect(technicalComplexity).toBeGreaterThan(simpleComplexity);
    });

    it("adds complexity for arrays and objects", () => {
      const simpleContent = { title: "Test" };
      const complexContent = {
        title: "Test",
        insights: ["1", "2", "3"],
        actions: ["a", "b"],
        api_usage: { news: 1, search: 2, chat: 3 },
      };

      const simpleComplexity = engine["calculateComplexity"](simpleContent);
      const complexComplexity = engine["calculateComplexity"](complexContent);

      expect(complexComplexity).toBeGreaterThan(simpleComplexity);
    });
  });

  describe("Term Replacement", () => {
    it("replaces terms with word boundaries", () => {
      const text = "The API call and application are different";
      const replacements = { API: "data connection" };

      const result = engine["replaceTerms"](text, replacements);

      expect(result).toBe(
        "The data connection call and application are different"
      );
    });

    it("handles case insensitive replacement", () => {
      const text = "API and api are the same";
      const replacements = { API: "data connection" };

      const result = engine["replaceTerms"](text, replacements);

      expect(result).toBe("data connection and data connection are the same");
    });

    it("handles multiple replacements", () => {
      const text = "The API uses ML algorithms";
      const replacements = {
        API: "data connection",
        ML: "machine learning",
      };

      const result = engine["replaceTerms"](text, replacements);

      expect(result).toBe(
        "The data connection uses machine learning algorithms"
      );
    });

    it("handles overlapping terms correctly", () => {
      const text = "REST API and API calls";
      const replacements = {
        "REST API": "web service",
        API: "data connection",
      };

      const result = engine["replaceTerms"](text, replacements);

      // Should replace longer term first
      expect(result).toBe("web service and data connection calls");
    });
  });
});
