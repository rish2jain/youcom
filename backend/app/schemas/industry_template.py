"""Pydantic schemas for industry template system."""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TemplateStatus(str, Enum):
    """Status of a template application."""
    ACTIVE = "active"
    MODIFIED = "modified"
    ARCHIVED = "archived"


class IndustryTemplateCreate(BaseModel):
    """Schema for creating a new industry template."""
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    industry_sector: str = Field(..., min_length=1, max_length=100, description="Industry sector")
    description: str = Field("", max_length=2000, description="Template description")
    template_config: Dict[str, Any] = Field(..., description="Complete template configuration")
    default_competitors: List[str] = Field(default_factory=list, description="Default competitor names")
    default_keywords: List[str] = Field(default_factory=list, description="Default monitoring keywords")
    risk_categories: List[str] = Field(default_factory=list, description="Industry-specific risk categories")
    kpi_metrics: List[str] = Field(default_factory=list, description="Key performance indicators")

    @validator('template_config')
    def validate_template_config(cls, v):
        """Ensure template_config contains required fields."""
        required_fields = ['watchlist_config', 'notification_rules', 'analysis_settings']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"template_config must contain '{field}'")
        return v

    @validator('default_competitors')
    def validate_competitors(cls, v):
        """Validate competitor list."""
        if len(v) > 50:
            raise ValueError("Maximum 50 default competitors allowed")
        return [competitor.strip() for competitor in v if competitor.strip()]

    @validator('default_keywords')
    def validate_keywords(cls, v):
        """Validate keyword list."""
        if len(v) > 100:
            raise ValueError("Maximum 100 default keywords allowed")
        return [keyword.strip().lower() for keyword in v if keyword.strip()]


class IndustryTemplateUpdate(BaseModel):
    """Schema for updating an industry template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    template_config: Optional[Dict[str, Any]] = None
    default_competitors: Optional[List[str]] = None
    default_keywords: Optional[List[str]] = None
    risk_categories: Optional[List[str]] = None
    kpi_metrics: Optional[List[str]] = None
    is_active: Optional[bool] = None

    @validator('template_config')
    def validate_template_config(cls, v):
        """Ensure template_config contains required fields if provided."""
        if v is not None:
            required_fields = ['watchlist_config', 'notification_rules', 'analysis_settings']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f"template_config must contain '{field}'")
        return v


class IndustryTemplateResponse(BaseModel):
    """Schema for industry template responses."""
    id: int
    name: str
    industry_sector: str
    description: str
    template_config: Dict[str, Any]
    default_competitors: List[str]
    default_keywords: List[str]
    risk_categories: List[str]
    kpi_metrics: List[str]
    usage_count: int
    rating: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


class IndustryTemplateMetadata(BaseModel):
    """Schema for template metadata (lightweight response)."""
    id: int
    name: str
    industry_sector: str
    description: str
    usage_count: int
    rating: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True


class TemplateApplicationCreate(BaseModel):
    """Schema for applying a template to a workspace."""
    template_id: int = Field(..., description="ID of the template to apply")
    workspace_id: str = Field(..., min_length=1, description="Target workspace ID")
    customizations: Dict[str, Any] = Field(default_factory=dict, description="Template customizations")

    @validator('customizations')
    def validate_customizations(cls, v):
        """Ensure customizations is a valid dictionary."""
        if v is None:
            return {}
        return v


class TemplateApplicationUpdate(BaseModel):
    """Schema for updating a template application."""
    customizations: Optional[Dict[str, Any]] = None
    status: Optional[TemplateStatus] = None
    rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Rating from 0.0 to 5.0")
    feedback: Optional[str] = Field(None, max_length=2000, description="User feedback")


class TemplateApplicationResponse(BaseModel):
    """Schema for template application responses."""
    id: int
    template_id: int
    workspace_id: str
    user_id: str
    customizations: Dict[str, Any]
    applied_at: datetime
    status: str
    rating: Optional[float]
    feedback: Optional[str]
    template_name: str
    industry_sector: str

    class Config:
        from_attributes = True


class TemplateRating(BaseModel):
    """Schema for rating a template."""
    rating: float = Field(..., ge=0.0, le=5.0, description="Rating from 0.0 to 5.0")
    feedback: Optional[str] = Field(None, max_length=2000, description="Optional feedback")


class TemplateSearchRequest(BaseModel):
    """Schema for template search requests."""
    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    industry_sector: Optional[str] = Field(None, max_length=100, description="Filter by industry sector")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")


class TemplateFilter(BaseModel):
    """Schema for filtering templates."""
    industry_sector: Optional[str] = None
    is_active: Optional[bool] = True
    min_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    min_usage_count: Optional[int] = Field(None, ge=0)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

    @validator('created_before')
    def validate_date_range(cls, v, values):
        """Ensure created_before is after created_after."""
        if v and 'created_after' in values and values['created_after'] and v < values['created_after']:
            raise ValueError("created_before must be after created_after")
        return v


class TemplateStatistics(BaseModel):
    """Schema for template usage statistics."""
    template_id: int
    name: str
    industry_sector: str
    total_usage: int
    status_counts: Dict[str, int]
    rating_stats: Dict[str, float]
    created_at: datetime
    updated_at: datetime


class IndustryList(BaseModel):
    """Schema for available industries."""
    industries: List[str] = Field(..., description="List of available industry sectors")


class TemplateConfigValidation(BaseModel):
    """Schema for validating template configurations."""
    watchlist_config: Dict[str, Any] = Field(..., description="Watchlist configuration")
    notification_rules: Dict[str, Any] = Field(..., description="Notification rules")
    analysis_settings: Dict[str, Any] = Field(..., description="Analysis settings")
    
    @validator('watchlist_config')
    def validate_watchlist_config(cls, v):
        """Validate watchlist configuration structure."""
        required_fields = ['companies', 'keywords', 'sources']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"watchlist_config must contain '{field}'")
        return v
    
    @validator('notification_rules')
    def validate_notification_rules(cls, v):
        """Validate notification rules structure."""
        required_fields = ['triggers', 'channels', 'frequency']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"notification_rules must contain '{field}'")
        return v
    
    @validator('analysis_settings')
    def validate_analysis_settings(cls, v):
        """Validate analysis settings structure."""
        required_fields = ['risk_thresholds', 'impact_categories', 'confidence_levels']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"analysis_settings must contain '{field}'")
        return v


class BulkTemplateOperation(BaseModel):
    """Schema for bulk template operations."""
    template_ids: List[int] = Field(..., min_items=1, max_items=50, description="List of template IDs")
    operation: str = Field(..., description="Operation to perform")
    
    @validator('operation')
    def validate_operation(cls, v):
        """Validate bulk operation type."""
        valid_operations = ['activate', 'deactivate', 'delete', 'export']
        if v not in valid_operations:
            raise ValueError(f"Invalid operation. Must be one of: {valid_operations}")
        return v


class TemplateExport(BaseModel):
    """Schema for template export."""
    templates: List[IndustryTemplateResponse] = Field(..., description="List of templates to export")
    export_format: str = Field("json", description="Export format")
    include_applications: bool = Field(False, description="Include application data")
    
    @validator('export_format')
    def validate_export_format(cls, v):
        """Validate export format."""
        valid_formats = ['json', 'yaml', 'csv']
        if v not in valid_formats:
            raise ValueError(f"Invalid export format. Must be one of: {valid_formats}")
        return v