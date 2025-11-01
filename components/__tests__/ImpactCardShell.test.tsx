import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ImpactCardShell } from "../ImpactCardShell";
import * as api from "@/lib/api";

// Mock the API
jest.mock("@/lib/api");
const mockApi = api;

// Mock socket
jest.mock("@/lib/socket", () => ({
  getSocket: () => ({
    emit: jest.fn(),
    on: jest.fn(),
    off: jest.fn(),
  }),
}));

// Mock lazy-loaded components
jest.mock("../ImpactCardHeader", () => ({
  __esModule: true,
  default: ({ card, onClick }: any) => (
    <div data-testid="impact-card-header" onClick={onClick}>
      {card.competitor_name}
    </div>
  ),
}));

jest.mock("../RiskScoreWidget", () => ({
  __esModule: true,
  default: ({ card }: any) => (
    <div data-testid="risk-score-widget">{card.competitor_name} Risk</div>
  ),
}));

jest.mock("../SourceCitations", () => ({
  __esModule: true,
  default: ({ card }: any) => (
    <div data-testid="source-citations">{card.competitor_name} Sources</div>
  ),
}));

jest.mock("../ActionRecommendations", () => ({
  __esModule: true,
  default: ({ card }: any) => (
    <div data-testid="action-recommendations">
      {card.competitor_name} Actions
    </div>
  ),
}));

jest.mock("../CollaborationPane", () => ({
  __esModule: true,
  default: ({ card }: any) => (
    <div data-testid="collaboration-pane">
      {card.competitor_name} Collaboration
    </div>
  ),
}));

const mockImpactCard = {
  id: 1,
  competitor_name: "OpenAI",
  risk_score: 85,
  risk_level: "high",
  confidence_score: 92,
  credibility_score: 0.82,
  requires_review: false,
  impact_areas: [
    {
      area: "product",
      impact_score: 90,
      description: "GPT-4 Turbo poses significant competitive threat",
    },
  ],
  key_insights: ["OpenAI announced GPT-4 Turbo with 128K context window"],
  recommended_actions: [],
  next_steps_plan: [],
  total_sources: 47,
  source_breakdown: {
    news_articles: 12,
    search_results: 15,
    research_citations: 20,
  },
  api_usage: {
    news_calls: 3,
    search_calls: 2,
    chat_calls: 1,
    ari_calls: 1,
    total_calls: 7,
  },
  created_at: "2024-01-01T00:00:00Z",
  processing_time: "4.32s",
};

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{component}</QueryClientProvider>
  );
};

describe("ImpactCardShell Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApi.api.get.mockResolvedValue({
      data: { items: [mockImpactCard], total: 1 },
    });
  });

  it("renders shell with header and generate form", async () => {
    renderWithQueryClient(<ImpactCardShell />);

    expect(screen.getByText("Impact Cards")).toBeInTheDocument();
    expect(screen.getByText("You.com Powered")).toBeInTheDocument();
    expect(screen.getByText("🚀 Generate Impact Card")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Competitor name (e.g., OpenAI)")
    ).toBeInTheDocument();
  });

  it("loads and displays impact cards", async () => {
    renderWithQueryClient(<ImpactCardShell />);

    await waitFor(() => {
      expect(screen.getByTestId("impact-card-header")).toBeInTheDocument();
      expect(screen.getByText("OpenAI")).toBeInTheDocument();
    });
  });

  it("handles card selection", async () => {
    const onCardSelect = jest.fn();
    renderWithQueryClient(<ImpactCardShell onCardSelect={onCardSelect} />);

    await waitFor(() => {
      const cardHeader = screen.getByTestId("impact-card-header");
      fireEvent.click(cardHeader);
    });

    await waitFor(() => {
      expect(onCardSelect).toHaveBeenCalledWith(mockImpactCard);
      expect(screen.getByText("OpenAI - Impact Analysis")).toBeInTheDocument();
    });
  });

  it("generates new impact card", async () => {
    mockApi.api.post.mockResolvedValue({ data: mockImpactCard });

    renderWithQueryClient(<ImpactCardShell />);

    const competitorInput = screen.getByPlaceholderText(
      "Competitor name (e.g., OpenAI)"
    );
    const generateButton = screen.getByText("Generate Impact Card");

    fireEvent.change(competitorInput, { target: { value: "OpenAI" } });
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(mockApi.api.post).toHaveBeenCalledWith("/api/v1/impact/generate", {
        competitor_name: "OpenAI",
        keywords: [],
      });
    });
  });

  it("shows loading state", () => {
    mockApi.api.get.mockImplementation(() => new Promise(() => {}));
    renderWithQueryClient(<ImpactCardShell />);

    expect(screen.getByTestId("loading-skeleton")).toBeInTheDocument();
  });

  it("handles credibility filter", async () => {
    renderWithQueryClient(<ImpactCardShell />);

    const filterSlider = screen.getByRole("slider");
    fireEvent.change(filterSlider, { target: { value: "0.5" } });

    await waitFor(() => {
      expect(mockApi.api.get).toHaveBeenCalledWith("/api/v1/impact/", {
        params: { min_credibility: 0.5 },
      });
    });
  });

  it("validates form input", () => {
    renderWithQueryClient(<ImpactCardShell />);

    const generateButton = screen.getByText("Generate Impact Card");
    fireEvent.click(generateButton);

    expect(
      screen.getByText("Competitor name must be at least 2 characters.")
    ).toBeInTheDocument();
  });

  it("shows empty state when no cards", async () => {
    mockApi.api.get.mockResolvedValue({ data: { items: [], total: 0 } });

    renderWithQueryClient(<ImpactCardShell />);

    await waitFor(() => {
      expect(
        screen.getByText("No Impact Cards generated yet.")
      ).toBeInTheDocument();
    });
  });

  it("renders lazy-loaded components when card is selected", async () => {
    renderWithQueryClient(<ImpactCardShell />);

    await waitFor(() => {
      const cardHeader = screen.getByTestId("impact-card-header");
      fireEvent.click(cardHeader);
    });

    await waitFor(() => {
      expect(screen.getByTestId("risk-score-widget")).toBeInTheDocument();
      expect(screen.getByTestId("source-citations")).toBeInTheDocument();
      expect(screen.getByTestId("action-recommendations")).toBeInTheDocument();
      expect(screen.getByTestId("collaboration-pane")).toBeInTheDocument();
    });
  });

  it("handles collaboration disabled mode", async () => {
    renderWithQueryClient(<ImpactCardShell collaborationEnabled={false} />);

    await waitFor(() => {
      const cardHeader = screen.getByTestId("impact-card-header");
      fireEvent.click(cardHeader);
    });

    await waitFor(() => {
      expect(
        screen.queryByTestId("collaboration-pane")
      ).not.toBeInTheDocument();
    });
  });
});
