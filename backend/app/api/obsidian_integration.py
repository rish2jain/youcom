"""
Obsidian Knowledge Management Integration API Endpoints
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.obsidian_integration import (
    ObsidianIntegration, ObsidianSyncLog, ObsidianNoteMapping, ObsidianNoteTemplate
)
from app.models.user import User
from app.schemas.obsidian_integration import (
    ObsidianIntegrationCreate, ObsidianIntegrationUpdate, ObsidianIntegrationResponse,
    ObsidianSyncRequest, ObsidianSyncResponse, ObsidianNoteTemplateCreate,
    ObsidianNoteTemplateResponse, ObsidianHealthCheckResponse, ObsidianSyncStatusResponse
)
from app.services.obsidian_client import ObsidianClient, ObsidianVaultError, ObsidianConnectionError
from app.services.obsidian_sync_service import ObsidianSyncService
from app.services.obsidian_template_service import ObsidianTemplateService
from app.services.encryption_service import encryption_service

router = APIRouter(prefix="/obsidian", tags=["Obsidian Integration"])


# Integration Management Endpoints

@router.post("/integrations", response_model=ObsidianIntegrationResponse)
async def create_obsidian_integration(
    integration_data: ObsidianIntegrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Assume this dependency exists
):
    """Create a new Obsidian integration"""
    
    # Validate vault path accessibility
    try:
        async with ObsidianClient(
            vault_path=integration_data.vault_path,
            api_endpoint=integration_data.api_endpoint,
            api_key=integration_data.api_key,
            api_port=integration_data.api_port or 27123
        ) as client:
            health = await client.health_check()
            if health["overall_status"] != "healthy":
                raise HTTPException(
                    status_code=400,
                    detail=f"Vault health check failed: {health['errors']}"
                )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to connect to Obsidian vault: {str(e)}"
        )
    
    # Encrypt API key if provided
    api_key_encrypted = None
    if integration_data.api_key:
        api_key_encrypted = encryption_service.encrypt(integration_data.api_key)
    
    # Create integration
    integration = ObsidianIntegration(
        user_id=current_user.id,
        vault_name=integration_data.vault_name,
        vault_path=integration_data.vault_path,
        vault_id=integration_data.vault_id,
        api_endpoint=integration_data.api_endpoint,
        api_key_encrypted=api_key_encrypted,
        api_port=integration_data.api_port or 27123,
        sync_enabled=integration_data.sync_enabled,
        auto_sync=integration_data.auto_sync,
        sync_frequency_minutes=integration_data.sync_frequency_minutes or 15,
        base_folder=integration_data.base_folder or "Competitive Intelligence",
        company_folder_template=integration_data.company_folder_template or "Companies/{company_name}",
        market_folder_template=integration_data.market_folder_template or "Market Analysis/{industry}",
        trend_folder_template=integration_data.trend_folder_template or "Trends/{category}",
        enable_backlinks=integration_data.enable_backlinks,
        backlink_format=integration_data.backlink_format or "wikilink",
        auto_create_index=integration_data.auto_create_index,
        include_source_links=integration_data.include_source_links,
        include_metadata=integration_data.include_metadata,
        include_timestamps=integration_data.include_timestamps,
        markdown_style=integration_data.markdown_style or "obsidian"
    )
    
    db.add(integration)
    await db.commit()
    await db.refresh(integration)
    
    # Create default templates
    template_service = ObsidianTemplateService(db)
    await template_service.create_default_templates(str(integration.id))
    
    # Create tag hierarchy
    await template_service.create_tag_hierarchy(str(integration.id))
    
    return ObsidianIntegrationResponse.from_orm(integration)


@router.get("/integrations", response_model=List[ObsidianIntegrationResponse])
async def list_obsidian_integrations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all Obsidian integrations for the current user"""
    
    result = await db.execute(
        select(ObsidianIntegration)
        .where(ObsidianIntegration.user_id == current_user.id)
        .order_by(ObsidianIntegration.created_at.desc())
    )
    integrations = result.scalars().all()
    
    return [ObsidianIntegrationResponse.from_orm(integration) for integration in integrations]


