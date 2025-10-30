"""
Advanced Orchestration API Endpoints - Week 1 Implementation
Exposes optimized You.com API orchestration with performance monitoring.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.advanced_orchestrator import get_advanced_you_client, AdvancedYouComOrchestrator
from app.services.performance_monitor import metrics_collector, performance_analyzer, performance_optimizer
from app.services.auth_service import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advanced", tags=["Advanced Orchestration"])

# Request/Response Models
class OptimizedImpactCardRequest(BaseModel):
    competitor: str = Field(..., description="Competitor name to analyze")
    keywords: Optional[List[str]] = Field(default=None, description="Additional keywords for analysis")
    progress_room: Optional[str] = Field(default=None, description="WebSocket room for progress updates")

class OptimizedImpactCardResponse(BaseModel):
    competitor: str
    generated_at: str
    risk_score: int
    risk_level: str
    confidence_score: int
    processing_time: str
    route: str
    optimization: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    source_quality: Optional[Dict[str, Any]] = None
    requires_review: bool = False

class PerformanceMetricsResponse(BaseModel):
    api_metrics: Dict[str, Any]
    system_health: Dict[str, Any]
    optimization_recommendations: List[str]
    generated_at: str

class OptimizationReportResponse(BaseModel):
    performance_metrics: Dict[str, Any]
    cost_optimization: Dict[str, Any]
    system_health: Dict[str, Any]
    recommendations: List[str]
    generated_at: str

@router.post("/impact-card/optimized", response_model=OptimizedImpactCardResponse)
async def generate_optimized_impact_card(
    request: OptimizedImpactCardRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    you_client: AdvancedYouComOrchestrator = Depends(get_advanced_you_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate impact card using advanced orchestration with sub-minute performance.
    This endpoint showcases Week 1 optimization improvements.
    """
    logger.info(f"🚀 Optimized impact card request for {request.competitor} by {current_user.email}")
    
    try:
        # Record request metric
        await metrics_collector.record_metric(
            "api_request_optimized_impact_card",
            1.0,
            {"user_id": str(current_user.id), "competitor": request.competitor}
        )
        
        # Generate optimized impact card
        impact_card = await you_client.generate_impact_card_optimized(
            competitor=request.competitor,
            keywords=request.keywords,
            progress_room=request.progress_room,
            db_session=db
        )
        
        # Record performance metrics
        processing_time = float(impact_card.get("processing_time", "0s").replace("s", ""))
        await metrics_collector.record_metric(
            "impact_card_generation_time",
            processing_time,
            {
                "route": impact_card.get("optimization", {}).get("route", "unknown"),
                "competitor": request.competitor
            }
        )
        
        # Background task: Update optimization recommendations
        background_tasks.add_task(
            _update_optimization_recommendations,
            impact_card.get("optimization", {}),
            impact_card.get("performance_metrics", {})
        )
        
        logger.info(f"✅ Optimized impact card generated for {request.competitor} in {processing_time}s")
        
        return OptimizedImpactCardResponse(
            competitor=impact_card["competitor"],
            generated_at=impact_card["generated_at"],
            risk_score=impact_card["risk_score"],
            risk_level=impact_card["risk_level"],
            confidence_score=impact_card["confidence_score"],
            processing_time=impact_card["processing_time"],
            route=impact_card.get("optimization", {}).get("route", "unknown"),
            optimization=impact_card.get("optimization", {}),
            performance_metrics=impact_card.get("performance_metrics", {}),
            source_quality=impact_card.get("source_quality"),
            requires_review=impact_card.get("requires_review", False)
        )
        
    except Exception as e:
        logger.error(f"❌ Optimized impact card generation failed: {str(e)}")
        
        # Record error metric
        await metrics_collector.record_metric(
            "api_error_optimized_impact_card",
            1.0,
            {"error": str(e), "competitor": request.competitor}
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate optimized impact card: {str(e)}"
        )

@router.get("/performance/metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    duration_minutes: int = 60,
    current_user: User = Depends(get_current_user),
    you_client: AdvancedYouComOrchestrator = Depends(get_advanced_you_client)
):
    """Get real-time performance metrics and system health"""
    logger.info(f"📊 Performance metrics requested by {current_user.email}")
    
    try:
        # Get system health analysis
        system_health = await performance_analyzer.analyze_system_health()
        
        # Get API performance metrics
        api_metrics = {}
        for api in ["news", "search", "chat", "ari", "overall"]:
            api_metrics[api] = await metrics_collector.get_aggregated_metrics(
                f"api_latency_{api}",
                duration_minutes
            )
        
        # Get optimization recommendations
        optimization_report = await performance_optimizer.get_optimization_report()
        
        return PerformanceMetricsResponse(
            api_metrics=api_metrics,
            system_health={
                "status": system_health.status,
                "score": system_health.score,
                "issues": system_health.issues,
                "recommendations": system_health.recommendations
            },
            optimization_recommendations=optimization_report.get("recommendations", []),
            generated_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Performance metrics retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )

