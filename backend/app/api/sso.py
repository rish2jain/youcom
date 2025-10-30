"""
SSO API Endpoints - Week 1 Implementation
Google, Azure AD, and Okta SSO authentication endpoints.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.sso_service import sso_service, SSOError
from app.services.auth_service import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/sso", tags=["SSO Authentication"])

# Request/Response Models
class SSOProvidersResponse(BaseModel):
    available_providers: List[str]
    total_providers: int
    configured_providers: int
    status: str

class SSOAuthURLResponse(BaseModel):
    auth_url: str
    state: str
    provider: str
    expires_in: int = 600  # 10 minutes

class SSOCallbackResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    provider: str
    message: str

class SSOStatusResponse(BaseModel):
    available_providers: List[str]
    active_states: int
    status: str

@router.get("/providers", response_model=SSOProvidersResponse)
async def get_sso_providers():
    """Get available SSO providers"""
    logger.info("📋 SSO providers requested")
    
    try:
        status = await sso_service.get_sso_status()
        
        return SSOProvidersResponse(
            available_providers=status["available_providers"],
            total_providers=status["total_providers"],
            configured_providers=status["configured_providers"],
            status=status["status"]
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get SSO providers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get SSO providers: {str(e)}"
        )

@router.get("/auth/{provider}", response_model=SSOAuthURLResponse)
async def initiate_sso_auth(
    provider: str,
    workspace_id: Optional[str] = Query(None, description="Workspace ID to join after authentication")
):
    """Initiate SSO authentication flow"""
    logger.info(f"🔐 SSO authentication initiated for provider: {provider}")
    
    try:
        # Validate provider
        available_providers = sso_service.get_available_providers()
        if provider not in available_providers:
            raise HTTPException(
                status_code=400,
                detail=f"SSO provider '{provider}' is not available. Available providers: {available_providers}"
            )
        
        # Generate SSO URL
        auth_url, state = sso_service.generate_sso_url(provider, workspace_id)
        
        logger.info(f"✅ SSO auth URL generated for {provider}")
        
        return SSOAuthURLResponse(
            auth_url=auth_url,
            state=state,
            provider=provider
        )
        
    except SSOError as e:
        logger.error(f"❌ SSO initiation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"SSO authentication failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ SSO initiation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate SSO authentication: {str(e)}"
        )

@router.get("/callback/{provider}")
async def handle_sso_callback(
    provider: str,
    code: str = Query(..., description="Authorization code from SSO provider"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    error: Optional[str] = Query(None, description="Error from SSO provider"),
    error_description: Optional[str] = Query(None, description="Error description"),
    db: AsyncSession = Depends(get_db)
):
    """Handle SSO callback from provider"""
    logger.info(f"🔄 SSO callback received for provider: {provider}")
    
    # Check for errors from SSO provider
    if error:
        logger.error(f"❌ SSO provider error: {error} - {error_description}")
        raise HTTPException(
            status_code=400,
            detail=f"SSO authentication failed: {error_description or error}"
        )
    
    try:
        # Handle SSO callback
        user, access_token = await sso_service.handle_sso_callback(
            provider, code, state, db
        )
        
        logger.info(f"✅ SSO authentication successful for {user.email} via {provider}")
        
        # In a real application, you might want to redirect to the frontend
        # with the token or set it as a secure cookie
        return SSOCallbackResponse(
            user=user,
            access_token=access_token,
            provider=provider,
            message=f"Successfully authenticated via {provider}"
        )
        
    except SSOError as e:
        logger.error(f"❌ SSO callback failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"SSO authentication failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ SSO callback error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process SSO callback: {str(e)}"
        )

@router.get("/status", response_model=SSOStatusResponse)
async def get_sso_status(
    current_user: User = Depends(get_current_user)
):
    """Get SSO service status (authenticated endpoint)"""
    logger.info(f"📊 SSO status requested by {current_user.email}")
    
    try:
        status = await sso_service.get_sso_status()
        
        return SSOStatusResponse(
            available_providers=status["available_providers"],
            active_states=status["active_states"],
            status=status["status"]
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get SSO status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get SSO status: {str(e)}"
        )

@router.post("/cleanup")
async def cleanup_expired_states(
    current_user: User = Depends(get_current_user)
):
    """Cleanup expired SSO states (admin endpoint)"""
    logger.info(f"🧹 SSO cleanup requested by {current_user.email}")
    
    try:
        # Only allow admin users to cleanup
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin access required"
            )
        
        sso_service.cleanup_expired_states()
        
        return {
            "status": "cleanup_completed",
            "message": "Expired SSO states cleaned up",
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"❌ SSO cleanup failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup SSO states: {str(e)}"
        )

# Google SSO specific endpoints
@router.get("/google/auth")
async def google_sso_auth(
    workspace_id: Optional[str] = Query(None)
):
    """Initiate Google SSO authentication"""
    return await initiate_sso_auth("google", workspace_id)

@router.get("/google/callback")
async def google_sso_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle Google SSO callback"""
    return await handle_sso_callback("google", code, state, error, error_description, db)

# Azure AD SSO specific endpoints
@router.get("/azure/auth")
async def azure_sso_auth(
    workspace_id: Optional[str] = Query(None)
):
    """Initiate Azure AD SSO authentication"""
    return await initiate_sso_auth("azure", workspace_id)

@router.get("/azure/callback")
async def azure_sso_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle Azure AD SSO callback"""
    return await handle_sso_callback("azure", code, state, error, error_description, db)

# Okta SSO specific endpoints
@router.get("/okta/auth")
async def okta_sso_auth(
    workspace_id: Optional[str] = Query(None)
):
    """Initiate Okta SSO authentication"""
    return await initiate_sso_auth("okta", workspace_id)

@router.get("/okta/callback")
async def okta_sso_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle Okta SSO callback"""
    return await handle_sso_callback("okta", code, state, error, error_description, db)

# Frontend redirect endpoints (for better UX)
@router.get("/redirect/{provider}")
async def sso_redirect(
    provider: str,
    workspace_id: Optional[str] = Query(None)
):
    """Redirect to SSO provider (for frontend integration)"""
    try:
        auth_url, state = sso_service.generate_sso_url(provider, workspace_id)
        return RedirectResponse(url=auth_url, status_code=302)
        
    except Exception as e:
        logger.error(f"❌ SSO redirect failed: {str(e)}")
        # Redirect to frontend error page
        error_url = f"/auth/error?message={str(e)}&provider={provider}"
        return RedirectResponse(url=error_url, status_code=302)

# Health check endpoint
@router.get("/health")
async def sso_health_check():
    """SSO service health check"""
    try:
        status = await sso_service.get_sso_status()
        
        return {
            "status": "healthy" if status["available_providers"] else "no_providers",
            "available_providers": status["available_providers"],
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"❌ SSO health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }