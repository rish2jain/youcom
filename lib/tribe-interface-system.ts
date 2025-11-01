import {
  TribeUser,
  UserRole,
  InterfaceMode,
  InterfaceModeConfig,
  ContentFilter,
  AdaptedContent,
  TribeInterfaceState,
} from "./types/tribe-interface";

/**
 * Tribe Interface System - Core logic for role-based UI adaptation
 */
export class TribeInterfaceSystem {
  private state: TribeInterfaceState;
  private modeConfigs: Record<InterfaceMode, InterfaceModeConfig>;

  constructor() {
    this.state = {
      currentMode: "analyst",
      detectedRole: null,
      user: null,
      modeHistory: [],
      lastModeSwitch: null,
      adaptationMetrics: {
        contentFiltered: 0,
        complexityReduced: 0,
        userSatisfaction: 0,
      },
    };

    this.modeConfigs = {
      executive: {
        name: "executive",
        maxInsights: 3,
        showTechnicalDetails: false,
        enableCollaboration: false,
        summaryLevel: "high",
        cognitiveLoadLimit: 10,
        features: {
          apiMetrics: false,
          sourceBreakdown: false,
          explainability: false,
          annotations: false,
          sharing: true,
          advancedFilters: false,
        },
      },
      analyst: {
        name: "analyst",
        maxInsights: 8,
        showTechnicalDetails: true,
        enableCollaboration: true,
        summaryLevel: "detailed",
        cognitiveLoadLimit: 25,
        features: {
          apiMetrics: true,
          sourceBreakdown: true,
          explainability: true,
          annotations: true,
          sharing: true,
          advancedFilters: true,
        },
      },
      team: {
        name: "team",
        maxInsights: 5,
        showTechnicalDetails: false,
        enableCollaboration: true,
        summaryLevel: "medium",
        cognitiveLoadLimit: 15,
        features: {
          apiMetrics: false,
          sourceBreakdown: true,
          explainability: false,
          annotations: true,
          sharing: true,
          advancedFilters: false,
        },
      },
    };
  }

  /**
   * Detect user role from authentication and context
   */
  detectUserRole(user: any): UserRole {
    // Role detection logic based on user attributes
    if (user.role) {
      return user.role as UserRole;
    }

    // Fallback detection based on email domain, department, or seniority
    if (
      user.email?.includes("ceo") ||
      user.email?.includes("cto") ||
      user.seniority === "c-level"
    ) {
      return "executive";
    }

    if (
      user.department === "strategy" ||
      user.department === "product" ||
      user.seniority === "director"
    ) {
      return "analyst";
    }

    return "team";
  }

  /**
   * Get suggested interface mode based on user role
   */
  suggestMode(role: UserRole): InterfaceMode {
    const suggestions: Record<UserRole, InterfaceMode> = {
      executive: "executive",
      analyst: "analyst",
      team: "team",
    };

    return suggestions[role] || "analyst";
  }

  /**
   * Switch interface mode
   */
  switchMode(mode: InterfaceMode, user?: TribeUser): void {
    const previousMode = this.state.currentMode;

    this.state.currentMode = mode;
    this.state.modeHistory.push(previousMode);
    this.state.lastModeSwitch = new Date();

    // Update user preferences if user is provided
    if (user) {
      user.preferences.defaultMode = mode;
      this.state.user = user;
    }

    // Persist mode preference
    if (typeof window !== "undefined") {
      localStorage.setItem("tribe_interface_mode", mode);
      localStorage.setItem(
        "tribe_mode_history",
        JSON.stringify(this.state.modeHistory.slice(-10))
      );
    }
  }

  /**
   * Get current mode configuration
   */
  getCurrentModeConfig(): InterfaceModeConfig {
    return this.modeConfigs[this.state.currentMode];
  }

  /**
   * Get mode configuration by name
   */
  getModeConfig(mode: InterfaceMode): InterfaceModeConfig {
    return this.modeConfigs[mode];
  }

  /**
   * Check if feature is enabled for current mode
   */
  isFeatureEnabled(feature: keyof InterfaceModeConfig["features"]): boolean {
    return this.getCurrentModeConfig().features[feature];
  }

  /**
   * Get content filter settings for current mode
   */
  getContentFilter(): ContentFilter {
    const config = this.getCurrentModeConfig();

    return {
      filterTechnicalJargon: !config.showTechnicalDetails,
      maxComplexity: config.cognitiveLoadLimit,
      prioritizeActions: config.name === "executive",
      hideImplementationDetails: config.name !== "analyst",
      summarizeEvidence: config.summaryLevel === "high",
    };
  }

