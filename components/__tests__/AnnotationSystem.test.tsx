import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AnnotationSystem from "../AnnotationSystem";

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

const mockAnnotations = [
  {
    id: 1,
    user_id: 1,
    impact_card_id: 1,
    content: "This is an important insight",
    annotation_type: "insight",
    position: { x: 100, y: 200 },
    target_text: "Selected text",
    created_at: "2024-01-01T00:00:00Z",
    is_resolved: 0,
    user_name: "Test User",
    user_email: "test@example.com",
  },
  {
    id: 2,
    user_id: 1,
    impact_card_id: 1,
    content: "What about this concern?",
    annotation_type: "question",
    created_at: "2024-01-02T00:00:00Z",
    is_resolved: 1,
    resolved_by: 1,
    user_name: "Test User",
    user_email: "test@example.com",
    resolver_name: "Admin User",
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

describe("AnnotationSystem Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockClear();
  });

  it("renders annotations list", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnnotations,
    } as Response);

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

    expect(screen.getByText("Annotations (0)")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Annotations (2)")).toBeInTheDocument();
      expect(
        screen.getByText("This is an important insight")
      ).toBeInTheDocument();
      expect(screen.getByText("What about this concern?")).toBeInTheDocument();
    });
  });

  it("shows loading state", () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

    expect(document.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("shows empty state when no annotations", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response);

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

    await waitFor(() => {
      expect(screen.getByText("No annotations yet")).toBeInTheDocument();
      expect(
        screen.getByText("Add the first annotation to start collaborating")
      ).toBeInTheDocument();
    });
  });

  it("opens create annotation form", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response);

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

    await waitFor(() => {
      const addButton = screen.getByText("Add Annotation");
      fireEvent.click(addButton);

      expect(
        screen.getByPlaceholderText("Enter your annotation...")
      ).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText("Referenced text (optional)")
      ).toBeInTheDocument();
    });
  });

  it("creates new annotation", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ id: 3, content: "New annotation" }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          ...mockAnnotations,
          { id: 3, content: "New annotation" },
        ],
      } as Response);

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

    await waitFor(() => {
      const addButton = screen.getByText("Add Annotation");
      fireEvent.click(addButton);
    });

    const contentInput = screen.getByPlaceholderText(
      "Enter your annotation..."
    );
    const targetTextInput = screen.getByPlaceholderText(
      "Referenced text (optional)"
    );

    fireEvent.change(contentInput, { target: { value: "New annotation" } });
    fireEvent.change(targetTextInput, { target: { value: "Referenced text" } });

    const submitButton = screen.getByText("Add Annotation");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/annotations/?impact_card_id=1",
        expect.objectContaining({
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: "New annotation",
            annotation_type: "insight",
            target_text: "Referenced text",
          }),
        })
      );
    });
  });

  it("toggles resolved status", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAnnotations,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockAnnotations[0], is_resolved: 1 }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAnnotations,
      } as Response);

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

    await waitFor(() => {
      const resolveButtons = screen.getAllByRole("button");
      const resolveButton = resolveButtons.find(
        (button) => button.querySelector("svg") // Find button with check icon
      );
      if (resolveButton) {
        fireEvent.click(resolveButton);
      }
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/annotations/1",
        expect.objectContaining({
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_resolved: 1 }),
        })
      );
    });
  });

  it("deletes annotation", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAnnotations,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [mockAnnotations[1]],
      } as Response);

    // Mock window.confirm
    window.confirm = jest.fn(() => true);

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

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
        "/api/v1/annotations/1",
        expect.objectContaining({
          method: "DELETE",
        })
      );
    });
  });

  it("filters resolved annotations", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockAnnotations,
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [mockAnnotations[0]], // Only unresolved
      } as Response);

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

    await waitFor(() => {
      const hideResolvedButton = screen.getByText("Hide Resolved");
      fireEvent.click(hideResolvedButton);
    });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/v1/annotations/impact-card/1?include_resolved=false"
      );
    });
  });

  it("displays annotation types with correct styling", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnnotations,
    } as Response);

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Insight")).toBeInTheDocument();
      expect(screen.getByText("Question")).toBeInTheDocument();
      expect(screen.getByText("Resolved")).toBeInTheDocument();
    });
  });

  it("shows target text when available", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnnotations,
    } as Response);

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

    await waitFor(() => {
      expect(screen.getByText('"Selected text"')).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    mockFetch.mockRejectedValueOnce(new Error("API Error"));

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to load annotations/)
      ).toBeInTheDocument();
    });
  });

  it("shows user information", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnnotations,
    } as Response);

    renderWithQueryClient(<AnnotationSystem impactCardId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Test User")).toBeInTheDocument();
      expect(screen.getByText("Resolved by Admin User")).toBeInTheDocument();
    });
  });
});
