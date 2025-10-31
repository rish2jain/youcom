"use client";

import { useState } from "react";
import { HeroSection } from "@/components/HeroSection";
import { SampleDataBanner } from "@/components/SampleDataBanner";
import { FeaturedImpactCard } from "@/components/FeaturedImpactCard";
import { DemoGuidance } from "@/components/DemoGuidance";

import { LiveDemoModal } from "@/components/LiveDemoModal";
import { APIPipelineVisual } from "@/components/APIPipelineVisual";
import { SuccessAnimation } from "@/components/SuccessAnimation";
import SuccessMetrics from "@/components/SuccessMetrics";

export default function DemoPage() {
  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [showLiveDemo, setShowLiveDemo] = useState(false);

  const handleSuccess = (message: string) => {
    setSuccessMessage(message);
    setShowSuccess(true);
  };

  const handleGenerateDemo = async () => {
    setShowLiveDemo(true);
  };

  const handleNavigateToResearch = () => {
    window.location.href = "/research";
  };

  const handleNavigateToAnalytics = () => {
    window.location.href = "/analytics";
  };

  const handleNavigateToDashboard = () => {
    window.location.href = "/dashboard";
  };

  const handleAddApiKey = () => {
    window.location.href = "/settings";
  };

  const handleContinueDemo = () => {
    document
      .getElementById("demo-section")
      ?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="space-y-12">
      {/* Demo Header */}
      <div className="bg-gradient-to-r from-orange-600 to-red-600 py-4 px-6 rounded-lg text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold mb-1">🎭 Demo Mode - API Showcase</h2>
            <p className="text-orange-50 text-sm">
              Explore how we orchestrate 4 You.com APIs (News, Search, Chat, ARI) to generate competitive intelligence
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">4 APIs</div>
            <div className="text-orange-100 text-xs">Orchestrated in Real-Time</div>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <HeroSection
        onStartDemo={handleGenerateDemo}
        onViewDashboard={handleNavigateToDashboard}
      />

      {/* Sample Data Banner */}
      <SampleDataBanner
        onAddApiKey={handleAddApiKey}
        onContinueDemo={handleContinueDemo}
      />

      {/* API Pipeline Visual */}
      <APIPipelineVisual />

      {/* Featured Impact Card */}
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            🚨 Live Intelligence Alert
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            <strong className="text-red-600">HIGH THREAT DETECTED:</strong>{" "}
            OpenAI's latest move scored 8.8/10 risk. This analysis was generated
            by orchestrating all 4 You.com APIs in 2 minutes 14 seconds.
          </p>
        </div>
        <FeaturedImpactCard />
      </div>

      {/* Enhanced Demo Guidance */}
      <DemoGuidance
        onGenerateDemo={handleGenerateDemo}
        onNavigateToResearch={handleNavigateToResearch}
        onNavigateToAnalytics={handleNavigateToAnalytics}
        onNavigateToDashboard={handleNavigateToDashboard}
      />

      {/* Success Metrics */}
      <SuccessMetrics />

      {/* Live Demo Modal */}
      <LiveDemoModal
        isOpen={showLiveDemo}
        onClose={() => setShowLiveDemo(false)}
      />

      {/* Success Animation */}
      <SuccessAnimation
        show={showSuccess}
        message={successMessage}
        onComplete={() => setShowSuccess(false)}
      />
    </div>
  );
}
