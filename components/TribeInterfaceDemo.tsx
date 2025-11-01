"use client";

import React, { useState } from "react";
import { TribeInterfaceProvider } from "./TribeInterfaceProvider";
import {
  TribeInterface,
  AdaptiveContent,
  FeatureGate,
  ExecutiveCard,
  AnalystCard,
  TeamCard,
} from "./TribeInterface";
import { TribeModeSelector } from "./TribeModeSelector";
import { ContentSummarizer } from "./ContentSummarizer";
import { RoleDetector } from "./RoleDetector";
import { ModePreferences } from "./ModePreferences";
import { TribeUser, InterfaceMode } from "@/lib/types/tribe-interface";

// DEMO DATA - Static sample data for demonstration purposes only
// This component uses mock data to showcase the Tribe Interface system
const mockExecutiveUser: TribeUser = {
  id: "exec-1",
  role: "executive",
  permissions: ["view", "share"],
  department: "leadership",
  seniority: "c-level",
  preferences: {
    defaultMode: "executive",
    maxInsights: 3,
    showTechnicalDetails: false,
    enableCollaboration: false,
    summaryLevel: "high",
    thresholds: {
      riskScore: 80,
      confidenceScore: 90,
      sourceCount: 5,
    },
    notifications: {
      email: true,
      inApp: true,
      slack: false,
      frequency: "immediate",
    },
  },
};

const mockAnalystUser: TribeUser = {
  id: "analyst-1",
  role: "analyst",
  permissions: ["view", "edit", "analyze"],
  department: "strategy",
  seniority: "senior",
  preferences: {
    defaultMode: "analyst",
    maxInsights: 8,
    showTechnicalDetails: true,
    enableCollaboration: true,
    summaryLevel: "detailed",
    thresholds: {
      riskScore: 60,
      confidenceScore: 75,
      sourceCount: 10,
    },
    notifications: {
      email: true,
      inApp: true,
      slack: true,
      frequency: "hourly",
    },
  },
};

const mockContent = {
  title: "OpenAI Competitive Analysis",
  summary:
    "OpenAI has released GPT-5 with advanced reasoning capabilities, neural network architecture improvements, and comprehensive API integrations.",
  insights: [
    "GPT-5 shows significant improvements in mathematical reasoning using advanced ML algorithms",
    "New multimodal capabilities enable image and video processing through neural networks",
    "API pricing has been reduced by 50% to increase adoption and leverage market position",
    "Enterprise features include fine-tuning and custom models with sophisticated optimization",
    "Safety measures have been enhanced with constitutional AI and comprehensive frameworks",
  ],
  actions: [
    "Evaluate our AI strategy against GPT-5 capabilities and implement necessary changes",
    "Assess pricing impact on our competitive position and optimize our API offerings",
    "Review our multimodal roadmap timeline and leverage advanced technologies",
    "Consider partnership opportunities with OpenAI to facilitate growth",
  ],
  api_usage: {
    news: 3,
    search: 5,
    chat: 2,
    ari: 1,
  },
  confidence_score: 85,
  risk_score: 92,
  total_sources: 25,
  competitor_name: "OpenAI",
  risk_level: "high",
};

