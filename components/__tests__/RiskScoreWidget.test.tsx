import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import RiskScoreWidget from "../RiskScoreWidget";
import * as api from "@/lib/api";

// Mock the API
jest.mock("@/lib/api");
const mockApi = api;

// Mock Recharts
jest.mock("recharts", () => ({
  PieChart: ({ children }: any) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Pie: ({ children }: any) => <div data-testid="pie">{children}</div>,
  Cell: () => <div data-testid="cell" />,
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  LineChart: ({ children }: any) => (
    <div data-testid="line-chart">{children}</div>
  ),
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
}));

const mockCard = {
  id: 1,
  competitor_name: "OpenAI",
  risk_score: 85,
  risk_level: "high",
  confidence_score: 92,
  credibility_score: 0.82,
  impact_areas: [
    {
      area: "product",
      impact_score: 90,
      description: "GPT-4 Turbo poses significant competitive threat",
    },
    {
      area: "market",
      impact_score: 75,
      description: "Strong market positioning",
    },
  ],
  created_at: "2024-01-01T00:00:00Z",
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

describe("RiskScoreWidget Component", () => {
  const defaultProps = {
    card: mockCard,
    isExpanded: false,
    onToggle: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockApi.api.get.mockResolvedValue({
      data: {
        series: {
          OpenAI: [
            {
              created_at: "2024-01-01T00:00:00Z",
              risk_score: 80,
              credibility_score: 0.8,
            },
            {
              created_at: "2024-01-02T00:00:00Z",
              risk_score: 85,
              credibility_score: 0.82,
            },
          ],
        },
      },
    });
  });

  it("renders collapsed header", () => {
    renderWithQueryClient(<RiskScoreWidget {...defaultProps} />);

    expect(screen.getByText("Risk Score Analysis")).toBeInTheDocument();
    expect(screen.getByText("Increasing Risk")).toBeInTheDocument();
  });

  it("shows stable trend when risk hasn't changed significantly", async () => {
    mockApi.api.get.mockResolvedValue({
      data: {
        series: {
          OpenAI: [
            {
              created_at: "2024-01-01T00:00:00Z",
              risk_score: 85,
              credibility_score: 0.8,
            },
            {
              created_at: "2024-01-02T00:00:00Z",
              risk_score: 87,
              credibility_score: 0.82,
            },
          ],
        },
      },
    });

    renderWithQueryClient(<RiskScoreWidget {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Stable")).toBeInTheDocument();
    });
  });

  it("expands to show detailed content", async () => {
    renderWithQueryClient(
      <RiskScoreWidget {...defaultProps} isExpanded={true} />
    );

    await waitFor(() => {
      expect(screen.getByTestId("pie-chart")).toBeInTheDocument();
      expect(screen.getByText("Risk Score")).toBeInTheDocument();
      expect(screen.getByText("Confidence Score")).toBeInTheDocument();
      expect(screen.getByText("Credibility Score")).toBeInTheDocument();
    });
  });

  it("displays impact areas breakdown when expanded", async () => {
    renderWithQueryClient(
      <RiskScoreWidget {...defaultProps} isExpanded={true} />
    );

    fireEvent.click(screen.getByText("Show Details"));

    await waitFor(() => {
      expect(screen.getByText("product")).toBeInTheDocument();
      expect(screen.getByText("market")).toBeInTheDocument();
      expect(
        screen.getByText("GPT-4 Turbo poses significant competitive threat")
      ).toBeInTheDocument();
    });
  });

  it("shows trend chart when historical data is available", async () => {
    renderWithQueryClient(
      <RiskScoreWidget {...defaultProps} isExpanded={true} />
    );

    await waitFor(() => {
      expect(screen.getByText("Risk Trend")).toBeInTheDocument();
      expect(screen.getByTestId("line-chart")).toBeInTheDocument();
    });
  });

  it("handles toggle functionality", () => {
    const onToggle = jest.fn();
    renderWithQueryClient(
      <RiskScoreWidget {...defaultProps} onToggle={onToggle} />
    );

    fireEvent.click(screen.getByText("Risk Score Analysis"));
    expect(onToggle).toHaveBeenCalled();
  });

  it("shows loading state for trend data", () => {
    mockApi.api.get.mockImplementation(() => new Promise(() => {}));
    renderWithQueryClient(
      <RiskScoreWidget {...defaultProps} isExpanded={true} />
    );

    expect(screen.getByText("Loading trend data...")).toBeInTheDocument();
  });

  it("handles API error gracefully", async () => {
    mockApi.api.get.mockRejectedValue(new Error("API Error"));
    renderWithQueryClient(
      <RiskScoreWidget {...defaultProps} isExpanded={true} />
    );

    await waitFor(() => {
      expect(screen.queryByTestId("line-chart")).not.toBeInTheDocument();
    });
  });

  it("displays risk level guide", async () => {
    renderWithQueryClient(
      <RiskScoreWidget {...defaultProps} isExpanded={true} />
    );

    await waitFor(() => {
      expect(screen.getByText("Risk Level Guide:")).toBeInTheDocument();
      expect(screen.getByText("Critical (80-100):")).toBeInTheDocument();
      expect(screen.getByText("Immediate action required")).toBeInTheDocument();
    });
  });

  it("calculates correct trend direction", async () => {
    // Test decreasing trend
    mockApi.api.get.mockResolvedValue({
      data: {
        series: {
          OpenAI: [
            {
              created_at: "2024-01-01T00:00:00Z",
              risk_score: 90,
              credibility_score: 0.8,
            },
            {
              created_at: "2024-01-02T00:00:00Z",
              risk_score: 80,
              credibility_score: 0.82,
            },
          ],
        },
      },
    });

    renderWithQueryClient(<RiskScoreWidget {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Decreasing Risk")).toBeInTheDocument();
    });
  });

  it("shows correct risk colors for different scores", async () => {
    const criticalCard = {
      ...mockCard,
      risk_score: 95,
      risk_level: "critical",
    };
    renderWithQueryClient(
      <RiskScoreWidget
        {...defaultProps}
        card={criticalCard}
        isExpanded={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("CRITICAL RISK")).toBeInTheDocument();
    });
  });

  it("handles empty trend data", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { series: { OpenAI: [] } },
    });

    renderWithQueryClient(
      <RiskScoreWidget {...defaultProps} isExpanded={true} />
    );

    await waitFor(() => {
      expect(screen.queryByText("Risk Trend")).not.toBeInTheDocument();
    });
  });
});
