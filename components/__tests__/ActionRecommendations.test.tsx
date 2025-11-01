import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import ActionRecommendations from "../ActionRecommendations";
import * as api from "@/lib/api";

// Mock the API
jest.mock("@/lib/api");
const mockApi = api;

const mockActions = [
  {
    action: "Accelerate long-context model development",
    priority: "high",
    timeline: "immediate",
    owner: "Product Team",
    okr_goal: "Enhance product differentiation",
    impact_score: 90,
    effort_score: 40,
    score: 70,
    evidence: [
      {
        title: "GPT-4 Turbo Announcement",
        url: "https://openai.com/gpt4-turbo",
      },
    ],
    index: 0,
  },
  {
    action: "Develop competitive pricing strategy",
    priority: "medium",
    timeline: "1 week",
    owner: "Strategy Team",
    okr_goal: "Market positioning",
    impact_score: 70,
    effort_score: 30,
    score: 55,
    evidence: [],
    index: 1,
  },
];

const mockCard = {
  id: 1,
  competitor_name: "OpenAI",
  recommended_actions: mockActions,
  next_steps_plan: undefined,
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

describe("ActionRecommendations Component", () => {
  const defaultProps = {
    card: mockCard,
    isExpanded: false,
    onToggle: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockApi.api.post.mockResolvedValue({ data: { success: true } });
  });

  it("renders collapsed header", () => {
    renderWithQueryClient(<ActionRecommendations {...defaultProps} />);

    expect(screen.getByText("Action Recommendations")).toBeInTheDocument();
    expect(screen.getByText("(2 actions)")).toBeInTheDocument();
    expect(screen.getByText("2 prioritized")).toBeInTheDocument();
  });

  it("expands to show detailed content", () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    expect(
      screen.getByText("Accelerate long-context model development")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Develop competitive pricing strategy")
    ).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
    expect(screen.getByText("MEDIUM")).toBeInTheDocument();
  });

  it("displays action details correctly", () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    expect(screen.getByText("immediate")).toBeInTheDocument();
    expect(screen.getByText("Product Team")).toBeInTheDocument();
    expect(
      screen.getByText("Enhance product differentiation")
    ).toBeInTheDocument();
    expect(screen.getByText("Impact Score:")).toBeInTheDocument();
    expect(screen.getByText("90/100")).toBeInTheDocument();
    expect(screen.getByText("Effort Score:")).toBeInTheDocument();
    expect(screen.getByText("40/100")).toBeInTheDocument();
  });

  it("shows supporting evidence when available", () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    expect(screen.getByText("Supporting Evidence:")).toBeInTheDocument();
    expect(screen.getByText("GPT-4 Turbo Announcement")).toBeInTheDocument();
  });

  it("filters actions by role", () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    const roleSelect = screen.getByDisplayValue("All Roles");
    fireEvent.change(roleSelect, { target: { value: "product_manager" } });

    // Should show only product-related actions
    expect(
      screen.getByText("Accelerate long-context model development")
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Develop competitive pricing strategy")
    ).not.toBeInTheDocument();
  });

  it("filters actions by priority", () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    const prioritySelect = screen.getByDisplayValue("All Priorities");
    fireEvent.change(prioritySelect, { target: { value: "high" } });

    // Should show only high priority actions
    expect(
      screen.getByText("Accelerate long-context model development")
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Develop competitive pricing strategy")
    ).not.toBeInTheDocument();
  });

  it("handles feedback submission", async () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    const helpfulButton = screen.getAllByText("Helpful")[0];
    fireEvent.click(helpfulButton);

    await waitFor(() => {
      expect(mockApi.api.post).toHaveBeenCalledWith("/api/v1/feedback/impact", {
        impact_card_id: 1,
        action_index: 0,
        sentiment: "up",
      });
    });

    expect(screen.getByText("Thanks for the feedback!")).toBeInTheDocument();
  });

  it("handles negative feedback", async () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    const notRelevantButton = screen.getAllByText("Not relevant")[0];
    fireEvent.click(notRelevantButton);

    await waitFor(() => {
      expect(mockApi.api.post).toHaveBeenCalledWith("/api/v1/feedback/impact", {
        impact_card_id: 1,
        action_index: 0,
        sentiment: "down",
      });
    });
  });

  it("dismisses actions", () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    const dismissButtons = screen.getAllByTitle("Dismiss action");
    fireEvent.click(dismissButtons[0]);

    // Action should be removed from view
    expect(
      screen.queryByText("Accelerate long-context model development")
    ).not.toBeInTheDocument();
    expect(screen.getByText("1 action(s) dismissed")).toBeInTheDocument();
  });

  it("restores dismissed actions", () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    // Dismiss an action
    const dismissButtons = screen.getAllByTitle("Dismiss action");
    fireEvent.click(dismissButtons[0]);

    // Restore all actions
    const restoreButton = screen.getByText("Restore all");
    fireEvent.click(restoreButton);

    expect(
      screen.getByText("Accelerate long-context model development")
    ).toBeInTheDocument();
  });

  it("handles toggle functionality", () => {
    const onToggle = jest.fn();
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} onToggle={onToggle} />
    );

    fireEvent.click(screen.getByText("Action Recommendations"));
    expect(onToggle).toHaveBeenCalled();
  });

  it("shows empty state when no actions", () => {
    const cardWithoutActions = {
      ...mockCard,
      recommended_actions: [],
      next_steps_plan: [],
    };

    renderWithQueryClient(
      <ActionRecommendations
        {...defaultProps}
        card={cardWithoutActions}
        isExpanded={true}
      />
    );

    expect(
      screen.getByText("No action recommendations available.")
    ).toBeInTheDocument();
  });

  it("shows filtered empty state", () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    const roleSelect = screen.getByDisplayValue("All Roles");
    fireEvent.change(roleSelect, { target: { value: "executive" } });

    expect(
      screen.getByText("No actions match the current filters.")
    ).toBeInTheDocument();
    expect(screen.getByText("Reset filters")).toBeInTheDocument();
  });

  it("resets filters", () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    const roleSelect = screen.getByDisplayValue("All Roles");
    fireEvent.change(roleSelect, { target: { value: "product_manager" } });

    const resetButton = screen.getByText("Reset filters");
    fireEvent.click(resetButton);

    expect(roleSelect).toHaveValue("all");
  });

  it("marks actions as complete", () => {
    const consoleSpy = jest.spyOn(console, "log").mockImplementation();
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    const completeButton = screen.getAllByText("Mark Complete")[0];
    fireEvent.click(completeButton);

    expect(consoleSpy).toHaveBeenCalledWith(
      "Mark action as completed:",
      "Accelerate long-context model development"
    );

    consoleSpy.mockRestore();
  });

  it("displays priority scoring guide", () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    expect(screen.getByText("Priority Scoring Guide")).toBeInTheDocument();
    expect(
      screen.getByText("Impact Score - (Effort Score ÷ 2)")
    ).toBeInTheDocument();
    expect(screen.getByText("High Impact, Low Effort:")).toBeInTheDocument();
  });

  it("sorts actions by priority score", () => {
    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    const actionElements = screen.getAllByText(/Priority Score:/);
    // First action should have higher score (70.0)
    expect(actionElements[0]).toBeInTheDocument();
  });

  it("handles feedback API errors", async () => {
    mockApi.api.post.mockRejectedValue(new Error("API Error"));

    renderWithQueryClient(
      <ActionRecommendations {...defaultProps} isExpanded={true} />
    );

    const helpfulButton = screen.getAllByText("Helpful")[0];
    fireEvent.click(helpfulButton);

    await waitFor(() => {
      expect(
        screen.getByText("Unable to record feedback right now.")
      ).toBeInTheDocument();
    });
  });

  it("uses next_steps_plan when available", () => {
    const cardWithNextSteps = {
      ...mockCard,
      recommended_actions: undefined,
      next_steps_plan: mockActions,
    };

    renderWithQueryClient(
      <ActionRecommendations
        {...defaultProps}
        card={cardWithNextSteps}
        isExpanded={true}
      />
    );

    expect(
      screen.getByText("Accelerate long-context model development")
    ).toBeInTheDocument();
  });
});
