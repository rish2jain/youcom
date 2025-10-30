"""
Obsidian Knowledge Management Integration Database Models
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ObsidianIntegration(Base):
    """Obsidian knowledge management integration configuration"""
    __tablename__ = "obsidian_integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Obsidian vault configuration
    vault_name = Column(String(255), nullable=False)
    vault_path = Column(String(500), nullable=False)
    vault_id = Column(String(100))  # Obsidian vault identifier if available
    
    # API configuration (for Obsidian REST API plugin or similar)
    api_endpoint = Column(String(500))  # Local REST API endpoint
    api_key_encrypted = Column(Text)  # Encrypted API key
    api_port = Column(Integer, default=27123)  # Default Obsidian REST API port
    
    # Sync configuration
    sync_enabled = Column(Boolean, default=True)
    auto_sync = Column(Boolean, default=True)  # Auto-sync on new intelligence
    sync_frequency_minutes = Column(Integer, default=15)  # Sync every 15 minutes
    
    # Note organization settings
    base_folder = Column(String(255), default="Competitive Intelligence")  # Base folder for CIA notes
    company_folder_template = Column(String(255), default="Companies/{company_name}")
    market_folder_template = Column(String(255), default="Market Analysis/{industry}")
    trend_folder_template = Column(String(255), default="Trends/{category}")
    
    # Template configuration
    note_templates = Column(JSON, default=dict)  # Custom note templates
    tag_hierarchy = Column(JSON, default=dict)  # Tag organization structure
    
    # Backlink configuration
    enable_backlinks = Column(Boolean, default=True)
    backlink_format = Column(String(50), default="wikilink")  # wikilink or markdown
    auto_create_index = Column(Boolean, default=True)  # Create index notes
    
    # Content preferences
    include_source_links = Column(Boolean, default=True)
    include_metadata = Column(Boolean, default=True)
    include_timestamps = Column(Boolean, default=True)
    markdown_style = Column(String(50), default="standard")  # standard, obsidian, github
    
    # Sync status and health
    last_sync_at = Column(DateTime)
    last_successful_sync_at = Column(DateTime)
    sync_status = Column(String(50), default="active")  # active, error, paused, disconnected
    last_error_message = Column(Text)
    consecutive_failures = Column(Integer, default=0)
    
    # Usage statistics
    total_notes_created = Column(Integer, default=0)
    total_notes_updated = Column(Integer, default=0)
    total_backlinks_created = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sync_logs = relationship("ObsidianSyncLog", back_populates="integration", cascade="all, delete-orphan")
    note_mappings = relationship("ObsidianNoteMapping", back_populates="integration", cascade="all, delete-orphan")
    note_templates = relationship("ObsidianNoteTemplate", back_populates="integration", cascade="all, delete-orphan")


class ObsidianSyncLog(Base):
    """Log of Obsidian synchronization activities"""
    __tablename__ = "obsidian_sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("obsidian_integrations.id"), nullable=False)
    
    # Sync details
    sync_type = Column(String(50), nullable=False)  # full_sync, incremental_sync, manual_sync, single_note
    operation = Column(String(20), nullable=False)  # create, update, delete, export
    
    # Content details
    content_type = Column(String(50))  # impact_card, company_profile, market_analysis, trend_report
    content_id = Column(String(100))  # ID of the source content
    note_path = Column(String(500))  # Path to the note in Obsidian vault
    
    # Results
    status = Column(String(20), nullable=False)  # success, partial_success, failure
    notes_processed = Column(Integer, default=0)
    notes_created = Column(Integer, default=0)
    notes_updated = Column(Integer, default=0)
    backlinks_created = Column(Integer, default=0)
    
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
    integration = relationship("ObsidianIntegration", back_populates="sync_logs")


class ObsidianNoteMapping(Base):
    """Track mapping between CIA content and Obsidian notes"""
    __tablename__ = "obsidian_note_mappings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("obsidian_integrations.id"), nullable=False)
    
    # CIA content details
    content_type = Column(String(50), nullable=False)  # impact_card, company_profile, market_analysis
    content_id = Column(String(100), nullable=False)  # ID of the source content
    content_title = Column(String(500))
    
    # Obsidian note details
    note_path = Column(String(500), nullable=False)  # Full path to note in vault
    note_filename = Column(String(255), nullable=False)
    note_folder = Column(String(500))
    
    # Note metadata
    obsidian_note_id = Column(String(100))  # Obsidian internal note ID if available
    note_hash = Column(String(64))  # Hash of note content for change detection
    
    # Sync tracking
    created_in_obsidian_at = Column(DateTime, nullable=False)
    last_updated_in_obsidian_at = Column(DateTime)
    last_synced_at = Column(DateTime)
    sync_version = Column(Integer, default=1)
    
    # Status
    is_active = Column(Boolean, default=True)
    needs_update = Column(Boolean, default=False)
    
    # Backlink tracking
    backlinks_to = Column(JSON, default=list)  # List of notes this note links to
    backlinks_from = Column(JSON, default=list)  # List of notes that link to this note
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integration = relationship("ObsidianIntegration", back_populates="note_mappings")


class ObsidianNoteTemplate(Base):
    """Custom note templates for different types of competitive intelligence"""
    __tablename__ = "obsidian_note_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("obsidian_integrations.id"), nullable=False)
    
    # Template details
    template_name = Column(String(255), nullable=False)
    template_type = Column(String(50), nullable=False)  # company_profile, market_analysis, trend_report, impact_card
    description = Column(Text)
    
    # Template content
    template_content = Column(Text, nullable=False)  # Markdown template with placeholders
    frontmatter_template = Column(Text)  # YAML frontmatter template
    
    # Template configuration
    variables = Column(JSON, default=list)  # List of template variables
    required_fields = Column(JSON, default=list)  # Required fields for template
    default_tags = Column(JSON, default=list)  # Default tags to apply
    
    # Usage settings
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    integration = relationship("ObsidianIntegration", back_populates="note_templates")