  /**
   * Adapt content based on current mode and user preferences
   */
  adaptContent(content: any): AdaptedContent {
    const config = this.getCurrentModeConfig();
    const filter = this.getContentFilter();
    const originalComplexity = this.calculateComplexity(content);

    let adaptedContent: AdaptedContent = {
      title: content.title || "",
      summary: content.summary || "",
      insights: content.insights || [],
      actions: content.actions || [],
      metadata: {
        originalComplexity,
        adaptedComplexity: originalComplexity,
        filteringApplied: [],
      },
    };

    // Apply mode-specific adaptations
    if (config.name === "executive") {
      adaptedContent = this.adaptForExecutive(adaptedContent, content);
    } else if (config.name === "analyst") {
      adaptedContent = this.adaptForAnalyst(adaptedContent, content);
    } else if (config.name === "team") {
      adaptedContent = this.adaptForTeam(adaptedContent, content);
    }

    // Apply content filtering
    if (filter.filterTechnicalJargon) {
      adaptedContent = this.filterTechnicalJargon(adaptedContent);
    }

    // Limit insights based on mode
    if (adaptedContent.insights.length > config.maxInsights) {
      adaptedContent.insights = adaptedContent.insights.slice(
        0,
        config.maxInsights
      );
      adaptedContent.metadata.filteringApplied.push("insights_limited");
    }

    // Calculate final complexity
    adaptedContent.metadata.adaptedComplexity =
      this.calculateComplexity(adaptedContent);

    // Update metrics
    this.state.adaptationMetrics.contentFiltered++;
    if (adaptedContent.metadata.adaptedComplexity < originalComplexity) {
      this.state.adaptationMetrics.complexityReduced++;
    }

    return adaptedContent;
  }

  /**
   * Adapt content for Executive mode
   */
  private adaptForExecutive(
    adaptedContent: AdaptedContent,
    originalContent: any
  ): AdaptedContent {
    // Simplify language and focus on business impact
    adaptedContent.summary = this.simplifyLanguage(adaptedContent.summary);

    // Prioritize actions over insights
    if (originalContent.recommendedActions) {
      adaptedContent.actions = originalContent.recommendedActions
        .slice(0, 3)
        .map((action: any) => this.simplifyLanguage(action.action || action));
    }

    // Limit to top 3 most critical insights
    adaptedContent.insights = adaptedContent.insights
      .slice(0, 3)
      .map((insight) => this.simplifyLanguage(insight));

    adaptedContent.metadata.filteringApplied.push("executive_simplification");
    return adaptedContent;
  }

  /**
   * Adapt content for Analyst mode
   */
  private adaptForAnalyst(
    adaptedContent: AdaptedContent,
    originalContent: any
  ): AdaptedContent {
    // Include technical details and full context
    adaptedContent.technicalDetails = {
      apiUsage: originalContent.api_usage,
      sourceBreakdown: originalContent.source_breakdown,
      explainability: originalContent.explainability,
      confidence: originalContent.confidence_score,
    };

    // Include all available insights and actions
    if (originalContent.key_insights) {
      adaptedContent.insights = originalContent.key_insights;
    }

    if (originalContent.recommendedActions || originalContent.next_steps_plan) {
      adaptedContent.actions = (
        originalContent.recommendedActions || originalContent.next_steps_plan
      ).map((action: any) => action.action || action);
    }

    adaptedContent.metadata.filteringApplied.push("analyst_enhancement");
    return adaptedContent;
  }

  /**
   * Adapt content for Team mode
   */
  private adaptForTeam(
    adaptedContent: AdaptedContent,
    originalContent: any
  ): AdaptedContent {
    // Focus on collaborative aspects and actionable insights
    adaptedContent.summary = this.addCollaborativeContext(
      adaptedContent.summary
    );

    // Include moderate level of detail
    if (originalContent.impact_areas) {
      adaptedContent.insights = originalContent.impact_areas
        .slice(0, 5)
        .map((area: any) => `${area.area}: ${area.description}`);
    }

    // Focus on team-actionable items
    if (originalContent.recommendedActions) {
      adaptedContent.actions = originalContent.recommendedActions
        .filter((action: any) => action.owner !== "Executive Team")
        .slice(0, 4)
        .map((action: any) => action.action || action);
    }

    adaptedContent.metadata.filteringApplied.push("team_collaboration");
    return adaptedContent;
  }

