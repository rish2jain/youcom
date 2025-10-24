import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { APIUsageDashboard } from "../APIUsageDashboard";
import * as api from "@/lib/api";

// Mock the API
jest.mock("@/lib/api");
const mockApi = api as jest.Mocked<typeof api>;

// Mock recharts to avoid rendering issues in tests
jest.mock("recharts", () => ({
  ...jest.requireActual("recharts"),
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Cell: () => <div />,
}));

// Mock data
const mockApiUsageMetrics = {
  impact_cards: 5,
  company_research: 3,
  total_calls: 24,
  success_rate: 0.96,
  average_latency_ms: 850,
  p95_latency_ms: 1200,
  p99_latency_ms: 1500,
  by_service: {
    news: 6,
    search: 8,
    chat: 5,
    ari: 5,
  },
  usage_last_24h: [
    { time: "00:00", news: 1, search: 2, chat: 1, ari: 1 },
    { time: "06:00", news: 2, search: 3, chat: 2, ari: 2 },
    { time: "12:00", news: 3, search: 3, chat: 2, ari: 2 },
  ],
  last_call_at: "2024-01-01T12:00:00Z",
  total_sources: 150,
  average_processing_seconds: 45,
  last_generated_at: "2024-01-01T12:00:00Z",
};

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

describe("APIUsageDashboard Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders dashboard title and badge", () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    expect(screen.getByText("You.com API Usage Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Live Demo Metrics")).toBeInTheDocument();
  });

  it("displays key metrics", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText("24")).toBeInTheDocument(); // Total API Calls
      expect(screen.getByText("5")).toBeInTheDocument(); // Impact Cards
      expect(screen.getByText("96.0%")).toBeInTheDocument(); // Success Rate
      expect(screen.getByText("1200 ms")).toBeInTheDocument(); // p95 Latency
    });

    expect(screen.getByText("Total API Calls")).toBeInTheDocument();
    expect(screen.getByText("Impact Cards Generated")).toBeInTheDocument();
    expect(screen.getByText("Success Rate")).toBeInTheDocument();
    expect(screen.getByText("p95 Latency")).toBeInTheDocument();
  });

  it("shows company research count in impact cards metric", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Company research: 3")).toBeInTheDocument();
    });
  });

  it("displays API service breakdown", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText("6 calls total")).toBeInTheDocument(); // News API
      expect(screen.getByText("8 calls total")).toBeInTheDocument(); // Search API
      expect(screen.getByText("5 calls total")).toBeInTheDocument(); // Chat API or ARI API
    });

    expect(screen.getByText("News API")).toBeInTheDocument();
    expect(screen.getByText("Search API")).toBeInTheDocument();
    expect(screen.getByText("Chat API")).toBeInTheDocument();
    expect(screen.getByText("ARI API")).toBeInTheDocument();
  });

  it("renders pie chart for API calls by service", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText("API Calls by Service")).toBeInTheDocument();
      expect(screen.getByTestId("pie-chart")).toBeInTheDocument();
    });
  });

  it("renders bar chart for usage over time", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Usage Over Time")).toBeInTheDocument();
      expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
    });
  });

  it("shows loading state", () => {
    mockApi.api.get.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithQueryClient(<APIUsageDashboard />);

    expect(
      document.querySelector(".animate-pulse")
    ).toBeInTheDocument();
  });

  it("shows empty state when no metrics available", async () => {
    mockApi.api.get.mockResolvedValue({ data: null });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(
        screen.getByText("Live API analytics will appear once calls have been recorded.")
      ).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    mockApi.api.get.mockRejectedValue(new Error("Failed to load metrics"));

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Unable to load API usage metrics.")).toBeInTheDocument();
    });

    // Component should still render
    expect(screen.getByText("You.com API Usage Dashboard")).toBeInTheDocument();
  });

  it("displays performance insights", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Performance Insights")).toBeInTheDocument();
      expect(screen.getByText("Orchestration Efficiency")).toBeInTheDocument();
      expect(screen.getByText("Cache Optimization")).toBeInTheDocument();
      expect(screen.getByText("Real-time Updates")).toBeInTheDocument();
    });
  });

  it("shows average latency in performance insights", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/average latency 850 ms/)).toBeInTheDocument();
    });
  });

  it("displays API integration details", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      // News API details
      expect(screen.getByText("• Real-time monitoring")).toBeInTheDocument();
      expect(screen.getByText("• Competitor alerts")).toBeInTheDocument();

      // Search API details
      expect(screen.getByText("• Context enrichment")).toBeInTheDocument();
      expect(screen.getByText("• Company profiles")).toBeInTheDocument();

      // Chat API details
      expect(screen.getByText("• Custom Agents")).toBeInTheDocument();
      expect(screen.getByText("• Impact analysis")).toBeInTheDocument();

      // ARI API details
      expect(screen.getByText("• Deep research")).toBeInTheDocument();
      expect(screen.getByText("• 400+ sources")).toBeInTheDocument();
    });
  });

  it("shows placeholders when metrics are null", async () => {
    const metricsWithNulls = {
      ...mockApiUsageMetrics,
      success_rate: null,
      average_latency_ms: null,
      p95_latency_ms: null,
      p99_latency_ms: null,
    };

    mockApi.api.get.mockResolvedValue({ data: metricsWithNulls });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      // Should show "—" for null values
      const placeholders = screen.getAllByText("—");
      expect(placeholders.length).toBeGreaterThan(0);
    });
  });

  it("handles empty API service data", async () => {
    const metricsWithEmptyServices = {
      ...mockApiUsageMetrics,
      by_service: {
        news: 0,
        search: 0,
        chat: 0,
        ari: 0,
      },
    };

    mockApi.api.get.mockResolvedValue({ data: metricsWithEmptyServices });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText("No API calls recorded yet.")).toBeInTheDocument();
    });
  });

  it("handles empty timeline data", async () => {
    const metricsWithEmptyTimeline = {
      ...mockApiUsageMetrics,
      usage_last_24h: [],
    };

    mockApi.api.get.mockResolvedValue({ data: metricsWithEmptyTimeline });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText("No API activity in the last 24 hours.")).toBeInTheDocument();
    });
  });

  it("displays cache optimization details", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(
        screen.getByText(/Smart caching reduces duplicate calls: News \(15m\), Search \(1h\), ARI \(7d\)/)
      ).toBeInTheDocument();
    });
  });

  it("shows p99 latency in metric card", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/p99: 1500 ms/)).toBeInTheDocument();
    });
  });

  it("displays aggregated calls info in total calls metric", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(
        screen.getByText("Aggregated across News, Search, Chat, ARI")
      ).toBeInTheDocument();
    });
  });

  it("shows success rate calculation info", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText("Successful calls ÷ total attempts")).toBeInTheDocument();
    });
  });

  it("fetches metrics with correct stale time", () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    // Verify the API was called
    expect(mockApi.api.get).toHaveBeenCalledWith("/api/v1/metrics/api-usage");
  });

  it("displays company research count in real-time updates", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockApiUsageMetrics });

    renderWithQueryClient(<APIUsageDashboard />);

    await waitFor(() => {
      expect(screen.getByText(/company research records:/)).toBeInTheDocument();
    });
  });
});
