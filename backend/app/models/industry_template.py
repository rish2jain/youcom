"""Industry template models for the Advanced Intelligence Suite."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from ..database import Base


class IndustryTemplate(Base):
    """Industry-specific template for competitive intelligence configuration."""
    
    __tablename__ = "industry_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    industry_sector = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    template_config = Column(JSON, nullable=False)  # Complete template configuration
    default_competitors = Column(JSON)  # List of default competitor names
    default_keywords = Column(JSON)  # List of default monitoring keywords
    risk_categories = Column(JSON)  # Industry-specific risk categories
    kpi_metrics = Column(JSON)  # Key performance indicators for the industry
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    usage_count = Column(Integer, default=0)  # Number of times template has been applied
    rating = Column(Float, default=0.0)  # Average user rating (0.0-5.0)
    is_active = Column(Boolean, default=True)  # Whether template is available for use
    created_by = Column(String(255))  # User ID who created the template
    
    # Relationships
    applications = relationship("TemplateApplication", back_populates="template")

    def __repr__(self):
        return f"<IndustryTemplate(id={self.id}, name='{self.name}', sector='{self.industry_sector}')>"


class TemplateApplication(Base):
    """Record of template application to a workspace."""
    
    __tablename__ = "template_applications"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("industry_templates.id"), nullable=False, index=True)
    workspace_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    customizations = Column(JSON)  # User-specific customizations to the template
    applied_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    status = Column(String(50), default="active", index=True)  # active, modified, archived
    rating = Column(Float)  # User rating for this template application (0.0-5.0)
    feedback = Column(Text)  # User feedback on template effectiveness
    
    # Relationships
    template = relationship("IndustryTemplate", back_populates="applications")

    def __repr__(self):
        return f"<TemplateApplication(id={self.id}, template_id={self.template_id}, workspace_id='{self.workspace_id}')>"