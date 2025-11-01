"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ExternalLink,
  Info,
  TrendingUp,
  Clock,
  Target,
  AlertCircle,
} from "lucide-react";

interface SourceCredibilityAnalysis {
  id: number;
  source_url: string;
  source_title: string;
  source_type: string;
  tier_level: string;
  credibility_score: number;
  authority_score: number;
  recency_score: number;
  relevance_score: number;
  validation_method: string;
  quality_flags: string[];
  warning_flags: string[];
  conflicts_with: number[];
  conflict_severity: string;
  created_at: string;
}

interface SourceQualityVisualizationProps {
  impactCardId: number;
  sourceAnalyses: SourceCredibilityAnalysis[];
  onRefresh?: () => void;
}

const SourceQualityVisualization: React.FC<SourceQualityVisualizationProps> = ({
  impactCardId,
  sourceAnalyses,
  onRefresh,
}) => {
  const [selectedSource, setSelectedSource] =
    useState<SourceCredibilityAnalysis | null>(null);
  const [activeTab, setActiveTab] = useState("overview");

  // Calculate summary statistics
  const totalSources = sourceAnalyses.length;
  const averageCredibility =
    totalSources > 0
      ? sourceAnalyses.reduce((sum, s) => sum + s.credibility_score, 0) /
        totalSources
      : 0;

  const tierCounts = sourceAnalyses.reduce((acc, source) => {
    acc[source.tier_level] = (acc[source.tier_level] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const conflictingSources = sourceAnalyses.filter(
    (s) => s.conflicts_with.length > 0
  );
  const highQualitySources = sourceAnalyses.filter(
    (s) => s.credibility_score >= 0.8
  );
  const lowQualitySources = sourceAnalyses.filter(
    (s) => s.credibility_score < 0.5
  );

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "tier1":
        return "bg-green-100 text-green-800 border-green-200";
      case "tier2":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "tier3":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getTierLabel = (tier: string) => {
    switch (tier) {
      case "tier1":
        return "Authoritative";
      case "tier2":
        return "Reputable";
      case "tier3":
        return "Community";
      default:
        return "Unknown";
    }
  };

  const getCredibilityColor = (score: number) => {
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const getConflictSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "text-red-600";
      case "major":
        return "text-orange-600";
      case "minor":
        return "text-yellow-600";
      default:
        return "text-gray-600";
    }
  };

  const formatUrl = (url: string) => {
    try {
      const domain = new URL(url).hostname;
      return domain.replace("www.", "");
    } catch {
      return url;
    }
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-blue-600" />
              <div>
                <p className="text-sm text-gray-600">Total Sources</p>
                <p className="text-2xl font-bold">{totalSources}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm text-gray-600">Avg. Credibility</p>
                <p
                  className={`text-2xl font-bold ${getCredibilityColor(
                    averageCredibility
                  )}`}
                >
                  {(averageCredibility * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm text-gray-600">High Quality</p>
                <p className="text-2xl font-bold text-green-600">
                  {highQualitySources.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-orange-600" />
              <div>
                <p className="text-sm text-gray-600">Conflicts</p>
                <p className="text-2xl font-bold text-orange-600">
                  {conflictingSources.length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sources">Source Details</TabsTrigger>
          <TabsTrigger value="conflicts">Conflicts</TabsTrigger>
          <TabsTrigger value="methodology">Methodology</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Tier Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="w-5 h-5" />
                <span>Source Tier Distribution</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(tierCounts).map(([tier, count]) => (
                  <div key={tier} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Badge className={getTierColor(tier)}>
                        {getTierLabel(tier)}
                      </Badge>
                      <span className="text-sm text-gray-600">
                        {tier === "tier1" &&
                          "Authoritative sources with high editorial standards"}
                        {tier === "tier2" &&
                          "Reputable sources with good editorial standards"}
                        {tier === "tier3" && "Community and unverified sources"}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold">{count}</span>
                      <div className="w-20">
                        <Progress
                          value={(count / totalSources) * 100}
                          className="h-2"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quality Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="w-5 h-5" />
                <span>Quality Distribution</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-green-600">
                    {highQualitySources.length}
                  </p>
                  <p className="text-sm text-gray-600">High Quality (≥80%)</p>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <Info className="w-8 h-8 text-yellow-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-yellow-600">
                    {
                      sourceAnalyses.filter(
                        (s) =>
                          s.credibility_score >= 0.5 &&
                          s.credibility_score < 0.8
                      ).length
                    }
                  </p>
                  <p className="text-sm text-gray-600">
                    Medium Quality (50-79%)
                  </p>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <XCircle className="w-8 h-8 text-red-600 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-red-600">
                    {lowQualitySources.length}
                  </p>
                  <p className="text-sm text-gray-600">Low Quality (&lt;50%)</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sources" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Source List */}
            <Card>
              <CardHeader>
                <CardTitle>Source Analysis</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 max-h-96 overflow-y-auto">
                {sourceAnalyses.map((source) => (
                  <div
                    key={source.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedSource?.id === source.id
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                    onClick={() => setSelectedSource(source)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <Badge className={getTierColor(source.tier_level)}>
                            {getTierLabel(source.tier_level)}
                          </Badge>
                          {source.conflicts_with.length > 0 && (
                            <AlertTriangle className="w-4 h-4 text-orange-500" />
                          )}
                        </div>
                        <p
                          className="font-medium text-sm truncate"
                          title={source.source_title}
                        >
                          {source.source_title || "Untitled"}
                        </p>
                        <p className="text-xs text-gray-500 truncate">
                          {formatUrl(source.source_url)}
                        </p>
                      </div>
                      <div className="text-right ml-2">
                        <p
                          className={`text-sm font-semibold ${getCredibilityColor(
                            source.credibility_score
                          )}`}
                        >
                          {(source.credibility_score * 100).toFixed(0)}%
                        </p>
                        <p className="text-xs text-gray-500 capitalize">
                          {source.source_type}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Source Details */}
            <Card>
              <CardHeader>
                <CardTitle>Source Details</CardTitle>
              </CardHeader>
              <CardContent>
                {selectedSource ? (
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">
                        {selectedSource.source_title || "Untitled"}
                      </h4>
                      <div className="flex items-center space-x-2 mb-2">
                        <Badge
                          className={getTierColor(selectedSource.tier_level)}
                        >
                          {getTierLabel(selectedSource.tier_level)}
                        </Badge>
                        <span className="text-sm text-gray-500 capitalize">
                          {selectedSource.source_type}
                        </span>
                      </div>
                      <a
                        href={selectedSource.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline text-sm flex items-center space-x-1"
                      >
                        <span>{formatUrl(selectedSource.source_url)}</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>

                    {/* Credibility Scores */}
                    <div className="space-y-3">
                      <h5 className="font-medium">Credibility Breakdown</h5>

                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Overall Credibility</span>
                          <span
                            className={`font-semibold ${getCredibilityColor(
                              selectedSource.credibility_score
                            )}`}
                          >
                            {(selectedSource.credibility_score * 100).toFixed(
                              0
                            )}
                            %
                          </span>
                        </div>
                        <Progress
                          value={selectedSource.credibility_score * 100}
                          className="h-2"
                        />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Authority Score</span>
                          <span className="font-semibold">
                            {(selectedSource.authority_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <Progress
                          value={selectedSource.authority_score * 100}
                          className="h-2"
                        />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Recency Score</span>
                          <span className="font-semibold">
                            {(selectedSource.recency_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <Progress
                          value={selectedSource.recency_score * 100}
                          className="h-2"
                        />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Relevance Score</span>
                          <span className="font-semibold">
                            {(selectedSource.relevance_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <Progress
                          value={selectedSource.relevance_score * 100}
                          className="h-2"
                        />
                      </div>
                    </div>

                    {/* Quality Flags */}
                    {selectedSource.quality_flags.length > 0 && (
                      <div>
                        <h5 className="font-medium mb-2">Quality Indicators</h5>
                        <div className="flex flex-wrap gap-1">
                          {selectedSource.quality_flags.map((flag, index) => (
                            <Badge
                              key={index}
                              className="bg-green-100 text-green-800 border-green-200"
                            >
                              <CheckCircle className="w-3 h-3 mr-1" />
                              {flag.replace(/_/g, " ")}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Warning Flags */}
                    {selectedSource.warning_flags.length > 0 && (
                      <div>
                        <h5 className="font-medium mb-2">Warning Indicators</h5>
                        <div className="flex flex-wrap gap-1">
                          {selectedSource.warning_flags.map((flag, index) => (
                            <Badge
                              key={index}
                              className="bg-red-100 text-red-800 border-red-200"
                            >
                              <AlertTriangle className="w-3 h-3 mr-1" />
                              {flag.replace(/_/g, " ")}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Validation Method */}
                    <div>
                      <h5 className="font-medium mb-2">Validation Method</h5>
                      <p className="text-sm text-gray-600">
                        {selectedSource.validation_method}
                      </p>
                    </div>

                    {/* Conflicts */}
                    {selectedSource.conflicts_with.length > 0 && (
                      <div>
                        <h5 className="font-medium mb-2">Conflicts Detected</h5>
                        <div className="flex items-center space-x-2">
                          <AlertTriangle
                            className={`w-4 h-4 ${getConflictSeverityColor(
                              selectedSource.conflict_severity
                            )}`}
                          />
                          <span
                            className={`text-sm font-medium ${getConflictSeverityColor(
                              selectedSource.conflict_severity
                            )}`}
                          >
                            {selectedSource.conflict_severity.toUpperCase()}{" "}
                            conflict with {selectedSource.conflicts_with.length}{" "}
                            source(s)
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    <Info className="w-8 h-8 mx-auto mb-2" />
                    <p>Select a source to view detailed analysis</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="conflicts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
                <span>Conflicting Evidence Detection</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {conflictingSources.length > 0 ? (
                <div className="space-y-4">
                  {conflictingSources.map((source) => (
                    <div key={source.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h4 className="font-medium">
                            {source.source_title || "Untitled"}
                          </h4>
                          <p className="text-sm text-gray-500">
                            {formatUrl(source.source_url)}
                          </p>
                        </div>
                        <Badge
                          className={`${getConflictSeverityColor(
                            source.conflict_severity
                          )} border`}
                        >
                          {source.conflict_severity.toUpperCase()} CONFLICT
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">
                            Credibility Score:
                          </span>
                          <span
                            className={`ml-2 font-semibold ${getCredibilityColor(
                              source.credibility_score
                            )}`}
                          >
                            {(source.credibility_score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-600">Conflicts with:</span>
                          <span className="ml-2 font-semibold">
                            {source.conflicts_with.length} source(s)
                          </span>
                        </div>
                      </div>

                      <div className="mt-3 p-3 bg-yellow-50 rounded border-l-4 border-yellow-400">
                        <p className="text-sm text-yellow-800">
                          <AlertCircle className="w-4 h-4 inline mr-1" />
                          This source conflicts with other sources in the
                          analysis. Consider additional verification or expert
                          review.
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
                  <p>No conflicting evidence detected</p>
                  <p className="text-sm">
                    All sources appear to be consistent with each other
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="methodology" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Source Quality Methodology</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Tier Classification</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center space-x-2">
                    <Badge className="bg-green-100 text-green-800 border-green-200">
                      Tier 1
                    </Badge>
                    <span>
                      Authoritative sources (WSJ, Reuters, Bloomberg, etc.) -
                      Score: 85-100%
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">
                      Tier 2
                    </Badge>
                    <span>
                      Reputable sources (TechCrunch, VentureBeat, etc.) - Score:
                      65-84%
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className="bg-red-100 text-red-800 border-red-200">
                      Tier 3
                    </Badge>
                    <span>
                      Community sources (blogs, social media, etc.) - Score:
                      20-64%
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">Credibility Calculation</h4>
                <p className="text-sm text-gray-600 mb-2">
                  Overall credibility score is calculated as the average of
                  three components:
                </p>
                <div className="space-y-1 text-sm">
                  <div>
                    <strong>Authority Score:</strong> Based on domain reputation
                    and tier classification
                  </div>
                  <div>
                    <strong>Recency Score:</strong> Based on publication date
                    and freshness
                  </div>
                  <div>
                    <strong>Relevance Score:</strong> Based on content relevance
                    to the analysis topic
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">Conflict Detection</h4>
                <p className="text-sm text-gray-600">
                  Sources are flagged as conflicting when they have significant
                  credibility score differences (&gt;60%) or when they come from
                  the same domain but different tiers, indicating potential
                  inconsistencies in the information.
                </p>
              </div>

              <div>
                <h4 className="font-medium mb-2">Quality Indicators</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <h5 className="font-medium text-green-600 mb-1">
                      Positive Indicators
                    </h5>
                    <ul className="space-y-1 text-gray-600">
                      <li>• Authoritative source domain</li>
                      <li>• Official government/education source</li>
                      <li>• High credibility score (&gt;80%)</li>
                      <li>• Recent publication date</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="font-medium text-red-600 mb-1">
                      Warning Indicators
                    </h5>
                    <ul className="space-y-1 text-gray-600">
                      <li>• Low credibility score (&lt;50%)</li>
                      <li>• Insufficient metadata</li>
                      <li>• Unknown source type</li>
                      <li>• Conflicting information</li>
                    </ul>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Refresh Button */}
      {onRefresh && (
        <div className="flex justify-end">
          <Button onClick={onRefresh} variant="outline">
            <Clock className="w-4 h-4 mr-2" />
            Refresh Analysis
          </Button>
        </div>
      )}
    </div>
  );
};

export default SourceQualityVisualization;
