"""
Advanced Intelligence API Endpoints - Week 3 Implementation
Multi-agent AI system and predictive intelligence endpoints.
"""

import logging
import json
import redis
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from redis.connection import ConnectionPool

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.multi_agent_orchestrator import multi_agent_orchestrator
from app.services.predictive_intelligence import predictive_intelligence, PredictionType
from app.services.auth_service import get_current_user
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/intelligence", tags=["Advanced Intelligence"])

# Redis client for batch results storage with production-ready configuration
try:
    pool = ConnectionPool.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        max_connections=20,
        health_check_interval=30
    )
    redis_client = redis.Redis(connection_pool=pool)
    # Test connection
    redis_client.ping()
    logger.info("✅ Redis connection established successfully")
except Exception as e:
    logger.error(f"❌ Redis connection failed: {str(e)}")
    redis_client = None

# Batch storage wrapper functions
def get_batch_result(batch_id: str) -> Optional[Dict[str, Any]]:
    """Get batch result from Redis"""
    if not redis_client:
        logger.warning("Redis not available, batch result not found")
        return None
    
    try:
        result = redis_client.get(f"batch:{batch_id}")
        return json.loads(result) if result else None
    except Exception as e:
        logger.error(f"Failed to get batch result {batch_id}: {str(e)}")
        return None

def set_batch_result(batch_id: str, data: Dict[str, Any], ttl: int = 86400) -> bool:
    """Set batch result in Redis with TTL and maintain user batch set atomically"""
    if not redis_client:
        logger.warning("Redis not available, batch result not stored")
        return False
    
    try:
        user_id = data.get("user_id")
        if user_id:
            # Use pipeline for atomic operations
            pipe = redis_client.pipeline()
            # Store batch result with TTL
            pipe.setex(f"batch:{batch_id}", ttl, json.dumps(data))
            # Add to user's batch sorted set with expiry timestamp as score
            expiry_timestamp = (datetime.utcnow() + timedelta(seconds=ttl)).timestamp()
            pipe.zadd(f"user:{user_id}:batches", {batch_id: expiry_timestamp})
            # Execute atomically
            pipe.execute()
        else:
            redis_client.setex(f"batch:{batch_id}", ttl, json.dumps(data))
        return True
    except Exception as e:
        logger.error(f"Failed to set batch result {batch_id}: {str(e)}")
        return False

def delete_batch_result(batch_id: str, user_id: Optional[int] = None) -> bool:
    """Delete batch result from Redis"""
    if not redis_client:
        logger.warning("Redis not available, batch result not deleted")
        return False
    
    try:
        redis_client.delete(f"batch:{batch_id}")
        if user_id:
            # Remove from user's batch sorted set
            redis_client.zrem(f"user:{user_id}:batches", batch_id)
        return True
    except Exception as e:
        logger.error(f"Failed to delete batch result {batch_id}: {str(e)}")
        return False

def list_batch_results(user_id: int) -> List[str]:
    """List batch results for a user, removing expired entries"""
    if not redis_client:
        logger.warning("Redis not available, returning empty batch list")
        return []
    
    try:
        user_batch_set = f"user:{user_id}:batches"
        current_timestamp = datetime.utcnow().timestamp()
        
        # Remove expired batch IDs from sorted set
        redis_client.zremrangebyscore(user_batch_set, 0, current_timestamp)
        
        # Get remaining batch IDs
        batch_ids = redis_client.zrange(user_batch_set, 0, -1)
        return list(batch_ids) if batch_ids else []
    except Exception as e:
        logger.error(f"Failed to list batch results for user {user_id}: {str(e)}")
        return []

# Request/Response Models
class ComprehensiveIntelligenceRequest(BaseModel):
    competitor: str = Field(..., description="Competitor to analyze")
    analysis_depth: str = Field(default="comprehensive", description="Analysis depth: standard, comprehensive, deep")
    include_strategy: bool = Field(default=True, description="Include strategic recommendations")
    include_predictions: bool = Field(default=False, description="Include predictive analysis")

class PredictiveAnalysisRequest(BaseModel):
    company: str = Field(..., description="Company to analyze")
    prediction_types: Optional[List[str]] = Field(default=None, description="Types of predictions to generate")
    time_horizons: Optional[List[str]] = Field(default=None, description="Time horizons for predictions")

class MultiAgentStatusResponse(BaseModel):
    orchestrator_status: str
    agents: Dict[str, Any]
    active_tasks: int
    completed_tasks: int

