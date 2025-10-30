"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import {
  Shield,
  ShieldCheck,
  AlertTriangle,
  Info,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Clock,
  Users,
  CheckCircle,
  Star,
} from "lucide-react";

interface SourceEvidence {
  id: number;
  source_name: string;
  source_url: string;
  source_tier: number;
  title?: string;
  excerpt?: string;
  publish_date?: string;
  relevance_score?: number;
  credibility_score?: number;
  you_api_source?: string;
}

interface EvidenceBadgeData {
  id: number;
  entity_type: string;
  entity_id: number;
  confidence_percentage: number;
  confidence_level: string;
  total_sources: number;
  tier_1_sources: number;
  tier_2_sources: number;
  tier_3_sources: number;
  tier_4_sources: number;
  freshness_score: number;
  oldest_source_hours?: number;
  newest_source_hours?: number;
  average_source_age_hours?: number;
  badge_color?: string;
  badge_icon?: string;
  display_text?: string;
  weighted_source_score: number;
  overall_quality_score: number;
  source_details: SourceEvidence[];
}

interface EvidenceBadgeResponse {
  badge: EvidenceBadgeData;
  top_sources_expanded: SourceEvidence[];
  quality_breakdown: {
    confidence_breakdown: {
      source_quality: number;
      freshness: number;
      cross_validation: number;
      fact_checking: number;
    };
    source_distribution: {
      tier_1: number;
      tier_2: number;
      tier_3: number;
      tier_4: number;
    };
    freshness_details: {
      newest_hours?: number;
      oldest_hours?: number;
      average_hours?: number;
    };
  };
  recommendations: string[];
}

interface ConfidenceMetrics {
  overall_confidence: number;
  confidence_level: string;
  source_count: number;
  tier_breakdown: {
    tier_1: number;
    tier_2: number;
    tier_3: number;
    tier_4: number;
  };
  freshness_indicator: string;
  quality_indicators: string[];
}

interface EvidenceBadgeProps {
  entityType: string;
  entityId: number;
  compact?: boolean;
  showExpanded?: boolean;
  onConfidenceClick?: () => void;
}

