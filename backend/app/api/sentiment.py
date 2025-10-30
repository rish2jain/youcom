"""
Sentiment Analysis API endpoints for Advanced Intelligence Suite
Provides real-time sentiment analysis, trend detection, and alerting
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Union
import logging
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.sentiment_analysis import (
    SentimentAnalysis, SentimentTrend, SentimentAlert, SentimentProcessingQueue
)
from app.services.sentiment_processor import sentiment_processor
from app.services.sentiment_trend_analyzer import sentiment_trend_analyzer
from app.services.sentiment_alert_worker import sentiment_alert_worker
from app.services.sentiment_classifier import get_entity_recognizer, get_sentiment_classifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])


# Pydantic models for API requests and responses
class SentimentAnalysisRequest(BaseModel):
    content_text: str = Field(..., min_length=10, max_length=10000)
    content_type: str = Field(default="news", pattern="^(news|social|report|email)$")
    source_url: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=4)


class SentimentAnalysisResponse(BaseModel):
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    entities: List[Dict[str, Any]]
    processing_time: float
    content_id: str


class EntitySentimentResponse(BaseModel):
    entity_name: str
    entity_type: str
    current_sentiment: float
    sentiment_label: str
    total_mentions: int
    confidence: float
    last_updated: datetime


class SentimentTrendResponse(BaseModel):
    entity_name: str
    entity_type: str
    timeframe: str
    trend_direction: str
    trend_strength: float
    current_sentiment: float
    previous_sentiment: float
    sentiment_change: float
    volatility: float
    total_mentions: int
    period_start: datetime
    period_end: datetime


class SentimentAlertResponse(BaseModel):
    id: int
    entity_name: str
    entity_type: str
    alert_type: str
    alert_severity: str
    current_sentiment: float
    previous_sentiment: Optional[float]
    sentiment_change: Optional[float]
    confidence: float
    triggered_at: datetime
    is_resolved: bool
    message: str


class SentimentVisualizationResponse(BaseModel):
    entity_name: str
    timeframe: str
    data_points: List[Dict[str, Any]]
    summary: Dict[str, Any]


class QueueStatusResponse(BaseModel):
    is_running: bool
    pending: int
    processing: int
    completed: int
    failed: int
    total: int


# WebSocket connection manager
class SentimentWebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                # Log the exception and remove disconnected clients
                logging.getLogger(__name__).exception(f"Failed to send WebSocket message: {e}")
                self.disconnect(connection)


websocket_manager = SentimentWebSocketManager()


# API Endpoints

@router.post("/analyze", response_model=SentimentAnalysisResponse)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """Analyze sentiment of provided content."""
    try:
        # Generate unique content ID
        content_id = f"api_{datetime.now(timezone.utc).timestamp()}"
        
        # Process content for sentiment analysis
        result = await sentiment_processor.process_content(
            content_id=content_id,
            content_text=request.content_text,
            content_type=request.content_type,
            source_url=request.source_url
        )
        
        return SentimentAnalysisResponse(
            sentiment_score=result.sentiment_score,
            sentiment_label=result.sentiment_label,
            confidence=result.confidence,
            entities=result.entities,
            processing_time=result.processing_time,
            content_id=content_id
        )
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")


@router.post("/queue")
async def queue_content_for_analysis(
    request: SentimentAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """Queue content for background sentiment analysis."""
    try:
        content_id = f"queue_{datetime.now(timezone.utc).timestamp()}"
        
        success = await sentiment_processor.queue_content_for_processing(
            content_id=content_id,
            content_text=request.content_text,
            content_type=request.content_type,
            source_url=request.source_url,
            priority=request.priority
        )
        
        if success:
            return {"content_id": content_id, "status": "queued", "message": "Content queued for processing"}
        else:
            raise HTTPException(status_code=400, detail="Failed to queue content")
            
    except Exception as e:
        logger.error(f"Error queuing content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue content: {str(e)}")


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status():
    """Get current processing queue status."""
    try:
        status = await sentiment_alert_worker.get_worker_status()
        queue_status = await sentiment_processor.queue_content_for_processing.__self__.get_queue_status()
        
        return QueueStatusResponse(**queue_status)
        
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")


@router.get("/entities", response_model=List[EntitySentimentResponse])
async def get_entity_sentiments(
    entity_type: Optional[str] = Query(None, pattern="^(company|product|market)$"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get current sentiment for entities."""
    try:
        # Build query for latest sentiment by entity
        query = select(
            SentimentAnalysis.entity_name,
            SentimentAnalysis.entity_type,
            func.avg(SentimentAnalysis.sentiment_score).label('avg_sentiment'),
            func.count(SentimentAnalysis.id).label('mention_count'),
            func.avg(SentimentAnalysis.confidence).label('avg_confidence'),
            func.max(SentimentAnalysis.processing_timestamp).label('last_updated')
        ).where(
            SentimentAnalysis.processing_timestamp >= datetime.now(timezone.utc) - timedelta(days=7)
        ).group_by(
            SentimentAnalysis.entity_name,
            SentimentAnalysis.entity_type
        ).order_by(
            desc('mention_count')
        ).limit(limit)
        
        if entity_type:
            query = query.where(SentimentAnalysis.entity_type == entity_type)
        
        result = await db.execute(query)
        entities = result.all()
        
        response = []
        for entity in entities:
            # Determine sentiment label
            if entity.avg_sentiment > 0.1:
                sentiment_label = "positive"
            elif entity.avg_sentiment < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            response.append(EntitySentimentResponse(
                entity_name=entity.entity_name,
                entity_type=entity.entity_type,
                current_sentiment=float(entity.avg_sentiment),
                sentiment_label=sentiment_label,
                total_mentions=entity.mention_count,
                confidence=float(entity.avg_confidence),
                last_updated=entity.last_updated
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting entity sentiments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get entity sentiments: {str(e)}")


@router.get("/trends", response_model=List[SentimentTrendResponse])
async def get_sentiment_trends(
    timeframe: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    entity_name: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None, pattern="^(company|product|market)$"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get sentiment trends for entities."""
    try:
        query = select(SentimentTrend).where(
            SentimentTrend.timeframe == timeframe
        ).order_by(desc(SentimentTrend.created_at)).limit(limit)
        
        if entity_name:
            query = query.where(SentimentTrend.entity_name.ilike(f"%{entity_name}%"))
        
        if entity_type:
            query = query.where(SentimentTrend.entity_type == entity_type)
        
        result = await db.execute(query)
        trends = result.scalars().all()
        
        response = []
        for trend in trends:
            # Calculate sentiment change from historical data
            sentiment_change = 0.0
            previous_sentiment = None
            
            # Look for previous period data
            previous_period_start = trend.period_start - (trend.period_end - trend.period_start)
            previous_period_end = trend.period_start
            
            previous_trend_query = select(SentimentTrend).where(
                and_(
                    SentimentTrend.entity_name == trend.entity_name,
                    SentimentTrend.timeframe == trend.timeframe,
                    SentimentTrend.period_start >= previous_period_start,
                    SentimentTrend.period_end <= previous_period_end
                )
            ).order_by(desc(SentimentTrend.period_end)).limit(1)
            
            previous_trend_result = await db.execute(previous_trend_query)
            previous_trend = previous_trend_result.scalar_one_or_none()
            
            if previous_trend:
                previous_sentiment = previous_trend.average_sentiment
                sentiment_change = trend.average_sentiment - previous_sentiment
            
            response.append(SentimentTrendResponse(
                entity_name=trend.entity_name,
                entity_type=trend.entity_type,
                timeframe=trend.timeframe,
                trend_direction=trend.trend_direction or "stable",
                trend_strength=trend.trend_strength or 0.0,
                current_sentiment=trend.average_sentiment,
                previous_sentiment=previous_sentiment,
                sentiment_change=sentiment_change,
                volatility=trend.sentiment_volatility,
                total_mentions=trend.total_mentions,
                period_start=trend.period_start,
                period_end=trend.period_end
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting sentiment trends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sentiment trends: {str(e)}")


@router.get("/alerts", response_model=List[SentimentAlertResponse])
async def get_sentiment_alerts(
    severity: Optional[str] = Query(None, pattern="^(low|medium|high|critical)$"),
    resolved: Optional[bool] = Query(None),
    entity_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get sentiment alerts."""
    try:
        query = select(SentimentAlert).order_by(desc(SentimentAlert.triggered_at)).limit(limit)
        
        if severity:
            query = query.where(SentimentAlert.alert_severity == severity)
        
        if resolved is not None:
            query = query.where(SentimentAlert.is_resolved == resolved)
        
        if entity_name:
            query = query.where(SentimentAlert.entity_name.ilike(f"%{entity_name}%"))
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        response = []
        for alert in alerts:
            # Generate alert message
            change_direction = "improved" if (alert.sentiment_change or 0) > 0 else "declined"
            change_magnitude = "significantly" if abs(alert.sentiment_change or 0) > 0.3 else "moderately"
            
            message = (f"Sentiment for {alert.entity_name} has {change_magnitude} {change_direction} "
                      f"to {alert.current_sentiment:.2f}")
            
            response.append(SentimentAlertResponse(
                id=alert.id,
                entity_name=alert.entity_name,
                entity_type=alert.entity_type,
                alert_type=alert.alert_type,
                alert_severity=alert.alert_severity,
                current_sentiment=alert.current_sentiment,
                previous_sentiment=alert.previous_sentiment,
                sentiment_change=alert.sentiment_change,
                confidence=alert.confidence,
                triggered_at=alert.triggered_at,
                is_resolved=alert.is_resolved,
                message=message
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting sentiment alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sentiment alerts: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_sentiment_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Resolve a sentiment alert."""
    try:
        alert = await db.get(SentimentAlert, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.is_resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        return {"message": "Alert resolved successfully", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")


@router.get("/visualization/{entity_name}", response_model=SentimentVisualizationResponse)
async def get_sentiment_visualization(
    entity_name: str,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get sentiment visualization data for an entity."""
    try:
        visualization_data = await sentiment_trend_analyzer.get_sentiment_visualization_data(
            entity_name=entity_name,
            days=days
        )
        
        if "error" in visualization_data:
            raise HTTPException(status_code=500, detail=visualization_data["error"])
        
        return SentimentVisualizationResponse(**visualization_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting visualization data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get visualization data: {str(e)}")


@router.post("/analyze/trigger")
async def trigger_sentiment_analysis(
    entity_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Trigger immediate sentiment analysis for entity or all entities."""
    try:
        result = await sentiment_alert_worker.trigger_immediate_analysis(entity_name)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "message": "Sentiment analysis triggered successfully",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger analysis: {str(e)}")


# WebSocket endpoint for real-time sentiment streaming
@router.websocket("/stream")
async def sentiment_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time sentiment updates."""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            
            # Echo back for connection testing
            await websocket.send_json({
                "type": "ping_response",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Connection active"
            })
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        websocket_manager.disconnect(websocket)


# Utility function to broadcast sentiment updates via WebSocket
async def broadcast_sentiment_update(update_data: dict):
    """Broadcast sentiment update to all connected WebSocket clients."""
    await websocket_manager.broadcast({
        "type": "sentiment_update",
        "timestamp": datetime.utcnow().isoformat(),
        "data": update_data
    })


# Health check endpoint
@router.get("/health")
async def sentiment_health_check():
    """Health check for sentiment analysis system."""
    try:
        worker_status = await sentiment_alert_worker.get_worker_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "worker_status": worker_status,
            "services": {
                "sentiment_processor": "active",
                "trend_analyzer": "active",
                "alert_worker": "active" if worker_status["is_running"] else "inactive"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }
@router.get("/integration/status")
async def get_sentiment_integration_status(db: AsyncSession = Depends(get_db)):
    """Get sentiment-news integration status."""
    try:
        from app.services.sentiment_news_integration import SentimentNewsIntegrationService
        
        integration_service = SentimentNewsIntegrationService(db)
        status = await integration_service.get_integration_status()
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting integration status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get integration status: {str(e)}")

@router.get("/integration/analytics")
async def get_sentiment_analytics_data(db: AsyncSession = Depends(get_db)):
    """Get sentiment analytics data for dashboard integration."""
    try:
        from app.services.sentiment_news_integration import SentimentNewsIntegrationService
        
        integration_service = SentimentNewsIntegrationService(db)
        analytics_data = await integration_service.connect_with_analytics_dashboard()
        
        return analytics_data
        
    except Exception as e:
        logger.error(f"Error getting analytics data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics data: {str(e)}")