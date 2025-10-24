import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WatchList } from "../WatchList";
import * as api from "@/lib/api";

// Mock the API
jest.mock("@/lib/api");
const mockApi = api as jest.Mocked<typeof api>;

// Mock data
const mockWatchItems = [
  {
    id: 1,
    competitor_name: "OpenAI",
    keywords: ["GPT", "ChatGPT", "API"],
    description: "Leading AI company",
    is_active: true,
    created_at: "2024-01-01T00:00:00Z",
    last_checked: null,
  },
  {
    id: 2,
    competitor_name: "Anthropic",
    keywords: ["Claude", "AI assistant"],
    description: "AI safety company",
    is_active: false,
    created_at: "2024-01-02T00:00:00Z",
    last_checked: "2024-01-02T12:00:00Z",
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

describe("WatchList Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders watchlist with items", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockWatchItems, total: 2 },
    });

    renderWithQueryClient(<WatchList />);

    expect(screen.getByText("Competitor Watchlist")).toBeInTheDocument();
    expect(screen.getByText("Add Competitor")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("OpenAI")).toBeInTheDocument();
      expect(screen.getByText("Anthropic")).toBeInTheDocument();
    });

    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("shows empty state when no items", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: [], total: 0 },
    });

    renderWithQueryClient(<WatchList />);

    await waitFor(() => {
      expect(
        screen.getByText("No competitors being monitored yet.")
      ).toBeInTheDocument();
      expect(
        screen.getByText("Add your first competitor to get started!")
      ).toBeInTheDocument();
    });
  });

  it("shows loading state", () => {
    mockApi.api.get.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithQueryClient(<WatchList />);

    expect(
      screen.getByTestId("loading-skeleton") ||
        document.querySelector(".animate-pulse")
    ).toBeInTheDocument();
  });

  it("opens add form when clicking Add Competitor", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: [], total: 0 },
    });

    renderWithQueryClient(<WatchList />);

    const addButton = screen.getByText("Add Competitor");
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("e.g., OpenAI, Anthropic, Google")
      ).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText("e.g., GPT, ChatGPT, API, announcement")
      ).toBeInTheDocument();
    });
  });

  it("submits new competitor form", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: [], total: 0 },
    });
    mockApi.api.post.mockResolvedValue({
      data: {
        id: 3,
        competitor_name: "Google AI",
        keywords: ["Gemini", "Bard"],
        description: "Google AI division",
        is_active: true,
        created_at: "2024-01-03T00:00:00Z",
      },
    });

    renderWithQueryClient(<WatchList />);

    // Open form
    fireEvent.click(screen.getByText("Add Competitor"));

    await waitFor(() => {
      const nameInput = screen.getByPlaceholderText(
        "e.g., OpenAI, Anthropic, Google"
      );
      const keywordsInput = screen.getByPlaceholderText(
        "e.g., GPT, ChatGPT, API, announcement"
      );
      const descriptionInput = screen.getByPlaceholderText(
        "Why are you monitoring this competitor?"
      );

      fireEvent.change(nameInput, { target: { value: "Google AI" } });
      fireEvent.change(keywordsInput, { target: { value: "Gemini, Bard" } });
      fireEvent.change(descriptionInput, {
        target: { value: "Google AI division" },
      });

      const submitButton = screen.getByText("Add Competitor");
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(mockApi.api.post).toHaveBeenCalledWith("/api/v1/watch/", {
        competitor_name: "Google AI",
        keywords: ["Gemini", "Bard"],
        description: "Google AI division",
      });
    });
  });

  it("generates impact card for competitor", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockWatchItems, total: 2 },
    });
    mockApi.api.post.mockResolvedValue({
      data: { id: 1, message: "Impact card generated" },
    });

    renderWithQueryClient(<WatchList />);

    await waitFor(() => {
      const generateButtons = screen.getAllByTitle("Generate Impact Card");
      fireEvent.click(generateButtons[0]);
    });

    await waitFor(() => {
      expect(mockApi.api.post).toHaveBeenCalledWith(
        "/api/v1/impact/watch/1/generate"
      );
    });
  });

  it("toggles competitor active status", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockWatchItems, total: 2 },
    });
    mockApi.api.post.mockResolvedValue({
      data: { ...mockWatchItems[1], is_active: true },
    });

    renderWithQueryClient(<WatchList />);

    await waitFor(() => {
      const activateButtons = screen.getAllByTitle("Activate");
      fireEvent.click(activateButtons[0]); // Activate the inactive item
    });

    await waitFor(() => {
      expect(mockApi.api.post).toHaveBeenCalledWith("/api/v1/watch/2/activate");
    });
  });

  it("deletes competitor", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockWatchItems, total: 2 },
    });
    mockApi.api.delete.mockResolvedValue({ data: {} });

    renderWithQueryClient(<WatchList />);

    await waitFor(() => {
      const deleteButtons = screen.getAllByTitle("Delete");
      fireEvent.click(deleteButtons[0]);
    });

    await waitFor(() => {
      expect(mockApi.api.delete).toHaveBeenCalledWith("/api/v1/watch/1");
    });
  });

  it("shows demo suggestions", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: [], total: 0 },
    });

    renderWithQueryClient(<WatchList />);

    await waitFor(() => {
      expect(screen.getByText("💡 Demo Suggestions")).toBeInTheDocument();
      expect(screen.getByText("+ OpenAI")).toBeInTheDocument();
      expect(screen.getByText("+ Anthropic")).toBeInTheDocument();
      expect(screen.getByText("+ Google AI")).toBeInTheDocument();
      expect(screen.getByText("+ Mistral AI")).toBeInTheDocument();
    });
  });

  it("fills form with demo suggestion", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: [], total: 0 },
    });

    renderWithQueryClient(<WatchList />);

    // Open form first
    fireEvent.click(screen.getByText("Add Competitor"));

    await waitFor(() => {
      const openAIButton = screen.getByText("+ OpenAI");
      fireEvent.click(openAIButton);

      const nameInput = screen.getByPlaceholderText(
        "e.g., OpenAI, Anthropic, Google"
      );
      expect(nameInput).toHaveValue("OpenAI");

      const keywordsInput = screen.getByPlaceholderText(
        "e.g., GPT, ChatGPT, API, announcement"
      );
      expect(keywordsInput).toHaveValue("GPT, ChatGPT, API");
    });
  });

  it("handles API errors gracefully", async () => {
    mockApi.api.get.mockRejectedValue(new Error("API Error"));

    renderWithQueryClient(<WatchList />);

    // Component should still render without crashing
    expect(screen.getByText("Competitor Watchlist")).toBeInTheDocument();
  });

  it("displays keywords as badges", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockWatchItems, total: 2 },
    });

    renderWithQueryClient(<WatchList />);

    await waitFor(() => {
      expect(screen.getByText("GPT")).toBeInTheDocument();
      expect(screen.getByText("ChatGPT")).toBeInTheDocument();
      expect(screen.getByText("API")).toBeInTheDocument();
      expect(screen.getByText("Claude")).toBeInTheDocument();
      expect(screen.getByText("AI assistant")).toBeInTheDocument();
    });
  });

  it("shows last checked timestamp", async () => {
    mockApi.api.get.mockResolvedValue({
      data: { items: mockWatchItems, total: 2 },
    });

    renderWithQueryClient(<WatchList />);

    await waitFor(() => {
      expect(screen.getByText(/Last checked:/)).toBeInTheDocument();
    });
  });
});
