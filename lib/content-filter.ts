import { InterfaceMode, ContentFilter } from "./types/tribe-interface";

/**
 * Content filtering and summarization algorithms for different user roles
 */
export class ContentFilterEngine {
  private technicalTerms: Record<string, string> = {
    // API and Technical Terms
    API: "data connection",
    "REST API": "web service",
    GraphQL: "data query system",
    JSON: "data format",
    HTTP: "web protocol",
    HTTPS: "secure web protocol",
    SQL: "database query",
    NoSQL: "flexible database",
    PostgreSQL: "database system",
    Redis: "fast storage",

    // AI/ML Terms
    ML: "machine learning",
    "AI model": "artificial intelligence system",
    "neural network": "AI system",
    "deep learning": "advanced AI",
    algorithm: "automated process",
    regression: "prediction method",
    clustering: "grouping method",
    classification: "categorization method",
    "natural language processing": "text analysis",
    NLP: "text analysis",
    transformer: "AI architecture",
    GPT: "text generation AI",
    LLM: "language AI system",

    // Infrastructure Terms
    microservices: "system components",
    containerization: "deployment method",
    Kubernetes: "container management",
    Docker: "container technology",
    "CI/CD": "automated deployment",
    DevOps: "development operations",
    "cloud computing": "remote computing",
    serverless: "managed computing",
    "load balancer": "traffic distributor",
    CDN: "content delivery network",

    // Business/Technical Jargon
    utilize: "use",
    leverage: "use",
    facilitate: "help",
    enable: "allow",
    optimize: "improve",
    enhance: "improve",
    implement: "build",
    deploy: "launch",
    integrate: "connect",
    scalable: "expandable",
    robust: "reliable",
    comprehensive: "complete",
    extensive: "wide-ranging",
    sophisticated: "advanced",
    "cutting-edge": "latest",
    "state-of-the-art": "advanced",
    paradigm: "approach",
    methodology: "method",
    framework: "structure",
    architecture: "design",
    infrastructure: "foundation",
  };

  private businessTerms: Record<string, string> = {
    ROI: "return on investment",
    KPI: "key performance indicator",
    OKR: "objectives and key results",
    SLA: "service level agreement",
    B2B: "business-to-business",
    B2C: "business-to-consumer",
    SaaS: "software as a service",
    PaaS: "platform as a service",
    IaaS: "infrastructure as a service",
    MVP: "minimum viable product",
    PMF: "product-market fit",
    GTM: "go-to-market",
    TAM: "total addressable market",
    SAM: "serviceable addressable market",
    CAC: "customer acquisition cost",
    LTV: "lifetime value",
    ARR: "annual recurring revenue",
    MRR: "monthly recurring revenue",
    churn: "customer loss rate",
  };

  /**
   * Apply content filtering based on interface mode
   */
  applyContentFilter(content: any, mode: InterfaceMode): any {
    const filter = this.getFilterConfig(mode);
    let filteredContent = { ...content };

    // Apply technical jargon filtering
    if (filter.filterTechnicalJargon) {
      filteredContent = this.filterTechnicalJargon(filteredContent);
    }

    // Apply complexity reduction
    if (filter.maxComplexity > 0) {
      filteredContent = this.reduceComplexity(
        filteredContent,
        filter.maxComplexity
      );
    }

    // Prioritize actions for executive mode
    if (filter.prioritizeActions) {
      filteredContent = this.prioritizeActions(filteredContent);
    }

    // Hide implementation details
    if (filter.hideImplementationDetails) {
      filteredContent = this.hideImplementationDetails(filteredContent);
    }

    // Summarize evidence
    if (filter.summarizeEvidence) {
      filteredContent = this.summarizeEvidence(filteredContent);
    }

    return filteredContent;
  }

  /**
   * Get filter configuration for interface mode
   */
  private getFilterConfig(mode: InterfaceMode): ContentFilter {
    const configs: Record<InterfaceMode, ContentFilter> = {
      executive: {
        filterTechnicalJargon: true,
        maxComplexity: 10,
        prioritizeActions: true,
        hideImplementationDetails: true,
        summarizeEvidence: true,
      },
      analyst: {
        filterTechnicalJargon: false,
        maxComplexity: 25,
        prioritizeActions: false,
        hideImplementationDetails: false,
        summarizeEvidence: false,
      },
      team: {
        filterTechnicalJargon: true,
        maxComplexity: 15,
        prioritizeActions: false,
        hideImplementationDetails: true,
        summarizeEvidence: false,
      },
    };

    return configs[mode];
  }

