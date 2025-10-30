"""
HubSpot Integration API Endpoints
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.database import get_db
from app.models.hubspot_integration import (
    HubSpotIntegration, HubSpotSyncLog, HubSpotCustomProperty, HubSpotWorkflowTrigger
)
from app.models.workspace import Workspace
from app.schemas.hubspot_integration import (
    HubSpotOAuthRequest, HubSpotOAuthResponse, HubSpotTokenExchange,
    HubSpotIntegrationCreate, HubSpotIntegrationUpdate, HubSpotIntegrationResponse,
    HubSpotSyncRequest, HubSpotSyncLogResponse, HubSpotHealthCheckResponse,
    HubSpotLeadEnrichmentRequest, HubSpotLeadEnrichmentResponse,
    HubSpotWorkflowTriggerRequest, HubSpotWorkflowTriggerResponse,
    HubSpotCustomPropertyResponse, HubSpotIntegrationStats, HubSpotErrorResponse
)
from app.services.hubspot_client import HubSpotClient, HubSpotAPIError, HubSpotAuthError
from app.services.hubspot_sync_service import HubSpotSyncService, get_integration_by_workspace
from app.services.hubspot_automation_service import HubSpotAutomationService, create_automation_service
from app.services.encryption_service import encryption_service
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hubspot", tags=["HubSpot Integration"])

# OAuth Configuration from settings


@router.post("/oauth/authorize", response_model=HubSpotOAuthResponse)
async def get_oauth_url(request: HubSpotOAuthRequest):
    """Get HubSpot OAuth authorization URL"""
    try:
        auth_url = HubSpotClient.get_oauth_url(
            client_id=settings.hubspot_client_id,
            redirect_uri=request.redirect_uri,
            scopes=request.scopes,
            state=request.state
        )
        
        return HubSpotOAuthResponse(
            authorization_url=auth_url,
            state=request.state
        )
    except Exception as e:
        logger.error(f"Failed to generate OAuth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate OAuth URL")


@router.post("/oauth/token", response_model=dict)
async def exchange_oauth_token(request: HubSpotTokenExchange):
    """Exchange OAuth code for access tokens"""
    try:
        token_data = await HubSpotClient.exchange_code_for_tokens(
            client_id=settings.hubspot_client_id,
            client_secret=settings.hubspot_client_secret.get_secret_value(),
            redirect_uri=request.redirect_uri,
            code=request.code
        )
        
        # Don't return the actual tokens in the response for security
        return {
            "status": "success",
            "expires_in": token_data.get("expires_in"),
            "scope": token_data.get("scope"),
            "token_type": token_data.get("token_type")
        }
    except HubSpotAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to exchange OAuth token: {e}")
        raise HTTPException(status_code=500, detail="Failed to exchange OAuth token")


@router.post("/integrations", response_model=HubSpotIntegrationResponse)
async def create_integration(
    request: HubSpotIntegrationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Create a new HubSpot integration"""
    try:
        # Check if integration already exists for this workspace
        existing = await get_integration_by_workspace(request.workspace_id, db)
        if existing:
            raise HTTPException(status_code=400, detail="HubSpot integration already exists for this workspace")
        
        # Verify workspace exists
        workspace_query = select(Workspace).where(Workspace.id == request.workspace_id)
        workspace_result = await db.execute(workspace_query)
        workspace = workspace_result.scalar_one_or_none()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        # Test the HubSpot connection
        async with HubSpotClient(request.access_token, request.refresh_token) as client:
            account_info = await client.get_account_info()
            portal_id = str(account_info.get("portalId", request.hubspot_portal_id))
            account_name = account_info.get("accountName", request.hubspot_account_name)
        
        # Create integration
        integration = HubSpotIntegration(
            workspace_id=request.workspace_id,
            hubspot_portal_id=portal_id,
            hubspot_account_name=account_name,
            access_token_encrypted=encryption_service.encrypt(request.access_token),
            refresh_token_encrypted=encryption_service.encrypt(request.refresh_token) if request.refresh_token else None,
            sync_frequency_minutes=request.sync_frequency_minutes,
            workflow_mappings=request.workflow_mappings or {},
            sync_status="active",
            created_at=datetime.utcnow()
        )
        
        db.add(integration)
        await db.commit()
        await db.refresh(integration)
        
        # Set up custom properties in background
        background_tasks.add_task(setup_custom_properties_background, integration.id)
        
        return HubSpotIntegrationResponse.model_validate(integration)
        
    except HubSpotAuthError as e:
        raise HTTPException(status_code=401, detail=f"HubSpot authentication failed: {e}")
    except HubSpotAPIError as e:
        raise HTTPException(status_code=400, detail=f"HubSpot API error: {e}")
    except Exception as e:
        logger.error(f"Failed to create HubSpot integration: {e}")
        raise HTTPException(status_code=500, detail="Failed to create integration")


