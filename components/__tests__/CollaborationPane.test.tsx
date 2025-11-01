import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import CollaborationPane from "../CollaborationPane";
import * as api from "@/lib/api";

// Mock the API
jest.mock("@/lib/api");
const mockApi = api;

// Mock MLFeedbackPanel
jest.mock("../MLFeedbackPanel", () => ({
  MLFeedbackPanel: ({ impactCardId }: any) => (
    <div data-testid="ml-feedback-panel">ML Feedback for {impactCardId}</div>
  ),
}));

const mockCard = {
  id: 1,
  competitor_name: "OpenAI",
  risk_score: 85,
  risk_level: "high",
  confidence_score: 92,
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
  explainability: {
    reasoning:
      "Model detected significant competitive threat based on multiple factors",
    impact_areas: [
      {
        area: "product",
        impact_score: 90,
        description: "Direct product competition",
      },
    ],
    key_insights: ["Key insight from explainability"],
    source_summary: { news: 5, research: 3 },
  },
};

const mockNotificationLogs = [
  {
    id: "1",
    competitor_name: "OpenAI",
    channel: "slack",
    message: "New competitive threat detected",
    created_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "2",
    competitor_name: "Anthropic",
    channel: "email",
    message: "Claude 3 announcement",
    created_at: "2024-01-02T00:00:00Z",
  },
];

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

