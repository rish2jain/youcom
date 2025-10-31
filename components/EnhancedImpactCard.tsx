"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import InsightTimeline from "./InsightTimeline";
import EvidenceBadge from "./EvidenceBadge";
import ActionTracker from "./ActionTracker";
import PersonalPlaybooks from "./PersonalPlaybooks";
import {
  TrendingUp,
  Shield,
  CheckCircle,
  Clock,
  Users,
  Target,
  AlertTriangle,
  Info,
  ExternalLink,
  Download,
  Share,
} from "lucide-react";

interface ImpactCard {
  id: number;
  competitor_name: string;
  risk_score: number;
  risk_level: string;
  confidence_score: number;
  impact_areas: Array<{
    area: string;
    impact_level: string;
    description: string;
  }>;
  key_insights: string[];
  recommended_actions: Array<{
    action: string;
    priority: string;
    owner: string;
    timeline: string;
  }>;
  sources: Array<{
    name: string;
    url: string;
    title?: string;
    excerpt?: string;
    publish_date?: string;
  }>;
  created_at: string;
  updated_at: string;
}

interface EnhancedImpactCardProps {
  impactCard: ImpactCard;
  userId?: number;
  onUpdate?: (card: ImpactCard) => void;
}

const EnhancedImpactCard: React.FC<EnhancedImpactCardProps> = ({
  impactCard,
  userId = 1,
  onUpdate,
}) => {
  const [activeTab, setActiveTab] = useState("overview");

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case "critical":
        return "bg-red-100 text-red-800 border-red-200";
      case "high":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case "critical":
        return <AlertTriangle className="w-4 h-4" />;
      case "high":
        return <TrendingUp className="w-4 h-4" />;
      case "medium":
        return <Info className="w-4 h-4" />;
      case "low":
        return <CheckCircle className="w-4 h-4" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case "urgent":
        return "bg-red-100 text-red-800";
      case "high":
        return "bg-orange-100 text-orange-800";
      case "medium":
        return "bg-blue-100 text-blue-800";
      case "low":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <CardTitle className="text-2xl text-gray-900">
                {impactCard.competitor_name} Impact Analysis
              </CardTitle>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">Risk Score:</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          impactCard.risk_score >= 80
                            ? "bg-red-500"
                            : impactCard.risk_score >= 60
                            ? "bg-orange-500"
                            : impactCard.risk_score >= 40
                            ? "bg-yellow-500"
                            : "bg-green-500"
                        }`}
                        style={{ width: `${impactCard.risk_score}%` }}
                      />
                    </div>
                    <span className="font-medium text-gray-900">
                      {impactCard.risk_score}/100
                    </span>
                  </div>
                </div>
                <Badge
                  className={getRiskColor(impactCard.risk_level)}
                  variant="outline"
                >
                  {getRiskIcon(impactCard.risk_level)}
                  <span className="ml-1 capitalize">
                    {impactCard.risk_level}
                  </span>
                </Badge>
                <EvidenceBadge
                  entityType="impact_card"
                  entityId={impactCard.id}
                  compact={true}
                />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-1" />
                Export
              </Button>
              <Button variant="outline" size="sm">
                <Share className="w-4 h-4 mr-1" />
                Share
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Enhanced Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-4"
      >
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="evidence">Evidence</TabsTrigger>
          <TabsTrigger value="actions">Actions</TabsTrigger>
          <TabsTrigger value="playbooks">Playbooks</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Impact Areas */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Impact Areas</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {impactCard.impact_areas?.map((area, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900 capitalize">
                        {area.area}
                      </h4>
                      <Badge
                        className={getRiskColor(area.impact_level)}
                        variant="outline"
                      >
                        {area.impact_level}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600">{area.description}</p>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Key Insights */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Key Insights</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {impactCard.key_insights?.map((insight, index) => (
                    <li key={index} className="flex items-start space-x-2">
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-sm text-gray-700">{insight}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Recommended Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recommended Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {impactCard.recommended_actions?.map((action, index) => (
                  <div
                    key={index}
                    className="p-4 border border-gray-200 rounded-lg"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-gray-900 text-sm">
                        {action.action}
                      </h4>
                      <Badge
                        className={getPriorityColor(action.priority)}
                        variant="outline"
                      >
                        {action.priority}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span className="flex items-center">
                        <Users className="w-3 h-3 mr-1" />
                        {action.owner}
                      </span>
                      <span className="flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {action.timeline}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Metadata */}
          <Card>
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Confidence Score</span>
                  <p className="font-medium">{impactCard.confidence_score}%</p>
                </div>
                <div>
                  <span className="text-gray-500">Total Sources</span>
                  <p className="font-medium">
                    {impactCard.sources?.length || 0}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Created</span>
                  <p className="font-medium">
                    {formatDate(impactCard.created_at)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Last Updated</span>
                  <p className="font-medium">
                    {formatDate(impactCard.updated_at)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline">
          <InsightTimeline
            companyName={impactCard.competitor_name}
            impactCardId={impactCard.id}
            onAnalyzeComplete={(data) => {
              console.log("Timeline analysis complete:", data);
            }}
          />
        </TabsContent>

        {/* Evidence Tab */}
        <TabsContent value="evidence">
          <div className="space-y-6">
            <EvidenceBadge
              entityType="impact_card"
              entityId={impactCard.id}
              compact={false}
              showExpanded={true}
            />

            {/* Sources List */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">All Sources</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {impactCard.sources?.map((source, index) => (
                    <div
                      key={index}
                      className="p-4 border border-gray-200 rounded-lg"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 text-sm mb-1">
                            {source.title || source.name}
                          </h4>
                          <p className="text-xs text-gray-500 mb-2">
                            {source.name}
                          </p>
                          {source.excerpt && (
                            <p className="text-sm text-gray-600 line-clamp-2">
                              {source.excerpt}
                            </p>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(source.url, "_blank")}
                        >
                          <ExternalLink className="w-3 h-3" />
                        </Button>
                      </div>
                      {source.publish_date && (
                        <div className="text-xs text-gray-500">
                          Published: {formatDate(source.publish_date)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Actions Tab */}
        <TabsContent value="actions">
          <ActionTracker
            onGenerateActions={async () => {
              console.log("Generating actions for impact card:", impactCard.id);
            }}
            onAddCustomAction={() => {
              console.log(
                "Adding custom action for impact card:",
                impactCard.id
              );
            }}
          />
        </TabsContent>

        {/* Playbooks Tab */}
        <TabsContent value="playbooks">
          <PersonalPlaybooks
            onSelectPlaybook={(playbookId) => {
              console.log("Playbook selected:", playbookId);
            }}
            onCreatePlaybook={() => {
              console.log("Creating new playbook");
            }}
          />
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights">
          <div className="space-y-6">
            {/* AI-Generated Insights */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  AI-Generated Strategic Insights
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">
                    Market Position Analysis
                  </h4>
                  <p className="text-sm text-blue-800">
                    Based on the competitive intelligence gathered,{" "}
                    {impactCard.competitor_name} appears to be strengthening
                    their market position through strategic initiatives that
                    could impact your competitive advantage.
                  </p>
                </div>
                <div className="p-4 bg-yellow-50 rounded-lg">
                  <h4 className="font-medium text-yellow-900 mb-2">
                    Strategic Recommendations
                  </h4>
                  <ul className="text-sm text-yellow-800 space-y-1">
                    <li>
                      • Monitor their product development cycles more closely
                    </li>
                    <li>• Assess potential impact on your customer segments</li>
                    <li>• Consider accelerating competing initiatives</li>
                    <li>• Prepare defensive strategies for key markets</li>
                  </ul>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <h4 className="font-medium text-green-900 mb-2">
                    Opportunity Assessment
                  </h4>
                  <p className="text-sm text-green-800">
                    While {impactCard.competitor_name} is making strategic
                    moves, there are still opportunities to differentiate and
                    capture market share through focused execution on your
                    unique value propositions.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Trend Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Trend Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600 mb-1">
                      ↗️ +15%
                    </div>
                    <div className="text-sm text-gray-600">
                      Activity Increase
                    </div>
                    <div className="text-xs text-gray-500">vs. last month</div>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600 mb-1">
                      🎯 85%
                    </div>
                    <div className="text-sm text-gray-600">
                      Prediction Accuracy
                    </div>
                    <div className="text-xs text-gray-500">
                      based on patterns
                    </div>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600 mb-1">
                      ⚡ 3.2x
                    </div>
                    <div className="text-sm text-gray-600">
                      Faster Detection
                    </div>
                    <div className="text-xs text-gray-500">
                      vs. manual monitoring
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EnhancedImpactCard;