  /**
   * Filter technical jargon and replace with simpler terms
   */
  private filterTechnicalJargon(content: any): any {
    const filtered = { ...content };
    const allTerms = { ...this.technicalTerms, ...this.businessTerms };

    // Filter text fields
    const textFields = ["title", "summary", "description"];
    textFields.forEach((field) => {
      if (filtered[field]) {
        filtered[field] = this.replaceTerms(filtered[field], allTerms);
      }
    });

    // Filter arrays of strings
    const arrayFields = [
      "insights",
      "key_insights",
      "actions",
      "recommendations",
    ];
    arrayFields.forEach((field) => {
      if (Array.isArray(filtered[field])) {
        filtered[field] = filtered[field].map((item: any) => {
          if (typeof item === "string") {
            return this.replaceTerms(item, allTerms);
          } else if (item.action) {
            return {
              ...item,
              action: this.replaceTerms(item.action, allTerms),
            };
          } else if (item.description) {
            return {
              ...item,
              description: this.replaceTerms(item.description, allTerms),
            };
          }
          return item;
        });
      }
    });

    return filtered;
  }

  /**
   * Reduce content complexity by simplifying sentences and structure
   */
  private reduceComplexity(content: any, maxComplexity: number): any {
    const filtered = { ...content };
    let currentComplexity = this.calculateComplexity(content);

    if (currentComplexity <= maxComplexity) {
      return filtered;
    }

    // Simplify sentences
    const textFields = ["title", "summary", "description"];
    textFields.forEach((field) => {
      if (filtered[field]) {
        filtered[field] = this.simplifySentences(filtered[field]);
      }
    });

    // Limit array lengths
    const arrayFields = [
      "insights",
      "key_insights",
      "actions",
      "recommendations",
    ];
    arrayFields.forEach((field) => {
      if (Array.isArray(filtered[field])) {
        const maxItems = Math.max(1, Math.floor(maxComplexity / 3));
        filtered[field] = filtered[field].slice(0, maxItems);
      }
    });

    // Remove complex nested structures
    if (filtered.impact_areas && filtered.impact_areas.length > 3) {
      filtered.impact_areas = filtered.impact_areas.slice(0, 3);
    }

    if (filtered.source_breakdown) {
      filtered.source_summary = `${
        filtered.source_breakdown.news_articles +
        filtered.source_breakdown.search_results +
        filtered.source_breakdown.research_citations
      } sources analyzed`;
      delete filtered.source_breakdown;
    }

    return filtered;
  }

  /**
   * Prioritize actions over insights for executive mode
   */
  private prioritizeActions(content: any): any {
    const filtered = { ...content };

    // Move actions to the top and limit insights
    if (filtered.recommended_actions || filtered.next_steps_plan) {
      const actions = filtered.recommended_actions || filtered.next_steps_plan;
      filtered.priority_actions = actions.slice(0, 3).map((action: any) => ({
        action: action.action || action,
        priority: action.priority || "high",
        timeline: action.timeline || "immediate",
        owner: action.owner || "leadership team",
      }));
    }

    // Limit insights to most critical
    if (filtered.key_insights) {
      filtered.key_insights = filtered.key_insights.slice(0, 2);
    }

    if (filtered.insights) {
      filtered.insights = filtered.insights.slice(0, 2);
    }

    // Add executive summary if not present
    if (!filtered.executive_summary && filtered.summary) {
      filtered.executive_summary = this.createExecutiveSummary(filtered);
    }

    return filtered;
  }

  /**
   * Hide implementation details for non-analyst modes
   */
  private hideImplementationDetails(content: any): any {
    const filtered = { ...content };

    // Remove technical implementation details
    const technicalFields = [
      "api_usage",
      "processing_time",
      "explainability",
      "source_quality",
      "credibility_score",
      "confidence_intervals",
      "model_parameters",
      "feature_weights",
    ];

    technicalFields.forEach((field) => {
      delete filtered[field];
    });

    // Simplify source information
    if (filtered.total_sources) {
      filtered.source_summary = `Analysis based on ${filtered.total_sources} verified sources`;
    }

    return filtered;
  }

