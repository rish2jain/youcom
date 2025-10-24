"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Search,
  Building,
  TrendingUp,
  Download,
  Share,
  Zap,
  ExternalLink,
} from "lucide-react";
import { api } from "@/lib/api";

interface CompanyResearch {
  id: number;
  company_name: string;
  search_results: any;
  research_report: any;
  total_sources: number;
  api_usage: {
    search_calls: number;
    ari_calls: number;
    total_calls: number;
  };
  created_at: string;
}

export function CompanyResearch() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedResearch, setSelectedResearch] =
    useState<CompanyResearch | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [shareEmails, setShareEmails] = useState("");
  const [isExporting, setIsExporting] = useState(false);
  const [isSharing, setIsSharing] = useState(false);

  const queryClient = useQueryClient();

  // Fetch recent research
  const {
    data: recentResearch,
    isLoading,
    error: researchError,
  } = useQuery({
    queryKey: ["companyResearch"],
    queryFn: () => api.get("/api/v1/research/").then((res) => res.data),
  });

  const researchErrorMessage = researchError
    ? researchError instanceof Error
      ? researchError.message
      : "Unable to load research history."
    : null;

  // Research company mutation
  const researchMutation = useMutation({
    mutationFn: (company_name: string) =>
      api.post("/api/v1/research/company", { company_name }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["companyResearch"] });
      setSelectedResearch(data.data);
      setSearchQuery("");
      setActionError(null);
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "Research request failed. Please try again.";
      setActionError(message);
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const query = searchQuery.trim();
    if (!query) {
      setActionError("Enter a company name to research.");
      return;
    }

    setActionError(null);
    researchMutation.mutate(query);
  };

  const handleExportPDF = async (research: CompanyResearch) => {
    try {
      setIsExporting(true);
      setActionError(null);

      const response = await api.get(`/api/v1/research/${research.id}/export`, {
        responseType: 'blob',
      });

      // Create blob and download
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${research.company_name.replace(/\s+/g, '_')}_research_report.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setActionError('Failed to export PDF. Please try again.');
      console.error('Export error:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const handleShare = async () => {
    if (!selectedResearch) return;

    const emails = shareEmails.split(',').map(e => e.trim()).filter(e => e);
    if (emails.length === 0) {
      setActionError('Please enter at least one email address.');
      return;
    }

    try {
      setIsSharing(true);
      setActionError(null);

      await api.post(`/api/v1/research/${selectedResearch.id}/share`, {
        emails: emails,
      });

      setShowShareDialog(false);
      setShareEmails('');
      alert(`Report shared successfully with ${emails.length} recipient(s)!`);
    } catch (error) {
      setActionError('Failed to share report. Please check your email settings.');
      console.error('Share error:', error);
    } finally {
      setIsSharing(false);
    }
  };

  const extractKeyInfo = (research: CompanyResearch) => {
    const searchResults = research.search_results?.results || [];
    const report = research.research_report?.report || "";

    // Extract basic info from search results
    const basicInfo = searchResults.slice(0, 3).map((result: any) => ({
      title: result.title || "",
      snippet: result.snippet || "",
      url: result.url || "",
    }));

    // Extract key points from ARI report
    // Handle different report formats from You.com API
    let reportText = "";
    if (typeof report === "string") {
      reportText = report;
    } else if (Array.isArray(report) && report.length > 0) {
      // Handle array format from Express Agent
      reportText = report
        .map((item) => item.text || item.content || JSON.stringify(item))
        .join("\n");
    } else {
      reportText = JSON.stringify(report);
    }

    const reportSections = reportText
      .split("\n")
      .filter((line: string) => line.trim().length > 0);

    return {
      basicInfo,
      reportSections: reportSections.slice(0, 5),
      totalSources: research.total_sources,
    };
  };

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="flex items-center space-x-2 mb-4">
          <Building className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Company Research
          </h3>
          <div className="you-api-badge">
            <Zap className="w-3 h-3 inline mr-1" />
            Search + ARI APIs
          </div>
        </div>

        <form onSubmit={handleSearch} className="flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter any company name (e.g., Perplexity AI, Stripe, Notion)"
              required
            />
          </div>
          <button
            type="submit"
            disabled={researchMutation.isPending}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
          >
            {researchMutation.isPending ? (
              <>
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                <span>Researching...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Research Company</span>
              </>
            )}
          </button>
        </form>

        {researchMutation.isPending && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center space-x-2 text-blue-700">
              <div className="animate-pulse w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-sm">
                Processing with You.com APIs: Search → ARI → Analysis
              </span>
            </div>
            <div className="mt-2 text-xs text-blue-600">
              Gathering information from 400+ sources...
            </div>
          </div>
        )}

        {actionError && (
          <div className="mt-4 p-3 border border-red-200 bg-red-50 text-sm text-red-700 rounded-lg" role="alert">
            {actionError}
          </div>
        )}

        {/* Quick Suggestions */}
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">
            💡 Try These Companies
          </h4>
          <div className="flex flex-wrap gap-2">
            {[
              "Perplexity AI",
              "Stripe",
              "Notion",
              "Figma",
              "Canva",
              "Discord",
              "Zoom",
              "Slack",
              "Databricks",
              "Snowflake",
            ].map((company) => (
              <button
                key={company}
                onClick={() => setSearchQuery(company)}
                className="px-3 py-1 text-sm bg-white border border-gray-200 rounded-full hover:bg-gray-100 transition-colors"
              >
                {company}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Research */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Recent Research
        </h3>

        {researchErrorMessage && (
          <div className="mb-4 p-3 border border-red-200 bg-red-50 text-sm text-red-700 rounded-lg">
            {researchErrorMessage}
          </div>
        )}

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse p-4 border rounded-lg">
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            ))}
          </div>
        ) : recentResearch?.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Building className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p>No company research yet.</p>
            <p className="text-sm">
              Research your first company to see You.com APIs in action!
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {recentResearch?.slice(0, 5).map((research: CompanyResearch) => (
              <div
                key={research.id}
                onClick={() => setSelectedResearch(research)}
                className="p-4 border rounded-lg cursor-pointer hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {research.company_name}
                    </h4>
                    <div className="text-sm text-gray-600 mt-1">
                      {research.total_sources} sources •{" "}
                      {new Date(research.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-blue-600 font-medium">
                      {research.api_usage.total_calls} API calls
                    </div>
                    <div className="text-xs text-gray-500">
                      Search: {research.api_usage.search_calls} | ARI:{" "}
                      {research.api_usage.ari_calls}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Selected Research Detail */}
      {selectedResearch && (
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold text-gray-900">
              {selectedResearch.company_name} - Research Report
            </h3>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => handleExportPDF(selectedResearch)}
                disabled={isExporting}
                className="flex items-center space-x-2 text-blue-600 hover:text-blue-700 disabled:opacity-50 disabled:cursor-not-allowed px-3 py-2 border border-blue-600 rounded-lg hover:bg-blue-50"
              >
                <Download className="w-4 h-4" />
                <span>{isExporting ? 'Exporting...' : 'Export PDF'}</span>
              </button>
              <button
                onClick={() => setShowShareDialog(true)}
                className="flex items-center space-x-2 text-green-600 hover:text-green-700 px-3 py-2 border border-green-600 rounded-lg hover:bg-green-50"
              >
                <Share className="w-4 h-4" />
                <span>Share</span>
              </button>
              <button
                onClick={() => setSelectedResearch(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Research Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {selectedResearch.total_sources}
              </div>
              <div className="text-sm text-gray-600">Total Sources</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {selectedResearch.api_usage.search_calls}
              </div>
              <div className="text-sm text-gray-600">Search API Calls</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {selectedResearch.api_usage.ari_calls}
              </div>
              <div className="text-sm text-gray-600">ARI API Calls</div>
            </div>
          </div>

          {/* Research Content */}
          {(() => {
            const info = extractKeyInfo(selectedResearch);
            return (
              <div className="space-y-6">
                {/* Basic Information */}
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <Search className="w-4 h-4 mr-2" />
                    Company Overview (You.com Search API)
                  </h4>
                  <div className="space-y-3">
                    {info.basicInfo.map((item: any, index: number) => (
                      <div
                        key={index}
                        className="p-3 border-l-4 border-blue-500 bg-blue-50"
                      >
                        <h5 className="font-medium text-gray-900 mb-1">
                          {item.title}
                        </h5>
                        <p className="text-sm text-gray-700 mb-2">
                          {item.snippet}
                        </p>
                        {item.url && (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:text-blue-700 flex items-center"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            Source
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Deep Research Report */}
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <TrendingUp className="w-4 h-4 mr-2" />
                    Deep Research Analysis (You.com ARI API)
                  </h4>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    {info.reportSections.length > 0 ? (
                      <div className="space-y-3">
                        {info.reportSections.map((section, index) => (
                          <p
                            key={index}
                            className="text-sm text-gray-700 leading-relaxed"
                          >
                            {section}
                          </p>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600 italic">
                        Comprehensive research report generated from{" "}
                        {selectedResearch.total_sources} sources
                      </p>
                    )}
                  </div>
                </div>

                {/* API Usage Details */}
                <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                    <Zap className="w-4 h-4 mr-2" />
                    You.com API Integration
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">
                        Search API Usage
                      </h5>
                      <ul className="text-sm text-gray-600 space-y-1">
                        <li>• Company profile gathering</li>
                        <li>• Business model analysis</li>
                        <li>• Market positioning research</li>
                        <li>• Competitor identification</li>
                      </ul>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-900 mb-2">
                        ARI API Usage
                      </h5>
                      <ul className="text-sm text-gray-600 space-y-1">
                        <li>• 400+ source comprehensive analysis</li>
                        <li>• Funding and investment history</li>
                        <li>• Strategic partnerships</li>
                        <li>• Market trends and opportunities</li>
                      </ul>
                    </div>
                  </div>
                  <div className="mt-4 text-center">
                    <div className="text-sm text-gray-600">
                      Research completed in <strong>&lt;2 minutes</strong> vs.
                      2-4 hours manually
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      )}

      {/* Share Dialog Modal */}
      {showShareDialog && selectedResearch && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Share Research Report
              </h3>
              <button
                onClick={() => setShowShareDialog(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                Share <strong>{selectedResearch.company_name}</strong> research
                report via email
              </p>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Addresses (comma-separated)
              </label>
              <input
                type="text"
                value={shareEmails}
                onChange={(e) => setShareEmails(e.target.value)}
                placeholder="email1@example.com, email2@example.com"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {actionError && (
              <div className="mb-4 p-3 border border-red-200 bg-red-50 text-sm text-red-700 rounded-lg">
                {actionError}
              </div>
            )}

            <div className="flex space-x-3">
              <button
                onClick={() => setShowShareDialog(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleShare}
                disabled={isSharing || !shareEmails.trim()}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSharing ? 'Sharing...' : 'Share Report'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}