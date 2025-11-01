"use client";

import { useState, useEffect } from "react";
import { RefreshCw, RotateCcw, ExternalLink, HelpCircle } from "lucide-react";
import { HeroSection } from "@/components/HeroSection";
import { SampleDataBanner } from "@/components/SampleDataBanner";
import { FeaturedImpactCard } from "@/components/FeaturedImpactCard";
import { DemoGuidance } from "@/components/DemoGuidance";

import { LiveDemoModal } from "@/components/LiveDemoModal";
import { APIPipelineVisual } from "@/components/APIPipelineVisual";
import { SuccessAnimation } from "@/components/SuccessAnimation";
import SuccessMetrics from "@/components/SuccessMetrics";
import { useNotificationContext } from "@/app/notifications/NotificationProvider";
import Link from "next/link";

export default function DemoPage() {
  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [showLiveDemo, setShowLiveDemo] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isMounted, setIsMounted] = useState(false);
  const { addNotification } = useNotificationContext();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleSuccess = (message: string) => {
    setSuccessMessage(message);
    setShowSuccess(true);
  };

  const handleGenerateDemo = async () => {
    setShowLiveDemo(true);
    // Show confirmation after modal opens
    setTimeout(() => {
      addNotification({
        type: "info",
        message: "Demo started! Watch the 4 APIs orchestrate in real-time.",
        autoClose: true,
        duration: 4000,
      });
    }, 500);
  };

  const handleNavigateToResearch = async () => {
    addNotification({
      type: "info",
      message: "Navigating to Research page...",
      autoClose: true,
      duration: 2000,
    });
    setTimeout(() => {
      window.location.href = "/research";
    }, 300);
  };

  const handleNavigateToAnalytics = async () => {
    addNotification({
      type: "info",
      message: "Navigating to Analytics page...",
      autoClose: true,
      duration: 2000,
    });
    setTimeout(() => {
      window.location.href = "/analytics";
    }, 300);
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

  const handleResetDemo = async () => {
    setIsResetting(true);
    // Simulate reset
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsResetting(false);
    addNotification({
      type: "success",
      message: "Demo reset successfully! You can start fresh now.",
      autoClose: true,
      duration: 3000,
    });
    // Reset any demo state if needed
    setShowLiveDemo(false);
    setShowSuccess(false);
  };

  const handleRefreshDemo = async () => {
    setIsRefreshing(true);
    // Simulate refresh
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setIsRefreshing(false);
    addNotification({
      type: "success",
      message: "Demo data refreshed!",
      autoClose: true,
      duration: 3000,
    });
  };

  return (
    <div className="space-y-12">
      {/* Demo Header */}
      <div className="bg-gradient-to-r from-orange-600 to-red-600 py-4 px-6 rounded-lg text-white">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-bold mb-1">🎭 Demo Mode - API Showcase</h2>
            <p className="text-orange-50 text-sm">
              Explore how we orchestrate 4 You.com APIs (News, Search, Chat, ARI) to generate competitive intelligence
            </p>
          </div>
          <div className="flex items-center gap-4 flex-shrink-0">
            <div className="text-right hidden sm:block">
              <div className="text-2xl font-bold">4 APIs</div>
              <div className="text-orange-100 text-xs">Orchestrated in Real-Time</div>
            </div>
            {isMounted && (
              <div className="flex gap-2">
                <button
                  onClick={handleRefreshDemo}
                  disabled={isRefreshing}
                  className="px-3 py-2 bg-white/20 hover:bg-white/30 backdrop-blur border border-white/30 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  title="Refresh demo data"
                  type="button"
                >
                  <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
                  <span className="hidden sm:inline">{isRefreshing ? "Refreshing..." : "Refresh"}</span>
                  <span className="sm:hidden">{isRefreshing ? "..." : "↻"}</span>
                </button>
                <button
                  onClick={handleResetDemo}
                  disabled={isResetting}
                  className="px-3 py-2 bg-white/20 hover:bg-white/30 backdrop-blur border border-white/30 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  title="Reset demo to initial state"
                  type="button"
                >
                  <RotateCcw className={`w-4 h-4 ${isResetting ? "animate-spin" : ""}`} />
                  <span className="hidden sm:inline">{isResetting ? "Resetting..." : "Reset"}</span>
                  <span className="sm:hidden">{isResetting ? "..." : "↻"}</span>
                </button>
              </div>
            )}
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
          <div className="flex items-center justify-center gap-2 mb-2">
            <h2 className="text-3xl font-bold text-gray-900">
              🚨 Live Intelligence Alert
            </h2>
            <div className="group relative">
              <HelpCircle className="w-5 h-5 text-gray-400 cursor-help" />
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 p-3 bg-gray-900 text-white text-xs rounded-lg whitespace-normal w-64 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                This alert demonstrates real-time threat detection using all 4 You.com APIs. 
                <Link href="/analytics" className="text-blue-300 underline hover:text-blue-200 mt-1 block">
                  Learn more about API orchestration →
                </Link>
              </div>
            </div>
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto">
            <strong className="text-red-600">HIGH THREAT DETECTED:</strong>{" "}
            OpenAI's latest move scored 8.8/10 risk. This analysis was generated
            by orchestrating all 4 You.com APIs in 2 minutes 14 seconds.
          </p>
          <div className="mt-4 flex items-center justify-center gap-4">
            <Link
              href="/analytics"
              className="text-sm text-blue-600 hover:text-blue-700 font-medium inline-flex items-center gap-1"
            >
              View detailed API metrics
              <ExternalLink className="w-3 h-3" />
            </Link>
            <Link
              href="/monitoring"
              className="text-sm text-purple-600 hover:text-purple-700 font-medium inline-flex items-center gap-1"
            >
              Learn about monitoring
              <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
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
