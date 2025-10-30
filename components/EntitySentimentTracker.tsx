"use client";

import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";

// Type definitions
interface Entity {
  entity_name: string;
  entity_type: string;
  trend_direction: "up" | "down" | "stable";
  change_percent: number;
  current_sentiment: number;
  total_mentions: number;
}

interface EntitySentimentData {
  entity_name: string;
  entity_type: string;
  current_sentiment: number;
  sentiment_history: Array<{
    timestamp: string;
    sentiment_score: number;
    volume: number;
  }>;
  sentiment_breakdown: {
    positive: number;
    negative: number;
    neutral: number;
  };
  recent_mentions: Array<{
    content: string;
    source: string;
    sentiment: number;
    timestamp: string;
  }>;
  trend_analysis: {
    direction: "up" | "down" | "stable";
    change_percent: number;
    significance: string;
  };
  top_topics: Array<{
    topic: string;
    sentiment: number;
    mentions: number;
  }>;
}

// Type guard for EntitySentimentData
function isEntitySentimentData(obj: any): obj is EntitySentimentData {
  const allowedEntityTypes = [
    "company",
    "product",
    "person",
    "technology",
    "industry",
  ];
  const allowedTrendDirections = ["improving", "declining", "stable"];

  return (
    obj &&
    typeof obj.entity_name === "string" &&
    obj.entity_name.length > 0 &&
    typeof obj.entity_type === "string" &&
    allowedEntityTypes.includes(obj.entity_type) &&
    typeof obj.current_sentiment === "number" &&
    obj.sentiment_breakdown &&
    typeof obj.sentiment_breakdown === "object" &&
    typeof obj.sentiment_breakdown.positive === "number" &&
    typeof obj.sentiment_breakdown.negative === "number" &&
    typeof obj.sentiment_breakdown.neutral === "number" &&
    Array.isArray(obj.sentiment_history) &&
    obj.sentiment_history.every(
      (item: any) =>
        item &&
        typeof item.timestamp === "string" &&
        typeof item.sentiment_score === "number" &&
        typeof item.volume === "number"
    ) &&
    obj.trend_analysis &&
    typeof obj.trend_analysis === "object" &&
    typeof obj.trend_analysis.direction === "string" &&
    ["up", "down", "stable"].includes(obj.trend_analysis.direction) &&
    Array.isArray(obj.top_topics) &&
    obj.top_topics.every(
      (topic: any) =>
        topic &&
        typeof topic === "object" &&
        typeof topic.topic === "string" &&
        typeof topic.sentiment === "number" &&
        typeof topic.mentions === "number"
    ) &&
    Array.isArray(obj.recent_mentions) &&
    obj.recent_mentions.every(
      (mention: any) =>
        mention &&
        typeof mention.content === "string" &&
        typeof mention.source === "string" &&
        typeof mention.timestamp === "string" &&
        typeof mention.sentiment === "number" &&
        Number.isFinite(mention.sentiment)
    )
  );
}
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  Building2,
  Package,
  TrendingUp,
  TrendingDown,
  Search,
  Filter,
  Star,
  MessageCircle,
} from "lucide-react";
import { api } from "@/lib/api";

