import { NextResponse } from "next/server";
import { getUsageTracker } from "@/lib/usage-tracker";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const range = (searchParams.get("range") || "24h") as
      | "24h"
      | "7d"
      | "30d"
      | "90d";

    const usageTracker = getUsageTracker();
    const metrics = usageTracker.getMetrics(range);
    const recentActivity = usageTracker.getRecentActivity(10);

    // Enhanced metrics with additional details
    const enhancedMetrics = {
      ...metrics,
      last_call_at:
        recentActivity.length > 0
          ? recentActivity[0].timestamp.toISOString()
          : null,
      last_generated_at: new Date().toISOString(),

      // API details for dashboard
      apis: {
        news: {
          requests: metrics.by_service.news || 0,
          success_rate: calculateSuccessRate(recentActivity, "news"),
          avg_response_time: calculateAvgResponseTime(recentActivity, "news"),
          cost: metrics.cost_breakdown.by_service.news || 0,
          description: "Real-time competitive news monitoring",
        },
        search: {
          requests: metrics.by_service.search || 0,
          success_rate: calculateSuccessRate(recentActivity, "search"),
          avg_response_time: calculateAvgResponseTime(recentActivity, "search"),
          cost: metrics.cost_breakdown.by_service.search || 0,
          description: "Context enrichment and background research",
        },
        chat: {
          requests: metrics.by_service.chat || 0,
          success_rate: calculateSuccessRate(recentActivity, "chat"),
          avg_response_time: calculateAvgResponseTime(recentActivity, "chat"),
          cost: metrics.cost_breakdown.by_service.chat || 0,
          description: "AI-powered impact analysis via Custom Agents",
        },
        ari: {
          requests: metrics.by_service.ari || 0,
          success_rate: calculateSuccessRate(recentActivity, "ari"),
          avg_response_time: calculateAvgResponseTime(recentActivity, "ari"),
          cost: metrics.cost_breakdown.by_service.ari || 0,
          description: "Deep research reports with 400+ sources",
        },
      },

      // Cost breakdown
      cost_breakdown: {
        total_cost: metrics.cost_breakdown.total_cost,
        projected_monthly:
          metrics.cost_breakdown.total_cost * (30 / getDaysInRange(range)),
        cost_per_request:
          metrics.total_calls > 0
            ? metrics.cost_breakdown.total_cost / metrics.total_calls
            : 0,
        budget_limit: 500.0,
        budget_used_percent: (metrics.cost_breakdown.total_cost / 500.0) * 100,
      },

      // Rate limits (estimated based on typical You.com limits)
      rate_limits: {
        news: {
          used: metrics.by_service.news || 0,
          limit: 10000,
          reset_time: getNextMonthStart(),
          usage_percent: ((metrics.by_service.news || 0) / 10000) * 100,
        },
        search: {
          used: metrics.by_service.search || 0,
          limit: 5000,
          reset_time: getNextMonthStart(),
          usage_percent: ((metrics.by_service.search || 0) / 5000) * 100,
        },
        chat: {
          used: metrics.by_service.chat || 0,
          limit: 2000,
          reset_time: getNextMonthStart(),
          usage_percent: ((metrics.by_service.chat || 0) / 2000) * 100,
        },
        ari: {
          used: metrics.by_service.ari || 0,
          limit: 1000,
          reset_time: getNextMonthStart(),
          usage_percent: ((metrics.by_service.ari || 0) / 1000) * 100,
        },
      },

      // Recent activity
      recent_activity: recentActivity.slice(0, 5).map((call) => ({
        timestamp: call.timestamp.toISOString(),
        api: call.api_name,
        endpoint: call.endpoint,
        status: call.success ? "success" : "error",
        response_time: call.response_time_ms,
        cost: call.cost_estimate,
      })),

      // Impact cards and company research counts (derived from activity)
      impact_cards: countByEndpoint(recentActivity, "/v1/impact"),
      company_research: countByEndpoint(recentActivity, "/v1/research"),
      total_sources: estimateTotalSources(recentActivity),
      average_processing_seconds: metrics.average_latency_ms / 1000,
    };

    return NextResponse.json(enhancedMetrics);
  } catch (error) {
    console.error("Failed to fetch API usage metrics:", error);
    return NextResponse.json(
      { error: "Failed to fetch API usage metrics" },
      { status: 500 }
    );
  }
}

function calculateSuccessRate(activity: any[], apiName: string): number {
  const apiCalls = activity.filter((call) => call.api_name === apiName);
  if (apiCalls.length === 0) return 100;

  const successfulCalls = apiCalls.filter((call) => call.success);
  return (successfulCalls.length / apiCalls.length) * 100;
}

function calculateAvgResponseTime(activity: any[], apiName: string): number {
  const apiCalls = activity.filter((call) => call.api_name === apiName);
  if (apiCalls.length === 0) return 0;

  const totalTime = apiCalls.reduce(
    (sum, call) => sum + call.response_time_ms,
    0
  );
  return totalTime / apiCalls.length;
}

function getDaysInRange(range: string): number {
  switch (range) {
    case "24h":
      return 1;
    case "7d":
      return 7;
    case "30d":
      return 30;
    case "90d":
      return 90;
    default:
      return 1;
  }
}

function getNextMonthStart(): string {
  const now = new Date();
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  return nextMonth.toISOString();
}

function countByEndpoint(activity: any[], endpoint: string): number {
  return activity.filter((call) => call.endpoint.includes(endpoint)).length;
}

function estimateTotalSources(activity: any[]): number {
  // Estimate based on ARI calls (400 sources each) + Search calls (10 sources each)
  const ariCalls = activity.filter((call) => call.api_name === "ari").length;
  const searchCalls = activity.filter(
    (call) => call.api_name === "search"
  ).length;
  return ariCalls * 400 + searchCalls * 10;
}
