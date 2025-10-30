"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  Search,
  Star,
  Users,
  TrendingUp,
  Filter,
  ChevronRight,
  Check,
} from "lucide-react";
import { api } from "@/lib/api";

interface IndustryTemplate {
  id: number;
  name: string;
  industry_sector: string;
  description: string;
  template_config: {
    default_competitors: string[];
    default_keywords: string[];
    risk_categories: string[];
    kpi_metrics: string[];
  };
  usage_count: number;
  rating: number;
  created_at: string;
}

interface IndustryTemplateSelectorProps {
  onTemplateSelect: (template: IndustryTemplate) => void;
  selectedTemplateId?: number;
}

export function IndustryTemplateSelector({
  onTemplateSelect,
  selectedTemplateId,
}: IndustryTemplateSelectorProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIndustry, setSelectedIndustry] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"popularity" | "rating" | "recent">(
    "popularity"
  );

  const { data: templates, isLoading } = useQuery({
    queryKey: ["industryTemplates", searchQuery, selectedIndustry, sortBy],
    queryFn: () => {
      const params: any = {};
      if (searchQuery) params.search = searchQuery;
      if (selectedIndustry !== "all") params.industry = selectedIndustry;
      params.sort_by = sortBy;

      return api
        .get("/api/v1/industry_templates/", { params })
        .then((res) => res.data.items);
    },
    staleTime: 60000, // 1 minute
  });

  const industries = [
    "all",
    "SaaS",
    "FinTech",
    "HealthTech",
    "E-commerce",
    "Manufacturing",
    "Energy",
    "Media",
    "Consulting",
  ];

  const getIndustryIcon = (industry: string) => {
    const iconMap: Record<string, string> = {
      SaaS: "💻",
      FinTech: "💰",
      HealthTech: "🏥",
      "E-commerce": "🛒",
      Manufacturing: "🏭",
      Energy: "⚡",
      Media: "📺",
      Consulting: "💼",
    };
    return iconMap[industry] || "🏢";
  };

  const filteredTemplates = templates || [];

  if (isLoading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <Building2 className="w-5 h-5 mr-2 text-blue-600" />
          Industry Templates
        </h3>
        <div className="text-sm text-gray-600">
          {filteredTemplates.length} templates available
        </div>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex flex-wrap gap-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-700">Industry:</span>
            <select
              value={selectedIndustry}
              onChange={(e) => setSelectedIndustry(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {industries.map((industry) => (
                <option key={industry} value={industry}>
                  {industry === "all" ? "All Industries" : industry}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gray-700">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) =>
                setSortBy(e.target.value as "popularity" | "rating" | "recent")
              }
              className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="popularity">Most Popular</option>
              <option value="rating">Highest Rated</option>
              <option value="recent">Most Recent</option>
            </select>
          </div>
        </div>
      </div>

      {/* Templates Grid */}
      {filteredTemplates.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template: IndustryTemplate) => (
            <div
              key={template.id}
              onClick={() => onTemplateSelect(template)}
              className={`p-6 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                selectedTemplateId === template.id
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">
                    {getIndustryIcon(template.industry_sector)}
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">
                      {template.name}
                    </h4>
                    <div className="text-sm text-gray-600">
                      {template.industry_sector}
                    </div>
                  </div>
                </div>
                {selectedTemplateId === template.id && (
                  <Check className="w-5 h-5 text-blue-600" />
                )}
              </div>

              <p className="text-sm text-gray-700 mb-4 line-clamp-3">
                {template.description}
              </p>

              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Competitors:</span>
                  <span className="font-medium">
                    {template.template_config.default_competitors?.length || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Keywords:</span>
                  <span className="font-medium">
                    {template.template_config.default_keywords?.length || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Risk Categories:</span>
                  <span className="font-medium">
                    {template.template_config.risk_categories?.length || 0}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Users className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-600">
                      {template.usage_count} uses
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Star className="w-4 h-4 text-yellow-400 fill-current" />
                    <span className="text-sm font-medium">
                      {template.rating.toFixed(1)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <Building2 className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-lg mb-2">No templates found</p>
          <p className="text-sm">
            {searchQuery || selectedIndustry !== "all"
              ? "Try adjusting your search or filters."
              : "Industry templates will appear here once they're created."}
          </p>
        </div>
      )}
    </div>
  );
}
