/**
 * React hook for fetching dashboard data from APIs
 * Provides alerts (impact cards) and recent research data
 */

import { useQuery } from "@tanstack/react-query";
import { backendApi } from "../api";

export interface DashboardAlert {
  id: string;
  company: string;
  riskScore: number;
  riskLevel: "high" | "medium" | "low" | "critical";
  timeAgo: string;
  summary: string;
}

export interface DashboardResearch {
  id: string;
  company: string;
  sources: number;
  summary: string;
  completedAt: string;
}

/**
 * Format timestamp as relative time (e.g., "2 minutes ago")
 */
function formatTimeAgo(date: Date | string): string {
  const now = new Date();
  const then = typeof date === "string" ? new Date(date) : date;
  const diffMs = now.getTime() - then.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffDays > 0) {
    return `${diffDays} ${diffDays === 1 ? "day" : "days"} ago`;
  } else if (diffHours > 0) {
    return `${diffHours} ${diffHours === 1 ? "hour" : "hours"} ago`;
  } else if (diffMinutes > 0) {
    return `${diffMinutes} ${diffMinutes === 1 ? "minute" : "minutes"} ago`;
  } else {
    return "just now";
  }
}

/**
 * Transform risk level to dashboard format
 */
function transformRiskLevel(
  riskLevel: string
): "high" | "medium" | "low" | "critical" {
  const normalized = riskLevel.toLowerCase();
  if (normalized === "critical") return "critical";
  if (normalized === "high") return "high";
  if (normalized === "medium") return "medium";
  return "low";
}

/**
 * Transform impact card to dashboard alert
 */
function transformImpactCardToAlert(card: any): DashboardAlert {
  // Get summary from key insights or explanation
  let summary = "";
  if (card.key_insights && card.key_insights.length > 0) {
    summary = card.key_insights[0];
  } else if (card.explainability?.reasoning) {
    summary = card.explainability.reasoning.substring(0, 150) + "...";
  } else if (card.explainability?.key_insights && card.explainability.key_insights.length > 0) {
    summary = card.explainability.key_insights[0];
  } else {
    summary = `Risk assessment for ${card.competitor_name}`;
  }

  return {
    id: String(card.id),
    company: card.competitor_name,
    riskScore: card.risk_score / 10, // Convert 0-100 to 0-10 scale
    riskLevel: transformRiskLevel(card.risk_level),
    timeAgo: formatTimeAgo(card.created_at),
    summary: summary.substring(0, 200), // Limit length
  };
}

/**
 * Transform company research to dashboard research
 */
function transformResearchToDashboard(research: any): DashboardResearch {
  return {
    id: String(research.id),
    company: research.company_name,
    sources: research.total_sources || 0,
    summary: research.summary || "Comprehensive competitive analysis report",
    completedAt: formatTimeAgo(research.created_at),
  };
}

/**
 * Hook to fetch dashboard alerts (top impact cards)
 */
export function useDashboardAlerts(limit: number = 3) {
  return useQuery<DashboardAlert[]>({
    queryKey: ["dashboardAlerts", limit],
    queryFn: async () => {
      try {
        const response = await backendApi.get(
          `/api/v1/impact/?limit=${limit}&skip=0&risk_level=high`
        );
        
        // If no high-risk items, get any risk level items
        let items = response.data?.items || [];
        if (items.length === 0) {
          const allResponse = await backendApi.get(
            `/api/v1/impact/?limit=${limit}&skip=0`
          );
          items = allResponse.data?.items || [];
        }

        // Sort by risk score descending and take top N
        const sorted = items
          .sort((a: any, b: any) => (b.risk_score || 0) - (a.risk_score || 0))
          .slice(0, limit);

        return sorted.map(transformImpactCardToAlert);
      } catch (error) {
        console.error("Error fetching dashboard alerts:", error);
        // Return empty array on error instead of throwing
        return [];
      }
    },
    staleTime: 30 * 1000, // 30 seconds - data is considered fresh for 30 seconds
    refetchInterval: 60 * 60 * 1000, // Auto-refresh every hour
    refetchOnWindowFocus: true, // Refresh when user returns to tab
    retry: 1,
  });
}

/**
 * Hook to fetch recent research data
 */
export function useDashboardResearch(limit: number = 3) {
  return useQuery<DashboardResearch[]>({
    queryKey: ["dashboardResearch", limit],
    queryFn: async () => {
      try {
        const response = await backendApi.get(
          `/api/v1/research/?limit=${limit}&skip=0`
        );
        
        // Research endpoint returns array directly
        const items = Array.isArray(response.data) ? response.data : [];
        
        // Sort by created_at descending and take top N
        const sorted = items
          .sort((a: any, b: any) => {
            const dateA = new Date(a.created_at || 0).getTime();
            const dateB = new Date(b.created_at || 0).getTime();
            return dateB - dateA;
          })
          .slice(0, limit);

        return sorted.map(transformResearchToDashboard);
      } catch (error) {
        console.error("Error fetching dashboard research:", error);
        // Return empty array on error instead of throwing
        return [];
      }
    },
    staleTime: 30 * 1000, // 30 seconds - data is considered fresh for 30 seconds
    refetchInterval: 60 * 60 * 1000, // Auto-refresh every hour
    refetchOnWindowFocus: true, // Refresh when user returns to tab
    retry: 1,
  });
}

/**
 * Combined hook for all dashboard data
 */
export function useDashboardData() {
  const alerts = useDashboardAlerts(3);
  const research = useDashboardResearch(3);

  const refetch = () => {
    alerts.refetch();
    research.refetch();
  };

  return {
    alerts: {
      data: alerts.data || [],
      isLoading: alerts.isLoading,
      error: alerts.error,
      refetch: alerts.refetch,
    },
    research: {
      data: research.data || [],
      isLoading: research.isLoading,
      error: research.error,
      refetch: research.refetch,
    },
    isLoading: alerts.isLoading || research.isLoading,
    hasError: !!alerts.error || !!research.error,
    refetch, // Combined refetch function
    dataUpdatedAt: Math.max(
      alerts.dataUpdatedAt || 0,
      research.dataUpdatedAt || 0
    ),
  };
}