@router.get("/integrations/{workspace_id}", response_model=HubSpotIntegrationResponse)
async def get_integration(
    workspace_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get HubSpot integration for a workspace"""
    integration = await get_integration_by_workspace(workspace_id, db)
    if not integration:
        raise HTTPException(status_code=404, detail="HubSpot integration not found")
    
    return HubSpotIntegrationResponse.model_validate(integration)


@router.put("/integrations/{integration_id}", response_model=HubSpotIntegrationResponse)
async def update_integration(
    integration_id: UUID,
    request: HubSpotIntegrationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update HubSpot integration"""
    query = select(HubSpotIntegration).where(HubSpotIntegration.id == integration_id)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Update fields
    if request.sync_enabled is not None:
        integration.sync_enabled = request.sync_enabled
    if request.sync_frequency_minutes is not None:
        integration.sync_frequency_minutes = request.sync_frequency_minutes
    if request.workflow_mappings is not None:
        integration.workflow_mappings = request.workflow_mappings
    
    integration.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(integration)
    
    return HubSpotIntegrationResponse.model_validate(integration)


@router.delete("/integrations/{integration_id}")
async def delete_integration(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete HubSpot integration"""
    query = select(HubSpotIntegration).where(HubSpotIntegration.id == integration_id)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    await db.delete(integration)
    await db.commit()
    
    return {"status": "success", "message": "Integration deleted"}


@router.post("/integrations/{integration_id}/sync")
async def trigger_sync(
    integration_id: UUID,
    request: HubSpotSyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger HubSpot synchronization"""
    query = select(HubSpotIntegration).where(HubSpotIntegration.id == integration_id)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if not integration.sync_enabled:
        raise HTTPException(status_code=400, detail="Sync is disabled for this integration")
    
    # Trigger sync in background
    background_tasks.add_task(
        perform_sync_background,
        integration_id,
        request.sync_type,
        request.direction
    )
    
    return [{"status": "sync_triggered", "sync_type": request.sync_type, "direction": request.direction}]


@router.get("/integrations/{integration_id}/sync-logs", response_model=List[HubSpotSyncLogResponse])
async def get_sync_logs(
    integration_id: UUID,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get sync logs for an integration"""
    query = (
        select(HubSpotSyncLog)
        .where(HubSpotSyncLog.integration_id == integration_id)
        .order_by(desc(HubSpotSyncLog.started_at))
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(query)
    sync_logs = result.scalars().all()
    
    return [HubSpotSyncLogResponse.model_validate(log) for log in sync_logs]


@router.get("/integrations/{integration_id}/health", response_model=HubSpotHealthCheckResponse)
async def check_integration_health(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Check HubSpot integration health"""
    query = select(HubSpotIntegration).where(HubSpotIntegration.id == integration_id)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    issues = []
    recommendations = []
    api_connectivity = False
    token_valid = False
    
    try:
        # Test API connectivity and token validity
        async with HubSpotClient.from_encrypted_tokens(
            integration.access_token_encrypted,
            integration.refresh_token_encrypted
        ) as client:
            await client.get_account_info()
            api_connectivity = True
            token_valid = True
    except HubSpotAuthError:
        issues.append("Authentication token is invalid or expired")
        recommendations.append("Refresh the OAuth token or re-authenticate")
    except Exception as e:
        issues.append(f"API connectivity issue: {str(e)}")
        recommendations.append("Check network connectivity and HubSpot API status")
    
    # Check sync status
    if integration.consecutive_failures > 3:
        issues.append(f"Multiple consecutive sync failures ({integration.consecutive_failures})")
        recommendations.append("Review sync logs and resolve underlying issues")
    
    # Check last sync time
    if integration.last_sync_at and integration.last_sync_at < datetime.utcnow() - timedelta(hours=24):
        issues.append("No sync in the last 24 hours")
        recommendations.append("Check if sync is enabled and scheduled properly")
    
    # Determine overall status
    if not api_connectivity or not token_valid:
        status = "error"
    elif issues:
        status = "warning"
    else:
        status = "healthy"
    
    return HubSpotHealthCheckResponse(
        integration_id=integration.id,
        status=status,
        last_sync_status=integration.sync_status,
        last_sync_at=integration.last_sync_at,
        consecutive_failures=integration.consecutive_failures,
        api_connectivity=api_connectivity,
        token_valid=token_valid,
        custom_properties_status="active" if integration.custom_properties_created else "not_configured",
        issues=issues,
        recommendations=recommendations
    )


@router.post("/integrations/{integration_id}/enrich-lead", response_model=HubSpotLeadEnrichmentResponse)
async def enrich_lead(
    integration_id: UUID,
    request: HubSpotLeadEnrichmentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Enrich a HubSpot lead with competitive intelligence"""
    query = select(HubSpotIntegration).where(HubSpotIntegration.id == integration_id)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    try:
        async with HubSpotAutomationService(integration, db) as automation_service:
            result = await automation_service.enrich_new_lead(
                request.contact_id,
                request.company_id
            )
            
            return HubSpotLeadEnrichmentResponse(**result)
            
    except Exception as e:
        logger.error(f"Failed to enrich lead {request.contact_id}: {e}")
        return HubSpotLeadEnrichmentResponse(
            status="error",
            contact_id=request.contact_id,
            company_id=request.company_id,
            error=str(e)
        )


@router.post("/integrations/{integration_id}/trigger-workflow", response_model=dict)
async def trigger_workflow(
    integration_id: UUID,
    request: HubSpotWorkflowTriggerRequest,
    db: AsyncSession = Depends(get_db)
):
    """Trigger a HubSpot workflow"""
    query = select(HubSpotIntegration).where(HubSpotIntegration.id == integration_id)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    try:
        async with HubSpotAutomationService(integration, db) as automation_service:
            result = await automation_service._trigger_workflow(
                request.trigger_type,
                request.object_id,
                request.object_type,
                request.context or {}
            )
            
            return result
            
    except Exception as e:
        logger.error(f"Failed to trigger workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/{integration_id}/custom-properties", response_model=List[HubSpotCustomPropertyResponse])
async def get_custom_properties(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get custom properties created for the integration"""
    query = select(HubSpotCustomProperty).where(HubSpotCustomProperty.integration_id == integration_id)
    result = await db.execute(query)
    properties = result.scalars().all()
    
    return [HubSpotCustomPropertyResponse.model_validate(prop) for prop in properties]


@router.get("/integrations/{integration_id}/stats", response_model=HubSpotIntegrationStats)
async def get_integration_stats(
    integration_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get integration statistics"""
    query = select(HubSpotIntegration).where(HubSpotIntegration.id == integration_id)
    result = await db.execute(query)
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Get sync statistics
    last_24h = datetime.utcnow() - timedelta(hours=24)
    sync_stats_query = (
        select(
            func.count(HubSpotSyncLog.id).label("total_syncs"),
            func.count(HubSpotSyncLog.id).filter(HubSpotSyncLog.status == "failure").label("failed_syncs"),
            func.avg(HubSpotSyncLog.duration_seconds).label("avg_duration")
        )
        .where(
            and_(
                HubSpotSyncLog.integration_id == integration_id,
                HubSpotSyncLog.started_at >= last_24h
            )
        )
    )
    
    sync_result = await db.execute(sync_stats_query)
    sync_stats = sync_result.first()
    
    total_syncs = sync_stats.total_syncs or 0
    failed_syncs = sync_stats.failed_syncs or 0
    success_rate = ((total_syncs - failed_syncs) / total_syncs * 100) if total_syncs > 0 else 100.0
    
    return HubSpotIntegrationStats(
        total_contacts_synced=integration.total_contacts_synced,
        total_companies_synced=integration.total_companies_synced,
        total_workflows_triggered=integration.total_workflows_triggered,
        sync_success_rate=success_rate,
        average_sync_duration=float(sync_stats.avg_duration or 0),
        last_24h_syncs=total_syncs,
        last_24h_errors=failed_syncs,
        custom_properties_count=len(integration.custom_properties_created or []),
        active_workflow_mappings=len(integration.workflow_mappings or {})
    )


# Background task functions
async def setup_custom_properties_background(integration_id: UUID):
    """Background task to set up custom properties"""
    async for db in get_db():
        try:
            query = select(HubSpotIntegration).where(HubSpotIntegration.id == integration_id)
            result = await db.execute(query)
            integration = result.scalar_one_or_none()
            
            if integration:
                async with HubSpotSyncService(integration, db) as sync_service:
                    await sync_service.setup_custom_properties()
                    
        except Exception as e:
            logger.error(f"Failed to set up custom properties for integration {integration_id}: {e}")
        finally:
            break


async def perform_sync_background(integration_id: UUID, sync_type: str, direction: str):
    """Background task to perform sync"""
    async for db in get_db():
        try:
            query = select(HubSpotIntegration).where(HubSpotIntegration.id == integration_id)
            result = await db.execute(query)
            integration = result.scalar_one_or_none()
            
            if integration:
                async with HubSpotSyncService(integration, db) as sync_service:
                    if direction == "to_hubspot":
                        await sync_service.sync_to_hubspot(sync_type)
                    elif direction == "from_hubspot":
                        await sync_service.sync_from_hubspot(sync_type)
                    else:  # bidirectional
                        await sync_service.bidirectional_sync(sync_type)
                        
        except Exception as e:
            logger.error(f"Failed to perform sync for integration {integration_id}: {e}")
        finally:
            break

@router.get("/workflow/status")
async def get_integration_workflow_status(db: AsyncSession = Depends(get_db)):
    """Get integration workflow status."""
    try:
        from app.services.integration_workflow_service import IntegrationWorkflowService
        
        workflow_service = IntegrationWorkflowService(db)
        status = await workflow_service.get_workflow_integration_status()
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting integration workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@router.post("/workflow/health-check")
async def trigger_integration_health_check(db: AsyncSession = Depends(get_db)):
    """Trigger integration health check."""
    try:
        from app.services.integration_workflow_service import IntegrationWorkflowService
        
        workflow_service = IntegrationWorkflowService(db)
        health_status = await workflow_service.wire_integration_health_checks()
        
        return {
            "message": "Integration health check completed",
            "health_status": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering integration health check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger health check: {str(e)}")