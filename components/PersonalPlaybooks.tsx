"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import {
  Play,
  Star,
  Clock,
  Users,
  Target,
  CheckCircle,
  ArrowRight,
  Lightbulb,
  FileText,
  Settings,
  Bookmark,
  TrendingUp,
} from "lucide-react";

interface PersonaPreset {
  id: number;
  name: string;
  description?: string;
  category: string;
  analysis_depth: string;
  usage_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface UserPlaybook {
  id: number;
  user_id: number;
  persona_preset_id: number;
  custom_name?: string;
  last_used?: string;
  usage_count: number;
  current_step: number;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
  persona_preset: PersonaPreset;
}

interface PlaybookRecommendation {
  persona_preset: PersonaPreset;
  match_score: number;
  match_reasons: string[];
  estimated_time_minutes: number;
  key_benefits: string[];
}

interface PlaybookExecutionPlan {
  playbook: UserPlaybook;
  steps: Array<{
    step: number;
    name: string;
    description: string;
    estimated_minutes: number;
    [key: string]: any;
  }>;
  estimated_duration: number;
  required_inputs: string[];
  expected_outputs: string[];
  success_criteria: string[];
}

interface PersonalPlaybooksProps {
  userId: number;
  currentContext?: {
    user_type?: string;
    task_type?: string;
    experience_level?: string;
  };
  onPlaybookExecute?: (playbookId: number, targetCompany?: string) => void;
}

const PersonalPlaybooks: React.FC<PersonalPlaybooksProps> = ({
  userId,
  currentContext = {},
  onPlaybookExecute,
}) => {
  const [personas, setPersonas] = useState<PersonaPreset[]>([]);
  const [userPlaybooks, setUserPlaybooks] = useState<UserPlaybook[]>([]);
  const [recommendations, setRecommendations] = useState<
    PlaybookRecommendation[]
  >([]);
  const [selectedPlaybook, setSelectedPlaybook] = useState<UserPlaybook | null>(
    null
  );
  const [executionPlan, setExecutionPlan] =
    useState<PlaybookExecutionPlan | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "recommended" | "my-playbooks" | "browse"
  >("recommended");
  const [targetCompany, setTargetCompany] = useState("");

  useEffect(() => {
    loadData();
  }, [userId]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      // Load personas, user playbooks, and recommendations in parallel
      const [personasResponse, playbooksResponse, recommendationsResponse] =
        await Promise.all([
          fetch("/api/v1/enhancements/playbooks/personas"),
          fetch(`/api/v1/enhancements/playbooks/user/${userId}`),
          fetch("/api/v1/enhancements/playbooks/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, context: currentContext }),
          }),
        ]);

      if (personasResponse.ok) {
        const personasData = await personasResponse.json();
        setPersonas(personasData);
      }

      if (playbooksResponse.ok) {
        const playbooksData = await playbooksResponse.json();
        setUserPlaybooks(playbooksData);
      }

      if (recommendationsResponse.ok) {
        const recommendationsData = await recommendationsResponse.json();
        setRecommendations(recommendationsData);
      }
    } catch (error) {
      console.error("Failed to load playbook data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const createPlaybook = async (
    personaPresetId: number,
    customName?: string
  ) => {
    try {
      const response = await fetch("/api/v1/enhancements/playbooks/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          persona_preset_id: personaPresetId,
          custom_name: customName,
        }),
      });