const EvidenceBadge: React.FC<EvidenceBadgeProps> = ({
  entityType,
  entityId,
  compact = false,
  showExpanded = false,
  onConfidenceClick,
}) => {
  const [evidenceData, setEvidenceData] =
    useState<EvidenceBadgeResponse | null>(null);
  const [confidenceMetrics, setConfidenceMetrics] =
    useState<ConfidenceMetrics | null>(null);
  const [isExpanded, setIsExpanded] = useState(showExpanded);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadEvidenceData();
  }, [entityType, entityId]);

  const loadEvidenceData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Load both detailed and metrics data
      const [evidenceResponse, metricsResponse] = await Promise.all([
        fetch(`/api/v1/enhancements/evidence/${entityType}/${entityId}`),
        fetch(
          `/api/v1/enhancements/evidence/${entityType}/${entityId}/metrics`
        ),
      ]);

      if (evidenceResponse.ok) {
        const evidenceData: EvidenceBadgeResponse =
          await evidenceResponse.json();
        setEvidenceData(evidenceData);
      }

      if (metricsResponse.ok) {
        const metricsData: ConfidenceMetrics = await metricsResponse.json();
        setConfidenceMetrics(metricsData);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load evidence data"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const getBadgeIcon = (confidenceLevel: string) => {
    switch (confidenceLevel) {
      case "very_high":
        return <ShieldCheck className="w-4 h-4" />;
      case "high":
        return <Shield className="w-4 h-4" />;
      case "medium":
        return <CheckCircle className="w-4 h-4" />;
      case "low":
        return <AlertTriangle className="w-4 h-4" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const getBadgeColor = (confidenceLevel: string) => {
    switch (confidenceLevel) {
      case "very_high":
        return "bg-green-100 text-green-800 border-green-200";
      case "high":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getTierName = (tier: number) => {
    switch (tier) {
      case 1:
        return "Authoritative";
      case 2:
        return "Reputable";
      case 3:
        return "Community";
      case 4:
        return "Unverified";
      default:
        return "Unknown";
    }
  };

  const getTierColor = (tier: number) => {
    switch (tier) {
      case 1:
        return "text-green-600 bg-green-50";
      case 2:
        return "text-blue-600 bg-blue-50";
      case 3:
        return "text-yellow-600 bg-yellow-50";
      case 4:
        return "text-gray-600 bg-gray-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const formatTimeAgo = (hours?: number) => {
    if (!hours) return "Unknown";
    if (hours < 1) return "Just now";
    if (hours < 24) return `${Math.floor(hours)}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const getFreshnessColor = (indicator: string) => {
    switch (indicator) {
      case "very_fresh":
        return "text-green-600";
      case "fresh":
        return "text-blue-600";
      case "stale":
        return "text-yellow-600";
      case "very_stale":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center space-x-2 p-2 bg-gray-50 rounded-md animate-pulse">
        <div className="w-4 h-4 bg-gray-300 rounded" />
        <div className="w-24 h-4 bg-gray-300 rounded" />
      </div>
    );
  }

  if (error || !confidenceMetrics) {
    return (
      <div className="flex items-center space-x-2 p-2 bg-red-50 rounded-md">
        <AlertTriangle className="w-4 h-4 text-red-500" />
        <span className="text-sm text-red-600">Evidence unavailable</span>
      </div>
    );
  }

  // Compact view
  if (compact) {
    return (
      <div
        className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full border cursor-pointer hover:shadow-sm transition-shadow ${getBadgeColor(
          confidenceMetrics.confidence_level
        )}`}
        onClick={onConfidenceClick}
      >
        {getBadgeIcon(confidenceMetrics.confidence_level)}
        <span className="text-sm font-medium">
          {Math.round(confidenceMetrics.overall_confidence)}% confident
        </span>
        <span className="text-xs opacity-75">
          • {confidenceMetrics.source_count} sources
        </span>
      </div>
    );
  }

  // Full view
  return (
    <Card className="w-full">
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div
              className={`p-2 rounded-lg ${getBadgeColor(
                confidenceMetrics.confidence_level
              )}`}
            >
              {getBadgeIcon(confidenceMetrics.confidence_level)}
            </div>
            <div>
              <h3 className="font-medium text-gray-900">
                {Math.round(confidenceMetrics.overall_confidence)}% Confidence
              </h3>
              <p className="text-sm text-gray-500">
                Based on {confidenceMetrics.source_count} sources
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </Button>
        </div>

        {/* Quality Indicators */}
        {confidenceMetrics.quality_indicators.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {confidenceMetrics.quality_indicators.map((indicator, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                <Star className="w-3 h-3 mr-1" />
                {indicator}
              </Badge>
            ))}
          </div>
        )}

        {/* Source Distribution */}
        <div className="grid grid-cols-4 gap-2 mb-4">
          {Object.entries(confidenceMetrics.tier_breakdown).map(
            ([tier, count]) => {
              const tierNum = parseInt(tier.split("_")[1]);
              return (
                <div key={tier} className="text-center">
                  <div
                    className={`text-xs px-2 py-1 rounded ${getTierColor(
                      tierNum
                    )}`}
                  >
                    {getTierName(tierNum)}
                  </div>
                  <div className="text-sm font-medium mt-1">{count}</div>
                </div>
              );
            }
          )}
        </div>

        {/* Freshness Indicator */}
        <div className="flex items-center justify-between text-sm mb-4">
          <span className="text-gray-500">Freshness:</span>
          <span
            className={`font-medium ${getFreshnessColor(
              confidenceMetrics.freshness_indicator
            )}`}
          >
            <Clock className="w-3 h-3 inline mr-1" />
            {confidenceMetrics.freshness_indicator.replace("_", " ")}
          </span>
        </div>

        {/* Expanded Details */}
        {isExpanded && evidenceData && (
          <div className="space-y-4 border-t pt-4">
            {/* Quality Breakdown */}
            <div>
              <h4 className="font-medium text-sm text-gray-900 mb-3">
                Quality Breakdown
              </h4>
              <div className="space-y-2">
                {Object.entries(
                  evidenceData.quality_breakdown.confidence_breakdown
                ).map(([metric, value]) => (
                  <div
                    key={metric}
                    className="flex items-center justify-between"
                  >
                    <span className="text-sm text-gray-600 capitalize">
                      {metric.replace("_", " ")}
                    </span>
                    <div className="flex items-center space-x-2">
                      <Progress value={value} className="w-16 h-2" />
                      <span className="text-sm font-medium w-8">
                        {Math.round(value)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Sources */}
            {evidenceData.top_sources_expanded.length > 0 && (
              <div>
                <h4 className="font-medium text-sm text-gray-900 mb-3">
                  Top Supporting Sources
                </h4>
                <div className="space-y-3">
                  {evidenceData.top_sources_expanded.map((source) => (
                    <div key={source.id} className="p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <h5 className="font-medium text-sm text-gray-900">
                              {source.source_name}
                            </h5>
                            <Badge
                              variant="outline"
                              className={`text-xs ${getTierColor(
                                source.source_tier
                              )}`}
                            >
                              Tier {source.source_tier}
                            </Badge>
                            {source.you_api_source && (
                              <Badge variant="secondary" className="text-xs">
                                {source.you_api_source}
                              </Badge>
                            )}
                          </div>
                          {source.title && (
                            <p className="text-sm text-gray-700 mb-1">
                              {source.title}
                            </p>
                          )}
                          {source.excerpt && (
                            <p className="text-xs text-gray-600 line-clamp-2">
                              {source.excerpt}
                            </p>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            window.open(source.source_url, "_blank")
                          }
                        >
                          <ExternalLink className="w-3 h-3" />
                        </Button>
                      </div>
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>
                          {formatTimeAgo(
                            source.publish_date
                              ? (Date.now() -
                                  new Date(source.publish_date).getTime()) /
                                  (1000 * 60 * 60)
                              : undefined
                          )}
                        </span>
                        {source.relevance_score && (
                          <span>
                            Relevance:{" "}
                            {Math.round(source.relevance_score * 100)}%
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {evidenceData.recommendations.length > 0 && (
              <div>
                <h4 className="font-medium text-sm text-gray-900 mb-3">
                  Recommendations
                </h4>
                <ul className="space-y-2">
                  {evidenceData.recommendations.map((rec, index) => (
                    <li
                      key={index}
                      className="flex items-start space-x-2 text-sm text-gray-600"
                    >
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default EvidenceBadge;
