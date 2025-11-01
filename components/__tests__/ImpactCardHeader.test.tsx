import { render, screen, fireEvent } from "@testing-library/react";
import ImpactCardHeader from "../ImpactCardHeader";

const mockCard = {
  id: 1,
  competitor_name: "OpenAI",
  risk_score: 85,
  risk_level: "high",
  confidence_score: 92,
  total_sources: 47,
  created_at: "2024-01-01T00:00:00Z",
  requires_review: false,
  key_insights: ["OpenAI announced GPT-4 Turbo with 128K context window"],
};

describe("ImpactCardHeader Component", () => {
  const defaultProps = {
    card: mockCard,
    onClick: jest.fn(),
    isSelected: false,
    viewMode: "detailed",
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders card header with basic information", () => {
    render(<ImpactCardHeader {...defaultProps} />);

    expect(screen.getByText("OpenAI")).toBeInTheDocument();
    expect(screen.getByText("HIGH RISK")).toBeInTheDocument();
    expect(screen.getByText("Score: 85/100")).toBeInTheDocument();
    expect(screen.getByText("Confidence: 92%")).toBeInTheDocument();
    expect(screen.getByText("47 sources")).toBeInTheDocument();
  });

  it("shows key insight in detailed mode", () => {
    render(<ImpactCardHeader {...defaultProps} />);

    expect(screen.getByText("Key Insight:")).toBeInTheDocument();
    expect(
      screen.getByText("OpenAI announced GPT-4 Turbo with 128K context window")
    ).toBeInTheDocument();
  });

  it("hides key insight in compact mode", () => {
    render(<ImpactCardHeader {...defaultProps} viewMode="compact" />);

    expect(screen.queryByText("Key Insight:")).not.toBeInTheDocument();
  });

  it("shows technical metrics in technical mode", () => {
    render(<ImpactCardHeader {...defaultProps} viewMode="technical" />);

    expect(screen.getByText("Risk Score")).toBeInTheDocument();
    expect(screen.getByText("Confidence")).toBeInTheDocument();
    expect(screen.getByText("Sources")).toBeInTheDocument();
  });

  it("shows review required badge when needed", () => {
    const cardWithReview = { ...mockCard, requires_review: true };
    render(<ImpactCardHeader {...defaultProps} card={cardWithReview} />);

    expect(screen.getByText("Analyst review requested")).toBeInTheDocument();
  });

  it("handles click events", () => {
    const onClick = jest.fn();
    render(<ImpactCardHeader {...defaultProps} onClick={onClick} />);

    fireEvent.click(screen.getByText("OpenAI"));
    expect(onClick).toHaveBeenCalled();
  });

  it("shows selected state styling", () => {
    const { container } = render(
      <ImpactCardHeader {...defaultProps} isSelected={true} />
    );

    expect(container.firstChild).toHaveClass("border-blue-500", "bg-blue-50");
    expect(screen.getByText("Expanded")).toBeInTheDocument();
  });

  it("displays correct risk colors for different levels", () => {
    const criticalCard = { ...mockCard, risk_level: "critical" };
    render(<ImpactCardHeader {...defaultProps} card={criticalCard} />);

    expect(screen.getByText("CRITICAL RISK")).toHaveClass(
      "text-red-600",
      "bg-red-100"
    );
  });

  it("formats timestamp correctly", () => {
    render(<ImpactCardHeader {...defaultProps} />);

    // Should show formatted date (the actual output shows 12/31/2023, 7:00:00 PM)
    expect(screen.getByText(/12\/31\/2023/)).toBeInTheDocument();
  });

  it("shows multiple insights indicator in technical mode", () => {
    const cardWithMultipleInsights = {
      ...mockCard,
      key_insights: ["Insight 1", "Insight 2", "Insight 3"],
    };
    render(
      <ImpactCardHeader
        {...defaultProps}
        card={cardWithMultipleInsights}
        viewMode="technical"
      />
    );

    expect(screen.getByText("+2 more insights")).toBeInTheDocument();
  });

  it("handles missing or invalid timestamps", () => {
    const cardWithInvalidDate = { ...mockCard, created_at: "invalid-date" };
    render(<ImpactCardHeader {...defaultProps} card={cardWithInvalidDate} />);

    expect(screen.getByText("Invalid Date")).toBeInTheDocument();
  });
});
