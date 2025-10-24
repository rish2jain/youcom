from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
from app.database import get_db
from app.models.impact_card import ImpactCard
from app.models.watch import WatchItem
from app.schemas.impact_card import (
    ImpactCardCreate, 
    ImpactCard as ImpactCardSchema, 
    ImpactCardList,
    ImpactCardGenerate
)
from app.services.you_client import get_you_client, YouComAPIError, YouComOrchestrator
from app.realtime import emit_progress

router = APIRouter(prefix="/impact", tags=["impact-cards"])
logger = logging.getLogger(__name__)


@router.get("/comparison")
async def compare_impact_cards(
    competitors: str,
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Return time-series risk metrics for one or more competitors."""

    competitor_list = [c.strip() for c in competitors.split(",") if c.strip()]
    if not competitor_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Competitors parameter is required")

    cutoff = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(ImpactCard)
        .where(ImpactCard.competitor_name.in_(competitor_list))
        .where(ImpactCard.created_at >= cutoff)
        .order_by(ImpactCard.competitor_name, ImpactCard.created_at)
    )

    items = result.scalars().all()
    series: Dict[str, List[Dict[str, Any]]] = {c: [] for c in competitor_list}

    for card in items:
        series[card.competitor_name].append(
            {
                "created_at": card.created_at.isoformat() if card.created_at else None,
                "risk_score": card.risk_score,
                "credibility_score": card.credibility_score,
                "requires_review": card.requires_review,
                "confidence_score": card.confidence_score,
            }
        )

    return {
        "competitors": competitor_list,
        "days": days,
        "series": series,
    }

@router.post("/generate", response_model=ImpactCardSchema, status_code=status.HTTP_201_CREATED)
async def generate_impact_card(
    request: ImpactCardGenerate,
    db: AsyncSession = Depends(get_db),
    you_client: YouComOrchestrator = Depends(get_you_client),
):
    """Generate a new Impact Card using You.com APIs"""
    try:
        # Generate Impact Card using all 4 You.com APIs
        logger.info(f"🚀 Generating Impact Card for {request.competitor_name}")
        await emit_progress(
            "impact_generation_started",
            {"competitor": request.competitor_name},
        )
        impact_data = await you_client.generate_impact_card(
            competitor=request.competitor_name,
            keywords=request.keywords,
            progress_room="impact_cards",
            db_session=db,
        )
        
        # Create database record
        db_impact_card = ImpactCard(
            watch_item_id=None,  # Can be null for ad-hoc generation
            competitor_name=request.competitor_name,
            risk_score=impact_data["risk_score"],
            risk_level=impact_data["risk_level"],
            confidence_score=impact_data["confidence_score"],
            credibility_score=impact_data.get("credibility_score", 0.0),
            requires_review=impact_data.get("requires_review", False),
            impact_areas=impact_data["impact_areas"],
            key_insights=impact_data["key_insights"],
            recommended_actions=impact_data["recommended_actions"],
            next_steps_plan=impact_data.get("next_steps_plan", []),
            explainability=impact_data.get("explainability", {}),
            total_sources=impact_data["total_sources"],
            source_breakdown=impact_data["source_breakdown"],
            source_quality=impact_data.get("source_quality", {}),
            api_usage=impact_data["api_usage"],
            processing_time=impact_data["processing_time"],
            raw_data=impact_data["raw_data"]
        )
        
        db.add(db_impact_card)
        await db.commit()
        await db.refresh(db_impact_card)
        
        logger.info(f"✅ Impact Card generated successfully for {request.competitor_name}")
        await emit_progress(
            "impact_generation_completed",
            {
                "competitor": request.competitor_name,
                "risk_score": impact_data["risk_score"],
                "risk_level": impact_data["risk_level"],
                "total_sources": impact_data["total_sources"],
            },
        )
        return db_impact_card
        
    except YouComAPIError as e:
        logger.error(f"❌ You.com API error: {str(e)}")
        await emit_progress(
            "impact_generation_failed",
            {"competitor": request.competitor_name, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"You.com API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error generating Impact Card: {str(e)}")
        await emit_progress(
            "impact_generation_failed",
            {"competitor": request.competitor_name, "error": "internal-error"},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Impact Card"
        )

@router.post("/watch/{watch_id}/generate", response_model=ImpactCardSchema, status_code=status.HTTP_201_CREATED)
async def generate_impact_card_for_watch(
    watch_id: int,
    db: AsyncSession = Depends(get_db),
    you_client: YouComOrchestrator = Depends(get_you_client),
):
    """Generate Impact Card for a specific watchlist item"""
    # Get watch item
    result = await db.execute(select(WatchItem).where(WatchItem.id == watch_id))
    watch_item = result.scalar_one_or_none()
    
    if not watch_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch item not found"
        )
    
    try:
        # Generate Impact Card
        logger.info(f"🚀 Generating Impact Card for watch item {watch_id}: {watch_item.competitor_name}")
        await emit_progress(
            "impact_generation_started",
            {"competitor": watch_item.competitor_name},
        )
        impact_data = await you_client.generate_impact_card(
            competitor=watch_item.competitor_name,
            keywords=watch_item.keywords,
            progress_room="impact_cards",
            db_session=db,
        )
        
        # Create database record
        db_impact_card = ImpactCard(
            watch_item_id=watch_id,
            competitor_name=watch_item.competitor_name,
            risk_score=impact_data["risk_score"],
            risk_level=impact_data["risk_level"],
            confidence_score=impact_data["confidence_score"],
            credibility_score=impact_data.get("credibility_score", 0.0),
            requires_review=impact_data.get("requires_review", False),
            impact_areas=impact_data["impact_areas"],
            key_insights=impact_data["key_insights"],
            recommended_actions=impact_data["recommended_actions"],
            next_steps_plan=impact_data.get("next_steps_plan", []),
            explainability=impact_data.get("explainability", {}),
            total_sources=impact_data["total_sources"],
            source_breakdown=impact_data["source_breakdown"],
            source_quality=impact_data.get("source_quality", {}),
            api_usage=impact_data["api_usage"],
            processing_time=impact_data["processing_time"],
            raw_data=impact_data["raw_data"]
        )
        
        db.add(db_impact_card)
        await db.commit()
        await db.refresh(db_impact_card)
        
        logger.info(f"✅ Impact Card generated for watch item {watch_id}")
        await emit_progress(
            "impact_generation_completed",
            {
                "competitor": watch_item.competitor_name,
                "risk_score": impact_data["risk_score"],
                "risk_level": impact_data["risk_level"],
                "total_sources": impact_data["total_sources"],
            },
        )
        return db_impact_card
        
    except YouComAPIError as e:
        logger.error(f"❌ You.com API error: {str(e)}")
        await emit_progress(
            "impact_generation_failed",
            {"competitor": watch_item.competitor_name, "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"You.com API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        await emit_progress(
            "impact_generation_failed",
            {"competitor": watch_item.competitor_name, "error": "internal-error"},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Impact Card"
        )

@router.get("/", response_model=ImpactCardList)
async def get_impact_cards(
    skip: int = 0,
    limit: int = 100,
    competitor: str = None,
    risk_level: str = None,
    min_credibility: float = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all Impact Cards with optional filtering"""
    query = select(ImpactCard)
    
    if competitor:
        query = query.where(ImpactCard.competitor_name.ilike(f"%{competitor}%"))
    
    if risk_level:
        query = query.where(ImpactCard.risk_level == risk_level)

    if min_credibility is not None:
        query = query.where(ImpactCard.credibility_score >= min_credibility)
    
    query = query.offset(skip).limit(limit).order_by(ImpactCard.created_at.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Get total count
    count_query = select(ImpactCard)
    if competitor:
        count_query = count_query.where(ImpactCard.competitor_name.ilike(f"%{competitor}%"))
    if risk_level:
        count_query = count_query.where(ImpactCard.risk_level == risk_level)
    if min_credibility is not None:
        count_query = count_query.where(ImpactCard.credibility_score >= min_credibility)
    
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    return ImpactCardList(items=items, total=total)

@router.get("/{card_id}", response_model=ImpactCardSchema)
async def get_impact_card(
    card_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific Impact Card"""
    result = await db.execute(select(ImpactCard).where(ImpactCard.id == card_id))
    impact_card = result.scalar_one_or_none()
    
    if not impact_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Impact Card not found"
        )
    
    return impact_card

@router.get("/watch/{watch_id}", response_model=ImpactCardList)
async def get_impact_cards_for_watch(
    watch_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get all Impact Cards for a specific watch item"""
    # Verify watch item exists
    result = await db.execute(select(WatchItem).where(WatchItem.id == watch_id))
    watch_item = result.scalar_one_or_none()
    
    if not watch_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watch item not found"
        )
    
    # Get impact cards
    query = select(ImpactCard).where(ImpactCard.watch_item_id == watch_id)
    query = query.offset(skip).limit(limit).order_by(ImpactCard.created_at.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Get total count
    count_query = select(ImpactCard).where(ImpactCard.watch_item_id == watch_id)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    return ImpactCardList(items=items, total=total)
