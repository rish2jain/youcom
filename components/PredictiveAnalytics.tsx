"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  AlertTriangle,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

interface MarketData {
  market_overview: {
    total_competitive_activities: number;
    average_market_risk: number;
    market_temperature: string;
    unique_competitors: number;
  };
  top_competitors: Array<{
    name: string;
    activity_count: number;
    average_risk_score: number;
  }>;
  insights: string[];
}

interface CompetitorTrend {
  competitor: string;
  risk_trend: string;
  activity_frequency_per_week: number;
  average_risk_score: number;
  latest_risk_score: number;
  prediction: string;
}

interface ExecutiveSummary {
  key_metrics: {
    total_competitive_activities: number;
    market_temperature: string;
    unique_competitors_tracked: number;
    average_market_risk: number;
  };
  top_threats: Array<{
    name: string;
    activity_count: number;
    average_risk_score: number;
  }>;
  strategic_recommendations: Array<{
    priority: string;
    category: string;
    action: string;
    rationale: string;
  }>;
}

export function PredictiveAnalytics() {
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [executiveSummary, setExecutiveSummary] =
    useState<ExecutiveSummary | null>(null);
  const [selectedCompetitor, setSelectedCompetitor] = useState<string>("");
  const [competitorTrend, setCompetitorTrend] =
    useState<CompetitorTrend | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMarketData = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/v1/analytics/market-landscape");
      if (!response.ok) throw new Error("Failed to fetch market data");

      const data = await response.json();
      setMarketData(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load market data"
      );
    } finally {
      setLoading(false);
    }
  };

  const fetchExecutiveSummary = async () => {
    try {
      const response = await fetch("/api/v1/analytics/executive-summary");
      if (!response.ok) throw new Error("Failed to fetch executive summary");

      const data = await response.json();
      setExecutiveSummary(data.executive_summary);
    } catch (err) {
      console.error("Failed to load executive summary:", err);
    }
  };

  const fetchCompetitorTrend = async (competitor: string) => {
    if (!competitor) return;

    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/analytics/competitor-trends/${encodeURIComponent(competitor)}`
      );
      if (!response.ok) throw new Error("Failed to fetch competitor trend");

      const data = await response.json();
      setCompetitorTrend(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load competitor trend"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMarketData();
    fetchExecutiveSummary();
  }, []);

  const getTemperatureColor = (temperature: string) => {
    switch (temperature) {
      case "hot":
        return "text-red-600 bg-red-50";
      case "warm":
        return "text-orange-600 bg-orange-50";
      case "cool":
        return "text-blue-600 bg-blue-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "increasing":
        return <TrendingUp className="h-4 w-4 text-red-500" />;
      case "decreasing":
        return <TrendingDown className="h-4 w-4 text-green-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "bg-red-100 text-red-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "low":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (loading && !marketData) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading predictive analytics...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Predictive Analytics</h2>
        <Button onClick={fetchMarketData} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh Data"}
        </Button>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-red-600">
              <AlertTriangle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Market Overview</TabsTrigger>
          <TabsTrigger value="competitors">Competitor Trends</TabsTrigger>
          <TabsTrigger value="executive">Executive Summary</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {marketData && (
            <>
              {/* Market Overview Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Market Temperature
                    </CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <Badge
                      className={getTemperatureColor(
                        marketData.market_overview.market_temperature
                      )}
                    >
                      {marketData.market_overview.market_temperature.toUpperCase()}
                    </Badge>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Competitive Activities
                    </CardTitle>
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {marketData.market_overview.total_competitive_activities}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Average Risk Score
                    </CardTitle>
                    <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {marketData.market_overview.average_market_risk}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      Competitors Tracked
                    </CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {marketData.market_overview.unique_competitors}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Top Competitors Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Top Competitive Threats</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={marketData.top_competitors}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar
                        dataKey="average_risk_score"
                        fill="#ef4444"
                        name="Risk Score"
                      />
                      <Bar
                        dataKey="activity_count"
                        fill="#3b82f6"
                        name="Activity Count"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Market Insights */}
              <Card>
                <CardHeader>
                  <CardTitle>Market Insights</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {marketData.insights.map((insight, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-sm">{insight}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        <TabsContent value="competitors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Competitor Trend Analysis</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <input
                  type="text"
                  placeholder="Enter competitor name..."
                  value={selectedCompetitor}
                  onChange={(e) => setSelectedCompetitor(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                />
                <Button
                  onClick={() => fetchCompetitorTrend(selectedCompetitor)}
                >
                  Analyze Trend
                </Button>
              </div>

              {competitorTrend && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex items-center space-x-2">
                      {getTrendIcon(competitorTrend.risk_trend)}
                      <span className="font-medium">
                        Risk Trend: {competitorTrend.risk_trend}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium">
                        Activity: {competitorTrend.activity_frequency_per_week}
                        /week
                      </span>
                    </div>
                    <div>
                      <span className="font-medium">
                        Avg Risk: {competitorTrend.average_risk_score}
                      </span>
                    </div>
                  </div>

                  <Card className="bg-blue-50">
                    <CardContent className="pt-6">
                      <h4 className="font-medium mb-2">Prediction</h4>
                      <p className="text-sm">{competitorTrend.prediction}</p>
                    </CardContent>
                  </Card>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="executive" className="space-y-4">
          {executiveSummary && (
            <>
              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">
                      {
                        executiveSummary.key_metrics
                          .total_competitive_activities
                      }
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Total Activities
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <Badge
                      className={getTemperatureColor(
                        executiveSummary.key_metrics.market_temperature
                      )}
                    >
                      {executiveSummary.key_metrics.market_temperature.toUpperCase()}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-2">
                      Market Temperature
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">
                      {executiveSummary.key_metrics.unique_competitors_tracked}
                    </div>
                    <p className="text-xs text-muted-foreground">Competitors</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">
                      {executiveSummary.key_metrics.average_market_risk}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Avg Risk Score
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Strategic Recommendations */}
              <Card>
                <CardHeader>
                  <CardTitle>Strategic Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {executiveSummary.strategic_recommendations.map(
                      (rec, index) => (
                        <div key={index} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <Badge className={getPriorityColor(rec.priority)}>
                              {rec.priority.toUpperCase()} PRIORITY
                            </Badge>
                            <Badge variant="outline">{rec.category}</Badge>
                          </div>
                          <h4 className="font-medium mb-1">{rec.action}</h4>
                          <p className="text-sm text-gray-600">
                            {rec.rationale}
                          </p>
                        </div>
                      )
                    )}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
