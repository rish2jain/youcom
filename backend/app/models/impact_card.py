from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ImpactCard(Base):
    __tablename__ = "impact_cards"

    id = Column(Integer, primary_key=True, index=True)
    watch_item_id = Column(Integer, ForeignKey("watch_items.id"), nullable=True, index=True)
    competitor_name = Column(String(255), nullable=False, index=True)
    
    # Core metrics
    risk_score = Column(Integer, nullable=False, index=True)  # 0-100
    risk_level = Column(String(50), nullable=False)  # low, medium, high, critical
    confidence_score = Column(Integer, nullable=False)  # 0-100
    credibility_score = Column(Float, default=0.0)
    requires_review = Column(Boolean, default=False, nullable=False, index=True)

    # Analysis data
    impact_areas = Column(JSON, default=list)  # List of impact area objects
    key_insights = Column(JSON, default=list)  # List of insights
    recommended_actions = Column(JSON, default=list)  # List of action objects
    next_steps_plan = Column(JSON, default=list)  # Ranked action plan with enrichment
    explainability = Column(JSON, default=dict)

    # Source information
    total_sources = Column(Integer, default=0)
    source_breakdown = Column(JSON, default=dict)  # Breakdown by API type
    source_quality = Column(JSON, default=dict)

    # API usage tracking
    api_usage = Column(JSON, default=dict)  # Track You.com API calls
    processing_time = Column(String(100), nullable=True)
    
    # Raw data from You.com APIs
    raw_data = Column(JSON, default=dict)  # Complete API responses
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    watch_item = relationship("WatchItem", backref="impact_cards")
    timeline_entries = relationship("InsightTimeline", back_populates="impact_card", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="impact_card", cascade="all, delete-orphan")
    action_recommendations = relationship("ActionRecommendation", back_populates="impact_card", cascade="all, delete-orphan")
    reasoning_steps = relationship("ReasoningStep", back_populates="impact_card", cascade="all, delete-orphan")
    source_analyses = relationship("SourceCredibilityAnalysis", back_populates="impact_card", cascade="all, delete-orphan")
    uncertainty_detections = relationship("UncertaintyDetection", back_populates="impact_card", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ImpactCard(id={self.id}, competitor='{self.competitor_name}', risk_score={self.risk_score})>"
