"""
Insight Timeline models for tracking changes and deltas in competitive intelligence.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from .base import Base

class InsightTimeline(Base):
    """Track historical insights and changes over time."""
    __tablename__ = "insight_timelines"
    
    id = Column(Integer, primary_key=True, index=True)
    impact_card_id = Column(Integer, ForeignKey("impact_cards.id"), nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    
    # Timeline tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    previous_analysis_date = Column(DateTime, nullable=True)
    
    # Risk score changes
    current_risk_score = Column(Float, nullable=False)
    previous_risk_score = Column(Float, nullable=True)
    risk_score_delta = Column(Float, nullable=True)  # Calculated field
    
    # Content changes
    new_stories_count = Column(Integer, default=0)
    updated_stories_count = Column(Integer, default=0)
    new_evidence_count = Column(Integer, default=0)
    
    # Change highlights
    key_changes = Column(JSON, nullable=True)  # List of change descriptions
    fresh_insights = Column(JSON, nullable=True)  # New insights since last run
    trend_shifts = Column(JSON, nullable=True)  # Trend direction changes
    
    # Metadata
    analysis_version = Column(String(50), nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Relationships
    impact_card = relationship("ImpactCard", back_populates="timeline_entries")
    delta_highlights = relationship("DeltaHighlight", back_populates="timeline", cascade="all, delete-orphan")

class DeltaHighlight(Base):
    """Individual delta highlights for timeline entries."""
    __tablename__ = "delta_highlights"
    
    id = Column(Integer, primary_key=True, index=True)
    timeline_id = Column(Integer, ForeignKey("insight_timelines.id"), nullable=False)
    
    # Highlight details
    highlight_type = Column(String(50), nullable=False)  # 'new_story', 'risk_change', 'trend_shift'
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Importance and freshness
    importance_score = Column(Float, default=0.5)  # 0.0 to 1.0
    freshness_hours = Column(Integer, nullable=True)  # Hours since this change
    
    # Visual indicators
    badge_type = Column(String(20), nullable=True)  # 'new', 'updated', 'trending', 'alert'
    badge_color = Column(String(20), nullable=True)  # 'green', 'yellow', 'red', 'blue'
    
    # Source information
    source_url = Column(String(1000), nullable=True)
    source_name = Column(String(200), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_dismissed = Column(Boolean, default=False)
    
    # Relationships
    timeline = relationship("InsightTimeline", back_populates="delta_highlights")

class TrendSparkline(Base):
    """Store sparkline data for trend visualization."""
    __tablename__ = "trend_sparklines"
    
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # 'risk_score', 'activity_level', 'sentiment'
    
    # Time series data
    data_points = Column(JSON, nullable=False)  # List of {timestamp, value} objects
    time_range = Column(String(20), nullable=False)  # '7d', '30d', '90d'
    
    # Trend analysis
    trend_direction = Column(String(20), nullable=True)  # 'up', 'down', 'stable'
    trend_strength = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)