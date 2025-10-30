"""
Community Intelligence Models

Models for community-driven intelligence validation, user contributions,
reputation system, and expert network integration.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from app.database import Base


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
    NEWCOMER = "newcomer"          # 0-99 points
    CONTRIBUTOR = "contributor"     # 100-499 points
    TRUSTED = "trusted"            # 500-999 points
    EXPERT = "expert"              # 1000-2499 points
    AUTHORITY = "authority"        # 2500+ points


class CommunityUser(Base):
    """Community user profile with reputation and expertise"""
    __tablename__ = "community_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, index=True)
    
    # Reputation System
    reputation_score = Column(Integer, default=0)
    reputation_level = Column(String, default=ReputationLevel.NEWCOMER)
    
    # Expertise Areas
    expertise_areas = Column(JSON, default=list)  # List of industry/topic expertise
    verified_expert = Column(Boolean, default=False)
    expert_verification_date = Column(DateTime, nullable=True)
    
    # Activity Metrics
    total_contributions = Column(Integer, default=0)
    successful_validations = Column(Integer, default=0)
    accuracy_rate = Column(Float, default=0.0)
    
    # Badges and Achievements
    badges = Column(JSON, default=list)  # List of earned badges
    achievements = Column(JSON, default=dict)  # Achievement progress
    
    # Profile Information
    bio = Column(Text, nullable=True)
    linkedin_profile = Column(String, nullable=True)
    company = Column(String, nullable=True)
    title = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contributions = relationship("CommunityContribution", back_populates="contributor")
    validations = relationship("CommunityValidation", back_populates="validator")


class CommunityContribution(Base):
    """User-contributed intelligence and insights"""
    __tablename__ = "community_contributions"

    id = Column(Integer, primary_key=True, index=True)
    contributor_id = Column(Integer, ForeignKey("community_users.id"), index=True)
    
    # Contribution Details
    contribution_type = Column(String, index=True)  # ContributionType enum
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    
    # Context and Metadata
    company_mentioned = Column(String, nullable=True, index=True)
    industry = Column(String, nullable=True, index=True)
    tags = Column(JSON, default=list)  # Searchable tags
    
    # Source Information
    sources = Column(JSON, default=list)  # Supporting sources
    evidence_links = Column(JSON, default=list)  # Evidence URLs
    confidence_level = Column(Float, default=0.5)  # Contributor's confidence
    
    # Validation Status
    validation_status = Column(String, default=ValidationStatus.PENDING)
    validation_count = Column(Integer, default=0)
    positive_validations = Column(Integer, default=0)
    negative_validations = Column(Integer, default=0)
    
    # Quality Metrics
    quality_score = Column(Float, default=0.0)
    community_rating = Column(Float, default=0.0)
    expert_reviewed = Column(Boolean, default=False)
    
    # Impact Tracking
    views = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    citations = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contributor = relationship("CommunityUser", back_populates="contributions")
    validations = relationship("CommunityValidation", back_populates="contribution")


class CommunityValidation(Base):
    """Community validation of contributions and intelligence"""
    __tablename__ = "community_validations"

    id = Column(Integer, primary_key=True, index=True)
    contribution_id = Column(Integer, ForeignKey("community_contributions.id"), index=True)
    validator_id = Column(Integer, ForeignKey("community_users.id"), index=True)
    
    # Validation Details
    validation_type = Column(String, nullable=False)  # accuracy, relevance, completeness
    is_positive = Column(Boolean, nullable=False)
    confidence = Column(Float, default=0.5)
    
    # Validation Content
    feedback = Column(Text, nullable=True)
    suggested_improvements = Column(Text, nullable=True)
    additional_sources = Column(JSON, default=list)
    
    # Quality Assessment
    accuracy_rating = Column(Integer, nullable=True)  # 1-5 scale
    relevance_rating = Column(Integer, nullable=True)  # 1-5 scale
    completeness_rating = Column(Integer, nullable=True)  # 1-5 scale
    
    # Validation Metadata
    validation_method = Column(String, nullable=True)  # manual, automated, expert
    time_spent_minutes = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contribution = relationship("CommunityContribution", back_populates="validations")
    validator = relationship("CommunityUser", back_populates="validations")


class ExpertNetwork(Base):
    """Expert analyst network for high-quality intelligence"""
    __tablename__ = "expert_network"

    id = Column(Integer, primary_key=True, index=True)
    community_user_id = Column(Integer, ForeignKey("community_users.id"), unique=True)
    
    # Expert Credentials
    credentials = Column(JSON, default=dict)  # Education, certifications, experience
    specializations = Column(JSON, default=list)  # Specific areas of expertise
    industries = Column(JSON, default=list)  # Industry expertise
    
    # Verification Status
    verification_status = Column(String, default="pending")  # pending, verified, rejected
    verified_by = Column(String, nullable=True)  # Admin who verified
    verification_date = Column(DateTime, nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Expert Metrics
    expert_score = Column(Float, default=0.0)
    analysis_count = Column(Integer, default=0)
    accuracy_rate = Column(Float, default=0.0)
    response_time_hours = Column(Float, default=24.0)
    
    # Availability
    available_for_consultation = Column(Boolean, default=True)
    hourly_rate = Column(Float, nullable=True)
    max_hours_per_week = Column(Integer, default=10)
    
    # Contact Information
    preferred_contact_method = Column(String, default="platform")
    contact_details = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CommunityChallenge(Base):
    """Community challenges and competitions"""
    __tablename__ = "community_challenges"

    id = Column(Integer, primary_key=True, index=True)
    
    # Challenge Details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    challenge_type = Column(String, nullable=False)  # research, validation, analysis
    
    # Challenge Parameters
    target_company = Column(String, nullable=True)
    target_industry = Column(String, nullable=True)
    research_question = Column(Text, nullable=False)
    
    # Rewards and Incentives
    reward_points = Column(Integer, default=100)
    reward_badges = Column(JSON, default=list)
    monetary_reward = Column(Float, nullable=True)
    
    # Challenge Status
    status = Column(String, default="active")  # active, completed, cancelled
    participant_count = Column(Integer, default=0)
    submission_count = Column(Integer, default=0)
    
    # Timeline
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=False)
    
    # Challenge Metadata
    difficulty_level = Column(String, default="medium")  # easy, medium, hard, expert
    required_expertise = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CommunityInsight(Base):
    """Aggregated community insights and intelligence"""
    __tablename__ = "community_insights"

    id = Column(Integer, primary_key=True, index=True)
    
    # Insight Details
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    insight_type = Column(String, nullable=False)  # trend, competitive_move, market_shift
    
    # Context
    companies_mentioned = Column(JSON, default=list)
    industries = Column(JSON, default=list)
    geographic_regions = Column(JSON, default=list)
    
    # Community Validation
    contributing_users = Column(Integer, default=0)
    validation_score = Column(Float, default=0.0)
    confidence_level = Column(Float, default=0.0)
    
    # Supporting Evidence
    source_contributions = Column(JSON, default=list)  # Contributing contribution IDs
    expert_validations = Column(JSON, default=list)  # Expert validation IDs
    supporting_sources = Column(JSON, default=list)  # External sources
    
    # Impact and Reach
    views = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    citations = Column(Integer, default=0)
    
    # Quality Metrics
    accuracy_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    timeliness_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)


class CommunityLeaderboard(Base):
    """Community leaderboards and rankings"""
    __tablename__ = "community_leaderboards"

    id = Column(Integer, primary_key=True, index=True)
    
    # Leaderboard Configuration
    leaderboard_type = Column(String, nullable=False)  # weekly, monthly, yearly, all_time
    category = Column(String, nullable=False)  # contributions, validations, accuracy, expertise
    
    # Time Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Rankings
    rankings = Column(JSON, default=list)  # List of user rankings with scores
    
    # Metadata
    total_participants = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)