from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging

from app.database import get_db
from app.models.impact_card import ImpactCard
from app.models.action_recommendation import ActionRecommendation
from app.services.decision_engine import DecisionEngine
from app.schemas.action_recommendation import (
    DecisionEngineRequest,
    DecisionEngineResponse,
    ActionRecommendation as ActionRecommendationSchema,
    ActionRecommendationCreate,
    ActionRecommendationList,
    ActionRecommendationUpdate
)

router = APIRouter(prefix="/decision-engine", tags=["decision-engine"])
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=DecisionEngineResponse)
async def generate_recommendations(
    request: DecisionEngineRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate action recommendations using the Decision Engine."""
    try:
        decision_engine = DecisionEngine(db)
        response = await decision_engine.generate_recommendations(request)
        
        logger.info(f"✅ Generated {response.total_recommendations} recommendations for {request.competitor_name}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error generating recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )

@router.post("/impact-card/{card_id}/generate", response_model=DecisionEngineResponse)
async def generate_recommendations_for_impact_card(
    card_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate recommendations for an existing Impact Card."""
    # Get the impact card
    result = await db.execute(select(ImpactCard).where(ImpactCard.id == card_id))
    impact_card = result.scalar_one_or_none()
    
    if not impact_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact Card not found"
        )
    
    try:
        # Create request from impact card data
        request = DecisionEngineRequest(
            risk_score=impact_card.risk_score,
            competitor_name=impact_card.competitor_name,
            impact_areas=impact_card.impact_areas or [],
            key_insights=impact_card.key_insights or [],
            confidence_score=impact_card.confidence_score,
            context={}
        )
        
        decision_engine = DecisionEngine(db)
        response = await decision_engine.generate_recommendations(request)
        
        # Save recommendations to database
        recommendations = [
            ActionRecommendationCreate(**rec.model_dump()) 
            for rec in response.recommendations
        ]
        await decision_engine.save_recommendations(recommendations, card_id)
        
        logger.info(f"✅ Generated and saved {response.total_recommendations} recommendations for Impact Card {card_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error generating recommendations for Impact Card {card_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations"
        )

@router.get("/recommendations", response_model=ActionRecommendationList)
async def get_action_recommendations(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    priority: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Get action recommendations with optional filtering."""
    query = select(ActionRecommendation)
    
    if category:
        query = query.where(ActionRecommendation.category == category)
    
    if priority:
        query = query.where(ActionRecommendation.priority == priority)
    
    if status:
        query = query.where(ActionRecommendation.status == status)
    
    query = query.offset(skip).limit(limit).order_by(ActionRecommendation.overall_score.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Get total count using SQL COUNT
    from sqlalchemy import func
    count_query = select(func.count()).select_from(ActionRecommendation)
    if category:
        count_query = count_query.where(ActionRecommendation.category == category)
    if priority:
        count_query = count_query.where(ActionRecommendation.priority == priority)
    if status:
        count_query = count_query.where(ActionRecommendation.status == status)
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return ActionRecommendationList(items=items, total=total)

@router.get("/recommendations/{recommendation_id}", response_model=ActionRecommendationSchema)
async def get_action_recommendation(
    recommendation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific action recommendation."""
    result = await db.execute(
        select(ActionRecommendation).where(ActionRecommendation.id == recommendation_id)
    )
    recommendation = result.scalar_one_or_none()
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action recommendation not found"
        )
    
    return recommendation

@router.put("/recommendations/{recommendation_id}", response_model=ActionRecommendationSchema)
async def update_action_recommendation(
    recommendation_id: int,
    update_data: ActionRecommendationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an action recommendation."""
    result = await db.execute(
        select(ActionRecommendation).where(ActionRecommendation.id == recommendation_id)
    )
    recommendation = result.scalar_one_or_none()
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action recommendation not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(recommendation, field, value)
    
    await db.commit()
    await db.refresh(recommendation)
    
    logger.info(f"✅ Updated action recommendation {recommendation_id}")
    return recommendation

@router.get("/impact-card/{card_id}/recommendations", response_model=ActionRecommendationList)
async def get_recommendations_for_impact_card(
    card_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all action recommendations for a specific Impact Card."""
    # Verify impact card exists
    result = await db.execute(select(ImpactCard).where(ImpactCard.id == card_id))
    impact_card = result.scalar_one_or_none()
    
    if not impact_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact Card not found"
        )
    
    # Get recommendations
    query = select(ActionRecommendation).where(ActionRecommendation.impact_card_id == card_id)
    query = query.order_by(ActionRecommendation.overall_score.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return ActionRecommendationList(items=items, total=len(items))