"use client";

import { useState } from "react";
import { WatchList } from "@/components/WatchList";
import { ImpactCardDisplay } from "@/components/ImpactCardDisplay";
import { CompanyResearch } from "@/components/CompanyResearch";
import { APIUsageDashboard } from "@/components/APIUsageDashboard";
import { NotificationRulesManager } from "@/components/NotificationRulesManager";
import { DemoModeToggle } from "@/components/DemoModeToggle";
import { QuickDemoActions } from "@/components/QuickDemoActions";
import { SuccessAnimation } from "@/components/SuccessAnimation";
import { PredictiveAnalytics } from "@/components/PredictiveAnalytics";
import { IntegrationManager } from "@/components/IntegrationManager";
import InsightTimeline from "@/components/InsightTimeline";
import EvidenceBadge from "@/components/EvidenceBadge";
import PersonalPlaybooks from "@/components/PersonalPlaybooks";
import ActionTracker from "@/components/ActionTracker";
import EnhancedImpactCard from "@/components/EnhancedImpactCard";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<
    "enterprise" | "individual" | "analytics" | "integrations" | "enhancements"
  >("enterprise");
  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const handleSuccess = (message: string) => {
    setSuccessMessage(message);
    setShowSuccess(true);
    setErrorMessage("");
  };

  const handleError = (message: string) => {
    setErrorMessage(message);
    setShowSuccess(false);
  };

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center py-12 bg-white rounded-lg shadow-sm">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Enterprise Competitive Intelligence Agent
        </h1>
        <p className="text-xl text-gray-600 mb-6 max-w-3xl mx-auto">
          AI-powered competitive intelligence that transforms information
          overload into actionable insights using all 4 You.com APIs in perfect
          orchestration.
        </p>
        <div className="flex justify-center space-x-4 mb-8">
          <div className="flex items-center space-x-2 text-sm bg-blue-50 px-4 py-2 rounded-full">
            <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
            <span>News API: Real-time monitoring</span>
          </div>
          <div className="flex items-center space-x-2 text-sm bg-green-50 px-4 py-2 rounded-full">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            <span>Search API: Context enrichment</span>
          </div>
          <div className="flex items-center space-x-2 text-sm bg-purple-50 px-4 py-2 rounded-full">
            <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
            <span>Chat API: Impact analysis</span>
          </div>
          <div className="flex items-center space-x-2 text-sm bg-orange-50 px-4 py-2 rounded-full">
            <span className="w-2 h-2 bg-orange-500 rounded-full"></span>
            <span>ARI API: Deep research</span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex justify-center space-x-2 mb-6 flex-wrap">
          <button
            onClick={() => setActiveTab("enterprise")}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === "enterprise"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Enterprise
          </button>
          <button
            onClick={() => setActiveTab("individual")}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === "individual"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Individual
          </button>
          <button
            onClick={() => setActiveTab("analytics")}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === "analytics"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Analytics
          </button>
          <button
            onClick={() => setActiveTab("integrations")}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === "integrations"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Integrations
          </button>
          <button
            onClick={() => setActiveTab("enhancements")}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === "enhancements"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Enhancements
          </button>
        </div>

        {/* Demo Controls */}
        <div className="flex justify-center">
          <DemoModeToggle />
        </div>
      </div>

      {/* Quick Demo Actions */}
      <QuickDemoActions onSuccess={handleSuccess} onError={handleError} />

      {/* Error Message */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-red-700 text-sm">{errorMessage}</div>
        </div>
      )}

      {/* Enterprise Mode */}
      {activeTab === "enterprise" && (
        <div className="space-y-8">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Enterprise Competitive Monitoring
            </h2>
            <p className="text-gray-600 mb-6">
              Monitor competitors in real-time and generate Impact Cards using
              all 4 You.com APIs. Perfect for product managers, strategy teams,
              and executives.
            </p>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <WatchList />
              <ImpactCardDisplay />
            </div>
          </div>

          {/* Automated Alerts */}
          <NotificationRulesManager />
        </div>
      )}

      {/* Individual Mode */}
      {activeTab === "individual" && (
        <div className="space-y-8">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Individual Company Research
            </h2>
            <p className="text-gray-600 mb-6">
              Research any company instantly using You.com's Search and ARI
              APIs. Perfect for job seekers, investors, entrepreneurs, and
              researchers.
            </p>
            <CompanyResearch />
          </div>
        </div>
      )}

      {/* Analytics Mode */}
      {activeTab === "analytics" && (
        <div className="space-y-8">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Predictive Analytics & Market Intelligence
            </h2>
            <p className="text-gray-600 mb-6">
              Advanced analytics powered by competitive intelligence data.
              Market landscape analysis, competitor trend prediction, and
              executive briefings.
            </p>
            <PredictiveAnalytics />
          </div>
        </div>
      )}

      {/* Integrations Mode */}
      {activeTab === "integrations" && (
        <div className="space-y-8">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Integration Management
            </h2>
            <p className="text-gray-600 mb-6">
              Connect your competitive intelligence to external platforms. Sync
              findings to Notion databases, create Salesforce opportunities, and
              automate workflows.
            </p>
            <IntegrationManager />
          </div>
        </div>
      )}

      {/* Enhancements Mode */}
      {activeTab === "enhancements" && (
        <div className="space-y-8">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Enhancement Features
            </h2>
            <p className="text-gray-600 mb-6">
              Advanced features including insight timelines, evidence badges,
              personal playbooks, and action tracking. These enhancements
              provide deeper insights and better workflow management.
            </p>

            {/* Feature Showcase Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Insight Timeline Demo */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  📈 Insight Timeline & Delta Highlights
                </h3>
                <InsightTimeline
                  companyName="OpenAI"
                  impactCardId={1}
                  onAnalyzeComplete={(data) => {
                    handleSuccess(`Timeline analysis complete for OpenAI`);
                  }}
                />
              </div>

              {/* Evidence Badge Demo */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  🛡️ Confidence & Evidence Badges
                </h3>
                <div className="space-y-4">
                  <EvidenceBadge
                    entityType="impact_card"
                    entityId={1}
                    compact={false}
                  />
                  <div className="text-sm text-gray-600">
                    <p>
                      Evidence badges show confidence levels, source quality,
                      and freshness indicators. Click to expand and see detailed
                      source analysis with tier classifications.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Personal Playbooks */}
            <div className="space-y-4 mb-8">
              <h3 className="text-lg font-semibold text-gray-900">
                📋 Personal Playbooks
              </h3>
              <PersonalPlaybooks
                userId={1}
                currentContext={{
                  user_type: "individual",
                  task_type: "research",
                  experience_level: "medium",
                }}
                onPlaybookExecute={(playbookId, targetCompany) => {
                  handleSuccess(
                    `Executed playbook ${playbookId} for ${
                      targetCompany || "general research"
                    }`
                  );
                }}
              />
            </div>

            {/* Action Tracker */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">
                ✅ Action Tracker Lite
              </h3>
              <ActionTracker
                impactCardId={1}
                userId={1}
                viewMode="list"
                showSummary={true}
                onActionUpdate={(action) => {
                  handleSuccess(
                    `Action "${action.title}" updated successfully`
                  );
                }}
              />
            </div>

            {/* Enhanced Impact Card Demo */}
            <div className="space-y-4 mt-8">
              <h3 className="text-lg font-semibold text-gray-900">
                🎯 Enhanced Impact Card
              </h3>
              <p className="text-gray-600 mb-4">
                See how all enhancement features work together in a unified
                Impact Card experience:
              </p>
              <EnhancedImpactCard
                impactCard={{
                  id: 1,
                  competitor_name: "OpenAI",
                  risk_score: 75,
                  risk_level: "high",
                  confidence_score: 88,
                  impact_areas: [
                    {
                      area: "product",
                      impact_level: "high",
                      description:
                        "New GPT model release could impact competitive positioning",
                    },
                    {
                      area: "market",
                      impact_level: "medium",
                      description:
                        "Expanding into enterprise markets with new partnerships",
                    },
                  ],
                  key_insights: [
                    "OpenAI announced GPT-4 Turbo with improved capabilities and lower costs",
                    "New enterprise partnerships suggest aggressive B2B expansion",
                    "Developer adoption metrics show strong ecosystem growth",
                  ],
                  recommended_actions: [
                    {
                      action:
                        "Analyze feature parity gaps with new GPT-4 Turbo",
                      priority: "high",
                      owner: "Product Team",
                      timeline: "1 week",
                    },
                    {
                      action: "Review enterprise pricing strategy",
                      priority: "medium",
                      owner: "Strategy Team",
                      timeline: "2 weeks",
                    },
                  ],
                  sources: [
                    {
                      name: "TechCrunch",
                      url: "https://techcrunch.com/openai-gpt4-turbo",
                      title:
                        "OpenAI announces GPT-4 Turbo with improved performance",
                      excerpt:
                        "OpenAI today announced GPT-4 Turbo, a more capable and cost-effective version...",
                      publish_date: new Date().toISOString(),
                    },
                    {
                      name: "The Information",
                      url: "https://theinformation.com/openai-enterprise",
                      title: "OpenAI's enterprise push gains momentum",
                      excerpt:
                        "OpenAI is making significant inroads into enterprise markets...",
                      publish_date: new Date(
                        Date.now() - 86400000
                      ).toISOString(),
                    },
                  ],
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString(),
                }}
                userId={1}
                onUpdate={(card) => {
                  handleSuccess(
                    `Impact card for ${card.competitor_name} updated`
                  );
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* API Usage Dashboard */}
      <APIUsageDashboard />

      {/* Feature Showcase */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-8 rounded-lg">
        <h3 className="text-2xl font-bold text-gray-900 mb-4">
          🏆 Complete Competitive Intelligence Platform
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white p-4 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-2">
              🔗 You.com API Integration
            </h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• News API: Real-time monitoring</li>
              <li>• Search API: Context enrichment</li>
              <li>• Chat API: Impact analysis</li>
              <li>• ARI API: Deep research reports</li>
            </ul>
          </div>
          <div className="bg-white p-4 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-2">
              🔧 Advanced Integrations
            </h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Notion: Database synchronization</li>
              <li>• Salesforce: CRM workflows</li>
              <li>• Slack: Team notifications</li>
              <li>• Email: Report sharing</li>
            </ul>
          </div>
          <div className="bg-white p-4 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-2">
              📊 Predictive Analytics
            </h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Market temperature analysis</li>
              <li>• Competitor trend prediction</li>
              <li>• Executive briefings</li>
              <li>• Strategic recommendations</li>
            </ul>
          </div>
        </div>

        {/* Demo Information */}
        <h3 className="text-xl font-bold text-gray-900 mb-4">
          🎬 Demo Workflows
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Enterprise Workflow
            </h4>
            <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
              <li>
                Create watchlist for competitors (OpenAI, Anthropic, Google)
              </li>
              <li>News API monitors for announcements in real-time</li>
              <li>Search API enriches context and background</li>
              <li>Chat API (Custom Agents) analyzes competitive impact</li>
              <li>ARI API generates comprehensive research reports</li>
              <li>System creates actionable Impact Cards with risk scores</li>
            </ol>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">
              Individual Workflow
            </h4>
            <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
              <li>Enter any company name for instant research</li>
              <li>Search API gathers company profile and context</li>
              <li>ARI API generates deep research from 400+ sources</li>
              <li>System creates comprehensive company analysis</li>
              <li>Export reports for presentations and sharing</li>
              <li>Perfect for interviews, investments, and due diligence</li>
            </ol>
          </div>
        </div>
        <div className="mt-6 p-4 bg-white rounded-lg">
          <p className="text-sm text-gray-600">
            <strong>Success Metrics:</strong> Save 10+ hours/week for enterprise
            teams, detect competitive moves 3-5 days earlier, achieve 85%+
            accuracy in impact classification. For individuals: Complete company
            research in under 2 minutes vs. 2-4 hours manually.
          </p>
        </div>
      </div>

      {/* Success Animation */}
      <SuccessAnimation
        show={showSuccess}
        message={successMessage}
        onComplete={() => setShowSuccess(false)}
      />
    </div>
  );
}
