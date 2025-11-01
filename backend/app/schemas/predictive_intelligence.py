"""Schemas for predictive intelligence API endpoints."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class PatternEventSchema(BaseModel):
    """Schema for pattern events."""
    id: int
    event_type: str
    description: str
    event_date: datetime
    risk_score: Optional[int] = None
    impact_areas: List[str] = Field(default_factory=list)
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = None
    
    class Config:
        from_attributes = True


class CompetitorPatternSchema(BaseModel):
    """Schema for competitor patterns."""
    id: int
    competitor_name: str
    pattern_type: str
    sequence: List[Dict[str, Any]] = Field(default_factory=list)
    frequency: int
    confidence: float
    average_duration: Optional[int] = None
    typical_intervals: List[int] = Field(default_factory=list)
    first_observed: datetime
    last_observed: datetime
    is_active: bool
    contributing_factors: List[str] = Field(default_factory=list)
    success_indicators: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PredictedEventSchema(BaseModel):
    """Schema for predicted events."""
    id: int
    pattern_id: int
    competitor_name: str
    event_type: str
    description: str
    probability: float
    confidence: float
    predicted_date: Optional[datetime] = None
    timeframe: str
    earliest_date: Optional[datetime] = None
    latest_date: Optional[datetime] = None
    reasoning: List[str] = Field(default_factory=list)
    trigger_events: List[str] = Field(default_factory=list)
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    status: str
    actual_outcome: Optional[str] = None
    validation_date: Optional[datetime] = None
    accuracy_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # ML enhancement fields
    ml_probability: Optional[float] = None
    ml_confidence: Optional[float] = None
    ml_reasoning: List[str] = Field(default_factory=list)
    confidence_intervals: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PredictionValidationRequest(BaseModel):
    """Schema for prediction validation requests."""
    actual_outcome: str = Field(..., min_length=10, max_length=1000)
    accuracy_score: float = Field(..., ge=0.0, le=1.0)
    notes: Optional[str] = Field(None, max_length=500)


class PatternAnalysisRequest(BaseModel):
    """Schema for pattern analysis requests."""
    competitor_name: str = Field(..., min_length=2, max_length=255)
    force_reanalysis: bool = Field(default=False)
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)


class PredictionGenerationRequest(BaseModel):
    """Schema for prediction generation requests."""
    competitor_name: str = Field(..., min_length=2, max_length=255)
    prediction_horizon_days: int = Field(default=90, ge=1, le=365)
    min_probability: float = Field(default=0.3, ge=0.0, le=1.0)


class PredictiveIntelligenceMetrics(BaseModel):
    """Schema for predictive intelligence metrics."""
    total_patterns: int
    active_patterns: int
    total_predictions: int
    pending_predictions: int
    validated_predictions: int
    overall_accuracy: float
    accuracy_by_type: Dict[str, float] = Field(default_factory=dict)
    pattern_confidence_avg: float
    prediction_confidence_avg: float
    top_competitors: List[Dict[str, Any]] = Field(default_factory=list)
    recent_predictions: List[PredictedEventSchema] = Field(default_factory=list)


class EnhancedImpactCardSchema(BaseModel):
    """Enhanced impact card schema with predictions."""
    # Base impact card fields
    id: int
    competitor_name: str
    risk_score: int
    risk_level: str
    confidence_score: int
    impact_areas: List[Dict[str, Any]] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)
    recommended_actions: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    
    # Predictive intelligence fields
    predicted_moves: List[PredictedEventSchema] = Field(default_factory=list)
    related_patterns: List[CompetitorPatternSchema] = Field(default_factory=list)
    prediction_summary: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class MLModelPerformance(BaseModel):
    """Schema for ML model performance metrics."""
    status: str
    total_predictions: int
    accurate_predictions: int
    accuracy_rate: float
    feature_importance: Dict[str, float] = Field(default_factory=dict)
    model_types: Dict[str, str] = Field(default_factory=dict)
    last_training_date: Optional[datetime] = None
    training_samples: int = 0


class PredictionDashboardData(BaseModel):
    """Schema for prediction dashboard data."""
    metrics: PredictiveIntelligenceMetrics
    recent_patterns: List[CompetitorPatternSchema] = Field(default_factory=list)
    high_probability_predictions: List[PredictedEventSchema] = Field(default_factory=list)
    competitor_activity: Dict[str, int] = Field(default_factory=dict)
    prediction_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    ml_performance: MLModelPerformance