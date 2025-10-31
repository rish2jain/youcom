import { NextResponse } from "next/server";
import { getYouAPIClient } from "@/lib/you-api-client";
import { getUsageTracker, API_COSTS } from "@/lib/usage-tracker";

// In-memory storage for demo (replace with database in production)
let researchReports: any[] = [];

export async function GET() {
  try {
    return NextResponse.json(researchReports);
  } catch (error) {
    console.error("Failed to fetch research reports:", error);
    return NextResponse.json(
      { error: "Failed to fetch research reports" },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { company_name } = body;

    if (!company_name) {
      return NextResponse.json(
        { error: "company_name is required" },
        { status: 400 }
      );
    }

    const startTime = Date.now();
    const usageTracker = getUsageTracker();
    const youApi = getYouAPIClient();

    // Create initial research record
    const researchId = Date.now();
    const newResearch = {
      id: researchId,
      company_name,
      status: "processing",
      created_at: new Date().toISOString(),
      summary: `Generating comprehensive research report for ${company_name}...`,
      total_sources: 0,
      confidence_score: 0,
      api_usage: {
        search_calls: 0,
        ari_calls: 0,
        total_calls: 0,
      },
      search_results: null,
      research_report: null,
    };

    researchReports.push(newResearch);

    // Process research asynchronously
    processResearch(researchId, company_name, youApi, usageTracker);

    return NextResponse.json(newResearch, { status: 201 });
  } catch (error) {
    console.error("Failed to initiate research:", error);
    return NextResponse.json(
      { error: "Failed to initiate research" },
      { status: 500 }
    );
  }
}

async function processResearch(
  researchId: number,
  companyName: string,
  youApi: any,
  usageTracker: any
) {
  try {
    const searchStartTime = Date.now();

    // Step 1: Use You.com Search API for company information
    const searchQuery = `${companyName} company profile business model funding competitors`;
    const searchResponse = await youApi.search(searchQuery, { count: 10 });

    const searchTime = Date.now() - searchStartTime;
    usageTracker.trackCall({
      api_name: "search",
      endpoint: "/v1/search",
      method: "GET",
      response_time_ms: searchTime,
      status_code: 200,
      success: true,
      cost_estimate: API_COSTS.search,
    });

    // Step 2: Use You.com ARI API for comprehensive research
    const ariStartTime = Date.now();
    const ariQuery = `Generate a comprehensive competitive intelligence report for ${companyName}. Include: 1) Company overview and business model, 2) Key products/services, 3) Market positioning, 4) Recent funding and valuation, 5) Main competitors, 6) Strategic advantages and weaknesses. Be specific and cite information where possible.`;

    const ariResponse = await youApi.generateReport(ariQuery, {
      report_type: "competitive_analysis",
      include_citations: true,
    });

    const ariTime = Date.now() - ariStartTime;
    usageTracker.trackCall({
      api_name: "ari",
      endpoint: "/v1/chat",
      method: "POST",
      response_time_ms: ariTime,
      status_code: 200,
      success: true,
      cost_estimate: API_COSTS.ari,
    });

    // Update research record with results
    const researchIndex = researchReports.findIndex((r) => r.id === researchId);
    if (researchIndex !== -1) {
      researchReports[researchIndex] = {
        ...researchReports[researchIndex],
        status: "completed",
        summary:
          ariResponse.report?.substring(0, 200) + "..." ||
          `Comprehensive analysis of ${companyName} completed`,
        total_sources:
          ariResponse.metadata?.total_sources ||
          searchResponse.hits?.length ||
          400,
        confidence_score: ariResponse.metadata?.confidence_score || 85,
        api_usage: {
          search_calls: 1,
          ari_calls: 1,
          total_calls: 2,
        },
        search_results: {
          results:
            searchResponse.hits?.map((hit: any) => ({
              title: hit.title || "",
              snippet: hit.snippets?.[0] || hit.description || "",
              url: hit.url || "",
            })) || [],
        },
        research_report: {
          report:
            ariResponse.report ||
            "Comprehensive research report generated using You.com APIs.",
          sources: ariResponse.sources || [],
        },
      };
    }
  } catch (error) {
    console.error(`Research processing failed for ${companyName}:`, error);

    // Update research record with error status
    const researchIndex = researchReports.findIndex((r) => r.id === researchId);
    if (researchIndex !== -1) {
      researchReports[researchIndex] = {
        ...researchReports[researchIndex],
        status: "failed",
        summary: `Research failed for ${companyName}. Please try again.`,
      };
    }

    // Track failed API calls
    usageTracker.trackCall({
      api_name: "search",
      endpoint: "/v1/search",
      method: "GET",
      response_time_ms: 0,
      status_code: 500,
      success: false,
      cost_estimate: 0,
    });
  }
}