  /**
   * Summarize evidence for executive consumption
   */
  private summarizeEvidence(content: any): any {
    const filtered = { ...content };

    // Create evidence summary
    if (filtered.source_quality || filtered.total_sources) {
      const sources = filtered.total_sources || 0;
      const credibility = filtered.credibility_score
        ? Math.round(filtered.credibility_score * 100)
        : 85;

      filtered.evidence_summary = {
        source_count: sources,
        credibility_score: credibility,
        summary: `High-confidence analysis based on ${sources} verified sources with ${credibility}% credibility rating`,
      };

      // Remove detailed source information
      delete filtered.source_quality;
      delete filtered.source_breakdown;
    }

    // Summarize impact areas
    if (filtered.impact_areas && filtered.impact_areas.length > 0) {
      const topImpact = filtered.impact_areas.sort(
        (a: any, b: any) => b.impact_score - a.impact_score
      )[0];

      filtered.primary_impact = {
        area: topImpact.area,
        severity:
          topImpact.impact_score > 80
            ? "critical"
            : topImpact.impact_score > 60
            ? "high"
            : "moderate",
        description: topImpact.description,
      };
    }

    return filtered;
  }

  /**
   * Create executive summary from content
   */
  private createExecutiveSummary(content: any): string {
    const competitor = content.competitor_name || "Competitor";
    const riskLevel = content.risk_level || "moderate";
    const riskScore = content.risk_score || 50;

    let summary = `${competitor} poses a ${riskLevel} competitive threat (${riskScore}/100 risk score).`;

    if (content.key_insights && content.key_insights.length > 0) {
      const topInsight = content.key_insights[0];
      summary += ` Key concern: ${this.simplifySentences(topInsight)}.`;
    }

    if (content.recommended_actions && content.recommended_actions.length > 0) {
      const topAction = content.recommended_actions[0];
      const action = topAction.action || topAction;
      summary += ` Immediate action required: ${this.simplifySentences(
        action
      )}.`;
    }

    return summary;
  }

