"""
Explainability Engine data models for transparent AI reasoning
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ReasoningStep(Base):
    """Individual step in the reasoning chain for risk score calculation"""
    __tablename__ = "reasoning_steps"

    id = Column(Integer, primary_key=True, index=True)
    impact_card_id = Column(Integer, ForeignKey("impact_cards.id"), nullable=False, index=True)
    
    # Step identification
    step_order = Column(Integer, nullable=False)  # Order in the reasoning chain
    step_type = Column(String(50), nullable=False)  # factor_analysis, source_evaluation, risk_calculation, etc.
    step_name = Column(String(255), nullable=False)  # Human-readable step name
    
    # Factor contribution
    factor_name = Column(String(255), nullable=False)  # e.g., "Product Launch Impact", "Market Share Threat"
    factor_weight = Column(Float, nullable=False)  # 0.0 to 1.0 importance weight
    factor_contribution = Column(Float, nullable=False)  # Contribution to final risk score
    
    # Evidence and reasoning
    evidence_sources = Column(JSON, default=lambda: [])  # List of source URLs/titles that support this factor
    reasoning_text = Column(Text, nullable=False)  # Detailed explanation of this reasoning step
    confidence_level = Column(Float, nullable=False)  # 0.0 to 1.0 confidence in this step
    
    # Uncertainty indicators
    uncertainty_flags = Column(JSON, default=lambda: [])  # List of uncertainty indicators
    conflicting_evidence = Column(JSON, default=lambda: [])  # Evidence that contradicts this factor
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    impact_card = relationship("ImpactCard", back_populates="reasoning_steps")
    
    def __repr__(self):
        return f"<ReasoningStep(id={self.id}, factor='{self.factor_name}', weight={self.factor_weight})>"

class SourceCredibilityAnalysis(Base):
    """Detailed analysis of source quality and credibility for each impact card"""
    __tablename__ = "source_credibility_analysis"

    id = Column(Integer, primary_key=True, index=True)
    impact_card_id = Column(Integer, ForeignKey("impact_cards.id"), nullable=False, index=True)
    
    # Source identification
    source_url = Column(String(2048), nullable=False)
    source_title = Column(String(512), nullable=True)
    source_type = Column(String(50), nullable=False)  # news, search, research
    
    # Credibility scoring
    tier_level = Column(String(20), nullable=False)  # tier1, tier2, tier3
    credibility_score = Column(Float, nullable=False)  # 0.0 to 1.0
    authority_score = Column(Float, nullable=False)  # Domain authority
    recency_score = Column(Float, nullable=False)  # How recent the source is
    relevance_score = Column(Float, nullable=False)  # Relevance to the analysis
    
    # Quality indicators
    validation_method = Column(String(100), nullable=False)  # How credibility was determined
    quality_flags = Column(JSON, default=lambda: [])  # Quality indicators (verified, authoritative, etc.)
    warning_flags = Column(JSON, default=lambda: [])  # Warning indicators (outdated, unverified, etc.)
    
    # Conflict detection
    conflicts_with = Column(JSON, default=lambda: [])  # IDs of other sources this conflicts with
    conflict_severity = Column(String(20), default="none")  # none, minor, major, critical
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    impact_card = relationship("ImpactCard", back_populates="source_analyses")
    
    def __repr__(self):
        return f"<SourceCredibilityAnalysis(id={self.id}, url='{self.source_url[:50]}...', tier='{self.tier_level}')>"

class UncertaintyDetection(Base):
    """Detection and tracking of uncertainty in AI analysis"""
    __tablename__ = "uncertainty_detections"

    id = Column(Integer, primary_key=True, index=True)
    impact_card_id = Column(Integer, ForeignKey("impact_cards.id"), nullable=False, index=True)
    
    # Uncertainty identification
    uncertainty_type = Column(String(50), nullable=False)  # data_quality, conflicting_evidence, low_confidence, etc.
    uncertainty_level = Column(String(20), nullable=False)  # low, medium, high, critical
    confidence_threshold = Column(Float, nullable=False)  # Threshold that triggered this detection
    
    # Detection details
    affected_components = Column(JSON, default=lambda: [])  # Which parts of analysis are affected
    uncertainty_description = Column(Text, nullable=False)  # Human-readable description
    
    # Recommendations
    human_validation_required = Column(Boolean, default=False)
    recommended_actions = Column(JSON, default=lambda: [])  # Recommended actions to resolve uncertainty
    validation_priority = Column(String(20), default="medium")  # low, medium, high, urgent
    
    # Resolution tracking
    is_resolved = Column(Boolean, default=False)
    resolution_method = Column(String(100), nullable=True)  # How uncertainty was resolved
    resolved_by = Column(String(100), nullable=True)  # Who resolved it
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    impact_card = relationship("ImpactCard", back_populates="uncertainty_detections")
    
    def __repr__(self):
        return f"<UncertaintyDetection(id={self.id}, type='{self.uncertainty_type}', level='{self.uncertainty_level}')>"