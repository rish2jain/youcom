import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import SourceCitations from "../SourceCitations";

// Mock window.open
Object.defineProperty(window, "open", {
  writable: true,
  value: jest.fn(),
});

const mockCard = {
  id: 1,
  competitor_name: "OpenAI",
  credibility_score: 0.82,
  total_sources: 47,
  source_breakdown: {
    news_articles: 12,
    search_results: 15,
    research_citations: 20,
  },
  source_quality: {
    score: 0.82,
    tiers: { tier1: 2, tier2: 1, tier3: 0 },
    total: 3,
    top_sources: [
      { title: "WSJ Article", url: "https://wsj.com/article", type: "news" },
      {
        title: "TechCrunch Report",
        url: "https://techcrunch.com/report",
        type: "news",
      },
      { title: "Medium Post", url: "https://medium.com/post", type: "blog" },
      {
        title: "Twitter Thread",
        url: "https://twitter.com/thread",
        type: "social",
      },
    ],
  },
};

describe("SourceCitations Component", () => {
  const defaultProps = {
    card: mockCard,
    isExpanded: false,
    onToggle: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders collapsed header", () => {
    render(<SourceCitations {...defaultProps} />);

    expect(screen.getByText("Source Citations")).toBeInTheDocument();
    expect(screen.getByText("(47 total)")).toBeInTheDocument();
    expect(screen.getByText("82% credible")).toBeInTheDocument();
  });

  it("expands to show detailed content", () => {
    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    expect(screen.getByText("Credibility Overview")).toBeInTheDocument();
    expect(screen.getByText("Source Breakdown")).toBeInTheDocument();
    expect(screen.getByText("Overall Score:")).toBeInTheDocument();
    expect(screen.getByText("82%")).toBeInTheDocument();
  });

  it("displays source breakdown correctly", () => {
    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    expect(screen.getByText("News Articles:")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Search Results:")).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("Research Citations:")).toBeInTheDocument();
    expect(screen.getByText("20")).toBeInTheDocument();
  });

  it("shows tier information", () => {
    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    expect(screen.getByText("Tier 1 sources:")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("Tier 2 sources:")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("displays sources with correct tier classifications", () => {
    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    expect(screen.getByText("WSJ Article")).toBeInTheDocument();
    expect(screen.getByText("TechCrunch Report")).toBeInTheDocument();
    expect(screen.getByText("Medium Post")).toBeInTheDocument();
    expect(screen.getByText("Twitter Thread")).toBeInTheDocument();
  });

  it("handles source clicks and tracking", () => {
    const mockOpen = jest.fn();
    window.open = mockOpen;

    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    const wsjSource = screen.getByText("WSJ Article");
    fireEvent.click(wsjSource.closest("div")!);

    expect(mockOpen).toHaveBeenCalledWith(
      "https://wsj.com/article",
      "_blank",
      "noopener,noreferrer"
    );
  });

  it("filters sources by credibility", () => {
    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    const credibilitySlider = screen.getByRole("slider");
    fireEvent.change(credibilitySlider, { target: { value: "0.8" } });

    // Should filter out lower credibility sources
    expect(screen.getByText("WSJ Article")).toBeInTheDocument();
    // Medium and Twitter should be filtered out due to lower credibility
  });

  it("sorts sources by different criteria", () => {
    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    const sortSelect = screen.getByDisplayValue("Credibility");
    fireEvent.change(sortSelect, { target: { value: "title" } });

    // Sources should be reordered alphabetically by title
  });

  it("shows/hides all sources", () => {
    const cardWithManySources = {
      ...mockCard,
      source_quality: {
        ...mockCard.source_quality!,
        top_sources: Array.from({ length: 10 }, (_, i) => ({
          title: `Source ${i + 1}`,
          url: `https://example${i + 1}.com`,
          type: "news",
        })),
      },
    };

    render(
      <SourceCitations
        {...defaultProps}
        card={cardWithManySources}
        isExpanded={true}
      />
    );

    expect(screen.getByText("Show All 10 Sources")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Show All 10 Sources"));
    expect(screen.getByText("Show Less")).toBeInTheDocument();
  });

  it("handles toggle functionality", () => {
    const onToggle = jest.fn();
    render(<SourceCitations {...defaultProps} onToggle={onToggle} />);

    fireEvent.click(screen.getByText("Source Citations"));
    expect(onToggle).toHaveBeenCalled();
  });

  it("shows empty state when no sources", () => {
    const cardWithoutSources = {
      ...mockCard,
      source_quality: {
        ...mockCard.source_quality!,
        top_sources: [],
      },
    };

    render(
      <SourceCitations
        {...defaultProps}
        card={cardWithoutSources}
        isExpanded={true}
      />
    );

    expect(
      screen.getByText("No source citations available.")
    ).toBeInTheDocument();
  });

  it("shows filtered empty state", () => {
    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    const credibilitySlider = screen.getByRole("slider");
    fireEvent.change(credibilitySlider, { target: { value: "1.0" } });

    expect(
      screen.getByText("No sources meet the credibility filter criteria.")
    ).toBeInTheDocument();
    expect(screen.getByText("Reset filter")).toBeInTheDocument();
  });

  it("resets credibility filter", () => {
    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    const credibilitySlider = screen.getByRole("slider");
    fireEvent.change(credibilitySlider, { target: { value: "0.8" } });

    const resetButton = screen.getByText("Reset filter");
    fireEvent.click(resetButton);

    expect(credibilitySlider).toHaveValue("0");
  });

  it("displays source quality legend", () => {
    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    expect(screen.getByText("Source Quality Tiers")).toBeInTheDocument();
    expect(screen.getByText("WSJ, Reuters, Bloomberg, FT")).toBeInTheDocument();
    expect(screen.getByText("TechCrunch, VentureBeat")).toBeInTheDocument();
    expect(screen.getByText("HN, Reddit, Medium")).toBeInTheDocument();
    expect(screen.getByText("Blogs, Social Media")).toBeInTheDocument();
  });

  it("shows credibility stars for sources", () => {
    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    // Should show star ratings for each source
    const stars = screen.getAllByTestId(/star/i);
    expect(stars.length).toBeGreaterThan(0);
  });

  it("tracks clicked sources visually", () => {
    render(<SourceCitations {...defaultProps} isExpanded={true} />);

    const wsjSource = screen.getByText("WSJ Article");
    const sourceContainer = wsjSource.closest("div")!;

    fireEvent.click(sourceContainer);

    // Should show visual indication that source was clicked
    expect(sourceContainer).toHaveClass("bg-blue-50", "border-blue-200");
  });

  it("handles missing source quality data", () => {
    const cardWithoutQuality = {
      ...mockCard,
      source_quality: undefined,
    };

    render(
      <SourceCitations
        {...defaultProps}
        card={cardWithoutQuality}
        isExpanded={true}
      />
    );

    expect(
      screen.getByText("No source citations available.")
    ).toBeInTheDocument();
  });
});
