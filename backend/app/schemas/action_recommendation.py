from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime

class ResourceEstimateBase(BaseModel):
    time_required: str = Field(..., description="Human readable time estimate")
    estimated_hours_min: Optional[int] = Field(None, ge=0, description="Minimum hours estimate")
    estimated_hours_max: Optional[int] = Field(None, ge=0, description="Maximum hours estimate")
    team_members: int = Field(1, ge=1, description="Number of team members required")
    skill_requirements: List[str] = Field(default_factory=list, description="Required skills")
    budget_impact: str = Field(..., pattern="^(low|medium|high)$", description="Budget impact level")
    budget_estimate_min: Optional[float] = Field(None, ge=0, description="Minimum budget estimate")
    budget_estimate_max: Optional[float] = Field(None, ge=0, description="Maximum budget estimate")
    dependencies: List[Dict[str, Any]] = Field(default_factory=list, description="Dependencies")
    constraints: List[Dict[str, Any]] = Field(default_factory=list, description="Constraints")
    risks: List[Dict[str, Any]] = Field(default_factory=list, description="Risk factors")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence in estimate")
    estimation_method: Optional[str] = Field(None, description="How estimate was derived")

class ResourceEstimateCreate(ResourceEstimateBase):
    action_recommendation_id: int

class ResourceEstimate(ResourceEstimateBase):
    id: int
    action_recommendation_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ActionRecommendationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Action title")
    description: str = Field(..., min_length=1, description="Detailed action description")
    category: str = Field(..., pattern="^(immediate|short-term|strategic)$", description="Action category")
    priority: str = Field(..., pattern="^(high|medium|low)$", description="Action priority")
    timeline: str = Field(..., description="Expected timeline for completion")
    estimated_hours: Optional[int] = Field(None, ge=0, description="Estimated hours to complete")
    team_members_required: Optional[int] = Field(None, ge=1, description="Team members needed")
    budget_impact: str = Field(..., pattern="^(low|medium|high)$", description="Budget impact")
    dependencies: List[str] = Field(default_factory=list, description="Action dependencies")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendation")
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Expected impact score")
    effort_score: float = Field(..., ge=0.0, le=1.0, description="Required effort score")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall recommendation score")
    reasoning: List[str] = Field(default_factory=list, description="Reasoning steps")
    evidence_links: List[Dict[str, str]] = Field(default_factory=list, description="Supporting evidence")
    okr_alignment: Optional[str] = Field(None, description="OKR goal alignment")
    status: str = Field("pending", pattern="^(pending|approved|rejected|completed)$")
    assigned_to: Optional[str] = Field(None, description="Person assigned to action")
    owner_type: Optional[str] = Field(None, description="Owner type (team, individual, department)")

    @field_validator('dependencies')
    @classmethod
    def validate_dependencies(cls, v: List[str]) -> List[str]:
        """Validate dependencies list"""
        if len(v) > 20:  # Reasonable limit
            raise ValueError('Maximum 20 dependencies allowed')
        return [dep.strip() for dep in v if dep.strip()]

    @field_validator('reasoning')
    @classmethod
    def validate_reasoning(cls, v: List[str]) -> List[str]:
        """Validate reasoning steps"""
        if len(v) > 10:  # Reasonable limit
            raise ValueError('Maximum 10 reasoning steps allowed')
        return [reason.strip() for reason in v if reason.strip()]

class ActionRecommendationCreate(ActionRecommendationBase):
    impact_card_id: int
    resource_estimate: Optional[ResourceEstimateBase] = None

class ActionRecommendation(ActionRecommendationBase):
    id: int
    impact_card_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    resource_estimate: Optional[ResourceEstimate] = None

    class Config:
        from_attributes = True

class ActionRecommendationList(BaseModel):
    items: List[ActionRecommendation]
    total: int

class ActionRecommendationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, pattern="^(immediate|short-term|strategic)$")
    priority: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    timeline: Optional[str] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    team_members_required: Optional[int] = Field(None, ge=1)
    budget_impact: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    dependencies: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(pending|approved|rejected|completed)$")
    assigned_to: Optional[str] = None
    owner_type: Optional[str] = None
    okr_alignment: Optional[str] = None

class DecisionEngineRequest(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from impact card")
    competitor_name: str = Field(..., min_length=1, description="Competitor name")
    impact_areas: List[Dict[str, Any]] = Field(default_factory=list, description="Impact areas")
    key_insights: List[str] = Field(default_factory=list, description="Key insights")
    confidence_score: int = Field(..., ge=0, le=100, description="Confidence score")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

class DecisionEngineResponse(BaseModel):
    recommendations: List[ActionRecommendationBase]
    total_recommendations: int
    processing_time_ms: int
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    reasoning_summary: str