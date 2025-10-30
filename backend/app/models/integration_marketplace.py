"""
Integration Marketplace Models

Models for third-party integrations, developer ecosystem,
and revenue sharing marketplace.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, func
from sqlalchemy.orm import relationship

from app.database import Base


class IntegrationStatus(str, Enum):
    """Status of integrations"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    SUSPENDED = "suspended"


class IntegrationCategory(str, Enum):
    """Categories of integrations"""
    PRODUCTIVITY = "productivity"
    CRM = "crm"
    ANALYTICS = "analytics"
    COMMUNICATION = "communication"
    PROJECT_MANAGEMENT = "project_management"
    STORAGE = "storage"
    SECURITY = "security"
    MARKETING = "marketing"
    FINANCE = "finance"
    CUSTOM = "custom"


class PricingModel(str, Enum):
    """Pricing models for integrations"""
    FREE = "free"
    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    USAGE_BASED = "usage_based"
    REVENUE_SHARE = "revenue_share"


class DeveloperTier(str, Enum):
    """Developer tiers in the marketplace"""
    INDIVIDUAL = "individual"
    STARTUP = "startup"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    PARTNER = "partner"


class IntegrationDeveloper(Base):
    """Developers who create integrations"""
    __tablename__ = "integration_developers"

    id = Column(Integer, primary_key=True, index=True)
    
    # Developer Information
    developer_name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    website = Column(String, nullable=True)
    
    # Developer Profile
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    github_username = Column(String, nullable=True)
    linkedin_profile = Column(String, nullable=True)
    
    # Developer Tier and Status
    tier = Column(String, default=DeveloperTier.INDIVIDUAL)
    verified = Column(Boolean, default=False)
    verification_date = Column(DateTime, nullable=True)
    
    # Revenue Sharing
    revenue_share_percentage = Column(Float, default=70.0)  # Developer gets 70%
    total_earnings = Column(Float, default=0.0)
    payout_method = Column(String, default="stripe")
    payout_details = Column(JSON, default=dict)
    
    # Developer Metrics
    total_integrations = Column(Integer, default=0)
    published_integrations = Column(Integer, default=0)
    total_installs = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    
    # API Access
    api_key = Column(String, unique=True, nullable=True)
    api_quota_per_month = Column(Integer, default=10000)
    api_calls_used = Column(Integer, default=0)
    
    # Status
    status = Column(String, default="active")  # active, suspended, banned
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    integrations = relationship("Integration", back_populates="developer")


class Integration(Base):
    """Third-party integrations in the marketplace"""
    __tablename__ = "marketplace_integrations"

    id = Column(Integer, primary_key=True, index=True)
    developer_id = Column(Integer, ForeignKey("integration_developers.id"), index=True)
    
    # Integration Details
    name = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    short_description = Column(String, nullable=False)
    
    # Categorization
    category = Column(String, nullable=False, index=True)  # IntegrationCategory enum
    tags = Column(JSON, default=list)  # Searchable tags
    
    # Integration Metadata
    version = Column(String, default="1.0.0")
    changelog = Column(JSON, default=list)  # Version history
    
    # Visual Assets
    icon_url = Column(String, nullable=True)
    banner_url = Column(String, nullable=True)
    screenshots = Column(JSON, default=list)  # Screenshot URLs
    
    # Technical Details
    webhook_url = Column(String, nullable=True)
    api_endpoints = Column(JSON, default=dict)  # API configuration
    configuration_schema = Column(JSON, default=dict)  # Config requirements
    supported_events = Column(JSON, default=list)  # Events this integration handles
    
    # Requirements and Compatibility
    minimum_plan = Column(String, default="starter")  # Minimum CIA plan required
    supported_regions = Column(JSON, default=list)  # Geographic restrictions
    dependencies = Column(JSON, default=list)  # Other integrations required
    
    # Pricing
    pricing_model = Column(String, default=PricingModel.FREE)
    price = Column(Float, default=0.0)
    trial_days = Column(Integer, default=0)
    
    # Status and Approval
    status = Column(String, default=IntegrationStatus.DRAFT, index=True)
    review_notes = Column(Text, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    
    # Usage Metrics
    total_installs = Column(Integer, default=0)
    active_installs = Column(Integer, default=0)
    total_revenue = Column(Float, default=0.0)
    
    # Quality Metrics
    average_rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    # SEO and Discovery
    featured = Column(Boolean, default=False)
    trending_score = Column(Float, default=0.0)
    search_keywords = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    developer = relationship("IntegrationDeveloper", back_populates="integrations")
    installations = relationship("IntegrationInstallation", back_populates="integration")
    reviews = relationship("IntegrationReview", back_populates="integration")


class IntegrationInstallation(Base):
    """User installations of integrations"""
    __tablename__ = "marketplace_integration_installations"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("marketplace_integrations.id"), index=True)
    user_id = Column(String, index=True)  # CIA platform user ID
    workspace_id = Column(String, nullable=True, index=True)  # For enterprise workspaces
    
    # Installation Details
    configuration = Column(JSON, default=dict)  # User-specific configuration
    enabled = Column(Boolean, default=True)
    
    # Usage Tracking
    last_used = Column(DateTime, nullable=True)
    total_api_calls = Column(Integer, default=0)
    total_events_processed = Column(Integer, default=0)
    
    # Billing
    subscription_id = Column(String, nullable=True)  # Stripe subscription ID
    billing_status = Column(String, default="active")  # active, cancelled, past_due
    next_billing_date = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String, default="active")  # active, disabled, error
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    installed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integration = relationship("Integration", back_populates="installations")


