import { NextRequest, NextResponse } from "next/server";

// Helper to get backend URL
const getBackendUrl = () => {
  const envUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765";
  // Always replace Docker hostname with localhost for server-side requests
  // (Server-side fetch can resolve backend:, but we prefer localhost for consistency)
  if (envUrl && envUrl.includes("backend:")) {
    return envUrl.replace(/backend:/g, "localhost:");
  }
  return envUrl;
};
const BACKEND_URL = getBackendUrl();

/**
 * Proxy route for /api/v1/news
 * Forwards requests to the FastAPI backend
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get("limit") || "10";
    
    // Try to forward to backend if there's a news endpoint
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/news?limit=${limit}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        return NextResponse.json(data);
      }
    } catch (backendError) {
      // Backend doesn't have this endpoint or is not available
      console.log("Backend news endpoint not available, returning empty response");
    }

    // Return empty response if backend doesn't have news endpoint
    // This matches the expected format from components
    return NextResponse.json(
      { items: [], total: 0 },
      { status: 200 }
    );
  } catch (error) {
    console.error("Error proxying news request:", error);
    // Return empty response on error to prevent frontend crashes
    return NextResponse.json(
      { items: [], total: 0 },
      { status: 200 }
    );
  }
}

