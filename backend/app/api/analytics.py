"""Predictive analytics API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.analytics_service import get_analytics_service
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/competitor-trends/{competitor_name}")
async def get_competitor_trends(
    competitor_name: str,
    days_back: int = Query(30, ge=7, le=365, description="Days to analyze (7-365)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get predictive trends for a specific competitor"""
    
    analytics_service = get_analytics_service()
    result = await analytics_service.analyze_competitor_trends(
        competitor_name, days_back, db
    )
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail=f"Trend analysis failed: {result['error']}"
        )
    
    return result


@router.get("/market-landscape")
async def get_market_landscape(
    days_back: int = Query(30, ge=7, le=365, description="Days to analyze (7-365)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get overall market landscape analysis"""
    
    analytics_service = get_analytics_service()
    result = await analytics_service.market_landscape_analysis(days_back, db)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail=f"Market analysis failed: {result['error']}"
        )
    
    return result


@router.get("/api-usage-predictions")
async def get_api_usage_predictions(
    days_back: int = Query(30, ge=7, le=365, description="Days to analyze (7-365)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get API usage predictions and cost estimates"""
    
    analytics_service = get_analytics_service()
    result = await analytics_service.api_usage_predictions(days_back, db)
    
    if result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail=f"Usage prediction failed: {result['error']}"
        )
    
    return result


@router.get("/executive-summary")
async def get_executive_summary(
    days_back: int = Query(30, ge=7, le=90, description="Days to analyze (7-90)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get executive summary with key insights and recommendations"""
    
    analytics_service = get_analytics_service()
    
    # Get market landscape
    market_result = await analytics_service.market_landscape_analysis(days_back, db)
    if market_result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail=f"Executive summary failed: {market_result['error']}"
        )
    
    # Get API usage predictions
    usage_result = await analytics_service.api_usage_predictions(days_back, db)
    
    # Validate usage result
    if usage_result.get("status") != "success":
        raise HTTPException(
            status_code=400,
            detail=f"API usage analysis failed: {usage_result.get('error', 'Unknown error')}"
        )
    
    # Compile executive summary
    market_data = market_result.get("market_overview", {})
    top_competitors = market_result.get("top_competitors", [])
    
    # Safely extract usage data
    total_api_calls = usage_result.get("current_usage", {}).get("total_api_calls", 0)
    estimated_monthly_cost = usage_result.get("predictions", {}).get("estimated_monthly_cost", 0)
    
    summary = {
        "period": f"Last {days_back} days",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "key_metrics": {
            "total_competitive_activities": market_data.get("total_competitive_activities", 0),
            "market_temperature": market_data.get("market_temperature", "unknown"),
            "unique_competitors_tracked": market_data.get("unique_competitors", 0),
            "average_market_risk": market_data.get("average_market_risk", 0)
        },
        "top_threats": top_competitors[:3],
        "strategic_recommendations": _generate_executive_recommendations(market_data, top_competitors),
        "api_efficiency": {
            "total_api_calls": total_api_calls,
            "predicted_monthly_cost": estimated_monthly_cost
        }
    }
    
    return {
        "status": "success",
        "executive_summary": summary
    }


def _generate_executive_recommendations(market_data: Dict[str, Any], top_competitors: list) -> list:
    """Generate strategic recommendations for executives"""
    
    recommendations = []
    
    market_temp = market_data.get("market_temperature", "unknown")
    avg_risk = market_data.get("average_market_risk", 0)
    competitor_count = market_data.get("unique_competitors", 0)
    
    # Market temperature recommendations
    if market_temp == "hot":
        recommendations.append({
            "priority": "high",
            "category": "defensive",
            "action": "Accelerate product development and competitive differentiation",
            "rationale": "High competitive activity requires immediate defensive measures"
        })
    elif market_temp == "cool":
        recommendations.append({
            "priority": "medium",
            "category": "offensive", 
            "action": "Consider aggressive market expansion and feature launches",
            "rationale": "Low competitive pressure creates opportunity for market share gains"
        })
    
    # Risk-based recommendations
    if avg_risk > 70:
        recommendations.append({
            "priority": "high",
            "category": "strategic",
            "action": "Conduct comprehensive competitive response planning",
            "rationale": f"Average market risk of {avg_risk} indicates significant threats"
        })
    
    # Competitor-specific recommendations
    if top_competitors:
        top_threat = top_competitors[0]
        if top_threat["average_risk_score"] > 75:
            recommendations.append({
                "priority": "high",
                "category": "tactical",
                "action": f"Develop specific response strategy for {top_threat['name']}",
                "rationale": f"Top competitor showing high risk score of {top_threat['average_risk_score']}"
            })
    
    # Market structure recommendations
    if competitor_count > 15:
        recommendations.append({
            "priority": "medium",
            "category": "strategic",
            "action": "Focus on market consolidation opportunities",
            "rationale": "Fragmented market with many competitors suggests consolidation potential"
        })
    
    return recommendations