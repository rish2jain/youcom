"""
Pydantic schemas for insight timeline and delta highlights.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DeltaHighlightBase(BaseModel):
    highlight_type: str = Field(..., description="Type of highlight: new_story, risk_change, trend_shift")
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    freshness_hours: Optional[int] = None
    badge_type: Optional[str] = Field(None, description="Visual badge type: new, updated, trending, alert")
    badge_color: Optional[str] = Field(None, description="Badge color: green, yellow, red, blue")
    source_url: Optional[str] = None
    source_name: Optional[str] = None

class DeltaHighlightCreate(DeltaHighlightBase):
    pass

class DeltaHighlight(DeltaHighlightBase):
    id: int
    timeline_id: int
    created_at: datetime
    is_dismissed: bool = False
    
    class Config:
        from_attributes = True

class TrendSparklineBase(BaseModel):
    company_name: str = Field(..., max_length=255)
    metric_type: str = Field(..., description="Metric type: risk_score, activity_level, sentiment")
    data_points: List[Dict[str, Any]] = Field(..., description="Time series data points")
    time_range: str = Field(..., description="Time range: 7d, 30d, 90d")
    trend_direction: Optional[str] = Field(None, description="Trend direction: up, down, stable")
    trend_strength: Optional[float] = Field(None, ge=0.0, le=1.0)

class TrendSparklineCreate(TrendSparklineBase):
    pass

class TrendSparkline(TrendSparklineBase):
    id: int
    last_updated: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class InsightTimelineBase(BaseModel):
    company_name: str = Field(..., max_length=255)
    current_risk_score: float = Field(..., ge=0.0, le=100.0)
    previous_risk_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    new_stories_count: int = Field(default=0, ge=0)
    updated_stories_count: int = Field(default=0, ge=0)
    new_evidence_count: int = Field(default=0, ge=0)
    key_changes: Optional[List[str]] = None
    fresh_insights: Optional[List[str]] = None
    trend_shifts: Optional[List[str]] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)

class InsightTimelineCreate(InsightTimelineBase):
    impact_card_id: int
    previous_analysis_date: Optional[datetime] = None
    analysis_version: Optional[str] = None

class InsightTimeline(InsightTimelineBase):
    id: int
    impact_card_id: int
    created_at: datetime
    previous_analysis_date: Optional[datetime] = None
    risk_score_delta: Optional[float] = None
    analysis_version: Optional[str] = None
    
    # Related data
    delta_highlights: List[DeltaHighlight] = []
    
    class Config:
        from_attributes = True

class InsightDeltaResponse(BaseModel):
    """Response model for delta analysis."""
    timeline: InsightTimeline
    sparkline_data: Optional[TrendSparkline] = None
    summary: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True