      if (response.ok) {
        const newPlaybook = await response.json();
        setUserPlaybooks((prev) => [...prev, newPlaybook]);
        setActiveTab("my-playbooks");
        return newPlaybook;
      }
    } catch (error) {
      console.error("Failed to create playbook:", error);
    }
  };

  const loadExecutionPlan = async (playbookId: number, company?: string) => {
    try {
      const url = `/api/v1/enhancements/playbooks/${playbookId}/plan${
        company ? `?target_company=${encodeURIComponent(company)}` : ""
      }`;
      const response = await fetch(url);

      if (response.ok) {
        const plan = await response.json();
        setExecutionPlan(plan);
      }
    } catch (error) {
      console.error("Failed to load execution plan:", error);
    }
  };

  const executePlaybook = async (playbookId: number, company?: string) => {
    try {
      const response = await fetch(
        `/api/v1/enhancements/playbooks/${playbookId}/execute`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            target_company: company,
            execution_type: "research",
          }),
        }
      );

      if (response.ok) {
        const result = await response.json();
        onPlaybookExecute?.(playbookId, company);
        // Refresh user playbooks to update usage stats
        loadData();
        return result;
      }
    } catch (error) {
      console.error("Failed to execute playbook:", error);
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "individual":
        return <Users className="w-4 h-4" />;
      case "enterprise":
        return <Target className="w-4 h-4" />;
      case "research":
        return <FileText className="w-4 h-4" />;
      default:
        return <Lightbulb className="w-4 h-4" />;
    }
  };

  const getDepthColor = (depth: string) => {
    switch (depth) {
      case "quick":
        return "bg-green-100 text-green-800";
      case "medium":
        return "bg-blue-100 text-blue-800";
      case "deep":
        return "bg-purple-100 text-purple-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatTimeEstimate = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0
      ? `${hours}h ${remainingMinutes}m`
      : `${hours}h`;
  };

  const RecommendationCard: React.FC<{
    recommendation: PlaybookRecommendation;
  }> = ({ recommendation }) => (
    <Card className="hover:shadow-md transition-shadow cursor-pointer">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            {getCategoryIcon(recommendation.persona_preset.category)}
            <h3 className="font-medium text-gray-900">
              {recommendation.persona_preset.name}
            </h3>
          </div>
          <div className="flex items-center space-x-2">
            <Badge
              className={getDepthColor(
                recommendation.persona_preset.analysis_depth
              )}
            >
              {recommendation.persona_preset.analysis_depth}
            </Badge>
            <div className="text-right">
              <div className="text-sm font-medium text-green-600">
                {Math.round(recommendation.match_score * 100)}% match
              </div>
              <div className="text-xs text-gray-500">
                {formatTimeEstimate(recommendation.estimated_time_minutes)}
              </div>
            </div>
          </div>
        </div>

        {recommendation.persona_preset.description && (
          <p className="text-sm text-gray-600 mb-3">
            {recommendation.persona_preset.description}
          </p>
        )}

        <div className="space-y-2 mb-4">
          <div>
            <h4 className="text-xs font-medium text-gray-700 mb-1">
              Why this matches:
            </h4>
            <ul className="text-xs text-gray-600 space-y-1">
              {recommendation.match_reasons.slice(0, 2).map((reason, index) => (
                <li key={index} className="flex items-start space-x-1">
                  <span className="w-1 h-1 bg-blue-500 rounded-full mt-1.5 flex-shrink-0" />
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-medium text-gray-700 mb-1">
              Key benefits:
            </h4>
            <ul className="text-xs text-gray-600 space-y-1">
              {recommendation.key_benefits.slice(0, 2).map((benefit, index) => (
                <li key={index} className="flex items-start space-x-1">
                  <CheckCircle className="w-3 h-3 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="flex space-x-2">
          <Button
            size="sm"
            onClick={() => createPlaybook(recommendation.persona_preset.id)}
            className="flex-1"
          >
            <Bookmark className="w-3 h-3 mr-1" />
            Add to My Playbooks
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              createPlaybook(recommendation.persona_preset.id).then(
                (playbook) => {
                  if (playbook) {
                    setSelectedPlaybook(playbook);
                    loadExecutionPlan(playbook.id, targetCompany);
                  }
                }
              );
            }}
          >
            <Play className="w-3 h-3 mr-1" />
            Use Now
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const PlaybookCard: React.FC<{ playbook: UserPlaybook }> = ({ playbook }) => (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            {getCategoryIcon(playbook.persona_preset.category)}
            <div>
              <h3 className="font-medium text-gray-900">
                {playbook.custom_name || playbook.persona_preset.name}
              </h3>
              {playbook.custom_name && (
                <p className="text-xs text-gray-500">
                  {playbook.persona_preset.name}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {playbook.is_favorite && (
              <Star className="w-4 h-4 text-yellow-500 fill-current" />
            )}
            <Badge
              className={getDepthColor(playbook.persona_preset.analysis_depth)}
            >
              {playbook.persona_preset.analysis_depth}
            </Badge>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
          <span>Used {playbook.usage_count} times</span>
          {playbook.last_used && (
            <span>
              Last used {new Date(playbook.last_used).toLocaleDateString()}
            </span>
          )}
        </div>

        <div className="flex space-x-2">
          <Button
            size="sm"
            onClick={() => {
              setSelectedPlaybook(playbook);
              loadExecutionPlan(playbook.id, targetCompany);
            }}
            className="flex-1"
          >
            <Play className="w-3 h-3 mr-1" />
            Execute
          </Button>
          <Button size="sm" variant="outline">
            <Settings className="w-3 h-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );

  const ExecutionPlanModal: React.FC = () => {
    if (!executionPlan) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <Card className="w-full max-w-2xl max-h-[80vh] overflow-y-auto">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>
                Execution Plan:{" "}
                {executionPlan.playbook.custom_name ||
                  executionPlan.playbook.persona_preset.name}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExecutionPlan(null)}
              >
                ×
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Target Company Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Company (Optional)
              </label>
              <input
                type="text"
                value={targetCompany}
                onChange={(e) => setTargetCompany(e.target.value)}
                placeholder="e.g., OpenAI, Perplexity AI"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Execution Steps */}
            <div>
              <h3 className="font-medium text-gray-900 mb-3">
                Execution Steps
              </h3>
              <div className="space-y-3">
                {executionPlan.steps.map((step, index) => (
                  <div key={step.step} className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">
                      {step.step}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-sm text-gray-900">
                        {step.name}
                      </h4>
                      <p className="text-sm text-gray-600 mb-1">
                        {step.description}
                      </p>
                      <div className="flex items-center space-x-4 text-xs text-gray-500">
                        <span className="flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {step.estimated_minutes}m
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Summary */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Total Time:</span>
                  <p className="font-medium">
                    {formatTimeEstimate(executionPlan.estimated_duration)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Expected Outputs:</span>
                  <p className="font-medium">
                    {executionPlan.expected_outputs.length} deliverables
                  </p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-3">
              <Button
                onClick={() => {
                  executePlaybook(executionPlan.playbook.id, targetCompany);
                  setExecutionPlan(null);
                }}
                className="flex-1"
              >
                <Play className="w-4 h-4 mr-2" />
                Start Execution
              </Button>
              <Button variant="outline" onClick={() => setExecutionPlan(null)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Personal Playbooks
        </h2>
        <p className="text-gray-600">
          Persona-driven presets that configure data slices, export templates,
          and follow-up tasks for your specific goals.
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            {
              id: "recommended",
              label: "Recommended",
              count: recommendations.length,
            },
            {
              id: "my-playbooks",
              label: "My Playbooks",
              count: userPlaybooks.length,
            },
            { id: "browse", label: "Browse All", count: personas.length },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <Badge variant="secondary" className="ml-2 text-xs">
                  {tab.count}
                </Badge>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="min-h-[400px]">
        {activeTab === "recommended" && (
          <div className="space-y-4">
            {recommendations.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {recommendations.map((rec, index) => (
                  <RecommendationCard key={index} recommendation={rec} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">
                  No recommendations yet
                </h3>
                <p>Browse all playbooks to find ones that match your needs</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "my-playbooks" && (
          <div className="space-y-4">
            {userPlaybooks.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {userPlaybooks.map((playbook) => (
                  <PlaybookCard key={playbook.id} playbook={playbook} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Bookmark className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">No playbooks yet</h3>
                <p>
                  Create your first playbook from the recommended or browse
                  sections
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === "browse" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {personas.map((persona) => (
                <Card
                  key={persona.id}
                  className="hover:shadow-md transition-shadow"
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        {getCategoryIcon(persona.category)}
                        <h3 className="font-medium text-gray-900">
                          {persona.name}
                        </h3>
                      </div>
                      <Badge className={getDepthColor(persona.analysis_depth)}>
                        {persona.analysis_depth}
                      </Badge>
                    </div>

                    {persona.description && (
                      <p className="text-sm text-gray-600 mb-3">
                        {persona.description}
                      </p>
                    )}

                    <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                      <span className="capitalize">{persona.category}</span>
                      <span>Used {persona.usage_count} times</span>
                    </div>

                    <Button
                      size="sm"
                      onClick={() => createPlaybook(persona.id)}
                      className="w-full"
                    >
                      <Bookmark className="w-3 h-3 mr-1" />
                      Add to My Playbooks
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Execution Plan Modal */}
      <ExecutionPlanModal />
    </div>
  );
};

export default PersonalPlaybooks;
