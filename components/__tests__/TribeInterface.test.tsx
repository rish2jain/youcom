import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { TribeInterfaceProvider } from "../TribeInterfaceProvider";
import {
  TribeInterface,
  AdaptiveContent,
  FeatureGate,
  ExecutiveCard,
  AnalystCard,
  TeamCard,
} from "../TribeInterface";
import { TribeModeSelector } from "../TribeModeSelector";
import { TribeUser } from "@/lib/types/tribe-interface";

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, "localStorage", {
  value: mockLocalStorage,
});

// Mock sessionStorage
const mockSessionStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, "sessionStorage", {
  value: mockSessionStorage,
});

// Test user data
const mockExecutiveUser: TribeUser = {
  id: "exec-1",
  role: "executive",
  permissions: ["view", "share"],
  department: "leadership",
  seniority: "c-level",
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

const mockAnalystUser: TribeUser = {
  id: "analyst-1",
  role: "analyst",
  permissions: ["view", "edit", "analyze"],
  department: "strategy",
  seniority: "senior",
  preferences: {
    defaultMode: "analyst",
    maxInsights: 8,
    showTechnicalDetails: true,
    enableCollaboration: true,
    summaryLevel: "detailed",
    thresholds: {
      riskScore: 60,
      confidenceScore: 75,
      sourceCount: 10,
    },
    notifications: {
      email: true,
      inApp: true,
      slack: true,
      frequency: "hourly",
    },
  },
};

const mockContent = {
  title: "OpenAI Competitive Analysis",
  summary:
    "OpenAI has released GPT-5 with advanced reasoning capabilities and multimodal features.",
  insights: [
    "GPT-5 shows significant improvements in mathematical reasoning",
    "New multimodal capabilities enable image and video processing",
    "API pricing has been reduced by 50% to increase adoption",
    "Enterprise features include fine-tuning and custom models",
    "Safety measures have been enhanced with constitutional AI",
  ],
  actions: [
    "Evaluate our AI strategy against GPT-5 capabilities",
    "Assess pricing impact on our competitive position",
    "Review our multimodal roadmap timeline",
    "Consider partnership opportunities with OpenAI",
  ],
  api_usage: {
    news: 3,
    search: 5,
    chat: 2,
    ari: 1,
  },
  confidence_score: 85,
  risk_score: 92,
  total_sources: 25,
};

describe("TribeInterface System", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
    mockSessionStorage.getItem.mockReturnValue(null);
  });

  describe("TribeInterfaceProvider", () => {
    it("initializes with default analyst mode", () => {
      render(
        <TribeInterfaceProvider>
          <div data-testid="test-content">Test Content</div>
        </TribeInterfaceProvider>
      );

      expect(screen.getByTestId("test-content")).toBeInTheDocument();
    });

    it("initializes with user preferences", () => {
      render(
        <TribeInterfaceProvider user={mockExecutiveUser}>
          <TribeModeSelector compact />
        </TribeInterfaceProvider>
      );

      expect(screen.getByText("Executive")).toBeInTheDocument();
    });

    it("persists mode changes to localStorage", async () => {
      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <TribeModeSelector compact />
        </TribeInterfaceProvider>
      );

      // Click to open dropdown
      fireEvent.click(screen.getByText("Analyst"));

      // Switch to executive mode
      fireEvent.click(screen.getByText("Executive"));

      await waitFor(() => {
        expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
          "tribe_interface_mode",
          "executive"
        );
      });
    });
  });

  describe("TribeModeSelector", () => {
    it("renders compact mode selector", () => {
      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <TribeModeSelector compact />
        </TribeInterfaceProvider>
      );

      expect(screen.getByText("Analyst")).toBeInTheDocument();
    });

    it("shows mode descriptions in full mode", () => {
      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <TribeModeSelector compact={false} />
        </TribeInterfaceProvider>
      );

      expect(screen.getByText("Interface Mode")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Detailed analysis with full technical depth and evidence"
        )
      ).toBeInTheDocument();
    });

    it("suggests appropriate mode for user role", () => {
      render(
        <TribeInterfaceProvider user={mockExecutiveUser}>
          <TribeModeSelector compact={false} />
        </TribeInterfaceProvider>
      );

      // Should show executive mode as active since user is executive
      expect(screen.getByText("Active")).toBeInTheDocument();
    });

    it("handles mode switching", async () => {
      const onModeChange = jest.fn();

      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <TribeModeSelector compact={false} onModeChange={onModeChange} />
        </TribeInterfaceProvider>
      );

      // Click on executive mode
      const executiveButton = screen.getByText("Executive").closest("button");
      fireEvent.click(executiveButton!);

      await waitFor(() => {
        expect(onModeChange).toHaveBeenCalledWith("executive");
      });
    });
  });

  describe("AdaptiveContent", () => {
    it("adapts content for executive mode", () => {
      render(
        <TribeInterfaceProvider user={mockExecutiveUser}>
          <AdaptiveContent content={mockContent} />
        </TribeInterfaceProvider>
      );

      // Should show simplified content
      expect(
        screen.getByText("OpenAI Competitive Analysis")
      ).toBeInTheDocument();

      // Should limit insights for executive mode (max 3)
      const insights = screen.getAllByText(/GPT-5|multimodal|API pricing/);
      expect(insights.length).toBeLessThanOrEqual(3);
    });

    it("shows full content for analyst mode", () => {
      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <AdaptiveContent content={mockContent} />
        </TribeInterfaceProvider>
      );

      // Should show more detailed content
      expect(screen.getByText("Key Insights")).toBeInTheDocument();
      expect(screen.getByText("Recommended Actions")).toBeInTheDocument();
    });

    it("filters technical jargon for executive mode", () => {
      const technicalContent = {
        ...mockContent,
        summary:
          "OpenAI has deployed a new ML model with advanced API capabilities and neural network architecture.",
      };

      render(
        <TribeInterfaceProvider user={mockExecutiveUser}>
          <AdaptiveContent content={technicalContent} />
        </TribeInterfaceProvider>
      );

      // Technical terms should be simplified
      const summary = screen.getByText(/machine learning.*data connection/);
      expect(summary).toBeInTheDocument();
    });
  });

  describe("FeatureGate", () => {
    it("shows content when feature is enabled", () => {
      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <FeatureGate feature="apiMetrics">
            <div data-testid="gated-content">API Metrics Content</div>
          </FeatureGate>
        </TribeInterfaceProvider>
      );

      expect(screen.getByTestId("gated-content")).toBeInTheDocument();
    });

    it("hides content when feature is disabled", () => {
      render(
        <TribeInterfaceProvider user={mockExecutiveUser}>
          <FeatureGate feature="apiMetrics">
            <div data-testid="gated-content">API Metrics Content</div>
          </FeatureGate>
        </TribeInterfaceProvider>
      );

      expect(screen.queryByTestId("gated-content")).not.toBeInTheDocument();
    });

    it("shows fallback when feature is disabled", () => {
      render(
        <TribeInterfaceProvider user={mockExecutiveUser}>
          <FeatureGate
            feature="apiMetrics"
            fallback={<div data-testid="fallback">Simplified View</div>}
          >
            <div data-testid="gated-content">API Metrics Content</div>
          </FeatureGate>
        </TribeInterfaceProvider>
      );

      expect(screen.queryByTestId("gated-content")).not.toBeInTheDocument();
      expect(screen.getByTestId("fallback")).toBeInTheDocument();
    });
  });

  describe("ExecutiveCard", () => {
    it("renders executive-focused card", () => {
      render(
        <ExecutiveCard
          title="OpenAI Threat"
          riskScore={92}
          actions={["Evaluate AI strategy", "Assess pricing impact"]}
          insight="GPT-5 poses significant competitive threat"
        />
      );

      expect(screen.getByText("OpenAI Threat")).toBeInTheDocument();
      expect(screen.getByText("Risk: 92/100")).toBeInTheDocument();
      expect(
        screen.getByText("GPT-5 poses significant competitive threat")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Immediate Actions Required")
      ).toBeInTheDocument();
    });

    it("limits actions to top 3", () => {
      const manyActions = [
        "Action 1",
        "Action 2",
        "Action 3",
        "Action 4",
        "Action 5",
      ];

      render(
        <ExecutiveCard
          title="Test"
          riskScore={80}
          actions={manyActions}
          insight="Test insight"
        />
      );

      // Should only show first 3 actions
      expect(screen.getByText("Action 1")).toBeInTheDocument();
      expect(screen.getByText("Action 2")).toBeInTheDocument();
      expect(screen.getByText("Action 3")).toBeInTheDocument();
      expect(screen.queryByText("Action 4")).not.toBeInTheDocument();
    });

    it("applies correct risk color coding", () => {
      const { rerender } = render(
        <ExecutiveCard
          title="High Risk"
          riskScore={95}
          actions={["Action"]}
          insight="High risk insight"
        />
      );

      // High risk should have red styling
      expect(screen.getByText("Risk: 95/100")).toHaveClass("text-red-600");

      rerender(
        <ExecutiveCard
          title="Low Risk"
          riskScore={30}
          actions={["Action"]}
          insight="Low risk insight"
        />
      );

      // Low risk should have green styling
      expect(screen.getByText("Risk: 30/100")).toHaveClass("text-green-600");
    });
  });

  describe("AnalystCard", () => {
    it("renders analyst-focused card with technical details", () => {
      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <AnalystCard data={mockContent} showTechnicalDetails />
        </TribeInterfaceProvider>
      );

      expect(
        screen.getByText("OpenAI Competitive Analysis")
      ).toBeInTheDocument();
      expect(screen.getByText("Confidence: 85%")).toBeInTheDocument();
      expect(screen.getByText("25 sources")).toBeInTheDocument();
    });

    it("shows technical metrics when enabled", () => {
      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <AnalystCard data={mockContent} showTechnicalDetails />
        </TribeInterfaceProvider>
      );

      expect(screen.getByText("Technical Metrics")).toBeInTheDocument();
      expect(screen.getByText("News API")).toBeInTheDocument();
      expect(screen.getByText("Search API")).toBeInTheDocument();
    });

    it("hides technical metrics when disabled", () => {
      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <AnalystCard data={mockContent} showTechnicalDetails={false} />
        </TribeInterfaceProvider>
      );

      expect(screen.queryByText("Technical Metrics")).not.toBeInTheDocument();
    });
  });

  describe("TeamCard", () => {
    it("renders team-focused card with collaboration features", () => {
      const onAnnotate = jest.fn();
      const onShare = jest.fn();

      render(
        <TribeInterfaceProvider user={{ ...mockAnalystUser, role: "team" }}>
          <TeamCard
            data={mockContent}
            onAnnotate={onAnnotate}
            onShare={onShare}
          />
        </TribeInterfaceProvider>
      );

      expect(
        screen.getByText("OpenAI Competitive Analysis")
      ).toBeInTheDocument();
      expect(screen.getByText("Add Note")).toBeInTheDocument();
      expect(screen.getByText("Share")).toBeInTheDocument();
    });

    it("handles annotation and sharing actions", () => {
      const onAnnotate = jest.fn();
      const onShare = jest.fn();

      render(
        <TribeInterfaceProvider user={{ ...mockAnalystUser, role: "team" }}>
          <TeamCard
            data={mockContent}
            onAnnotate={onAnnotate}
            onShare={onShare}
          />
        </TribeInterfaceProvider>
      );

      fireEvent.click(screen.getByText("Add Note"));
      expect(onAnnotate).toHaveBeenCalled();

      fireEvent.click(screen.getByText("Share"));
      expect(onShare).toHaveBeenCalled();
    });

    it("shows collaboration guidance", () => {
      render(
        <TribeInterfaceProvider user={{ ...mockAnalystUser, role: "team" }}>
          <TeamCard data={mockContent} />
        </TribeInterfaceProvider>
      );

      expect(
        screen.getByText(/Team collaboration enabled/)
      ).toBeInTheDocument();
    });
  });

  describe("Content Adaptation", () => {
    it("reduces complexity for executive mode", () => {
      render(
        <TribeInterfaceProvider user={mockExecutiveUser}>
          <TribeInterface content={mockContent} showCognitiveLoad>
            <AdaptiveContent content={mockContent} />
          </TribeInterface>
        </TribeInterfaceProvider>
      );

      // Should show cognitive load indicator
      expect(screen.getByText(/Complexity:/)).toBeInTheDocument();

      // Should show adaptation notice
      expect(
        screen.getByText(/Content adapted for executive mode/)
      ).toBeInTheDocument();
    });

    it("preserves full content for analyst mode", () => {
      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <TribeInterface content={mockContent}>
            <AdaptiveContent content={mockContent} />
          </TribeInterface>
        </TribeInterfaceProvider>
      );

      // Should show interface optimized message
      expect(
        screen.getByText(/Interface optimized for analyst users/)
      ).toBeInTheDocument();
    });

    it("tracks adaptation metrics", () => {
      render(
        <TribeInterfaceProvider user={mockExecutiveUser}>
          <TribeInterface content={mockContent}>
            <AdaptiveContent content={mockContent} />
          </TribeInterface>
        </TribeInterfaceProvider>
      );

      // Should show that content has been adapted
      expect(screen.getByText(/items adapted/)).toBeInTheDocument();
    });
  });

  describe("Mode Persistence", () => {
    it("loads saved mode from localStorage", () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === "tribe_interface_mode") {
          return JSON.stringify({
            mode: "executive",
            timestamp: new Date().toISOString(),
          });
        }
        return null;
      });

      render(
        <TribeInterfaceProvider>
          <TribeModeSelector compact />
        </TribeInterfaceProvider>
      );

      expect(screen.getByText("Executive")).toBeInTheDocument();
    });

    it("saves mode changes to localStorage", async () => {
      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <TribeModeSelector compact />
        </TribeInterfaceProvider>
      );

      // Open dropdown and switch mode
      fireEvent.click(screen.getByText("Analyst"));
      fireEvent.click(screen.getByText("Executive"));

      await waitFor(() => {
        expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
          "tribe_interface_mode",
          "executive"
        );
      });
    });

    it("tracks mode switching history", async () => {
      render(
        <TribeInterfaceProvider user={mockAnalystUser}>
          <TribeModeSelector compact />
        </TribeInterfaceProvider>
      );

      // Switch modes multiple times
      fireEvent.click(screen.getByText("Analyst"));
      fireEvent.click(screen.getByText("Executive"));

      await waitFor(() => {
        expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
          expect.stringContaining("tribe_mode_history"),
          expect.any(String)
        );
      });
    });
  });
});