class IntegrationReview(Base):
    """User reviews and ratings for integrations"""
    __tablename__ = "marketplace_integration_reviews"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("marketplace_integrations.id"), index=True)
    user_id = Column(String, index=True)
    
    # Review Content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String, nullable=True)
    review_text = Column(Text, nullable=True)
    
    # Review Metadata
    verified_purchase = Column(Boolean, default=False)
    helpful_votes = Column(Integer, default=0)
    total_votes = Column(Integer, default=0)
    
    # Developer Response
    developer_response = Column(Text, nullable=True)
    developer_response_date = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String, default="published")  # published, hidden, flagged
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integration = relationship("Integration", back_populates="reviews")


class IntegrationWebhook(Base):
    """Webhook events for integrations"""
    __tablename__ = "marketplace_integration_webhooks"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("marketplace_integrations.id"), index=True)
    installation_id = Column(Integer, ForeignKey("marketplace_integration_installations.id"), index=True)
    
    # Event Details
    event_type = Column(String, nullable=False, index=True)
    event_data = Column(JSON, default=dict)
    
    # Processing Status
    status = Column(String, default="pending")  # pending, processing, completed, failed
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Response Details
    response_status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timing
    scheduled_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntegrationAnalytics(Base):
    """Analytics data for integrations"""
    __tablename__ = "marketplace_integration_analytics"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("marketplace_integrations.id"), index=True)
    
    # Time Period
    date = Column(DateTime, nullable=False, index=True)
    
    # Usage Metrics
    daily_active_users = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)
    events_processed = Column(Integer, default=0)
    
    # Installation Metrics
    new_installs = Column(Integer, default=0)
    uninstalls = Column(Integer, default=0)
    active_installs = Column(Integer, default=0)
    
    # Revenue Metrics
    revenue = Column(Float, default=0.0)
    new_subscriptions = Column(Integer, default=0)
    cancelled_subscriptions = Column(Integer, default=0)
    
    # Performance Metrics
    average_response_time_ms = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)
    success_rate = Column(Float, default=0.0)
    
    # Engagement Metrics
    feature_usage = Column(JSON, default=dict)  # Usage per feature
    user_retention_rate = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntegrationPayout(Base):
    """Revenue payouts to developers"""
    __tablename__ = "integration_payouts"

    id = Column(Integer, primary_key=True, index=True)
    developer_id = Column(Integer, ForeignKey("integration_developers.id"), index=True)
    
    # Payout Details
    payout_period_start = Column(DateTime, nullable=False)
    payout_period_end = Column(DateTime, nullable=False)
    
    # Revenue Breakdown
    gross_revenue = Column(Float, nullable=False)
    platform_fee = Column(Float, nullable=False)
    net_payout = Column(Float, nullable=False)
    
    # Integration Breakdown
    integration_revenues = Column(JSON, default=dict)  # Revenue per integration
    
    # Payout Processing
    payout_method = Column(String, nullable=False)  # stripe, paypal, bank_transfer
    payout_reference = Column(String, nullable=True)  # External reference ID
    
    # Status
    status = Column(String, default="pending")  # pending, processing, completed, failed
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntegrationSupport(Base):
    """Support tickets for integrations"""
    __tablename__ = "marketplace_integration_support"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("marketplace_integrations.id"), index=True)
    user_id = Column(String, index=True)
    
    # Ticket Details
    ticket_number = Column(String, unique=True, nullable=False)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    # Classification
    category = Column(String, nullable=False)  # bug, feature_request, question, billing
    priority = Column(String, default="medium")  # low, medium, high, urgent
    
    # Status
    status = Column(String, default="open")  # open, in_progress, resolved, closed
    assigned_to = Column(String, nullable=True)  # Developer or support agent
    
    # Resolution
    resolution = Column(Text, nullable=True)
    resolution_time_hours = Column(Float, nullable=True)
    
    # Communication
    last_response_by = Column(String, nullable=True)  # user, developer, support
    last_response_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class MarketplaceSettings(Base):
    """Global marketplace settings and configuration"""
    __tablename__ = "marketplace_settings"

    id = Column(Integer, primary_key=True, index=True)
    
    # Revenue Sharing
    default_revenue_share = Column(Float, default=70.0)  # Default developer share
    platform_fee_percentage = Column(Float, default=30.0)  # Platform fee
    
    # Review and Approval
    auto_approve_updates = Column(Boolean, default=False)
    review_required_for_new = Column(Boolean, default=True)
    minimum_rating_for_featured = Column(Float, default=4.0)
    
    # Developer Limits
    max_integrations_per_developer = Column(Integer, default=10)
    api_rate_limit_per_minute = Column(Integer, default=100)
    
    # Marketplace Features
    featured_integrations_count = Column(Integer, default=6)
    trending_calculation_days = Column(Integer, default=7)
    
    # Payout Settings
    minimum_payout_amount = Column(Float, default=50.0)
    payout_frequency_days = Column(Integer, default=30)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)