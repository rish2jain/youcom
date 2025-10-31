import React from "react";
import { useState } from "react";
import {
  ChevronDownIcon,
  QuestionMarkCircleIcon,
} from "@heroicons/react/24/outline";

interface HeaderProps {
  onStartAnalysis: () => void;
  currentPath?: string;
}

const Header: React.FC<HeaderProps> = ({ onStartAnalysis, currentPath }) => {
  const [showHelp, setShowHelp] = useState(false);

  const helpItems = [
    {
      title: "News API",
      description: "Real-time competitive intelligence monitoring",
      icon: "📰",
    },
    {
      title: "Search API",
      description: "Context enrichment and background research",
      icon: "🔍",
    },
    {
      title: "Custom Agents",
      description: "AI-powered impact analysis and extraction",
      icon: "🤖",
    },
    {
      title: "ARI Reports",
      description: "Deep research with 400+ sources in 2 minutes",
      icon: "📊",
    },
  ];

  const getBreadcrumbs = (currentPath?: string) => {
    const pathMap: Record<string, string> = {
      dashboard: "Intelligence Dashboard",
      demo: "API Showcase Demo",
      research: "Company Research",
      monitoring: "Competitive Monitoring",
      analytics: "Predictive Analytics",
      integrations: "Integration Management",
      settings: "Settings & Configuration",
    };

    return [
      { label: "Enterprise CIA", href: "/" },
      {
        label: pathMap[currentPath || "home"] || "Home",
        href: currentPath === "home" ? "/" : `/${currentPath}`,
      },
    ];
  };

  const breadcrumbs = getBreadcrumbs(currentPath);

  return (
    <div className="bg-white border-b border-gray-200">
      {/* Main Header */}
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left Side - Logo & Primary CTA */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">CIA</span>
              </div>
              <h1 className="text-xl font-semibold text-gray-900">
                Competitive Intelligence Agent
              </h1>
            </div>

            <button
              onClick={onStartAnalysis}
              className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <span>⚡</span>
              <span>Start Analysis</span>
            </button>
          </div>

          {/* Right Side - Help & User Menu */}
          <div className="flex items-center space-x-4">
            {/* How it Works Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowHelp(!showHelp)}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <QuestionMarkCircleIcon className="w-5 h-5" />
                <span className="text-sm font-medium">How it works</span>
                <ChevronDownIcon className="w-4 h-4" />
              </button>

              {showHelp && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 mb-3">
                      Powered by You.com APIs
                    </h3>
                    <div className="space-y-3">
                      {helpItems.map((item, index) => (
                        <div key={index} className="flex items-start space-x-3">
                          <span className="text-lg">{item.icon}</span>
                          <div>
                            <h4 className="font-medium text-gray-900 text-sm">
                              {item.title}
                            </h4>
                            <p className="text-gray-600 text-xs">
                              {item.description}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 pt-3 border-t border-gray-100">
                      <a
                        href="/docs"
                        className="text-blue-600 text-sm font-medium hover:text-blue-700"
                      >
                        View full documentation →
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* User Menu */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                <span className="text-gray-600 text-sm font-medium">JD</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Breadcrumb Navigation */}
      {currentPath && (
        <div className="px-6 py-2 bg-gray-50 border-t border-gray-100">
          <nav className="flex items-center space-x-2 text-sm">
            {breadcrumbs.map((crumb, index) => (
              <React.Fragment key={index}>
                <a
                  href={crumb.href}
                  className={`${
                    index === breadcrumbs.length - 1
                      ? "text-gray-900 font-medium"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  {crumb.label}
                </a>
                {index < breadcrumbs.length - 1 && (
                  <span className="text-gray-400">/</span>
                )}
              </React.Fragment>
            ))}
          </nav>
        </div>
      )}
    </div>
  );
};

export default Header;
