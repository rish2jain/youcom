"""
Community Intelligence Schemas

Pydantic schemas for community-driven intelligence validation,
user contributions, reputation system, and expert network.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class ContributionType(str, Enum):
    """Types of community contributions"""
    INTELLIGENCE_VALIDATION = "intelligence_validation"
    SOURCE_CREDIBILITY = "source_credibility"
    COMPETITIVE_INSIGHT = "competitive_insight"
    MARKET_ANALYSIS = "market_analysis"
    EXPERT_ANALYSIS = "expert_analysis"
    FACT_CHECK = "fact_check"
    TREND_IDENTIFICATION = "trend_identification"


class ValidationStatus(str, Enum):
    """Status of community validations"""
    PENDING = "pending"
    VALIDATED = "validated"
    DISPUTED = "disputed"
    REJECTED = "rejected"
    EXPERT_REVIEWED = "expert_reviewed"


class ReputationLevel(str, Enum):
    """User reputation levels"""
    NEWCOMER = "newcomer"
    CONTRIBUTOR = "contributor"
    TRUSTED = "trusted"
    EXPERT = "expert"
    AUTHORITY = "authority"


# Community User Schemas
class CommunityUserBase(BaseModel):
    """Base community user schema"""
    expertise_areas: List[str] = Field(default_factory=list)
    bio: Optional[str] = None
    linkedin_profile: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None


class CommunityUserCreate(CommunityUserBase):
    """Schema for creating community user profile"""
    user_id: str


class CommunityUserUpdate(BaseModel):
    """Schema for updating community user profile"""
    expertise_areas: Optional[List[str]] = None
    bio: Optional[str] = None
    linkedin_profile: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None


class CommunityUserResponse(CommunityUserBase):
    """Schema for community user response"""
    id: int
    user_id: str
    reputation_score: int
    reputation_level: ReputationLevel
    verified_expert: bool
    total_contributions: int
    successful_validations: int
    accuracy_rate: float
    badges: List[str]
    achievements: Dict[str, Any]
    created_at: datetime
    last_active: datetime

    class Config:
        from_attributes = True


# Community Contribution Schemas
class CommunityContributionBase(BaseModel):
    """Base community contribution schema"""
    contribution_type: ContributionType
    title: str = Field(..., min_length=5, max_length=200)
    content: str = Field(..., min_length=20)
    company_mentioned: Optional[str] = None
    industry: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    evidence_links: List[str] = Field(default_factory=list)
    confidence_level: float = Field(default=0.5, ge=0.0, le=1.0)


class CommunityContributionCreate(CommunityContributionBase):
    """Schema for creating community contribution"""
    pass


class CommunityContributionUpdate(BaseModel):
    """Schema for updating community contribution"""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    content: Optional[str] = Field(None, min_length=20)
    tags: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    evidence_links: Optional[List[str]] = None
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)


class CommunityContributionResponse(CommunityContributionBase):
    """Schema for community contribution response"""
    id: int
    contributor_id: int
    validation_status: ValidationStatus
    validation_count: int
    positive_validations: int
    negative_validations: int
    quality_score: float
    community_rating: float
    expert_reviewed: bool
    views: int
    shares: int
    citations: int
    created_at: datetime
    updated_at: datetime
    
    # Contributor information
    contributor: Optional[CommunityUserResponse] = None

    class Config:
        from_attributes = True


# Community Validation Schemas
class CommunityValidationBase(BaseModel):
    """Base community validation schema"""
    validation_type: str = Field(..., pattern="^(accuracy|relevance|completeness)$")
    is_positive: bool
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    feedback: Optional[str] = None
    suggested_improvements: Optional[str] = None
    additional_sources: List[str] = Field(default_factory=list)
    accuracy_rating: Optional[int] = Field(None, ge=1, le=5)
    relevance_rating: Optional[int] = Field(None, ge=1, le=5)
    completeness_rating: Optional[int] = Field(None, ge=1, le=5)
    time_spent_minutes: Optional[int] = Field(None, ge=1)


class CommunityValidationCreate(CommunityValidationBase):
    """Schema for creating community validation"""
    contribution_id: int


class CommunityValidationResponse(CommunityValidationBase):
    """Schema for community validation response"""
    id: int
    contribution_id: int
    validator_id: int
    validation_method: Optional[str] = None
    created_at: datetime
    
    # Validator information
    validator: Optional[CommunityUserResponse] = None

    class Config:
        from_attributes = True


# Expert Network Schemas
class ExpertNetworkBase(BaseModel):
    """Base expert network schema"""
    credentials: Dict[str, Any] = Field(default_factory=dict)
    specializations: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    available_for_consultation: bool = True
    hourly_rate: Optional[float] = Field(None, ge=0)
    max_hours_per_week: int = Field(default=10, ge=1, le=40)
    preferred_contact_method: str = Field(default="platform")


class ExpertNetworkCreate(ExpertNetworkBase):
    """Schema for creating expert network profile"""
    community_user_id: int


class ExpertNetworkUpdate(BaseModel):
    """Schema for updating expert network profile"""
    credentials: Optional[Dict[str, Any]] = None
    specializations: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    available_for_consultation: Optional[bool] = None
    hourly_rate: Optional[float] = Field(None, ge=0)
    max_hours_per_week: Optional[int] = Field(None, ge=1, le=40)
    preferred_contact_method: Optional[str] = None


class ExpertNetworkResponse(ExpertNetworkBase):
    """Schema for expert network response"""
    id: int
    community_user_id: int
    verification_status: str
    verified_by: Optional[str] = None
    verification_date: Optional[datetime] = None
    expert_score: float
    analysis_count: int
    accuracy_rate: float
    response_time_hours: float
    created_at: datetime

    class Config:
        from_attributes = True


# Community Challenge Schemas
class CommunityChallengeBase(BaseModel):
    """Base community challenge schema"""
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=20)
    challenge_type: str = Field(..., pattern="^(research|validation|analysis)$")
    target_company: Optional[str] = None
    target_industry: Optional[str] = None
    research_question: str = Field(..., min_length=10)
    reward_points: int = Field(default=100, ge=10)
    reward_badges: List[str] = Field(default_factory=list)
    monetary_reward: Optional[float] = Field(None, ge=0)
    end_date: datetime
    difficulty_level: str = Field(default="medium", pattern="^(easy|medium|hard|expert)$")
    required_expertise: List[str] = Field(default_factory=list)


class CommunityChallengeCreate(CommunityChallengeBase):
    """Schema for creating community challenge"""
    pass


class CommunityChallengeResponse(CommunityChallengeBase):
    """Schema for community challenge response"""
    id: int
    status: str
    participant_count: int
    submission_count: int
    start_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Community Insight Schemas
class CommunityInsightBase(BaseModel):
    """Base community insight schema"""
    title: str = Field(..., min_length=5, max_length=200)
    summary: str = Field(..., min_length=50)
    insight_type: str = Field(..., pattern="^(trend|competitive_move|market_shift)$")
    companies_mentioned: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    geographic_regions: List[str] = Field(default_factory=list)


class CommunityInsightCreate(CommunityInsightBase):
    """Schema for creating community insight"""
    source_contributions: List[int] = Field(default_factory=list)
    expert_validations: List[int] = Field(default_factory=list)
    supporting_sources: List[str] = Field(default_factory=list)


class CommunityInsightResponse(CommunityInsightBase):
    """Schema for community insight response"""
    id: int
    contributing_users: int
    validation_score: float
    confidence_level: float
    views: int
    shares: int
    citations: int
    accuracy_score: float
    relevance_score: float
    timeliness_score: float
    created_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Leaderboard Schemas
class LeaderboardEntry(BaseModel):
    """Individual leaderboard entry"""
    user_id: int
    username: str
    score: float
    rank: int
    badge: Optional[str] = None
    change_from_previous: Optional[int] = None


class CommunityLeaderboardResponse(BaseModel):
    """Schema for community leaderboard response"""
    id: int
    leaderboard_type: str
    category: str
    period_start: datetime
    period_end: datetime
    rankings: List[LeaderboardEntry]
    total_participants: int
    last_updated: datetime

    class Config:
        from_attributes = True


# Gamification Schemas
class BadgeDefinition(BaseModel):
    """Badge definition schema"""
    name: str
    description: str
    icon: str
    requirements: Dict[str, Any]
    points_value: int
    rarity: str = Field(default="common", pattern="^(common|uncommon|rare|epic|legendary)$")


class Achievement(BaseModel):
    """Achievement schema"""
    name: str
    description: str
    progress: float = Field(ge=0.0, le=1.0)
    completed: bool = False
    completed_at: Optional[datetime] = None
    reward_points: int
    reward_badges: List[str] = Field(default_factory=list)


class ReputationUpdate(BaseModel):
    """Reputation update schema"""
    user_id: int
    points_change: int
    reason: str
    activity_type: str
    activity_id: Optional[int] = None


# Analytics Schemas
class CommunityAnalytics(BaseModel):
    """Community analytics schema"""
    total_users: int
    active_users_30d: int
    total_contributions: int
    contributions_30d: int
    total_validations: int
    validations_30d: int
    average_accuracy_rate: float
    expert_count: int
    top_contributors: List[LeaderboardEntry]
    trending_topics: List[str]
    engagement_metrics: Dict[str, float]


class ContributionAnalytics(BaseModel):
    """Contribution analytics schema"""
    contribution_id: int
    views: int
    shares: int
    citations: int
    validation_rate: float
    quality_score: float
    engagement_score: float
    impact_score: float
    trending_score: float


# Search and Filter Schemas
class CommunitySearchRequest(BaseModel):
    """Community search request schema"""
    query: str = Field(..., min_length=2)
    contribution_types: Optional[List[ContributionType]] = None
    industries: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    min_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_validation_count: Optional[int] = Field(None, ge=0)
    expert_reviewed_only: bool = False
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = Field(default="relevance", pattern="^(relevance|date|quality|popularity)$")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class CommunitySearchResponse(BaseModel):
    """Community search response schema"""
    total_results: int
    results: List[CommunityContributionResponse]
    facets: Dict[str, List[Dict[str, Any]]]
    suggestions: List[str]


# Notification Schemas
class CommunityNotification(BaseModel):
    """Community notification schema"""
    user_id: int
    notification_type: str
    title: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    read: bool = False
    created_at: datetime