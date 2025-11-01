"use client";

import React, { memo, useState, useMemo } from "react";
import {
  ExternalLink,
  Filter,
  Star,
  ChevronDown,
  ChevronUp,
  Eye,
} from "lucide-react";

interface SourceQuality {
  score: number;
  tiers: Record<string, number>;
  total: number;
  top_sources: Array<{ title?: string; url: string; type?: string }>;
}

interface ImpactCard {
  id: number;
  competitor_name: string;
  credibility_score: number;
  source_quality?: SourceQuality;
  source_breakdown: {
    news_articles: number;
    search_results: number;
    research_citations: number;
  };
  total_sources: number;
}

interface SourceCitationsProps {
  card: ImpactCard;
  isExpanded: boolean;
  onToggle: () => void;
}

interface Source {
  title?: string;
  url: string;
  type?: string;
  tier?: number;
  credibility?: number;
}

const SourceCitations = memo<SourceCitationsProps>(
  ({ card, isExpanded, onToggle }) => {
    const [credibilityFilter, setCredibilityFilter] = useState(0);
    const [sortBy, setSortBy] = useState<"credibility" | "type" | "title">(
      "credibility"
    );
    const [showAllSources, setShowAllSources] = useState(false);
    const [clickedSources, setClickedSources] = useState<Set<string>>(
      new Set()
    );

    // Process and enhance sources with credibility scores
    const processedSources = useMemo(() => {
      if (!card.source_quality?.top_sources) return [];

      return card.source_quality.top_sources.map((source, index) => {
        // Assign tier based on source type or position
        let tier = 3; // default
        let credibility = 0.5; // default

        // Determine tier based on URL domain or type
        let domain = "";
        try {
          domain = new URL(source.url).hostname.toLowerCase();
        } catch {
          // Invalid URL, use default values
          tier = 3;
          credibility = 0.5;
        }
        if (
          domain.includes("wsj.com") ||
          domain.includes("reuters.com") ||
          domain.includes("bloomberg.com") ||
          domain.includes("ft.com")
        ) {
          tier = 1;
          credibility = 0.9;
        } else if (
          domain.includes("techcrunch.com") ||
          domain.includes("venturebeat.com") ||
          domain.includes("theinformation.com")
        ) {
          tier = 2;
          credibility = 0.75;
        } else if (
          domain.includes("medium.com") ||
          domain.includes("reddit.com") ||
          domain.includes("news.ycombinator.com")
        ) {
          tier = 3;
          credibility = 0.55;
        } else if (
          domain.includes("twitter.com") ||
          domain.includes("x.com") ||
          source.type === "blog"
        ) {
          tier = 4;
          credibility = 0.35;
        }

        return {
          ...source,
          tier,
          credibility,
          id: `${source.url}-${index}`,
        };
      });
    }, [card.source_quality]);

    // Filter and sort sources
    const filteredSources = useMemo(() => {
      let filtered = processedSources.filter(
        (source) => source.credibility >= credibilityFilter
      );

      // Sort sources
      filtered.sort((a, b) => {
        switch (sortBy) {
          case "credibility":
            return b.credibility - a.credibility;
          case "type":
            return (a.type || "").localeCompare(b.type || "");
          case "title":
            return (a.title || a.url).localeCompare(b.title || b.url);
          default:
            return 0;
        }
      });

      return showAllSources ? filtered : filtered.slice(0, 5);
    }, [processedSources, credibilityFilter, sortBy, showAllSources]);

    const handleSourceClick = (source: Source) => {
      setClickedSources((prev) => new Set(Array.from(prev).concat(source.url)));
      // Track click analytics here if needed
      window.open(source.url, "_blank", "noopener,noreferrer");
    };

    const getTierColor = (tier: number) => {
      switch (tier) {
        case 1:
          return "bg-green-100 text-green-800 border-green-200";
        case 2:
          return "bg-blue-100 text-blue-800 border-blue-200";
        case 3:
          return "bg-yellow-100 text-yellow-800 border-yellow-200";
        case 4:
          return "bg-orange-100 text-orange-800 border-orange-200";
        default:
          return "bg-gray-100 text-gray-800 border-gray-200";
      }
    };

    const getTierLabel = (tier: number) => {
      switch (tier) {
        case 1:
          return "Tier 1 - Authoritative";
        case 2:
          return "Tier 2 - Reputable";
        case 3:
          return "Tier 3 - Community";
        case 4:
          return "Tier 4 - Unverified";
        default:
          return "Unknown Tier";
      }
    };

    const getCredibilityStars = (credibility: number) => {
      const stars = Math.round(credibility * 5);
      return Array.from({ length: 5 }, (_, i) => (
        <Star
          key={i}
          className={`w-3 h-3 ${
            i < stars ? "text-yellow-400 fill-current" : "text-gray-300"
          }`}
        />
      ));
    };

    return (
      <div className="mb-6 border border-gray-200 rounded-lg">
        {/* Header */}
        <div
          className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={onToggle}
        >
          <div className="flex justify-between items-center">
            <h5 className="font-semibold text-gray-900 flex items-center space-x-2">
              <span>Source Citations</span>
              <span className="text-sm text-gray-500">
                ({card.total_sources} total)
              </span>
            </h5>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-green-600">
                {Math.round(card.credibility_score * 100)}% credible
              </span>
              {isExpanded ? (
                <ChevronUp className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              )}
            </div>
          </div>
        </div>

        {/* Expanded Content */}
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-gray-100">
            {/* Source Breakdown Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 mb-6">
              <div className="p-4 border border-gray-200 rounded-lg">
                <h6 className="font-semibold text-gray-900 mb-2">
                  Credibility Overview
                </h6>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Overall Score:</span>
                    <span className="font-medium">
                      {Math.round(card.credibility_score * 100)}%
                    </span>
                  </div>
                  {card.source_quality?.tiers && (
                    <>
                      <div className="flex justify-between">
                        <span>Tier 1 sources:</span>
                        <span>{card.source_quality.tiers.tier1 || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Tier 2 sources:</span>
                        <span>{card.source_quality.tiers.tier2 || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Tier 3 sources:</span>
                        <span>{card.source_quality.tiers.tier3 || 0}</span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              <div className="p-4 border border-gray-200 rounded-lg">
                <h6 className="font-semibold text-gray-900 mb-2">
                  Source Breakdown
                </h6>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>News Articles:</span>
                    <span className="font-medium">
                      {card.source_breakdown.news_articles}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Search Results:</span>
                    <span className="font-medium">
                      {card.source_breakdown.search_results}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Research Citations:</span>
                    <span className="font-medium">
                      {card.source_breakdown.research_citations}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Filters and Controls */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Filter className="w-4 h-4 text-gray-500" />
                  <label className="text-sm text-gray-700">
                    Min Credibility:
                  </label>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.1}
                    value={credibilityFilter}
                    onChange={(e) =>
                      setCredibilityFilter(parseFloat(e.target.value))
                    }
                    className="w-20"
                  />
                  <span className="text-sm text-gray-600 w-8">
                    {credibilityFilter.toFixed(1)}
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <label className="text-sm text-gray-700">Sort by:</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
                    className="text-sm border border-gray-300 rounded px-2 py-1"
                  >
                    <option value="credibility">Credibility</option>
                    <option value="type">Type</option>
                    <option value="title">Title</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Sources List */}
            <div className="space-y-3">
              {filteredSources.length > 0 ? (
                filteredSources.map((source) => (
                  <div
                    key={source.id}
                    className={`p-3 border rounded-lg transition-all duration-200 hover:shadow-md cursor-pointer ${
                      clickedSources.has(source.url)
                        ? "bg-blue-50 border-blue-200"
                        : "bg-white border-gray-200 hover:border-gray-300"
                    }`}
                    onClick={() => handleSourceClick(source)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <h6 className="text-sm font-medium text-gray-900 truncate">
                            {source.title ||
                              (() => {
                                try {
                                  return new URL(source.url).hostname;
                                } catch {
                                  return source.url;
                                }
                              })()}
                          </h6>
                          <ExternalLink className="w-3 h-3 text-gray-400 flex-shrink-0" />
                          {clickedSources.has(source.url) && (
                            <Eye className="w-3 h-3 text-blue-500 flex-shrink-0" />
                          )}
                        </div>

                        <div className="flex items-center space-x-2 mb-2">
                          <span
                            className={`px-2 py-1 text-xs rounded border ${getTierColor(
                              source.tier || 3
                            )}`}
                          >
                            {getTierLabel(source.tier || 3)}
                          </span>
                          <div className="flex items-center space-x-1">
                            {getCredibilityStars(source.credibility)}
                          </div>
                        </div>

                        <p className="text-xs text-gray-600 truncate">
                          {source.url}
                        </p>
                      </div>

                      <div className="text-right ml-3">
                        <div className="text-sm font-medium text-gray-900">
                          {Math.round(source.credibility * 100)}%
                        </div>
                        <div className="text-xs text-gray-500">credibility</div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-gray-500">
                  <div className="text-sm">
                    {credibilityFilter > 0
                      ? "No sources meet the credibility filter criteria."
                      : "No source citations available."}
                  </div>
                  {credibilityFilter > 0 && (
                    <button
                      onClick={() => setCredibilityFilter(0)}
                      className="text-xs text-blue-600 hover:underline mt-1"
                    >
                      Reset filter
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Show More/Less Button */}
            {processedSources.length > 5 && (
              <div className="text-center mt-4">
                <button
                  onClick={() => setShowAllSources(!showAllSources)}
                  className="text-sm text-blue-600 hover:underline"
                >
                  {showAllSources
                    ? "Show Less"
                    : `Show All ${processedSources.length} Sources`}
                </button>
              </div>
            )}

            {/* Source Quality Legend */}
            <div className="mt-6 p-3 bg-gray-50 rounded-lg">
              <h6 className="text-xs font-semibold text-gray-900 mb-2">
                Source Quality Tiers
              </h6>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-1 rounded border bg-green-100 text-green-800 border-green-200">
                    Tier 1
                  </span>
                  <span className="text-gray-600">
                    WSJ, Reuters, Bloomberg, FT
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-1 rounded border bg-blue-100 text-blue-800 border-blue-200">
                    Tier 2
                  </span>
                  <span className="text-gray-600">TechCrunch, VentureBeat</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-1 rounded border bg-yellow-100 text-yellow-800 border-yellow-200">
                    Tier 3
                  </span>
                  <span className="text-gray-600">HN, Reddit, Medium</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-1 rounded border bg-orange-100 text-orange-800 border-orange-200">
                    Tier 4
                  </span>
                  <span className="text-gray-600">Blogs, Social Media</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }
);

SourceCitations.displayName = "SourceCitations";

export default SourceCitations;