export function TribeInterfaceDemo() {
  const [currentUser, setCurrentUser] = useState<TribeUser>(mockAnalystUser);
  const [showPreferences, setShowPreferences] = useState(false);
  const [showRoleDetector, setShowRoleDetector] = useState(false);

  const handleUserSwitch = (userType: "executive" | "analyst" | "team") => {
    if (userType === "executive") {
      setCurrentUser(mockExecutiveUser);
    } else if (userType === "analyst") {
      setCurrentUser(mockAnalystUser);
    } else {
      setCurrentUser({
        ...mockAnalystUser,
        role: "team",
        preferences: {
          ...mockAnalystUser.preferences,
          defaultMode: "team",
          enableCollaboration: true,
        },
      });
    }
  };

  return (
    <TribeInterfaceProvider user={currentUser}>
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto space-y-8">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-3xl font-bold text-gray-900">
                Tribe Interface System Demo
              </h1>
              <span className="px-3 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded-full border border-purple-300">
                🎨 DEMO PAGE
              </span>
            </div>
            <div className="bg-purple-50 border-l-4 border-purple-400 p-3 rounded-r mb-6">
              <p className="text-purple-800 text-sm font-medium mb-1">
                ⚠️ Demo Mode: This component uses static mock data to showcase the Tribe Interface system.
              </p>
              <p className="text-gray-600 text-sm">
                Experience role-based UI adaptation with dynamic content filtering
                and mode switching.
              </p>
            </div>

            {/* User Controls */}
            <div className="flex flex-wrap gap-4 mb-6">
              <div className="flex gap-2">
                <button
                  onClick={() => handleUserSwitch("executive")}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    currentUser.role === "executive"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  Executive User
                </button>
                <button
                  onClick={() => handleUserSwitch("analyst")}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    currentUser.role === "analyst"
                      ? "bg-purple-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  Analyst User
                </button>
                <button
                  onClick={() => handleUserSwitch("team")}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    currentUser.role === "team"
                      ? "bg-green-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  Team User
                </button>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setShowRoleDetector(true)}
                  className="px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg hover:bg-yellow-200 transition-colors"
                >
                  Test Role Detection
                </button>
                <button
                  onClick={() => setShowPreferences(true)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Preferences
                </button>
              </div>
            </div>

            {/* Current User Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">
                Current User Profile
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-blue-700 font-medium">Role:</span>
                  <span className="ml-2 capitalize">{currentUser.role}</span>
                </div>
                <div>
                  <span className="text-blue-700 font-medium">Department:</span>
                  <span className="ml-2">{currentUser.department}</span>
                </div>
                <div>
                  <span className="text-blue-700 font-medium">Seniority:</span>
                  <span className="ml-2">{currentUser.seniority}</span>
                </div>
                <div>
                  <span className="text-blue-700 font-medium">
                    Default Mode:
                  </span>
                  <span className="ml-2 capitalize">
                    {currentUser.preferences.defaultMode}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Mode Selector Demo */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Mode Selection
            </h2>
            <TribeModeSelector showDescription />
          </div>

          {/* Content Adaptation Demo */}
          <TribeInterface content={mockContent} showCognitiveLoad>
            <div className="space-y-6">
              {/* Content Summarizer */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Content Summarization
                </h2>
                <ContentSummarizer content={mockContent} showMetrics />
              </div>

              {/* Adaptive Content */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Adaptive Content
                </h2>
                <AdaptiveContent content={mockContent} />
              </div>

              {/* Role-Specific Cards */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Role-Specific Components
                </h2>

                {currentUser.role === "executive" && (
                  <ExecutiveCard
                    title="OpenAI Threat Assessment"
                    riskScore={92}
                    actions={[
                      "Immediate strategic review required",
                      "Assess competitive positioning",
                      "Evaluate partnership opportunities",
                    ]}
                    insight="GPT-5 release poses significant competitive threat requiring immediate executive attention"
                  />
                )}

                {currentUser.role === "analyst" && (
                  <AnalystCard data={mockContent} showTechnicalDetails />
                )}

                {currentUser.role === "team" && (
                  <TeamCard
                    data={mockContent}
                    onAnnotate={() =>
                      alert("Annotation feature would open here")
                    }
                    onShare={() => alert("Sharing feature would open here")}
                  />
                )}
              </div>

              {/* Feature Gates Demo */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Feature Gates
                </h2>

                <div className="space-y-4">
                  <FeatureGate
                    feature="apiMetrics"
                    fallback={
                      <div className="p-4 bg-gray-100 rounded-lg text-gray-600">
                        API metrics hidden for this role
                      </div>
                    }
                  >
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <h4 className="font-medium text-blue-900 mb-2">
                        API Metrics (Analyst Only)
                      </h4>
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        <div className="text-center">
                          <div className="font-bold text-blue-600">3</div>
                          <div className="text-blue-800">News API</div>
                        </div>
                        <div className="text-center">
                          <div className="font-bold text-green-600">5</div>
                          <div className="text-green-800">Search API</div>
                        </div>
                        <div className="text-center">
                          <div className="font-bold text-purple-600">2</div>
                          <div className="text-purple-800">Chat API</div>
                        </div>
                        <div className="text-center">
                          <div className="font-bold text-orange-600">1</div>
                          <div className="text-orange-800">ARI API</div>
                        </div>
                      </div>
                    </div>
                  </FeatureGate>

                  <FeatureGate
                    feature="annotations"
                    fallback={
                      <div className="p-4 bg-gray-100 rounded-lg text-gray-600">
                        Collaboration features not available for this role
                      </div>
                    }
                  >
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <h4 className="font-medium text-green-900 mb-2">
                        Collaboration Features (Team Mode)
                      </h4>
                      <div className="flex gap-2">
                        <button className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700">
                          Add Annotation
                        </button>
                        <button className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700">
                          Share Analysis
                        </button>
                        <button className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700">
                          Team Discussion
                        </button>
                      </div>
                    </div>
                  </FeatureGate>
                </div>
              </div>
            </div>
          </TribeInterface>

          {/* Role Detector Modal */}
          {showRoleDetector && (
            <RoleDetector
              onRoleConfirmed={(role) => {
                console.log("Role confirmed:", role);
                setShowRoleDetector(false);
              }}
              onModeSelected={(mode) => {
                console.log("Mode selected:", mode);
                setShowRoleDetector(false);
              }}
            />
          )}

          {/* Preferences Modal */}
          {showPreferences && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
                <ModePreferences onClose={() => setShowPreferences(false)} />
              </div>
            </div>
          )}
        </div>
      </div>
    </TribeInterfaceProvider>
  );
}
