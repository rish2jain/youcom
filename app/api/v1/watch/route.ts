import { NextResponse } from "next/server";
import { getYouAPIClient } from "@/lib/you-api-client";
import { getUsageTracker, API_COSTS } from "@/lib/usage-tracker";

// In-memory storage for demo (replace with database in production)
let watchItems: any[] = [];

export async function GET() {
  try {
    // If no items exist, return empty array (no fallback to mock data)
    return NextResponse.json({
      items: watchItems,
      total: watchItems.length,
    });
  } catch (error) {
    console.error("Failed to fetch watchlist:", error);
    return NextResponse.json(
      { error: "Failed to fetch watchlist" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const startTime = Date.now();
    const usageTracker = getUsageTracker();

    // Validate required fields
    if (!body.competitor_name) {
      return NextResponse.json(
        { error: "competitor_name is required" },
        { status: 400 }
      );
    }

    // Create new watch item
    const newItem = {
      id: Date.now(),
      competitor_name: body.competitor_name,
      keywords: Array.isArray(body.keywords)
        ? body.keywords
        : typeof body.keywords === "string"
        ? body.keywords.split(",").map((k: string) => k.trim())
        : [body.competitor_name],
      description:
        body.description ||
        `Monitoring ${body.competitor_name} for competitive intelligence`,
      created_at: new Date().toISOString(),
      is_active: true,
      last_checked: new Date().toISOString(),
      status: "active",
      latest_activity: null,
      impact_cards_generated: 0,
    };

    // Try to fetch initial news for this competitor using You.com News API
    try {
      const youApi = getYouAPIClient();
      const newsQuery = `${body.competitor_name} ${newItem.keywords.join(
        " "
      )} news`;

      const newsResponse = await youApi.searchNews(newsQuery, {
        count: 5,
        freshness: "week",
      });

      const responseTime = Date.now() - startTime;

      // Track API usage
      usageTracker.trackCall({
        api_name: "news",
        endpoint: "/v1/news/search",
        method: "GET",
        response_time_ms: responseTime,
        status_code: 200,
        success: true,
        cost_estimate: API_COSTS.news,
      });

      // Update item with latest activity if news found
      if (newsResponse.hits && newsResponse.hits.length > 0) {
        const latestNews = newsResponse.hits[0];
        (
          newItem as any
        ).latest_activity = `Latest: ${latestNews.title} - ${latestNews.source}`;
        newItem.last_checked = new Date().toISOString();
      }
    } catch (apiError) {
      console.warn(
        `Failed to fetch initial news for ${body.competitor_name}:`,
        apiError
      );

      // Track failed API call
      usageTracker.trackCall({
        api_name: "news",
        endpoint: "/v1/news/search",
        method: "GET",
        response_time_ms: Date.now() - startTime,
        status_code: 500,
        success: false,
        cost_estimate: 0,
      });

      // Continue without news data - don't fail the entire request
      (newItem as any).latest_activity =
        "Monitoring active - initial news fetch pending";
    }

    // Add to watchlist
    watchItems.push(newItem);

    return NextResponse.json(newItem, { status: 201 });
  } catch (error) {
    console.error("Failed to create watch item:", error);
    return NextResponse.json(
      { error: "Failed to create watch item" },
      { status: 500 }
    );
  }
}
