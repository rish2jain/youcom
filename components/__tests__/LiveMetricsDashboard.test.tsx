import { render, screen, waitFor } from "@testing-library/react";
import { LiveMetricsDashboard } from "../LiveMetricsDashboard";

// Mock timer functions
jest.useFakeTimers();

describe("LiveMetricsDashboard Component", () => {
  afterEach(() => {
    jest.clearAllTimers();
  });

  it("renders dashboard title and description", () => {
    render(<LiveMetricsDashboard />);

    expect(screen.getByText(/Live Demo Metrics/i)).toBeInTheDocument();
    expect(screen.getByText(/Real You.com API usage powering competitive intelligence/i)).toBeInTheDocument();
  });

  it("renders all four metric cards", () => {
    render(<LiveMetricsDashboard />);

    expect(screen.getByText("You.com API Calls")).toBeInTheDocument();
    expect(screen.getByText("Sources Aggregated")).toBeInTheDocument();
    expect(screen.getByText("Impact Cards Generated")).toBeInTheDocument();
    expect(screen.getByText("Avg Response Time")).toBeInTheDocument();
  });

  it("renders metric subtitles", () => {
    render(<LiveMetricsDashboard />);

    expect(screen.getByText("Across News, Search, Chat, ARI")).toBeInTheDocument();
    expect(screen.getByText("From 400+ sources per query")).toBeInTheDocument();
    expect(screen.getByText("Real competitive intelligence")).toBeInTheDocument();
    expect(screen.getByText("Lightning fast analysis")).toBeInTheDocument();
  });

  it("animates metrics from 0 to target values", async () => {
    render(<LiveMetricsDashboard />);

    // Initially should show 0 or low values
    const initialApiCalls = screen.getByText(/You.com API Calls/i).closest("div")?.querySelector(".text-3xl");
    expect(initialApiCalls?.textContent).toBe("0");

    // Fast-forward time to complete animation
    jest.advanceTimersByTime(2000);

    // Wait for state updates
    await waitFor(() => {
      const finalApiCalls = screen.getByText(/You.com API Calls/i).closest("div")?.querySelector(".text-3xl");
      expect(finalApiCalls?.textContent).toContain("1,247");
    });
  });

  it("displays API usage breakdown", () => {
    render(<LiveMetricsDashboard />);

    expect(screen.getByText("News API")).toBeInTheDocument();
    expect(screen.getByText("Search API")).toBeInTheDocument();
    expect(screen.getByText("Chat API")).toBeInTheDocument();
    expect(screen.getByText("ARI API")).toBeInTheDocument();

    // Check for breakdown values
    expect(screen.getByText("312")).toBeInTheDocument();
    expect(screen.getByText("428")).toBeInTheDocument();
    expect(screen.getByText("287")).toBeInTheDocument();
    expect(screen.getByText("220")).toBeInTheDocument();
  });

  it("displays system status and success rate", () => {
    render(<LiveMetricsDashboard />);

    expect(screen.getByText(/System Status: All APIs Operational/i)).toBeInTheDocument();
    expect(screen.getByText(/98.7% Success Rate/i)).toBeInTheDocument();
  });

  it("shows pulsing animation during counting", () => {
    render(<LiveMetricsDashboard />);

    // Check for pulse animation class
    const metricCards = document.querySelectorAll(".animate-pulse");
    expect(metricCards.length).toBeGreaterThan(0);
  });

  it("stops pulsing after animation completes", async () => {
    render(<LiveMetricsDashboard />);

    // Fast-forward to complete animation
    jest.advanceTimersByTime(2500);

    await waitFor(() => {
      // Pulse animation should be removed
      const pulsing = document.querySelectorAll(".animate-pulse");
      // Only the status indicator should still pulse
      expect(pulsing.length).toBeLessThanOrEqual(2);
    });
  });

  it("displays final metric values correctly", async () => {
    render(<LiveMetricsDashboard />);

    jest.advanceTimersByTime(2000);

    await waitFor(() => {
      expect(screen.getByText("1,247")).toBeInTheDocument(); // Total API Calls
      expect(screen.getByText("42,384")).toBeInTheDocument(); // Sources Aggregated
      expect(screen.getByText("156")).toBeInTheDocument(); // Impact Cards
      expect(screen.getByText("1.8s")).toBeInTheDocument(); // Avg Response Time
    });
  });

  it("renders with correct gradient background", () => {
    render(<LiveMetricsDashboard />);

    const container = document.querySelector(".bg-gradient-to-br");
    expect(container).toBeInTheDocument();
  });

  it("displays all metric icons", () => {
    render(<LiveMetricsDashboard />);

    // Icons should be rendered (lucide-react renders SVGs)
    const icons = document.querySelectorAll("svg");
    expect(icons.length).toBeGreaterThan(0);
  });

  it("animates metrics with correct timing", async () => {
    render(<LiveMetricsDashboard />);

    // Check intermediate values during animation
    jest.advanceTimersByTime(1000); // Halfway through

    await waitFor(() => {
      const apiCallsText = screen.getByText(/You.com API Calls/i).closest("div")?.querySelector(".text-3xl")?.textContent;
      const apiCallsValue = parseInt(apiCallsText?.replace(/,/g, "") || "0");

      // Should be roughly halfway to target (1247 / 2 = ~623)
      expect(apiCallsValue).toBeGreaterThan(0);
      expect(apiCallsValue).toBeLessThan(1247);
    });
  });
});
