"""
Pydantic schemas for Obsidian Integration API
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


# Base schemas
class ObsidianIntegrationBase(BaseModel):
    vault_name: str = Field(..., description="Name of the Obsidian vault")
    vault_path: str = Field(..., description="Path to the Obsidian vault directory")
    vault_id: Optional[str] = Field(None, description="Obsidian vault identifier")
    api_endpoint: Optional[str] = Field(None, description="Obsidian REST API endpoint")
    api_port: Optional[int] = Field(27123, description="Obsidian REST API port")
    sync_enabled: bool = Field(True, description="Whether sync is enabled")
    auto_sync: bool = Field(True, description="Whether to auto-sync on content changes")
    sync_frequency_minutes: int = Field(15, description="Sync frequency in minutes")
    base_folder: str = Field("Competitive Intelligence", description="Base folder for CIA notes")
    company_folder_template: str = Field("Companies/{company_name}", description="Template for company folders")
    market_folder_template: str = Field("Market Analysis/{industry}", description="Template for market analysis folders")
    trend_folder_template: str = Field("Trends/{category}", description="Template for trend report folders")
    enable_backlinks: bool = Field(True, description="Whether to create backlinks")
    backlink_format: str = Field("wikilink", description="Format for backlinks (wikilink or markdown)")
    auto_create_index: bool = Field(True, description="Whether to auto-create index notes")
    include_source_links: bool = Field(True, description="Whether to include source links")
    include_metadata: bool = Field(True, description="Whether to include metadata in notes")
    include_timestamps: bool = Field(True, description="Whether to include timestamps")
    markdown_style: str = Field("obsidian", description="Markdown style (obsidian, standard, github)")

    @validator('backlink_format')
    def validate_backlink_format(cls, v):
        if v not in ['wikilink', 'markdown']:
            raise ValueError('backlink_format must be either "wikilink" or "markdown"')
        return v

    @validator('markdown_style')
    def validate_markdown_style(cls, v):
        if v not in ['obsidian', 'standard', 'github']:
            raise ValueError('markdown_style must be one of "obsidian", "standard", "github"')
        return v


class ObsidianIntegrationCreate(ObsidianIntegrationBase):
    api_key: Optional[str] = Field(None, description="API key for Obsidian REST API")


class ObsidianIntegrationUpdate(BaseModel):
    vault_name: Optional[str] = None
    vault_path: Optional[str] = None
    vault_id: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_port: Optional[int] = None
    sync_enabled: Optional[bool] = None
    auto_sync: Optional[bool] = None
    sync_frequency_minutes: Optional[int] = None
    base_folder: Optional[str] = None
    company_folder_template: Optional[str] = None
    market_folder_template: Optional[str] = None
    trend_folder_template: Optional[str] = None
    enable_backlinks: Optional[bool] = None
    backlink_format: Optional[str] = None
    auto_create_index: Optional[bool] = None
    include_source_links: Optional[bool] = None
    include_metadata: Optional[bool] = None
    include_timestamps: Optional[bool] = None
    markdown_style: Optional[str] = None


class ObsidianIntegrationResponse(ObsidianIntegrationBase):
    id: str
    user_id: int
    sync_status: str
    last_sync_at: Optional[datetime] = None
    last_successful_sync_at: Optional[datetime] = None
    consecutive_failures: int = 0
    last_error_message: Optional[str] = None
    total_notes_created: int = 0
    total_notes_updated: int = 0
    total_backlinks_created: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Sync-related schemas
class ObsidianSyncRequest(BaseModel):
    sync_type: str = Field("incremental_sync", description="Type of sync (full_sync, incremental_sync, manual_sync)")
    async_sync: bool = Field(True, description="Whether to run sync asynchronously")

    @validator('sync_type')
    def validate_sync_type(cls, v):
        if v not in ['full_sync', 'incremental_sync', 'manual_sync']:
            raise ValueError('sync_type must be one of "full_sync", "incremental_sync", "manual_sync"')
        return v


class ObsidianSyncResponse(BaseModel):
    status: str = Field(..., description="Sync status (started, success, failure)")
    message: str = Field(..., description="Sync result message")
    sync_type: str = Field(..., description="Type of sync performed")
    sync_log_id: Optional[str] = Field(None, description="ID of the sync log entry")
    notes_processed: int = Field(0, description="Number of notes processed")
    notes_created: int = Field(0, description="Number of notes created")
    notes_updated: int = Field(0, description="Number of notes updated")
    backlinks_created: int = Field(0, description="Number of backlinks created")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    async_sync: bool = Field(..., description="Whether sync was run asynchronously")


class ObsidianSyncStatusResponse(BaseModel):
    integration_id: str
    sync_enabled: bool
    sync_status: str
    last_sync_at: Optional[str] = None
    last_successful_sync_at: Optional[str] = None
    consecutive_failures: int
    last_error_message: Optional[str] = None
    total_notes: int
    pending_updates: int
    usage_stats: Dict[str, int]
    recent_sync_logs: List[Dict[str, Any]]


# Health check schemas
class ObsidianHealthCheckResponse(BaseModel):
    integration_id: str
    overall_status: str = Field(..., description="Overall health status (healthy, unhealthy)")
    vault_accessible: bool = Field(..., description="Whether vault is accessible")
    api_accessible: bool = Field(..., description="Whether API is accessible")
    can_read: bool = Field(..., description="Whether vault can be read")
    can_write: bool = Field(..., description="Whether vault can be written to")
    errors: List[str] = Field(default_factory=list, description="List of health check errors")
    vault_info: Dict[str, Any] = Field(default_factory=dict, description="Vault information")
    checked_at: str = Field(..., description="Timestamp of health check")


# Template schemas
class ObsidianNoteTemplateBase(BaseModel):
    template_name: str = Field(..., description="Name of the template")
    template_type: str = Field(..., description="Type of template (company_profile, impact_card, etc.)")
    description: Optional[str] = Field(None, description="Template description")
    template_content: str = Field(..., description="Template content with placeholders")
    frontmatter_template: Optional[str] = Field(None, description="YAML frontmatter template")
    variables: List[str] = Field(default_factory=list, description="List of template variables")
    required_fields: List[str] = Field(default_factory=list, description="Required fields for template")
    default_tags: List[str] = Field(default_factory=list, description="Default tags to apply")
    is_default: bool = Field(False, description="Whether this is a default template")
    is_active: bool = Field(True, description="Whether template is active")

    @validator('template_type')
    def validate_template_type(cls, v):
        valid_types = ['company_profile', 'impact_card', 'market_analysis', 'trend_report']
        if v not in valid_types:
            raise ValueError(f'template_type must be one of {valid_types}')
        return v


class ObsidianNoteTemplateCreate(ObsidianNoteTemplateBase):
    pass


class ObsidianNoteTemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    description: Optional[str] = None
    template_content: Optional[str] = None
    frontmatter_template: Optional[str] = None
    variables: Optional[List[str]] = None
    required_fields: Optional[List[str]] = None
    default_tags: Optional[List[str]] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class ObsidianNoteTemplateResponse(ObsidianNoteTemplateBase):
    id: str
    integration_id: str
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Note mapping schemas
class ObsidianNoteMappingResponse(BaseModel):
    id: str
    integration_id: str
    content_type: str
    content_id: str
    content_title: Optional[str] = None
    note_path: str
    note_filename: str
    note_folder: Optional[str] = None
    obsidian_note_id: Optional[str] = None
    note_hash: Optional[str] = None
    created_in_obsidian_at: datetime
    last_updated_in_obsidian_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    sync_version: int = 1
    is_active: bool = True
    needs_update: bool = False
    backlinks_to: List[str] = Field(default_factory=list)
    backlinks_from: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Sync log schemas
class ObsidianSyncLogResponse(BaseModel):
    id: str
    integration_id: str
    sync_type: str
    operation: str
    content_type: Optional[str] = None
    content_id: Optional[str] = None
    note_path: Optional[str] = None
    status: str
    notes_processed: int = 0
    notes_created: int = 0
    notes_updated: int = 0
    backlinks_created: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    sync_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# Export request schemas
class ObsidianExportRequest(BaseModel):
    content_ids: List[str] = Field(..., description="List of content IDs to export")
    content_type: str = Field(..., description="Type of content to export")
    force_update: bool = Field(False, description="Whether to force update existing notes")

    @validator('content_type')
    def validate_content_type(cls, v):
        valid_types = ['impact_card', 'company_profile', 'market_analysis', 'trend_report']
        if v not in valid_types:
            raise ValueError(f'content_type must be one of {valid_types}')
        return v


class ObsidianExportResponse(BaseModel):
    status: str = Field(..., description="Export status")
    message: str = Field(..., description="Export result message")
    content_type: str = Field(..., description="Type of content exported")
    exported_count: int = Field(..., description="Number of items exported")
    notes_created: int = Field(0, description="Number of notes created")
    notes_updated: int = Field(0, description="Number of notes updated")
    backlinks_created: int = Field(0, description="Number of backlinks created")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")


# Vault information schemas
class ObsidianVaultInfoResponse(BaseModel):
    vault_path: str
    vault_name: str
    total_notes: int
    total_size: int
    api_available: bool
    config: Dict[str, Any] = Field(default_factory=dict)
    last_checked: str


# Search and filter schemas
class ObsidianNoteSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    content_type: Optional[str] = Field(None, description="Filter by content type")
    folder: Optional[str] = Field(None, description="Filter by folder")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    date_from: Optional[datetime] = Field(None, description="Filter by creation date from")
    date_to: Optional[datetime] = Field(None, description="Filter by creation date to")
    limit: int = Field(50, description="Maximum number of results")
    offset: int = Field(0, description="Offset for pagination")


class ObsidianNoteSearchResponse(BaseModel):
    total_count: int
    results: List[ObsidianNoteMappingResponse]
    query: Optional[str] = None
    filters_applied: Dict[str, Any] = Field(default_factory=dict)