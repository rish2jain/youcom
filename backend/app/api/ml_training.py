"""
API endpoints for ML Training and Model Management

This module provides REST API endpoints for the ML Accuracy Engine,
including model training, prediction, and registry management.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.ml_training_service import MLTrainingService, ModelType, TriggerType
from app.services.ml_prediction_service import MLPredictionService, PredictionRequest, PredictionType
from app.services.ml_model_registry import MLModelRegistry, ModelStatus, DeploymentStrategy, ABTestConfig

router = APIRouter(prefix="/api/ml", tags=["ML Training"])

# Pydantic models for API requests/responses

class TrainingJobRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_type: ModelType
    trigger_type: TriggerType = TriggerType.MANUAL
    config_override: Optional[Dict[str, Any]] = None

class TrainingJobResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    job_id: str
    model_type: str
    status: str
    created_at: str
    message: str

class PredictionRequestModel(BaseModel):
    entity_id: str
    entity_type: str
    prediction_type: PredictionType
    features: Optional[Dict[str, Any]] = None
    use_cache: bool = True

class PredictionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    prediction_type: str
    predicted_value: Any
    confidence_score: float
    model_version: str
    fallback_used: bool
    processing_time_ms: float
    metadata: Dict[str, Any]

class ModelRegistrationRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_type: ModelType
    version: str
    file_paths: Dict[str, str]
    performance_metrics: Dict[str, float]
    training_config: Dict[str, Any]
    tags: Optional[List[str]] = None
    description: str = ""
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.IMMEDIATE

class ModelDeploymentRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_id: str
    deployment_strategy: Optional[DeploymentStrategy] = None
    ab_test_config: Optional[Dict[str, Any]] = None

class ABTestConfigModel(BaseModel):
    model_config = {"protected_namespaces": ()}

    test_id: str
    model_a_version: str
    model_b_version: str
    traffic_split: float = Field(ge=0.0, le=1.0)
    start_date: datetime
    end_date: datetime
    success_metrics: List[str]
    minimum_samples: int = 100

class RollbackRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_type: ModelType
    target_version: Optional[str] = None
    reason: str = "Manual rollback"

# Training endpoints

@router.post("/training/start", response_model=TrainingJobResponse)
async def start_training_job(
    request: TrainingJobRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start a new model training job."""
    try:
        training_service = MLTrainingService(db)
        
        job_id = await training_service.start_training_job(
            model_type=request.model_type,
            trigger_type=request.trigger_type,
            config_override=request.config_override
        )
        
        return TrainingJobResponse(
            job_id=job_id,
            model_type=request.model_type.value,
            status="pending",
            created_at=datetime.utcnow().isoformat(),
            message="Training job started successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start training job: {str(e)}")

