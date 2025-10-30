"""
Pydantic schemas for evidence badges and source tracking.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SourceEvidenceBase(BaseModel):
    source_name: str = Field(..., max_length=200)
    source_url: str = Field(..., max_length=1000)
    source_tier: int = Field(..., ge=1, le=4, description="Source tier: 1=authoritative, 4=unverified")
    title: Optional[str] = Field(None, max_length=500)
    excerpt: Optional[str] = None
    publish_date: Optional[datetime] = None
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    credibility_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    you_api_source: Optional[str] = Field(None, description="Which You.com API provided this source")

class SourceEvidenceCreate(SourceEvidenceBase):
    pass

class SourceEvidence(SourceEvidenceBase):
    id: int
    badge_id: int
    extracted_at: datetime
    
    class Config:
        from_attributes = True

class EvidenceBadgeBase(BaseModel):
    entity_type: str = Field(..., description="Type: impact_card, insight, recommendation")
    entity_id: int
    confidence_percentage: float = Field(..., ge=0.0, le=100.0)
    total_sources: int = Field(default=0, ge=0)
    tier_1_sources: int = Field(default=0, ge=0)
    tier_2_sources: int = Field(default=0, ge=0)
    tier_3_sources: int = Field(default=0, ge=0)
    tier_4_sources: int = Field(default=0, ge=0)
    freshness_score: float = Field(..., ge=0.0, le=1.0)
    oldest_source_hours: Optional[int] = Field(None, ge=0)
    newest_source_hours: Optional[int] = Field(None, ge=0)
    average_source_age_hours: Optional[float] = Field(None, ge=0.0)
    cross_validation_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    bias_detection_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    fact_check_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    top_sources: Optional[List[Dict[str, Any]]] = None

class EvidenceBadgeCreate(EvidenceBadgeBase):
    pass

class EvidenceBadge(EvidenceBadgeBase):
    id: int
    confidence_level: str
    badge_color: Optional[str] = None
    badge_icon: Optional[str] = None
    display_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed properties
    weighted_source_score: float = Field(..., description="Computed weighted source quality score")
    overall_quality_score: float = Field(..., description="Computed overall quality score")
    
    # Related data
    source_details: List[SourceEvidence] = []
    
    class Config:
        from_attributes = True

class EvidenceBadgeResponse(BaseModel):
    """Response model for evidence badge with expanded details."""
    badge: EvidenceBadge
    top_sources_expanded: List[SourceEvidence] = Field(default_factory=list)
    quality_breakdown: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True

class ConfidenceMetrics(BaseModel):
    """Aggregated confidence metrics for display."""
    overall_confidence: float = Field(..., ge=0.0, le=100.0)
    confidence_level: str = Field(..., description="low, medium, high, very_high")
    source_count: int = Field(..., ge=0)
    tier_breakdown: Dict[str, int] = Field(default_factory=dict)
    freshness_indicator: str = Field(..., description="very_fresh, fresh, stale, very_stale")
    quality_indicators: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True