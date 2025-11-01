import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import CommentThreads from "../CommentThreads";

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

const mockThreads = [
  {
    id: 1,
    user_id: 1,
    impact_card_id: 1,
    content: "This is a parent comment",
    created_at: "2024-01-01T00:00:00Z",
    is_edited: 0,
    user_name: "Test User",
    user_email: "test@example.com",
    replies_count: 2,
    replies: [
      {
        id: 2,
        user_id: 2,
        impact_card_id: 1,
        content: "This is a reply",
        parent_comment_id: 1,
        created_at: "2024-01-01T01:00:00Z",
        is_edited: 0,
        user_name: "Another User",
        user_email: "another@example.com",
        replies_count: 0,
        replies: [],
      },
      {
        id: 3,
        user_id: 1,
        impact_card_id: 1,
        content: "Another reply",
        parent_comment_id: 1,
        created_at: "2024-01-01T02:00:00Z",
        is_edited: 1,
        user_name: "Test User",
        user_email: "test@example.com",
        replies_count: 0,
        replies: [],
      },
    ],
  },
];

const mockConflicts = [
  {
    id: 1,
    conflict_type: "interpretation",
    confidence_score: 85,
    description: "Potential interpretation conflict detected",
    is_resolved: false,
    detected_at: "2024-01-01T00:00:00Z",
    comment_1: {
      id: 1,
      content: "This is a great opportunity",
      author: "User A",
    },
    comment_2: {
      id: 2,
      content: "I disagree, this is not important",
      author: "User B",
    },
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

describe("CommentThreads Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockClear();
  });

  it("renders comment threads", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockThreads,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

    expect(screen.getByText("Discussion (0 threads)")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Discussion (1 threads)")).toBeInTheDocument();
      expect(screen.getByText("This is a parent comment")).toBeInTheDocument();
    });
  });

  it("shows loading state", () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

    expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("shows empty state when no comments", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

    await waitFor(() => {
      expect(screen.getByText("No comments yet")).toBeInTheDocument();
      expect(
        screen.getByText("Start the discussion by posting the first comment")
      ).toBeInTheDocument();
    });
  });

  it("creates new comment", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 4, content: "New comment" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockThreads,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

    await waitFor(() => {
      const textarea = screen.getByPlaceholderText("Start a new discussion...");
      fireEvent.change(textarea, { target: { value: "New comment" } });

      const postButton = screen.getByText("Post Comment");
      fireEvent.click(postButton);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/comments/?impact_card_id=1",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: "New comment" }),
        })
      );
    });
  });

  it("expands and collapses reply threads", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockThreads,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

    await waitFor(() => {
      const expandButton = screen.getByText("2 replies");
      fireEvent.click(expandButton);

      expect(screen.getByText("This is a reply")).toBeInTheDocument();
      expect(screen.getByText("Another reply")).toBeInTheDocument();
    });
  });

  it("creates reply to comment", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockThreads,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 5, content: "Reply comment" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockThreads,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

    await waitFor(() => {
      const replyButtons = screen.getAllByRole("button");
      const replyButton = replyButtons.find(
        (button) =>
          button.querySelector("svg") &&
          button.getAttribute("title") === "Reply"
      );
      if (replyButton) {
        fireEvent.click(replyButton);
      }
    });

    await waitFor(() => {
      const replyTextarea = screen.getByPlaceholderText("Write a reply...");
      fireEvent.change(replyTextarea, { target: { value: "Reply comment" } });

      const sendButton = screen.getByText("Reply");
      fireEvent.click(sendButton);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/comments/?impact_card_id=1",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: "Reply comment",
            parent_comment_id: 1,
          }),
        })
      );
    });
  });

  it("edits comment", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockThreads,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 1, content: "Updated comment" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockThreads,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

    await waitFor(() => {
      const editButtons = screen.getAllByRole("button");
      const editButton = editButtons.find(
        (button) => button.querySelector("svg") // Find edit button
      );
      if (editButton) {
        fireEvent.click(editButton);
      }
    });

    await waitFor(() => {
      const editTextarea = screen.getByDisplayValue("This is a parent comment");
      fireEvent.change(editTextarea, { target: { value: "Updated comment" } });

      const updateButton = screen.getByText("Update");
      fireEvent.click(updateButton);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/comments/1",
        expect.objectContaining({
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: "Updated comment" }),
        })
      );
    });
  });

  it("deletes comment", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockThreads,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

    // Mock window.confirm
    window.confirm = jest.fn(() => true);

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

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
        "/api/v1/comments/1",
        expect.objectContaining({
          method: "DELETE",
        })
      );
    });
  });

  it("displays conflicts", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockConflicts,
      } as Response);

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

    await waitFor(() => {
      expect(screen.getByText("1 conflicts detected")).toBeInTheDocument();
      expect(
        screen.getByText("Conflicting Interpretations Detected")
      ).toBeInTheDocument();
      expect(screen.getByText("interpretation conflict")).toBeInTheDocument();
      expect(screen.getByText("85% confidence")).toBeInTheDocument();
    });
  });

  it("shows user information and timestamps", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockThreads,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Test User")).toBeInTheDocument();
      expect(screen.getByText("1/1/2024")).toBeInTheDocument(); // Date formatting may vary
    });
  });

  it("shows edited badge for edited comments", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockThreads,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

    await waitFor(() => {
      const expandButton = screen.getByText("2 replies");
      fireEvent.click(expandButton);

      expect(screen.getByText("Edited")).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    mockFetch.mockRejectedValueOnce(new Error("API Error"));

    renderWithQueryClient(<CommentThreads impactCardId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load comments/)).toBeInTheDocument();
    });
  });

  it("works with different context types", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

    renderWithQueryClient(<CommentThreads sharedWatchlistId={1} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/comments/threads?shared_watchlist_id=1"
      );
    });
  });
});
