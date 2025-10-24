"""
Enterprise CIA - FastAPI Backend
Competitive Intelligence Agent powered by You.com APIs
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import socketio
from app.config import settings
from app.database import engine, Base, get_db
from app.api import watch, impact, research
from app.api import metrics, notifications, feedback
from app.api import auth, workspaces
from app.realtime import sio
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
    yield
    
    # Shutdown
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

    from app.services.you_client import YouComOrchestrator

    async with YouComOrchestrator() as client:
        async def check_api(name: str, coroutine, endpoint: str):
            try:
                await asyncio.wait_for(coroutine, timeout=10)
                return name, {"status": "healthy", "endpoint": endpoint}
            except asyncio.TimeoutError:
                return name, {
                    "status": "unhealthy",
                    "error": "timeout after 10s",
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
            ),
            check_api(
                "news",
                client.fetch_news("health-check", limit=1),
                settings.you_news_url,
            ),
            check_api(
                "chat",
                client.analyze_impact({"articles": []}, {"results": []}, "HealthCo"),
                settings.you_chat_url,
            ),
            check_api(
                "ari",
                client.generate_research_report("health-check signal"),
                settings.you_ari_url,
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
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": overall,
        "apis": api_results,
    }


@app.get("/api/v1/health/you-apis")
async def check_you_apis():
    """Health check for all You.com APIs with short-lived caching."""

    now = datetime.utcnow()
    cached = YOU_API_HEALTH_CACHE.get("data")
    cached_at = YOU_API_HEALTH_CACHE.get("timestamp")

    if cached and cached_at and now - cached_at < YOU_API_HEALTH_TTL:
        return cached

    results = await _run_you_api_checks()
    YOU_API_HEALTH_CACHE["data"] = results
    YOU_API_HEALTH_CACHE["timestamp"] = now
    return results

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
