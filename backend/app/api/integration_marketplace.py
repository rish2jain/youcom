"""
Integration Marketplace API

API endpoints for third-party integrations, developer ecosystem,
and revenue sharing marketplace.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging

from app.database import get_db
from app.models.integration_marketplace import (
    IntegrationDeveloper, MarketplaceIntegration, MarketplaceIntegrationInstallation,
    IntegrationReview, IntegrationAnalytics, IntegrationSupport
)
from app.services.integration_marketplace import IntegrationMarketplaceService
from app.services.auth_service import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin access and return current user"""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def get_marketplace_service(db: Session = Depends(get_db)) -> IntegrationMarketplaceService:
    """Get integration marketplace service instance"""
    return IntegrationMarketplaceService(db)


# Developer Management Endpoints

@router.post("/developers/register", response_model=Dict[str, Any])
async def register_developer(
    developer_data: Dict[str, Any],
    marketplace_service: IntegrationMarketplaceService = Depends(get_marketplace_service),
    current_user = Depends(get_current_user)
):
    """Register as a developer in the marketplace"""
    try:
        developer = await marketplace_service.register_developer(developer_data)
        
        return {
            "id": developer.id,
            "developer_name": developer.developer_name,
            "email": developer.email,
            "tier": developer.tier,
            "api_key": developer.api_key,
            "revenue_share_percentage": developer.revenue_share_percentage,
            "created_at": developer.created_at.isoformat(),
            "message": "Developer registered successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering developer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/developers/me", response_model=Dict[str, Any])
