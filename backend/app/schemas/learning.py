"""
Pydantic schemas for learning loop API endpoints.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class AlertOutcomeCreate(BaseModel):
    """Schema for creating a new alert outcome record."""
    alert_id: Optional[int] = None
    competitor_name: str = Field(..., min_length=1, max_length=255)
    action_taken: str = Field(..., pattern="^(acted_upon|dismissed|escalated|ignored)$")
    outcome_quality: str = Field(..., pattern="^(helpful|not_helpful|false_positive|missed_signal)$")
    user_feedback: Optional[str] = None
    business_impact: Optional[str] = Field(None, pattern="^(high|medium|low|none)$")
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    processing_time: Optional[float] = Field(None, ge=0)
    source_count: Optional[int] = Field(None, ge=0)

class AlertOutcomeResponse(BaseModel):
    """Schema for alert outcome responses."""
    id: int
    alert_id: Optional[int]
    competitor_name: str
    action_taken: str
    outcome_quality: str
    user_feedback: Optional[str]
    business_impact: Optional[str]
    created_at: datetime
    confidence_score: Optional[float]
    processing_time: Optional[float]
    source_count: Optional[int]
    
    class Config:
        from_attributes = True

class LearningInsightResponse(BaseModel):
    """Schema for learning insight responses."""
    type: str
    competitor: str
    current_value: float
    suggested_value: float
    confidence: float
    reason: str
    potential_impact: str
    created_at: datetime
    status: str = "pending"

class ApplyInsightRequest(BaseModel):
    """Schema for applying a learning insight."""
    type: str = Field(..., pattern="^(threshold_adjustment|keyword_optimization|source_quality|timing_improvement)$")
    competitor: str = Field(..., min_length=1, max_length=255)
    current_value: float
    suggested_value: float
    confidence: float
    reason: str
    potential_impact: str

class LearningMetrics(BaseModel):
    """Schema for learning loop performance metrics."""
    period_days: int
    total_outcomes: int
    helpful_rate: float
    action_rate: float
    false_positive_rate: float
    top_competitors: List[Dict[str, Any]]
    learning_effectiveness: Dict[str, float]

class MonitoringRecommendation(BaseModel):
    """Schema for monitoring improvement recommendations."""
    type: str
    priority: str = Field(..., pattern="^(high|medium|low)$")
    title: str
    description: str
    expected_improvement: str
    implementation_effort: str = Field(..., pattern="^(low|medium|high)$")
    confidence: float = Field(..., ge=0, le=1)

class FeedbackAnalysis(BaseModel):
    """Schema for feedback pattern analysis."""
    competitor_name: str
    total_feedback: int
    helpful_percentage: float
    action_percentage: float
    false_positive_percentage: float
    common_issues: List[str]
    recommendations: List[MonitoringRecommendation]

class LearningTrend(BaseModel):
    """Schema for learning effectiveness trends."""
    date: datetime
    helpful_rate: float
    action_rate: float
    false_positive_rate: float
    total_alerts: int
    user_satisfaction: float