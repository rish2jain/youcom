"""
Evidence Badge models for tracking confidence and source quality.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship

from .base import Base

class EvidenceBadge(Base):
    """Track confidence and evidence quality for insights and recommendations."""
    __tablename__ = "evidence_badges"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Associated entity (can be impact card, insight, or recommendation)
    entity_type = Column(String(50), nullable=False)  # 'impact_card', 'insight', 'recommendation'
    entity_id = Column(Integer, nullable=False)
    
    # Confidence metrics
    confidence_percentage = Column(Float, nullable=False)  # 0.0 to 100.0
    confidence_level = Column(String(20), nullable=False)  # 'low', 'medium', 'high', 'very_high'
    
    # Source quality
    total_sources = Column(Integer, default=0)
    tier_1_sources = Column(Integer, default=0)  # WSJ, Reuters, Bloomberg, FT
    tier_2_sources = Column(Integer, default=0)  # TechCrunch, VentureBeat, The Information
    tier_3_sources = Column(Integer, default=0)  # HN, Reddit (verified), Medium (verified)
    tier_4_sources = Column(Integer, default=0)  # Blogs, Twitter/X, press releases
    
    # Freshness metrics
    freshness_score = Column(Float, nullable=False)  # 0.0 to 1.0
    oldest_source_hours = Column(Integer, nullable=True)
    newest_source_hours = Column(Integer, nullable=True)
    average_source_age_hours = Column(Float, nullable=True)
    
    # Quality indicators
    cross_validation_score = Column(Float, nullable=True)  # How well sources agree
    bias_detection_score = Column(Float, nullable=True)    # Detected bias level
    fact_check_score = Column(Float, nullable=True)        # Fact-checking confidence
    
    # Top supporting sources (for expansion)
    top_sources = Column(JSON, nullable=True)  # List of top 3 sources with metadata
    
    # Badge display
    badge_color = Column(String(20), nullable=True)  # 'green', 'yellow', 'orange', 'red'
    badge_icon = Column(String(50), nullable=True)   # Icon identifier
    display_text = Column(String(100), nullable=True)  # Short display text
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Computed fields
    @property
    def weighted_source_score(self) -> float:
        """Calculate weighted source quality score."""
        if self.total_sources == 0:
            return 0.0
        
        # Weights for different tiers
        tier_weights = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.3}
        
        weighted_sum = (
            (self.tier_1_sources or 0) * tier_weights[1] +
            (self.tier_2_sources or 0) * tier_weights[2] +
            (self.tier_3_sources or 0) * tier_weights[3] +
            (self.tier_4_sources or 0) * tier_weights[4]
        )
        
        return min(1.0, weighted_sum / self.total_sources)
    
    @property
    def overall_quality_score(self) -> float:
        """Calculate overall quality score combining all factors."""
        confidence_weight = 0.4
        source_weight = 0.3
        freshness_weight = 0.2
        validation_weight = 0.1
        
        confidence_score = self.confidence_percentage / 100.0
        source_score = self.weighted_source_score
        freshness_score = self.freshness_score or 0.0
        validation_score = self.cross_validation_score or 0.5
        
        return (
            confidence_score * confidence_weight +
            source_score * source_weight +
            freshness_score * freshness_weight +
            validation_score * validation_weight
        )

class SourceEvidence(Base):
    """Individual source evidence for detailed tracking."""
    __tablename__ = "source_evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    badge_id = Column(Integer, ForeignKey("evidence_badges.id"), nullable=False)
    
    # Source details
    source_name = Column(String(200), nullable=False)
    source_url = Column(String(1000), nullable=False)
    source_tier = Column(Integer, nullable=False)  # 1-4 tier classification
    
    # Content details
    title = Column(String(500), nullable=True)
    excerpt = Column(Text, nullable=True)
    publish_date = Column(DateTime, nullable=True)
    
    # Quality metrics
    relevance_score = Column(Float, nullable=True)  # How relevant to the insight
    credibility_score = Column(Float, nullable=True)  # Source credibility
    sentiment_score = Column(Float, nullable=True)   # Sentiment analysis
    
    # Metadata
    extracted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    you_api_source = Column(String(50), nullable=True)  # Which You.com API provided this
    
    # Relationships
    badge = relationship("EvidenceBadge", backref="source_details")