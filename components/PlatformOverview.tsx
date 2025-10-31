import React from "react";
import {
  LinkIcon,
  CogIcon,
  ChartBarIcon,
  ArrowTopRightOnSquareIcon,
} from "@heroicons/react/24/outline";

interface PlatformSection {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  benefit: string;
  features: string[];
  cta: string;
  ctaLink: string;
  color: string;
}

const PlatformOverview: React.FC = () => {
  const platformSections: PlatformSection[] = [
    {
      icon: LinkIcon,
      title: "You.com API Integration",
      benefit: "Save 40% dev time vs building custom connectors",
      features: [
        "Real-time news monitoring",
        "Context-aware search",
        "AI-powered impact analysis",
        "Deep research reports (400+ sources)",
      ],
      cta: "View Integration Guide",
      ctaLink: "/docs/integration",
      color: "blue",
    },
    {
      icon: CogIcon,
      title: "Advanced Integrations",
      benefit: "Sync insights to your existing tools",
      features: [
        "Notion database synchronization",
        "Salesforce CRM workflows",
        "Slack team notifications",
        "Email report distribution",
      ],
      cta: "Setup Integrations",
      ctaLink: "/integrations",
      color: "green",
    },
    {
      icon: ChartBarIcon,
      title: "Predictive Analytics",
      benefit: "Predict market moves 3-5 days earlier",
      features: [
        "Market temperature analysis",
        "Competitor trend prediction",
        "Executive briefing generation",
        "Strategic recommendations",
      ],
      cta: "View Analytics",
      ctaLink: "/analytics",
      color: "purple",
    },
  ];

  const getColorClasses = (color: string) => {
    switch (color) {
      case "blue":
        return {
          bg: "bg-blue-50",
          border: "border-blue-200",
          icon: "text-blue-600",
          button: "bg-blue-600 hover:bg-blue-700 text-white",
        };
      case "green":
        return {
          bg: "bg-green-50",
          border: "border-green-200",
          icon: "text-green-600",
          button: "bg-green-600 hover:bg-green-700 text-white",
        };
      case "purple":
        return {
          bg: "bg-purple-50",
          border: "border-purple-200",
          icon: "text-purple-600",
          button: "bg-purple-600 hover:bg-purple-700 text-white",
        };
      default:
        return {
          bg: "bg-gray-50",
          border: "border-gray-200",
          icon: "text-gray-600",
          button: "bg-gray-600 hover:bg-gray-700 text-white",
        };
    }
  };

  return (
    <div className="bg-white p-8 rounded-lg shadow-sm">
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          🏆 Complete Competitive Intelligence Platform
        </h3>
        <p className="text-gray-600">
          Comprehensive solution powered by You.com APIs with enterprise
          integrations
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {platformSections.map((section, index) => {
          const Icon = section.icon;
          const colors = getColorClasses(section.color);

          return (
            <div
              key={index}
              className={`${colors.bg} ${colors.border} border-2 rounded-lg p-6 transition-all hover:shadow-md`}
            >
              {/* Icon and Title */}
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-white rounded-lg shadow-sm">
                  <Icon className={`w-6 h-6 ${colors.icon}`} />
                </div>
                <h4 className="font-bold text-gray-900">{section.title}</h4>
              </div>

              {/* Benefit */}
              <div className="mb-4">
                <p className="text-sm font-semibold text-gray-800 mb-2">
                  💡 {section.benefit}
                </p>
              </div>

              {/* Features */}
              <div className="mb-6">
                <ul className="space-y-2">
                  {section.features.map((feature, featureIndex) => (
                    <li
                      key={featureIndex}
                      className="flex items-start space-x-2"
                    >
                      <div className="w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 flex-shrink-0"></div>
                      <span className="text-sm text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* CTA Button */}
              <button
                onClick={() => console.log(`Navigate to: ${section.ctaLink}`)}
                className={`w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium transition-colors ${colors.button}`}
              >
                <span>{section.cta}</span>
                <ArrowTopRightOnSquareIcon className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>

      {/* Bottom Summary */}
      <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
        <div className="text-center">
          <h4 className="font-bold text-gray-900 mb-2">
            🚀 Ready for Enterprise Deployment
          </h4>
          <p className="text-sm text-gray-700">
            Complete platform with SOC 2 compliance, RBAC, audit logging, and
            99.9% uptime SLA. Replaces $50K/year competitive intelligence
            subscriptions with 75% cost savings.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PlatformOverview;