@router.get("/integrations/{integration_id}", response_model=ObsidianIntegrationResponse)
async def get_obsidian_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific Obsidian integration"""
    
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    return ObsidianIntegrationResponse.from_orm(integration)


@router.put("/integrations/{integration_id}", response_model=ObsidianIntegrationResponse)
async def update_obsidian_integration(
    integration_id: str,
    update_data: ObsidianIntegrationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an Obsidian integration"""
    
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    
    # Handle API key encryption
    if "api_key" in update_dict and update_dict["api_key"]:
        update_dict["api_key_encrypted"] = encryption_service.encrypt(update_dict["api_key"])
        del update_dict["api_key"]
    
    for field, value in update_dict.items():
        if hasattr(integration, field):
            setattr(integration, field, value)
    
    integration.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(integration)
    
    return ObsidianIntegrationResponse.from_orm(integration)


@router.delete("/integrations/{integration_id}")
async def delete_obsidian_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an Obsidian integration"""
    
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    await db.delete(integration)
    await db.commit()
    
    return {"message": "Integration deleted successfully"}


# Health Check and Status Endpoints

@router.get("/integrations/{integration_id}/health", response_model=ObsidianHealthCheckResponse)
async def check_obsidian_integration_health(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check the health of an Obsidian integration"""
    
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    try:
        async with ObsidianClient.from_encrypted_credentials(
            vault_path=integration.vault_path,
            api_endpoint=integration.api_endpoint,
            encrypted_api_key=integration.api_key_encrypted,
            api_port=integration.api_port or 27123
        ) as client:
            health = await client.health_check()
            vault_info = await client.get_vault_info()
            
            return ObsidianHealthCheckResponse(
                integration_id=integration_id,
                overall_status=health["overall_status"],
                vault_accessible=health["vault_accessible"],
                api_accessible=health["api_accessible"],
                can_read=health["can_read"],
                can_write=health["can_write"],
                errors=health["errors"],
                vault_info=vault_info,
                checked_at=health["checked_at"]
            )
    
    except Exception as e:
        return ObsidianHealthCheckResponse(
            integration_id=integration_id,
            overall_status="unhealthy",
            vault_accessible=False,
            api_accessible=False,
            can_read=False,
            can_write=False,
            errors=[str(e)],
            vault_info={},
            checked_at=datetime.now(timezone.utc).isoformat()
        )


