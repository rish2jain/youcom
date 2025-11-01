"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

// Lazy load monitoring-specific components
const WatchList = dynamic(
  () =>
    import("@/components/WatchList").then((mod) => ({
      default: mod.WatchList,
    })),
  {
    ssr: false,
    loading: () => (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-20 bg-gray-200 rounded animate-pulse"></div>
        ))}
      </div>
    ),
  }
);

const PersonalPlaybooks = dynamic(
  () => import("@/components/PersonalPlaybooks"),
  {
    ssr: false,
    loading: () => (
      <div className="h-48 bg-gray-100 rounded-lg animate-pulse"></div>
    ),
  }
);

const ActionTracker = dynamic(() => import("@/components/ActionTracker"), {
  ssr: false,
  loading: () => (
    <div className="h-64 bg-gray-100 rounded-lg animate-pulse"></div>
  ),
});

const SuccessAnimation = dynamic(
  () =>
    import("@/components/SuccessAnimation").then((mod) => ({
      default: mod.SuccessAnimation,
    })),
  {
    ssr: false,
    loading: () => null,
  }
);

export default function MonitoringPage() {
  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const handleSuccess = (message: string) => {
    setSuccessMessage(message);
    setShowSuccess(true);
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Value Proposition Header */}
        <div className="bg-gradient-to-r from-green-600 to-teal-600 py-4 px-6 rounded-lg text-white mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold mb-1">
                👔 Competitive Operations
              </h2>
              <p className="text-green-50 text-sm">
                <strong>So what?</strong> Automate competitor tracking with
                custom playbooks and action tracking.
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">3</div>
              <div className="text-green-100 text-xs">Active Competitors</div>
            </div>
          </div>
        </div>

        {/* Header */}
        <div className="mb-8">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Competitive Monitoring & Operations
          </h1>
          <p className="text-gray-600">
            Manage your competitor watchlist with automated playbooks and action
            tracking
          </p>
        </div>

        {/* Competitor Watchlist */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <span>👀</span>
            Competitor Watchlist
          </h2>
          <p className="text-gray-600 mb-4">
            Monitor your key competitors and receive real-time alerts. For
            detailed company research,{" "}
            <Link
              href="/research"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              visit the Research page →
            </Link>
          </p>
          <WatchList />
        </div>

        {/* Playbooks Section */}
        <div className="mb-8">
          <PersonalPlaybooks
            onSelectPlaybook={handleSelectPlaybook}
            onCreatePlaybook={handleCreatePlaybook}
          />
        </div>

        {/* Action Tracker */}
        <ActionTracker
          onGenerateActions={handleGenerateActions}
          onAddCustomAction={handleAddCustomAction}
        />

        <SuccessAnimation
          show={showSuccess}
          message={successMessage}
          onComplete={() => setShowSuccess(false)}
        />
      </div>
    </div>
  );
}
