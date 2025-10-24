import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ImpactCardDisplay } from "../ImpactCardDisplay";
import * as api from "@/lib/api";

// Mock the API
jest.mock("@/lib/api");
const mockApi = api as jest.Mocked<typeof api>;

// Mock Recharts
jest.mock("recharts", () => ({
  PieChart: ({ children }: any) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  BarChart: ({ children }: any) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  Tooltip: () => <div data-testid="tooltip" />,
}));

const mockImpactCards = [
  {
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
    key_insights: [
      "OpenAI announced GPT-4 Turbo with 128K context window",
      "Strong enterprise adoption with Fortune 500 companies",
    ],
    recommended_actions: [
      {
        action: "Accelerate long-context model development",
        priority: "high",
        timeline: "immediate",
        owner: "Product",
        okr_goal: "Enhance product differentiation",
        impact_score: 90,
        effort_score: 40,
        score: 70,
        evidence: [],
        index: 0,
      },
    ],
    next_steps_plan: [
      {
        action: "Accelerate long-context model development",
        priority: "high",
        timeline: "immediate",
        owner: "Product",
        okr_goal: "Enhance product differentiation",
        impact_score: 90,
        effort_score: 40,
        score: 70,
        evidence: [],
        index: 0,
      },
    ],
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
      top_sources: [{ title: "Example", url: "https://example.com", type: "news" }],
    },
    api_usage: {
      news_calls: 3,
      search_calls: 2,
      chat_calls: 1,
      ari_calls: 1,
      total_calls: 7,
    },
    explainability: {
      reasoning: "Model reasoning",
      impact_areas: [],
      key_insights: [],
      source_summary: {},
    },
    created_at: "2024-01-01T00:00:00Z",
    processing_time: "4.32s",
  },
];

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

const renderWithQueryClient = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{component}</QueryClientProvider>
  );
};