  /**
   * Simplify complex sentences
   */
  private simplifySentences(text: string): string {
    return (
      text
        // Break long sentences
        .replace(/([.!?])\s+([A-Z])/g, "$1 $2")
        // Remove parenthetical information
        .replace(/\([^)]*\)/g, "")
        // Simplify complex phrases
        .replace(/in order to/gi, "to")
        .replace(/due to the fact that/gi, "because")
        .replace(/it is important to note that/gi, "")
        .replace(/it should be noted that/gi, "")
        .replace(/as a result of/gi, "because of")
        .replace(/with regard to/gi, "about")
        .replace(/in the event that/gi, "if")
        // Remove redundant words
        .replace(/\b(very|quite|rather|extremely|incredibly)\s+/gi, "")
        .replace(/\b(absolutely|completely|totally)\s+/gi, "")
        // Clean up extra spaces
        .replace(/\s+/g, " ")
        .trim()
    );
  }

  /**
   * Replace terms with simpler alternatives
   */
  private replaceTerms(
    text: string,
    replacements: Record<string, string>
  ): string {
    let result = text;

    // Sort by length (longest first) to avoid partial replacements
    const sortedTerms = Object.keys(replacements).sort(
      (a, b) => b.length - a.length
    );

    sortedTerms.forEach((term) => {
      const replacement = replacements[term];
      // Use word boundaries to avoid partial matches
      const regex = new RegExp(
        `\\b${term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`,
        "gi"
      );
      result = result.replace(regex, replacement);
    });

    return result;
  }

  /**
   * Calculate content complexity score
   */
  private calculateComplexity(content: any): number {
    let complexity = 0;

    // Text complexity
    const textFields = ["title", "summary", "description"];
    textFields.forEach((field) => {
      if (content[field]) {
        complexity += Math.floor(content[field].length / 50);
        // Add complexity for technical terms
        const technicalTermCount = Object.keys(this.technicalTerms).filter(
          (term) => content[field].toLowerCase().includes(term.toLowerCase())
        ).length;
        complexity += technicalTermCount;
      }
    });

    // Array complexity
    const arrayFields = [
      "insights",
      "key_insights",
      "actions",
      "recommendations",
      "impact_areas",
    ];
    arrayFields.forEach((field) => {
      if (Array.isArray(content[field])) {
        complexity += content[field].length;
      }
    });

    // Object complexity
    const objectFields = ["api_usage", "source_breakdown", "explainability"];
    objectFields.forEach((field) => {
      if (content[field] && typeof content[field] === "object") {
        complexity += Object.keys(content[field]).length;
      }
    });

    return complexity;
  }

  /**
   * Generate content summary for different modes
   */
  generateSummary(
    content: any,
    mode: InterfaceMode,
    maxLength: number = 200
  ): string {
    const competitor = content.competitor_name || "Competitor";
    const riskScore = content.risk_score || 0;
    const riskLevel = content.risk_level || "low";

    if (mode === "executive") {
      return this.generateExecutiveSummary(content, maxLength);
    } else if (mode === "analyst") {
      return this.generateAnalystSummary(content, maxLength);
    } else if (mode === "team") {
      return this.generateTeamSummary(content, maxLength);
    }

    return `${competitor} analysis complete with ${riskLevel} risk level (${riskScore}/100).`;
  }

  /**
   * Generate executive-focused summary
   */
  private generateExecutiveSummary(content: any, maxLength: number): string {
    const competitor = content.competitor_name || "Competitor";
    const riskScore = content.risk_score || 0;
    const riskLevel = content.risk_level || "low";

    let summary = `${competitor}: ${riskLevel.toUpperCase()} THREAT (${riskScore}/100). `;

    if (content.key_insights && content.key_insights.length > 0) {
      const insight = this.simplifySentences(content.key_insights[0]);
      summary += `${insight.substring(0, 100)}. `;
    }

    if (content.recommended_actions && content.recommended_actions.length > 0) {
      const action = content.recommended_actions[0];
      const actionText = action.action || action;
      summary += `ACTION: ${this.simplifySentences(actionText).substring(
        0,
        80
      )}.`;
    }

    return summary.substring(0, maxLength);
  }

  /**
   * Generate analyst-focused summary
   */
  private generateAnalystSummary(content: any, maxLength: number): string {
    const competitor = content.competitor_name || "Competitor";
    const riskScore = content.risk_score || 0;
    const confidence = content.confidence_score || 0;
    const sources = content.total_sources || 0;

    let summary = `${competitor} competitive analysis: ${riskScore}/100 risk score with ${confidence}% confidence based on ${sources} sources. `;

    if (content.impact_areas && content.impact_areas.length > 0) {
      const topImpact = content.impact_areas.sort(
        (a: any, b: any) => b.impact_score - a.impact_score
      )[0];
      summary += `Primary impact: ${topImpact.area} (${topImpact.impact_score}/100). `;
    }

    if (content.key_insights && content.key_insights.length > 0) {
      summary += `Key insights: ${content.key_insights
        .slice(0, 2)
        .join("; ")}.`;
    }

    return summary.substring(0, maxLength);
  }

  /**
   * Generate team-focused summary
   */
  private generateTeamSummary(content: any, maxLength: number): string {
    const competitor = content.competitor_name || "Competitor";
    const riskScore = content.risk_score || 0;

    let summary = `Team alert: ${competitor} competitive activity detected (${riskScore}/100 risk). `;

    if (content.recommended_actions && content.recommended_actions.length > 0) {
      const teamActions = content.recommended_actions.filter(
        (action: any) =>
          !action.owner ||
          (!action.owner.toLowerCase().includes("executive") &&
            !action.owner.toLowerCase().includes("ceo"))
      );

      if (teamActions.length > 0) {
        const action = teamActions[0];
        const actionText = action.action || action;
        summary += `Team action needed: ${actionText.substring(0, 100)}. `;
      }
    }

    summary += "Collaboration and coordination required across teams.";

    return summary.substring(0, maxLength);
  }
}

// Singleton instance - lazy initialization to avoid circular dependencies
let _contentFilterEngine: ContentFilterEngine | null = null;
export const contentFilterEngine = () => {
  if (!_contentFilterEngine) {
    _contentFilterEngine = new ContentFilterEngine();
  }
  return _contentFilterEngine;
};
