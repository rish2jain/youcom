"""API endpoints for predictive intelligence functionality."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.predictive_intelligence import CompetitorPattern, PredictedEvent, PatternEvent
from app.models.impact_card import ImpactCard
from app.schemas.predictive_intelligence import (
    CompetitorPatternSchema,
    PredictedEventSchema,
    PatternEventSchema,
    PredictionValidationRequest,
    PatternAnalysisRequest,
    PredictionGenerationRequest,
    PredictiveIntelligenceMetrics,
    EnhancedImpactCardSchema,
    MLModelPerformance,
    PredictionDashboardData
)
from app.services.predictive_intelligence import PredictiveIntelligenceEngine
from app.services.ml_prediction_service import MLPredictionService

router = APIRouter(prefix="/predictive", tags=["predictive-intelligence"])
logger = logging.getLogger(__name__)

def get_ml_service(db: Session = Depends(get_db)) -> MLPredictionService:
    """Get ML service instance with fresh DB session."""
    ml_service = MLPredictionService(db)
    ml_service.initialize_models()
    return ml_service


@router.post("/patterns/analyze", response_model=List[CompetitorPatternSchema])
async def analyze_competitor_patterns(
    request: PatternAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Analyze competitor patterns from historical data."""
    try:
        engine = PredictiveIntelligenceEngine(db)
        
        # Check if patterns already exist and are recent
        if not request.force_reanalysis:
            existing_patterns = db.query(CompetitorPattern).filter(
                and_(
                    CompetitorPattern.competitor_name == request.competitor_name,
                    CompetitorPattern.is_active == True,
                    CompetitorPattern.updated_at > datetime.utcnow() - timedelta(days=7)
                )
            ).all()
            
            if existing_patterns:
                logger.info(f"Using existing patterns for {request.competitor_name}")
                return existing_patterns
        
        # Analyze patterns
        patterns = engine.analyze_competitor_patterns(request.competitor_name)
        
        # Filter by minimum confidence
        filtered_patterns = [
            pattern for pattern in patterns 
            if pattern.confidence >= request.min_confidence
        ]
        
        # Train ML models in background if we have enough data
        background_tasks.add_task(train_ml_models_if_needed)
        
        logger.info(f"Analyzed {len(filtered_patterns)} patterns for {request.competitor_name}")
        return filtered_patterns
        
    except Exception as e:
        logger.error(f"Error analyzing patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze patterns: {str(e)}"
        )


@router.post("/predictions/generate", response_model=List[PredictedEventSchema])
async def generate_predictions(
    request: PredictionGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    ml_service: MLPredictionService = Depends(get_ml_service)
):
    """Generate predictions for a competitor based on identified patterns."""
    try:
        engine = PredictiveIntelligenceEngine(db)
        
        # Generate base predictions
        predictions = engine.generate_predictions(request.competitor_name)
        
        # Enhance predictions with ML if models are available
        enhanced_predictions = []
        predictions_updated = False
        
        for prediction in predictions:
            if prediction.probability >= request.min_probability:
                # Get the pattern for this prediction
                pattern = db.query(CompetitorPattern).filter(
                    CompetitorPattern.id == prediction.pattern_id
                ).first()
                
                if pattern:
                    # Convert prediction to dict for ML enhancement
                    pred_dict = {
                        "probability": prediction.probability,
                        "confidence": prediction.confidence,
                        "predicted_date": prediction.predicted_date,
                        "timeframe": prediction.timeframe
                    }
                    
                    # Enhance with ML
                    enhanced_dict = ml_service.enhance_prediction(pattern, pred_dict)
                    enhanced_dict = ml_service.calculate_confidence_intervals(enhanced_dict, pattern)
                    
                    # Update prediction object with ML enhancements
                    if "ml_probability" in enhanced_dict:
                        prediction.ml_probability = enhanced_dict["ml_probability"]
                        predictions_updated = True
                    if "ml_confidence" in enhanced_dict:
                        prediction.ml_confidence = enhanced_dict["ml_confidence"]
                        predictions_updated = True
                    if "ml_reasoning" in enhanced_dict:
                        prediction.ml_reasoning = enhanced_dict["ml_reasoning"]
                        predictions_updated = True
                    if "confidence_intervals" in enhanced_dict:
                        prediction.confidence_intervals = enhanced_dict["confidence_intervals"]
                        predictions_updated = True
                
                enhanced_predictions.append(prediction)
        
        # Commit all updates at once
        if predictions_updated:
            db.commit()
        
        logger.info(f"Generated {len(enhanced_predictions)} predictions for {request.competitor_name}")
        return enhanced_predictions
        
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate predictions: {str(e)}"
        )


