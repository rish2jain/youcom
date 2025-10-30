"""
Integration Marketplace Database Models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base

class Integration(Base):
    """Integration marketplace entry"""
    __tablename__ = "integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    
    # Developer information
    developer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    developer_name = Column(String(255))
    developer_email = Column(String(255))
    
    # Integration details
    version = Column(String(50), default="1.0.0")
    webhook_url = Column(String(500))
    configuration_schema = Column(JSONB)
    required_permissions = Column(JSONB)
    
    # Marketplace metadata
    status = Column(String(50), default="draft")
    is_featured = Column(Boolean, default=False)
    install_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Revenue sharing
    revenue_share_percent = Column(Float, default=70.0)  # 70% to developer, 30% to platform
    monthly_revenue = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime)
    
    # Relationships
    installations = relationship("IntegrationInstallation", back_populates="integration")
    reviews = relationship("IntegrationReview", back_populates="integration")
    
    __table_args__ = (
        CheckConstraint("revenue_share_percent >= 0 AND revenue_share_percent <= 100", name="ck_integration_revenue_share_range"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_integration_rating_range"),
    )

class IntegrationInstallation(Base):
    """User integration installations"""
    __tablename__ = "integration_installations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"))
    
    # Configuration
    configuration = Column(JSONB)
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    last_used_at = Column(DateTime)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    installed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integration = relationship("Integration", back_populates="installations")

class IntegrationReview(Base):
    """Integration reviews and ratings"""
    __tablename__ = "integration_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255))
    comment = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integration = relationship("Integration", back_populates="reviews")
    
    __table_args__ = (
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_integration_review_rating_range"),
    )

class IntegrationUsageLog(Base):
    """Integration usage analytics"""
    __tablename__ = "integration_usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=False)
    installation_id = Column(UUID(as_uuid=True), ForeignKey("integration_installations.id"), nullable=False)
    
    # Usage details
    action = Column(String(100))  # e.g., "send_notification", "sync_data"
    success = Column(Boolean, default=True)
    latency_ms = Column(Integer)
    error_message = Column(Text)
    
    # Billing
    billable_units = Column(Integer, default=1)
    cost = Column(Float, default=0.0)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)