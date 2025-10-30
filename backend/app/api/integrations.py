"""
Integration Marketplace API Endpoints - Week 1 Implementation
Third-party integration marketplace with revenue sharing.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.integration_marketplace import IntegrationMarketplaceService
from app.services.auth_service import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations", tags=["Integration Marketplace"])

# Request/Response Models
class IntegrationRegistrationRequest(BaseModel):
    name: str = Field(..., description="Integration name")
    description: str = Field(..., description="Integration description")
    category: str = Field(..., description="Integration category")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for external integrations")
    configuration_schema: Dict[str, Any] = Field(default_factory=dict, description="Configuration schema")
    required_permissions: List[str] = Field(default_factory=list, description="Required permissions")

class IntegrationResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    category: str
    developer_name: Optional[str]
    version: str
    install_count: int
    rating: float
    rating_count: int
    is_featured: bool
    created_at: str

class IntegrationInstallationRequest(BaseModel):
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Integration configuration")
    workspace_id: Optional[str] = Field(None, description="Workspace ID for installation")

class IntegrationInstallationResponse(BaseModel):
    installation_id: str
    integration: Dict[str, Any]
    configuration: Dict[str, Any]
    installed_at: str
    status: str = "active"

class IntegrationExecutionRequest(BaseModel):
    action: str = Field(..., description="Action to execute")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action payload")

class IntegrationExecutionResponse(BaseModel):
    success: bool
    result: Dict[str, Any]
    error: Optional[str]
    latency_ms: int
    timestamp: str

class MarketplaceStatsResponse(BaseModel):
    total_integrations: int
    active_integrations: int
    total_installations: int
    featured_integrations: int
    categories: Dict[str, int]
    top_integrations: List[Dict[str, Any]]

class RevenueShareResponse(BaseModel):
    integration_id: str
    period_start: str
    period_end: str
    total_revenue: float
    developer_share: float
    platform_share: float
    revenue_share_percent: float
    usage_count: int

@router.get("/marketplace", response_model=List[IntegrationResponse])
async def get_marketplace_integrations(
    category: Optional[str] = Query(None, description="Filter by category"),
    featured_only: bool = Query(False, description="Show only featured integrations"),
    limit: int = Query(50, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """Get integrations from marketplace"""
    logger.info(f"📱 Marketplace integrations requested (category: {category}, featured: {featured_only})")
    
    try:
        integrations = await integration_marketplace.get_marketplace_integrations(
            category=category,
            featured_only=featured_only,
            limit=limit,
            offset=offset,
            db_session=db
        )
        
        return [IntegrationResponse(**integration) for integration in integrations]
        
    except Exception as e:
        logger.error(f"❌ Failed to get marketplace integrations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get marketplace integrations: {str(e)}"
        )

@router.post("/register", response_model=Dict[str, Any])
async def register_integration(
    request: IntegrationRegistrationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register a new integration in the marketplace"""
    logger.info(f"📝 Integration registration requested: {request.name} by {current_user.email}")
    
    try:
        # Validate category
        try:
            category = IntegrationCategory(request.category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Valid categories: {[c.value for c in IntegrationCategory]}"
            )
        
        # Create integration config
        config = IntegrationConfig(
            name=request.name,
            description=request.description,
            category=category,
            webhook_url=request.webhook_url,
            configuration_schema=request.configuration_schema,
            required_permissions=request.required_permissions
        )
        
        # Register integration
        integration = await integration_marketplace.register_integration(
            config=config,
            developer_id=str(current_user.id),
            db_session=db
        )
        
        logger.info(f"✅ Integration registered: {request.name}")
        
        return {
            "id": str(integration.id),
            "name": integration.name,
            "slug": integration.slug,
            "status": integration.status,
            "message": "Integration registered successfully. Pending review.",
            "created_at": integration.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Integration registration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to register integration: {str(e)}"
        )