@router.get("/integrations/{integration_id}/status", response_model=ObsidianSyncStatusResponse)
async def get_obsidian_sync_status(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get synchronization status for an Obsidian integration"""
    
    # Verify integration ownership
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    sync_service = ObsidianSyncService(db)
    status = await sync_service.get_sync_status(integration_id)
    
    return ObsidianSyncStatusResponse(**status)


# Synchronization Endpoints

@router.post("/integrations/{integration_id}/sync", response_model=ObsidianSyncResponse)
async def trigger_obsidian_sync(
    integration_id: str,
    sync_request: ObsidianSyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger synchronization for an Obsidian integration"""
    
    # Verify integration ownership
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    if not integration.sync_enabled:
        raise HTTPException(status_code=400, detail="Sync is disabled for this integration")
    
    sync_service = ObsidianSyncService(db)
    
    if sync_request.async_sync:
        # Run sync in background
        background_tasks.add_task(
            sync_service.sync_integration,
            integration_id,
            sync_request.sync_type
        )
        
        return ObsidianSyncResponse(
            status="started",
            message="Sync started in background",
            sync_type=sync_request.sync_type,
            async_sync=True
        )
    else:
        # Run sync synchronously
        try:
            result = await sync_service.sync_integration(integration_id, sync_request.sync_type)
            
            return ObsidianSyncResponse(
                status=result["status"],
                message=f"Sync completed with {result.get('notes_processed', 0)} notes processed",
                sync_type=sync_request.sync_type,
                sync_log_id=result.get("sync_log_id"),
                notes_processed=result.get("notes_processed", 0),
                notes_created=result.get("notes_created", 0),
                notes_updated=result.get("notes_updated", 0),
                backlinks_created=result.get("backlinks_created", 0),
                errors=result.get("errors", []),
                async_sync=False
            )
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/integrations/{integration_id}/sync-logs")
async def get_obsidian_sync_logs(
    integration_id: str,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get synchronization logs for an Obsidian integration"""
    
    # Verify integration ownership
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Get sync logs
    result = await db.execute(
        select(ObsidianSyncLog)
        .where(ObsidianSyncLog.integration_id == integration_id)
        .order_by(ObsidianSyncLog.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "sync_type": log.sync_type,
            "operation": log.operation,
            "status": log.status,
            "started_at": log.started_at.isoformat(),
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            "duration_seconds": log.duration_seconds,
            "notes_processed": log.notes_processed,
            "notes_created": log.notes_created,
            "notes_updated": log.notes_updated,
            "backlinks_created": log.backlinks_created,
            "error_message": log.error_message,
            "error_details": log.error_details
        }
        for log in logs
    ]


# Note Export Endpoints

@router.post("/integrations/{integration_id}/export/impact-card/{impact_card_id}")
async def export_impact_card_to_obsidian(
    integration_id: str,
    impact_card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export a specific impact card to Obsidian"""
    
    # Verify integration ownership
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Get impact card
    from app.models.impact_card import ImpactCard
    result = await db.execute(
        select(ImpactCard).where(ImpactCard.id == impact_card_id)
    )
    impact_card = result.scalar_one_or_none()
    
    if not impact_card:
        raise HTTPException(status_code=404, detail="Impact card not found")
    
    try:
        sync_service = ObsidianSyncService(db)
        
        # Create a temporary sync result dict
        sync_results = {
            "notes_processed": 0,
            "notes_created": 0,
            "notes_updated": 0,
            "backlinks_created": 0,
            "errors": []
        }
        
        async with ObsidianClient.from_encrypted_credentials(
            vault_path=integration.vault_path,
            api_endpoint=integration.api_endpoint,
            encrypted_api_key=integration.api_key_encrypted,
            api_port=integration.api_port or 27123
        ) as client:
            await sync_service._sync_single_impact_card(integration, client, impact_card, sync_results)
        
        return {
            "message": "Impact card exported successfully",
            "impact_card_id": impact_card_id,
            "notes_created": sync_results["notes_created"],
            "notes_updated": sync_results["notes_updated"],
            "backlinks_created": sync_results["backlinks_created"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/integrations/{integration_id}/export/company-profile/{company_id}")
async def export_company_profile_to_obsidian(
    integration_id: str,
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export a specific company profile to Obsidian"""
    
    # Verify integration ownership
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Get company profile
    from app.models.company_research import CompanyResearch
    result = await db.execute(
        select(CompanyResearch).where(CompanyResearch.id == company_id)
    )
    company_profile = result.scalar_one_or_none()
    
    if not company_profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    
    try:
        sync_service = ObsidianSyncService(db)
        
        # Create a temporary sync result dict
        sync_results = {
            "notes_processed": 0,
            "notes_created": 0,
            "notes_updated": 0,
            "backlinks_created": 0,
            "errors": []
        }
        
        async with ObsidianClient.from_encrypted_credentials(
            vault_path=integration.vault_path,
            api_endpoint=integration.api_endpoint,
            encrypted_api_key=integration.api_key_encrypted,
            api_port=integration.api_port or 27123
        ) as client:
            await sync_service._sync_single_company_profile(integration, client, company_profile, sync_results)
        
        return {
            "message": "Company profile exported successfully",
            "company_id": company_id,
            "notes_created": sync_results["notes_created"],
            "notes_updated": sync_results["notes_updated"],
            "backlinks_created": sync_results["backlinks_created"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# Template Management Endpoints

@router.get("/integrations/{integration_id}/templates", response_model=List[ObsidianNoteTemplateResponse])
async def list_obsidian_templates(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all note templates for an integration"""
    
    # Verify integration ownership
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    template_service = ObsidianTemplateService(db)
    templates = await template_service.get_all_templates(integration_id)
    
    return [ObsidianNoteTemplateResponse.from_orm(template) for template in templates]


@router.post("/integrations/{integration_id}/templates", response_model=ObsidianNoteTemplateResponse)
async def create_obsidian_template(
    integration_id: str,
    template_data: ObsidianNoteTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new note template"""
    
    # Verify integration ownership
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    template = ObsidianNoteTemplate(
        integration_id=integration_id,
        **template_data.dict()
    )
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return ObsidianNoteTemplateResponse.from_orm(template)


@router.get("/integrations/{integration_id}/notes")
async def list_obsidian_notes(
    integration_id: str,
    content_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List notes managed by the integration"""
    
    # Verify integration ownership
    result = await db.execute(
        select(ObsidianIntegration)
        .where(
            and_(
                ObsidianIntegration.id == integration_id,
                ObsidianIntegration.user_id == current_user.id
            )
        )
    )
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    # Build query
    query = select(ObsidianNoteMapping).where(
        and_(
            ObsidianNoteMapping.integration_id == integration_id,
            ObsidianNoteMapping.is_active == True
        )
    )
    
    if content_type:
        query = query.where(ObsidianNoteMapping.content_type == content_type)
    
    query = query.order_by(ObsidianNoteMapping.created_in_obsidian_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    mappings = result.scalars().all()
    
    return [
        {
            "id": str(mapping.id),
            "content_type": mapping.content_type,
            "content_id": mapping.content_id,
            "content_title": mapping.content_title,
            "note_path": mapping.note_path,
            "note_filename": mapping.note_filename,
            "note_folder": mapping.note_folder,
            "created_in_obsidian_at": mapping.created_in_obsidian_at.isoformat(),
            "last_updated_in_obsidian_at": mapping.last_updated_in_obsidian_at.isoformat() if mapping.last_updated_in_obsidian_at else None,
            "last_synced_at": mapping.last_synced_at.isoformat() if mapping.last_synced_at else None,
            "sync_version": mapping.sync_version,
            "needs_update": mapping.needs_update,
            "backlinks_to": mapping.backlinks_to or [],
            "backlinks_from": mapping.backlinks_from or []
        }
        for mapping in mappings
    ]


# Utility function to get current user (placeholder)
async def get_current_user() -> User:
    """Placeholder for user authentication dependency"""
    # This should be replaced with actual authentication logic
    # For now, return a mock user
    return User(id=1, email="user@example.com", username="testuser")


@router.get("/workflow/status")
async def get_obsidian_workflow_status(db: AsyncSession = Depends(get_db)):
    """Get Obsidian workflow integration status."""
    try:
        from app.services.integration_workflow_service import IntegrationWorkflowService
        
        workflow_service = IntegrationWorkflowService(db)
        status = await workflow_service.get_workflow_integration_status()
        
        # Filter for Obsidian-specific information
        obsidian_status = {
            "workflow_health": status.get("workflow_health"),
            "obsidian_exports_completed": status.get("metrics", {}).get("obsidian_exports_completed", 0),
            "average_export_time": status.get("metrics", {}).get("average_sync_time", 0.0),
            "auto_export_enabled": status.get("configuration", {}).get("auto_obsidian_export", False),
            "last_updated": status.get("last_updated")
        }
        
        return obsidian_status
        
    except Exception as e:
        logger.error(f"Error getting Obsidian workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")