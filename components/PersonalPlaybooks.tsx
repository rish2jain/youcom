import React from "react";
import { useState } from "react";
import {
  PlusIcon,
  UserIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  CurrencyDollarIcon,
  BuildingOfficeIcon,
  AcademicCapIcon,
} from "@heroicons/react/24/outline";

interface Playbook {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  badge: string;
  whoItsFor: string;
  features: string[];
  isRecommended?: boolean;
}

interface PersonalPlaybooksProps {
  onSelectPlaybook: (playbookId: string) => void;
  onCreatePlaybook: () => void;
}

const PersonalPlaybooks: React.FC<PersonalPlaybooksProps> = ({
  onSelectPlaybook,
  onCreatePlaybook,
}) => {
  const [activeFilter, setActiveFilter] = useState("recommended");

  const defaultPlaybooks: Playbook[] = [
    {
      id: "startup-investor",
      name: "Startup Investor",
      description:
        "Track funding rounds, market validation, and competitive positioning for investment decisions",
      icon: CurrencyDollarIcon,
      badge: "Popular",
      whoItsFor: "VCs, Angel Investors, Investment Analysts",
      features: [
        "Funding round tracking",
        "Market size analysis",
        "Competitive landscape",
        "Team background checks",
      ],
      isRecommended: true,
    },
    {
      id: "product-manager",
      name: "Product Manager",
      description:
        "Monitor feature launches, user feedback, and competitive analysis for product strategy",
      icon: ChartBarIcon,
      badge: "Recommended",
      whoItsFor: "Product Managers, Product Owners, Strategy Teams",
      features: [
        "Feature comparison",
        "Launch tracking",
        "User sentiment analysis",
        "Pricing intelligence",
      ],
      isRecommended: true,
    },
    {
      id: "competitor-analyst",
      name: "Competitor Analyst",
      description:
        "Deep competitive intelligence and market positioning analysis for strategic planning",
      icon: MagnifyingGlassIcon,
      badge: "Advanced",
      whoItsFor: "Strategy Teams, Market Researchers, Consultants",
      features: [
        "SWOT analysis",
        "Market positioning",
        "Threat assessment",
        "Strategic recommendations",
      ],
      isRecommended: true,
    },
    {
      id: "job-seeker",
      name: "Job Seeker",
      description:
        "Research companies, interview preparation, and industry trend analysis",
      icon: UserIcon,
      badge: "New",
      whoItsFor: "Job Seekers, Career Changers, Students",
      features: [
        "Company culture analysis",
        "Interview prep",
        "Salary benchmarking",
        "Growth trajectory",
      ],
      isRecommended: false,
    },
    {
      id: "sales-professional",
      name: "Sales Professional",
      description:
        "Prospect research, competitive intelligence for deals, and market opportunity analysis",
      icon: BuildingOfficeIcon,
      badge: "Business",
      whoItsFor: "Sales Reps, Account Managers, Business Development",
      features: [
        "Prospect intelligence",
        "Deal competitive analysis",
        "Market opportunity sizing",
        "Decision maker mapping",
      ],
      isRecommended: false,
    },
    {
      id: "academic-researcher",
      name: "Academic Researcher",
      description:
        "Industry analysis, trend tracking, and comprehensive market research for academic work",
      icon: AcademicCapIcon,
      badge: "Research",
      whoItsFor: "Researchers, Academics, Graduate Students",
      features: [
        "Industry trend analysis",
        "Market research",
        "Citation tracking",
        "Data export for papers",
      ],
      isRecommended: false,
    },
  ];

  const filterOptions = [
    { id: "recommended", label: "Recommended", count: 3 },
    { id: "my-playbooks", label: "My Playbooks", count: 0 },
    { id: "browse-all", label: "Browse All", count: 6 },
  ];

  const getFilteredPlaybooks = () => {
    switch (activeFilter) {
      case "recommended":
        return defaultPlaybooks.filter((p) => p.isRecommended);
      case "my-playbooks":
        return []; // User's custom playbooks would go here
      case "browse-all":
        return defaultPlaybooks;
      default:
        return defaultPlaybooks;
    }
  };

  const getBadgeColor = (badge: string) => {
    switch (badge.toLowerCase()) {
      case "popular":
        return "bg-green-100 text-green-700";
      case "recommended":
        return "bg-blue-100 text-blue-700";
      case "advanced":
        return "bg-purple-100 text-purple-700";
      case "new":
        return "bg-yellow-100 text-yellow-700";
      case "business":
        return "bg-orange-100 text-orange-700";
      case "research":
        return "bg-indigo-100 text-indigo-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            Personal Playbooks
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Choose a playbook to customize what data matters to you
          </p>
        </div>

        <button
          onClick={onCreatePlaybook}
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          <span>Create Playbook</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-0">
          {filterOptions.map((filter) => (
            <button
              key={filter.id}
              onClick={() => setActiveFilter(filter.id)}
              className={`px-4 py-3 border-b-2 font-medium text-sm transition-colors ${
                activeFilter === filter.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {filter.label}
              {filter.count > 0 && (
                <span
                  className={`ml-2 px-2 py-1 text-xs rounded-full ${
                    activeFilter === filter.id
                      ? "bg-blue-100 text-blue-600"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {filter.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Playbook Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {getFilteredPlaybooks().map((playbook) => {
          const Icon = playbook.icon;

          return (
            <div
              key={playbook.id}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => onSelectPlaybook(playbook.id)}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-50 rounded-lg">
                    <Icon className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900">
                      {playbook.name}
                    </h4>
                    <span
                      className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getBadgeColor(
                        playbook.badge
                      )}`}
                    >
                      {playbook.badge}
                    </span>
                  </div>
                </div>
              </div>

              {/* Description */}
              <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                {playbook.description}
              </p>

              {/* Who It's For */}
              <div className="mb-4">
                <div className="flex items-center space-x-2 mb-2">
                  <UserIcon className="w-4 h-4 text-gray-400" />
                  <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Who it's for
                  </span>
                </div>
                <p className="text-sm text-gray-700">{playbook.whoItsFor}</p>
              </div>

              {/* Key Features */}
              <div className="mb-6">
                <h5 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  Key Features
                </h5>
                <div className="space-y-1">
                  {playbook.features.slice(0, 3).map((feature, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                      <span className="text-xs text-gray-600">{feature}</span>
                    </div>
                  ))}
                  {playbook.features.length > 3 && (
                    <div className="flex items-center space-x-2">
                      <div className="w-1.5 h-1.5 bg-gray-300 rounded-full"></div>
                      <span className="text-xs text-gray-500">
                        +{playbook.features.length - 3} more features
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* CTA Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectPlaybook(playbook.id);
                }}
                className="w-full bg-blue-600 text-white py-2.5 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
              >
                Try This Playbook
              </button>
            </div>
          );
        })}
      </div>

      {/* Empty State for My Playbooks */}
      {activeFilter === "my-playbooks" &&
        getFilteredPlaybooks().length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <PlusIcon className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No custom playbooks yet
            </h3>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              Create your first custom playbook to tailor the analysis to your
              specific needs and workflow.
            </p>
            <button
              onClick={onCreatePlaybook}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Create Your First Playbook
            </button>
          </div>
        )}
    </div>
  );
};

export default PersonalPlaybooks;
