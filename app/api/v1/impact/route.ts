import { NextRequest, NextResponse } from "next/server";

// Helper to get backend URL, handling Docker hostname for browser access
const getBackendUrl = () => {
  const envUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765";
  // Always replace Docker hostname with localhost for consistency
  // (Server-side fetch can resolve backend:, but we prefer localhost)
  if (envUrl && envUrl.includes("backend:")) {
    return envUrl.replace(/backend:/g, "localhost:");
  }
  return envUrl;
};
const BACKEND_URL = getBackendUrl();

/**
 * Proxy route for /api/v1/impact
 * Forwards requests to the FastAPI backend
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get("limit") || "100";
    const skip = searchParams.get("skip") || "0";
    const competitor = searchParams.get("competitor");
    const riskLevel = searchParams.get("risk_level");
    const minCredibility = searchParams.get("min_credibility");

    // Build query string
    const queryParams = new URLSearchParams({
      limit,
      skip,
    });
    
    if (competitor) queryParams.append("competitor", competitor);
    if (riskLevel) queryParams.append("risk_level", riskLevel);
    if (minCredibility) queryParams.append("min_credibility", minCredibility);

    const response = await fetch(
      `${BACKEND_URL}/api/v1/impact/?${queryParams.toString()}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      console.error(`Backend error: ${response.status} ${response.statusText}`);
      return NextResponse.json(
        { items: [], total: 0 },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error proxying impact request:", error);
    return NextResponse.json(
      { items: [], total: 0 },
      { status: 500 }
    );
  }
}

/**
 * POST /api/v1/impact
 * Proxy for generating impact cards
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${BACKEND_URL}/api/v1/impact/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
      return NextResponse.json(
        { error: errorData.detail || "Failed to generate impact card" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    console.error("Error proxying impact generation request:", error);
    return NextResponse.json(
      { error: "Failed to generate impact card" },
      { status: 500 }
    );
  }
}

