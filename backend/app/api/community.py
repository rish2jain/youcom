"""
Community Intelligence API

API endpoints for community-driven intelligence validation,
user contributions, reputation system, and expert network.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models.community import CommunityUser, CommunityContribution, CommunityValidation
from app.schemas.community import (
    CommunityUserCreate, CommunityUserUpdate, CommunityUserResponse,
    CommunityContributionCreate, CommunityContributionUpdate, CommunityContributionResponse,
    CommunityValidationCreate, CommunityValidationResponse,
    CommunityInsightCreate, CommunityInsightResponse,
    CommunityChallengeCreate, CommunityChallengeResponse,
    CommunityLeaderboardResponse, CommunityAnalytics,
    CommunitySearchRequest, CommunitySearchResponse
)
from app.services.community_intelligence import CommunityIntelligenceService
from app.services.you_client import YouComOrchestrator
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/community", tags=["community"])


def get_community_service(
    db: Session = Depends(get_db)
) -> CommunityIntelligenceService:
    """Get community intelligence service instance"""
    you_client = YouComOrchestrator()
    return CommunityIntelligenceService(db, you_client)


@router.post("/users", response_model=CommunityUserResponse)
async def create_community_profile(
    profile_data: CommunityUserCreate,
    community_service: CommunityIntelligenceService = Depends(get_community_service),
    current_user = Depends(get_current_user)
):
    """Create or update community user profile"""
    try:
        community_user = await community_service.create_community_user(
            user_id=current_user.id,
            profile_data=profile_data.dict()
        )
        return community_user
        
    except Exception as e:
        logger.error(f"Error creating community profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/me", response_model=CommunityUserResponse)
async def get_my_community_profile(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get current user's community profile"""
    try:
        community_user = db.query(CommunityUser).filter(
            CommunityUser.user_id == current_user.id
        ).first()
        
        if not community_user:
            raise HTTPException(status_code=404, detail="Community profile not found")
        
        return community_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting community profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/me", response_model=CommunityUserResponse)
