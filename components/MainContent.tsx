"use client";

import { WatchList } from "@/components/WatchList";
import { CompanyResearch } from "@/components/CompanyResearch";
import { APIUsageDashboard } from "@/components/APIUsageDashboard";
import { PredictiveAnalytics } from "@/components/PredictiveAnalytics";
import { IntegrationManager } from "@/components/IntegrationManager";
import PersonalPlaybooks from "@/components/PersonalPlaybooks";
import ActionTracker from "@/components/ActionTracker";
import ImpactCard from "@/components/ImpactCard";
import SuccessMetrics from "@/components/SuccessMetrics";
import APIToggle from "@/components/APIToggle";
import DemoActions from "@/components/DemoActions";
import { SuccessAnimation } from "@/components/SuccessAnimation";
import { useState } from "react";

interface MainContentProps {
  activeItem: string;
}

export default function MainContent({ activeItem }: MainContentProps) {
  const [useLiveData, setUseLiveData] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const handleSuccess = (message: string) => {
    setSuccessMessage(message);
    setShowSuccess(true);
  };

  const handleGenerateDemo = async () => {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    handleSuccess("Demo data loaded successfully!");
  };

  const handleResetDemo = async () => {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    handleSuccess("Demo data reset to clean state");
  };

  const handleSelectPlaybook = (playbookId: string) => {
    handleSuccess(`Applied ${playbookId} playbook configuration`);
  };

  const handleCreatePlaybook = () => {
    handleSuccess("Playbook creation wizard opened");
  };

  const handleGenerateActions = async () => {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    handleSuccess("Generated 3 new actions from competitive insights");
  };

  const handleAddCustomAction = () => {
    handleSuccess("Custom action creation form opened");
  };

  // DEMO: Enhanced impact card data with static demo content
  // This is sample data for demonstration purposes only
  const sampleImpactCard = {
    title: "OpenAI GPT-4 Turbo Launch Impact Analysis",
    riskScore: 75,
    riskLevel: "high" as const,
    impactAreas: ["Product Strategy", "Market Position", "Pricing"],
    timeline: "1-2 weeks",
    confidence: 88,
    sources: 12,
    lastUpdated: "2 hours ago",
    keyInsights:
      "OpenAI's GPT-4 Turbo launch introduces significant competitive pressure with improved performance and reduced pricing that could impact our market position.",
    timelineEvents: [
      {
        title: "GPT-4 Turbo Announced",
        time: "2 hours ago",
        status: "completed" as const,
      },
      {
        title: "Initial Market Reaction",
        time: "1 hour ago",
        status: "completed" as const,
      },
      {
        title: "Competitive Analysis",
        time: "30 minutes ago",
        status: "pending" as const,
      },
    ],
    recommendedActions: [
      {
        title: "Compare feature sets with GPT-4 Turbo",
        description:
          "Assess pricing impact on our positioning and identify feature gaps",
        priority: "high" as const,
        timeline: "1-2 weeks",
      },
    ],
    sourceBreakdown: { tier1: 8, tier2: 3, tier3: 1 },
    processingDetails: {
      completedAt: "2 hours ago",
      processingTime: "2.3 seconds",
      apisUsed: ["News API", "Search API", "Custom Agents API"],
    },
  };

  const renderContent = () => {
    switch (activeItem) {
      case "dashboard":
        return (
          <div className="space-y-8">
            {/* Welcome Section */}
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Welcome to Enterprise CIA
              </h1>
              <p className="text-gray-600 mb-4">
                AI-powered competitive intelligence using all 4 You.com APIs.
                Get started by loading sample data or connecting your live APIs.
              </p>
            </div>

            {/* Data Source Toggle */}
            <APIToggle
              useLiveData={useLiveData}
              onToggle={setUseLiveData}
              hasApiKey={!!process.env.YOU_API_KEY}
            />

            {/* Demo Actions */}
            <DemoActions
              onGenerateDemo={handleGenerateDemo}
              onResetDemo={handleResetDemo}
              isLiveMode={useLiveData}
            />

            {/* Main Dashboard Content */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Competitive Monitoring */}
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <h2 className="text-xl font-bold text-gray-900 mb-4">
                  Competitive Monitoring
                </h2>
                <WatchList />
              </div>

              {/* Company Research */}
              <div className="bg-white p-6 rounded-lg shadow-sm">
                <h2 className="text-xl font-bold text-gray-900 mb-4">
                  Company Research
                </h2>
                <CompanyResearch />
              </div>
            </div>

            {/* Impact Card Demo */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">
                  Latest Impact Analysis
                </h2>
                <span className="px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-full border border-yellow-300">
                  🎯 DEMO DATA
                </span>
              </div>
              <div className="relative">
                <ImpactCard data={sampleImpactCard} />
                <div className="absolute top-2 right-2 bg-yellow-100 text-yellow-800 text-xs font-medium px-2 py-1 rounded border border-yellow-300">
                  Demo Sample
                </div>
              </div>
            </div>

            {/* Success Metrics */}
            <SuccessMetrics />

            {/* API Usage Dashboard */}
            <APIUsageDashboard />
          </div>
        );

      case "research":
        return (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Company Research
              </h1>
              <p className="text-gray-600 mb-4">
                Generate comprehensive research reports using You.com ARI API
                with 400+ sources.
              </p>
            </div>
            <CompanyResearch />
          </div>
        );

      case "monitoring":
        return (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Competitive Monitoring
              </h1>
              <p className="text-gray-600 mb-4">
                Real-time monitoring of competitors using You.com News and
                Search APIs.
              </p>
            </div>
            <WatchList />

            {/* Personal Playbooks */}
            <PersonalPlaybooks
              onSelectPlaybook={handleSelectPlaybook}
              onCreatePlaybook={handleCreatePlaybook}
            />

            {/* Action Tracker */}
            <ActionTracker
              onGenerateActions={handleGenerateActions}
              onAddCustomAction={handleAddCustomAction}
            />
          </div>
        );

      case "analytics":
        return (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Predictive Analytics
              </h1>
              <p className="text-gray-600 mb-4">
                Advanced analytics and predictions powered by competitive
                intelligence data.
              </p>
            </div>
            <PredictiveAnalytics />
          </div>
        );

      case "integrations":
        return (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Integration Management
              </h1>
              <p className="text-gray-600 mb-4">
                Connect your favorite tools to sync competitive intelligence
                data automatically.
              </p>
            </div>
            <IntegrationManager />
          </div>
        );

      case "settings":
        return (
          <div className="space-y-8">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Settings & Configuration
              </h1>
              <p className="text-gray-600 mb-4">
                Configure your preferences, API settings, and personal
                playbooks.
              </p>
            </div>

            {/* API Configuration */}
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                API Configuration
              </h2>
              <APIToggle
                useLiveData={useLiveData}
                onToggle={setUseLiveData}
                hasApiKey={!!process.env.YOU_API_KEY}
              />
            </div>

            {/* Personal Playbooks */}
            <PersonalPlaybooks
              onSelectPlaybook={handleSelectPlaybook}
              onCreatePlaybook={handleCreatePlaybook}
            />

            {/* API Usage Metrics */}
            <APIUsageDashboard />
          </div>
        );

      default:
        return (
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Page Not Found
            </h1>
            <p className="text-gray-600">
              The requested page could not be found.
            </p>
          </div>
        );
    }
  };

  return (
    <>
      {renderContent()}

      {/* Success Animation */}
      <SuccessAnimation
        show={showSuccess}
        message={successMessage}
        onComplete={() => setShowSuccess(false)}
      />
    </>
  );
}
