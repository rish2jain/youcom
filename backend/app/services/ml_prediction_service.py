"""
ML Prediction Service with Confidence Scoring

This service provides enhanced predictions with confidence scores for the ML Accuracy Engine.
It includes fallback mechanisms, prediction caching, and optimization for real-time inference.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
import joblib
from sklearn.base import BaseEstimator
from sklearn.preprocessing import StandardScaler

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.ml_training import TrainingJob, ModelPerformanceMetric
from app.models.impact_card import ImpactCard
from app.services.feature_extractor import FeatureExtractor, FeatureSet
from app.services.ml_training_service import ModelType
from app.config import settings

logger = logging.getLogger(__name__)

class PredictionType(str, Enum):
    """Types of predictions the service can make."""
    IMPACT_CLASSIFICATION = "impact_classification"
    RISK_SCORING = "risk_scoring"
    CONFIDENCE_PREDICTION = "confidence_prediction"
    RELEVANCE_CLASSIFICATION = "relevance_classification"

@dataclass
class PredictionRequest:
    """Request for ML prediction."""
    entity_id: str
    entity_type: str
    prediction_type: PredictionType
    features: Optional[Dict[str, Any]] = None
    use_cache: bool = True

@dataclass
class PredictionResult:
    """Result of ML prediction with confidence scoring."""
    prediction_type: PredictionType
    predicted_value: Any
    confidence_score: float
    model_version: str
    fallback_used: bool
    processing_time_ms: float
    metadata: Dict[str, Any]

@dataclass
class ModelInfo:
    """Information about a loaded model."""
    model: BaseEstimator
    scaler: StandardScaler
    version: str
    model_type: ModelType
    performance_metrics: Dict[str, float]
    loaded_at: datetime

class MLPredictionService:
    """Service for ML predictions with confidence scoring and caching."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.feature_extractor = FeatureExtractor(db)
        self.model_storage_path = os.path.join(settings.data_dir, "ml_models")
        self.scalers_storage_path = os.path.join(settings.data_dir, "ml_scalers")
        
        # Model cache
        self.loaded_models: Dict[ModelType, ModelInfo] = {}
        self.model_cache_ttl = timedelta(hours=6)
        
        # Redis for prediction caching
        self.redis_client: Optional[redis.Redis] = None
        self.prediction_cache_ttl = timedelta(hours=1)
        self.redis_prefix = "ml_predictions:"
        
        # Fallback rules
        self.fallback_rules = {
            PredictionType.IMPACT_CLASSIFICATION: self._fallback_impact_classification,
            PredictionType.RISK_SCORING: self._fallback_risk_scoring,
            PredictionType.CONFIDENCE_PREDICTION: self._fallback_confidence_prediction,
            PredictionType.RELEVANCE_CLASSIFICATION: self._fallback_relevance_classification
        }
    
    async def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get or create Redis client."""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Prediction caching disabled.")
                self.redis_client = None
        
        return self.redis_client
    
    async def predict(self, request: PredictionRequest) -> PredictionResult:
        """Make a prediction with confidence scoring."""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Check cache first
            if request.use_cache:
                cached_result = await self._get_cached_prediction(request)
                if cached_result:
                    return cached_result
            
            # Get model type for prediction type
            model_type = self._get_model_type_for_prediction(request.prediction_type)
            
            # Load model if needed
            model_info = await self._load_model(model_type)
            
            if not model_info:
                # Use fallback
                return await self._fallback_prediction(request, start_time)
            
            # Extract features if not provided
            if not request.features:
                features = await self._extract_features_for_prediction(request)
                if not features:
                    return await self._fallback_prediction(request, start_time)
            else:
                features = request.features
            
            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features, model_info)
            
            # Make prediction
            prediction = model_info.model.predict([feature_vector])[0]
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                model_info, feature_vector, prediction, request.prediction_type
            )
            
            # Create result
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            result = PredictionResult(
                prediction_type=request.prediction_type,
                predicted_value=prediction,
                confidence_score=confidence_score,
                model_version=model_info.version,
                fallback_used=False,
                processing_time_ms=processing_time,
                metadata={
                    "model_type": model_info.model_type.value,
                    "feature_count": len(feature_vector),
                    "model_performance": model_info.performance_metrics
                }
            )
            
            # Cache result
            if request.use_cache:
                await self._cache_prediction(request, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return await self._fallback_prediction(request, start_time, error=str(e))
    
    def _get_model_type_for_prediction(self, prediction_type: PredictionType) -> ModelType:
        """Map prediction type to model type."""
        mapping = {
            PredictionType.IMPACT_CLASSIFICATION: ModelType.IMPACT_CLASSIFIER,
            PredictionType.RISK_SCORING: ModelType.RISK_SCORER,
            PredictionType.CONFIDENCE_PREDICTION: ModelType.CONFIDENCE_PREDICTOR,
            PredictionType.RELEVANCE_CLASSIFICATION: ModelType.RELEVANCE_CLASSIFIER
        }
        return mapping[prediction_type]
    
    async def _load_model(self, model_type: ModelType) -> Optional[ModelInfo]:
        """Load model and scaler from storage."""
        # Check if model is already loaded and not expired
        if model_type in self.loaded_models:
            model_info = self.loaded_models[model_type]
            if datetime.now(timezone.utc) - model_info.loaded_at < self.model_cache_ttl:
                return model_info
            else:
                # Remove expired model
                del self.loaded_models[model_type]
        
        try:
            # Get latest model version
            result = await self.db.execute(
                select(TrainingJob)
                .where(TrainingJob.model_type == model_type.value)
                .where(TrainingJob.status == "completed")
                .order_by(desc(TrainingJob.completed_at))
                .limit(1)
            )
            
            latest_job = result.scalar_one_or_none()
            if not latest_job:
                logger.warning(f"No trained model found for {model_type.value}")
                return None
            
            model_version = latest_job.new_model_version
            
            # Load model and scaler
            model_path = os.path.join(self.model_storage_path, f"{model_version}.joblib")
            scaler_path = os.path.join(self.scalers_storage_path, f"{model_version}_scaler.joblib")
            
            if not os.path.exists(model_path) or not os.path.exists(scaler_path):
                logger.error(f"Model files not found for {model_version}")
                return None
            
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            
            # Get performance metrics
            metrics_result = await self.db.execute(
                select(ModelPerformanceMetric)
                .where(ModelPerformanceMetric.model_version == model_version)
            )
            
            metrics_records = metrics_result.scalars().all()
            performance_metrics = {
                record.metric_name: record.metric_value 
                for record in metrics_records
            }
            
            # Create model info
            model_info = ModelInfo(
                model=model,
                scaler=scaler,
                version=model_version,
                model_type=model_type,
                performance_metrics=performance_metrics,
                loaded_at=datetime.now(timezone.utc)
            )
            
            # Cache loaded model
            self.loaded_models[model_type] = model_info
            
            logger.info(f"Loaded model {model_version} for {model_type.value}")
            return model_info
            
        except Exception as e:
            logger.error(f"Failed to load model for {model_type.value}: {e}")
            return None
    
    async def _extract_features_for_prediction(self, request: PredictionRequest) -> Optional[Dict[str, Any]]:
        """Extract features for prediction."""
        try:
            if request.entity_type == "impact_card":
                # Get impact card
                result = await self.db.execute(
                    select(ImpactCard).where(ImpactCard.id == int(request.entity_id))
                )
                impact_card = result.scalar_one_or_none()
                
                if not impact_card:
                    return None
                
                # Extract features
                feature_set = await self.feature_extractor.extract_impact_card_features(impact_card)
                
                # Convert to dictionary
                features = {}
                for feature in feature_set.features:
                    if feature.feature_type.value in ["numerical", "categorical"]:
                        features[feature.name] = feature.value
                
                return features
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract features for prediction: {e}")
            return None
    
    def _prepare_feature_vector(self, features: Dict[str, Any], model_info: ModelInfo) -> np.ndarray:
        """Prepare feature vector for model input."""
        # Create DataFrame with features
        df = pd.DataFrame([features])
        
        # Handle missing features (fill with 0)
        expected_features = model_info.scaler.feature_names_in_ if hasattr(model_info.scaler, 'feature_names_in_') else None
        
        if expected_features is not None:
            for feature in expected_features:
                if feature not in df.columns:
                    df[feature] = 0.0
            
            # Reorder columns to match training
            df = df[expected_features]
        
        # Fill missing values
        df = df.fillna(0)
        
        # Scale features
        feature_vector = model_info.scaler.transform(df)[0]
        
        return feature_vector
    
    def _calculate_confidence_score(
        self, 
        model_info: ModelInfo, 
        feature_vector: np.ndarray, 
        prediction: Any,
        prediction_type: PredictionType
    ) -> float:
        """Calculate confidence score for the prediction."""
        try:
            base_confidence = 0.5
            
            # Use model's predict_proba if available (for classifiers)
            if hasattr(model_info.model, 'predict_proba'):
                probabilities = model_info.model.predict_proba([feature_vector])[0]
                # Use max probability as confidence
                base_confidence = float(np.max(probabilities))
            
            # Adjust confidence based on model performance
            f1_score = model_info.performance_metrics.get("f1_score", 0.5)
            performance_adjustment = f1_score * 0.3  # Up to 30% boost from performance
            
            # Adjust confidence based on prediction type
            type_adjustment = self._get_type_confidence_adjustment(prediction_type, prediction)
            
            # Combine adjustments
            final_confidence = base_confidence + performance_adjustment + type_adjustment
            
            # Clamp to [0.0, 1.0]
            return max(0.0, min(1.0, final_confidence))
            
        except Exception as e:
            logger.warning(f"Failed to calculate confidence score: {e}")
            return 0.5  # Default confidence
    
    def _get_type_confidence_adjustment(self, prediction_type: PredictionType, prediction: Any) -> float:
        """Get confidence adjustment based on prediction type and value."""
        if prediction_type == PredictionType.RISK_SCORING:
            # Higher confidence for extreme risk scores
            if isinstance(prediction, (int, float)):
                if prediction > 80 or prediction < 20:
                    return 0.1  # 10% boost for extreme values
        
        elif prediction_type == PredictionType.CONFIDENCE_PREDICTION:
            # Confidence predictions are inherently less certain
            return -0.1  # 10% penalty
        
        return 0.0
    
    async def _fallback_prediction(
        self, 
        request: PredictionRequest, 
        start_time: datetime,
        error: Optional[str] = None
    ) -> PredictionResult:
        """Generate fallback prediction when ML model fails."""
        fallback_func = self.fallback_rules.get(request.prediction_type)
        
        if fallback_func:
            prediction, confidence = await fallback_func(request)
        else:
            prediction, confidence = 0.5, 0.3  # Default fallback
        
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        return PredictionResult(
            prediction_type=request.prediction_type,
            predicted_value=prediction,
            confidence_score=confidence,
            model_version="fallback",
            fallback_used=True,
            processing_time_ms=processing_time,
            metadata={
                "fallback_reason": error or "Model not available",
                "fallback_method": "rule_based"
            }
        )
    
    async def _fallback_impact_classification(self, request: PredictionRequest) -> Tuple[float, float]:
        """Fallback for impact classification."""
        try:
            if request.entity_type == "impact_card":
                # Get impact card
                result = await self.db.execute(
                    select(ImpactCard).where(ImpactCard.id == int(request.entity_id))
                )
                impact_card = result.scalar_one_or_none()
                
                if impact_card:
                    # Rule-based classification based on risk score and sources
                    risk_score = impact_card.risk_score or 0
                    total_sources = impact_card.total_sources or 0
                    credibility = impact_card.credibility_score or 0.5
                    
                    # Simple rule: high impact if risk > 70, sources > 2, credibility > 0.6
                    if risk_score > 70 and total_sources > 2 and credibility > 0.6:
                        return 1.0, 0.6  # High impact, moderate confidence
                    elif risk_score > 40 and total_sources > 1:
                        return 0.7, 0.5  # Medium impact, lower confidence
                    else:
                        return 0.3, 0.4  # Low impact, low confidence
            
            return 0.5, 0.3  # Default
            
        except Exception:
            return 0.5, 0.3
    
    async def _fallback_risk_scoring(self, request: PredictionRequest) -> Tuple[float, float]:
        """Fallback for risk scoring."""
        try:
            if request.entity_type == "impact_card":
                # Get impact card
                result = await self.db.execute(
                    select(ImpactCard).where(ImpactCard.id == int(request.entity_id))
                )
                impact_card = result.scalar_one_or_none()
                
                if impact_card:
                    # Use existing risk score with slight adjustment
                    base_risk = impact_card.risk_score or 50
                    
                    # Adjust based on sources and credibility
                    sources_adjustment = min(10, (impact_card.total_sources or 0) * 2)
                    credibility_adjustment = (impact_card.credibility_score or 0.5) * 10
                    
                    adjusted_risk = base_risk + sources_adjustment + credibility_adjustment
                    return min(100, max(0, adjusted_risk)), 0.5
            
            return 50.0, 0.3  # Default medium risk
            
        except Exception:
            return 50.0, 0.3
    
    async def _fallback_confidence_prediction(self, request: PredictionRequest) -> Tuple[float, float]:
        """Fallback for confidence prediction."""
        try:
            if request.entity_type == "impact_card":
                # Get impact card
                result = await self.db.execute(
                    select(ImpactCard).where(ImpactCard.id == int(request.entity_id))
                )
                impact_card = result.scalar_one_or_none()
                
                if impact_card:
                    # Base confidence on existing confidence score and credibility
                    base_confidence = (impact_card.confidence_score or 50) / 100
                    credibility_boost = (impact_card.credibility_score or 0.5) * 0.2
                    
                    final_confidence = min(1.0, base_confidence + credibility_boost)
                    return final_confidence, 0.4
            
            return 0.5, 0.3  # Default
            
        except Exception:
            return 0.5, 0.3
    
    async def _fallback_relevance_classification(self, request: PredictionRequest) -> Tuple[float, float]:
        """Fallback for relevance classification."""
        try:
            if request.entity_type == "impact_card":
                # Get impact card
                result = await self.db.execute(
                    select(ImpactCard).where(ImpactCard.id == int(request.entity_id))
                )
                impact_card = result.scalar_one_or_none()
                
                if impact_card:
                    # Rule-based relevance based on risk and recency
                    risk_score = impact_card.risk_score or 0
                    
                    # Check recency (more recent = more relevant)
                    if impact_card.created_at:
                        hours_old = (datetime.now(timezone.utc) - impact_card.created_at).total_seconds() / 3600
                        recency_factor = max(0, 1 - (hours_old / 168))  # Decay over a week
                    else:
                        recency_factor = 0.5
                    
                    # Combine risk and recency
                    relevance_score = (risk_score / 100) * 0.7 + recency_factor * 0.3
                    
                    return min(1.0, relevance_score), 0.5
            
            return 0.5, 0.3  # Default
            
        except Exception:
            return 0.5, 0.3
    
    async def _get_cached_prediction(self, request: PredictionRequest) -> Optional[PredictionResult]:
        """Get cached prediction if available."""
        redis_client = await self._get_redis_client()
        if not redis_client:
            return None
        
        try:
            cache_key = f"{self.redis_prefix}{request.prediction_type.value}:{request.entity_type}:{request.entity_id}"
            cached_data = await redis_client.get(cache_key)
            
            if not cached_data:
                return None
            
            data = json.loads(cached_data)
            
            return PredictionResult(
                prediction_type=PredictionType(data["prediction_type"]),
                predicted_value=data["predicted_value"],
                confidence_score=data["confidence_score"],
                model_version=data["model_version"],
                fallback_used=data["fallback_used"],
                processing_time_ms=data["processing_time_ms"],
                metadata=data["metadata"]
            )
            
        except Exception as e:
            logger.warning(f"Failed to get cached prediction: {e}")
            return None
    
    async def _cache_prediction(self, request: PredictionRequest, result: PredictionResult) -> None:
        """Cache prediction result."""
        redis_client = await self._get_redis_client()
        if not redis_client:
            return
        
        try:
            cache_key = f"{self.redis_prefix}{request.prediction_type.value}:{request.entity_type}:{request.entity_id}"
            
            cache_data = {
                "prediction_type": result.prediction_type.value,
                "predicted_value": result.predicted_value,
                "confidence_score": result.confidence_score,
                "model_version": result.model_version,
                "fallback_used": result.fallback_used,
                "processing_time_ms": result.processing_time_ms,
                "metadata": result.metadata,
                "cached_at": datetime.now(timezone.utc).isoformat()
            }
            
            await redis_client.setex(
                cache_key,
                int(self.prediction_cache_ttl.total_seconds()),
                json.dumps(cache_data, default=str)
            )
            
        except Exception as e:
            logger.warning(f"Failed to cache prediction: {e}")
    
    async def predict_batch(self, requests: List[PredictionRequest]) -> List[PredictionResult]:
        """Make batch predictions for multiple requests."""
        results = []
        
        # Group requests by prediction type for efficiency
        grouped_requests = {}
        for i, request in enumerate(requests):
            if request.prediction_type not in grouped_requests:
                grouped_requests[request.prediction_type] = []
            grouped_requests[request.prediction_type].append((i, request))
        
        # Process each group
        for prediction_type, type_requests in grouped_requests.items():
            model_type = self._get_model_type_for_prediction(prediction_type)
            model_info = await self._load_model(model_type)
            
            for original_index, request in type_requests:
                result = await self.predict(request)
                results.append((original_index, result))
        
        # Sort results back to original order
        results.sort(key=lambda x: x[0])
        return [result for _, result in results]
    
    async def invalidate_prediction_cache(
        self, 
        entity_id: str, 
        entity_type: str,
        prediction_type: Optional[PredictionType] = None
    ) -> int:
        """Invalidate cached predictions for an entity."""
        redis_client = await self._get_redis_client()
        if not redis_client:
            return 0
        
        try:
            if prediction_type:
                # Invalidate specific prediction type
                cache_key = f"{self.redis_prefix}{prediction_type.value}:{entity_type}:{entity_id}"
                deleted = await redis_client.delete(cache_key)
                return deleted
            else:
                # Invalidate all prediction types for entity using SCAN
                pattern = f"{self.redis_prefix}*:{entity_type}:{entity_id}"
                keys = []
                cursor = 0
                while True:
                    cursor, batch_keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
                    keys.extend(batch_keys)
                    if cursor == 0:
                        break
                
                if keys:
                    # Delete in batches to avoid large operations
                    deleted = 0
                    batch_size = 100
                    for i in range(0, len(keys), batch_size):
                        batch = keys[i:i + batch_size]
                        deleted += await redis_client.delete(*batch)
                    return deleted
                return 0
                
        except Exception as e:
            logger.warning(f"Failed to invalidate prediction cache: {e}")
            return 0
    
    async def get_prediction_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get prediction service statistics."""
        redis_client = await self._get_redis_client()
        
        stats = {
            "loaded_models": len(self.loaded_models),
            "model_info": {},
            "cache_enabled": redis_client is not None,
            "cache_stats": {}
        }
        
        # Model information
        for model_type, model_info in self.loaded_models.items():
            stats["model_info"][model_type.value] = {
                "version": model_info.version,
                "loaded_at": model_info.loaded_at.isoformat(),
                "performance_metrics": model_info.performance_metrics
            }
        
        # Cache statistics
        if redis_client:
            try:
                pattern = f"{self.redis_prefix}*"
                keys = []
                cursor = 0
                while True:
                    cursor, batch_keys = await redis_client.scan(cursor=cursor, match=pattern, count=100)
                    keys.extend(batch_keys)
                    if cursor == 0:
                        break
                
                stats["cache_stats"]["total_cached_predictions"] = len(keys)
                
                # Sample some keys to get cache hit info
                if keys:
                    sample_keys = keys[:min(10, len(keys))]
                    cache_info = []
                    for key in sample_keys:
                        ttl = await redis_client.ttl(key)
                        cache_info.append({"key": key, "ttl_seconds": ttl})
                    stats["cache_stats"]["sample_cache_info"] = cache_info
                
            except Exception as e:
                logger.warning(f"Failed to get cache statistics: {e}")
        
        return stats