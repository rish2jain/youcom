"""
Learning Loop API endpoints for tracking alert outcomes and generating insights.
Implements the feedback loop to improve competitive intelligence monitoring.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, func, select

from ..database import get_db
from ..models.learning import AlertOutcome, LearningInsight
from ..schemas.learning import (
    AlertOutcomeCreate,
    AlertOutcomeResponse,
    LearningInsightResponse,
    ApplyInsightRequest
)
from ..services.learning_service import LearningService

router = APIRouter(prefix="/learning", tags=["learning"])

@router.post("/outcomes", response_model=AlertOutcomeResponse)
async def record_alert_outcome(
    outcome_data: AlertOutcomeCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Record the outcome of an alert (acted upon, dismissed, etc.)
    This feeds into the learning loop to improve future monitoring.
    """
    try:
        # Create new alert outcome record
        outcome = AlertOutcome(
            alert_id=outcome_data.alert_id,
            competitor_name=outcome_data.competitor_name,
            action_taken=outcome_data.action_taken,
            outcome_quality=outcome_data.outcome_quality,
            user_feedback=outcome_data.user_feedback,
            business_impact=outcome_data.business_impact,
            created_at=datetime.utcnow()
        )
        
        db.add(outcome)
        await db.commit()
        await db.refresh(outcome)
        
        # Trigger learning insight generation asynchronously
        learning_service = LearningService(db)
        await learning_service.generate_insights_async(outcome_data.competitor_name)
        
        return AlertOutcomeResponse.model_validate(outcome)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record outcome: {str(e)}")

@router.get("/outcomes", response_model=List[AlertOutcomeResponse])
async def get_alert_outcomes(
    competitor: Optional[str] = Query(None, description="Filter by competitor name"),
    limit: int = Query(50, le=100, description="Maximum number of outcomes to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve alert outcomes for analysis and display.
    """
    try:
        query = select(AlertOutcome).order_by(desc(AlertOutcome.created_at))
        
        if competitor:
            query = query.where(AlertOutcome.competitor_name.ilike(f"%{competitor}%"))
            
        query = query.limit(limit)
        result = await db.execute(query)
        outcomes = result.scalars().all()
        
        return [AlertOutcomeResponse.model_validate(outcome) for outcome in outcomes]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch outcomes: {str(e)}")

@router.get("/insights", response_model=dict)
async def get_learning_insights(
    competitor: Optional[str] = Query(None, description="Filter by competitor name"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-generated learning insights based on alert outcomes.
    These insights suggest improvements to monitoring thresholds, keywords, etc.
    """
    try:
        learning_service = LearningService(db)
        insights = await learning_service.generate_insights(competitor)
        
        return {
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat(),
            "competitor_filter": competitor
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate insights: {str(e)}")

@router.post("/apply")
async def apply_learning_insight(
    insight_request: ApplyInsightRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply a learning insight to update monitoring configuration.
    This closes the learning loop by automatically improving the system.
    """
    try:
        learning_service = LearningService(db)
        result = await learning_service.apply_insight(insight_request)
        
        return {
            "success": True,
            "message": f"Applied {insight_request.type} insight for {insight_request.competitor}",
            "changes": result
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to apply insight: {str(e)}")

@router.get("/metrics")
async def get_learning_metrics(
    days: int = Query(30, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get learning loop performance metrics.
    """
    try:
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Calculate key metrics using async queries
        total_query = select(func.count(AlertOutcome.id)).where(
            AlertOutcome.created_at >= since_date
        )
        total_result = await db.execute(total_query)
        total_outcomes = total_result.scalar() or 0
        
        helpful_query = select(func.count(AlertOutcome.id)).where(
            AlertOutcome.created_at >= since_date,
            AlertOutcome.outcome_quality == "helpful"
        )
        helpful_result = await db.execute(helpful_query)
        helpful_outcomes = helpful_result.scalar() or 0
        
        acted_query = select(func.count(AlertOutcome.id)).where(
            AlertOutcome.created_at >= since_date,
            AlertOutcome.action_taken == "acted_upon"
        )
        acted_result = await db.execute(acted_query)
        acted_upon = acted_result.scalar() or 0
        
        false_positive_query = select(func.count(AlertOutcome.id)).where(
            AlertOutcome.created_at >= since_date,
            AlertOutcome.outcome_quality == "false_positive"
        )
        false_positive_result = await db.execute(false_positive_query)
        false_positives = false_positive_result.scalar() or 0
        
        # Calculate rates
        helpful_rate = (helpful_outcomes / total_outcomes * 100) if total_outcomes > 0 else 0
        action_rate = (acted_upon / total_outcomes * 100) if total_outcomes > 0 else 0
        false_positive_rate = (false_positives / total_outcomes * 100) if total_outcomes > 0 else 0
        
        # Get top competitors by feedback volume
        top_competitors_query = select(
            AlertOutcome.competitor_name,
            func.count(AlertOutcome.id).label("feedback_count")
        ).where(
            AlertOutcome.created_at >= since_date
        ).group_by(
            AlertOutcome.competitor_name
        ).order_by(
            desc("feedback_count")
        ).limit(5)
        
        top_competitors_result = await db.execute(top_competitors_query)
        top_competitors = top_competitors_result.all()
        
        return {
            "period_days": days,
            "total_outcomes": total_outcomes,
            "helpful_rate": round(helpful_rate, 1),
            "action_rate": round(action_rate, 1),
            "false_positive_rate": round(false_positive_rate, 1),
            "top_competitors": [
                {"name": comp[0], "feedback_count": comp[1]} 
                for comp in top_competitors
            ],
            "learning_effectiveness": {
                "signal_to_noise": round(100 - false_positive_rate, 1),
                "user_satisfaction": round(helpful_rate, 1),
                "actionability": round(action_rate, 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate metrics: {str(e)}")

@router.get("/recommendations")
async def get_monitoring_recommendations(
    competitor: Optional[str] = Query(None, description="Get recommendations for specific competitor"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-powered recommendations for improving monitoring effectiveness.
    """
    try:
        learning_service = LearningService(db)
        recommendations = await learning_service.get_recommendations(competitor)
        
        return {
            "recommendations": recommendations,
            "competitor": competitor,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")