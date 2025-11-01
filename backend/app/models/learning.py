"""
Database models for the learning loop functionality.
Tracks alert outcomes and learning insights to improve monitoring.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from ..database import Base

class AlertOutcome(Base):
    """
    Records the outcome of competitive intelligence alerts.
    Used to train the system and improve future monitoring.
    """
    __tablename__ = "alert_outcomes"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, nullable=True)  # Reference to original alert
    competitor_name = Column(String(255), nullable=False, index=True)
    
    # User actions
    action_taken = Column(String(50), nullable=False)  # acted_upon, dismissed, escalated, ignored
    outcome_quality = Column(String(50), nullable=False)  # helpful, not_helpful, false_positive, missed_signal
    user_feedback = Column(Text, nullable=True)
    business_impact = Column(String(20), nullable=True)  # high, medium, low, none
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String(100), nullable=True)  # For multi-user tracking
    
    # Learning metrics
    confidence_score = Column(Float, nullable=True)  # AI confidence in original alert
    processing_time = Column(Float, nullable=True)  # Time to generate alert
    source_count = Column(Integer, nullable=True)  # Number of sources used

class LearningInsight(Base):
    """
    AI-generated insights for improving monitoring effectiveness.
    Based on analysis of alert outcomes and user feedback.
    """
    __tablename__ = "learning_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    competitor_name = Column(String(255), nullable=False, index=True)
    
    # Insight details
    insight_type = Column(String(50), nullable=False)  # threshold_adjustment, keyword_optimization, etc.
    current_value = Column(Float, nullable=False)
    suggested_value = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)  # AI confidence in suggestion
    
    # Reasoning
    reason = Column(Text, nullable=False)
    potential_impact = Column(Text, nullable=False)
    supporting_data = Column(Text, nullable=True)  # JSON with supporting metrics
    
    # Status
    status = Column(String(20), default="pending")  # pending, applied, rejected
    applied_at = Column(DateTime, nullable=True)
    applied_by = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # When insight becomes stale

class MonitoringAdjustment(Base):
    """
    Records adjustments made to monitoring configuration based on learning.
    Tracks the effectiveness of applied insights.
    """
    __tablename__ = "monitoring_adjustments"
    
    id = Column(Integer, primary_key=True, index=True)
    competitor_name = Column(String(255), nullable=False, index=True)
    insight_id = Column(Integer, ForeignKey("learning_insights.id"), nullable=True)
    
    # Adjustment details
    adjustment_type = Column(String(50), nullable=False)
    old_value = Column(Float, nullable=False)
    new_value = Column(Float, nullable=False)
    
    # Effectiveness tracking
    alerts_before = Column(Integer, nullable=True)  # Alert count before adjustment
    alerts_after = Column(Integer, nullable=True)  # Alert count after adjustment
    quality_before = Column(Float, nullable=True)  # Quality score before
    quality_after = Column(Float, nullable=True)  # Quality score after
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    evaluation_date = Column(DateTime, nullable=True)  # When effectiveness was measured
    
    # Relationship
    insight = relationship("LearningInsight", backref="adjustments")

class FeedbackSession(Base):
    """
    Groups related feedback for analysis.
    Helps identify patterns in user behavior and preferences.
    """
    __tablename__ = "feedback_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    session_start = Column(DateTime, default=datetime.utcnow, nullable=False)
    session_end = Column(DateTime, nullable=True)
    
    # Session metrics
    alerts_reviewed = Column(Integer, default=0)
    actions_taken = Column(Integer, default=0)
    feedback_provided = Column(Integer, default=0)
    
    # User context
    user_role = Column(String(50), nullable=True)  # executive, analyst, etc.
    industry = Column(String(100), nullable=True)
    company_size = Column(String(50), nullable=True)