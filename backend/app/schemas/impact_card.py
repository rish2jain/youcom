from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime

class ImpactArea(BaseModel):
    area: str
    impact_score: int = Field(ge=0, le=100)
    description: str

class RecommendedAction(BaseModel):
    action: str
    priority: str = Field(pattern="^(high|medium|low)$")
    timeline: str = Field(pattern="^(immediate|short-term|long-term)$")
    owner: str
    okr_goal: str
    impact_score: int = Field(ge=0, le=100)
    effort_score: int = Field(ge=0, le=100)
    score: float
    evidence: List[Dict[str, str]] = Field(default_factory=list)
    index: int

class SourceQuality(BaseModel):
    score: float
    tiers: Dict[str, int] = Field(default_factory=dict)
    total: int
    top_sources: List[Dict[str, Any]] = Field(default_factory=list)

class Explainability(BaseModel):
    reasoning: Optional[str]
    impact_areas: List[ImpactArea] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)
    source_summary: Optional[Dict[str, Any]] = None

class SourceBreakdown(BaseModel):
    news_articles: int = 0
    search_results: int = 0
    research_citations: int = 0

class APIUsage(BaseModel):
    news_calls: int = 0
    search_calls: int = 0
    chat_calls: int = 0
    ari_calls: int = 0
    total_calls: int = 0

class ImpactCardBase(BaseModel):
    competitor_name: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: str = Field(pattern="^(low|medium|high|critical)$")
    confidence_score: int = Field(ge=0, le=100)
    impact_areas: List[ImpactArea] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)
    recommended_actions: List[RecommendedAction] = Field(default_factory=list)
    next_steps_plan: List[RecommendedAction] = Field(default_factory=list)
    total_sources: int = 0
    source_breakdown: SourceBreakdown = Field(default_factory=SourceBreakdown)
    source_quality: Optional[SourceQuality] = None
    credibility_score: float = 0.0
    requires_review: bool = False
    api_usage: APIUsage = Field(default_factory=APIUsage)
    processing_time: Optional[str] = None
    explainability: Explainability = Field(default_factory=Explainability)

class ImpactCardCreate(ImpactCardBase):
    watch_item_id: int
    raw_data: Dict[str, Any] = Field(default_factory=dict)

class ImpactCard(ImpactCardBase):
    id: int
    watch_item_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class ImpactCardList(BaseModel):
    items: List[ImpactCard]
    total: int

class ImpactCardGenerate(BaseModel):
    competitor_name: str = Field(..., min_length=2, max_length=100, description="Competitor company name")
    keywords: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="List of keywords to monitor (max 10)"
    )

    @field_validator('competitor_name')
    @classmethod
    def validate_competitor_name(cls, v: str) -> str:
        """Validate and sanitize competitor name"""
        if not v or not v.strip():
            raise ValueError('Competitor name cannot be empty')
        # Strip whitespace and limit length
        sanitized = v.strip()[:100]
        return sanitized

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate and limit keywords"""
        if not v:
            return []
        if len(v) > 10:
            raise ValueError('Maximum 10 keywords allowed')
        # Sanitize each keyword and limit length
        sanitized = []
        for keyword in v:
            if keyword and keyword.strip():
                sanitized.append(keyword.strip()[:50])
        return sanitized[:10]  # Extra safety check