@router.post("/{integration_id}/install", response_model=IntegrationInstallationResponse)
async def install_integration(
    integration_id: str,
    request: IntegrationInstallationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Install integration for user/workspace"""
    logger.info(f"⬇️ Integration installation requested: {integration_id} by {current_user.email}")
    
    try:
        # Install integration
        installation = await integration_marketplace.install_integration(
            integration_id=integration_id,
            user_id=str(current_user.id),
            workspace_id=request.workspace_id,
            configuration=request.configuration,
            db_session=db
        )
        
        # Get integration details
        from app.models.integration import Integration
        integration = await db.get(Integration, integration_id)
        
        logger.info(f"✅ Integration installed: {integration_id}")
        
        return IntegrationInstallationResponse(
            installation_id=str(installation.id),
            integration={
                "id": str(integration.id),
                "name": integration.name,
                "slug": integration.slug,
                "category": integration.category,
                "version": integration.version
            },
            configuration=installation.configuration,
            installed_at=installation.installed_at.isoformat()
        )
        
    except ValueError as e:
        logger.error(f"❌ Integration installation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Integration installation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to install integration: {str(e)}"
        )

@router.delete("/installations/{installation_id}")
async def uninstall_integration(
    installation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Uninstall integration"""
    logger.info(f"🗑️ Integration uninstallation requested: {installation_id} by {current_user.email}")
    
    try:
        success = await integration_marketplace.uninstall_integration(
            installation_id=installation_id,
            user_id=str(current_user.id),
            db_session=db
        )
        
        if success:
            logger.info(f"✅ Integration uninstalled: {installation_id}")
            return {
                "status": "uninstalled",
                "installation_id": installation_id,
                "message": "Integration uninstalled successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to uninstall integration")
        
    except ValueError as e:
        logger.error(f"❌ Integration uninstallation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Integration uninstallation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to uninstall integration: {str(e)}"
        )

@router.get("/my-integrations", response_model=List[Dict[str, Any]])
async def get_user_integrations(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's installed integrations"""
    logger.info(f"📋 User integrations requested by {current_user.email}")
    
    try:
        integrations = await integration_marketplace.get_user_integrations(
            user_id=str(current_user.id),
            workspace_id=workspace_id,
            db_session=db
        )
        
        return integrations
        
    except Exception as e:
        logger.error(f"❌ Failed to get user integrations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user integrations: {str(e)}"
        )

@router.post("/installations/{installation_id}/execute", response_model=IntegrationExecutionResponse)
async def execute_integration(
    installation_id: str,
    request: IntegrationExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Execute integration action"""
    logger.info(f"⚡ Integration execution requested: {installation_id} action: {request.action}")
    
    try:
        # Execute integration
        result = await integration_marketplace.execute_integration(
            installation_id=installation_id,
            action=request.action,
            payload=request.payload,
            db_session=db
        )
        
        # Background task: Update usage analytics
        background_tasks.add_task(
            _update_integration_analytics,
            installation_id,
            request.action,
            result["success"],
            result["latency_ms"]
        )
        
        logger.info(f"✅ Integration executed: {installation_id} - {request.action}")
        
        return IntegrationExecutionResponse(
            success=result["success"],
            result=result["result"],
            error=result["error"],
            latency_ms=result["latency_ms"],
            timestamp=datetime.utcnow().isoformat()
        )
        
    except ValueError as e:
        logger.error(f"❌ Integration execution failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Integration execution error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute integration: {str(e)}"
        )

@router.get("/stats", response_model=MarketplaceStatsResponse)
async def get_marketplace_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get marketplace statistics"""
    logger.info(f"📊 Marketplace stats requested by {current_user.email}")
    
    try:
        # Get basic stats (simplified for demo)
        integrations = await integration_marketplace.get_marketplace_integrations(
            limit=1000,
            db_session=db
        )
        
        total_integrations = len(integrations)
        active_integrations = len([i for i in integrations if i.get("status") == "active"])
        featured_integrations = len([i for i in integrations if i.get("is_featured")])
        
        # Category breakdown
        categories = {}
        for integration in integrations:
            category = integration.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        
        # Top integrations by install count
        top_integrations = sorted(
            integrations,
            key=lambda x: x.get("install_count", 0),
            reverse=True
        )[:10]
        
        return MarketplaceStatsResponse(
            total_integrations=total_integrations,
            active_integrations=active_integrations,
            total_installations=sum(i.get("install_count", 0) for i in integrations),
            featured_integrations=featured_integrations,
            categories=categories,
            top_integrations=top_integrations
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get marketplace stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get marketplace stats: {str(e)}"
        )

@router.get("/{integration_id}/revenue", response_model=RevenueShareResponse)
async def get_integration_revenue(
    integration_id: str,
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get integration revenue share (for developers)"""
    logger.info(f"💰 Revenue share requested for {integration_id} by {current_user.email}")
    
    try:
        # Check if user is the developer of this integration
        from app.models.integration import Integration
        integration = await db.get(Integration, integration_id)
        if not integration or str(integration.developer_id) != str(current_user.id):
            raise HTTPException(
                status_code=403,
                detail="Access denied. You can only view revenue for your own integrations."
            )
        
        # Calculate revenue share
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=period_days)
        
        revenue_data = await integration_marketplace.calculate_revenue_share(
            integration_id=integration_id,
            period_start=period_start,
            period_end=period_end,
            db_session=db
        )
        
        return RevenueShareResponse(**revenue_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get integration revenue: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get integration revenue: {str(e)}"
        )

@router.post("/{integration_id}/approve")
async def approve_integration(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Approve integration for marketplace (admin only)"""
    logger.info(f"✅ Integration approval requested: {integration_id} by {current_user.email}")
    
    try:
        # Check admin permissions
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )
        
        # Approve integration
        integration = await integration_marketplace.approve_integration(
            integration_id=integration_id,
            reviewer_id=str(current_user.id),
            db_session=db
        )
        
        logger.info(f"✅ Integration approved: {integration.name}")
        
        return {
            "status": "approved",
            "integration_id": str(integration.id),
            "name": integration.name,
            "approved_at": integration.approved_at.isoformat(),
            "message": "Integration approved for marketplace"
        }
        
    except ValueError as e:
        logger.error(f"❌ Integration approval failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Integration approval error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to approve integration: {str(e)}"
        )

@router.get("/categories")
async def get_integration_categories():
    """Get available integration categories"""
    return {
        "categories": [
            {
                "value": category.value,
                "label": category.value.replace("_", " ").title()
            }
            for category in IntegrationCategory
        ]
    }

@router.get("/sdk/info")
async def get_sdk_info():
    """Get SDK information for developers"""
    return {
        "sdk_version": "1.0.0",
        "documentation_url": "/docs/integrations/sdk",
        "example_webhook_url": "https://your-app.com/webhooks/cia-integration",
        "supported_actions": [
            "send_notification",
            "sync_data",
            "create_record",
            "update_record",
            "search_records"
        ],
        "configuration_schema_example": {
            "type": "object",
            "properties": {
                "api_key": {"type": "string", "description": "API key for authentication"},
                "webhook_url": {"type": "string", "description": "Webhook URL for notifications"},
                "sync_interval": {"type": "integer", "description": "Sync interval in minutes"}
            },
            "required": ["api_key"]
        }
    }

# Background task functions
async def _update_integration_analytics(
    installation_id: str,
    action: str,
    success: bool,
    latency_ms: int
):
    """Background task to update integration analytics"""
    try:
        # In a real implementation, you would update analytics here
        logger.info(f"📊 Analytics updated for {installation_id}: {action} - {success} - {latency_ms}ms")
        
    except Exception as e:
        logger.error(f"❌ Failed to update integration analytics: {e}")

# Health check
@router.get("/health")
async def integration_marketplace_health():
    """Integration marketplace health check"""
    return {
        "status": "healthy",
        "marketplace": "active",
        "supported_categories": len(IntegrationCategory),
        "timestamp": datetime.utcnow().isoformat()
    }