async def update_my_community_profile(
    profile_update: CommunityUserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update current user's community profile"""
    try:
        community_user = db.query(CommunityUser).filter(
            CommunityUser.user_id == current_user.id
        ).first()
        
        if not community_user:
            raise HTTPException(status_code=404, detail="Community profile not found")
        
        # Update fields
        update_data = profile_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(community_user, field, value)
        
        community_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(community_user)
        
        return community_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating community profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contributions", response_model=CommunityContributionResponse)
async def submit_contribution(
    contribution_data: CommunityContributionCreate,
    background_tasks: BackgroundTasks,
    community_service: CommunityIntelligenceService = Depends(get_community_service),
    current_user = Depends(get_current_user)
):
    """Submit a new community contribution"""
    try:
        contribution = await community_service.submit_contribution(
            user_id=current_user.id,
            contribution_data=contribution_data
        )
        
        # Add background task for AI validation
        background_tasks.add_task(
            community_service.ai_validate_contribution_async,
            contribution.id
        )
        
        return contribution
        
    except Exception as e:
        logger.error(f"Error submitting contribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contributions", response_model=List[CommunityContributionResponse])
async def get_contributions(
    contribution_type: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    validation_status: Optional[str] = Query(None),
    min_quality_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    expert_reviewed_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get community contributions with filtering"""
    try:
        query = db.query(CommunityContribution)
        
        # Apply filters
        if contribution_type:
            query = query.filter(CommunityContribution.contribution_type == contribution_type)
        
        if company:
            query = query.filter(CommunityContribution.company_mentioned.ilike(f"%{company}%"))
        
        if industry:
            query = query.filter(CommunityContribution.industry.ilike(f"%{industry}%"))
        
        if validation_status:
            query = query.filter(CommunityContribution.validation_status == validation_status)
        
        if min_quality_score is not None:
            query = query.filter(CommunityContribution.quality_score >= min_quality_score)
        
        if expert_reviewed_only:
            query = query.filter(CommunityContribution.expert_reviewed == True)
        
        contributions = query.order_by(CommunityContribution.created_at.desc())\
                            .offset(offset)\
                            .limit(limit)\
                            .all()
        
        return contributions
        
    except Exception as e:
        logger.error(f"Error getting contributions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contributions/{contribution_id}", response_model=CommunityContributionResponse)
async def get_contribution(
    contribution_id: int,
    db: Session = Depends(get_db)
):
    """Get specific contribution by ID"""
    try:
        contribution = db.query(CommunityContribution).filter(
            CommunityContribution.id == contribution_id
        ).first()
        
        if not contribution:
            raise HTTPException(status_code=404, detail="Contribution not found")
        
        # Increment view count
        contribution.views += 1
        db.commit()
        
        return contribution
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contributions/{contribution_id}/validate", response_model=CommunityValidationResponse)
async def validate_contribution(
    contribution_id: int,
    validation_data: CommunityValidationCreate,
    community_service: CommunityIntelligenceService = Depends(get_community_service),
    current_user = Depends(get_current_user)
):
    """Submit validation for a contribution"""
    try:
        # Create new validation data with contribution_id instead of mutating
        validation_data_with_id = validation_data.copy(update={"contribution_id": contribution_id})
        
        validation = await community_service.validate_contribution(
            user_id=current_user.id,
            validation_data=validation_data_with_id
        )
        
        return validation
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error validating contribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contributions/{contribution_id}/validations", response_model=List[CommunityValidationResponse])
async def get_contribution_validations(
    contribution_id: int,
    db: Session = Depends(get_db)
):
    """Get all validations for a contribution"""
    try:
        validations = db.query(CommunityValidation).filter(
            CommunityValidation.contribution_id == contribution_id
        ).order_by(CommunityValidation.created_at.desc()).all()
        
        return validations
        
    except Exception as e:
        logger.error(f"Error getting validations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insights", response_model=CommunityInsightResponse)
async def create_community_insight(
    insight_data: CommunityInsightCreate,
    community_service: CommunityIntelligenceService = Depends(get_community_service),
    current_user = Depends(get_current_user)
):
    """Create aggregated community insight"""
    try:
        insight = await community_service.generate_community_insight(
            contribution_ids=insight_data.source_contributions,
            insight_type=insight_data.insight_type,
            title=insight_data.title,
            summary=insight_data.summary
        )
        
        return insight
        
    except Exception as e:
        logger.error(f"Error creating insight: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights", response_model=List[CommunityInsightResponse])
async def get_community_insights(
    insight_type: Optional[str] = Query(None),
    companies: Optional[List[str]] = Query(None),
    industries: Optional[List[str]] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    community_service: CommunityIntelligenceService = Depends(get_community_service)
):
    """Get community insights with filtering"""
    try:
        filters = {}
        if insight_type:
            filters["insight_type"] = insight_type
        if companies:
            filters["companies"] = companies
        if industries:
            filters["industries"] = industries
        if min_confidence is not None:
            filters["min_confidence"] = min_confidence
        
        insights = await community_service.get_community_insights(
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting insights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_leaderboard(
    leaderboard_type: str = Query("monthly"),
    category: str = Query("contributions"),
    limit: int = Query(50, ge=1, le=100),
    community_service: CommunityIntelligenceService = Depends(get_community_service)
):
    """Get community leaderboard"""
    try:
        leaderboard = await community_service.get_leaderboard(
            leaderboard_type=leaderboard_type,
            category=category,
            limit=limit
        )
        
        return leaderboard
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_model=CommunityAnalytics)
async def get_community_analytics(
    community_service: CommunityIntelligenceService = Depends(get_community_service),
    current_user = Depends(get_current_user)
):
    """Get comprehensive community analytics"""
    try:
        analytics = await community_service.get_community_analytics()
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=CommunitySearchResponse)
async def search_community_content(
    search_request: CommunitySearchRequest,
    db: Session = Depends(get_db)
):
    """Search community contributions and insights"""
    try:
        # Build search query
        query = db.query(CommunityContribution)
        
        # Text search (simplified - can be enhanced with full-text search)
        if search_request.query:
            search_term = f"%{search_request.query}%"
            query = query.filter(
                CommunityContribution.title.ilike(search_term) |
                CommunityContribution.content.ilike(search_term)
            )
        
        # Apply filters
        if search_request.contribution_types:
            query = query.filter(
                CommunityContribution.contribution_type.in_(search_request.contribution_types)
            )
        
        if search_request.industries:
            query = query.filter(
                CommunityContribution.industry.in_(search_request.industries)
            )
        
        if search_request.companies:
            query = query.filter(
                CommunityContribution.company_mentioned.in_(search_request.companies)
            )
        
        if search_request.min_quality_score is not None:
            query = query.filter(
                CommunityContribution.quality_score >= search_request.min_quality_score
            )
        
        if search_request.min_validation_count is not None:
            query = query.filter(
                CommunityContribution.validation_count >= search_request.min_validation_count
            )
        
        if search_request.expert_reviewed_only:
            query = query.filter(CommunityContribution.expert_reviewed == True)
        
        if search_request.date_from:
            query = query.filter(CommunityContribution.created_at >= search_request.date_from)
        
        if search_request.date_to:
            query = query.filter(CommunityContribution.created_at <= search_request.date_to)
        
        # Apply sorting
        if search_request.sort_by == "date":
            query = query.order_by(CommunityContribution.created_at.desc())
        elif search_request.sort_by == "quality":
            query = query.order_by(CommunityContribution.quality_score.desc())
        elif search_request.sort_by == "popularity":
            query = query.order_by(CommunityContribution.views.desc())
        else:  # relevance (default)
            query = query.order_by(CommunityContribution.quality_score.desc())
        
        # Get total count
        total_results = query.count()
        
        # Apply pagination
        results = query.offset(search_request.offset)\
                      .limit(search_request.limit)\
                      .all()
        
        # Generate facets (simplified)
        facets = {
            "contribution_types": [
                {"value": "competitive_insight", "count": 45},
                {"value": "market_analysis", "count": 32},
                {"value": "trend_identification", "count": 28}
            ],
            "industries": [
                {"value": "Technology", "count": 67},
                {"value": "Finance", "count": 43},
                {"value": "Healthcare", "count": 29}
            ]
        }
        
        # Generate suggestions (simplified)
        suggestions = ["AI trends", "fintech competition", "SaaS market analysis"]
        
        return CommunitySearchResponse(
            total_results=total_results,
            results=results,
            facets=facets,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error searching community content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contributions/{contribution_id}/share")
async def share_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Share a contribution (increment share count)"""
    try:
        contribution = db.query(CommunityContribution).filter(
            CommunityContribution.id == contribution_id
        ).first()
        
        if not contribution:
            raise HTTPException(status_code=404, detail="Contribution not found")
        
        contribution.shares += 1
        db.commit()
        
        return {"message": "Contribution shared successfully", "shares": contribution.shares}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing contribution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/contributions", response_model=List[CommunityContributionResponse])
async def get_user_contributions(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get contributions by specific user"""
    try:
        # Get community user
        community_user = db.query(CommunityUser).filter(
            CommunityUser.user_id == user_id
        ).first()
        
        if not community_user:
            raise HTTPException(status_code=404, detail="Community user not found")
        
        contributions = db.query(CommunityContribution).filter(
            CommunityContribution.contributor_id == community_user.id
        ).order_by(CommunityContribution.created_at.desc())\
         .offset(offset)\
         .limit(limit)\
         .all()
        
        return contributions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user contributions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending", response_model=List[CommunityContributionResponse])
async def get_trending_contributions(
    timeframe: str = Query("week"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get trending contributions based on engagement"""
    try:
        # Calculate timeframe
        now = datetime.utcnow()
        if timeframe == "day":
            since = now - timedelta(days=1)
        elif timeframe == "week":
            since = now - timedelta(days=7)
        else:  # month
            since = now - timedelta(days=30)
        
        # Get trending contributions (simplified scoring)
        contributions = db.query(CommunityContribution).filter(
            CommunityContribution.created_at >= since
        ).order_by(
            (CommunityContribution.views + 
             CommunityContribution.shares * 3 + 
             CommunityContribution.positive_validations * 5).desc()
        ).limit(limit).all()
        
        return contributions
        
    except Exception as e:
        logger.error(f"Error getting trending contributions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))