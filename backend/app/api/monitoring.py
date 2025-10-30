"""
API monitoring endpoints for You.com API resilience and performance tracking.
Based on Discord hackathon insights for proactive monitoring.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.api_call_log import ApiCallLog
from app.services.resilient_you_client import ResilientYouComOrchestrator
from app.resilience_config import get_resilience_config

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/dashboard")
async def get_monitoring_dashboard(
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive monitoring dashboard data"""
    
    # Get recent API call logs
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Query API call statistics
    api_stats_query = await db.execute(
        select(
            ApiCallLog.api_type,
            func.count(ApiCallLog.id).label("total_calls"),
            func.sum(func.cast(ApiCallLog.success, int)).label("successful_calls"),
            func.avg(ApiCallLog.latency_ms).label("avg_latency"),
            func.max(ApiCallLog.latency_ms).label("max_latency"),
            func.min(ApiCallLog.latency_ms).label("min_latency")
        )
        .where(ApiCallLog.created_at >= since)
        .group_by(ApiCallLog.api_type)
    )
    
    api_stats = {}
    for row in api_stats_query:
        success_rate = (row.successful_calls / row.total_calls * 100) if row.total_calls > 0 else 0
        api_stats[row.api_type] = {
            "total_calls": row.total_calls,
            "successful_calls": row.successful_calls,
            "failed_calls": row.total_calls - row.successful_calls,
            "success_rate": round(success_rate, 2),
            "avg_latency_ms": round(row.avg_latency or 0, 2),
            "max_latency_ms": row.max_latency or 0,
            "min_latency_ms": row.min_latency or 0
        }
    
    # Get recent failures
    recent_failures_query = await db.execute(
        select(ApiCallLog)
        .where(
            ApiCallLog.created_at >= since,
            ApiCallLog.success == False
        )
        .order_by(desc(ApiCallLog.created_at))
        .limit(10)
    )
    
    recent_failures = []
    for failure in recent_failures_query.scalars():
        recent_failures.append({
            "api_type": failure.api_type,
            "endpoint": failure.endpoint,
            "status_code": failure.status_code,
            "error_message": failure.error_message,
            "latency_ms": failure.latency_ms,
            "timestamp": failure.created_at.isoformat()
        })
    
    # Get current circuit breaker status
    async with ResilientYouComOrchestrator() as client:
        resilience_status = client.get_health_status()
    
    # Calculate overall health score
    total_apis = len(api_stats)
    healthy_apis = sum(1 for stats in api_stats.values() if stats["success_rate"] >= 90)
    health_score = (healthy_apis / total_apis * 100) if total_apis > 0 else 100
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "time_range_hours": hours,
        "overall_health": {
            "score": round(health_score, 2),
            "status": "healthy" if health_score >= 90 else "degraded" if health_score >= 70 else "unhealthy",
            "total_apis": total_apis,
            "healthy_apis": healthy_apis
        },
        "api_statistics": api_stats,
        "recent_failures": recent_failures,
        "circuit_breakers": resilience_status["circuit_breakers"],
        "rate_limiting": resilience_status["rate_limiting"],
        "recommendations": _generate_monitoring_recommendations(api_stats, resilience_status)
    }