class ComprehensiveIntelligenceResponse(BaseModel):
    competitor: str
    session_id: str
    executive_summary: Dict[str, Any]
    research_intelligence: Dict[str, Any]
    competitive_analysis: Dict[str, Any]
    strategic_intelligence: Dict[str, Any]
    multi_agent_metadata: Dict[str, Any]
    quality_metrics: Dict[str, Any]

class BatchAnalysisRequest(BaseModel):
    companies: List[str] = Field(..., min_length=1, max_length=10, description="List of companies to analyze")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis to perform")
    processing_time: str

class PredictiveAnalysisResponse(BaseModel):
    company: str
    generated_at: str
    predictions: List[Dict[str, Any]]
    prediction_summary: Dict[str, Any]
    engine_metadata: Dict[str, Any]

# Multi-Agent Intelligence Endpoints
@router.post("/multi-agent/comprehensive", response_model=ComprehensiveIntelligenceResponse)
async def generate_comprehensive_intelligence(
    request: ComprehensiveIntelligenceRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate comprehensive competitive intelligence using multi-agent system"""
    logger.info(f"🤖 Comprehensive intelligence requested for {request.competitor} by {current_user.email}")
    
    try:
        # Initialize multi-agent orchestrator if needed
        if not multi_agent_orchestrator.orchestrator:
            await multi_agent_orchestrator.initialize()
        
        # Generate comprehensive intelligence
        intelligence_result = await multi_agent_orchestrator.generate_comprehensive_intelligence(
            competitor=request.competitor,
            analysis_depth=request.analysis_depth,
            include_strategy=request.include_strategy
        )
        
        # Add predictive analysis if requested
        if request.include_predictions:
            background_tasks.add_task(
                _add_predictive_analysis,
                request.competitor,
                intelligence_result,
                current_user.id
            )
        
        logger.info(f"✅ Comprehensive intelligence generated for {request.competitor}")
        
        return ComprehensiveIntelligenceResponse(**intelligence_result)
        
    except Exception as e:
        logger.error(f"❌ Comprehensive intelligence generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate comprehensive intelligence: {str(e)}"
        )

@router.get("/multi-agent/status", response_model=MultiAgentStatusResponse)
async def get_multi_agent_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of multi-agent system"""
    logger.info(f"📊 Multi-agent status requested by {current_user.email}")
    
    try:
        status = await multi_agent_orchestrator.get_agent_status()
        return MultiAgentStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"❌ Failed to get multi-agent status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get multi-agent status: {str(e)}"
        )

@router.post("/multi-agent/initialize")
async def initialize_multi_agent_system(
    current_user: User = Depends(get_current_user)
):
    """Initialize multi-agent system"""
    logger.info(f"🚀 Multi-agent initialization requested by {current_user.email}")
    
    try:
        await multi_agent_orchestrator.initialize()
        
        return {
            "status": "initialized",
            "message": "Multi-agent system initialized successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Multi-agent initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize multi-agent system: {str(e)}"
        )

