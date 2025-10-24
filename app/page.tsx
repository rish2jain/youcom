"use client";

import { useState } from "react";
import { WatchList } from "@/components/WatchList";
import { ImpactCardDisplay } from "@/components/ImpactCardDisplay";
import { CompanyResearch } from "@/components/CompanyResearch";
import { APIUsageDashboard } from "@/components/APIUsageDashboard";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<"enterprise" | "individual">(
    "enterprise"
  );

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
        <div className="flex justify-center space-x-4">
          <button
            onClick={() => setActiveTab("enterprise")}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === "enterprise"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Enterprise Mode
          </button>
          <button
            onClick={() => setActiveTab("individual")}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === "individual"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Individual Mode
          </button>
        </div>
      </div>

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

      {/* API Usage Dashboard */}
      <APIUsageDashboard />

      {/* Demo Information */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-8 rounded-lg">
        <h3 className="text-2xl font-bold text-gray-900 mb-4">
          🏆 Hackathon Demo: You.com API Showcase
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
    </div>
  );
}