@router.get("/training/triggers")
async def check_training_triggers(db: AsyncSession = Depends(get_db)):
    """Check for models that need retraining."""
    try:
        training_service = MLTrainingService(db)
        triggers = await training_service.check_retraining_triggers()
        
        return {
            "triggers": [
                {
                    "model_type": model_type.value,
                    "trigger_type": trigger_type.value
                }
                for model_type, trigger_type in triggers
            ],
            "count": len(triggers)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check triggers: {str(e)}")

@router.get("/training/job/{job_id}")
async def get_training_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get the status of a training job."""
    try:
        training_service = MLTrainingService(db)
        job_status = await training_service.get_training_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail="Training job not found")
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@router.get("/training/performance/{model_type}")
async def get_model_performance_history(
    model_type: ModelType,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Get performance history for a model type."""
    try:
        training_service = MLTrainingService(db)
        history = await training_service.get_model_performance_history(model_type, days)
        
        return {
            "model_type": model_type.value,
            "days": days,
            "history": history
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance history: {str(e)}")

# Prediction endpoints

@router.post("/predict", response_model=PredictionResponse)
async def make_prediction(
    request: PredictionRequestModel,
    db: AsyncSession = Depends(get_db)
):
    """Make a prediction using ML models."""
    try:
        prediction_service = MLPredictionService(db)
        
        prediction_request = PredictionRequest(
            entity_id=request.entity_id,
            entity_type=request.entity_type,
            prediction_type=request.prediction_type,
            features=request.features,
            use_cache=request.use_cache
        )
        
        result = await prediction_service.predict(prediction_request)
        
        return PredictionResponse(
            prediction_type=result.prediction_type.value,
            predicted_value=result.predicted_value,
            confidence_score=result.confidence_score,
            model_version=result.model_version,
            fallback_used=result.fallback_used,
            processing_time_ms=result.processing_time_ms,
            metadata=result.metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/predict/batch")
async def make_batch_predictions(
    requests: List[PredictionRequestModel],
    db: AsyncSession = Depends(get_db)
):
    """Make batch predictions for multiple requests."""
    try:
        prediction_service = MLPredictionService(db)
        
        prediction_requests = [
            PredictionRequest(
                entity_id=req.entity_id,
                entity_type=req.entity_type,
                prediction_type=req.prediction_type,
                features=req.features,
                use_cache=req.use_cache
            )
            for req in requests
        ]
        
        results = await prediction_service.predict_batch(prediction_requests)
        
        return {
            "predictions": [
                PredictionResponse(
                    prediction_type=result.prediction_type.value,
                    predicted_value=result.predicted_value,
                    confidence_score=result.confidence_score,
                    model_version=result.model_version,
                    fallback_used=result.fallback_used,
                    processing_time_ms=result.processing_time_ms,
                    metadata=result.metadata
                )
                for result in results
            ],
            "count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@router.delete("/predict/cache/{entity_type}/{entity_id}")
async def invalidate_prediction_cache(
    entity_type: str,
    entity_id: str,
    prediction_type: Optional[PredictionType] = None,
    db: AsyncSession = Depends(get_db)
):
    """Invalidate cached predictions for an entity."""
    try:
        prediction_service = MLPredictionService(db)
        
        deleted_count = await prediction_service.invalidate_prediction_cache(
            entity_id=entity_id,
            entity_type=entity_type,
            prediction_type=prediction_type
        )
        
        return {
            "message": f"Invalidated {deleted_count} cached predictions",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")

@router.get("/predict/stats")
async def get_prediction_statistics(
    days: int = Query(7, ge=1, le=30),
    db: AsyncSession = Depends(get_db)
):
    """Get prediction service statistics."""
    try:
        prediction_service = MLPredictionService(db)
        stats = await prediction_service.get_prediction_statistics(days)
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prediction statistics: {str(e)}")

# Model registry endpoints

@router.post("/registry/register")
async def register_model(
    request: ModelRegistrationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new model version in the registry."""
    try:
        registry = MLModelRegistry(db)
        
        model_id = await registry.register_model(
            model_type=request.model_type,
            version=request.version,
            file_paths=request.file_paths,
            performance_metrics=request.performance_metrics,
            training_config=request.training_config,
            tags=request.tags,
            description=request.description,
            deployment_strategy=request.deployment_strategy
        )
        
        return {
            "model_id": model_id,
            "message": "Model registered successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register model: {str(e)}")

@router.post("/registry/deploy")
async def deploy_model(
    request: ModelDeploymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Deploy a model version to production."""
    try:
        registry = MLModelRegistry(db)
        
        ab_test_config = None
        if request.ab_test_config:
            ab_test_config = ABTestConfig(**request.ab_test_config)
        
        success = await registry.deploy_model(
            model_id=request.model_id,
            deployment_strategy=request.deployment_strategy,
            ab_test_config=ab_test_config
        )
        
        if success:
            return {"message": "Model deployed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Model deployment failed")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deploy model: {str(e)}")

@router.post("/registry/rollback")
async def rollback_model(
    request: RollbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """Rollback to a previous model version."""
    try:
        registry = MLModelRegistry(db)
        
        success = await registry.rollback_model(
            model_type=request.model_type,
            target_version=request.target_version,
            reason=request.reason
        )
        
        if success:
            return {"message": "Model rollback completed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Model rollback failed")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rollback model: {str(e)}")

@router.get("/registry/models")
async def list_models(
    model_type: Optional[ModelType] = None,
    status: Optional[ModelStatus] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """List models in the registry."""
    try:
        registry = MLModelRegistry(db)
        models = await registry.list_models(model_type, status, limit)
        
        return {
            "models": [
                {
                    "model_id": model.model_id,
                    "model_type": model.model_type.value,
                    "version": model.version,
                    "status": model.status.value,
                    "created_at": model.created_at.isoformat(),
                    "deployed_at": model.deployed_at.isoformat() if model.deployed_at else None,
                    "performance_metrics": model.performance_metrics,
                    "tags": model.tags,
                    "description": model.description
                }
                for model in models
            ],
            "count": len(models)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

@router.get("/registry/models/{model_id}")
async def get_model_info(model_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed information about a specific model."""
    try:
        registry = MLModelRegistry(db)
        model = await registry.get_model_info(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return {
            "model_id": model.model_id,
            "model_type": model.model_type.value,
            "version": model.version,
            "status": model.status.value,
            "created_at": model.created_at.isoformat(),
            "deployed_at": model.deployed_at.isoformat() if model.deployed_at else None,
            "performance_metrics": model.performance_metrics,
            "training_config": model.training_config,
            "file_paths": model.file_paths,
            "checksum": model.checksum,
            "tags": model.tags,
            "description": model.description
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@router.get("/registry/version/{model_type}")
async def get_active_model_version(
    model_type: ModelType,
    for_ab_test: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get the active model version for a model type."""
    try:
        registry = MLModelRegistry(db)
        version = await registry.get_model_version(model_type, for_ab_test)
        
        return {
            "model_type": model_type.value,
            "active_version": version,
            "ab_test_enabled": for_ab_test
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model version: {str(e)}")

@router.delete("/registry/cleanup")
async def cleanup_old_models(
    days: int = Query(90, ge=30, le=365),
    db: AsyncSession = Depends(get_db)
):
    """Clean up old inactive models."""
    try:
        registry = MLModelRegistry(db)
        cleanup_count = await registry.cleanup_old_models(days)
        
        return {
            "message": f"Cleaned up {cleanup_count} old models",
            "cleanup_count": cleanup_count,
            "days_threshold": days
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup models: {str(e)}")

@router.get("/registry/stats")
async def get_registry_statistics(db: AsyncSession = Depends(get_db)):
    """Get model registry statistics."""
    try:
        registry = MLModelRegistry(db)
        stats = await registry.get_registry_statistics()
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get registry statistics: {str(e)}")

# Health check endpoint

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check for ML services."""
    try:
        # Check database connection
        await db.execute("SELECT 1")
        
        # Check services
        training_service = MLTrainingService(db)
        prediction_service = MLPredictionService(db)
        registry = MLModelRegistry(db)
        
        # Get basic stats
        prediction_stats = await prediction_service.get_prediction_statistics(1)
        registry_stats = await registry.get_registry_statistics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "training": "available",
                "prediction": "available",
                "registry": "available"
            },
            "loaded_models": prediction_stats.get("loaded_models", 0),
            "total_registered_models": sum(
                sum(status_counts.values()) 
                for status_counts in registry_stats.get("model_counts", {}).values()
            ),
            "cache_enabled": prediction_stats.get("cache_enabled", False)
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")