/**
 * API Usage Tracker - Tracks You.com API usage for metrics and cost monitoring
 */

interface APICall {
  id: string;
  api_name: "news" | "search" | "chat" | "ari";
  endpoint: string;
  method: string;
  response_time_ms: number;
  status_code: number;
  success: boolean;
  cost_estimate: number;
  timestamp: Date;
  user_id?: string;
  request_size?: number;
  response_size?: number;
}

interface UsageMetrics {
  total_calls: number;
  success_rate: number;
  average_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  by_service: Record<string, number>;
  cost_breakdown: {
    total_cost: number;
    by_service: Record<string, number>;
  };
  usage_last_24h: Array<{
    time: string;
    news: number;
    search: number;
    chat: number;
    ari: number;
  }>;
}

class UsageTracker {
  private calls: APICall[] = [];
  private readonly STORAGE_KEY = "you_api_usage_tracker";
  private readonly MAX_STORED_CALLS = 10000;

  constructor() {
    this.loadFromStorage();
  }

  /**
   * Track an API call
   */
  trackCall(call: Omit<APICall, "id" | "timestamp">): void {
    const apiCall: APICall = {
      ...call,
      id: this.generateId(),
      timestamp: new Date(),
    };

    this.calls.push(apiCall);

    // Keep only recent calls to prevent memory issues
    if (this.calls.length > this.MAX_STORED_CALLS) {
      this.calls = this.calls.slice(-this.MAX_STORED_CALLS);
    }

    this.saveToStorage();
  }

  /**
   * Get usage metrics for a time range
   */
  getMetrics(timeRange: "24h" | "7d" | "30d" | "90d" = "24h"): UsageMetrics {
    const now = new Date();
    const cutoff = new Date();

    switch (timeRange) {
      case "24h":
        cutoff.setHours(now.getHours() - 24);
        break;
      case "7d":
        cutoff.setDate(now.getDate() - 7);
        break;
      case "30d":
        cutoff.setDate(now.getDate() - 30);
        break;
      case "90d":
        cutoff.setDate(now.getDate() - 90);
        break;
    }

    const relevantCalls = this.calls.filter((call) => call.timestamp >= cutoff);

    if (relevantCalls.length === 0) {
      return this.getEmptyMetrics();
    }

    const totalCalls = relevantCalls.length;
    const successfulCalls = relevantCalls.filter((call) => call.success);
    const successRate = successfulCalls.length / totalCalls;

    const responseTimes = relevantCalls
      .map((call) => call.response_time_ms)
      .sort((a, b) => a - b);
    const averageLatency =
      responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length;
    const p95Index = Math.floor(responseTimes.length * 0.95);
    const p99Index = Math.floor(responseTimes.length * 0.99);

    const byService: Record<string, number> = {};
    const costByService: Record<string, number> = {};

    relevantCalls.forEach((call) => {
      byService[call.api_name] = (byService[call.api_name] || 0) + 1;
      costByService[call.api_name] =
        (costByService[call.api_name] || 0) + call.cost_estimate;
    });

    const totalCost = Object.values(costByService).reduce(
      (sum, cost) => sum + cost,
      0
    );

    return {
      total_calls: totalCalls,
      success_rate: successRate,
      average_latency_ms: averageLatency,
      p95_latency_ms: responseTimes[p95Index] || 0,
      p99_latency_ms: responseTimes[p99Index] || 0,
      by_service: byService,
      cost_breakdown: {
        total_cost: totalCost,
        by_service: costByService,
      },
      usage_last_24h: this.generateTimeSeriesData(relevantCalls, timeRange),
    };
  }

  /**
   * Get recent API activity
   */
  getRecentActivity(limit: number = 10): APICall[] {
    return this.calls.slice(-limit).reverse();
  }

  /**
   * Clear all tracking data
   */
  clear(): void {
    this.calls = [];
    this.saveToStorage();
  }

  /**
   * Export usage data
   */
  exportData(): APICall[] {
    return [...this.calls];
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private loadFromStorage(): void {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        this.calls = data.map((call: any) => ({
          ...call,
          timestamp: new Date(call.timestamp),
        }));
      }
    } catch (error) {
      console.warn("Failed to load usage tracking data:", error);
      this.calls = [];
    }
  }

  private saveToStorage(): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.calls));
    } catch (error) {
      console.warn("Failed to save usage tracking data:", error);
    }
  }

  private getEmptyMetrics(): UsageMetrics {
    return {
      total_calls: 0,
      success_rate: 0,
      average_latency_ms: 0,
      p95_latency_ms: 0,
      p99_latency_ms: 0,
      by_service: {},
      cost_breakdown: {
        total_cost: 0,
        by_service: {},
      },
      usage_last_24h: [],
    };
  }

  private generateTimeSeriesData(
    calls: APICall[],
    timeRange: string
  ): Array<{
    time: string;
    news: number;
    search: number;
    chat: number;
    ari: number;
  }> {
    const buckets: Record<string, Record<string, number>> = {};

    calls.forEach((call) => {
      let bucketKey: string;

      if (timeRange === "24h") {
        bucketKey = call.timestamp.toISOString().substr(0, 13) + ":00"; // Hour buckets
      } else if (timeRange === "7d") {
        bucketKey = call.timestamp.toISOString().substr(0, 10); // Day buckets
      } else {
        bucketKey = call.timestamp.toISOString().substr(0, 7); // Month buckets
      }

      if (!buckets[bucketKey]) {
        buckets[bucketKey] = { news: 0, search: 0, chat: 0, ari: 0 };
      }

      buckets[bucketKey][call.api_name]++;
    });

    return Object.entries(buckets)
      .map(([time, counts]) => ({ time, ...counts }))
      .sort((a, b) => a.time.localeCompare(b.time));
  }
}

// Singleton instance
let usageTracker: UsageTracker | null = null;

export function getUsageTracker(): UsageTracker {
  if (!usageTracker) {
    usageTracker = new UsageTracker();
  }
  return usageTracker;
}

// Cost estimation (approximate You.com API pricing)
export const API_COSTS = {
  news: 0.024, // per request
  search: 0.04, // per request
  chat: 0.098, // per request
  ari: 0.12, // per request
};

export default UsageTracker;
