"use client";

import React, { useState, useEffect, useRef, Suspense } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Zap } from "lucide-react";
import { api } from "@/lib/api";
import { getSocket } from "@/lib/socket";
import { LoadingSkeleton } from "./LoadingSkeleton";

// Lazy-loaded components
const ImpactCardHeader = React.lazy(() => import("./ImpactCardHeader"));
const RiskScoreWidget = React.lazy(() => import("./RiskScoreWidget"));
const SourceCitations = React.lazy(() => import("./SourceCitations"));
const ActionRecommendations = React.lazy(
  () => import("./ActionRecommendations")
);
const CollaborationPane = React.lazy(() => import("./CollaborationPane"));

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

interface ImpactCardShellProps {
  viewMode?: "compact" | "detailed" | "technical";
  onCardSelect?: (card: ImpactCard | null) => void;
  collaborationEnabled?: boolean;
}

export function ImpactCardShell({
  viewMode = "detailed",
  onCardSelect,
  collaborationEnabled = true,
}: ImpactCardShellProps) {
  const [selectedCard, setSelectedCard] = useState<ImpactCard | null>(null);
  const [showRawData, setShowRawData] = useState(false);
  const [generateForm, setGenerateForm] = useState({
    competitor_name: "",
    keywords: "",
  });
  const [activeCompetitor, setActiveCompetitor] = useState<string | null>(null);
  const [progressLog, setProgressLog] = useState<ProgressEntry[]>([]);
  const [formError, setFormError] = useState<string | null>(null);
  const [credibilityFilter, setCredibilityFilter] = useState(0);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["executive-summary"])
  );

  const competitorRef = useRef<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch impact cards with credibility filtering
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

  // Generate new impact card mutation
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
      const newCard = data.data;
      setSelectedCard(newCard);
      onCardSelect?.(newCard);
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

  // WebSocket setup for real-time progress updates
  useEffect(() => {
    const socket = getSocket();
    socket.emit("join_room", { room: "impact_cards" });

    const resolveStepMessage = (
      step: string,
      payload: Record<string, unknown>
    ) => {
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
        [
          ...prev,
          {
            status: "step" as const,
            message,
            timestamp: new Date().toISOString(),
            competitor,
          },
        ].slice(-6)
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

  const handleCardSelect = (card: ImpactCard) => {
    setSelectedCard(card);
    onCardSelect?.(card);
  };

  const toggleSection = (sectionId: string) => {
    setExpandedSections((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  const impactErrorMessage = impactError
    ? impactError instanceof Error
      ? impactError.message
      : "Unable to load Impact Cards."
    : null;

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

      {/* Progress Log */}
      {progressLog.length > 0 && (
        <div className="mb-6 p-4 border border-blue-100 bg-blue-50 rounded-lg">
          <h5 className="text-sm font-semibold text-blue-700 mb-2">
            Live Generation Progress
          </h5>
          <ul className="space-y-1 text-sm text-blue-700">
            {progressLog.map((entry, index) => (
              <li
                key={`${entry.timestamp}-${index}`}
                className="flex items-start"
              >
                <span className="mr-2 text-blue-500">•</span>
                <span>
                  <span className="font-medium capitalize">{entry.status}</span>{" "}
                  — {entry.message}
                  <span className="ml-2 text-xs text-blue-400">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Credibility Filter */}
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

      {/* Error Display */}
      {impactErrorMessage && (
        <div className="p-4 border border-red-200 bg-red-50 text-sm text-red-700 rounded-lg mb-4">
          {impactErrorMessage}
        </div>
      )}

      {/* Impact Cards List */}
      {impactCards && impactCards.length > 0 ? (
        <div className="space-y-4 mb-6">
          {impactCards
            .slice(0, viewMode === "compact" ? 3 : 10)
            .map((card: ImpactCard) => (
              <Suspense key={card.id} fallback={<LoadingSkeleton />}>
                <ImpactCardHeader
                  card={card}
                  onClick={() => handleCardSelect(card)}
                  isSelected={selectedCard?.id === card.id}
                  viewMode={viewMode}
                />
              </Suspense>
            ))}
        </div>
      ) : (
        !impactErrorMessage && (
          <div className="text-center py-8 text-gray-500">
            <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p>No Impact Cards generated yet.</p>
            <p className="text-sm">
              Generate your first Impact Card to see You.com APIs in action!
            </p>
          </div>
        )
      )}

      {/* Selected Card Detail */}
      {selectedCard && (
        <div className="border-t pt-6">
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-xl font-bold text-gray-900">
              {selectedCard.competitor_name} - Impact Analysis
            </h4>
            <button
              onClick={() => {
                setSelectedCard(null);
                onCardSelect?.(null);
              }}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          {/* Risk Score Widget */}
          <Suspense fallback={<LoadingSkeleton />}>
            <RiskScoreWidget
              card={selectedCard}
              isExpanded={expandedSections.has("risk-score")}
              onToggle={() => toggleSection("risk-score")}
            />
          </Suspense>

          {/* Source Citations */}
          <Suspense fallback={<LoadingSkeleton />}>
            <SourceCitations
              card={selectedCard}
              isExpanded={expandedSections.has("sources")}
              onToggle={() => toggleSection("sources")}
            />
          </Suspense>

          {/* Action Recommendations */}
          <Suspense fallback={<LoadingSkeleton />}>
            <ActionRecommendations
              card={selectedCard}
              isExpanded={expandedSections.has("actions")}
              onToggle={() => toggleSection("actions")}
            />
          </Suspense>

          {/* Collaboration Pane */}
          {collaborationEnabled && (
            <Suspense fallback={<LoadingSkeleton />}>
              <CollaborationPane
                card={selectedCard}
                isExpanded={expandedSections.has("collaboration")}
                onToggle={() => toggleSection("collaboration")}
              />
            </Suspense>
          )}
        </div>
      )}
    </div>
  );
}
