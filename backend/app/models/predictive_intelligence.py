"""Predictive Intelligence models for competitor pattern analysis and predictions."""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CompetitorPattern(Base):
    """Model for storing identified competitor behavior patterns."""
    
    __tablename__ = "competitor_patterns"

    id = Column(Integer, primary_key=True, index=True)
    competitor_name = Column(String(255), nullable=False, index=True)
    pattern_type = Column(String(100), nullable=False, index=True)  # e.g., "product_launch", "pricing_change", "partnership"
    
    # Pattern characteristics
    sequence = Column(JSON, nullable=False)  # List of pattern events in chronological order
    frequency = Column(Integer, default=1)  # How many times this pattern has been observed
    confidence = Column(Float, nullable=False)  # Pattern confidence score (0.0-1.0)
    
    # Timing analysis
    average_duration = Column(Integer, nullable=True)  # Average duration in days
    typical_intervals = Column(JSON, default=lambda: [])  # List of typical intervals between events
    
    # Pattern metadata
    first_observed = Column(DateTime(timezone=True), nullable=False)
    last_observed = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    
    # Analysis data
    contributing_factors = Column(JSON, default=lambda: [])  # Factors that trigger this pattern
    success_indicators = Column(JSON, default=lambda: [])  # Indicators of pattern success
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    predicted_events = relationship("PredictedEvent", back_populates="pattern", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CompetitorPattern(id={self.id}, competitor='{self.competitor_name}', type='{self.pattern_type}')>"


class PredictedEvent(Base):
    """Model for storing predicted competitor events based on patterns."""
    
    __tablename__ = "predicted_events"

    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(Integer, ForeignKey("competitor_patterns.id"), nullable=False, index=True)
    competitor_name = Column(String(255), nullable=False, index=True)
    
    # Prediction details
    event_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    probability = Column(Float, nullable=False)  # Probability score (0.0-1.0)
    confidence = Column(Float, nullable=False)  # Confidence in prediction (0.0-1.0)
    
    # Timeline estimation
    predicted_date = Column(DateTime(timezone=True), nullable=True)
    timeframe = Column(String(100), nullable=False)  # e.g., "1-2 weeks", "next quarter"
    earliest_date = Column(DateTime(timezone=True), nullable=True)
    latest_date = Column(DateTime(timezone=True), nullable=True)
    
    # Reasoning and context
    reasoning = Column(JSON, default=lambda: [])  # List of reasoning steps
    trigger_events = Column(JSON, default=lambda: [])  # Events that triggered this prediction
    supporting_evidence = Column(JSON, default=lambda: [])  # Supporting evidence from historical data
    
    # Validation tracking
    status = Column(String(50), default="pending", index=True)  # pending, validated, invalidated, expired
    actual_outcome = Column(Text, nullable=True)
    validation_date = Column(DateTime(timezone=True), nullable=True)
    accuracy_score = Column(Float, nullable=True)  # How accurate the prediction was (0.0-1.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationships
    pattern = relationship("CompetitorPattern", back_populates="predicted_events")
    
    def __repr__(self):
        return f"<PredictedEvent(id={self.id}, competitor='{self.competitor_name}', type='{self.event_type}')>"


class PatternEvent(Base):
    """Model for storing individual events that make up competitor patterns."""
    
    __tablename__ = "pattern_events"

    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(Integer, ForeignKey("competitor_patterns.id"), nullable=False, index=True)
    impact_card_id = Column(Integer, ForeignKey("impact_cards.id"), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Event characteristics
    risk_score = Column(Integer, nullable=True)  # Risk score from impact card
    impact_areas = Column(JSON, default=lambda: [])  # Areas of business impact
    key_metrics = Column(JSON, default=lambda: {})  # Relevant metrics extracted from the event
    
    # Source information
    sources = Column(JSON, default=lambda: [])  # Source information for this event
    confidence = Column(Float, nullable=True)  # Confidence in event data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    pattern = relationship("CompetitorPattern")
    impact_card = relationship("ImpactCard")
    
    def __repr__(self):
        return f"<PatternEvent(id={self.id}, type='{self.event_type}', date='{self.event_date}')>"