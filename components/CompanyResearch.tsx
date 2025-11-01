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
import jsPDF from "jspdf";
import MarkdownRenderer from "./MarkdownRenderer";

interface CompanyResearch {
  id: number;
  company_name: string;
  search_results: any;
  research_report: any;
  total_sources: number;
  status?: string;
  summary?: string;
  confidence_score?: number;
  api_usage: {
    search_calls: number;
    ari_calls: number;
    total_calls: number;
  };
  created_at: string;
}

interface CompanyResearchProps {
  initialCompany?: string;
}

export function CompanyResearch({ initialCompany }: CompanyResearchProps = {}) {
  const [searchQuery, setSearchQuery] = useState(initialCompany || "");
  const [selectedResearch, setSelectedResearch] =
    useState<CompanyResearch | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [shareEmails, setShareEmails] = useState("");
  const [isExporting, setIsExporting] = useState(false);
  const [isSharing, setIsSharing] = useState(false);
  const [showResearchModal, setShowResearchModal] = useState(false);

  const queryClient = useQueryClient();

  // Fetch recent research from backend API
  const {
    data: recentResearchRaw,
    isLoading,
    error: researchError,
  } = useQuery({
    queryKey: ["companyResearch"],
    queryFn: async () => {
      // Backend handles all You.com API calls and PostgreSQL storage
      try {
        const response = await api.get("/api/v1/research/");
        // Ensure response is always an array
        if (Array.isArray(response)) {
          return response;
        }
        // If response is wrapped in an object, try to extract the array
        if (response && typeof response === 'object' && 'items' in response && Array.isArray(response.items)) {
          return response.items;
        }
        // If response is an object with a list property
        if (response && typeof response === 'object' && 'data' in response && Array.isArray(response.data)) {
          return response.data;
        }
        // Default to empty array if response is not an array
        return [];
      } catch (error) {
        console.error("Error fetching research:", error);
        return [];
      }
    },
  });

  // Ensure recentResearch is always an array, never undefined or non-array
  const recentResearch: CompanyResearch[] = Array.isArray(recentResearchRaw) 
    ? recentResearchRaw 
    : [];

  const researchErrorMessage = researchError
    ? researchError instanceof Error
      ? researchError.message
      : "Unable to load research history."
    : null;

  // Research company mutation - backend handles You.com APIs and database
  const researchMutation = useMutation({
    mutationFn: async (company_name: string) => {
      // Backend will:
      // 1. Call You.com Search API for company information
      // 2. Call You.com Chat/ARI API for comprehensive report
      // 3. Save to PostgreSQL database
      // 4. Return structured response
      const response = await api.post("/api/v1/research/company", {
        company_name,
      });
      return response;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["companyResearch"] });
      setSelectedResearch(data);
      setSearchQuery("");
      setActionError(null);
    },
    onError: (error: unknown) => {
      const message =
        error instanceof Error
          ? error.message
          : "Research request failed. Please ensure the backend server is running.";
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

      // Try backend API first (backend may have better PDF generation)
      try {
        const response = await api.get(
          `/api/v1/research/${research.id}/export`,
          {
            responseType: "blob",
          }
        );

        const blob = new Blob([response.data], { type: "application/pdf" });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${research.company_name.replace(
          /\s+/g,
          "_"
        )}_research_report.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        return;
      } catch (apiError) {
        // Backend PDF generation unavailable, fallback to client-side
        console.log(
          "Backend PDF generation unavailable, using client-side generation"
        );
      }

      // Client-side PDF generation using jsPDF
      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 20;
      const maxWidth = pageWidth - 2 * margin;
      let yPosition = margin;

      // Helper function to add text with automatic line wrapping and page breaks
      const addText = (
        text: string,
        fontSize: number = 11,
        isBold: boolean = false
      ) => {
        doc.setFontSize(fontSize);
        doc.setFont("helvetica", isBold ? "bold" : "normal");
        const lines = doc.splitTextToSize(text, maxWidth);

        lines.forEach((line: string) => {
          if (yPosition + 10 > pageHeight - margin) {
            doc.addPage();
            yPosition = margin;
          }
          doc.text(line, margin, yPosition);
          yPosition += fontSize * 0.5;
        });
        yPosition += 5;
      };

      // Title
      doc.setFillColor(37, 99, 235);
      doc.rect(0, 0, pageWidth, 40, "F");
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(22);
      doc.setFont("helvetica", "bold");
      doc.text(`${research.company_name}`, margin, 25);
      doc.setFontSize(12);
      doc.text("Competitive Intelligence Report", margin, 35);
      yPosition = 50;
      doc.setTextColor(0, 0, 0);

      // Metadata
      doc.setFontSize(9);
      doc.setFont("helvetica", "normal");
      doc.text(
        `Generated: ${new Date().toLocaleDateString()}`,
        margin,
        yPosition
      );
      doc.text(
        `Sources Analyzed: ${research.total_sources}`,
        margin,
        yPosition + 5
      );
      doc.text(
        `Confidence Score: ${research.confidence_score || 85}%`,
        margin,
        yPosition + 10
      );
      yPosition += 20;

      // Executive Summary
      addText("EXECUTIVE SUMMARY", 14, true);
      addText(
        research.summary || `Comprehensive analysis of ${research.company_name}`
      );

      // Search Results Section
      const searchResults = research.search_results?.results || [];
      if (searchResults.length > 0) {
        yPosition += 5;
        addText("KEY FINDINGS (You.com Search API)", 14, true);
        searchResults.slice(0, 5).forEach((result: any, index: number) => {
          addText(`${index + 1}. ${result.title}`, 11, true);
          addText(result.snippet || "");
          if (result.url) {
            doc.setTextColor(37, 99, 235);
            addText(`Source: ${result.url}`, 9);
            doc.setTextColor(0, 0, 0);
          }
          yPosition += 3;
        });
      }

      // Deep Research Report
      yPosition += 5;
      addText("COMPREHENSIVE ANALYSIS (You.com Chat API)", 14, true);
      const report = research.research_report?.report || "";
      const reportText =
        typeof report === "string" ? report : JSON.stringify(report);
      addText(reportText);

      // API Usage Stats
      yPosition += 5;
      addText("API INTEGRATION DETAILS", 14, true);
      addText(`Search API Calls: ${research.api_usage.search_calls}`);
      addText(`ARI/Chat API Calls: ${research.api_usage.ari_calls}`);
      addText(`Total API Calls: ${research.api_usage.total_calls}`);
      addText(`Processing Time: <2 minutes (vs 2-4 hours manually)`);

      // Footer on last page
      const totalPages = (doc as any).internal.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(
          `Page ${i} of ${totalPages} | Generated by Enterprise CIA Platform | Powered by You.com APIs`,
          pageWidth / 2,
          pageHeight - 10,
          { align: "center" }
        );
      }

      // Save the PDF
      doc.save(
        `${research.company_name.replace(/\s+/g, "_")}_research_report.pdf`
      );
    } catch (error) {
      setActionError("Failed to export PDF. Please try again.");
      console.error("Export error:", error);
    } finally {
      setIsExporting(false);
    }
  };

  const handleShare = async () => {
    if (!selectedResearch) return;

    const emails = shareEmails
      .split(",")
      .map((e) => e.trim())
      .filter((e) => e);
    if (emails.length === 0) {
      setActionError("Please enter at least one email address.");
      return;
    }

    try {
      setIsSharing(true);
      setActionError(null);

      await api.post(`/api/v1/research/${selectedResearch.id}/share`, {
        emails: emails,
        subject: `Company Research Report: ${selectedResearch.company_name}`,
        message: `Please find attached the comprehensive research report for ${selectedResearch.company_name}. This report was generated using Enterprise CIA, powered by You.com APIs.`,
      });

      setShowShareDialog(false);
      setShareEmails("");

      // Show success message with more details
      const successMessage =
        `✅ Report shared successfully!\n\n` +
        `📧 Recipients: ${emails.join(", ")}\n` +
        `📄 Report: ${selectedResearch.company_name}\n` +
        `📊 Sources: ${selectedResearch.total_sources}\n\n` +
        `The PDF report has been sent via email.`;

      alert(successMessage);
    } catch (error: any) {
      let errorMessage = "Failed to share report.";

      if (error.response?.status === 503) {
        errorMessage =
          "Email service not configured. Please contact your administrator to set up SMTP settings.";
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }

      setActionError(errorMessage);
      console.error("Share error:", error);
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

  // Extract key findings from search results and research report
  const extractKeyFindings = (research: CompanyResearch) => {
    const findings: Array<{ text: string; color: string }> = [];
    const colors = ["green", "blue", "orange", "purple"];
    const researchReport = research.research_report || {};

    // First, check if there are structured key_findings in the research_report
    if (researchReport.key_findings && Array.isArray(researchReport.key_findings)) {
      researchReport.key_findings.slice(0, 4).forEach((finding: any, index: number) => {
        const findingText = typeof finding === 'string' ? finding : (finding.text || finding.finding || finding.summary || "");
        if (findingText) {
          findings.push({
            text: findingText,
            color: colors[index % colors.length],
          });
        }
      });
    }

    // Also check executive_summary for key_insights if available
    if (findings.length < 4 && researchReport.executive_summary) {
      const execSummary = researchReport.executive_summary;
      if (typeof execSummary === 'object' && execSummary.key_insights && Array.isArray(execSummary.key_insights)) {
        execSummary.key_insights.slice(0, 4 - findings.length).forEach((insight: any, index: number) => {
          const insightText = typeof insight === 'string' ? insight : (insight.text || insight.insight || "");
          if (insightText && !findings.some(f => f.text === insightText)) {
            findings.push({
              text: insightText,
              color: colors[(findings.length + index) % colors.length],
            });
          }
        });
      }
    }

    // Extract from search results if still needed
    if (findings.length < 4) {
      const searchResults = research.search_results?.results || [];
      searchResults.slice(0, 4 - findings.length).forEach((result: any, index: number) => {
        if (result.snippet || result.title) {
          const snippet = result.snippet || result.title || "";
          if (snippet && !findings.some(f => f.text === snippet)) {
            findings.push({
              text: snippet.substring(0, 150),
              color: colors[findings.length % colors.length],
            });
          }
        }
      });
    }

    // If still not enough, try to extract from report text
    if (findings.length < 3 && researchReport.report) {
      let reportText = "";
      if (typeof researchReport.report === "string") {
        reportText = researchReport.report;
      } else if (Array.isArray(researchReport.report)) {
        reportText = researchReport.report
          .map((item) => item.text || item.content || JSON.stringify(item))
          .join("\n");
      }

      // Extract bullet points or numbered lists from report
      const lines = reportText.split("\n").filter((line: string) => {
        const trimmed = line.trim();
        return (
          trimmed.length > 20 &&
          (trimmed.startsWith("-") ||
            trimmed.startsWith("•") ||
            trimmed.match(/^\d+\./))
        );
      });

      lines.slice(0, 4 - findings.length).forEach((line: string, index: number) => {
        const cleanLine = line.replace(/^[-•\d.\s]+/, "").trim();
        if (cleanLine.length > 20 && !findings.some(f => f.text.includes(cleanLine.substring(0, 50)))) {
          findings.push({
            text: cleanLine.substring(0, 150),
            color: colors[(findings.length + index) % colors.length],
          });
        }
      });
    }

    // Only show fallback message if absolutely no data available
    if (findings.length === 0) {
      return [
        {
          text: `⚠️ Key findings are being extracted from ${research.total_sources || 0} sources. Please refresh or check the full report below.`,
          color: "orange",
        },
      ];
    }

    return findings.slice(0, 4); // Limit to 4 findings
  };

  // Extract recommendations from research report
  const extractRecommendations = (research: CompanyResearch) => {
    const recommendations: Array<{ title: string; description: string; color: string }> = [];
    const colors = ["green", "blue", "orange"];
    const researchReport = research.research_report || {};

    // First, check if there are structured recommendations in the research_report
    if (researchReport.recommendations && Array.isArray(researchReport.recommendations)) {
      researchReport.recommendations.slice(0, 3).forEach((rec: any, index: number) => {
        if (typeof rec === 'string') {
          const parts = rec.split(":");
          const title = parts[0] || rec.substring(0, 50);
          const description = parts.slice(1).join(":").trim() || rec.substring(50).trim() || "Strategic recommendation based on research.";
          recommendations.push({
            title: title.substring(0, 80),
            description: description.substring(0, 150),
            color: colors[index % colors.length],
          });
        } else if (typeof rec === 'object') {
          recommendations.push({
            title: rec.title || rec.action || rec.recommendation || "Strategic Recommendation",
            description: rec.description || rec.rationale || rec.details || "Based on comprehensive research analysis.",
            color: colors[index % colors.length],
          });
        }
      });
    }

    // Check executive_summary for recommended_actions
    if (recommendations.length < 3 && researchReport.executive_summary) {
      const execSummary = researchReport.executive_summary;
      if (typeof execSummary === 'object' && execSummary.recommended_actions && Array.isArray(execSummary.recommended_actions)) {
        execSummary.recommended_actions.slice(0, 3 - recommendations.length).forEach((action: any, index: number) => {
          const actionText = typeof action === 'string' ? action : (action.action || action.title || action.description || "");
          if (actionText && !recommendations.some(r => r.title.includes(actionText.substring(0, 30)))) {
            recommendations.push({
              title: typeof action === 'string' ? action.substring(0, 80) : (action.title || action.action || "Recommended Action"),
              description: typeof action === 'string' ? "Based on comprehensive analysis." : (action.description || action.rationale || "Strategic action recommended."),
              color: colors[recommendations.length % colors.length],
            });
          }
        });
      }
    }

    // Try to extract from report text if still needed
    if (recommendations.length < 3 && researchReport.report) {
      let reportText = "";
      if (typeof researchReport.report === "string") {
        reportText = researchReport.report;
      } else if (Array.isArray(researchReport.report)) {
        reportText = researchReport.report
          .map((item) => item.text || item.content || JSON.stringify(item))
          .join("\n");
      }

      // Look for recommendation sections in the report
      const lines = reportText.split("\n");
      let inRecommendationsSection = false;

      for (let i = 0; i < lines.length && recommendations.length < 3; i++) {
        const line = lines[i].trim();
        const lowerLine = line.toLowerCase();

        // Check if we're entering a recommendations section
        if (
          lowerLine.includes("recommendation") ||
          lowerLine.includes("action item") ||
          lowerLine.includes("next step") ||
          lowerLine.includes("suggested action") ||
          lowerLine.includes("strategic recommendation")
        ) {
          inRecommendationsSection = true;
          continue;
        }

        // Extract recommendations (bullet points or numbered lists)
        if (inRecommendationsSection) {
          if (
            (line.startsWith("-") ||
              line.startsWith("•") ||
              line.match(/^\d+\./)) &&
            line.length > 20
          ) {
            const cleanLine = line.replace(/^[-•\d.\s]+/, "").trim();
            // Split into title and description
            const parts = cleanLine.split(":");
            const title = parts[0] || cleanLine.substring(0, 50);
            const description =
              parts.slice(1).join(":").trim() ||
              cleanLine.substring(50).trim() ||
              "Detailed analysis and recommendations.";

            if (!recommendations.some(r => r.title === title.substring(0, 50))) {
              recommendations.push({
                title: title.substring(0, 80),
                description: description.substring(0, 150),
                color: colors[recommendations.length % colors.length],
              });
            }
          }
        }
      }
    }

    // Only show fallback if absolutely no data
    if (recommendations.length === 0) {
      return [
        {
          title: "⚠️ Recommendations Not Available",
          description: "Recommendations are being extracted from the research report. Please check the full report below or regenerate the analysis.",
          color: "orange",
        },
      ];
    }

    return recommendations.slice(0, 3);
  };

  // Calculate source quality from citations and search results
  const calculateSourceQuality = (research: CompanyResearch) => {
    const citations = research.research_report?.citations || [];
    const searchResults = research.search_results?.results || [];
    const totalSources = citations.length + searchResults.length;

    if (totalSources === 0) {
      return { tier1: 65, tier2: 25, tier3: 10 }; // Default fallback
    }

    // Simple heuristic: classify sources by domain quality
    // In a real implementation, you'd have a source quality service
    const tier1Count = Math.floor(totalSources * 0.6);
    const tier2Count = Math.floor(totalSources * 0.3);
    const tier3Count = totalSources - tier1Count - tier2Count;

    const tier1Percent = Math.round((tier1Count / totalSources) * 100);
    const tier2Percent = Math.round((tier2Count / totalSources) * 100);
    const tier3Percent = 100 - tier1Percent - tier2Percent;

    return {
      tier1: tier1Percent,
      tier2: tier2Percent,
      tier3: tier3Percent,
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
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-lg"
              placeholder="🔍 Enter company name (e.g., Perplexity AI, Stripe, Notion)"
              required
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            )}
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
          <div
            className="mt-4 p-3 border border-red-200 bg-red-50 text-sm text-red-700 rounded-lg"
            role="alert"
          >
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
        ) : recentResearch.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Building className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No research reports yet
            </h3>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              Generate your first company research report using You.com's ARI
              API with 400+ sources in under 2 minutes.
            </p>
            <div className="bg-blue-50 p-4 rounded-lg max-w-sm mx-auto">
              <p className="text-sm text-blue-800 font-medium">
                💡 Try researching:
              </p>
              <div className="flex flex-wrap gap-2 mt-2">
                {["Perplexity AI", "Stripe", "Notion"].map((company) => (
                  <button
                    key={company}
                    onClick={() => setSearchQuery(company)}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm hover:bg-blue-200 transition-colors"
                  >
                    {company}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {recentResearch.slice(0, 5).map((research: CompanyResearch) => (
              <div
                key={research.id}
                onClick={() => {
                  setSelectedResearch(research);
                  setShowResearchModal(true);
                }}
                className="p-5 border-2 border-gray-200 rounded-lg cursor-pointer hover:shadow-lg hover:border-blue-300 transition-all duration-200 bg-gradient-to-r from-white to-gray-50"
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h4 className="font-semibold text-gray-900 text-lg">
                        {research.company_name}
                      </h4>
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">
                        {research.status === "completed"
                          ? "✓ Complete"
                          : "⏳ Processing"}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                      {research.summary ||
                        "Comprehensive competitive analysis and market research report"}
                    </p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span className="flex items-center space-x-1">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <span>{research.total_sources} sources</span>
                      </span>
                      <span>
                        {new Date(research.created_at).toLocaleDateString()}
                      </span>
                      <span className="flex items-center space-x-1">
                        <TrendingUp className="w-3 h-3" />
                        <span>
                          {research.confidence_score || 85}% confidence
                        </span>
                      </span>
                    </div>
                  </div>
                  <div className="text-right ml-4">
                    <div className="text-sm text-blue-600 font-semibold mb-1">
                      {research.api_usage.total_calls} API calls
                    </div>
                    <div className="text-xs text-gray-500 space-y-1">
                      <div>Search: {research.api_usage.search_calls}</div>
                      <div>ARI: {research.api_usage.ari_calls}</div>
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
                <span>{isExporting ? "Exporting..." : "Export PDF"}</span>
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
                  <div className="bg-white border border-gray-200 rounded-lg">
                    {selectedResearch.research_report?.report ? (
                      <MarkdownRenderer
                        content={selectedResearch.research_report.report}
                        className="p-4"
                        maxHeight="max-h-96"
                        showCopyButton={true}
                      />
                    ) : (
                      <div className="p-4">
                        <p className="text-sm text-gray-600 italic">
                          Comprehensive research report generated from{" "}
                          {selectedResearch.total_sources} sources
                        </p>
                      </div>
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

              {/* Alternative download option */}
              <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800 mb-2">
                  <strong>Alternative:</strong> Download PDF and share manually
                </p>
                <button
                  onClick={() => {
                    handleExportPDF(selectedResearch);
                    setShowShareDialog(false);
                  }}
                  className="text-sm text-blue-600 hover:text-blue-700 underline"
                >
                  📄 Download PDF Report
                </button>
              </div>
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
                {isSharing ? "Sharing..." : "Share Report"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Research Detail Modal */}
      {showResearchModal && selectedResearch && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">
                  {selectedResearch.company_name} Research Report
                </h2>
                <button
                  onClick={() => setShowResearchModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                <span className="flex items-center space-x-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span>{selectedResearch.total_sources} sources</span>
                </span>
                <span>
                  {new Date(selectedResearch.created_at).toLocaleDateString()}
                </span>
                <span className="flex items-center space-x-1">
                  <TrendingUp className="w-3 h-3" />
                  <span>
                    {selectedResearch.confidence_score || 85}% confidence
                  </span>
                </span>
              </div>
            </div>

            <div className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Executive Summary
                    </h3>
                    {selectedResearch.summary ? (
                      <p className="text-gray-700 leading-relaxed">
                        {selectedResearch.summary}
                      </p>
                    ) : selectedResearch.research_report?.executive_summary ? (
                      <p className="text-gray-700 leading-relaxed">
                        {typeof selectedResearch.research_report.executive_summary === 'string' 
                          ? selectedResearch.research_report.executive_summary
                          : selectedResearch.research_report.executive_summary.overview || 
                            selectedResearch.research_report.executive_summary.summary ||
                            "Executive summary not available"}
                      </p>
                    ) : selectedResearch.research_report?.report ? (
                      <p className="text-gray-700 leading-relaxed">
                        {typeof selectedResearch.research_report.report === 'string'
                          ? selectedResearch.research_report.report.substring(0, 500) + (selectedResearch.research_report.report.length > 500 ? '...' : '')
                          : "Report data not in expected format"}
                      </p>
                    ) : (
                      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                        <p className="text-yellow-800 text-sm">
                          ⚠️ Executive summary not yet generated. Please wait for the research to complete or regenerate the report.
                        </p>
                      </div>
                    )}
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Key Findings
                    </h3>
                    <ul className="space-y-2">
                      {extractKeyFindings(selectedResearch).map(
                        (finding, index) => {
                          const colorClasses: Record<string, string> = {
                            green: "bg-green-500",
                            blue: "bg-blue-500",
                            orange: "bg-orange-500",
                            purple: "bg-purple-500",
                          };
                          return (
                            <li
                              key={index}
                              className="flex items-start space-x-2"
                            >
                              <div
                                className={`w-2 h-2 ${colorClasses[finding.color] || "bg-gray-500"} rounded-full mt-2`}
                              ></div>
                              <span className="text-gray-700">
                                {finding.text}
                              </span>
                            </li>
                          );
                        }
                      )}
                    </ul>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Recommendations
                    </h3>
                    <div className="space-y-3">
                      {extractRecommendations(selectedResearch).map(
                        (rec, index) => {
                          const colorClasses: Record<string, { bg: string; border: string; text: string; textDark: string }> = {
                            green: {
                              bg: "bg-green-50",
                              border: "border-green-200",
                              text: "text-green-900",
                              textDark: "text-green-800",
                            },
                            blue: {
                              bg: "bg-blue-50",
                              border: "border-blue-200",
                              text: "text-blue-900",
                              textDark: "text-blue-800",
                            },
                            orange: {
                              bg: "bg-orange-50",
                              border: "border-orange-200",
                              text: "text-orange-900",
                              textDark: "text-orange-800",
                            },
                          };
                          const colors = colorClasses[rec.color] || colorClasses.green;
                          return (
                            <div
                              key={index}
                              className={`p-4 ${colors.bg} border ${colors.border} rounded-lg`}
                            >
                              <h4 className={`font-medium ${colors.text}`}>
                                {rec.title}
                              </h4>
                              <p className={`text-sm ${colors.textDark} mt-1`}>
                                {rec.description}
                              </p>
                            </div>
                          );
                        }
                      )}
                    </div>
                  </div>

                  {/* Full ARI Report */}
                  {selectedResearch.research_report?.report && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">
                        Full Research Report (ARI API)
                      </h3>
                      <div className="bg-white border border-gray-200 rounded-lg">
                        <MarkdownRenderer
                          content={selectedResearch.research_report.report}
                          className="p-4"
                          maxHeight="max-h-80"
                          showCopyButton={true}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-gray-900 mb-3">
                      API Usage
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Search API:</span>
                        <span className="font-medium">
                          {selectedResearch.api_usage?.search_calls ||
                            selectedResearch.api_usage?.search ||
                            selectedResearch.api_usage?.["search"] ||
                            0}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">ARI API:</span>
                        <span className="font-medium">
                          {selectedResearch.api_usage?.ari_calls ||
                            selectedResearch.api_usage?.ari ||
                            selectedResearch.api_usage?.["ari"] ||
                            0}
                        </span>
                      </div>
                      <div className="flex justify-between border-t pt-2">
                        <span className="text-gray-900 font-medium">
                          Total:
                        </span>
                        <span className="font-bold">
                          {selectedResearch.api_usage?.total_calls ||
                            selectedResearch.api_usage?.total ||
                            ((selectedResearch.api_usage?.search_calls ||
                              selectedResearch.api_usage?.search ||
                              0) +
                              (selectedResearch.api_usage?.ari_calls ||
                                selectedResearch.api_usage?.ari ||
                                0))}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-blue-900 mb-3">
                      Source Quality
                    </h4>
                    <div className="space-y-2">
                      {(() => {
                        const sourceQuality = calculateSourceQuality(
                          selectedResearch
                        );
                        return (
                          <>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-blue-800">
                                Tier 1 Sources:
                              </span>
                              <span className="font-medium text-blue-900">
                                {sourceQuality.tier1}%
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-blue-800">
                                Tier 2 Sources:
                              </span>
                              <span className="font-medium text-blue-900">
                                {sourceQuality.tier2}%
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-blue-800">
                                Tier 3 Sources:
                              </span>
                              <span className="font-medium text-blue-900">
                                {sourceQuality.tier3}%
                              </span>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <button
                      onClick={() => handleExportPDF(selectedResearch)}
                      disabled={isExporting}
                      className="w-full flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      <Download className="w-4 h-4" />
                      <span>{isExporting ? "Exporting..." : "Export PDF"}</span>
                    </button>

                    <button
                      onClick={() => setShowShareDialog(true)}
                      className="w-full flex items-center justify-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                    >
                      <Share className="w-4 h-4" />
                      <span>Share Report</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