  /**
   * Filter technical jargon from content
   */
  private filterTechnicalJargon(content: AdaptedContent): AdaptedContent {
    const technicalTerms = [
      "API",
      "REST",
      "JSON",
      "HTTP",
      "SQL",
      "NoSQL",
      "ML",
      "AI model",
      "algorithm",
      "neural network",
      "regression",
      "clustering",
      "microservices",
      "containerization",
      "Kubernetes",
      "Docker",
    ];

    const replacements: Record<string, string> = {
      API: "data connection",
      ML: "machine learning",
      "AI model": "artificial intelligence system",
      algorithm: "automated process",
      "neural network": "AI system",
      microservices: "system components",
      containerization: "deployment method",
    };

    content.summary = this.replaceTerms(content.summary, replacements);
    content.insights = content.insights.map((insight) =>
      this.replaceTerms(insight, replacements)
    );
    content.actions = content.actions.map((action) =>
      this.replaceTerms(action, replacements)
    );

    content.metadata.filteringApplied.push("technical_jargon_filtered");
    return content;
  }

  /**
   * Simplify language for executive consumption
   */
  private simplifyLanguage(text: string): string {
    // Remove complex sentences and technical details
    return text
      .replace(/\b(implementation|infrastructure|architecture)\b/gi, "system")
      .replace(/\b(optimization|enhancement)\b/gi, "improvement")
      .replace(/\b(utilize|leverage)\b/gi, "use")
      .replace(/\b(facilitate|enable)\b/gi, "help")
      .replace(/\b(comprehensive|extensive)\b/gi, "complete");
  }

  /**
   * Add collaborative context to content
   */
  private addCollaborativeContext(text: string): string {
    if (!text.includes("team") && !text.includes("collaborate")) {
      return `${text} This requires team coordination and shared decision-making.`;
    }
    return text;
  }

  /**
   * Replace technical terms with simpler alternatives
   */
  private replaceTerms(
    text: string,
    replacements: Record<string, string>
  ): string {
    let result = text;
    Object.entries(replacements).forEach(([term, replacement]) => {
      const regex = new RegExp(`\\b${term}\\b`, "gi");
      result = result.replace(regex, replacement);
    });
    return result;
  }

  /**
   * Calculate content complexity score
   */
  private calculateComplexity(content: any): number {
    let complexity = 0;

    // Base complexity from content length
    const textLength =
      (content.summary || "").length +
      (content.insights || []).join(" ").length +
      (content.actions || []).join(" ").length;
    complexity += Math.floor(textLength / 100);

    // Add complexity for technical details
    if (content.technicalDetails) {
      complexity += 5;
    }

    // Add complexity for number of insights/actions
    complexity += (content.insights || []).length;
    complexity += (content.actions || []).length;

    return complexity;
  }

  /**
   * Get current state
   */
  getState(): TribeInterfaceState {
    return { ...this.state };
  }

  /**
   * Initialize from stored preferences
   */
  initialize(user?: TribeUser): void {
    if (typeof window !== "undefined") {
      const storedMode = localStorage.getItem(
        "tribe_interface_mode"
      ) as InterfaceMode;
      const storedHistory = localStorage.getItem("tribe_mode_history");

      if (storedMode && this.modeConfigs[storedMode]) {
        this.state.currentMode = storedMode;
      }

      if (storedHistory) {
        try {
          this.state.modeHistory = JSON.parse(storedHistory);
        } catch (e) {
          console.warn("Failed to parse mode history:", e);
        }
      }
    }

    if (user) {
      this.state.user = user;
      this.state.detectedRole = this.detectUserRole(user);

      // Use user's preferred mode if available
      if (user.preferences.defaultMode) {
        this.state.currentMode = user.preferences.defaultMode;
      } else {
        // Suggest mode based on detected role
        const suggestedMode = this.suggestMode(this.state.detectedRole);
        this.state.currentMode = suggestedMode;
      }
    }
  }

  /**
   * Record user satisfaction feedback
   */
  recordSatisfaction(rating: number): void {
    this.state.adaptationMetrics.userSatisfaction =
      (this.state.adaptationMetrics.userSatisfaction + rating) / 2;
  }
}

// Singleton instance - lazy initialization to avoid circular dependencies
let _tribeInterfaceSystem: TribeInterfaceSystem | null = null;
export const tribeInterfaceSystem = () => {
  if (!_tribeInterfaceSystem) {
    _tribeInterfaceSystem = new TribeInterfaceSystem();
  }
  return _tribeInterfaceSystem;
};
