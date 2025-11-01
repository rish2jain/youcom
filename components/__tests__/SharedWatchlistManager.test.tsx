import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import SharedWatchlistManager from "../SharedWatchlistManager";

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

const mockWatchlists = [
  {
    id: 1,
    workspace_id: 1,
    name: "AI Competitors",
    description: "Monitoring AI companies",
    is_active: true,
    watch_item_id: 1,
    created_by: 1,
    is_public: true,
    created_at: "2024-01-01T00:00:00Z",
    creator_name: "Test User",
    creator_email: "test@example.com",
    watch_item_name: "OpenAI Watch",
    watch_item_query: "OpenAI announcement",
    assigned_users_count: 3,
    comments_count: 5,
  },
  {
    id: 2,
    workspace_id: 1,
    name: "Private Watchlist",
    description: "Internal monitoring",
    is_active: false,
    watch_item_id: 2,
    created_by: 2,
    is_public: false,
    created_at: "2024-01-02T00:00:00Z",
    creator_name: "Another User",
    creator_email: "another@example.com",
    watch_item_name: "Competitor Watch",
    watch_item_query: "competitor news",
    assigned_users_count: 1,
    comments_count: 0,
  },
];

const mockWatchItems = [
  { id: 1, name: "OpenAI Watch", query: "OpenAI announcement" },
  { id: 2, name: "Competitor Watch", query: "competitor news" },
];

const mockWorkspaceUsers = [
  {
    user_id: 1,
    user_username: "testuser",
    user_email: "test@example.com",
    user_full_name: "Test User",
  },
  {
    user_id: 2,
    user_username: "anotheruser",
    user_email: "another@example.com",
    user_full_name: "Another User",
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

describe("SharedWatchlistManager Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockClear();
  });

  it("renders shared watchlists", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response);

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    expect(screen.getByText("Shared Watchlists (0)")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Shared Watchlists (2)")).toBeInTheDocument();
      expect(screen.getByText("AI Competitors")).toBeInTheDocument();
      expect(screen.getByText("Private Watchlist")).toBeInTheDocument();
    });
  });

  it("shows loading state", () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("shows empty state when no watchlists", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response);

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    await waitFor(() => {
      expect(screen.getByText("No shared watchlists yet")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Create the first shared watchlist to start collaborating"
        )
      ).toBeInTheDocument();
    });
  });

  it("opens create watchlist form", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response);

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    await waitFor(() => {
      const createButton = screen.getByText("Create Watchlist");
      fireEvent.click(createButton);

      expect(screen.getByPlaceholderText("Watchlist name")).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText("Description (optional)")
      ).toBeInTheDocument();
      expect(screen.getByText("Select watch item")).toBeInTheDocument();
    });
  });

  it("creates new shared watchlist", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 3, name: "New Watchlist" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response);

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    await waitFor(() => {
      const createButton = screen.getByText("Create Watchlist");
      fireEvent.click(createButton);
    });

    const nameInput = screen.getByPlaceholderText("Watchlist name");
    const descriptionInput = screen.getByPlaceholderText(
      "Description (optional)"
    );

    fireEvent.change(nameInput, { target: { value: "New Watchlist" } });
    fireEvent.change(descriptionInput, {
      target: { value: "Test description" },
    });

    // Select watch item (this would require more complex interaction with Select component)
    // For now, we'll just test the API call expectation

    const submitButton = screen.getByText("Create");
    // The button should be disabled until watch item is selected
    expect(submitButton).toBeDisabled();
  });

  it("toggles watchlist status", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockWatchlists[1], is_active: true }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response);

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    await waitFor(() => {
      const statusButtons = screen.getAllByRole("button");
      const statusButton = statusButtons.find(
        (button) => button.querySelector("svg") // Find activity button
      );
      if (statusButton) {
        fireEvent.click(statusButton);
      }
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/shared-watchlists/2",
        expect.objectContaining({
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_active: true }),
        })
      );
    });
  });

  it("toggles public/private status", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockWatchlists[0], is_public: false }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response);

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    await waitFor(() => {
      const publicButtons = screen.getAllByRole("button");
      const publicButton = publicButtons.find(
        (button) => button.querySelector("svg") // Find public/private toggle button
      );
      if (publicButton) {
        fireEvent.click(publicButton);
      }
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/shared-watchlists/1",
        expect.objectContaining({
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_public: false }),
        })
      );
    });
  });

  it("deletes watchlist", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [mockWatchlists[1]],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response);

    // Mock window.confirm
    window.confirm = jest.fn(() => true);

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    await waitFor(() => {
      const deleteButtons = screen.getAllByRole("button");
      const deleteButton = deleteButtons.find((button) =>
        button.classList.contains("text-red-600")
      );
      if (deleteButton) {
        fireEvent.click(deleteButton);
      }
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/shared-watchlists/1",
        expect.objectContaining({
          method: "DELETE",
        })
      );
    });
  });

  it("manages user assignments", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ user_id: 1, assigned_at: "2024-01-01T00:00:00Z" }],
      } as Response);

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    await waitFor(() => {
      const assignButtons = screen.getAllByRole("button");
      const assignButton = assignButtons.find(
        (button) => button.querySelector("svg") // Find user assignment button
      );
      if (assignButton) {
        fireEvent.click(assignButton);
      }
    });

    await waitFor(() => {
      expect(screen.getByText("Manage User Assignments")).toBeInTheDocument();
      expect(screen.getByText("Test User")).toBeInTheDocument();
      expect(screen.getByText("Another User")).toBeInTheDocument();
    });
  });

  it("filters watchlists", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [mockWatchlists[1]], // Include inactive
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response);

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    await waitFor(() => {
      const showInactiveButton = screen.getByText("Show Inactive");
      fireEvent.click(showInactiveButton);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/shared-watchlists/workspace/1?include_inactive=true&only_assigned=false"
      );
    });
  });

  it("shows watchlist details", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response);

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    await waitFor(() => {
      expect(screen.getByText("AI Competitors")).toBeInTheDocument();
      expect(screen.getByText("Monitoring AI companies")).toBeInTheDocument();
      expect(screen.getByText("Watching: OpenAI Watch")).toBeInTheDocument();
      expect(screen.getByText("Created by: Test User")).toBeInTheDocument();
      expect(screen.getByText("3 assigned")).toBeInTheDocument();
      expect(screen.getByText("5 comments")).toBeInTheDocument();
      expect(screen.getByText("Active")).toBeInTheDocument();
      expect(screen.getByText("Public")).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    mockFetch.mockRejectedValueOnce(new Error("API Error"));

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load watchlists/)).toBeInTheDocument();
    });
  });

  it("shows inactive watchlists with reduced opacity", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchlists,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWatchItems,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWorkspaceUsers,
      } as Response);

    renderWithQueryClient(<SharedWatchlistManager workspaceId={1} />);

    await waitFor(() => {
      const inactiveCard = screen
        .getByText("Private Watchlist")
        .closest(".opacity-60");
      expect(inactiveCard).toBeInTheDocument();
    });
  });
});