@router.get("/patterns", response_model=List[CompetitorPatternSchema])
async def get_patterns(
    competitor_name: Optional[str] = None,
    pattern_type: Optional[str] = None,
    min_confidence: float = 0.0,
    active_only: bool = True,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get competitor patterns with optional filtering."""
    try:
        query = db.query(CompetitorPattern)
        
        if competitor_name:
            query = query.filter(CompetitorPattern.competitor_name == competitor_name)
        
        if pattern_type:
            query = query.filter(CompetitorPattern.pattern_type == pattern_type)
        
        if min_confidence > 0:
            query = query.filter(CompetitorPattern.confidence >= min_confidence)
        
        if active_only:
            query = query.filter(CompetitorPattern.is_active == True)
        
        patterns = query.order_by(desc(CompetitorPattern.confidence)).limit(limit).all()
        
        return patterns
        
    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patterns: {str(e)}"
        )


@router.get("/predictions", response_model=List[PredictedEventSchema])
async def get_predictions(
    competitor_name: Optional[str] = None,
    event_type: Optional[str] = None,
    status: str = "pending",
    min_probability: float = 0.0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get predictions with optional filtering."""
    try:
        query = db.query(PredictedEvent)
        
        if competitor_name:
            query = query.filter(PredictedEvent.competitor_name == competitor_name)
        
        if event_type:
            query = query.filter(PredictedEvent.event_type == event_type)
        
        if status:
            query = query.filter(PredictedEvent.status == status)
        
        if min_probability > 0:
            query = query.filter(PredictedEvent.probability >= min_probability)
        
        # Only show non-expired predictions
        query = query.filter(
            PredictedEvent.expires_at > datetime.utcnow()
        )
        
        predictions = query.order_by(desc(PredictedEvent.probability)).limit(limit).all()
        
        return predictions
        
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get predictions: {str(e)}"
        )


@router.post("/predictions/{prediction_id}/validate")
async def validate_prediction(
    prediction_id: int,
    validation: PredictionValidationRequest,
    db: Session = Depends(get_db)
):
    """Validate a prediction with actual outcome."""
    try:
        engine = PredictiveIntelligenceEngine(db)
        
        success = engine.validate_prediction(
            prediction_id,
            validation.actual_outcome,
            validation.accuracy_score
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found"
            )
        
        return {
            "message": "Prediction validated successfully",
            "prediction_id": prediction_id,
            "accuracy_score": validation.accuracy_score,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate prediction: {str(e)}"
        )


