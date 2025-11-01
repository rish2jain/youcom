export interface ResourceEstimate {
  id: number;
  action_recommendation_id: number;
  time_required: string;
  estimated_hours_min?: number;
  estimated_hours_max?: number;
  team_members: number;
  skill_requirements: string[];
  budget_impact: "low" | "medium" | "high";
  budget_estimate_min?: number;
  budget_estimate_max?: number;
  dependencies: Array<{
    name: string;
    type: string;
    description?: string;
  }>;
  constraints: Array<{
    name: string;
    type: string;
    description?: string;
  }>;
  risks: Array<{
    name: string;
    probability: number;
    impact: string;
    mitigation?: string;
  }>;
  confidence_level: number;
  estimation_method?: string;
  created_at: string;
  updated_at?: string;
}

export interface ActionRecommendation {
  id: number;
  impact_card_id: number;
  title: string;
  description: string;
  category: "immediate" | "short-term" | "strategic";
  priority: "high" | "medium" | "low";
  timeline: string;
  estimated_hours?: number;
  team_members_required?: number;
  budget_impact: "low" | "medium" | "high";
  dependencies: string[];
  confidence_score: number;
  impact_score: number;
  effort_score: number;
  overall_score: number;
  reasoning: string[];
  evidence_links: Array<{
    title: string;
    url: string;
    source?: string;
  }>;
  okr_alignment?: string;
  status: "pending" | "approved" | "rejected" | "completed";
  assigned_to?: string;
  owner_type?: string;
  created_at: string;
  updated_at?: string;
  resource_estimate?: ResourceEstimate;
}

export interface ActionRecommendationCreate {
  impact_card_id: number;
  title: string;
  description: string;
  category: "immediate" | "short-term" | "strategic";
  priority: "high" | "medium" | "low";
  timeline: string;
  estimated_hours?: number;
  team_members_required?: number;
  budget_impact: "low" | "medium" | "high";
  dependencies?: string[];
  confidence_score: number;
  impact_score: number;
  effort_score: number;
  overall_score: number;
  reasoning?: string[];
  evidence_links?: Array<{
    title: string;
    url: string;
    source?: string;
  }>;
  okr_alignment?: string;
  status?: "pending" | "approved" | "rejected" | "completed";
  assigned_to?: string;
  owner_type?: string;
  resource_estimate?: Omit<
    ResourceEstimate,
    "id" | "action_recommendation_id" | "created_at" | "updated_at"
  >;
}

export interface ActionRecommendationUpdate {
  title?: string;
  description?: string;
  category?: "immediate" | "short-term" | "strategic";
  priority?: "high" | "medium" | "low";
  timeline?: string;
  estimated_hours?: number;
  team_members_required?: number;
  budget_impact?: "low" | "medium" | "high";
  dependencies?: string[];
  status?: "pending" | "approved" | "rejected" | "completed";
  assigned_to?: string;
  owner_type?: string;
  okr_alignment?: string;
}

export interface DecisionEngineRequest {
  risk_score: number;
  competitor_name: string;
  impact_areas: Array<{
    area: string;
    impact_score: number;
    description: string;
  }>;
  key_insights: string[];
  confidence_score: number;
  context?: Record<string, any>;
}

export interface DecisionEngineResponse {
  recommendations: ActionRecommendation[];
  total_recommendations: number;
  processing_time_ms: number;
  confidence_level: number;
  reasoning_summary: string;
}

export interface ActionRecommendationList {
  items: ActionRecommendation[];
  total: number;
}
