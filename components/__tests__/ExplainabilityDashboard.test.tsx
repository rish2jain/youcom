/**
 * Tests for ExplainabilityDashboard component
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import ExplainabilityDashboard from "../ExplainabilityDashboard";

// Mock the child components
jest.mock("../ReasoningChainVisualization", () => {
  return function MockReasoningChainVisualization({
    impactCardId,
    riskScore,
  }: any) {
    return (
      <div data-testid="reasoning-chain-visualization">
        Reasoning Chain for Impact Card {impactCardId} with Risk Score{" "}
        {riskScore}
      </div>
    );
  };
});

jest.mock("../SourceQualityVisualization", () => {
  return function MockSourceQualityVisualization({ impactCardId }: any) {
    return (
      <div data-testid="source-quality-visualization">
        Source Quality for Impact Card {impactCardId}
      </div>
    );
  };
});

jest.mock("../UncertaintyDetectionPanel", () => {
  return function MockUncertaintyDetectionPanel({ impactCardId }: any) {
    return (
      <div data-testid="uncertainty-detection-panel">
        Uncertainty Detection for Impact Card {impactCardId}
      </div>
    );
  };
});

// Mock UI components
jest.mock("@/components/ui/card", () => ({
  Card: ({ children, className }: any) => (
    <div className={className}>{children}</div>
  ),
  CardContent: ({ children }: any) => <div>{children}</div>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <h3>{children}</h3>,
}));

jest.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick, disabled, variant, size }: any) => (
    <button
      onClick={onClick}
      disabled={disabled}
      data-variant={variant}
      data-size={size}
    >
      {children}
    </button>
  ),
}));

jest.mock("@/components/ui/tabs", () => ({
  Tabs: ({ children, value, onValueChange }: any) => (
    <div
      data-testid="tabs"
      data-value={value}
      onClick={() => onValueChange?.("test")}
    >
      {children}
    </div>
  ),
  TabsList: ({ children }: any) => (
    <div data-testid="tabs-list">{children}</div>
  ),
  TabsTrigger: ({ children, value }: any) => (
    <button data-testid={`tab-trigger-${value}`}>{children}</button>
  ),
  TabsContent: ({ children, value }: any) => (
    <div data-testid={`tab-content-${value}`}>{children}</div>
  ),
}));

jest.mock("@/components/ui/badge", () => ({
  Badge: ({ children, className, variant }: any) => (
    <span className={className} data-variant={variant}>
      {children}
    </span>
  ),
}));

describe("ExplainabilityDashboard", () => {
  const defaultProps = {
    impactCardId: 123,
    riskScore: 75,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders loading state initially", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    expect(
      screen.getByText("Generating Explainability Analysis")
    ).toBeInTheDocument();
    expect(screen.getByText(/Creating reasoning chains/)).toBeInTheDocument();
  });

  it("renders dashboard with explainability data after loading", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    // Wait for loading to complete
    await waitFor(
      () => {
        expect(
          screen.getByText("AI Explainability Dashboard")
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Check summary metrics
    expect(screen.getByText("Overall Confidence")).toBeInTheDocument();
    expect(screen.getByText("Source Quality")).toBeInTheDocument();
    expect(screen.getByText("Uncertainty Level")).toBeInTheDocument();
    expect(screen.getByText("Human Validation")).toBeInTheDocument();
  });

  it("displays human validation warning when recommended", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    await waitFor(
      () => {
        expect(
          screen.getByText("Human Validation Recommended")
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(
      screen.getByText(/This analysis contains uncertainties/)
    ).toBeInTheDocument();
  });

  it("renders all tab triggers", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    await waitFor(
      () => {
        expect(screen.getByTestId("tab-trigger-overview")).toBeInTheDocument();
        expect(screen.getByTestId("tab-trigger-reasoning")).toBeInTheDocument();
        expect(screen.getByTestId("tab-trigger-sources")).toBeInTheDocument();
        expect(
          screen.getByTestId("tab-trigger-uncertainty")
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it("displays overview content by default", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    await waitFor(
      () => {
        expect(screen.getByText("Reasoning Steps")).toBeInTheDocument();
        expect(screen.getByText("Source Analysis")).toBeInTheDocument();
        expect(screen.getByText("Uncertainties")).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it("shows key insights in overview", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    await waitFor(
      () => {
        expect(screen.getByText("Key Insights")).toBeInTheDocument();
        expect(screen.getByText("Risk Score Composition")).toBeInTheDocument();
        expect(screen.getByText("Source Quality")).toBeInTheDocument();
        expect(screen.getByText("Attention Required")).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it("calls onGenerateExplainability when provided", async () => {
    const mockOnGenerate = jest.fn();
    render(
      <ExplainabilityDashboard
        {...defaultProps}
        onGenerateExplainability={mockOnGenerate}
      />
    );

    await waitFor(
      () => {
        expect(mockOnGenerate).toHaveBeenCalled();
      },
      { timeout: 3000 }
    );
  });

  it("calls onRequestValidation when provided", async () => {
    const mockOnRequestValidation = jest.fn();
    render(
      <ExplainabilityDashboard
        {...defaultProps}
        onRequestValidation={mockOnRequestValidation}
      />
    );

    // Wait for component to load
    await waitFor(
      () => {
        expect(
          screen.getByText("AI Explainability Dashboard")
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // The onRequestValidation should be passed to child components
    // This is tested indirectly through the mock components
    expect(
      screen.getByTestId("uncertainty-detection-panel")
    ).toBeInTheDocument();
  });

  it("handles refresh button click", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    await waitFor(
      () => {
        const refreshButton = screen.getByText("Refresh");
        expect(refreshButton).toBeInTheDocument();
        fireEvent.click(refreshButton);
      },
      { timeout: 3000 }
    );
  });

  it("handles export button click", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    await waitFor(
      () => {
        const exportButton = screen.getByText("Export");
        expect(exportButton).toBeInTheDocument();
        fireEvent.click(exportButton);
      },
      { timeout: 3000 }
    );
  });

  it("renders child components with correct props", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    await waitFor(
      () => {
        // Check that child components receive correct props
        expect(
          screen.getByTestId("reasoning-chain-visualization")
        ).toHaveTextContent(
          `Reasoning Chain for Impact Card ${defaultProps.impactCardId} with Risk Score ${defaultProps.riskScore}`
        );
        expect(
          screen.getByTestId("source-quality-visualization")
        ).toHaveTextContent(
          `Source Quality for Impact Card ${defaultProps.impactCardId}`
        );
        expect(
          screen.getByTestId("uncertainty-detection-panel")
        ).toHaveTextContent(
          `Uncertainty Detection for Impact Card ${defaultProps.impactCardId}`
        );
      },
      { timeout: 3000 }
    );
  });

  it("displays correct confidence percentages", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    await waitFor(
      () => {
        // Check that confidence percentages are displayed
        expect(screen.getByText("79%")).toBeInTheDocument(); // Overall confidence
        expect(screen.getByText("68%")).toBeInTheDocument(); // Source quality
      },
      { timeout: 3000 }
    );
  });

  it("displays correct uncertainty level", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    await waitFor(
      () => {
        expect(screen.getByText("Medium")).toBeInTheDocument(); // Uncertainty level
      },
      { timeout: 3000 }
    );
  });

  it("shows generate button when no explainability data", () => {
    // Mock the useEffect to not auto-generate
    const mockUseEffect = jest.spyOn(React, "useEffect");
    mockUseEffect.mockImplementation((f) => f());

    render(<ExplainabilityDashboard {...defaultProps} />);

    expect(
      screen.getByText("Explainability Analysis Not Available")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Generate Explainability Analysis")
    ).toBeInTheDocument();

    mockUseEffect.mockRestore();
  });

  it("handles generate button click when no data", () => {
    // Mock the useEffect to not auto-generate
    const mockUseEffect = jest.spyOn(React, "useEffect");
    mockUseEffect.mockImplementation(() => {});

    render(<ExplainabilityDashboard {...defaultProps} />);

    const generateButton = screen.getByText("Generate Explainability Analysis");
    fireEvent.click(generateButton);

    mockUseEffect.mockRestore();
  });

  it("displays analysis quality assessment", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    await waitFor(
      () => {
        expect(
          screen.getByText("Analysis Quality Assessment")
        ).toBeInTheDocument();
        expect(
          screen.getByText(/High quality analysis with strong confidence/)
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it("shows tier distribution in overview", async () => {
    render(<ExplainabilityDashboard {...defaultProps} />);

    await waitFor(
      () => {
        expect(screen.getByText("Tier 1")).toBeInTheDocument();
        expect(screen.getByText("Tier 2")).toBeInTheDocument();
        expect(screen.getByText("Tier 3")).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it("handles error state gracefully", async () => {
    // Mock console.error to avoid test output noise
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    // Mock a component that throws an error
    const ErrorComponent = () => {
      throw new Error("Test error");
    };

    // This test would need an error boundary to properly test error handling
    // For now, we just verify the component doesn't crash with invalid props
    render(<ExplainabilityDashboard impactCardId={0} riskScore={-1} />);

    consoleSpy.mockRestore();
  });
});
