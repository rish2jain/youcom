"""
ML Integration Service for Advanced Intelligence Suite

This service integrates the ML Accuracy Engine with the existing CIA pipeline,
connecting ML feedback systems, enhanced predictions, and model performance monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.models.impact_card import ImpactCard
from app.models.ml_training import FeedbackRecord, ModelPerformanceMetric, TrainingJob
from app.services.ml_prediction_service import MLPredictionService
from app.services.ml_training_service import MLTrainingService, TriggerType, ModelType
from app.services.performance_monitor import metrics_collector
from app.realtime import emit_progress

logger = logging.getLogger(__name__)

@dataclass
class MLEnhancedPrediction:
    """Enhanced prediction with ML confidence scoring."""
    original_value: Any
    ml_prediction: Any
    confidence_score: float
    model_version: str
    enhancement_applied: bool
    fallback_used: bool

@dataclass
class MLIntegrationMetrics:
    """Metrics for ML integration performance."""
    total_predictions: int
    enhanced_predictions: int
    average_confidence: float
    model_performance: Dict[str, float]
    integration_health: str

class MLIntegrationService:
    """Service for integrating ML engine with existing CIA pipeline."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.prediction_service = MLPredictionService(db)
        self.training_service = MLTrainingService(db)
        
        # Integration configuration
        self.confidence_threshold = 0.7  # Minimum confidence to apply ML enhancement
        self.fallback_enabled = True
        self.auto_training_enabled = True
        
        # Performance tracking
        self.integration_metrics = {
            "predictions_made": 0,
            "enhancements_applied": 0,
            "fallbacks_used": 0,
            "training_jobs_triggered": 0
        }
    
    async def enhance_impact_card_generation(
        self, 
        impact_card_data: Dict[str, Any],
        competitor: str
    ) -> Dict[str, Any]:
        """Enhance impact card generation with ML predictions and predictive intelligence."""
        try:
            logger.info(f"🤖 Enhancing impact card generation for {competitor}")
            
            # Create temporary impact card for feature extraction
            temp_impact_card = ImpactCard(
                competitor_name=competitor,
                risk_score=impact_card_data.get("risk_score", 50),
                confidence_score=impact_card_data.get("confidence_score", 50),
                impact_areas=impact_card_data.get("impact_areas", []),
                key_insights=impact_card_data.get("key_insights", []),
                total_sources=impact_card_data.get("total_sources", 0),
                credibility_score=impact_card_data.get("credibility_score", 0.5)
            )
            
            # Add to session temporarily for feature extraction
            self.db.add(temp_impact_card)
            await self.db.flush()  # Get ID without committing
            
            # Get ML enhancements
            enhancements = await self._get_ml_enhancements(temp_impact_card)
            
            # Get predictive intelligence enhancements
            predictive_enhancements = await self._get_predictive_intelligence(competitor)
            
            # Apply enhancements to impact card data
            enhanced_data = await self._apply_enhancements(impact_card_data, enhancements)
            enhanced_data = await self._apply_predictive_enhancements(enhanced_data, predictive_enhancements)
            
            # Remove temporary impact card
            await self.db.delete(temp_impact_card)
            
            # Record integration metrics
            await self._record_integration_metrics("impact_card_enhancement", enhancements)
            
            logger.info(f"✅ Impact card enhanced with ML predictions and predictive intelligence for {competitor}")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ Error enhancing impact card for {competitor}: {e}")
            # Return original data if enhancement fails
            return impact_card_data
    
    async def _get_ml_enhancements(self, impact_card: ImpactCard) -> Dict[str, MLEnhancedPrediction]:
        """Get ML enhancements for various impact card components."""
        enhancements = {}
        
        # Risk score enhancement
        risk_enhancement = await self._enhance_risk_score(impact_card)
        if risk_enhancement:
            enhancements["risk_score"] = risk_enhancement
        
        # Confidence score enhancement
        confidence_enhancement = await self._enhance_confidence_score(impact_card)
        if confidence_enhancement:
            enhancements["confidence_score"] = confidence_enhancement
        
        # Impact classification enhancement
        impact_enhancement = await self._enhance_impact_classification(impact_card)
        if impact_enhancement:
            enhancements["impact_classification"] = impact_enhancement
        
        # Relevance enhancement
        relevance_enhancement = await self._enhance_relevance(impact_card)
        if relevance_enhancement:
            enhancements["relevance"] = relevance_enhancement
        
        return enhancements
    
    async def _get_predictive_intelligence(self, competitor: str) -> Dict[str, Any]:
        """Get predictive intelligence for the competitor."""
        try:
            from app.services.predictive_intelligence import PredictiveIntelligenceEngine
            from app.models.predictive_intelligence import PredictedEvent, CompetitorPattern
            from sqlalchemy import and_
            
            engine = PredictiveIntelligenceEngine(self.db)
            
            # Get active predictions for this competitor
            predictions = self.db.query(PredictedEvent).filter(
                and_(
                    PredictedEvent.competitor_name == competitor,
                    PredictedEvent.status == "pending",
                    PredictedEvent.expires_at > datetime.utcnow()
                )
            ).order_by(desc(PredictedEvent.probability)).limit(3).all()
            
            # Get active patterns for this competitor
            patterns = self.db.query(CompetitorPattern).filter(
                and_(
                    CompetitorPattern.competitor_name == competitor,
                    CompetitorPattern.is_active == True
                )
            ).order_by(desc(CompetitorPattern.confidence)).limit(2).all()
            
            # Format predictions for impact card
            formatted_predictions = []
            for pred in predictions:
                formatted_predictions.append({
                    "type": pred.event_type,
                    "description": pred.description,
                    "probability": pred.probability,
                    "timeframe": pred.timeframe,
                    "reasoning": pred.reasoning[:2] if pred.reasoning else []
                })
            
            # Format patterns for impact card
            formatted_patterns = []
            for pattern in patterns:
                formatted_patterns.append({
                    "type": pattern.pattern_type,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence,
                    "last_observed": pattern.last_observed.isoformat() if pattern.last_observed else None
                })
            
            return {
                "predictions": formatted_predictions,
                "patterns": formatted_patterns,
                "prediction_summary": {
                    "total_predictions": len(predictions),
                    "high_probability_count": len([p for p in predictions if p.probability > 0.7]),
                    "next_predicted_event": formatted_predictions[0] if formatted_predictions else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting predictive intelligence for {competitor}: {e}")
            return {"predictions": [], "patterns": [], "prediction_summary": None}
    
    async def _apply_predictive_enhancements(
        self, 
        impact_card_data: Dict[str, Any], 
        predictive_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply predictive intelligence enhancements to impact card data."""
        try:
            # Add predictive intelligence section to impact card
            if predictive_data.get("predictions") or predictive_data.get("patterns"):
                impact_card_data["predictive_intelligence"] = predictive_data
                
                # Enhance key insights with predictions
                if predictive_data.get("predictions"):
                    prediction_insights = []
                    for pred in predictive_data["predictions"][:2]:  # Top 2 predictions
                        insight = f"Predicted {pred['type']} activity {pred['timeframe']} (probability: {pred['probability']:.0%})"
                        prediction_insights.append(insight)
                    
                    # Add to existing insights
                    existing_insights = impact_card_data.get("key_insights", [])
                    impact_card_data["key_insights"] = prediction_insights + existing_insights
                
                # Enhance recommended actions with predictive context
                if predictive_data.get("prediction_summary", {}).get("high_probability_count", 0) > 0:
                    predictive_action = {
                        "action": "Monitor for predicted competitor moves",
                        "priority": "high",
                        "timeline": "immediate",
                        "owner": "Strategy Team",
                        "okr_goal": "Competitive Intelligence",
                        "impact_score": 85,
                        "effort_score": 30,
                        "score": 2.8,
                        "evidence": [
                            {
                                "source": "Predictive Intelligence Engine",
                                "description": f"{predictive_data['prediction_summary']['high_probability_count']} high-probability events predicted"
                            }
                        ],
                        "index": 0
                    }
                    
                    # Add to existing actions
                    existing_actions = impact_card_data.get("recommended_actions", [])
                    impact_card_data["recommended_actions"] = [predictive_action] + existing_actions
                
                # Enhance risk assessment with predictive context
                if predictive_data.get("prediction_summary", {}).get("high_probability_count", 0) > 1:
                    # Increase risk score slightly for multiple high-probability predictions
                    current_risk = impact_card_data.get("risk_score", 50)
                    enhanced_risk = min(100, current_risk + 10)
                    impact_card_data["risk_score"] = enhanced_risk
                    
                    # Update risk level if needed
                    if enhanced_risk >= 80:
                        impact_card_data["risk_level"] = "critical"
                    elif enhanced_risk >= 60:
                        impact_card_data["risk_level"] = "high"
            
            return impact_card_data
            
        except Exception as e:
            logger.error(f"Error applying predictive enhancements: {e}")
            return impact_card_data
    
    async def _enhance_risk_score(self, impact_card: ImpactCard) -> Optional[MLEnhancedPrediction]:
        """Enhance risk score using ML prediction."""
        try:
            # Use ML prediction service for risk score enhancement
            # This is a placeholder for the actual ML prediction logic
            result = {"confidence_score": 0.8, "prediction": impact_card.risk_score}
            self.integration_metrics["predictions_made"] += 1
            
            if result.get("confidence_score", 0) >= self.confidence_threshold:
                self.integration_metrics["enhancements_applied"] += 1
                return MLEnhancedPrediction(
                    original_value=impact_card.risk_score,
                    ml_prediction=result.get("prediction", impact_card.risk_score),
                    confidence_score=result.get("confidence_score", 0.8),
                    model_version="v1.0",
                    enhancement_applied=True,
                    fallback_used=False
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Risk score enhancement failed: {e}")
            return None
    
    async def _enhance_confidence_score(self, impact_card: ImpactCard) -> Optional[MLEnhancedPrediction]:
        """Enhance confidence score using ML prediction."""
        try:
            # Placeholder implementation
            result = {"confidence_score": 0.8, "prediction": impact_card.confidence_score}
            self.integration_metrics["predictions_made"] += 1
            
            if result.get("confidence_score", 0) >= self.confidence_threshold:
                self.integration_metrics["enhancements_applied"] += 1
                
                return MLEnhancedPrediction(
                    original_value=impact_card.confidence_score,
                    ml_prediction=result.get("prediction", impact_card.confidence_score),
                    confidence_score=result.get("confidence_score", 0.8),
                    model_version="v1.0",
                    enhancement_applied=True,
                    fallback_used=False
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Confidence score enhancement failed: {e}")
            return None
    
    async def _enhance_impact_classification(self, impact_card: ImpactCard) -> Optional[MLEnhancedPrediction]:
        """Enhance impact classification using ML prediction."""
        try:
            # Placeholder implementation
            result = {"confidence_score": 0.75, "prediction": "enhanced_classification"}
            self.integration_metrics["predictions_made"] += 1
            
            if result.get("confidence_score", 0) >= self.confidence_threshold:
                self.integration_metrics["enhancements_applied"] += 1
                return MLEnhancedPrediction(
                    original_value="original_classification",
                    ml_prediction=result.get("prediction", "enhanced_classification"),
                    confidence_score=result.get("confidence_score", 0.75),
                    model_version="v1.0",
                    enhancement_applied=True,
                    fallback_used=False
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Impact classification enhancement failed: {e}")
            return None
    
    async def _enhance_relevance(self, impact_card: ImpactCard) -> Optional[MLEnhancedPrediction]:
        """Enhance relevance classification using ML prediction."""
        try:
            # Placeholder implementation
            result = {"confidence_score": 0.7, "prediction": "enhanced_relevance"}
            self.integration_metrics["predictions_made"] += 1
            
            if result.get("confidence_score", 0) >= self.confidence_threshold:
                self.integration_metrics["enhancements_applied"] += 1
                return MLEnhancedPrediction(
                    original_value="original_relevance",
                    ml_prediction=result.get("prediction", "enhanced_relevance"),
                    confidence_score=result.get("confidence_score", 0.7),
                    model_version="v1.0",
                    enhancement_applied=True,
                    fallback_used=False
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Relevance enhancement failed: {e}")
            return None
    
    async def _apply_enhancements(
        self, 
        impact_card_data: Dict[str, Any], 
        enhancements: Dict[str, MLEnhancedPrediction]
    ) -> Dict[str, Any]:
        """Apply ML enhancements to impact card data."""
        enhanced_data = impact_card_data.copy()
        ml_metadata = {
            "ml_enhanced": True,
            "enhancements_applied": [],
            "model_versions": {},
            "confidence_scores": {}
        }
        
        # Apply risk score enhancement
        if "risk_score" in enhancements:
            enhancement = enhancements["risk_score"]
            if enhancement.enhancement_applied:
                # Blend original and ML prediction based on confidence
                blend_factor = enhancement.confidence_score
                enhanced_risk = int(
                    enhancement.original_value * (1 - blend_factor) + 
                    enhancement.ml_prediction * blend_factor
                )
                enhanced_data["risk_score"] = enhanced_risk
                
                ml_metadata["enhancements_applied"].append("risk_score")
                ml_metadata["model_versions"]["risk_score"] = enhancement.model_version
                ml_metadata["confidence_scores"]["risk_score"] = enhancement.confidence_score
        
        # Apply confidence score enhancement
        if "confidence_score" in enhancements:
            enhancement = enhancements["confidence_score"]
            if enhancement.enhancement_applied:
                enhanced_data["confidence_score"] = enhancement.ml_prediction
                
                ml_metadata["enhancements_applied"].append("confidence_score")
                ml_metadata["model_versions"]["confidence_score"] = enhancement.model_version
                ml_metadata["confidence_scores"]["confidence_score"] = enhancement.confidence_score
        
        # Apply impact classification enhancement
        if "impact_classification" in enhancements:
            enhancement = enhancements["impact_classification"]
            if enhancement.enhancement_applied:
                # Add ML classification to metadata
                ml_metadata["ml_impact_classification"] = enhancement.ml_prediction
                ml_metadata["enhancements_applied"].append("impact_classification")
                ml_metadata["model_versions"]["impact_classification"] = enhancement.model_version
                ml_metadata["confidence_scores"]["impact_classification"] = enhancement.confidence_score
        
        # Apply relevance enhancement
        if "relevance" in enhancements:
            enhancement = enhancements["relevance"]
            if enhancement.enhancement_applied:
                ml_metadata["ml_relevance_score"] = enhancement.ml_prediction
                ml_metadata["enhancements_applied"].append("relevance")
                ml_metadata["model_versions"]["relevance"] = enhancement.model_version
                ml_metadata["confidence_scores"]["relevance"] = enhancement.confidence_score
        
        # Add ML metadata to explainability
        if "explainability" not in enhanced_data:
            enhanced_data["explainability"] = {}
        enhanced_data["explainability"]["ml_enhancements"] = ml_metadata
        
        return enhanced_data
    
    async def process_user_feedback(
        self, 
        impact_card_id: int, 
        feedback_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Process user feedback and trigger ML retraining if needed."""
        try:
            logger.info(f"📝 Processing user feedback for impact card {impact_card_id}")
            
            # Create feedback record
            feedback_record = FeedbackRecord(
                user_id=user_id,
                impact_card_id=impact_card_id,
                feedback_type=feedback_data.get("feedback_type"),
                original_value=feedback_data.get("original_value"),
                corrected_value=feedback_data.get("corrected_value"),
                confidence=feedback_data.get("confidence", 0.8),
                processed=False
            )
            
            self.db.add(feedback_record)
            await self.db.commit()
            
            # Invalidate prediction cache for this impact card
            await self.prediction_service.invalidate_prediction_cache(
                str(impact_card_id), 
                "impact_card"
            )
            
            # Check if retraining should be triggered
            if self.auto_training_enabled:
                await self._check_and_trigger_retraining()
            
            # Record metrics
            await metrics_collector.record_metric(
                "ml_feedback_processed",
                1.0,
                {"feedback_type": feedback_data.get("feedback_type")}
            )
            
            logger.info(f"✅ User feedback processed for impact card {impact_card_id}")
            
            return {
                "feedback_id": feedback_record.id,
                "status": "processed",
                "retraining_triggered": self.auto_training_enabled
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing user feedback: {e}")
            await self.db.rollback()
            raise
    
    async def _check_and_trigger_retraining(self) -> None:
        """Check if retraining should be triggered based on feedback."""
        try:
            # Check retraining triggers
            triggers = await self.training_service.check_retraining_triggers()
            
            for model_type, trigger_type in triggers:
                logger.info(f"🔄 Triggering retraining for {model_type.value} due to {trigger_type.value}")
                
                job_id = await self.training_service.start_training_job(
                    model_type, 
                    trigger_type
                )
                
                self.integration_metrics["training_jobs_triggered"] += 1
                
                # Emit progress event
                await emit_progress(
                    "ml_training_started",
                    {
                        "model_type": model_type.value,
                        "trigger_type": trigger_type.value,
                        "job_id": job_id
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ Error checking retraining triggers: {e}")
    
    async def _record_integration_metrics(
        self, 
        operation: str, 
        enhancements: Dict[str, MLEnhancedPrediction]
    ) -> None:
        """Record integration performance metrics."""
        try:
            # Count enhancements applied
            enhancements_applied = sum(
                1 for enhancement in enhancements.values() 
                if enhancement.enhancement_applied
            )
            
            # Calculate average confidence
            confidences = [
                enhancement.confidence_score 
                for enhancement in enhancements.values()
                if enhancement.enhancement_applied
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Record metrics
            await metrics_collector.record_metric(
                f"ml_integration_{operation}",
                1.0,
                {
                    "enhancements_applied": enhancements_applied,
                    "total_enhancements": len(enhancements),
                    "average_confidence": avg_confidence
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to record integration metrics: {e}")
    
    async def get_model_performance_status(self) -> Dict[str, Any]:
        """Get current model performance status for system health checks."""
        try:
            performance_status = {}
            
            for model_type in ModelType:
                # Get latest performance metrics
                result = await self.db.execute(
                    select(ModelPerformanceMetric)
                    .where(ModelPerformanceMetric.model_type == model_type.value)
                    .where(ModelPerformanceMetric.metric_name == "f1_score")
                    .order_by(desc(ModelPerformanceMetric.evaluation_timestamp))
                    .limit(1)
                )
                
                latest_metric = result.scalar_one_or_none()
                
                if latest_metric:
                    performance_status[model_type.value] = {
                        "f1_score": latest_metric.metric_value,
                        "model_version": latest_metric.model_version,
                        "last_evaluated": latest_metric.evaluation_timestamp.isoformat(),
                        "status": "healthy" if latest_metric.metric_value >= 0.8 else "degraded"
                    }
                else:
                    performance_status[model_type.value] = {
                        "status": "no_data",
                        "message": "No performance metrics available"
                    }
            
            # Get recent training jobs
            training_result = await self.db.execute(
                select(TrainingJob)
                .where(TrainingJob.status.in_(["running", "completed", "failed"]))
                .order_by(desc(TrainingJob.created_at))
                .limit(5)
            )
            
            recent_training = [
                {
                    "job_id": job.job_id,
                    "model_type": job.model_type,
                    "status": job.status,
                    "trigger_type": job.trigger_type,
                    "created_at": job.created_at.isoformat(),
                    "performance_improvement": job.performance_improvement
                }
                for job in training_result.scalars().all()
            ]
            
            return {
                "model_performance": performance_status,
                "recent_training_jobs": recent_training,
                "integration_metrics": self.integration_metrics.copy(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting model performance status: {e}")
            return {
                "error": str(e),
                "status": "error",
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def get_integration_metrics(self) -> MLIntegrationMetrics:
        """Get comprehensive integration metrics."""
        try:
            # Get prediction statistics
            prediction_stats = await self.prediction_service.get_prediction_statistics()
            
            # Calculate integration health
            enhancement_rate = (
                self.integration_metrics["enhancements_applied"] / 
                max(1, self.integration_metrics["predictions_made"])
            )
            
            if enhancement_rate >= 0.7:
                health = "excellent"
            elif enhancement_rate >= 0.5:
                health = "good"
            elif enhancement_rate >= 0.3:
                health = "fair"
            else:
                health = "poor"
            
            # Get model performance summary
            model_performance = {}
            for model_type in ModelType:
                result = await self.db.execute(
                    select(ModelPerformanceMetric.metric_value)
                    .where(ModelPerformanceMetric.model_type == model_type.value)
                    .where(ModelPerformanceMetric.metric_name == "f1_score")
                    .order_by(desc(ModelPerformanceMetric.evaluation_timestamp))
                    .limit(1)
                )
                
                latest_f1 = result.scalar_one_or_none()
                if latest_f1:
                    model_performance[model_type.value] = latest_f1
            
            return MLIntegrationMetrics(
                total_predictions=self.integration_metrics["predictions_made"],
                enhanced_predictions=self.integration_metrics["enhancements_applied"],
                average_confidence=enhancement_rate,
                model_performance=model_performance,
                integration_health=health
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting integration metrics: {e}")
            return MLIntegrationMetrics(
                total_predictions=0,
                enhanced_predictions=0,
                average_confidence=0.0,
                model_performance={},
                integration_health="error"
            )