@router.get("/optimization/report", response_model=OptimizationReportResponse)
async def get_optimization_report(
    current_user: User = Depends(get_current_user),
    you_client: AdvancedYouComOrchestrator = Depends(get_advanced_you_client)
):
    """Get comprehensive optimization report"""
    logger.info(f"📈 Optimization report requested by {current_user.email}")
    
    try:
        # Get comprehensive optimization report
        report = await you_client.get_optimization_report()
        
        return OptimizationReportResponse(
            performance_metrics=report["performance_metrics"],
            cost_optimization=report["cost_optimization"],
            system_health=report["system_health"],
            recommendations=report["recommendations"],
            generated_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Optimization report generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate optimization report: {str(e)}"
        )

@router.post("/performance/optimize")
async def trigger_optimization(
    current_user: User = Depends(get_current_user)
):
    """Trigger performance optimization based on current metrics"""
    logger.info(f"🔧 Performance optimization triggered by {current_user.email}")
    
    try:
        # Get optimization recommendations
        cache_optimization = await performance_optimizer.optimize_cache_ttl()
        routing_optimization = await performance_optimizer.optimize_query_routing()
        
        return {
            "status": "optimization_triggered",
            "cache_optimization": cache_optimization,
            "routing_optimization": routing_optimization,
            "message": "Optimization recommendations generated",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Performance optimization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger optimization: {str(e)}"
        )

@router.get("/health/circuit-breakers")
async def get_circuit_breaker_status(
    current_user: User = Depends(get_current_user),
    you_client: AdvancedYouComOrchestrator = Depends(get_advanced_you_client)
):
    """Get circuit breaker status for all APIs"""
    logger.info(f"🔌 Circuit breaker status requested by {current_user.email}")
    
    try:
        health_status = you_client.get_health_status()
        
        return {
            "circuit_breakers": health_status["circuit_breakers"],
            "rate_limiting": health_status["rate_limiting"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Circuit breaker status retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get circuit breaker status: {str(e)}"
        )

@router.post("/cache/clear")
async def clear_cache(
    cache_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    you_client: AdvancedYouComOrchestrator = Depends(get_advanced_you_client)
):
    """Clear cache (for testing and troubleshooting)"""
    logger.info(f"🗑️ Cache clear requested by {current_user.email}")
    
    try:
        if you_client.cache:
            if cache_type:
                # Clear specific cache type
                pattern = f"youcom:{cache_type}:*"
                keys = await you_client.cache.keys(pattern)
                if keys:
                    await you_client.cache.delete(*keys)
                    cleared_count = len(keys)
                else:
                    cleared_count = 0
            else:
                # Clear all You.com cache
                pattern = "youcom:*"
                keys = await you_client.cache.keys(pattern)
                if keys:
                    await you_client.cache.delete(*keys)
                    cleared_count = len(keys)
                else:
                    cleared_count = 0
            
            return {
                "status": "cache_cleared",
                "cache_type": cache_type or "all",
                "cleared_count": cleared_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "cache_unavailable",
                "message": "Redis cache not available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ Cache clear failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )

# Background task functions
async def _update_optimization_recommendations(
    optimization_data: Dict[str, Any],
    performance_data: Dict[str, Any]
):
    """Background task to update optimization recommendations"""
    try:
        # Record optimization metrics
        if "actual_time" in optimization_data:
            actual_time = float(optimization_data["actual_time"].replace("s", ""))
            estimated_time = float(optimization_data.get("estimated_time", 0))
            
            # Record accuracy of time estimation with proper edge case handling
            if actual_time == 0 and estimated_time == 0:
                accuracy = 1.0  # Both zero is perfect accuracy
            elif estimated_time == 0:
                accuracy = 0.0  # Can't estimate zero time
            else:
                accuracy = 1.0 - abs(actual_time - estimated_time) / max(estimated_time, 1.0)
                accuracy = max(0.0, min(1.0, accuracy))  # Clamp to [0.0, 1.0]
            
            await metrics_collector.record_metric(
                "time_estimation_accuracy",
                accuracy,
                {"route": optimization_data.get("route", "unknown")}
            )
        
        # Record route performance
        if "route" in optimization_data:
            route = optimization_data["route"]
            processing_time = float(optimization_data.get("actual_time", "0s").replace("s", ""))
            
            await metrics_collector.record_metric(
                f"route_latency_{route}",
                processing_time * 1000,  # Convert to milliseconds
                {"complexity": optimization_data.get("complexity", "unknown")}
            )
        
        logger.info("📊 Optimization metrics updated")
        
    except Exception as e:
        logger.error(f"❌ Failed to update optimization recommendations: {e}")

# Note: Router-level event handlers are deprecated.
# Performance monitoring startup/shutdown should be handled at the application level in main.py