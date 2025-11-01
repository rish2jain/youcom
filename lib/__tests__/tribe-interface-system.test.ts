import { TribeInterfaceSystem } from "../tribe-interface-system";
import { TribeUser, UserRole, InterfaceMode } from "../types/tribe-interface";

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(global, "localStorage", {
  value: mockLocalStorage,
});

describe("TribeInterfaceSystem", () => {
  let system: TribeInterfaceSystem;

  beforeEach(() => {
    system = new TribeInterfaceSystem();
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
  });

  describe("Role Detection", () => {
    it("detects executive role from user attributes", () => {
      const user = {
        id: "user-1",
        email: "ceo@company.com",
        seniority: "c-level",
        department: "leadership",
      };

      const detectedRole = system.detectUserRole(user);
      expect(detectedRole).toBe("executive");
    });

    it("detects analyst role from department", () => {
      const user = {
        id: "user-2",
        email: "analyst@company.com",
        department: "strategy",
        seniority: "senior",
      };

      const detectedRole = system.detectUserRole(user);
      expect(detectedRole).toBe("analyst");
    });

    it("defaults to team role for unknown users", () => {
      const user = {
        id: "user-3",
        email: "user@company.com",
      };

      const detectedRole = system.detectUserRole(user);
      expect(detectedRole).toBe("team");
    });

    it("detects role from explicit role attribute", () => {
      const user = {
        id: "user-4",
        role: "analyst" as UserRole,
        email: "user@company.com",
      };

      const detectedRole = system.detectUserRole(user);
      expect(detectedRole).toBe("analyst");
    });
  });

  describe("Mode Suggestions", () => {
    it("suggests executive mode for executive role", () => {
      const suggestedMode = system.suggestMode("executive");
      expect(suggestedMode).toBe("executive");
    });

    it("suggests analyst mode for analyst role", () => {
      const suggestedMode = system.suggestMode("analyst");
      expect(suggestedMode).toBe("analyst");
    });

    it("suggests team mode for team role", () => {
      const suggestedMode = system.suggestMode("team");
      expect(suggestedMode).toBe("team");
    });
  });

  describe("Mode Switching", () => {
    it("switches interface mode", () => {
      system.switchMode("executive");

      const state = system.getState();
      expect(state.currentMode).toBe("executive");
      expect(state.lastModeSwitch).toBeInstanceOf(Date);
    });

    it("tracks mode history", () => {
      system.switchMode("executive");
      system.switchMode("analyst");
      system.switchMode("team");

      const state = system.getState();
      expect(state.modeHistory).toContain("analyst");
      expect(state.modeHistory).toContain("executive");
    });

    it("persists mode to localStorage", () => {
      system.switchMode("executive");

      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        "tribe_interface_mode",
        "executive"
      );
    });

    it("updates user preferences when user provided", () => {
      const user: TribeUser = {
        id: "user-1",
        role: "analyst",
        permissions: [],
        preferences: {
          defaultMode: "analyst",
          maxInsights: 5,
          showTechnicalDetails: true,
          enableCollaboration: true,
          summaryLevel: "medium",
          thresholds: {
            riskScore: 70,
            confidenceScore: 80,
            sourceCount: 10,
          },
          notifications: {
            email: true,
            inApp: true,
            slack: false,
            frequency: "immediate",
          },
        },
      };

      system.switchMode("executive", user);

      const state = system.getState();
      expect(state.user?.preferences.defaultMode).toBe("executive");
    });
  });

  describe("Mode Configuration", () => {
    it("returns correct configuration for executive mode", () => {
      system.switchMode("executive");
      const config = system.getCurrentModeConfig();

      expect(config.name).toBe("executive");
      expect(config.maxInsights).toBe(3);
      expect(config.showTechnicalDetails).toBe(false);
      expect(config.enableCollaboration).toBe(false);
      expect(config.features.apiMetrics).toBe(false);
    });

    it("returns correct configuration for analyst mode", () => {
      system.switchMode("analyst");
      const config = system.getCurrentModeConfig();

      expect(config.name).toBe("analyst");
      expect(config.maxInsights).toBe(8);
      expect(config.showTechnicalDetails).toBe(true);
      expect(config.enableCollaboration).toBe(true);
      expect(config.features.apiMetrics).toBe(true);
    });

    it("returns correct configuration for team mode", () => {
      system.switchMode("team");
      const config = system.getCurrentModeConfig();

      expect(config.name).toBe("team");
      expect(config.maxInsights).toBe(5);
      expect(config.showTechnicalDetails).toBe(false);
      expect(config.enableCollaboration).toBe(true);
      expect(config.features.annotations).toBe(true);
    });
  });

  describe("Feature Gating", () => {
    it("enables API metrics for analyst mode", () => {
      system.switchMode("analyst");
      expect(system.isFeatureEnabled("apiMetrics")).toBe(true);
    });

    it("disables API metrics for executive mode", () => {
      system.switchMode("executive");
      expect(system.isFeatureEnabled("apiMetrics")).toBe(false);
    });

    it("enables collaboration for team mode", () => {
      system.switchMode("team");
      expect(system.isFeatureEnabled("annotations")).toBe(true);
      expect(system.isFeatureEnabled("sharing")).toBe(true);
    });

    it("disables collaboration for executive mode", () => {
      system.switchMode("executive");
      expect(system.isFeatureEnabled("annotations")).toBe(false);
    });
  });

  describe("Content Adaptation", () => {
    const mockContent = {
      title: "Test Analysis",
      summary:
        "This is a comprehensive analysis using advanced ML algorithms and API integrations.",
      insights: [
        "Insight 1 with technical details",
        "Insight 2 about implementation",
        "Insight 3 regarding architecture",
        "Insight 4 about optimization",
        "Insight 5 concerning scalability",
      ],
      actions: [
        "Action 1: Implement new API",
        "Action 2: Optimize algorithm",
        "Action 3: Scale infrastructure",
      ],
      api_usage: {
        news: 3,
        search: 5,
        chat: 2,
        ari: 1,
      },
      confidence_score: 85,
    };

    it("adapts content for executive mode", () => {
      system.switchMode("executive");
      const adapted = system.adaptContent(mockContent);

      expect(adapted.insights.length).toBeLessThanOrEqual(3);
      expect(adapted.metadata.filteringApplied).toContain(
        "executive_simplification"
      );
      expect(adapted.summary).not.toContain("ML");
      expect(adapted.summary).toContain("machine learning");
    });

    it("preserves full content for analyst mode", () => {
      system.switchMode("analyst");
      const adapted = system.adaptContent(mockContent);

      expect(adapted.insights.length).toBe(mockContent.insights.length);
      expect(adapted.technicalDetails).toBeDefined();
      expect(adapted.technicalDetails.apiUsage).toEqual(mockContent.api_usage);
    });

    it("filters technical jargon for executive mode", () => {
      system.switchMode("executive");
      const adapted = system.adaptContent(mockContent);

      expect(adapted.summary).not.toContain("API");
      expect(adapted.summary).toContain("data connection");
      expect(adapted.metadata.filteringApplied).toContain(
        "technical_jargon_filtered"
      );
    });

    it("limits insights based on mode configuration", () => {
      system.switchMode("executive");
      const adapted = system.adaptContent(mockContent);

      expect(adapted.insights.length).toBeLessThanOrEqual(3);

      system.switchMode("analyst");
      const adaptedAnalyst = system.adaptContent(mockContent);

      expect(adaptedAnalyst.insights.length).toBeLessThanOrEqual(8);
    });

    it("calculates complexity correctly", () => {
      system.switchMode("executive");
      const adapted = system.adaptContent(mockContent);

      expect(adapted.metadata.originalComplexity).toBeGreaterThan(0);
      expect(adapted.metadata.adaptedComplexity).toBeLessThanOrEqual(
        adapted.metadata.originalComplexity
      );
    });

    it("tracks adaptation metrics", () => {
      system.switchMode("executive");
      system.adaptContent(mockContent);

      const state = system.getState();
      expect(state.adaptationMetrics.contentFiltered).toBe(1);
    });
  });

  describe("Content Filtering", () => {
    it("gets correct filter settings for executive mode", () => {
      system.switchMode("executive");
      const filter = system.getContentFilter();

      expect(filter.filterTechnicalJargon).toBe(true);
      expect(filter.prioritizeActions).toBe(true);
      expect(filter.hideImplementationDetails).toBe(true);
      expect(filter.summarizeEvidence).toBe(true);
      expect(filter.maxComplexity).toBe(10);
    });

    it("gets correct filter settings for analyst mode", () => {
      system.switchMode("analyst");
      const filter = system.getContentFilter();

      expect(filter.filterTechnicalJargon).toBe(false);
      expect(filter.prioritizeActions).toBe(false);
      expect(filter.hideImplementationDetails).toBe(false);
      expect(filter.summarizeEvidence).toBe(false);
      expect(filter.maxComplexity).toBe(25);
    });

    it("gets correct filter settings for team mode", () => {
      system.switchMode("team");
      const filter = system.getContentFilter();

      expect(filter.filterTechnicalJargon).toBe(true);
      expect(filter.prioritizeActions).toBe(false);
      expect(filter.hideImplementationDetails).toBe(true);
      expect(filter.summarizeEvidence).toBe(false);
      expect(filter.maxComplexity).toBe(15);
    });
  });

  describe("Initialization", () => {
    it("initializes with default state", () => {
      const state = system.getState();

      expect(state.currentMode).toBe("analyst");
      expect(state.detectedRole).toBeNull();
      expect(state.user).toBeNull();
      expect(state.modeHistory).toEqual([]);
    });

    it("loads saved mode from localStorage", () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === "tribe_interface_mode") return "executive";
        if (key === "tribe_mode_history")
          return JSON.stringify(["analyst", "executive"]);
        return null;
      });

      system.initialize();

      const state = system.getState();
      expect(state.currentMode).toBe("executive");
      expect(state.modeHistory).toEqual(["analyst", "executive"]);
    });

    it("initializes with user preferences", () => {
      const user: TribeUser = {
        id: "user-1",
        role: "executive",
        permissions: [],
        preferences: {
          defaultMode: "executive",
          maxInsights: 3,
          showTechnicalDetails: false,
          enableCollaboration: false,
          summaryLevel: "high",
          thresholds: {
            riskScore: 80,
            confidenceScore: 90,
            sourceCount: 5,
          },
          notifications: {
            email: true,
            inApp: true,
            slack: false,
            frequency: "immediate",
          },
        },
      };

      system.initialize(user);

      const state = system.getState();
      expect(state.user).toEqual(user);
      expect(state.detectedRole).toBe("executive");
      expect(state.currentMode).toBe("executive");
    });

    it("suggests mode based on detected role when no preference", () => {
      const user: TribeUser = {
        id: "user-1",
        role: "analyst",
        permissions: [],
        preferences: {
          defaultMode: "analyst", // This will be overridden by suggestion
          maxInsights: 5,
          showTechnicalDetails: true,
          enableCollaboration: true,
          summaryLevel: "medium",
          thresholds: {
            riskScore: 70,
            confidenceScore: 80,
            sourceCount: 10,
          },
          notifications: {
            email: true,
            inApp: true,
            slack: false,
            frequency: "immediate",
          },
        },
      };

      // Remove default mode to test suggestion
      delete (user.preferences as any).defaultMode;

      system.initialize(user);

      const state = system.getState();
      expect(state.currentMode).toBe("analyst"); // Should be suggested based on role
    });
  });

  describe("Satisfaction Tracking", () => {
    it("records user satisfaction", () => {
      const initialState = system.getState();
      const initialSatisfaction =
        initialState.adaptationMetrics.userSatisfaction;

      system.recordSatisfaction(4);

      const updatedState = system.getState();
      expect(updatedState.adaptationMetrics.userSatisfaction).toBeGreaterThan(
        initialSatisfaction
      );
    });

    it("calculates average satisfaction correctly", () => {
      system.recordSatisfaction(4);
      system.recordSatisfaction(5);

      const state = system.getState();
      expect(state.adaptationMetrics.userSatisfaction).toBe(4.5);
    });
  });

  describe("Error Handling", () => {
    it("handles localStorage errors gracefully", () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error("Storage quota exceeded");
      });

      expect(() => {
        system.switchMode("executive");
      }).not.toThrow();
    });

    it("handles invalid stored data gracefully", () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === "tribe_mode_history") return "invalid json";
        return null;
      });

      expect(() => {
        system.initialize();
      }).not.toThrow();
    });

    it("handles missing user data gracefully", () => {
      expect(() => {
        system.detectUserRole({});
      }).not.toThrow();

      const role = system.detectUserRole({});
      expect(role).toBe("team"); // Should default to team
    });
  });
});
