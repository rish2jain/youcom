import React from "react";
import {
  BuildingOfficeIcon,
  UserIcon,
  BoltIcon,
  MagnifyingGlassIcon,
  ChatBubbleLeftRightIcon,
  DocumentTextIcon,
  ArrowRightIcon,
  CheckCircleIcon,
} from "@heroicons/react/24/outline";

interface WorkflowStep {
  id: number;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  api?: string;
}

interface Workflow {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  steps: WorkflowStep[];
  metrics: string;
}

const DemoWorkflows: React.FC = () => {
  const workflows: Workflow[] = [
    {
      id: "enterprise",
      title: "Enterprise Workflow",
      description:
        "Real-time competitive monitoring for product teams and executives",
      icon: BuildingOfficeIcon,
      steps: [
        {
          id: 1,
          title: "Create Watchlist",
          description: "Add competitors (OpenAI, Anthropic, Google)",
          icon: MagnifyingGlassIcon,
          color: "blue",
        },
        {
          id: 2,
          title: "News Monitoring",
          description: "Real-time announcement detection",
          icon: BoltIcon,
          color: "green",
          api: "News API",
        },
        {
          id: 3,
          title: "Context Enrichment",
          description: "Background research and validation",
          icon: MagnifyingGlassIcon,
          color: "purple",
          api: "Search API",
        },
        {
          id: 4,
          title: "Impact Analysis",
          description: "AI-powered competitive impact assessment",
          icon: ChatBubbleLeftRightIcon,
          color: "orange",
          api: "Custom Agents",
        },
        {
          id: 5,
          title: "Deep Research",
          description: "Comprehensive reports from 400+ sources",
          icon: DocumentTextIcon,
          color: "red",
          api: "ARI API",
        },
        {
          id: 6,
          title: "Impact Cards",
          description: "Actionable insights with risk scores",
          icon: CheckCircleIcon,
          color: "green",
        },
      ],
      metrics: "Save 10+ hours/week, detect moves 3-5 days earlier",
    },
    {
      id: "individual",
      title: "Individual Workflow",
      description:
        "Instant company research for job seekers, investors, and entrepreneurs",
      icon: UserIcon,
      steps: [
        {
          id: 1,
          title: "Enter Company",
          description: "Type any company name for research",
          icon: MagnifyingGlassIcon,
          color: "blue",
        },
        {
          id: 2,
          title: "Profile Gathering",
          description: "Company context and background",
          icon: MagnifyingGlassIcon,
          color: "purple",
          api: "Search API",
        },
        {
          id: 3,
          title: "Deep Research",
          description: "Generate comprehensive analysis",
          icon: DocumentTextIcon,
          color: "red",
          api: "ARI API",
        },
        {
          id: 4,
          title: "Company Analysis",
          description: "Complete profile with insights",
          icon: CheckCircleIcon,
          color: "green",
        },
        {
          id: 5,
          title: "Export & Share",
          description: "PDF reports for presentations",
          icon: DocumentTextIcon,
          color: "blue",
        },
      ],
      metrics: "Complete research in <2 minutes vs 2-4 hours manually",
    },
  ];

  const getStepColor = (color: string) => {
    switch (color) {
      case "blue":
        return "bg-blue-500 text-white";
      case "green":
        return "bg-green-500 text-white";
      case "purple":
        return "bg-purple-500 text-white";
      case "orange":
        return "bg-orange-500 text-white";
      case "red":
        return "bg-red-500 text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  const getApiColor = (api: string) => {
    switch (api) {
      case "News API":
        return "bg-blue-100 text-blue-700";
      case "Search API":
        return "bg-green-100 text-green-700";
      case "Custom Agents":
        return "bg-purple-100 text-purple-700";
      case "ARI API":
        return "bg-orange-100 text-orange-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-8 rounded-lg border border-blue-200">
      <div className="text-center mb-8">
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          🎬 Interactive Demo Workflows
        </h3>
        <p className="text-gray-600">
          See how You.com APIs work together to deliver competitive intelligence
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {workflows.map((workflow) => {
          const WorkflowIcon = workflow.icon;

          return (
            <div
              key={workflow.id}
              className="bg-white rounded-lg p-6 shadow-sm"
            >
              {/* Workflow Header */}
              <div className="flex items-center space-x-3 mb-4">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <WorkflowIcon className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h4 className="font-bold text-gray-900">{workflow.title}</h4>
                  <p className="text-sm text-gray-600">
                    {workflow.description}
                  </p>
                </div>
              </div>

              {/* Workflow Steps */}
              <div className="space-y-4 mb-6">
                {workflow.steps.map((step, index) => {
                  const StepIcon = step.icon;
                  const isLast = index === workflow.steps.length - 1;

                  return (
                    <div key={step.id} className="relative">
                      <div className="flex items-start space-x-4">
                        {/* Step Icon */}
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center ${getStepColor(
                            step.color
                          )} flex-shrink-0`}
                        >
                          <StepIcon className="w-5 h-5" />
                        </div>

                        {/* Step Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-1">
                            <h5 className="font-semibold text-gray-900 text-sm">
                              {step.id}. {step.title}
                            </h5>
                            {step.api && (
                              <span
                                className={`px-2 py-1 text-xs font-medium rounded-full ${getApiColor(
                                  step.api
                                )}`}
                              >
                                {step.api}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-gray-600">
                            {step.description}
                          </p>
                        </div>
                      </div>

                      {/* Arrow Connector */}
                      {!isLast && (
                        <div className="flex justify-center mt-2 mb-2">
                          <ArrowRightIcon className="w-4 h-4 text-gray-400 transform rotate-90" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Workflow Metrics */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="flex items-center space-x-2">
                  <CheckCircleIcon className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium text-gray-900">
                    Success Metrics:
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{workflow.metrics}</p>
              </div>

              {/* Try Demo Button */}
              <button className="w-full mt-4 bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors">
                Try {workflow.title} Demo
              </button>
            </div>
          );
        })}
      </div>

      {/* API Integration Summary */}
      <div className="mt-8 bg-white p-6 rounded-lg shadow-sm">
        <h4 className="font-bold text-gray-900 mb-4 text-center">
          🔗 Powered by You.com API Suite
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="w-3 h-3 bg-blue-500 rounded-full mx-auto mb-2"></div>
            <div className="text-sm font-medium text-blue-700">News API</div>
            <div className="text-xs text-blue-600">Real-time monitoring</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="w-3 h-3 bg-green-500 rounded-full mx-auto mb-2"></div>
            <div className="text-sm font-medium text-green-700">Search API</div>
            <div className="text-xs text-green-600">Context enrichment</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded-lg">
            <div className="w-3 h-3 bg-purple-500 rounded-full mx-auto mb-2"></div>
            <div className="text-sm font-medium text-purple-700">
              Custom Agents
            </div>
            <div className="text-xs text-purple-600">Impact analysis</div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="w-3 h-3 bg-orange-500 rounded-full mx-auto mb-2"></div>
            <div className="text-sm font-medium text-orange-700">ARI API</div>
            <div className="text-xs text-orange-600">Deep research</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DemoWorkflows;