@router.get("/metrics", response_model=PredictiveIntelligenceMetrics)
async def get_predictive_metrics(db: Session = Depends(get_db)):
    """Get predictive intelligence metrics and performance data."""
    try:
        engine = PredictiveIntelligenceEngine(db)
        
        # Get pattern metrics
        total_patterns = db.query(CompetitorPattern).count()
        active_patterns = db.query(CompetitorPattern).filter(
            CompetitorPattern.is_active == True
        ).count()
        
        # Get prediction metrics
        total_predictions = db.query(PredictedEvent).count()
        pending_predictions = db.query(PredictedEvent).filter(
            and_(
                PredictedEvent.status == "pending",
                PredictedEvent.expires_at > datetime.utcnow()
            )
        ).count()
        validated_predictions = db.query(PredictedEvent).filter(
            PredictedEvent.status.in_(["validated", "invalidated"])
        ).count()
        
        # Get accuracy metrics
        accuracy_metrics = engine.get_pattern_accuracy_metrics()
        
        # Get average confidence scores
        pattern_confidence = db.query(func.avg(CompetitorPattern.confidence)).filter(
            CompetitorPattern.is_active == True
        ).scalar() or 0.0
        
        prediction_confidence = db.query(func.avg(PredictedEvent.confidence)).filter(
            PredictedEvent.status == "pending"
        ).scalar() or 0.0
        
        # Get top competitors by prediction count
        top_competitors_query = db.query(
            PredictedEvent.competitor_name,
            func.count(PredictedEvent.id).label('prediction_count')
        ).filter(
            PredictedEvent.status == "pending"
        ).group_by(PredictedEvent.competitor_name).order_by(
            desc('prediction_count')
        ).limit(5).all()
        
        top_competitors = [
            {"competitor": comp, "predictions": count}
            for comp, count in top_competitors_query
        ]
        
        # Get recent predictions
        recent_predictions = db.query(PredictedEvent).filter(
            PredictedEvent.status == "pending"
        ).order_by(desc(PredictedEvent.created_at)).limit(5).all()
        
        return PredictiveIntelligenceMetrics(
            total_patterns=total_patterns,
            active_patterns=active_patterns,
            total_predictions=total_predictions,
            pending_predictions=pending_predictions,
            validated_predictions=validated_predictions,
            overall_accuracy=accuracy_metrics.get("overall_accuracy", 0.0),
            accuracy_by_type=accuracy_metrics.get("type_metrics", {}),
            pattern_confidence_avg=float(pattern_confidence),
            prediction_confidence_avg=float(prediction_confidence),
            top_competitors=top_competitors,
            recent_predictions=recent_predictions
        )
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/dashboard", response_model=PredictionDashboardData)
async def get_prediction_dashboard(db: Session = Depends(get_db)):
    """Get comprehensive dashboard data for predictive intelligence."""
    try:
        # Get metrics
        metrics_response = await get_predictive_metrics(db)
        
        # Get recent patterns
        recent_patterns = db.query(CompetitorPattern).filter(
            CompetitorPattern.is_active == True
        ).order_by(desc(CompetitorPattern.updated_at)).limit(10).all()
        
        # Get high probability predictions
        high_prob_predictions = db.query(PredictedEvent).filter(
            and_(
                PredictedEvent.status == "pending",
                PredictedEvent.probability >= 0.7,
                PredictedEvent.expires_at > datetime.utcnow()
            )
        ).order_by(desc(PredictedEvent.probability)).limit(10).all()
        
        # Get competitor activity (predictions per competitor)
        competitor_activity_query = db.query(
            PredictedEvent.competitor_name,
            func.count(PredictedEvent.id).label('activity_count')
        ).filter(
            PredictedEvent.created_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(PredictedEvent.competitor_name).all()
        
        competitor_activity = {
            comp: count for comp, count in competitor_activity_query
        }
        
        # Get prediction timeline (predictions by date)
        timeline_query = db.query(
            func.date(PredictedEvent.created_at).label('date'),
            func.count(PredictedEvent.id).label('count')
        ).filter(
            PredictedEvent.created_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(func.date(PredictedEvent.created_at)).order_by('date').all()
        
        prediction_timeline = [
            {"date": date.isoformat(), "count": count}
            for date, count in timeline_query
        ]
        
        # Get ML performance
        ml_service = MLPredictionService(db)
        ml_performance_data = ml_service.get_model_performance_metrics()
        
        ml_performance = MLModelPerformance(
            status=ml_performance_data.get("status", "unknown"),
            total_predictions=ml_performance_data.get("total_predictions", 0),
            accurate_predictions=ml_performance_data.get("accurate_predictions", 0),
            accuracy_rate=ml_performance_data.get("accuracy_rate", 0.0),
            feature_importance=ml_performance_data.get("feature_importance", {}),
            model_types=ml_performance_data.get("model_types", {})
        )
        
        return PredictionDashboardData(
            metrics=metrics_response,
            recent_patterns=recent_patterns,
            high_probability_predictions=high_prob_predictions,
            competitor_activity=competitor_activity,
            prediction_timeline=prediction_timeline,
            ml_performance=ml_performance
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.get("/impact-cards/{card_id}/enhanced", response_model=EnhancedImpactCardSchema)
async def get_enhanced_impact_card(
    card_id: int,
    db: Session = Depends(get_db)
):
    """Get an impact card enhanced with predictive intelligence."""
    try:
        # Get the impact card
        impact_card = db.query(ImpactCard).filter(ImpactCard.id == card_id).first()
        
        if not impact_card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Impact card not found"
            )
        
        # Get related predictions
        predicted_moves = db.query(PredictedEvent).filter(
            and_(
                PredictedEvent.competitor_name == impact_card.competitor_name,
                PredictedEvent.status == "pending",
                PredictedEvent.expires_at > datetime.utcnow()
            )
        ).order_by(desc(PredictedEvent.probability)).limit(5).all()
        
        # Get related patterns
        related_patterns = db.query(CompetitorPattern).filter(
            and_(
                CompetitorPattern.competitor_name == impact_card.competitor_name,
                CompetitorPattern.is_active == True
            )
        ).order_by(desc(CompetitorPattern.confidence)).limit(3).all()
        
        # Create prediction summary
        prediction_summary = None
        if predicted_moves:
            avg_probability = sum(p.probability for p in predicted_moves) / len(predicted_moves)
            next_prediction = min(predicted_moves, key=lambda p: p.predicted_date or datetime.max)
            
            prediction_summary = {
                "total_predictions": len(predicted_moves),
                "average_probability": avg_probability,
                "next_predicted_event": {
                    "type": next_prediction.event_type,
                    "date": next_prediction.predicted_date.isoformat() if next_prediction.predicted_date else None,
                    "probability": next_prediction.probability
                },
                "high_probability_count": len([p for p in predicted_moves if p.probability > 0.7])
            }
        
        return EnhancedImpactCardSchema(
            id=impact_card.id,
            competitor_name=impact_card.competitor_name,
            risk_score=impact_card.risk_score,
            risk_level=impact_card.risk_level,
            confidence_score=impact_card.confidence_score,
            impact_areas=impact_card.impact_areas or [],
            key_insights=impact_card.key_insights or [],
            recommended_actions=impact_card.recommended_actions or [],
            created_at=impact_card.created_at,
            predicted_moves=predicted_moves,
            related_patterns=related_patterns,
            prediction_summary=prediction_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting enhanced impact card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get enhanced impact card: {str(e)}"
        )


@router.post("/ml/train")
async def train_ml_models(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger ML model training."""
    try:
        # Add training task to background
        background_tasks.add_task(train_ml_models_task)
        
        return {
            "message": "ML model training started",
            "status": "training_initiated",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting ML training: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start ML training: {str(e)}"
        )


@router.get("/ml/performance", response_model=MLModelPerformance)
async def get_ml_performance(db: Session = Depends(get_db)):
    """Get ML model performance metrics."""
    try:
        ml_service = MLPredictionService(db)
        performance_data = ml_service.get_model_performance_metrics()
        
        return MLModelPerformance(
            status=performance_data.get("status", "unknown"),
            total_predictions=performance_data.get("total_predictions", 0),
            accurate_predictions=performance_data.get("accurate_predictions", 0),
            accuracy_rate=performance_data.get("accuracy_rate", 0.0),
            feature_importance=performance_data.get("feature_importance", {}),
            model_types=performance_data.get("model_types", {})
        )
        
    except Exception as e:
        logger.error(f"Error getting ML performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ML performance: {str(e)}"
        )


# Background task functions
async def train_ml_models_if_needed():
    """Train ML models if sufficient data is available."""
    try:
        # Create new DB session for background task
        from app.database import SessionLocal
        db = SessionLocal()
        
        try:
            ml_service = MLPredictionService(db)
            
            # Check if we have enough validated predictions for training
            validated_count = db.query(PredictedEvent).filter(
                PredictedEvent.status.in_(["validated", "invalidated"])
            ).count()
            
            if validated_count >= ml_service.min_training_samples:
                logger.info(f"Training ML models with {validated_count} samples")
                training_results = ml_service.train_prediction_models()
                logger.info(f"ML training completed: {training_results}")
            else:
                logger.info(f"Insufficient data for ML training: {validated_count} samples")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in background ML training: {e}")


async def train_ml_models_task():
    """Background task for ML model training."""
    try:
        # Create new DB session for background task
        from app.database import SessionLocal
        db = SessionLocal()
        
        try:
            ml_service = MLPredictionService(db)
            training_results = ml_service.train_prediction_models()
            logger.info(f"Background ML training completed: {training_results}")
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error in background ML training task: {e}")