"""User behavior tracking models for learning loop functionality."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


class UserAction(Base):
    """Records individual user actions for behavior analysis."""
    
    __tablename__ = "user_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), nullable=False)  # Track user sessions
    
    # Action details
    action_type = Column(String(50), nullable=False)  # dismiss, act, escalate, share, view, etc.
    target_type = Column(String(50), nullable=False)  # alert, impact_card, watchlist, etc.
    target_id = Column(String(255), nullable=False)   # ID of the target object
    
    # Context and metadata
    context = Column(JSON, nullable=True)  # Additional context data
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Action outcome tracking
    reason = Column(String(255), nullable=True)  # User-provided reason for action
    outcome = Column(String(255), nullable=True)  # Result of the action
    confidence = Column(Float, nullable=True)     # User confidence in action (0-1)
    
    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)  # Time to take action
    page_load_time_ms = Column(Integer, nullable=True) # Page performance context
    
    # Relationships
    user = relationship("User", back_populates="actions")
    
    def __repr__(self):
        return f"<UserAction(user_id={self.user_id}, action_type={self.action_type}, target_type={self.target_type})>"


class BehaviorPattern(Base):
    """Aggregated behavior patterns for individual users."""
    
    __tablename__ = "behavior_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Pattern identification
    pattern_type = Column(String(50), nullable=False)  # alert_response, threshold_preference, etc.
    target_type = Column(String(50), nullable=False)   # What type of content this pattern applies to
    
    # Pattern metrics
    total_interactions = Column(Integer, default=0)
    dismissal_rate = Column(Float, default=0.0)        # Percentage of dismissals
    action_rate = Column(Float, default=0.0)           # Percentage of actions taken
    escalation_rate = Column(Float, default=0.0)       # Percentage of escalations
    
    # Timing patterns
    average_response_time = Column(Float, default=0.0)  # Average time to respond (seconds)
    peak_activity_hours = Column(JSON, nullable=True)   # Hours when user is most active
    
    # Threshold preferences
    suggested_threshold = Column(Float, nullable=True)   # AI-suggested threshold
    current_threshold = Column(Float, nullable=True)     # Current user threshold
    threshold_confidence = Column(Float, default=0.0)   # Confidence in suggestion
    
    # Pattern metadata
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    pattern_strength = Column(Float, default=0.0)       # How strong/reliable this pattern is
    
    # Relationships
    user = relationship("User", back_populates="behavior_patterns")
    
    def __repr__(self):
        return f"<BehaviorPattern(user_id={self.user_id}, pattern_type={self.pattern_type}, dismissal_rate={self.dismissal_rate})>"


class AlertFatigueMetric(Base):
    """Tracks alert fatigue metrics for users."""
    
    __tablename__ = "alert_fatigue_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Time period for metrics
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly
    
    # Alert metrics
    alerts_received = Column(Integer, default=0)
    alerts_dismissed = Column(Integer, default=0)
    alerts_acted_upon = Column(Integer, default=0)
    alerts_escalated = Column(Integer, default=0)
    
    # Fatigue indicators
    dismissal_rate = Column(Float, default=0.0)
    consecutive_dismissals = Column(Integer, default=0)
    time_to_first_action = Column(Float, nullable=True)  # Seconds
    engagement_score = Column(Float, default=1.0)        # 0-1, lower = more fatigued
    
    # Threshold suggestions
    suggested_threshold_adjustment = Column(Float, nullable=True)  # Suggested change
    threshold_adjustment_reason = Column(Text, nullable=True)
    adjustment_confidence = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    is_fatigue_detected = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="fatigue_metrics")
    
    def __repr__(self):
        return f"<AlertFatigueMetric(user_id={self.user_id}, dismissal_rate={self.dismissal_rate}, fatigue={self.is_fatigue_detected})>"


class LearningLoopState(Base):
    """Tracks the overall learning loop state for users."""
    
    __tablename__ = "learning_loop_states"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Learning progress
    total_actions_recorded = Column(Integer, default=0)
    patterns_identified = Column(Integer, default=0)
    threshold_adjustments_made = Column(Integer, default=0)
    
    # Current state
    learning_phase = Column(String(50), default="initialization")  # initialization, learning, optimizing
    confidence_level = Column(Float, default=0.0)  # Overall confidence in learned patterns
    
    # Adaptation settings
    auto_threshold_adjustment = Column(Boolean, default=False)
    requires_user_approval = Column(Boolean, default=True)
    
    # Performance tracking
    accuracy_improvement = Column(Float, default=0.0)  # Measured improvement in relevance
    user_satisfaction_score = Column(Float, nullable=True)  # User-reported satisfaction
    
    # Metadata
    last_pattern_update = Column(DateTime, nullable=True)
    last_threshold_adjustment = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="learning_state")
    
    def __repr__(self):
        return f"<LearningLoopState(user_id={self.user_id}, phase={self.learning_phase}, confidence={self.confidence_level})>"