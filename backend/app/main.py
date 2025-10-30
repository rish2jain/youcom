"""
Enterprise CIA - FastAPI Backend
Competitive Intelligence Agent powered by You.com APIs
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import socketio
from app.config import settings
from app.database import engine, Base, get_db
from app.api import watch, impact, research
from app.api import metrics, notifications, feedback
from app.api import auth, workspaces, analytics
from app.realtime import sio
from app.services.scheduler import alert_scheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Health check caching
YOU_API_HEALTH_CACHE: Dict[str, Any] = {"timestamp": None, "data": None}
YOU_API_HEALTH_TTL = timedelta(seconds=60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting Enterprise CIA Backend")
    logger.info(f"Environment: {settings.environment}")
    logger.info("Powered by You.com APIs: News, Search, Chat, ARI")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Database tables created")
    
    # Start automated alert scheduler
    await alert_scheduler.start()
    logger.info("🔔 Automated alert scheduler started")
    
    # Initialize SOC 2 security controls
    from app.services.soc2_service import soc2_service, AuditEventType
    await soc2_service.log_audit_event(
        event_type=AuditEventType.SYSTEM_CONFIGURATION,
        action="System startup",
        details={"environment": settings.environment, "version": "1.0.0"}
    )
    logger.info("🔒 SOC 2 audit logging initialized")
    
    # Start performance monitoring
    try:
        from app.services.performance_monitor import start_performance_monitoring
        await start_performance_monitoring()
        logger.info("🚀 Advanced orchestration monitoring started")
    except Exception as e:
        logger.warning(f"⚠️ Performance monitoring failed to start: {e}")
    
    # Initialize enhancement features
    try:
        from app.services.personal_playbook_service import PersonalPlaybookService
        from app.services.action_tracker_service import ActionTrackerService
        from app.database import get_db
        
        db = next(get_db())
        try:
            # Initialize built-in personas (sync call)
            playbook_service = PersonalPlaybookService(db)
            playbook_service.initialize_builtin_personas()
            logger.info("✅ Built-in persona presets initialized")
            
            # Initialize built-in action templates (sync call)
            action_service = ActionTrackerService(db)
            action_service.initialize_builtin_templates()
            logger.info("✅ Built-in action templates initialized")
            
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"⚠️ Enhancement features initialization failed: {e}")
    
    yield
    
    # Shutdown
    await alert_scheduler.stop()
    logger.info("🔔 Alert scheduler stopped")
    
    # Stop performance monitoring
    try:
        from app.services.performance_monitor import stop_performance_monitoring
        await stop_performance_monitoring()
        logger.info("⏹️ Advanced orchestration monitoring stopped")
    except Exception as e:
        logger.warning(f"⚠️ Performance monitoring failed to stop: {e}")
    logger.info("🛑 Shutting down Enterprise CIA Backend")

# Create FastAPI app
app = FastAPI(
    title="Enterprise CIA API",
    description="Competitive Intelligence Agent powered by You.com APIs",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3456",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3456"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
# Core features
app.include_router(watch.router, prefix="/api/v1")
app.include_router(impact.router, prefix="/api/v1")
app.include_router(research.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")

# Enterprise features
app.include_router(auth.router, prefix="/api/v1")
app.include_router(workspaces.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")

# Monitoring and resilience
from app.api import monitoring
app.include_router(monitoring.router, prefix="/api/v1")

# Week 1 Implementation - Advanced Features
from app.api import advanced_orchestration, sso, integrations
app.include_router(advanced_orchestration.router)
app.include_router(sso.router)
app.include_router(integrations.router)

# Week 2 Implementation - Enterprise Readiness
from app.api import compliance
app.include_router(compliance.router)

# Week 3 Implementation - Advanced Features
from app.api import advanced_intelligence
app.include_router(advanced_intelligence.router)

# Week 4 Implementation - Community Platform & White-label Solutions
from app.api import community, whitelabel, integration_marketplace
app.include_router(community.router)
app.include_router(whitelabel.router)
app.include_router(integration_marketplace.router)

# Enhancement Features - Timeline, Evidence, Playbooks, Actions
from app.api import enhancements
app.include_router(enhancements.router)

# Advanced Intelligence Suite - ML Feedback and Training
from app.api import ml_feedback, ml_features, ml_training
app.include_router(ml_feedback.router, prefix="/api/v1")
app.include_router(ml_features.router, prefix="/api/v1")
app.include_router(ml_training.router, prefix="/api/v1")

# Advanced Intelligence Suite - Industry Templates
from app.api import industry_templates
app.include_router(industry_templates.router, prefix="/api/v1")

# Advanced Intelligence Suite - Benchmarking Dashboard
from app.api import benchmarking
app.include_router(benchmarking.router, prefix="/api/v1")

# Advanced Intelligence Suite - Sentiment Analysis
from app.api import sentiment
app.include_router(sentiment.router, prefix="/api/v1")

# Socket.IO events for real-time updates
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    logger.info(f"🔌 Client connected: {sid}")
    await sio.emit('connected', {'message': 'Connected to Enterprise CIA'}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"🔌 Client disconnected: {sid}")

@sio.event
async def join_room(sid, data):
    """Join a specific room for updates"""
    room = data.get('room')
    if room:
        await sio.enter_room(sid, room)
        logger.info(f"🏠 Client {sid} joined room: {room}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Enterprise CIA Backend",
        "version": "1.0.0",
        "powered_by": "You.com APIs"
    }

# You.com API health check endpoint
async def _run_you_api_checks() -> Dict[str, Any]:
    """Execute health checks for all You.com APIs concurrently."""

    from app.services.resilient_you_client import ResilientYouComOrchestrator

    async with ResilientYouComOrchestrator() as client:
        async def check_api(name: str, coroutine, endpoint: str, timeout: int = 10):
            try:
                await asyncio.wait_for(coroutine, timeout=timeout)
                return name, {"status": "healthy", "endpoint": endpoint}
            except asyncio.TimeoutError:
                return name, {
                    "status": "unhealthy",
                    "error": f"timeout after {timeout}s",
                    "endpoint": endpoint,
                }
            except Exception as exc:  # pragma: no cover - defensive
                return name, {
                    "status": "unhealthy",
                    "error": str(exc),
                    "endpoint": endpoint,
                }

        checks = await asyncio.gather(
            check_api(
                "search",
                client.search_context("health-check", limit=1),
                settings.you_search_url,
                timeout=10,
            ),
            check_api(
                "news",
                client.fetch_news("health-check", limit=1),
                settings.you_news_url,
                timeout=10,
            ),
            check_api(
                "chat",
                client.analyze_impact({"articles": []}, {"results": []}, "HealthCo"),
                settings.you_chat_url,
                timeout=15,
            ),
            check_api(
                "ari",
                client.generate_research_report("Brief health check"),
                settings.you_ari_url,
                timeout=30,  # ARI needs more time for comprehensive research
            ),
        )

    api_results = {name: result for name, result in checks}
    statuses = [result["status"] for result in api_results.values()]

    if all(status == "healthy" for status in statuses):
        overall = "healthy"
    elif any(status == "healthy" for status in statuses):
        overall = "degraded"
    else:
        overall = "unhealthy"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall,
        "apis": api_results,
        "resilience_status": client.get_health_status(),
    }


@app.get("/api/v1/health/you-apis")
async def check_you_apis():
    """Health check for all You.com APIs with short-lived caching."""

    now = datetime.now(timezone.utc)
    cached = YOU_API_HEALTH_CACHE.get("data")
    cached_at = YOU_API_HEALTH_CACHE.get("timestamp")

    if cached and cached_at and now - cached_at < YOU_API_HEALTH_TTL:
        return cached

    results = await _run_you_api_checks()
    YOU_API_HEALTH_CACHE["data"] = results
    YOU_API_HEALTH_CACHE["timestamp"] = now
    return results

@app.get("/api/v1/health/resilience")
async def check_resilience_status():
    """Get detailed resilience status including circuit breakers and rate limiting."""
    from app.services.resilient_you_client import ResilientYouComOrchestrator
    
    async with ResilientYouComOrchestrator() as client:
        health_status = client.get_health_status()
        
        # Add summary metrics
        circuit_states = [cb["state"] for cb in health_status["circuit_breakers"].values()]
        open_circuits = sum(1 for state in circuit_states if state == "open")
        degraded_circuits = sum(1 for state in circuit_states if state == "half_open")
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_circuits": len(circuit_states),
                "open_circuits": open_circuits,
                "degraded_circuits": degraded_circuits,
                "healthy_circuits": len(circuit_states) - open_circuits - degraded_circuits,
                "overall_health": "healthy" if open_circuits == 0 else "degraded" if open_circuits < 2 else "unhealthy"
            },
            "details": health_status,
            "recommendations": _get_resilience_recommendations(health_status)
        }

def _get_resilience_recommendations(health_status: Dict) -> List[str]:
    """Generate recommendations based on circuit breaker status"""
    recommendations = []
    
    for api, status in health_status["circuit_breakers"].items():
        if status["state"] == "open":
            recommendations.append(f"🚨 {api.upper()} API is down - using fallback data")
        elif status["state"] == "half_open":
            recommendations.append(f"⚠️ {api.upper()} API is recovering - monitoring closely")
        elif status["failure_count"] > 2:
            recommendations.append(f"⚡ {api.upper()} API showing instability - consider manual review")
    
    if not recommendations:
        recommendations.append("✅ All APIs operating normally")
    
    return recommendations

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Enterprise CIA - Competitive Intelligence Agent",
        "description": "AI-powered competitive intelligence using You.com APIs",
        "apis_integrated": ["News API", "Search API", "Chat API (Custom Agents)", "ARI API"],
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Demo endpoint showcasing You.com API integration
@app.get("/api/v1/demo/you-apis")
async def demo_you_apis(db: AsyncSession = Depends(get_db)):
    """Return live status for the demo, sourced from real metrics."""

    metrics_payload = await metrics.api_usage_metrics(db=db)

    latest_card_row = await db.execute(
        select(ImpactCard).order_by(ImpactCard.created_at.desc()).limit(1)
    )
    latest_card = latest_card_row.scalars().first()

    latest_research_row = await db.execute(
        select(CompanyResearch).order_by(CompanyResearch.created_at.desc()).limit(1)
    )
    latest_research = latest_research_row.scalars().first()

    return {
        "message": "Enterprise CIA integrates all 4 You.com APIs",
        "metrics": metrics_payload,
        "latest_impact_card": (
            {
                "competitor": latest_card.competitor_name,
                "risk_score": latest_card.risk_score,
                "risk_level": latest_card.risk_level,
                "confidence": latest_card.confidence_score,
                "generated_at": latest_card.created_at.isoformat() if latest_card.created_at else None,
                "total_sources": latest_card.total_sources,
            }
            if latest_card
            else None
        ),
        "latest_company_research": (
            {
                "company": latest_research.company_name,
                "total_sources": latest_research.total_sources,
                "generated_at": latest_research.created_at.isoformat() if latest_research.created_at else None,
            }
            if latest_research
            else None
        ),
        "workflow": [
            "1. Monitor competitors via News API",
            "2. Enrich context via Search API",
            "3. Analyze impact via Chat API",
            "4. Generate deep research via ARI API",
            "5. Assemble actionable Impact Cards",
        ],
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "service": "Enterprise CIA"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "service": "Enterprise CIA"
        }
    )

# Mount Socket.IO app
socket_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:socket_app",
        host="0.0.0.0",
        port=8765,
        reload=settings.environment == "development"
    )