# Predictive Intelligence Endpoints
@router.post("/predictive/analyze", response_model=PredictiveAnalysisResponse)
async def generate_predictive_analysis(
    request: PredictiveAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate predictive analysis for a company"""
    logger.info(f"🔮 Predictive analysis requested for {request.company} by {current_user.email}")
    
    try:
        # Parse prediction types
        prediction_types = []
        if request.prediction_types:
            for pred_type in request.prediction_types:
                try:
                    prediction_types.append(PredictionType(pred_type))
                except ValueError:
                    logger.warning(f"Invalid prediction type: {pred_type}")
        
        # Gather company data (simplified - would integrate with research agents)
        company_data = await _gather_company_data(request.company)
        market_data = await _gather_market_data(request.company)
        
        # Generate predictions
        predictions_result = await predictive_intelligence.generate_comprehensive_predictions(
            company=request.company,
            company_data=company_data,
            market_data=market_data,
            prediction_types=prediction_types if prediction_types else None
        )
        
        logger.info(f"✅ Predictive analysis generated for {request.company}")
        
        return PredictiveAnalysisResponse(**predictions_result)
        
    except Exception as e:
        logger.error(f"❌ Predictive analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate predictive analysis: {str(e)}"
        )

@router.get("/predictive/types")
async def get_prediction_types():
    """Get available prediction types"""
    return {
        "prediction_types": [
            {
                "value": pred_type.value,
                "label": pred_type.value.replace("_", " ").title(),
                "description": _get_prediction_description(pred_type)
            }
            for pred_type in PredictionType
        ]
    }

@router.post("/predictive/funding/{company}")
async def predict_funding_round(
    company: str,
    time_horizon: str = "6_months",
    current_user: User = Depends(get_current_user)
):
    """Predict funding round for specific company"""
    logger.info(f"💰 Funding prediction requested for {company} by {current_user.email}")
    
    try:
        # Gather company data
        company_data = await _gather_company_data(company)
        market_data = await _gather_market_data(company)
        
        # Generate funding prediction
        funding_prediction = await predictive_intelligence.funding_predictor.predict_funding_round(
            company=company,
            company_data=company_data,
            market_data=market_data,
            time_horizon=time_horizon
        )
        
        return {
            "company": company,
            "prediction_type": "funding_round",
            "prediction": funding_prediction.prediction,
            "probability": funding_prediction.probability,
            "confidence_level": funding_prediction.confidence_level.value,
            "time_horizon": funding_prediction.time_horizon,
            "supporting_factors": funding_prediction.supporting_factors,
            "risk_factors": funding_prediction.risk_factors,
            "generated_at": funding_prediction.generated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Funding prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to predict funding round: {str(e)}"
        )

@router.post("/predictive/product-launch/{company}")
async def predict_product_launch(
    company: str,
    time_horizon: str = "3_months",
    current_user: User = Depends(get_current_user)
):
    """Predict product launch for specific company"""
    logger.info(f"🚀 Product launch prediction requested for {company} by {current_user.email}")
    
    try:
        # Gather company data
        company_data = await _gather_company_data(company)
        
        # Generate product launch prediction
        launch_prediction = await predictive_intelligence.product_predictor.predict_product_launch(
            company=company,
            company_data=company_data,
            time_horizon=time_horizon
        )
        
        return {
            "company": company,
            "prediction_type": "product_launch",
            "prediction": launch_prediction.prediction,
            "probability": launch_prediction.probability,
            "confidence_level": launch_prediction.confidence_level.value,
            "time_horizon": launch_prediction.time_horizon,
            "supporting_factors": launch_prediction.supporting_factors,
            "risk_factors": launch_prediction.risk_factors,
            "generated_at": launch_prediction.generated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Product launch prediction failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to predict product launch: {str(e)}"
        )

# Real-time Intelligence WebSocket
@router.websocket("/ws/intelligence/{session_id}")
async def intelligence_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time intelligence updates"""
    await websocket.accept()
    logger.info(f"🔌 Intelligence WebSocket connected: {session_id}")
    
    try:
        while True:
            # Wait for client messages
            data = await websocket.receive_text()
            message = eval(data)  # In production, use proper JSON parsing
            
            if message.get("type") == "start_analysis":
                competitor = message.get("competitor", "")
                
                # Define progress callback
                async def progress_callback(phase: str, data: Dict[str, Any]):
                    await websocket.send_text(str({
                        "type": "progress_update",
                        "phase": phase,
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                # Start comprehensive analysis with real-time updates
                try:
                    result = await multi_agent_orchestrator.generate_comprehensive_intelligence(
                        competitor=competitor,
                        analysis_depth="comprehensive",
                        include_strategy=True,
                        progress_callback=progress_callback
                    )
                    
                    # Send final result
                    await websocket.send_text(str({
                        "type": "analysis_complete",
                        "result": result,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    
                except Exception as e:
                    await websocket.send_text(str({
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            
    except WebSocketDisconnect:
        logger.info(f"🔌 Intelligence WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"❌ Intelligence WebSocket error: {str(e)}")
        await websocket.close()

# Batch Intelligence Processing
@router.post("/batch/analyze")
async def batch_intelligence_analysis(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Process batch intelligence analysis for multiple companies"""
    companies = request.companies
    analysis_type = request.analysis_type
    logger.info(f"📦 Batch analysis requested for {len(companies)} companies by {current_user.email}")
    
    try:
        batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Start batch processing in background
        background_tasks.add_task(
            _process_batch_analysis,
            batch_id,
            companies,
            analysis_type,
            current_user.id
        )
        
        return {
            "batch_id": batch_id,
            "status": "processing",
            "companies": companies,
            "analysis_type": analysis_type,
            "estimated_completion": "5-10 minutes",
            "message": "Batch analysis started. Check status using batch_id."
        }
        
    except Exception as e:
        logger.error(f"❌ Batch analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start batch analysis: {str(e)}"
        )

@router.get("/batch/{batch_id}/status")
async def get_batch_status(
    batch_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of batch intelligence analysis"""
    logger.info(f"📊 Batch status requested for {batch_id} by {current_user.email}")
    
    # Check batch results store
    result = get_batch_result(batch_id)
    if not result:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Check authorization - ensure user can access this batch
    if result.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return result

# Helper functions
async def _gather_company_data(company: str) -> Dict[str, Any]:
    """Gather company data for analysis"""
    # In production, this would integrate with research agents
    # For now, return mock data structure
    return {
        "company_name": company,
        "articles": [
            {"title": f"{company} announces new product", "content": "Product development news"},
            {"title": f"{company} hiring surge", "content": "Hiring 50 new engineers"}
        ],
        "media_coverage_score": 0.7,
        "innovation_score": 0.6
    }

async def _gather_market_data(company: str) -> Dict[str, Any]:
    """Gather market data for analysis"""
    # Mock market data
    return {
        "market_sentiment": 0.6,
        "competitive_pressure": 0.5,
        "growth_rate": 0.15
    }

def _get_prediction_description(pred_type: PredictionType) -> str:
    """Get description for prediction type"""
    descriptions = {
        PredictionType.FUNDING_ROUND: "Predict likelihood of upcoming funding rounds",
        PredictionType.PRODUCT_LAUNCH: "Predict probability of new product launches",
        PredictionType.MARKET_EXPANSION: "Predict market expansion and geographic growth",
        PredictionType.ACQUISITION: "Predict acquisition likelihood and targets",
        PredictionType.PARTNERSHIP: "Predict strategic partnerships and alliances",
        PredictionType.COMPETITIVE_MOVE: "Predict competitive moves and strategic changes"
    }
    return descriptions.get(pred_type, "Advanced predictive analysis")

# Background task functions
async def _add_predictive_analysis(
    competitor: str,
    intelligence_result: Dict[str, Any],
    user_id: int
):
    """Background task to add predictive analysis"""
    try:
        logger.info(f"🔮 Adding predictive analysis for {competitor}")
        
        # Gather data from intelligence result
        company_data = {
            "articles": intelligence_result.get("research_intelligence", {}).get("data_sources", {}),
            "competitive_analysis": intelligence_result.get("competitive_analysis", {})
        }
        
        # Generate predictions
        predictions = await predictive_intelligence.generate_comprehensive_predictions(
            company=competitor,
            company_data=company_data
        )
        
        # In production, would store results in database
        logger.info(f"✅ Predictive analysis completed for {competitor}")
        
    except Exception as e:
        logger.error(f"❌ Background predictive analysis failed: {str(e)}")

async def _process_batch_analysis(
    batch_id: str,
    companies: List[str],
    analysis_type: str,
    user_id: int
):
    """Background task to process batch analysis"""
    try:
        logger.info(f"📦 Processing batch analysis {batch_id} for {len(companies)} companies")
        
        results = []
        for company in companies:
            try:
                # Generate intelligence for each company
                if analysis_type == "comprehensive":
                    result = await multi_agent_orchestrator.generate_comprehensive_intelligence(
                        competitor=company,
                        analysis_depth="standard",
                        include_strategy=False
                    )
                else:
                    # Simplified analysis
                    company_data = await _gather_company_data(company)
                    market_data = await _gather_market_data(company)
                    result = await predictive_intelligence.generate_comprehensive_predictions(
                        company=company,
                        company_data=company_data,
                        market_data=market_data
                    )
                
                results.append({"company": company, "result": result, "status": "completed"})
                
            except Exception as e:
                logger.error(f"❌ Batch analysis failed for {company}: {str(e)}")
                results.append({"company": company, "error": str(e), "status": "failed"})
        
        # Store batch results in Redis with user_id
        batch_data = {
            "status": "completed",
            "results": results,
            "completed_at": datetime.utcnow().isoformat(),
            "user_id": user_id
        }
        set_batch_result(batch_id, batch_data, ttl=86400)  # 24 hour TTL
        logger.info(f"✅ Batch analysis {batch_id} completed")
        
    except Exception as e:
        logger.error(f"❌ Batch analysis {batch_id} failed: {str(e)}")
        batch_data = {
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat(),
            "user_id": user_id
        }
        set_batch_result(batch_id, batch_data, ttl=86400)



# Health check
@router.get("/health")
async def advanced_intelligence_health():
    """Advanced intelligence services health check"""
    try:
        # Check multi-agent system
        multi_agent_status = await multi_agent_orchestrator.get_agent_status()
        
        return {
            "status": "healthy",
            "services": {
                "multi_agent_system": "active" if multi_agent_status.get("orchestrator_status") == "active" else "inactive",
                "predictive_intelligence": "active",
                "batch_processing": "active"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }