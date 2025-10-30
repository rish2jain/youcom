"""
HubSpot CRM Integration Database Models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class HubSpotIntegration(Base):
    """HubSpot CRM integration configuration"""
    __tablename__ = "hubspot_integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    
    # HubSpot account information
    hubspot_portal_id = Column(String(50), nullable=False)
    hubspot_account_name = Column(String(255))
    
    # OAuth 2.0 credentials (encrypted)
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text)
    token_expires_at = Column(DateTime)
    
    # Integration configuration
    sync_enabled = Column(Boolean, default=True)
    sync_frequency_minutes = Column(Integer, default=5)  # Sync every 5 minutes
    
    # Custom properties created in HubSpot
    custom_properties_created = Column(JSON, default=list)
    
    # Workflow mappings
    workflow_mappings = Column(JSON, default=dict)
    
    # Sync status and health
    last_sync_at = Column(DateTime)
    last_successful_sync_at = Column(DateTime)
    sync_status = Column(String(50), default="active")  # active, error, paused
    last_error_message = Column(Text)
    consecutive_failures = Column(Integer, default=0)
    
    # Usage statistics
    total_contacts_synced = Column(Integer, default=0)
    total_companies_synced = Column(Integer, default=0)
    total_workflows_triggered = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sync_logs = relationship("HubSpotSyncLog", back_populates="integration", cascade="all, delete-orphan")


class HubSpotSyncLog(Base):
    """Log of HubSpot synchronization activities"""
    __tablename__ = "hubspot_sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("hubspot_integrations.id"), nullable=False)
    
    # Sync details
    sync_type = Column(String(50), nullable=False)  # full_sync, incremental_sync, manual_sync
    direction = Column(String(20), nullable=False)  # to_hubspot, from_hubspot, bidirectional
    
    # Results
    status = Column(String(20), nullable=False)  # success, partial_success, failure
    records_processed = Column(Integer, default=0)
    records_successful = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Error details
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Metadata
    sync_metadata = Column(JSON, default=dict)
    
    # Relationships
    integration = relationship("HubSpotIntegration", back_populates="sync_logs")


class HubSpotCustomProperty(Base):
    """Track custom properties created in HubSpot for competitive intelligence"""
    __tablename__ = "hubspot_custom_properties"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("hubspot_integrations.id"), nullable=False)
    
    # HubSpot property details
    hubspot_property_name = Column(String(255), nullable=False)
    hubspot_property_type = Column(String(50), nullable=False)  # string, number, enumeration, etc.
    hubspot_object_type = Column(String(50), nullable=False)  # contact, company, deal, etc.
    
    # CIA mapping
    cia_field_name = Column(String(255), nullable=False)
    cia_field_type = Column(String(50), nullable=False)
    
    # Property configuration
    property_label = Column(String(255))
    property_description = Column(Text)
    property_options = Column(JSON)  # For enumeration properties
    
    # Status
    is_active = Column(Boolean, default=True)
    created_in_hubspot_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HubSpotWorkflowTrigger(Base):
    """Track workflow triggers sent to HubSpot"""
    __tablename__ = "hubspot_workflow_triggers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("hubspot_integrations.id"), nullable=False)
    
    # Trigger details
    workflow_id = Column(String(50), nullable=False)
    workflow_name = Column(String(255))
    trigger_type = Column(String(100), nullable=False)  # competitive_event, risk_score_change, etc.
    
    # HubSpot object details
    hubspot_object_type = Column(String(50), nullable=False)  # contact, company, deal
    hubspot_object_id = Column(String(50), nullable=False)
    
    # CIA context
    impact_card_id = Column(UUID(as_uuid=True), ForeignKey("impact_cards.id"))
    competitive_event_type = Column(String(100))
    risk_score = Column(Integer)
    
    # Execution details
    status = Column(String(20), default="pending")  # pending, sent, success, failed
    sent_at = Column(DateTime)
    response_status_code = Column(Integer)
    response_message = Column(Text)
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)