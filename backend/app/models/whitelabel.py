"""
White-label Solutions Models

Models for custom branding, on-premise deployment,
and enterprise white-label configurations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship

from app.database import Base


class DeploymentType(str, Enum):
    """Types of deployment configurations"""
    CLOUD_HOSTED = "cloud_hosted"
    ON_PREMISE = "on_premise"
    HYBRID = "hybrid"
    AIR_GAPPED = "air_gapped"


class BrandingStatus(str, Enum):
    """Status of branding configuration"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class DeploymentStatus(str, Enum):
    """Status of deployment"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DEPLOYED = "deployed"
    FAILED = "failed"
    MAINTENANCE = "maintenance"
    TERMINATED = "terminated"


class WhiteLabelCustomer(Base):
    """White-label customer configuration"""
    __tablename__ = "whitelabel_customers"

    id = Column(Integer, primary_key=True, index=True)
    
    # Customer Information
    customer_name = Column(String, nullable=False)
    customer_domain = Column(String, unique=True, nullable=False)
    contact_email = Column(String, nullable=False)
    contact_name = Column(String, nullable=False)
    
    # Subscription Details
    subscription_tier = Column(String, default="enterprise")  # enterprise, premium, custom
    monthly_fee = Column(Float, nullable=False)
    setup_fee = Column(Float, default=0.0)
    contract_start_date = Column(DateTime, nullable=False)
    contract_end_date = Column(DateTime, nullable=False)
    
    # Configuration
    deployment_type = Column(String, default=DeploymentType.CLOUD_HOSTED)
    max_users = Column(Integer, default=100)
    max_api_calls_per_month = Column(Integer, default=10000)
    
    # Features Enabled
    features_enabled = Column(JSON, default=lambda: {})  # Feature flags
    integrations_enabled = Column(JSON, default=lambda: [])  # Enabled integrations
    
    # Support Configuration
    support_level = Column(String, default="standard")  # basic, standard, premium, dedicated
    dedicated_support_contact = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="active")  # active, suspended, terminated
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branding_configs = relationship("BrandingConfiguration", back_populates="customer")
    deployments = relationship("DeploymentConfiguration", back_populates="customer")


class BrandingConfiguration(Base):
    """Custom branding configuration for white-label customers"""
    __tablename__ = "branding_configurations"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("whitelabel_customers.id"), index=True)
    
    # Branding Details
    brand_name = Column(String, nullable=False)
    brand_tagline = Column(String, nullable=True)
    
    # Visual Identity
    primary_color = Column(String, default="#1f2937")  # Hex color
    secondary_color = Column(String, default="#3b82f6")  # Hex color
    accent_color = Column(String, default="#10b981")  # Hex color
    background_color = Column(String, default="#ffffff")  # Hex color
    text_color = Column(String, default="#111827")  # Hex color
    
    # Logo Configuration
    logo_url = Column(String, nullable=True)
    logo_dark_url = Column(String, nullable=True)  # Dark mode logo
    favicon_url = Column(String, nullable=True)
    
    # Typography
    primary_font = Column(String, default="Inter")
    secondary_font = Column(String, default="Inter")
    
    # Custom CSS
    custom_css = Column(Text, nullable=True)
    
    # Domain Configuration
    custom_domain = Column(String, unique=True, nullable=True)
    ssl_certificate_path = Column(String, nullable=True)
    
    # Email Branding
    email_header_logo = Column(String, nullable=True)
    email_footer_text = Column(Text, nullable=True)
    email_signature = Column(Text, nullable=True)
    
    # PDF Report Branding
    pdf_header_logo = Column(String, nullable=True)
    pdf_footer_text = Column(Text, nullable=True)
    pdf_watermark = Column(String, nullable=True)
    
    # Mobile App Branding
    mobile_app_icon = Column(String, nullable=True)
    mobile_splash_screen = Column(String, nullable=True)
    
    # Status and Metadata
    status = Column(String, default=BrandingStatus.DRAFT)
    version = Column(String, default="1.0")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = Column(DateTime, nullable=True)
    
    # Relationships
    customer = relationship("WhiteLabelCustomer", back_populates="branding_configs")


class DeploymentConfiguration(Base):
    """On-premise and custom deployment configuration"""
    __tablename__ = "deployment_configurations"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("whitelabel_customers.id"), index=True)
    
    # Deployment Details
    deployment_name = Column(String, nullable=False)
    deployment_type = Column(String, nullable=False)  # DeploymentType enum
    environment = Column(String, default="production")  # production, staging, development
    
    # Infrastructure Configuration
    server_specifications = Column(JSON, default=lambda: {})  # CPU, RAM, Storage requirements
    network_configuration = Column(JSON, default=lambda: {})  # Network settings, firewall rules
    security_configuration = Column(JSON, default=lambda: {})  # Security settings, encryption
    
    # Database Configuration
    database_type = Column(String, default="postgresql")
    database_configuration = Column(JSON, default=lambda: {})
    backup_configuration = Column(JSON, default=lambda: {})
    
    # Application Configuration
    application_settings = Column(JSON, default=lambda: {})  # App-specific settings
    environment_variables = Column(JSON, default=lambda: {})  # Environment variables
    feature_flags = Column(JSON, default=lambda: {})  # Feature toggles
    
    # Docker Configuration
    docker_image_tag = Column(String, nullable=True)
    docker_compose_config = Column(Text, nullable=True)
    kubernetes_config = Column(Text, nullable=True)
    
    # Monitoring and Logging
    monitoring_enabled = Column(Boolean, default=True)
    logging_level = Column(String, default="INFO")
    metrics_retention_days = Column(Integer, default=30)
    
    # Backup and Recovery
    backup_enabled = Column(Boolean, default=True)
    backup_frequency = Column(String, default="daily")  # hourly, daily, weekly
    backup_retention_days = Column(Integer, default=30)
    disaster_recovery_enabled = Column(Boolean, default=False)
    
    # SSL/TLS Configuration
    ssl_enabled = Column(Boolean, default=True)
    ssl_certificate_path = Column(String, nullable=True)
    ssl_private_key_path = Column(String, nullable=True)
    
    # Status and Health
    deployment_status = Column(String, default=DeploymentStatus.PENDING)
    health_check_url = Column(String, nullable=True)
    last_health_check = Column(DateTime, nullable=True)
    uptime_percentage = Column(Float, default=0.0)
    
    # Deployment Metadata
    deployed_version = Column(String, nullable=True)
    deployment_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deployed_at = Column(DateTime, nullable=True)
    last_maintenance = Column(DateTime, nullable=True)
    
    # Relationships
    customer = relationship("WhiteLabelCustomer", back_populates="deployments")


class CustomIntegration(Base):
    """Custom integrations for white-label customers"""
    __tablename__ = "custom_integrations"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("whitelabel_customers.id"), index=True)
    
    # Integration Details
    integration_name = Column(String, nullable=False)
    integration_type = Column(String, nullable=False)  # api, webhook, sso, etc.
    description = Column(Text, nullable=True)
    
    # Configuration
    configuration = Column(JSON, default=lambda: {})  # Integration-specific config
    credentials = Column(JSON, default=lambda: {})  # Encrypted credentials
    endpoints = Column(JSON, default=lambda: {})  # API endpoints
    
    # Status
    enabled = Column(Boolean, default=False)
    status = Column(String, default="inactive")  # active, inactive, error
    last_sync = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Usage Metrics
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WhiteLabelUsage(Base):
    """Usage tracking for white-label customers"""
    __tablename__ = "whitelabel_usage"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("whitelabel_customers.id"), index=True)
    
    # Usage Period
    usage_month = Column(Integer, nullable=False)  # 1-12
    usage_year = Column(Integer, nullable=False)
    
    # Usage Metrics
    active_users = Column(Integer, default=0)
    total_api_calls = Column(Integer, default=0)
    storage_used_gb = Column(Float, default=0.0)
    bandwidth_used_gb = Column(Float, default=0.0)
    
    # Feature Usage
    feature_usage = Column(MutableDict.as_mutable(JSON), default=lambda: {})  # Usage per feature
    integration_usage = Column(MutableDict.as_mutable(JSON), default=lambda: {})  # Usage per integration
    
    # Performance Metrics
    average_response_time_ms = Column(Float, default=0.0)
    uptime_percentage = Column(Float, default=0.0)
    error_rate_percentage = Column(Float, default=0.0)
    
    # Billing Information
    base_fee = Column(Float, default=0.0)
    usage_fees = Column(Float, default=0.0)
    total_fee = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SupportTicket(Base):
    """Support tickets for white-label customers"""
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("whitelabel_customers.id"), index=True)
    
    # Ticket Details
    ticket_number = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    # Classification
    priority = Column(String, default="medium")  # low, medium, high, critical
    category = Column(String, nullable=False)  # technical, billing, feature_request, bug
    severity = Column(String, default="minor")  # minor, major, critical, blocker
    
    # Status
    status = Column(String, default="open")  # open, in_progress, resolved, closed
    assigned_to = Column(String, nullable=True)  # Support agent
    
    # Resolution
    resolution = Column(Text, nullable=True)
    resolution_time_hours = Column(Float, nullable=True)
    
    # Customer Information
    reporter_name = Column(String, nullable=False)
    reporter_email = Column(String, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)


class WhiteLabelAnalytics(Base):
    """Analytics and reporting for white-label customers"""
    __tablename__ = "whitelabel_analytics"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("whitelabel_customers.id"), index=True)
    
    # Analytics Period
    date = Column(DateTime, nullable=False, index=True)
    
    # User Analytics
    daily_active_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    user_retention_rate = Column(Float, default=0.0)
    
    # Usage Analytics
    api_calls = Column(Integer, default=0)
    page_views = Column(Integer, default=0)
    session_duration_minutes = Column(Float, default=0.0)
    
    # Feature Analytics
    feature_usage = Column(JSON, default=lambda: {})  # Usage per feature
    most_used_features = Column(JSON, default=lambda: [])  # Top features
    
    # Performance Analytics
    average_response_time = Column(Float, default=0.0)
    error_rate = Column(Float, default=0.0)
    uptime_percentage = Column(Float, default=0.0)
    
    # Business Analytics
    revenue_generated = Column(Float, default=0.0)
    cost_per_user = Column(Float, default=0.0)
    customer_satisfaction_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)