describe("ImpactCardDisplay Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApi.api.get.mockImplementation((url: string) => {
      if (url.startsWith("/api/v1/impact/comparison")) {
        return Promise.resolve({ data: { series: { OpenAI: [] } } });
      }
      if (url === "/api/v1/notifications/logs") {
        return Promise.resolve({ data: { items: [] } });
      }
      if (url.startsWith("/api/v1/impact/")) {
        return Promise.resolve({ data: { items: mockImpactCards, total: 1 } });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it("renders impact cards list", async () => {
    mockApi.api.get.mockImplementation((url: string) => {
      if (url.startsWith("/api/v1/impact/comparison")) {
        return Promise.resolve({ data: { series: { OpenAI: [] } } });
      }
      if (url === "/api/v1/notifications/logs") {
        return Promise.resolve({ data: { items: [] } });
      }
      if (url.startsWith("/api/v1/impact/")) {
        return Promise.resolve({ data: { items: mockImpactCards, total: 1 } });
      }
      return Promise.resolve({ data: {} });
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    expect(screen.getByText("Impact Cards")).toBeInTheDocument();
    expect(screen.getByText("You.com Powered")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("OpenAI")).toBeInTheDocument();
      expect(screen.getByText("HIGH RISK")).toBeInTheDocument();
      expect(screen.getByText("Score: 85/100")).toBeInTheDocument();
      expect(screen.getByText("Credibility: 82%"))
        .toBeInTheDocument();
      expect(screen.getByText("47 sources")).toBeInTheDocument();
    });
  });

  it("shows empty state when no impact cards", async () => {
    mockApi.api.get.mockImplementation((url: string) => {
      if (url.startsWith("/api/v1/impact/comparison")) {
        return Promise.resolve({ data: { series: { OpenAI: [] } } });
      }
      if (url === "/api/v1/notifications/logs") {
        return Promise.resolve({ data: { items: [] } });
      }
      if (url.startsWith("/api/v1/impact/")) {
        return Promise.resolve({ data: { items: [], total: 0 } });
      }
      return Promise.resolve({ data: {} });
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    await waitFor(() => {
      expect(
        screen.getByText("No Impact Cards generated yet.")
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "Generate your first Impact Card to see You.com APIs in action!"
        )
      ).toBeInTheDocument();
    });
  });

  it("generates new impact card", async () => {
    mockApi.api.get.mockImplementation((url: string) => {
      if (url.startsWith("/api/v1/impact/comparison")) {
        return Promise.resolve({ data: { series: { OpenAI: [] } } });
      }
      if (url === "/api/v1/notifications/logs") {
        return Promise.resolve({ data: { items: [] } });
      }
      if (url.startsWith("/api/v1/impact/")) {
        return Promise.resolve({ data: { items: [], total: 0 } });
      }
      return Promise.resolve({ data: {} });
    });
    mockApi.api.post.mockResolvedValue({
      data: mockImpactCards[0],
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    const competitorInput = screen.getByPlaceholderText(
      "Competitor name (e.g., OpenAI)"
    );
    const keywordsInput = screen.getByPlaceholderText("Keywords (optional)");
    const generateButton = screen.getByText("Generate Impact Card");

    fireEvent.change(competitorInput, { target: { value: "OpenAI" } });
    fireEvent.change(keywordsInput, { target: { value: "GPT, ChatGPT" } });
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(mockApi.api.post).toHaveBeenCalledWith("/api/v1/impact/generate", {
        competitor_name: "OpenAI",
        keywords: ["GPT", "ChatGPT"],
      });
    });
  });

  it("shows processing indicator during generation", async () => {
    mockApi.api.get.mockImplementation((url: string) => {
      if (url.startsWith("/api/v1/impact/comparison")) {
        return Promise.resolve({ data: { series: { OpenAI: [] } } });
      }
      if (url === "/api/v1/notifications/logs") {
        return Promise.resolve({ data: { items: [] } });
      }
      if (url.startsWith("/api/v1/impact/")) {
        return Promise.resolve({ data: { items: [], total: 0 } });
      }
      return Promise.resolve({ data: {} });
    });
    mockApi.api.post.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithQueryClient(<ImpactCardDisplay />);

    const competitorInput = screen.getByPlaceholderText(
      "Competitor name (e.g., OpenAI)"
    );
    const generateButton = screen.getByText("Generate Impact Card");

    fireEvent.change(competitorInput, { target: { value: "OpenAI" } });
    fireEvent.click(generateButton);

    await waitFor(() => {
      expect(
        screen.getByText("Generating with You.com APIs...")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Processing: News → Search → Chat → ARI → Impact Card")
      ).toBeInTheDocument();
    });
  });

  it("displays detailed impact card when selected", async () => {
    mockApi.api.get.mockImplementation((url: string) => {
      if (url.startsWith("/api/v1/impact/comparison")) {
        return Promise.resolve({
          data: {
            series: {
              OpenAI: [
                { created_at: "2024-01-01T00:00:00Z", risk_score: 80, credibility_score: 0.8 },
              ],
            },
          },
        });
      }
      if (url === "/api/v1/notifications/logs") {
        return Promise.resolve({ data: { items: [] } });
      }
      if (url.startsWith("/api/v1/impact/")) {
        return Promise.resolve({ data: { items: mockImpactCards, total: 1 } });
      }
      return Promise.resolve({ data: {} });
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    await waitFor(() => {
      const impactCard = screen.getByText("OpenAI");
      fireEvent.click(impactCard.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByText("OpenAI - Impact Analysis")).toBeInTheDocument();
      expect(screen.getByText("92%")).toBeInTheDocument(); // Confidence score
      expect(screen.getByText("Confidence Score")).toBeInTheDocument();
      expect(screen.getByText("Total Sources")).toBeInTheDocument();
    });
  });

  it("shows impact areas in detailed view", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockImpactCards, total: 1 },
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    await waitFor(() => {
      const impactCard = screen.getByText("OpenAI");
      fireEvent.click(impactCard.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByText("Impact Areas")).toBeInTheDocument();
      expect(screen.getByText("Product")).toBeInTheDocument();
      expect(
        screen.getByText("GPT-4 Turbo poses significant competitive threat")
      ).toBeInTheDocument();
    });
  });

  it("shows key insights in detailed view", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockImpactCards, total: 1 },
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    await waitFor(() => {
      const impactCard = screen.getByText("OpenAI");
      fireEvent.click(impactCard.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByText("Key Insights")).toBeInTheDocument();
      expect(
        screen.getByText(
          "OpenAI announced GPT-4 Turbo with 128K context window"
        )
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          "Strong enterprise adoption with Fortune 500 companies"
        )
      ).toBeInTheDocument();
    });
  });

  it("shows recommended actions in detailed view", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockImpactCards, total: 1 },
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    await waitFor(() => {
      const impactCard = screen.getByText("OpenAI");
      fireEvent.click(impactCard.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByText("Recommended Actions")).toBeInTheDocument();
      expect(
        screen.getByText("Accelerate long-context model development")
      ).toBeInTheDocument();
      expect(screen.getByText("HIGH")).toBeInTheDocument();
      expect(screen.getByText("immediate")).toBeInTheDocument();
    });
  });

  it("shows You.com API usage in detailed view", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockImpactCards, total: 1 },
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    await waitFor(() => {
      const impactCard = screen.getByText("OpenAI");
      fireEvent.click(impactCard.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByText("You.com API Usage")).toBeInTheDocument();
      expect(screen.getByText("News API")).toBeInTheDocument();
      expect(screen.getByText("Search API")).toBeInTheDocument();
      expect(screen.getByText("Chat API")).toBeInTheDocument();
      expect(screen.getByText("ARI API")).toBeInTheDocument();
      expect(screen.getByText("Total API Calls: 7")).toBeInTheDocument();
    });
  });

  it("closes detailed view when clicking close button", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockImpactCards, total: 1 },
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    await waitFor(() => {
      const impactCard = screen.getByText("OpenAI");
      fireEvent.click(impactCard.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByText("OpenAI - Impact Analysis")).toBeInTheDocument();

      const closeButton = screen.getByText("✕");
      fireEvent.click(closeButton);
    });

    await waitFor(() => {
      expect(
        screen.queryByText("OpenAI - Impact Analysis")
      ).not.toBeInTheDocument();
    });
  });

  it("displays risk score gauge chart", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockImpactCards, total: 1 },
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    await waitFor(() => {
      const impactCard = screen.getByText("OpenAI");
      fireEvent.click(impactCard.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByTestId("pie-chart")).toBeInTheDocument();
      expect(screen.getByTestId("responsive-container")).toBeInTheDocument();
    });
  });

  it("handles form validation", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: [], total: 0 },
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    const generateButton = screen.getByText("Generate Impact Card");
    fireEvent.click(generateButton);

    // Should not make API call without competitor name
    expect(mockApi.api.post).not.toHaveBeenCalled();
  });

  it("shows correct risk level colors", async () => {
    const criticalRiskCard = {
      ...mockImpactCards[0],
      risk_level: "critical",
      risk_score: 95,
    };

    mockApi.api.get.mockResolvedValue({
      data: { items: [criticalRiskCard], total: 1 },
    });

    renderWithQueryClient(<ImpactCardDisplay />);

    await waitFor(() => {
      expect(screen.getByText("CRITICAL RISK")).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    mockApi.api.get.mockRejectedValue(new Error("API Error"));

    renderWithQueryClient(<ImpactCardDisplay />);

    // Component should still render without crashing
    expect(screen.getByText("Impact Cards")).toBeInTheDocument();
  });
});
