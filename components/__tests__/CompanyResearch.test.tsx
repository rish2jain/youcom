import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CompanyResearch } from "../CompanyResearch";
import * as api from "@/lib/api";

// Mock the API
jest.mock("@/lib/api");
const mockApi = api as jest.Mocked<typeof api>;

// Mock data
const mockCompanyResearch = [
  {
    id: 1,
    company_name: "Perplexity AI",
    search_results: {
      results: [
        {
          title: "Perplexity AI Company Overview",
          snippet: "AI-powered search engine revolutionizing information discovery",
          url: "https://perplexity.ai",
        },
        {
          title: "Perplexity Funding News",
          snippet: "Perplexity AI raises $70M in Series B funding",
          url: "https://news.example.com/perplexity-funding",
        },
      ],
    },
    research_report: {
      report: "Perplexity AI is a leading AI search company.\nFounded in 2022 by Aravind Srinivas.\nCompetes with Google and Bing in AI search space.\nHas raised over $100M in funding.\nFocused on conversational search experience.",
    },
    total_sources: 42,
    api_usage: {
      search_calls: 1,
      ari_calls: 1,
      total_calls: 2,
    },
    created_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    company_name: "Stripe",
    search_results: {
      results: [
        {
          title: "Stripe Payment Platform",
          snippet: "Online payment processing for internet businesses",
          url: "https://stripe.com",
        },
      ],
    },
    research_report: {
      report: "Stripe is a payment processing platform.\nFounded by Patrick and John Collison.\nValued at $95 billion.\nServes millions of businesses worldwide.",
    },
    total_sources: 58,
    api_usage: {
      search_calls: 1,
      ari_calls: 1,
      total_calls: 2,
    },
    created_at: "2024-01-02T00:00:00Z",
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

describe("CompanyResearch Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders company research form", () => {
    mockApi.api.get.mockResolvedValue({ data: [] });

    renderWithQueryClient(<CompanyResearch />);

    expect(screen.getByText("Company Research")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Enter any company name/)).toBeInTheDocument();
    expect(screen.getByText("Research Company")).toBeInTheDocument();
  });

  it("displays recent research list", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockCompanyResearch });

    renderWithQueryClient(<CompanyResearch />);

    expect(screen.getByText("Recent Research")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Perplexity AI")).toBeInTheDocument();
      expect(screen.getByText("Stripe")).toBeInTheDocument();
      expect(screen.getByText("42 sources •")).toBeInTheDocument();
      expect(screen.getByText("58 sources •")).toBeInTheDocument();
    });
  });

  it("shows empty state when no research", async () => {
    mockApi.api.get.mockResolvedValue({ data: [] });

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      expect(screen.getByText("No company research yet.")).toBeInTheDocument();
      expect(
        screen.getByText("Research your first company to see You.com APIs in action!")
      ).toBeInTheDocument();
    });
  });

  it("shows loading state", () => {
    mockApi.api.get.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithQueryClient(<CompanyResearch />);

    expect(
      document.querySelector(".animate-pulse")
    ).toBeInTheDocument();
  });

  it("submits research query", async () => {
    mockApi.api.get.mockResolvedValue({ data: [] });
    mockApi.api.post.mockResolvedValue({
      data: mockCompanyResearch[0],
    });

    renderWithQueryClient(<CompanyResearch />);

    const input = screen.getByPlaceholderText(/Enter any company name/);
    const submitButton = screen.getByText("Research Company");

    fireEvent.change(input, { target: { value: "Perplexity AI" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockApi.api.post).toHaveBeenCalledWith("/api/v1/research/company", {
        company_name: "Perplexity AI",
      });
    });
  });

  it("shows loading state during research", async () => {
    mockApi.api.get.mockResolvedValue({ data: [] });
    mockApi.api.post.mockImplementation(() => new Promise(() => {})); // Never resolves

    renderWithQueryClient(<CompanyResearch />);

    const input = screen.getByPlaceholderText(/Enter any company name/);
    const submitButton = screen.getByText("Research Company");

    fireEvent.change(input, { target: { value: "Test Company" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Researching...")).toBeInTheDocument();
      expect(
        screen.getByText(/Processing with You.com APIs/)
      ).toBeInTheDocument();
    });
  });

  it("displays company suggestions", async () => {
    mockApi.api.get.mockResolvedValue({ data: [] });

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      expect(screen.getByText("💡 Try These Companies")).toBeInTheDocument();
      expect(screen.getByText("Perplexity AI")).toBeInTheDocument();
      expect(screen.getByText("Stripe")).toBeInTheDocument();
      expect(screen.getByText("Notion")).toBeInTheDocument();
      expect(screen.getByText("Figma")).toBeInTheDocument();
    });
  });

  it("fills input with suggestion on click", async () => {
    mockApi.api.get.mockResolvedValue({ data: [] });

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      const suggestionButton = screen.getByText("Perplexity AI");
      fireEvent.click(suggestionButton);

      const input = screen.getByPlaceholderText(/Enter any company name/);
      expect(input).toHaveValue("Perplexity AI");
    });
  });

  it("opens research detail on click", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockCompanyResearch });

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      const researchItem = screen.getByText("Perplexity AI");
      fireEvent.click(researchItem.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByText("Perplexity AI - Research Report")).toBeInTheDocument();
      expect(screen.getByText("Export PDF")).toBeInTheDocument();
      expect(screen.getByText("Share")).toBeInTheDocument();
    });
  });

  it("displays API usage statistics in detail view", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockCompanyResearch });

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      const researchItem = screen.getByText("Perplexity AI");
      fireEvent.click(researchItem.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByText("Total Sources")).toBeInTheDocument();
      expect(screen.getByText("Search API Calls")).toBeInTheDocument();
      expect(screen.getByText("ARI API Calls")).toBeInTheDocument();
      expect(screen.getByText("42")).toBeInTheDocument(); // total sources
      expect(screen.getByText("1")).toBeInTheDocument(); // search calls
    });
  });

  it("displays search results in detail view", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockCompanyResearch });

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      const researchItem = screen.getByText("Perplexity AI");
      fireEvent.click(researchItem.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByText("Company Overview (You.com Search API)")).toBeInTheDocument();
      expect(screen.getByText("Perplexity AI Company Overview")).toBeInTheDocument();
      expect(
        screen.getByText(/AI-powered search engine revolutionizing/)
      ).toBeInTheDocument();
    });
  });

  it("displays research report in detail view", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockCompanyResearch });

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      const researchItem = screen.getByText("Perplexity AI");
      fireEvent.click(researchItem.closest("div")!);
    });

    await waitFor(() => {
      expect(
        screen.getByText("Deep Research Analysis (You.com ARI API)")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Perplexity AI is a leading AI search company/)
      ).toBeInTheDocument();
    });
  });

  it("closes detail view on X button click", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockCompanyResearch });

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      const researchItem = screen.getByText("Perplexity AI");
      fireEvent.click(researchItem.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByText("Perplexity AI - Research Report")).toBeInTheDocument();
    });

    const closeButton = screen.getByText("✕");
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(
        screen.queryByText("Perplexity AI - Research Report")
      ).not.toBeInTheDocument();
    });
  });

  it("shows error message on research failure", async () => {
    mockApi.api.get.mockResolvedValue({ data: [] });
    mockApi.api.post.mockRejectedValue(new Error("API request failed"));

    renderWithQueryClient(<CompanyResearch />);

    const input = screen.getByPlaceholderText(/Enter any company name/);
    const submitButton = screen.getByText("Research Company");

    fireEvent.change(input, { target: { value: "Test Company" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("prevents empty search submission", async () => {
    mockApi.api.get.mockResolvedValue({ data: [] });

    renderWithQueryClient(<CompanyResearch />);

    const submitButton = screen.getByText("Research Company");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByText("Enter a company name to research.")).toBeInTheDocument();
    });

    expect(mockApi.api.post).not.toHaveBeenCalled();
  });

  it("handles API errors gracefully when loading research", async () => {
    mockApi.api.get.mockRejectedValue(new Error("Failed to load research"));

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      expect(screen.getByText("Unable to load research history.")).toBeInTheDocument();
    });

    // Component should still render
    expect(screen.getByText("Company Research")).toBeInTheDocument();
  });

  it("displays You.com API badges", () => {
    mockApi.api.get.mockResolvedValue({ data: [] });

    renderWithQueryClient(<CompanyResearch />);

    expect(screen.getByText(/Search \+ ARI APIs/)).toBeInTheDocument();
  });

  it("shows API usage details in research card", async () => {
    mockApi.api.get.mockResolvedValue({ data: mockCompanyResearch });

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      expect(screen.getByText("2 API calls")).toBeInTheDocument();
      expect(screen.getByText(/Search: 1/)).toBeInTheDocument();
      expect(screen.getByText(/ARI: 1/)).toBeInTheDocument();
    });
  });

  it("handles array format research report", async () => {
    const researchWithArrayReport = {
      ...mockCompanyResearch[0],
      research_report: {
        report: [
          { text: "First section of report" },
          { content: "Second section of report" },
        ],
      },
    };

    mockApi.api.get.mockResolvedValue({ data: [researchWithArrayReport] });

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      const researchItem = screen.getByText("Perplexity AI");
      fireEvent.click(researchItem.closest("div")!);
    });

    await waitFor(() => {
      expect(screen.getByText(/First section of report/)).toBeInTheDocument();
    });
  });

  it("limits displayed recent research to 5 items", async () => {
    const manyResearchItems = Array.from({ length: 10 }, (_, i) => ({
      ...mockCompanyResearch[0],
      id: i + 1,
      company_name: `Company ${i + 1}`,
    }));

    mockApi.api.get.mockResolvedValue({ data: manyResearchItems });

    renderWithQueryClient(<CompanyResearch />);

    await waitFor(() => {
      // Should only show first 5
      expect(screen.getByText("Company 1")).toBeInTheDocument();
      expect(screen.getByText("Company 5")).toBeInTheDocument();
      expect(screen.queryByText("Company 6")).not.toBeInTheDocument();
    });
  });
});