export function EntitySentimentTracker() {
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
  const [entityType, setEntityType] = useState<
    "all" | "company" | "product" | "market"
  >("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"sentiment" | "volume" | "trend">(
    "sentiment"
  );

  const {
    data: entities,
    isLoading: entitiesLoading,
    isError: entitiesError,
    error: entitiesErrorData,
    refetch: refetchEntities,
  } = useQuery<Entity[], Error>({
    queryKey: ["entitySentiments", entityType, searchQuery, sortBy],
    queryFn: () => {
      const params: Record<string, string> = {};
      if (entityType !== "all") params.entity_type = entityType;
      if (searchQuery) params.search = searchQuery;
      params.sort_by = sortBy;

      return api
        .get("/api/v1/sentiment/entities", { params })
        .then((res) => res.data.entities);
    },
    staleTime: 60000, // 1 minute
  });

  const {
    data: entityDetails,
    isLoading: detailsLoading,
    isError: detailsError,
    error: detailsErrorData,
    refetch: refetchDetails,
  } = useQuery<any, Error>({
    queryKey: ["entitySentimentDetails", selectedEntity],
    queryFn: () =>
      api
        .get(`/api/v1/sentiment/entities/${selectedEntity}/details`)
        .then((res) => res.data),
    enabled: !!selectedEntity,
    staleTime: 30000,
  });

  // Handle errors via useEffect instead of deprecated onError
  useEffect(() => {
    if (entitiesError) {
      console.error("Failed to fetch entities:", entitiesError);
    }
    if (detailsError) {
      console.error("Failed to fetch entity details:", detailsError);
    }
  }, [entitiesError, detailsError]);

  const getSentimentColor = (score: number) => {
    if (score > 0.2) return "#10b981"; // green
    if (score > -0.2) return "#6b7280"; // gray
    return "#ef4444"; // red
  };

  const getSentimentLabel = (score: number) => {
    if (score > 0.2) return "Positive";
    if (score > -0.2) return "Neutral";
    return "Negative";
  };

  const getEntityIcon = (type: string) => {
    switch (type) {
      case "company":
        return <Building2 className="w-4 h-4" />;
      case "product":
        return <Package className="w-4 h-4" />;
      case "market":
        return <TrendingUp className="w-4 h-4" />;
      default:
        return <Star className="w-4 h-4" />;
    }
  };

  const getTrendIcon = (direction: string, changePercent: number) => {
    if (direction === "improving") {
      return <TrendingUp className="w-4 h-4 text-green-600" />;
    } else if (direction === "declining") {
      return <TrendingDown className="w-4 h-4 text-red-600" />;
    }
    return <div className="w-4 h-4 bg-gray-400 rounded-full"></div>;
  };

  const formatSentimentScore = (score: number) => {
    if (score > 0) return `+${(score * 100).toFixed(1)}%`;
    return `${(score * 100).toFixed(1)}%`;
  };

  if (entitiesLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const entitiesList = entities || [];
  const details =
    entityDetails && isEntitySentimentData(entityDetails)
      ? entityDetails
      : undefined;

  // Error handling
  if (entitiesError) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm" role="alert">
        <div className="text-center space-y-4">
          <div className="text-red-600 font-medium">
            Failed to load entities
          </div>
          <div className="text-gray-600 text-sm">
            {entitiesErrorData?.message || "An unexpected error occurred"}
          </div>
          <button
            onClick={() => refetchEntities()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <MessageCircle className="w-5 h-5 mr-2 text-blue-600" />
            Entity Sentiment Tracker
          </h3>
          <div className="text-sm text-gray-600">
            {entitiesList.length} entities tracked
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-wrap gap-4 mb-6">
          <div className="relative flex-1 min-w-64">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search entities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Type:</span>
            <select
              value={entityType}
              onChange={(e) =>
                setEntityType(
                  e.target.value as "all" | "company" | "product" | "market"
                )
              }
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="company">Companies</option>
              <option value="product">Products</option>
              <option value="market">Markets</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) =>
                setSortBy(e.target.value as "sentiment" | "volume" | "trend")
              }
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="sentiment">Sentiment Score</option>
              <option value="volume">Mention Volume</option>
              <option value="trend">Trend Change</option>
            </select>
          </div>
        </div>

        {/* Entity Grid */}
        {entitiesList.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {entitiesList.map((entity: Entity) => (
              <div
                key={`${entity.entity_name}-${entity.entity_type}`}
                onClick={() => setSelectedEntity(entity.entity_name)}
                className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                  selectedEntity === entity.entity_name
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {getEntityIcon(entity.entity_type)}
                    <div>
                      <div className="font-medium text-gray-900">
                        {entity.entity_name}
                      </div>
                      <div className="text-xs text-gray-600 capitalize">
                        {entity.entity_type}
                      </div>
                    </div>
                  </div>
                  {getTrendIcon(entity.trend_direction, entity.change_percent)}
                </div>

                <div className="flex items-center justify-between mb-2">
                  <div
                    className="text-xl font-bold"
                    style={{
                      color: getSentimentColor(entity.current_sentiment),
                    }}
                  >
                    {formatSentimentScore(entity.current_sentiment)}
                  </div>
                  <div className="text-right">
                    <div
                      className={`text-sm font-medium ${
                        entity.change_percent > 0
                          ? "text-green-600"
                          : entity.change_percent < 0
                          ? "text-red-600"
                          : "text-gray-600"
                      }`}
                    >
                      {entity.change_percent > 0 ? "+" : ""}
                      {entity.change_percent.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {entity.total_mentions} mentions
                    </div>
                  </div>
                </div>

                <div className="text-xs text-gray-600">
                  {getSentimentLabel(entity.current_sentiment)} sentiment
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <MessageCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg mb-2">No entities found</p>
            <p className="text-sm">
              {searchQuery || entityType !== "all"
                ? "Try adjusting your search or filters."
                : "Entity sentiment data will appear here once analysis begins."}
            </p>
          </div>
        )}
      </div>

      {/* Entity Details */}
      {selectedEntity &&
        (detailsError ? (
          <div className="bg-white p-6 rounded-lg shadow-sm" role="alert">
            <div className="text-center space-y-4">
              <div className="text-red-600 font-medium">
                Failed to load entity details
              </div>
              <div className="text-gray-600 text-sm">
                {detailsErrorData?.message || "An unexpected error occurred"}
              </div>
              <button
                onClick={() => refetchDetails()}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        ) : details && isEntitySentimentData(details) ? (
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h4 className="text-lg font-semibold text-gray-900 flex items-center">
                {getEntityIcon(details.entity_type)}
                <span className="ml-2">{details.entity_name}</span>
                <span className="ml-2 text-sm font-normal text-gray-600 capitalize">
                  ({details.entity_type})
                </span>
              </h4>
              <button
                onClick={() => setSelectedEntity(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Sentiment History Chart */}
              <div>
                <h5 className="font-semibold text-gray-900 mb-4">
                  Sentiment History
                </h5>
                {details.sentiment_history.length > 0 ? (
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={details.sentiment_history}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="timestamp"
                          tickFormatter={(value) =>
                            new Date(value).toLocaleDateString()
                          }
                        />
                        <YAxis domain={[-1, 1]} />
                        <Tooltip
                          labelFormatter={(value) =>
                            new Date(value).toLocaleString()
                          }
                          formatter={(value) => [
                            formatSentimentScore(Number(value)),
                            "Sentiment",
                          ]}
                        />
                        <Line
                          type="monotone"
                          dataKey="sentiment_score"
                          stroke="#3b82f6"
                          strokeWidth={2}
                          dot={{ fill: "#3b82f6", strokeWidth: 2, r: 4 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <TrendingUp className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                    <p className="text-sm">No historical data available</p>
                  </div>
                )}
              </div>

              {/* Sentiment Breakdown */}
              <div>
                <h5 className="font-semibold text-gray-900 mb-4">
                  Sentiment Breakdown
                </h5>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      {(() => {
                        const sentimentData = [
                          {
                            name: "Positive",
                            value: details.sentiment_breakdown.positive,
                            color: "#10b981",
                          },
                          {
                            name: "Neutral",
                            value: details.sentiment_breakdown.neutral,
                            color: "#6b7280",
                          },
                          {
                            name: "Negative",
                            value: details.sentiment_breakdown.negative,
                            color: "#ef4444",
                          },
                        ];

                        return (
                          <Pie
                            data={sentimentData}
                            cx="50%"
                            cy="50%"
                            innerRadius={40}
                            outerRadius={80}
                            dataKey="value"
                            nameKey="name"
                          >
                            {sentimentData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                        );
                      })()}
                      <Tooltip
                        formatter={(value) => [`${value} mentions`, ""]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Top Topics */}
            {details.top_topics && details.top_topics.length > 0 && (
              <div className="mt-6">
                <h5 className="font-semibold text-gray-900 mb-4">
                  Top Discussion Topics
                </h5>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {details.top_topics.map((topic, index) => (
                    <div key={index} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-sm">
                          {topic.topic}
                        </span>
                        <span
                          className="text-sm font-bold"
                          style={{ color: getSentimentColor(topic.sentiment) }}
                        >
                          {formatSentimentScore(topic.sentiment)}
                        </span>
                      </div>
                      <div className="text-xs text-gray-600">
                        {topic.mentions} mentions
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Mentions */}
            {details.recent_mentions && details.recent_mentions.length > 0 && (
              <div className="mt-6">
                <h5 className="font-semibold text-gray-900 mb-4">
                  Recent Mentions
                </h5>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {details.recent_mentions.map((mention, index) => (
                    <div
                      key={index}
                      className="p-3 border border-gray-200 rounded-lg"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="text-sm text-gray-700 flex-1 mr-4">
                          {mention.content}
                        </div>
                        <div
                          className="text-sm font-bold whitespace-nowrap"
                          style={{
                            color: getSentimentColor(mention.sentiment),
                          }}
                        >
                          {formatSentimentScore(mention.sentiment)}
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>{mention.source}</span>
                        <span>
                          {new Date(mention.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null)}
    </div>
  );
}
