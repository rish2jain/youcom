"""Integration schemas for API requests and responses"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.integration import IntegrationType


class IntegrationCreate(BaseModel):
    """Schema for creating a new integration"""
    name: str = Field(..., description="Integration name")
    integration_type: IntegrationType = Field(..., description="Type of integration")
    config: Dict[str, Any] = Field(..., description="Integration configuration")
    workspace_id: int = Field(..., description="Workspace ID")
    is_active: bool = Field(default=True, description="Whether integration is active")


class IntegrationUpdate(BaseModel):
    """Schema for updating an integration"""
    name: Optional[str] = Field(None, description="Integration name")
    config: Optional[Dict[str, Any]] = Field(None, description="Integration configuration")
    is_active: Optional[bool] = Field(None, description="Whether integration is active")


class IntegrationResponse(BaseModel):
    """Schema for integration response"""
    id: int
    name: str
    integration_type: IntegrationType
    config: Dict[str, Any]
    workspace_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    sync_count: int = 0
    error_count: int = 0
    success_rate: float = 0.0

    class Config:
        from_attributes = True


class IntegrationTestRequest(BaseModel):
    """Schema for testing integration connection"""
    config: Dict[str, Any] = Field(..., description="Integration configuration to test")


class IntegrationTestResponse(BaseModel):
    """Schema for integration test response"""
    status: str = Field(..., description="Test status (success/error)")
    message: str = Field(..., description="Test result message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional test details")


class NotionTestRequest(BaseModel):
    """Schema for testing Notion integration"""
    api_token: str = Field(..., description="Notion API token")


class NotionSyncRequest(BaseModel):
    """Schema for syncing data to Notion"""
    integration_id: int = Field(..., description="Integration ID")
    data_type: str = Field(..., description="Type of data to sync (research/impact)")
    data_id: int = Field(..., description="ID of data to sync")


class SalesforceTestRequest(BaseModel):
    """Schema for testing Salesforce integration"""
    instance_url: str = Field(..., description="Salesforce instance URL")
    access_token: str = Field(..., description="Salesforce access token")


class SalesforceSyncRequest(BaseModel):
    """Schema for syncing data to Salesforce"""
    integration_id: int = Field(..., description="Integration ID")
    data_type: str = Field(..., description="Type of data to sync (account/opportunity/task)")
    data_id: int = Field(..., description="ID of data to sync")


class IntegrationLogResponse(BaseModel):
    """Schema for integration log response"""
    id: int
    integration_id: int
    action: str
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IntegrationStatsResponse(BaseModel):
    """Schema for integration statistics"""
    total_integrations: int
    active_integrations: int
    total_syncs: int
    successful_syncs: int
    failed_syncs: int
    success_rate: float
    integrations_by_type: Dict[str, int]
    recent_activity: list[IntegrationLogResponse]