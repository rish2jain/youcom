"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  LineChart,
  Line,
  Legend,
} from "recharts";
import {
  AlertTriangle,
  TrendingUp,
  Clock,
  ExternalLink,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import { getSocket } from "@/lib/socket";

interface ImpactCard {
  id: number;
  competitor_name: string;
  risk_score: number;
  risk_level: string;
  confidence_score: number;
  impact_areas: Array<{
    area: string;
    impact_score: number;
    description: string;
  }>;
  key_insights: string[];
  recommended_actions?: RankedAction[];
  next_steps_plan?: RankedAction[];
  total_sources: number;
  source_breakdown: {
    news_articles: number;
    search_results: number;
    research_citations: number;
  };
  api_usage: {
    news_calls: number;
    search_calls: number;
    chat_calls: number;
    ari_calls: number;
    total_calls: number;
  };
  created_at: string;
  processing_time?: string;
  credibility_score: number;
  requires_review: boolean;
  source_quality?: SourceQuality;
  explainability?: Explainability;
}

interface SourceQuality {
  score: number;
  tiers: Record<string, number>;
  total: number;
  top_sources: Array<{ title?: string; url: string; type?: string }>;
}

interface Explainability {
  reasoning?: string;
  impact_areas?: ImpactCard["impact_areas"];
  key_insights?: string[];
  source_summary?: Record<string, any>;
}

interface RankedAction {
  action: string;
  priority: string;
  timeline: string;
  owner: string;
  okr_goal: string;
  impact_score: number;
  effort_score: number;
  score: number;
  evidence: Array<{ title?: string; url: string }>;
  index: number;
}

interface ProgressEntry {
  status: "started" | "step" | "completed" | "failed";
  message: string;
  timestamp: string;
  competitor: string;
}

export function ImpactCardDisplay() {
  const [selectedCard, setSelectedCard] = useState<ImpactCard | null>(null);
  const [showRawData, setShowRawData] = useState(false);
  const [generateForm, setGenerateForm] = useState({
    competitor_name: "",
    keywords: "",
  });
  const [activeCompetitor, setActiveCompetitor] = useState<string | null>(null);
  const [progressLog, setProgressLog] = useState<ProgressEntry[]>([]);
  const [formError, setFormError] = useState<string | null>(null);
  const competitorRef = useRef<string | null>(null);
  const [credibilityFilter, setCredibilityFilter] = useState(0);
  const [showExplainability, setShowExplainability] = useState(false);
  const [comparisonData, setComparisonData] = useState<Array<{ created_at: string | null; risk_score: number; credibility_score: number }>>([]);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const normalizedPlan = useMemo(() => {
    if (!selectedCard) return [] as RankedAction[];
    const plan = selectedCard.next_steps_plan ?? selectedCard.recommended_actions ?? [];
    return plan.map((action, idx) => ({
      ...action,
      owner: action.owner ?? "Strategy Team",
      okr_goal: action.okr_goal ?? "Drive competitive differentiation",
      impact_score: action.impact_score ?? 60,
      effort_score: action.effort_score ?? 60,
      score:
        action.score ?? (action.impact_score ?? 60) - ((action.effort_score ?? 60) / 2),
      evidence: action.evidence ?? [],
      index: action.index ?? idx,
    }));
  }, [selectedCard]);

  // Fetch impact cards
  const {
    data: impactCards,
    isLoading,
    error: impactError,
  } = useQuery({
    queryKey: ["impactCards", credibilityFilter],
    queryFn: () =>
      api
        .get("/api/v1/impact/", {
          params:
            credibilityFilter > 0
              ? { min_credibility: credibilityFilter }
              : undefined,
        })
        .then((res) => res.data.items),
  });

  const { data: notificationLogs } = useQuery({
    queryKey: ["notificationLogs"],
    queryFn: () => api.get("/api/v1/notifications/logs").then((res) => res.data.items),
    staleTime: 60_000,
  });

  const impactErrorMessage = impactError
    ? impactError instanceof Error
      ? impactError.message
      : "Unable to load Impact Cards."
    : null;

  // Generate new impact card
  const generateMutation = useMutation({
    mutationFn: (data: { competitor_name: string; keywords: string }) =>
      api.post("/api/v1/impact/generate", {
        ...data,
        keywords: data.keywords
          .split(",")
          .map((k: string) => k.trim())
          .filter(Boolean),
      }),
    onMutate: (variables) => {
      const competitor = variables.competitor_name.trim();
      setFormError(null);
      if (competitor) {
        setActiveCompetitor(competitor);
        competitorRef.current = competitor;
        setProgressLog([
          {
            status: "started",
            message: `Generating Impact Card for ${competitor}...`,
            timestamp: new Date().toISOString(),
            competitor,
          },
        ]);
      }
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["impactCards"] });
      setSelectedCard(data.data);
      setGenerateForm({ competitor_name: "", keywords: "" });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "Failed to generate Impact Card. Please try again.";
      setFormError(message);
      setProgressLog((prev) => [
        ...prev,
        {
          status: "failed",
          message,
          timestamp: new Date().toISOString(),
          competitor: competitorRef.current || "",
        },
      ]);
    },
  });

  const feedbackMutation = useMutation({
    mutationFn: (payload: {
      impact_card_id: number;
      action_index: number;
      sentiment: "up" | "down";
    }) => api.post("/api/v1/feedback/impact", payload),
    onSuccess: () => {
      setFeedbackMessage("Thanks for the feedback!");
      setTimeout(() => setFeedbackMessage(null), 3000);
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to record feedback right now.";
      setFeedbackMessage(message);
    },
  });

  useEffect(() => {
    const socket = getSocket();
    socket.emit("join_room", { room: "impact_cards" });

    const resolveStepMessage = (step: string, payload: Record<string, unknown>) => {
      switch (step) {
        case "news":
          return `News ingested (${payload.articles ?? 0} articles)`;
        case "search":
          return `Search context enriched (${payload.results ?? 0} results)`;
        case "analysis":
          return `Impact analysis scored (${payload.risk_score ?? "n/a"})`;
        case "research":
          return `Research synthesized (${payload.citations ?? 0} citations)`;
        default:
          return step;
      }
    };

    const handleStarted = (payload: { competitor: string }) => {
      const competitor = payload.competitor;
      setActiveCompetitor(competitor);
      competitorRef.current = competitor;
      setProgressLog([
        {
          status: "started",
          message: `Generating Impact Card for ${competitor}...`,
          timestamp: new Date().toISOString(),
          competitor,
        },
      ]);
    };

    const handleStep = (payload: { competitor: string; step: string }) => {
      const competitor = payload.competitor;
      if (competitorRef.current && competitorRef.current !== competitor) {
        return;
      }

      const message = resolveStepMessage(payload.step, payload);
      setProgressLog((prev) =>
        [...prev, {
          status: "step" as const,
          message,
          timestamp: new Date().toISOString(),
          competitor,
        }].slice(-6)
      );
    };

    const handleCompleted = (payload: {
      competitor: string;
      risk_score: number;
      risk_level: string;
      total_sources: number;
    }) => {
      const competitor = payload.competitor;
      if (competitorRef.current && competitorRef.current !== competitor) {
        return;
      }

      setProgressLog((prev) => [
        ...prev,
        {
          status: "completed",
          message: `Completed: Risk ${payload.risk_level} (${payload.risk_score}/100) with ${payload.total_sources} sources`,
          timestamp: new Date().toISOString(),
          competitor,
        },
      ]);
      competitorRef.current = null;
    };

    const handleFailed = (payload: { competitor: string; error: string }) => {
      const competitor = payload.competitor;
      if (competitorRef.current && competitorRef.current !== competitor) {
        return;
      }

      setProgressLog((prev) => [
        ...prev,
        {
          status: "failed",
          message: `Generation failed: ${payload.error}`,
          timestamp: new Date().toISOString(),
          competitor,
        },
      ]);
      competitorRef.current = null;
    };

    socket.on("impact_generation_started", handleStarted);
    socket.on("impact_generation_step", handleStep);
    socket.on("impact_generation_completed", handleCompleted);
    socket.on("impact_generation_failed", handleFailed);

    return () => {
      socket.off("impact_generation_started", handleStarted);
      socket.off("impact_generation_step", handleStep);
      socket.off("impact_generation_completed", handleCompleted);
      socket.off("impact_generation_failed", handleFailed);
    };
  }, []);

  useEffect(() => {
    if (!selectedCard) {
      setComparisonData([]);
      setFeedbackMessage(null);
      setShowExplainability(false);
      return;
    }

    setComparisonLoading(true);
    api
      .get("/api/v1/impact/comparison", {
        params: { competitors: selectedCard.competitor_name },
      })
      .then((res) => {
        const series = res.data.series?.[selectedCard.competitor_name] ?? [];
        setComparisonData(series);
      })
      .catch(() => {
        setComparisonData([]);
      })
      .finally(() => setComparisonLoading(false));
  }, [selectedCard]);

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case "critical":
        return "text-red-600 bg-red-100";
      case "high":
        return "text-orange-600 bg-orange-100";
      case "medium":
        return "text-yellow-600 bg-yellow-100";
      case "low":
        return "text-green-600 bg-green-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getRiskGaugeColor = (score: number) => {
    if (score >= 80) return "#ef4444"; // red
    if (score >= 60) return "#f97316"; // orange
    if (score >= 40) return "#eab308"; // yellow
    return "#22c55e"; // green
  };

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault();
    const competitor = generateForm.competitor_name.trim();
    if (competitor.length < 2) {
      setFormError("Competitor name must be at least 2 characters.");
      return;
    }

    setFormError(null);
    generateMutation.mutate({
      competitor_name: competitor,
      keywords: generateForm.keywords.trim(),
    });
  };

  const handleFeedback = (actionIndex: number, sentiment: "up" | "down") => {
    if (!selectedCard) return;
    feedbackMutation.mutate({
      impact_card_id: selectedCard.id,
      action_index: actionIndex,
      sentiment,
    });
  };

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Impact Cards</h3>
        <div className="you-api-badge">
          <Zap className="w-3 h-3 inline mr-1" />
          You.com Powered
        </div>
      </div>

      {/* Generate Form */}
      <form
        onSubmit={handleGenerate}
        className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg"
      >
        <h4 className="font-medium text-gray-900 mb-3">
          🚀 Generate Impact Card
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <input
              type="text"
              value={generateForm.competitor_name}
              onChange={(e) =>
                setGenerateForm({
                  ...generateForm,
                  competitor_name: e.target.value,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Competitor name (e.g., OpenAI)"
              required
            />
          </div>
          <div>
            <input
              type="text"
              value={generateForm.keywords}
              onChange={(e) =>
                setGenerateForm({ ...generateForm, keywords: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Keywords (optional)"
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={generateMutation.isPending}
          className="mt-3 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
        >
          {generateMutation.isPending ? (
            <>
              <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
              <span>Generating with You.com APIs...</span>
            </>
          ) : (
            <>
              <Zap className="w-4 h-4" />
              <span>Generate Impact Card</span>
            </>
          )}
        </button>
        {generateMutation.isPending && (
          <div className="mt-2 text-sm text-blue-600">
            Processing: News → Search → Chat → ARI → Impact Card
          </div>
        )}
        {formError && (
          <div className="mt-2 text-sm text-red-600" role="alert">
            {formError}
          </div>
        )}
      </form>

      {progressLog.length > 0 && (
        <div className="mb-6 p-4 border border-blue-100 bg-blue-50 rounded-lg">
          <h5 className="text-sm font-semibold text-blue-700 mb-2">
            Live Generation Progress
          </h5>
          <ul className="space-y-1 text-sm text-blue-700">
            {progressLog.map((entry, index) => (
              <li key={`${entry.timestamp}-${index}`} className="flex items-start">
                <span className="mr-2 text-blue-500">•</span>
                <span>
                  <span className="font-medium capitalize">{entry.status}</span> —
                  {" "}
                  {entry.message}
                  <span className="ml-2 text-xs text-blue-400">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h4 className="text-sm font-semibold text-gray-700">
            Filter by credibility score
          </h4>
          <p className="text-xs text-gray-500">
            Adjust to focus on cards with stronger evidence.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <input
            type="range"
            min={0}
            max={1}
            step={0.1}
            value={credibilityFilter}
            onChange={(e) => setCredibilityFilter(parseFloat(e.target.value))}
          />
          <span className="text-sm text-gray-700 w-10 text-right">
            {credibilityFilter.toFixed(1)}
          </span>
          {credibilityFilter > 0 && (
            <button
              onClick={() => setCredibilityFilter(0)}
              className="text-xs text-blue-600 hover:underline"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Impact Cards List */}
      <div className="space-y-4 mb-6">
        {impactErrorMessage && (
          <div className="p-4 border border-red-200 bg-red-50 text-sm text-red-700 rounded-lg">
            {impactErrorMessage}
          </div>
        )}
        {impactCards && impactCards.length > 0 ? (
          impactCards.slice(0, 3).map((card: ImpactCard) => (
            <div
              key={card.id}
              onClick={() => setSelectedCard(card)}
              className="p-4 border rounded-lg cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-medium text-gray-900">
                    {card.competitor_name}
                  </h4>
                  <div className="flex items-center space-x-2 mt-1">
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${getRiskColor(
                        card.risk_level
                      )}`}
                    >
                      {card.risk_level.toUpperCase()} RISK
                    </span>
                    <span className="text-sm text-gray-600">
                      Score: {card.risk_score}/100
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div
                    className="text-2xl font-bold"
                    style={{ color: getRiskGaugeColor(card.risk_score) }}
                  >
                    {card.risk_score}
                  </div>
                  <div className="text-xs text-gray-500">
                    {card.total_sources} sources
                  </div>
                  <div className="text-xs text-gray-500">
                    Credibility: {(card.credibility_score * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              <div className="text-sm text-gray-600 mb-2">
                <Clock className="w-3 h-3 inline mr-1" />
                {new Date(card.created_at).toLocaleString()}
              </div>

              {card.requires_review && (
                <div className="mb-2 inline-flex items-center space-x-2 rounded-full bg-red-50 px-3 py-1 text-xs text-red-600">
                  <AlertTriangle className="w-3 h-3" />
                  <span>Analyst review requested</span>
                </div>
              )}

              {card.key_insights.length > 0 && (
                <div className="text-sm text-gray-700">
                  <strong>Key Insight:</strong> {card.key_insights[0]}
                </div>
              )}
            </div>
          ))
        ) : (!impactErrorMessage && (
          <div className="text-center py-8 text-gray-500">
            <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p>No Impact Cards generated yet.</p>
            <p className="text-sm">
              Generate your first Impact Card to see You.com APIs in action!
            </p>
          </div>
        ))}
      </div>

      {/* Selected Card Detail */}
  {selectedCard && (
    <div className="border-t pt-6">
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-xl font-bold text-gray-900">
              {selectedCard.competitor_name} - Impact Analysis
            </h4>
            <button
              onClick={() => setSelectedCard(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          {/* Risk Score Gauge */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="text-center">
              <div className="relative w-32 h-32 mx-auto mb-2">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        {
                          value: selectedCard.risk_score,
                          fill: getRiskGaugeColor(selectedCard.risk_score),
                        },
                        {
                          value: 100 - selectedCard.risk_score,
                          fill: "#e5e7eb",
                        },
                      ]}
                      cx="50%"
                      cy="50%"
                      startAngle={90}
                      endAngle={-270}
                      innerRadius={40}
                      outerRadius={60}
                      dataKey="value"
                    ></Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-2xl font-bold">
                      {selectedCard.risk_score}
                    </div>
                    <div className="text-xs text-gray-500">Risk Score</div>
                  </div>
                </div>
              </div>
              <div
                className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(
                  selectedCard.risk_level
                )}`}
              >
                {selectedCard.risk_level.toUpperCase()} RISK
              </div>
            </div>

            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {selectedCard.confidence_score}%
              </div>
              <div className="text-sm text-gray-600">Confidence Score</div>
              <div className="text-xs text-gray-500 mt-1">
                AI Analysis Confidence
              </div>
            </div>

            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {selectedCard.total_sources}
              </div>
              <div className="text-sm text-gray-600">Total Sources</div>
              <div className="text-xs text-gray-500 mt-1">
                News: {selectedCard.source_breakdown.news_articles} | Search:{" "}
                {selectedCard.source_breakdown.search_results} | Research:{" "}
                {selectedCard.source_breakdown.research_citations}
              </div>
            </div>
          </div>

          {selectedCard.source_quality && (
            <div className="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 border border-gray-200 rounded-lg">
                <h5 className="font-semibold text-gray-900 mb-2">Credibility Overview</h5>
                <p className="text-sm text-gray-600">
                  Overall score: {Math.round(selectedCard.credibility_score * 100)}%
                </p>
                <ul className="mt-2 text-sm text-gray-600 space-y-1">
                  <li>Tier 1 sources: {selectedCard.source_quality.tiers?.tier1 ?? 0}</li>
                  <li>Tier 2 sources: {selectedCard.source_quality.tiers?.tier2 ?? 0}</li>
                  <li>Tier 3 sources: {selectedCard.source_quality.tiers?.tier3 ?? 0}</li>
                </ul>
              </div>
              <div className="p-4 border border-gray-200 rounded-lg">
                <h5 className="font-semibold text-gray-900 mb-2">Top Evidence</h5>
                <ul className="space-y-1 text-sm text-blue-600">
                  {selectedCard.source_quality.top_sources?.slice(0, 3).map((source, idx) => (
                    <li key={`${source.url}-${idx}`}>
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noreferrer"
                        className="hover:underline"
                      >
                        {source.title ?? source.url}
                      </a>
                    </li>
                  ))}
                  {(!selectedCard.source_quality.top_sources ||
                    selectedCard.source_quality.top_sources.length === 0) && (
                    <li className="text-gray-500">No evidence captured.</li>
                  )}
                </ul>
              </div>
    </div>
  )}

  <div className="mt-8">
    <h5 className="text-sm font-semibold text-gray-900 mb-2">Latest Notifications</h5>
    <div className="space-y-2 text-sm text-gray-600">
      {(notificationLogs ?? []).slice(0, 5).map((log: any) => (
        <div key={log.id} className="p-3 border border-gray-200 rounded-lg">
          <div className="flex justify-between">
            <span className="font-medium text-gray-800">{log.competitor_name}</span>
            <span className="text-xs text-gray-500">
              {log.created_at ? new Date(log.created_at).toLocaleString() : ""}
            </span>
          </div>
          <div className="text-xs text-gray-500">Channel: {log.channel}</div>
          <p className="text-sm text-gray-600 mt-1">{log.message}</p>
        </div>
      ))}
      {(!notificationLogs || notificationLogs.length === 0) && (
        <div className="text-xs text-gray-500">No alerts have been triggered yet.</div>
      )}
    </div>
  </div>

          {/* Impact Areas */}
          {selectedCard.impact_areas.length > 0 && (
            <div className="mb-6">
              <h5 className="font-semibold text-gray-900 mb-3">Impact Areas</h5>
              <div className="space-y-3">
                {selectedCard.impact_areas.map((area, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <span className="font-medium capitalize">
                        {area.area}
                      </span>
                      <span
                        className="text-sm font-medium"
                        style={{ color: getRiskGaugeColor(area.impact_score) }}
                      >
                        {area.impact_score}/100
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div
                        className="h-2 rounded-full"
                        style={{
                          width: `${area.impact_score}%`,
                          backgroundColor: getRiskGaugeColor(area.impact_score),
                        }}
                      ></div>
                    </div>
                    <p className="text-sm text-gray-600">{area.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mb-6">
            <h5 className="font-semibold text-gray-900 mb-3">Next Steps</h5>
            <div className="space-y-3">
              {normalizedPlan.map((action) => (
                <div key={action.index} className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <div>
                      <p className="font-medium text-gray-900">{action.action}</p>
                      <p className="text-xs text-gray-500">
                        Owner: {action.owner} · OKR: {action.okr_goal}
                      </p>
                    </div>
                    <div className="text-right text-sm text-gray-600">
                      <div>Impact: {action.impact_score}</div>
                      <div>Effort: {action.effort_score}</div>
                      <div className="font-semibold text-blue-600">
                        Priority Score: {action.score.toFixed(1)}
                      </div>
                    </div>
                  </div>
                  {action.evidence.length > 0 && (
                    <div className="text-xs text-gray-600 mb-2">
                      Evidence:
                      <ul className="list-disc list-inside space-y-1">
                        {action.evidence.map((item, idx) => (
                          <li key={`${item.url}-${idx}`}>
                            <a
                              href={item.url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-blue-600 hover:underline"
                            >
                              {item.title ?? item.url}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleFeedback(action.index, "up")}
                      className="text-sm text-green-600 hover:underline"
                      disabled={feedbackMutation.isPending}
                    >
                      👍 Helpful
                    </button>
                    <button
                      onClick={() => handleFeedback(action.index, "down")}
                      className="text-sm text-red-600 hover:underline"
                      disabled={feedbackMutation.isPending}
                    >
                      👎 Not relevant
                    </button>
                  </div>
                </div>
              ))}
            </div>
            {feedbackMessage && (
              <div className="mt-2 text-xs text-blue-600">{feedbackMessage}</div>
            )}
          </div>

          <div className="mb-6">
            <button
              onClick={() => setShowExplainability((prev) => !prev)}
              className="flex items-center space-x-2 text-sm text-blue-600 hover:underline"
            >
              <Zap className="w-4 h-4" />
              <span>{showExplainability ? "Hide" : "Show"} Explainability Deep Dive</span>
            </button>
            {showExplainability && selectedCard.explainability && (
              <div className="mt-3 p-4 bg-gray-50 rounded-lg text-sm text-gray-700 space-y-2">
                {selectedCard.explainability.reasoning && (
                  <p>
                    <strong>Model reasoning:</strong> {selectedCard.explainability.reasoning}
                  </p>
                )}
                <div>
                  <strong>Drivers:</strong>
                  <ul className="list-disc list-inside">
                    {selectedCard.explainability.impact_areas?.map((area, idx) => (
                      <li key={idx}>{area.area}: {area.description}</li>
                    ))}
                  </ul>
                </div>
                {selectedCard.source_quality && (
                  <div>
                    <strong>Source summary:</strong> {selectedCard.source_quality.total} references · credibility {Math.round(selectedCard.credibility_score * 100)}%
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="mb-6">
            <h5 className="font-semibold text-gray-900 mb-3">Competitor Trend</h5>
            {comparisonLoading ? (
              <div className="text-sm text-gray-500">Loading trend…</div>
            ) : comparisonData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={comparisonData.map((point) => ({
                      time: point.created_at
                        ? new Date(point.created_at).toLocaleString()
                        : "Unknown",
                      risk: point.risk_score,
                      credibility: Math.round(point.credibility_score * 100) / 100,
                    }))}
                  >
                    <XAxis dataKey="time" hide />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="risk" name="Risk Score" stroke="#2563eb" />
                    <Line type="monotone" dataKey="credibility" name="Credibility" stroke="#10b981" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="text-sm text-gray-500">No historical impact cards for trend analysis.</div>
            )}
          </div>

          {/* Key Insights */}
          {selectedCard.key_insights.length > 0 && (
            <div className="mb-6">
              <h5 className="font-semibold text-gray-900 mb-3">Key Insights</h5>
              <ul className="space-y-2">
                {selectedCard.key_insights.map((insight, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <TrendingUp className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* You.com API Usage */}
          <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
            <h5 className="font-semibold text-gray-900 mb-3 flex items-center">
              <Zap className="w-4 h-4 mr-2" />
              You.com API Usage
            </h5>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-lg font-bold text-blue-600">
                  {selectedCard.api_usage.news_calls}
                </div>
                <div className="text-xs text-gray-600">News API</div>
              </div>
              <div>
                <div className="text-lg font-bold text-green-600">
                  {selectedCard.api_usage.search_calls}
                </div>
                <div className="text-xs text-gray-600">Search API</div>
              </div>
              <div>
                <div className="text-lg font-bold text-purple-600">
                  {selectedCard.api_usage.chat_calls}
                </div>
                <div className="text-xs text-gray-600">Chat API</div>
              </div>
              <div>
                <div className="text-lg font-bold text-orange-600">
                  {selectedCard.api_usage.ari_calls}
                </div>
                <div className="text-xs text-gray-600">ARI API</div>
              </div>
            </div>
            <div className="text-center mt-3">
              <div className="text-sm text-gray-600">
                Total API Calls:{" "}
                <strong>{selectedCard.api_usage.total_calls}</strong>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="mt-8">
        <h5 className="text-sm font-semibold text-gray-900 mb-2">Latest Notifications</h5>
        <div className="space-y-2 text-sm text-gray-600">
          {(notificationLogs ?? []).slice(0, 5).map((log: any) => (
            <div key={log.id} className="p-3 border border-gray-200 rounded-lg">
              <div className="flex justify-between">
                <span className="font-medium text-gray-800">{log.competitor_name}</span>
                <span className="text-xs text-gray-500">
                  {log.created_at ? new Date(log.created_at).toLocaleString() : ""}
                </span>
              </div>
              <div className="text-xs text-gray-500">Channel: {log.channel}</div>
              <p className="text-sm text-gray-600 mt-1">{log.message}</p>
            </div>
          ))}
          {(!notificationLogs || notificationLogs.length === 0) && (
            <div className="text-xs text-gray-500">No alerts have been triggered yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}