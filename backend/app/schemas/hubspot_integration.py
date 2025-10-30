"""
Pydantic schemas for HubSpot integration API
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class HubSpotOAuthRequest(BaseModel):
    """Request to initiate HubSpot OAuth flow"""
    redirect_uri: str = Field(..., description="OAuth redirect URI")
    scopes: List[str] = Field(default=["crm.objects.contacts.read", "crm.objects.contacts.write", 
                                      "crm.objects.companies.read", "crm.objects.companies.write",
                                      "crm.schemas.contacts.read", "crm.schemas.companies.read",
                                      "automation"], description="OAuth scopes to request")
    state: Optional[str] = Field(None, description="OAuth state parameter")


class HubSpotOAuthResponse(BaseModel):
    """Response with OAuth authorization URL"""
    authorization_url: str = Field(..., description="HubSpot OAuth authorization URL")
    state: Optional[str] = Field(None, description="OAuth state parameter")


class HubSpotTokenExchange(BaseModel):
    """Request to exchange OAuth code for tokens"""
    code: str = Field(..., description="OAuth authorization code")
    redirect_uri: str = Field(..., description="OAuth redirect URI")


class HubSpotIntegrationCreate(BaseModel):
    """Request to create HubSpot integration"""
    workspace_id: UUID = Field(..., description="Workspace ID")
    hubspot_portal_id: str = Field(..., description="HubSpot portal ID")
    hubspot_account_name: Optional[str] = Field(None, description="HubSpot account name")
    access_token: str = Field(..., description="HubSpot access token")
    refresh_token: Optional[str] = Field(None, description="HubSpot refresh token")
    sync_frequency_minutes: int = Field(default=5, description="Sync frequency in minutes")
    workflow_mappings: Optional[Dict[str, str]] = Field(default=None, description="Workflow ID mappings")


class HubSpotIntegrationUpdate(BaseModel):
    """Request to update HubSpot integration"""
    sync_enabled: Optional[bool] = Field(None, description="Enable/disable sync")
    sync_frequency_minutes: Optional[int] = Field(None, description="Sync frequency in minutes")
    workflow_mappings: Optional[Dict[str, str]] = Field(None, description="Workflow ID mappings")


class HubSpotIntegrationResponse(BaseModel):
    """HubSpot integration response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    workspace_id: UUID
    hubspot_portal_id: str
    hubspot_account_name: Optional[str]
    sync_enabled: bool
    sync_frequency_minutes: int
    custom_properties_created: List[str]
    workflow_mappings: Dict[str, str]
    last_sync_at: Optional[datetime]
    last_successful_sync_at: Optional[datetime]
    sync_status: str
    last_error_message: Optional[str]
    consecutive_failures: int
    total_contacts_synced: int
    total_companies_synced: int
    total_workflows_triggered: int
    created_at: datetime
    updated_at: datetime


class HubSpotSyncRequest(BaseModel):
    """Request to trigger sync"""
    sync_type: str = Field(default="incremental", description="Sync type: incremental, full_sync, manual_sync")
    direction: str = Field(default="bidirectional", description="Sync direction: to_hubspot, from_hubspot, bidirectional")


class HubSpotSyncLogResponse(BaseModel):
    """HubSpot sync log response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    integration_id: UUID
    sync_type: str
    direction: str
    status: str
    records_processed: int
    records_successful: int
    records_failed: int
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    sync_metadata: Optional[Dict[str, Any]]


class HubSpotHealthCheckResponse(BaseModel):
    """HubSpot integration health check response"""
    integration_id: UUID
    status: str = Field(..., description="Health status: healthy, warning, error")
    last_sync_status: str
    last_sync_at: Optional[datetime]
    consecutive_failures: int
    api_connectivity: bool
    token_valid: bool
    custom_properties_status: str
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class HubSpotLeadEnrichmentRequest(BaseModel):
    """Request to enrich a lead"""
    contact_id: str = Field(..., description="HubSpot contact ID")
    company_id: Optional[str] = Field(None, description="HubSpot company ID")
    force_refresh: bool = Field(default=False, description="Force refresh of intelligence data")


class HubSpotLeadEnrichmentResponse(BaseModel):
    """Lead enrichment response"""
    status: str
    contact_id: str
    company_id: Optional[str]
    intelligence_data: Optional[Dict[str, Any]]
    error: Optional[str]


class HubSpotWorkflowTriggerRequest(BaseModel):
    """Request to trigger workflow"""
    trigger_type: str = Field(..., description="Type of trigger")
    object_id: str = Field(..., description="HubSpot object ID")
    object_type: str = Field(default="contact", description="HubSpot object type")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context data")


class HubSpotWorkflowTriggerResponse(BaseModel):
    """Workflow trigger response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    integration_id: UUID
    workflow_id: str
    workflow_name: Optional[str]
    trigger_type: str
    hubspot_object_type: str
    hubspot_object_id: str
    status: str
    sent_at: Optional[datetime]
    response_status_code: Optional[int]
    response_message: Optional[str]
    retry_count: int
    created_at: datetime


class HubSpotCustomPropertyResponse(BaseModel):
    """Custom property response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    integration_id: UUID
    hubspot_property_name: str
    hubspot_property_type: str
    hubspot_object_type: str
    cia_field_name: str
    cia_field_type: str
    property_label: Optional[str]
    property_description: Optional[str]
    is_active: bool
    created_in_hubspot_at: Optional[datetime]
    created_at: datetime


class HubSpotIntegrationStats(BaseModel):
    """Integration statistics"""
    total_contacts_synced: int
    total_companies_synced: int
    total_workflows_triggered: int
    sync_success_rate: float
    average_sync_duration: float
    last_24h_syncs: int
    last_24h_errors: int
    custom_properties_count: int
    active_workflow_mappings: int


class HubSpotErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None