describe("CollaborationPane Component", () => {
  const defaultProps = {
    card: mockCard,
    isExpanded: false,
    onToggle: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockApi.api.get.mockResolvedValue({
      data: { items: mockNotificationLogs },
    });
  });

  it("renders collapsed header", () => {
    renderWithQueryClient(<CollaborationPane {...defaultProps} />);

    expect(screen.getByText("Collaboration & Insights")).toBeInTheDocument();
    expect(screen.getByText("2 comments")).toBeInTheDocument();
  });

  it("shows active users when expanded", () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    expect(screen.getByText("Active Users")).toBeInTheDocument();
    expect(screen.getByText("Live")).toBeInTheDocument();
    expect(screen.getByText("Alice (PM)")).toBeInTheDocument();
    expect(screen.getByText("Bob (Strategy)")).toBeInTheDocument();
  });

  it("displays existing comments", () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    expect(screen.getByText("Team Discussion")).toBeInTheDocument();
    expect(
      screen.getByText(
        "This looks significant - we should prioritize the product response."
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Agreed. I'll coordinate with the competitive analysis team."
      )
    ).toBeInTheDocument();
  });

  it("adds new comments", () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    const textarea = screen.getByPlaceholderText(
      "Add a comment... (Press Enter to send)"
    );
    const sendButton = screen.getByText("Send");

    fireEvent.change(textarea, { target: { value: "This is a new comment" } });
    fireEvent.click(sendButton);

    expect(screen.getByText("This is a new comment")).toBeInTheDocument();
    expect(textarea).toHaveValue("");
  });

  it("adds comments with Enter key", () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    const textarea = screen.getByPlaceholderText(
      "Add a comment... (Press Enter to send)"
    );

    fireEvent.change(textarea, { target: { value: "Comment via Enter" } });
    fireEvent.keyPress(textarea, { key: "Enter", code: "Enter" });

    expect(screen.getByText("Comment via Enter")).toBeInTheDocument();
  });

  it("prevents adding empty comments", () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    const sendButton = screen.getByText("Send");
    expect(sendButton).toBeDisabled();

    const textarea = screen.getByPlaceholderText(
      "Add a comment... (Press Enter to send)"
    );
    fireEvent.change(textarea, { target: { value: "   " } }); // Only whitespace

    fireEvent.click(sendButton);
    expect(screen.queryByText("   ")).not.toBeInTheDocument();
  });

  it("displays notifications", async () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    await waitFor(() => {
      expect(screen.getByText("Recent Notifications")).toBeInTheDocument();
      expect(
        screen.getByText("New competitive threat detected")
      ).toBeInTheDocument();
      expect(screen.getByText("Claude 3 announcement")).toBeInTheDocument();
      expect(screen.getByText("slack")).toBeInTheDocument();
      expect(screen.getByText("email")).toBeInTheDocument();
    });
  });

  it("shows ML feedback panel", () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    expect(screen.getByTestId("ml-feedback-panel")).toBeInTheDocument();
    expect(screen.getByText("ML Feedback for 1")).toBeInTheDocument();
  });

  it("displays key insights", () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    expect(screen.getByText("Key Insights")).toBeInTheDocument();
    expect(
      screen.getByText("OpenAI announced GPT-4 Turbo with 128K context window")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Strong enterprise adoption with Fortune 500 companies")
    ).toBeInTheDocument();
  });

  it("toggles explainability deep dive", () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    const explainabilityButton = screen.getByText(
      "Show AI Explainability Deep Dive"
    );
    fireEvent.click(explainabilityButton);

    expect(screen.getByText("Model Reasoning:")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Model detected significant competitive threat based on multiple factors"
      )
    ).toBeInTheDocument();
    expect(screen.getByText("Impact Drivers:")).toBeInTheDocument();
    expect(screen.getByText("Source Analysis:")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Hide AI Explainability Deep Dive"));
    expect(screen.queryByText("Model Reasoning:")).not.toBeInTheDocument();
  });

  it("handles toggle functionality", () => {
    const onToggle = jest.fn();
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} onToggle={onToggle} />
    );

    fireEvent.click(screen.getByText("Collaboration & Insights"));
    expect(onToggle).toHaveBeenCalled();
  });

  it("shows empty notifications state", async () => {
    mockApi.api.get.mockResolvedValue({ data: { items: [] } });

    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    await waitFor(() => {
      expect(screen.getByText("No recent notifications")).toBeInTheDocument();
    });
  });

  it("formats timestamps correctly", () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    // Should show relative time for recent comments
    expect(screen.getByText("15m ago")).toBeInTheDocument();
    expect(screen.getByText("10m ago")).toBeInTheDocument();
  });

  it("handles Shift+Enter in textarea", () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    const textarea = screen.getByPlaceholderText(
      "Add a comment... (Press Enter to send)"
    );

    fireEvent.change(textarea, { target: { value: "Line 1" } });
    fireEvent.keyPress(textarea, {
      key: "Enter",
      code: "Enter",
      shiftKey: true,
    });

    // Should not submit comment with Shift+Enter
    expect(screen.queryByText("Line 1")).not.toBeInTheDocument();
  });

  it("displays collaboration action buttons", () => {
    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    expect(screen.getByText("Watch for Updates")).toBeInTheDocument();
    expect(screen.getByText("Set Alert")).toBeInTheDocument();
    expect(screen.getByText("Share with Team")).toBeInTheDocument();
  });

  it("handles missing explainability data", () => {
    const cardWithoutExplainability = {
      ...mockCard,
      explainability: undefined,
    };

    renderWithQueryClient(
      <CollaborationPane
        {...defaultProps}
        card={cardWithoutExplainability}
        isExpanded={true}
      />
    );

    const explainabilityButton = screen.getByText(
      "Show AI Explainability Deep Dive"
    );
    fireEvent.click(explainabilityButton);

    // Should not crash when explainability is undefined
    expect(screen.queryByText("Model Reasoning:")).not.toBeInTheDocument();
  });

  it("handles API errors for notifications", async () => {
    mockApi.api.get.mockRejectedValue(new Error("API Error"));

    renderWithQueryClient(
      <CollaborationPane {...defaultProps} isExpanded={true} />
    );

    await waitFor(() => {
      expect(screen.getByText("No recent notifications")).toBeInTheDocument();
    });
  });

  it("shows correct active user count", () => {
    renderWithQueryClient(<CollaborationPane {...defaultProps} />);

    expect(screen.getByText("2")).toBeInTheDocument(); // Active user count
  });

  it("handles missing key insights", () => {
    const cardWithoutInsights = {
      ...mockCard,
      key_insights: [],
    };

    renderWithQueryClient(
      <CollaborationPane
        {...defaultProps}
        card={cardWithoutInsights}
        isExpanded={true}
      />
    );

    expect(screen.queryByText("Key Insights")).not.toBeInTheDocument();
  });
});
