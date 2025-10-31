import React from "react";
import {
  ClockIcon,
  BoltIcon,
  CheckCircleIcon,
  RocketLaunchIcon,
} from "@heroicons/react/24/outline";

interface Metric {
  icon: React.ComponentType<{ className?: string }>;
  value: string;
  label: string;
  color: string;
  detail: string;
  caseStudyLink?: string;
}

const SuccessMetrics: React.FC = () => {
  const metrics: Metric[] = [
    {
      icon: ClockIcon,
      value: "10+ hours/week",
      label: "Time Savings Potential",
      color: "green",
      detail: "Automated competitive monitoring",
    },
    {
      icon: BoltIcon,
      value: "<5 minutes",
      label: "Real-time Detection",
      color: "blue",
      detail: "You.com News API integration",
    },
    {
      icon: CheckCircleIcon,
      value: "400+ sources",
      label: "Research Depth",
      color: "purple",
      detail: "ARI API comprehensive analysis",
    },
    {
      icon: RocketLaunchIcon,
      value: "4 APIs",
      label: "You.com Integration",
      color: "orange",
      detail: "News, Search, Chat, ARI",
    },
  ];

  const getColorClasses = (color: string) => {
    switch (color) {
      case "green":
        return "bg-green-50 border-green-200 text-green-700";
      case "blue":
        return "bg-blue-50 border-blue-200 text-blue-700";
      case "purple":
        return "bg-purple-50 border-purple-200 text-purple-700";
      case "orange":
        return "bg-orange-50 border-orange-200 text-orange-700";
      default:
        return "bg-gray-50 border-gray-200 text-gray-700";
    }
  };

  const getIconColor = (color: string) => {
    switch (color) {
      case "green":
        return "text-green-600";
      case "blue":
        return "text-blue-600";
      case "purple":
        return "text-purple-600";
      case "orange":
        return "text-orange-600";
      default:
        return "text-gray-600";
    }
  };

  return (
    <div className="bg-white p-8 rounded-lg shadow-sm">
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          Platform Capabilities
        </h3>
        <p className="text-gray-600">
          Powered by You.com's comprehensive API suite for competitive
          intelligence
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric, index) => {
          const Icon = metric.icon;

          return (
            <div
              key={index}
              className={`p-6 rounded-lg border-2 transition-all hover:shadow-md ${getColorClasses(
                metric.color
              )}`}
            >
              <div className="flex items-center justify-center mb-4">
                <div className={`p-3 rounded-full bg-white shadow-sm`}>
                  <Icon className={`w-8 h-8 ${getIconColor(metric.color)}`} />
                </div>
              </div>

              <div className="text-center">
                <div className="text-2xl font-bold mb-1">{metric.value}</div>
                <div className="font-semibold mb-2">{metric.label}</div>
                <div className="text-sm opacity-75 mb-3">{metric.detail}</div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8 text-center">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <p className="text-sm text-blue-800">
            <strong>🚀 Demo Platform:</strong> Experience the full power of
            You.com's API suite integrated into a comprehensive competitive
            intelligence platform. Try the sample data or connect your own API
            key to see real-time capabilities.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SuccessMetrics;
