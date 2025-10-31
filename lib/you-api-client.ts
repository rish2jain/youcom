/**
 * You.com API Client - Centralized service for all You.com API interactions
 * Handles News, Search, Chat (Custom Agents), and ARI APIs
 */

interface YouAPIConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

interface NewsResponse {
  hits: Array<{
    title: string;
    url: string;
    snippet: string;
    published_date: string;
    source: string;
  }>;
}

interface SearchResponse {
  hits: Array<{
    title: string;
    url: string;
    snippets: string[];
    description: string;
  }>;
}

interface ChatResponse {
  answer: string;
  sources?: Array<{
    name: string;
    url: string;
    snippet: string;
  }>;
}

export class YouAPIClient {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;

  constructor(config: YouAPIConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || "https://api.you.com";
    this.timeout = config.timeout || 30000;
  }

  private async makeRequest(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        "X-API-Key": this.apiKey,
        "Content-Type": "application/json",
        ...options.headers,
      },
      signal: AbortSignal.timeout(this.timeout),
    });

    if (!response.ok) {
      throw new Error(
        `You.com API Error: ${response.status} ${response.statusText}`
      );
    }

    return response.json();
  }

  /**
   * News API - Real-time competitive news monitoring
   */
  async searchNews(
    query: string,
    options: {
      count?: number;
      offset?: number;
      freshness?: "day" | "week" | "month";
      country?: string;
    } = {}
  ): Promise<NewsResponse> {
    const params = new URLSearchParams({
      q: query,
      count: (options.count || 10).toString(),
      offset: (options.offset || 0).toString(),
      ...(options.freshness && { freshness: options.freshness }),
      ...(options.country && { country: options.country }),
    });

    return this.makeRequest(`/v1/news/search?${params}`);
  }

  /**
   * Search API - Context enrichment and background research
   */
  async search(
    query: string,
    options: {
      count?: number;
      offset?: number;
      safesearch?: "strict" | "moderate" | "off";
      country?: string;
    } = {}
  ): Promise<SearchResponse> {
    const params = new URLSearchParams({
      query: query,
      count: (options.count || 10).toString(),
      offset: (options.offset || 0).toString(),
      ...(options.safesearch && { safesearch: options.safesearch }),
      ...(options.country && { country: options.country }),
    });

    return this.makeRequest(`/v1/search?${params}`);
  }

  /**
   * Chat API - Custom Agents for impact analysis
   */
  async chat(
    query: string,
    options: {
      chat_mode?: "default" | "custom" | "research";
      model?: string;
      include_sources?: boolean;
    } = {}
  ): Promise<ChatResponse> {
    return this.makeRequest("/v1/chat", {
      method: "POST",
      body: JSON.stringify({
        query,
        chat_mode: options.chat_mode || "default",
        ...(options.model && { model: options.model }),
        include_sources: options.include_sources !== false,
      }),
    });
  }

  /**
   * ARI API - Deep research reports with 400+ sources
   */
  async generateReport(
    query: string,
    options: {
      report_type?:
        | "research_report"
        | "competitive_analysis"
        | "market_analysis";
      include_citations?: boolean;
    } = {}
  ): Promise<{
    report: string;
    sources: Array<{
      title: string;
      url: string;
      snippet: string;
      credibility_score: number;
    }>;
    metadata: {
      total_sources: number;
      processing_time_ms: number;
      confidence_score: number;
    };
  }> {
    return this.makeRequest("/v1/chat", {
      method: "POST",
      body: JSON.stringify({
        query: `Generate a comprehensive ${
          options.report_type || "research_report"
        } for: ${query}`,
        chat_mode: "research",
        include_sources: options.include_citations !== false,
      }),
    });
  }

  /**
   * Health check for all APIs
   */
  async healthCheck(): Promise<{
    news: boolean;
    search: boolean;
    chat: boolean;
    ari: boolean;
  }> {
    const results = {
      news: false,
      search: false,
      chat: false,
      ari: false,
    };

    try {
      await this.searchNews("test", { count: 1 });
      results.news = true;
    } catch (error) {
      console.warn("News API health check failed:", error);
    }

    try {
      await this.search("test", { count: 1 });
      results.search = true;
    } catch (error) {
      console.warn("Search API health check failed:", error);
    }

    try {
      await this.chat("test");
      results.chat = true;
    } catch (error) {
      console.warn("Chat API health check failed:", error);
    }

    try {
      await this.generateReport("test");
      results.ari = true;
    } catch (error) {
      console.warn("ARI API health check failed:", error);
    }

    return results;
  }
}

// Singleton instance
let youApiClient: YouAPIClient | null = null;

export function getYouAPIClient(): YouAPIClient {
  if (!youApiClient) {
    const apiKey =
      process.env.YOU_API_KEY || process.env.NEXT_PUBLIC_YOU_API_KEY;
    if (!apiKey) {
      throw new Error(
        "You.com API key not configured. Please set YOU_API_KEY or NEXT_PUBLIC_YOU_API_KEY environment variable."
      );
    }
    youApiClient = new YouAPIClient({ apiKey });
  }
  return youApiClient;
}

export default YouAPIClient;