async def get_my_developer_profile(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current user's developer profile"""
    try:
        developer = db.query(IntegrationDeveloper).filter(
            IntegrationDeveloper.email == current_user.email
        ).first()
        
        if not developer:
            raise HTTPException(status_code=404, detail="Developer profile not found")
        
        return {
            "id": developer.id,
            "developer_name": developer.developer_name,
            "company_name": developer.company_name,
            "email": developer.email,
            "website": developer.website,
            "bio": developer.bio,
            "tier": developer.tier,
            "verified": developer.verified,
            "total_integrations": developer.total_integrations,
            "published_integrations": developer.published_integrations,
            "total_installs": developer.total_installs,
            "average_rating": developer.average_rating,
            "total_earnings": developer.total_earnings,
            "revenue_share_percentage": developer.revenue_share_percentage,
            "api_quota_per_month": developer.api_quota_per_month,
            "api_calls_used": developer.api_calls_used,
            "created_at": developer.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting developer profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Integration Management Endpoints

@router.post("/integrations", response_model=Dict[str, Any])
async def create_integration(
    integration_data: Dict[str, Any],
    marketplace_service: IntegrationMarketplaceService = Depends(get_marketplace_service),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new integration"""
    try:
        # Get developer ID
        developer = db.query(IntegrationDeveloper).filter(
            IntegrationDeveloper.email == current_user.email
        ).first()
        
        if not developer:
            raise HTTPException(status_code=404, detail="Developer profile not found")
        
        integration = await marketplace_service.create_integration(
            developer.id, integration_data
        )
        
        return {
            "id": integration.id,
            "name": integration.name,
            "slug": integration.slug,
            "category": integration.category,
            "status": integration.status,
            "version": integration.version,
            "pricing_model": integration.pricing_model,
            "price": integration.price,
            "created_at": integration.created_at.isoformat(),
            "message": "Integration created successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations", response_model=Dict[str, Any])
async def search_integrations(
    query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    pricing_model: Optional[str] = Query(None),
    featured_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    marketplace_service: IntegrationMarketplaceService = Depends(get_marketplace_service)
):
    """Search integrations in marketplace"""
    try:
        results = await marketplace_service.search_integrations(
            query=query,
            category=category,
            pricing_model=pricing_model,
            featured_only=featured_only,
            limit=limit,
            offset=offset
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching integrations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/{integration_id}", response_model=Dict[str, Any])
async def get_integration_details(
    integration_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about an integration"""
    try:
        integration = db.query(MarketplaceIntegration).filter(
            MarketplaceIntegration.id == integration_id
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        # Get recent reviews
        recent_reviews = db.query(IntegrationReview).filter(
            IntegrationReview.integration_id == integration_id
        ).order_by(IntegrationReview.created_at.desc()).limit(5).all()
        
        return {
            "id": integration.id,
            "name": integration.name,
            "slug": integration.slug,
            "description": integration.description,
            "short_description": integration.short_description,
            "category": integration.category,
            "tags": integration.tags,
            "version": integration.version,
            "changelog": integration.changelog,
            "icon_url": integration.icon_url,
            "banner_url": integration.banner_url,
            "screenshots": integration.screenshots,
            "pricing_model": integration.pricing_model,
            "price": integration.price,
            "trial_days": integration.trial_days,
            "minimum_plan": integration.minimum_plan,
            "supported_events": integration.supported_events,
            "configuration_schema": integration.configuration_schema,
            "total_installs": integration.total_installs,
            "active_installs": integration.active_installs,
            "average_rating": integration.average_rating,
            "total_reviews": integration.total_reviews,
            "featured": integration.featured,
            "status": integration.status,
            "published_at": integration.published_at.isoformat() if integration.published_at else None,
            "developer": {
                "id": integration.developer.id,
                "name": integration.developer.developer_name,
                "company": integration.developer.company_name,
                "verified": integration.developer.verified,
                "website": integration.developer.website
            },
            "recent_reviews": [
                {
                    "id": review.id,
                    "rating": review.rating,
                    "title": review.title,
                    "review_text": review.review_text,
                    "verified_purchase": review.verified_purchase,
                    "helpful_votes": review.helpful_votes,
                    "created_at": review.created_at.isoformat()
                }
                for review in recent_reviews
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting integration details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/{integration_id}/submit-review", response_model=Dict[str, Any])
async def submit_integration_for_review(
    integration_id: int,
    marketplace_service: IntegrationMarketplaceService = Depends(get_marketplace_service),
    current_user = Depends(get_current_user)
):
    """Submit integration for marketplace review"""
    try:
        integration = await marketplace_service.submit_for_review(integration_id)
        
        return {
            "id": integration.id,
            "name": integration.name,
            "status": integration.status,
            "updated_at": integration.updated_at.isoformat(),
            "message": "Integration submitted for review"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting integration for review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/{integration_id}/approve", response_model=Dict[str, Any])
async def approve_integration(
    integration_id: int,
    review_data: Dict[str, Any],
    marketplace_service: IntegrationMarketplaceService = Depends(get_marketplace_service),
    current_user: User = Depends(require_admin)
):
    """Approve integration for marketplace (admin only)"""
    try:
        
        integration = await marketplace_service.approve_integration(
            integration_id,
            current_user.id,
            review_data.get("review_notes")
        )
        
        return {
            "id": integration.id,
            "name": integration.name,
            "status": integration.status,
            "approved_by": integration.approved_by,
            "approved_at": integration.approved_at.isoformat(),
            "message": "Integration approved"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Installation Management Endpoints

@router.post("/integrations/{integration_id}/install", response_model=Dict[str, Any])
async def install_integration(
    integration_id: int,
    installation_data: Dict[str, Any],
    marketplace_service: IntegrationMarketplaceService = Depends(get_marketplace_service),
    current_user = Depends(get_current_user)
):
    """Install an integration"""
    try:
        installation = await marketplace_service.install_integration(
            integration_id=integration_id,
            user_id=current_user.id,
            workspace_id=installation_data.get("workspace_id"),
            configuration=installation_data.get("configuration", {})
        )
        
        return {
            "id": installation.id,
            "integration_id": installation.integration_id,
            "user_id": installation.user_id,
            "workspace_id": installation.workspace_id,
            "status": installation.status,
            "subscription_id": installation.subscription_id,
            "installed_at": installation.installed_at.isoformat(),
            "message": "Integration installed successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error installing integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/installations/{installation_id}", response_model=Dict[str, Any])
async def uninstall_integration(
    installation_id: int,
    marketplace_service: IntegrationMarketplaceService = Depends(get_marketplace_service),
    current_user = Depends(get_current_user)
):
    """Uninstall an integration"""
    try:
        success = await marketplace_service.uninstall_integration(
            installation_id, current_user.id
        )
        
        return {
            "success": success,
            "message": "Integration uninstalled successfully"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uninstalling integration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/installations", response_model=List[Dict[str, Any]])
async def get_my_installations(
    workspace_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user's installed integrations"""
    try:
        query = db.query(MarketplaceIntegrationInstallation).filter(
            MarketplaceIntegrationInstallation.user_id == current_user.id
        )
        
        if workspace_id:
            query = query.filter(MarketplaceIntegrationInstallation.workspace_id == workspace_id)
        
        if status:
            query = query.filter(MarketplaceIntegrationInstallation.status == status)
        
        installations = query.order_by(MarketplaceIntegrationInstallation.installed_at.desc()).all()
        
        return [
            {
                "id": installation.id,
                "integration": {
                    "id": installation.integration.id,
                    "name": installation.integration.name,
                    "slug": installation.integration.slug,
                    "icon_url": installation.integration.icon_url,
                    "category": installation.integration.category,
                    "version": installation.integration.version
                },
                "workspace_id": installation.workspace_id,
                "status": installation.status,
                "enabled": installation.enabled,
                "last_used": installation.last_used.isoformat() if installation.last_used else None,
                "total_api_calls": installation.total_api_calls,
                "billing_status": installation.billing_status,
                "installed_at": installation.installed_at.isoformat()
            }
            for installation in installations
        ]
        
    except Exception as e:
        logger.error(f"Error getting installations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Review and Rating Endpoints

@router.post("/integrations/{integration_id}/reviews", response_model=Dict[str, Any])
async def create_integration_review(
    integration_id: int,
    review_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a review for an integration"""
    try:
        # Check if user has installed the integration
        installation = db.query(MarketplaceIntegrationInstallation).filter(
            and_(
                MarketplaceIntegrationInstallation.integration_id == integration_id,
                MarketplaceIntegrationInstallation.user_id == current_user.id
            )
        ).first()
        
        verified_purchase = installation is not None
        
        # Check if user already reviewed
        existing_review = db.query(IntegrationReview).filter(
            and_(
                IntegrationReview.integration_id == integration_id,
                IntegrationReview.user_id == current_user.id
            )
        ).first()
        
        if existing_review:
            raise HTTPException(status_code=400, detail="You have already reviewed this integration")
        
        # Create review
        review = IntegrationReview(
            integration_id=integration_id,
            user_id=current_user.id,
            rating=review_data["rating"],
            title=review_data.get("title"),
            review_text=review_data.get("review_text"),
            verified_purchase=verified_purchase
        )
        
        db.add(review)
        
        # Update integration rating atomically in database
        from sqlalchemy import update
        db.execute(
            update(MarketplaceIntegration)
            .where(MarketplaceIntegration.id == integration_id)
            .values(
                total_reviews=MarketplaceIntegration.total_reviews + 1,
                average_rating=(MarketplaceIntegration.average_rating * MarketplaceIntegration.total_reviews + review_data["rating"]) / (MarketplaceIntegration.total_reviews + 1)
            )
        )
        
        db.commit()
        db.refresh(review)
        
        return {
            "id": review.id,
            "integration_id": review.integration_id,
            "rating": review.rating,
            "title": review.title,
            "verified_purchase": review.verified_purchase,
            "created_at": review.created_at.isoformat(),
            "message": "Review created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/{integration_id}/reviews", response_model=List[Dict[str, Any]])
async def get_integration_reviews(
    integration_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("newest"),
    db: Session = Depends(get_db)
):
    """Get reviews for an integration"""
    try:
        query = db.query(IntegrationReview).filter(
            IntegrationReview.integration_id == integration_id
        )
        
        # Apply sorting
        if sort_by == "newest":
            query = query.order_by(IntegrationReview.created_at.desc())
        elif sort_by == "oldest":
            query = query.order_by(IntegrationReview.created_at.asc())
        elif sort_by == "rating_high":
            query = query.order_by(IntegrationReview.rating.desc())
        elif sort_by == "rating_low":
            query = query.order_by(IntegrationReview.rating.asc())
        elif sort_by == "helpful":
            query = query.order_by(IntegrationReview.helpful_votes.desc())
        
        reviews = query.offset(offset).limit(limit).all()
        
        return [
            {
                "id": review.id,
                "rating": review.rating,
                "title": review.title,
                "review_text": review.review_text,
                "verified_purchase": review.verified_purchase,
                "helpful_votes": review.helpful_votes,
                "total_votes": review.total_votes,
                "developer_response": review.developer_response,
                "developer_response_date": review.developer_response_date.isoformat() if review.developer_response_date else None,
                "created_at": review.created_at.isoformat()
            }
            for review in reviews
        ]
        
    except Exception as e:
        logger.error(f"Error getting reviews: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Endpoints

@router.get("/integrations/{integration_id}/analytics", response_model=Dict[str, Any])
async def get_integration_analytics(
    integration_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    marketplace_service: IntegrationMarketplaceService = Depends(get_marketplace_service),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get analytics for an integration (developer only)"""
    try:
        # Check if user is the developer of this integration
        integration = db.query(MarketplaceIntegration).filter(MarketplaceIntegration.id == integration_id).first()
        if not integration:
            raise HTTPException(status_code=404, detail="Integration not found")
        
        developer = db.query(IntegrationDeveloper).filter(
            IntegrationDeveloper.email == current_user.email
        ).first()
        
        if not developer or integration.developer_id != developer.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        
        analytics = await marketplace_service.get_integration_analytics(
            integration_id, start_dt, end_dt
        )
        
        return analytics
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting integration analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Marketplace Statistics

@router.get("/stats", response_model=Dict[str, Any])
async def get_marketplace_stats(
    db: Session = Depends(get_db)
):
    """Get marketplace statistics"""
    try:
        # Get basic counts
        total_integrations = db.query(MarketplaceIntegration).filter(
            MarketplaceIntegration.status == "published"
        ).count()
        
        total_developers = db.query(IntegrationDeveloper).count()
        
        total_installs = db.query(func.sum(MarketplaceIntegration.total_installs)).scalar() or 0
        
        # Get category breakdown
        category_stats = db.query(
            MarketplaceIntegration.category,
            func.count(MarketplaceIntegration.id).label("count")
        ).filter(
            MarketplaceIntegration.status == "published"
        ).group_by(MarketplaceIntegration.category).all()
        
        # Get featured integrations
        featured_integrations = db.query(MarketplaceIntegration).filter(
            and_(
                MarketplaceIntegration.status == "published",
                MarketplaceIntegration.featured == True
            )
        ).limit(6).all()
        
        return {
            "overview": {
                "total_integrations": total_integrations,
                "total_developers": total_developers,
                "total_installs": total_installs,
                "average_rating": 4.2  # Would calculate from actual data
            },
            "categories": [
                {
                    "category": stat.category,
                    "count": stat.count
                }
                for stat in category_stats
            ],
            "featured_integrations": [
                {
                    "id": integration.id,
                    "name": integration.name,
                    "slug": integration.slug,
                    "short_description": integration.short_description,
                    "icon_url": integration.icon_url,
                    "category": integration.category,
                    "average_rating": integration.average_rating,
                    "total_installs": integration.total_installs,
                    "developer_name": integration.developer.developer_name
                }
                for integration in featured_integrations
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting marketplace stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Revenue Sharing

@router.post("/revenue/process-payouts", response_model=Dict[str, Any])
async def process_revenue_payouts(
    background_tasks: BackgroundTasks,
    marketplace_service: IntegrationMarketplaceService = Depends(get_marketplace_service),
    current_user: User = Depends(require_admin)
):
    """Process revenue sharing payouts (admin only)"""
    try:
        
        # Process payouts in background
        background_tasks.add_task(
            marketplace_service.process_revenue_sharing
        )
        
        return {
            "message": "Revenue payout processing started",
            "started_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing payouts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/developers/me/earnings", response_model=Dict[str, Any])
async def get_my_earnings(
    period: str = Query("30d"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get developer earnings summary"""
    try:
        developer = db.query(IntegrationDeveloper).filter(
            IntegrationDeveloper.email == current_user.email
        ).first()
        
        if not developer:
            raise HTTPException(status_code=404, detail="Developer profile not found")
        
        # Calculate date range
        now = datetime.utcnow()
        if period == "7d":
            start_date = now - timedelta(days=7)
        elif period == "30d":
            start_date = now - timedelta(days=30)
        elif period == "90d":
            start_date = now - timedelta(days=90)
        elif period == "1y":
            start_date = now - timedelta(days=365)
        else:  # all
            start_date = datetime(2020, 1, 1)
        
        # Get earnings data (simplified)
        return {
            "developer_id": developer.id,
            "period": period,
            "total_earnings": developer.total_earnings,
            "revenue_share_percentage": developer.revenue_share_percentage,
            "period_earnings": developer.total_earnings * 0.1,  # Mock data
            "pending_payout": developer.total_earnings * 0.05,  # Mock data
            "integrations": [
                {
                    "name": integration.name,
                    "total_installs": integration.total_installs,
                    "revenue": integration.total_revenue,
                    "earnings": integration.total_revenue * (developer.revenue_share_percentage / 100)
                }
                for integration in developer.integrations
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting earnings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))