@router.get("/alerts")
async def get_active_alerts(db: AsyncSession = Depends(get_db)):
    """Get active alerts based on API performance"""
    
    alerts = []
    
    # Check recent failure rates
    last_hour = datetime.utcnow() - timedelta(hours=1)
    
    failure_query = await db.execute(
        select(
            ApiCallLog.api_type,
            func.count(ApiCallLog.id).label("total_calls"),
            func.sum(func.cast(ApiCallLog.success == False, int)).label("failed_calls")
        )
        .where(ApiCallLog.created_at >= last_hour)
        .group_by(ApiCallLog.api_type)
    )
    
    for row in failure_query:
        if row.total_calls > 0:
            failure_rate = (row.failed_calls / row.total_calls) * 100
            
            if failure_rate >= 50:
                alerts.append({
                    "severity": "critical",
                    "api": row.api_type,
                    "message": f"{row.api_type.upper()} API failure rate is {failure_rate:.1f}% in the last hour",
                    "recommendation": f"Consider enabling fallback mode for {row.api_type} API",
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif failure_rate >= 25:
                alerts.append({
                    "severity": "warning",
                    "api": row.api_type,
                    "message": f"{row.api_type.upper()} API showing elevated failure rate: {failure_rate:.1f}%",
                    "recommendation": f"Monitor {row.api_type} API closely",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    # Check circuit breaker status
    async with ResilientYouComOrchestrator() as client:
        health_status = client.get_health_status()
        
        for api, status in health_status["circuit_breakers"].items():
            if status["state"] == "open":
                alerts.append({
                    "severity": "critical",
                    "api": api,
                    "message": f"{api.upper()} API circuit breaker is OPEN",
                    "recommendation": f"Using fallback data for {api} API",
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif status["state"] == "half_open":
                alerts.append({
                    "severity": "warning",
                    "api": api,
                    "message": f"{api.upper()} API circuit breaker is HALF_OPEN (recovering)",
                    "recommendation": f"Monitoring {api} API recovery",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_alerts": len(alerts),
        "critical_alerts": len([a for a in alerts if a["severity"] == "critical"]),
        "warning_alerts": len([a for a in alerts if a["severity"] == "warning"]),
        "alerts": alerts
    }

@router.get("/performance/{api_type}")
async def get_api_performance(
    api_type: str,
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed performance metrics for specific API"""
    
    if api_type not in ["news", "search", "chat", "ari"]:
        raise HTTPException(status_code=400, detail="Invalid API type")
    
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get hourly performance data
    hourly_query = await db.execute(
        select(
            func.date_trunc('hour', ApiCallLog.created_at).label('hour'),
            func.count(ApiCallLog.id).label('total_calls'),
            func.sum(func.cast(ApiCallLog.success, int)).label('successful_calls'),
            func.avg(ApiCallLog.latency_ms).label('avg_latency')
        )
        .where(
            ApiCallLog.api_type == api_type,
            ApiCallLog.created_at >= since
        )
        .group_by(func.date_trunc('hour', ApiCallLog.created_at))
        .order_by(func.date_trunc('hour', ApiCallLog.created_at))
    )
    
    hourly_data = []
    for row in hourly_query:
        success_rate = (row.successful_calls / row.total_calls * 100) if row.total_calls > 0 else 0
        hourly_data.append({
            "hour": row.hour.isoformat(),
            "total_calls": row.total_calls,
            "successful_calls": row.successful_calls,
            "success_rate": round(success_rate, 2),
            "avg_latency_ms": round(row.avg_latency or 0, 2)
        })
    
    # Get error distribution
    error_query = await db.execute(
        select(
            ApiCallLog.status_code,
            func.count(ApiCallLog.id).label('count')
        )
        .where(
            ApiCallLog.api_type == api_type,
            ApiCallLog.created_at >= since,
            ApiCallLog.success == False
        )
        .group_by(ApiCallLog.status_code)
    )
    
    error_distribution = {}
    for row in error_query:
        error_distribution[str(row.status_code or "unknown")] = row.count
    
    return {
        "api_type": api_type,
        "time_range_hours": hours,
        "hourly_performance": hourly_data,
        "error_distribution": error_distribution,
        "insights": _generate_api_insights(api_type, hourly_data, error_distribution)
    }

@router.get("/config")
async def get_resilience_config_endpoint():
    """Get current resilience configuration"""
    return get_resilience_config()

@router.post("/circuit-breaker/{api_type}/reset")
async def reset_circuit_breaker(api_type: str):
    """Manually reset circuit breaker for specific API"""
    
    if api_type not in ["news", "search", "chat", "ari"]:
        raise HTTPException(status_code=400, detail="Invalid API type")
    
    async with ResilientYouComOrchestrator() as client:
        circuit_breaker = client.circuit_breakers.get(api_type)
        if not circuit_breaker:
            raise HTTPException(status_code=404, detail="Circuit breaker not found")
        
        # Reset circuit breaker
        circuit_breaker.state.state = circuit_breaker.state.state.CLOSED
        circuit_breaker.state.failure_count = 0
        circuit_breaker.state.success_count = 0
        
        return {
            "message": f"Circuit breaker for {api_type} API has been reset",
            "api_type": api_type,
            "new_state": "closed",
            "timestamp": datetime.utcnow().isoformat()
        }

def _generate_monitoring_recommendations(
    api_stats: Dict[str, Any],
    resilience_status: Dict[str, Any]
) -> List[str]:
    """Generate monitoring recommendations based on current status"""
    
    recommendations = []
    
    # Check API performance
    for api, stats in api_stats.items():
        if stats["success_rate"] < 70:
            recommendations.append(f"🚨 {api.upper()} API success rate is {stats['success_rate']}% - consider maintenance")
        elif stats["success_rate"] < 90:
            recommendations.append(f"⚠️ {api.upper()} API success rate is {stats['success_rate']}% - monitor closely")
        
        if stats["avg_latency_ms"] > 5000:
            recommendations.append(f"🐌 {api.upper()} API average latency is {stats['avg_latency_ms']}ms - performance issue")
    
    # Check circuit breakers
    open_circuits = [
        api for api, status in resilience_status["circuit_breakers"].items()
        if status["state"] == "open"
    ]
    
    if open_circuits:
        recommendations.append(f"🔴 Circuit breakers OPEN for: {', '.join(open_circuits)} - using fallback data")
    
    if not recommendations:
        recommendations.append("✅ All APIs performing within normal parameters")
    
    return recommendations

def _generate_api_insights(
    api_type: str,
    hourly_data: List[Dict],
    error_distribution: Dict[str, int]
) -> List[str]:
    """Generate insights for specific API performance"""
    
    insights = []
    
    if not hourly_data:
        insights.append(f"No recent activity for {api_type} API")
        return insights
    
    # Analyze trends
    recent_hours = hourly_data[-3:] if len(hourly_data) >= 3 else hourly_data
    avg_success_rate = sum(h["success_rate"] for h in recent_hours) / len(recent_hours)
    avg_latency = sum(h["avg_latency_ms"] for h in recent_hours) / len(recent_hours)
    
    if avg_success_rate >= 95:
        insights.append(f"✅ {api_type.upper()} API performing excellently ({avg_success_rate:.1f}% success rate)")
    elif avg_success_rate >= 85:
        insights.append(f"👍 {api_type.upper()} API performing well ({avg_success_rate:.1f}% success rate)")
    else:
        insights.append(f"⚠️ {api_type.upper()} API showing issues ({avg_success_rate:.1f}% success rate)")
    
    # Latency insights
    if avg_latency < 1000:
        insights.append(f"⚡ Low latency: {avg_latency:.0f}ms average")
    elif avg_latency < 3000:
        insights.append(f"🕐 Moderate latency: {avg_latency:.0f}ms average")
    else:
        insights.append(f"🐌 High latency: {avg_latency:.0f}ms average - may need optimization")
    
    # Error analysis
    if "429" in error_distribution:
        insights.append("🚫 Rate limiting detected - consider increasing request intervals")
    
    if "500" in error_distribution or "502" in error_distribution or "503" in error_distribution:
        insights.append("🔧 Server errors detected - API may be experiencing issues")
    
    return insights