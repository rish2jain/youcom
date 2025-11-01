from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ActionRecommendation(Base):
    __tablename__ = "action_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    impact_card_id = Column(Integer, ForeignKey("impact_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Core recommendation data
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)  # immediate, short-term, strategic
    priority = Column(String(20), nullable=False, index=True)  # high, medium, low
    
    # Resource estimation
    timeline = Column(String(100), nullable=False)  # e.g., "1-2 weeks", "3-6 months"
    estimated_hours = Column(Integer, nullable=True)
    team_members_required = Column(Integer, nullable=True)
    budget_impact = Column(String(20), nullable=False)  # low, medium, high
    dependencies = Column(JSON, default=lambda: [])  # List of dependency strings
    
    # Scoring and confidence
    confidence_score = Column(Float, nullable=False)  # 0.0-1.0
    impact_score = Column(Float, nullable=False)  # 0.0-1.0
    effort_score = Column(Float, nullable=False)  # 0.0-1.0
    overall_score = Column(Float, nullable=False)  # Calculated composite score
    
    # Context and reasoning
    reasoning = Column(JSON, default=lambda: [])  # List of reasoning steps
    evidence_links = Column(JSON, default=lambda: [])  # Supporting evidence
    okr_alignment = Column(String(500), nullable=True)  # OKR goal alignment
    
    # Status tracking
    status = Column(String(20), default="pending", index=True)  # pending, approved, rejected, completed
    assigned_to = Column(String(255), nullable=True)
    owner_type = Column(String(50), nullable=True)  # team, individual, department
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    impact_card = relationship("ImpactCard", back_populates="action_recommendations")
    
    def __repr__(self):
        return f"<ActionRecommendation(id={self.id}, title='{self.title}', category='{self.category}')>"

class ResourceEstimate(Base):
    __tablename__ = "resource_estimates"

    id = Column(Integer, primary_key=True, index=True)
    action_recommendation_id = Column(Integer, ForeignKey("action_recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Time estimates
    time_required = Column(String(100), nullable=False)  # Human readable time estimate
    estimated_hours_min = Column(Integer, nullable=True)  # Minimum hours
    estimated_hours_max = Column(Integer, nullable=True)  # Maximum hours
    
    # Resource requirements
    team_members = Column(Integer, nullable=False, default=1)
    skill_requirements = Column(JSON, default=lambda: [])  # List of required skills
    budget_impact = Column(String(20), nullable=False)  # low, medium, high
    budget_estimate_min = Column(Float, nullable=True)  # Minimum budget estimate
    budget_estimate_max = Column(Float, nullable=True)  # Maximum budget estimate
    
    # Dependencies and constraints
    dependencies = Column(JSON, default=lambda: [])  # List of dependency objects
    constraints = Column(JSON, default=lambda: [])  # List of constraint objects
    risks = Column(JSON, default=lambda: [])  # List of risk factors
    
    # Confidence and validation
    confidence_level = Column(Float, nullable=False)  # 0.0-1.0
    estimation_method = Column(String(100), nullable=True)  # How estimate was derived
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    action_recommendation = relationship("ActionRecommendation", backref="resource_estimate")
    
    def __repr__(self):
        return f"<ResourceEstimate(id={self.id}, time_required='{self.time_required}', team_members={self.team_members})>"