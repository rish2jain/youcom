"""
ML Model Registry and Versioning Service

This service manages model versions, provides automatic rollback capabilities,
and implements A/B testing framework for model comparison in the ML Accuracy Engine.
"""

import asyncio
import logging
import os
import shutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float, Boolean, select, and_, desc, func
from sqlalchemy.sql import func as sql_func

from app.models.ml_training import TrainingJob, ModelPerformanceMetric
from app.models.ml_model_registry import ModelRegistryRecord, ABTestRecord
from app.services.ml_training_service import ModelType
from app.config import settings

logger = logging.getLogger(__name__)

class ModelStatus(str, Enum):
    """Status of a model in the registry."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    DEPRECATED = "deprecated"
    FAILED = "failed"

class DeploymentStrategy(str, Enum):
    """Deployment strategies for model updates."""
    IMMEDIATE = "immediate"
    GRADUAL = "gradual"
    AB_TEST = "ab_test"
    CANARY = "canary"

@dataclass
class ModelMetadata:
    """Metadata for a registered model."""
    model_id: str
    model_type: ModelType
    version: str
    status: ModelStatus
    created_at: datetime
    deployed_at: Optional[datetime]
    performance_metrics: Dict[str, float]
    training_config: Dict[str, Any]
    file_paths: Dict[str, str]
    checksum: str
    tags: List[str]
    description: str

@dataclass
class ABTestConfig:
    """Configuration for A/B testing between models."""
    test_id: str
    model_a_version: str
    model_b_version: str
    traffic_split: float  # Percentage for model B (0.0 to 1.0)
    start_date: datetime
    end_date: datetime
    success_metrics: List[str]
    minimum_samples: int

@dataclass
class RollbackPlan:
    """Plan for rolling back a model deployment."""
    current_version: str
    target_version: str
    rollback_reason: str
    rollback_strategy: DeploymentStrategy
    estimated_downtime: int  # seconds
    validation_checks: List[str]

class MLModelRegistry:
    """Service for managing ML model versions and deployments."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_storage_path = os.path.join(settings.data_dir, "ml_models")
        self.registry_storage_path = os.path.join(settings.data_dir, "ml_registry")
        
        # Ensure storage directories exist
        os.makedirs(self.model_storage_path, exist_ok=True)
        os.makedirs(self.registry_storage_path, exist_ok=True)
        
        # Active A/B tests cache
        self.active_ab_tests: Dict[ModelType, ABTestConfig] = {}
        self.ab_test_cache_ttl = timedelta(minutes=5)
        self.last_ab_test_refresh = datetime.min
    
    async def register_model(
        self,
        model_type: ModelType,
        version: str,
        file_paths: Dict[str, str],
        performance_metrics: Dict[str, float],
        training_config: Dict[str, Any],
        tags: Optional[List[str]] = None,
        description: str = "",
        deployment_strategy: DeploymentStrategy = DeploymentStrategy.IMMEDIATE
    ) -> str:
        """Register a new model version in the registry."""
        try:
            # Generate model ID
            model_id = f"{model_type.value}_{version}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Calculate checksum of model files
            checksum = await self._calculate_model_checksum(file_paths)
            
            # Copy model files to registry storage
            registry_paths = await self._copy_to_registry(model_id, file_paths)
            
            # Create registry record
            registry_record = ModelRegistryRecord(
                model_id=model_id,
                model_type=model_type.value,
                version=version,
                status=ModelStatus.INACTIVE.value,
                performance_metrics=performance_metrics,
                training_config=training_config,
                file_paths=registry_paths,
                checksum=checksum,
                tags=tags or [],
                description=description,
                deployment_strategy=deployment_strategy.value
            )
            
            self.db.add(registry_record)
            await self.db.commit()
            
            logger.info(f"Registered model {model_id} with version {version}")
            return model_id
            
        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            await self.db.rollback()
            raise
    
    async def deploy_model(
        self,
        model_id: str,
        deployment_strategy: Optional[DeploymentStrategy] = None,
        ab_test_config: Optional[ABTestConfig] = None
    ) -> bool:
        """Deploy a model version to production."""
        try:
            # Get model record
            result = await self.db.execute(
                select(ModelRegistryRecord).where(ModelRegistryRecord.model_id == model_id)
            )
            model_record = result.scalar_one_or_none()
            
            if not model_record:
                raise ValueError(f"Model {model_id} not found in registry")
            
            model_type = ModelType(model_record.model_type)
            strategy = deployment_strategy or DeploymentStrategy(model_record.deployment_strategy)
            
            # Validate model before deployment
            validation_result = await self._validate_model_for_deployment(model_record)
            if not validation_result["valid"]:
                raise ValueError(f"Model validation failed: {validation_result['errors']}")
            
            # Handle different deployment strategies
            if strategy == DeploymentStrategy.IMMEDIATE:
                success = await self._deploy_immediate(model_record)
            
            elif strategy == DeploymentStrategy.AB_TEST:
                if not ab_test_config:
                    raise ValueError("A/B test configuration required for AB_TEST strategy")
                success = await self._deploy_ab_test(model_record, ab_test_config)
            
            elif strategy == DeploymentStrategy.GRADUAL:
                success = await self._deploy_gradual(model_record)
            
            elif strategy == DeploymentStrategy.CANARY:
                success = await self._deploy_canary(model_record)
            
            else:
                raise ValueError(f"Unsupported deployment strategy: {strategy}")
            
            if success:
                # Update model status
                model_record.status = ModelStatus.ACTIVE.value
                model_record.deployed_at = datetime.utcnow()
                await self.db.commit()
                
                logger.info(f"Successfully deployed model {model_id} using {strategy.value} strategy")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to deploy model {model_id}: {e}")
            await self.db.rollback()
            return False
    
    async def _deploy_immediate(self, model_record: ModelRegistryRecord) -> bool:
        """Deploy model immediately, replacing current active model."""
        model_type = ModelType(model_record.model_type)
        
        # Deactivate current active model
        await self._deactivate_current_model(model_type)
        
        # Copy model files to active location
        active_paths = {
            "model": os.path.join(self.model_storage_path, f"{model_record.version}.joblib"),
            "scaler": os.path.join(self.model_storage_path, f"{model_record.version}_scaler.joblib")
        }
        
        try:
            # Copy files to temporary locations first, then atomically rename
            temp_paths = {}
            for file_type, registry_path in model_record.file_paths.items():
                if file_type in active_paths:
                    temp_path = active_paths[file_type] + ".tmp"
                    shutil.copy2(registry_path, temp_path)
                    temp_paths[file_type] = temp_path
            
            # Atomically rename all temp files to final locations
            for file_type, temp_path in temp_paths.items():
                os.rename(temp_path, active_paths[file_type])
            
            return True
            
        except Exception as e:
            # Clean up any partial temp files
            for file_type, temp_path in temp_paths.items():
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
            
            logger.error(f"Failed to deploy model files: {e}")
            return False
    
    async def _deploy_ab_test(self, model_record: ModelRegistryRecord, ab_test_config: ABTestConfig) -> bool:
        """Deploy model as part of an A/B test."""
        model_type = ModelType(model_record.model_type)
        
        # Create A/B test record
        ab_test_record = ABTestRecord(
            test_id=ab_test_config.test_id,
            model_type=model_type.value,
            model_a_version=ab_test_config.model_a_version,
            model_b_version=ab_test_config.model_b_version,
            traffic_split=ab_test_config.traffic_split,
            start_date=ab_test_config.start_date,
            end_date=ab_test_config.end_date,
            success_metrics=ab_test_config.success_metrics,
            minimum_samples=ab_test_config.minimum_samples
        )
        
        self.db.add(ab_test_record)
        await self.db.commit()
        
        # Update cache
        self.active_ab_tests[model_type] = ab_test_config
        
        # Set model status to testing
        model_record.status = ModelStatus.TESTING.value
        
        logger.info(f"Started A/B test {ab_test_config.test_id} for {model_type.value}")
        return True
    
    async def _deploy_gradual(self, model_record: ModelRegistryRecord) -> bool:
        """Deploy model gradually with traffic ramping."""
        # For now, implement as immediate deployment
        # In production, this would involve load balancer configuration
        return await self._deploy_immediate(model_record)
    
    async def _deploy_canary(self, model_record: ModelRegistryRecord) -> bool:
        """Deploy model as canary with monitoring."""
        # For now, implement as immediate deployment
        # In production, this would involve canary deployment infrastructure
        return await self._deploy_immediate(model_record)
    
    async def rollback_model(
        self,
        model_type: ModelType,
        target_version: Optional[str] = None,
        reason: str = "Manual rollback"
    ) -> bool:
        """Rollback to a previous model version."""
        try:
            # Get current active model
            current_result = await self.db.execute(
                select(ModelRegistryRecord)
                .where(ModelRegistryRecord.model_type == model_type.value)
                .where(ModelRegistryRecord.status == ModelStatus.ACTIVE.value)
                .order_by(desc(ModelRegistryRecord.deployed_at))
                .limit(1)
            )
            current_model = current_result.scalar_one_or_none()
            
            if not current_model:
                raise ValueError(f"No active model found for {model_type.value}")
            
            # Get target model (previous version if not specified)
            if target_version:
                target_result = await self.db.execute(
                    select(ModelRegistryRecord)
                    .where(ModelRegistryRecord.model_type == model_type.value)
                    .where(ModelRegistryRecord.version == target_version)
                )
                target_model = target_result.scalar_one_or_none()
            else:
                # Get previous active model
                target_result = await self.db.execute(
                    select(ModelRegistryRecord)
                    .where(ModelRegistryRecord.model_type == model_type.value)
                    .where(ModelRegistryRecord.status.in_([ModelStatus.ACTIVE.value, ModelStatus.INACTIVE.value]))
                    .where(ModelRegistryRecord.deployed_at < current_model.deployed_at)
                    .order_by(desc(ModelRegistryRecord.deployed_at))
                    .limit(1)
                )
                target_model = target_result.scalar_one_or_none()
            
            if not target_model:
                raise ValueError("No suitable rollback target found")
            
            # Create rollback plan
            rollback_plan = RollbackPlan(
                current_version=current_model.version,
                target_version=target_model.version,
                rollback_reason=reason,
                rollback_strategy=DeploymentStrategy.IMMEDIATE,
                estimated_downtime=30,  # seconds
                validation_checks=["model_file_exists", "performance_acceptable"]
            )
            
            # Execute rollback
            success = await self._execute_rollback(rollback_plan, current_model, target_model)
            
            if success:
                logger.info(f"Successfully rolled back {model_type.value} from {current_model.version} to {target_model.version}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rollback model {model_type.value}: {e}")
            return False
    
    async def _execute_rollback(
        self,
        rollback_plan: RollbackPlan,
        current_model: ModelRegistryRecord,
        target_model: ModelRegistryRecord
    ) -> bool:
        """Execute the rollback plan."""
        try:
            # Validate target model
            validation_result = await self._validate_model_for_deployment(target_model)
            if not validation_result["valid"]:
                raise ValueError(f"Target model validation failed: {validation_result['errors']}")
            
            # Deactivate current model
            current_model.status = ModelStatus.INACTIVE.value
            current_model.deprecated_at = datetime.utcnow()
            
            # Activate target model
            target_model.status = ModelStatus.ACTIVE.value
            target_model.deployed_at = datetime.utcnow()
            
            # Copy target model files to active location
            model_type = ModelType(target_model.model_type)
            active_paths = {
                "model": os.path.join(self.model_storage_path, f"{target_model.version}.joblib"),
                "scaler": os.path.join(self.model_storage_path, f"{target_model.version}_scaler.joblib")
            }
            
            for file_type, registry_path in target_model.file_paths.items():
                if file_type in active_paths and os.path.exists(registry_path):
                    shutil.copy2(registry_path, active_paths[file_type])
            
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute rollback: {e}")
            await self.db.rollback()
            return False
    
    async def get_model_version(self, model_type: ModelType, for_ab_test: bool = False) -> Optional[str]:
        """Get the appropriate model version for prediction."""
        if for_ab_test:
            # Check for active A/B tests
            ab_test = await self._get_active_ab_test(model_type)
            if ab_test:
                # Simple traffic splitting (in production, use proper routing)
                import random
                if random.random() < ab_test.traffic_split:
                    return ab_test.model_b_version
                else:
                    return ab_test.model_a_version
        
        # Get active model
        result = await self.db.execute(
            select(ModelRegistryRecord.version)
            .where(ModelRegistryRecord.model_type == model_type.value)
            .where(ModelRegistryRecord.status == ModelStatus.ACTIVE.value)
            .order_by(desc(ModelRegistryRecord.deployed_at))
            .limit(1)
        )
        
        return result.scalar_one_or_none()
    
    async def _get_active_ab_test(self, model_type: ModelType) -> Optional[ABTestConfig]:
        """Get active A/B test configuration for model type."""
        # Check cache first
        if (model_type in self.active_ab_tests and 
            datetime.utcnow() - self.last_ab_test_refresh < self.ab_test_cache_ttl):
            return self.active_ab_tests[model_type]
        
        # Refresh from database
        result = await self.db.execute(
            select(ABTestRecord)
            .where(ABTestRecord.model_type == model_type.value)
            .where(ABTestRecord.status == "active")
            .where(ABTestRecord.start_date <= datetime.utcnow())
            .where(ABTestRecord.end_date >= datetime.utcnow())
            .order_by(desc(ABTestRecord.start_date))
            .limit(1)
        )
        
        ab_test_record = result.scalar_one_or_none()
        
        if ab_test_record:
            ab_test_config = ABTestConfig(
                test_id=ab_test_record.test_id,
                model_a_version=ab_test_record.model_a_version,
                model_b_version=ab_test_record.model_b_version,
                traffic_split=ab_test_record.traffic_split,
                start_date=ab_test_record.start_date,
                end_date=ab_test_record.end_date,
                success_metrics=ab_test_record.success_metrics,
                minimum_samples=ab_test_record.minimum_samples
            )
            
            self.active_ab_tests[model_type] = ab_test_config
            self.last_ab_test_refresh = datetime.utcnow()
            
            return ab_test_config
        
        # Remove from cache if no active test
        if model_type in self.active_ab_tests:
            del self.active_ab_tests[model_type]
        
        return None
    
    async def _validate_model_for_deployment(self, model_record: ModelRegistryRecord) -> Dict[str, Any]:
        """Validate a model before deployment."""
        errors = []
        
        # Check if model files exist
        for file_type, file_path in model_record.file_paths.items():
            if not os.path.exists(file_path):
                errors.append(f"Model file not found: {file_path}")
        
        # Check performance metrics
        f1_score = model_record.performance_metrics.get("f1_score", 0)
        if f1_score < 0.7:  # Minimum acceptable performance
            errors.append(f"F1 score too low: {f1_score}")
        
        # Check model checksum
        if model_record.file_paths:
            current_checksum = await self._calculate_model_checksum(model_record.file_paths)
            if current_checksum != model_record.checksum:
                errors.append("Model checksum mismatch - files may be corrupted")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _calculate_model_checksum(self, file_paths: Dict[str, str]) -> str:
        """Calculate checksum for model files."""
        hasher = hashlib.sha256()
        
        for file_type in sorted(file_paths.keys()):  # Sort for consistent hashing
            file_path = file_paths[file_type]
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
        
        return hasher.hexdigest()
    
    async def _copy_to_registry(self, model_id: str, file_paths: Dict[str, str]) -> Dict[str, str]:
        """Copy model files to registry storage."""
        registry_dir = os.path.join(self.registry_storage_path, model_id)
        os.makedirs(registry_dir, exist_ok=True)
        
        registry_paths = {}
        
        for file_type, source_path in file_paths.items():
            if os.path.exists(source_path):
                filename = os.path.basename(source_path)
                registry_path = os.path.join(registry_dir, filename)
                shutil.copy2(source_path, registry_path)
                registry_paths[file_type] = registry_path
        
        return registry_paths
    
    async def _deactivate_current_model(self, model_type: ModelType) -> None:
        """Deactivate the currently active model."""
        result = await self.db.execute(
            select(ModelRegistryRecord)
            .where(ModelRegistryRecord.model_type == model_type.value)
            .where(ModelRegistryRecord.status == ModelStatus.ACTIVE.value)
        )
        
        current_models = result.scalars().all()
        
        for model in current_models:
            model.status = ModelStatus.INACTIVE.value
            model.deprecated_at = datetime.utcnow()
        
        await self.db.commit()
    
    async def list_models(
        self,
        model_type: Optional[ModelType] = None,
        status: Optional[ModelStatus] = None,
        limit: int = 50
    ) -> List[ModelMetadata]:
        """List models in the registry."""
        query = select(ModelRegistryRecord)
        
        if model_type:
            query = query.where(ModelRegistryRecord.model_type == model_type.value)
        
        if status:
            query = query.where(ModelRegistryRecord.status == status.value)
        
        query = query.order_by(desc(ModelRegistryRecord.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        records = result.scalars().all()
        
        return [record.to_metadata() for record in records]
    
    async def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        """Get detailed information about a specific model."""
        result = await self.db.execute(
            select(ModelRegistryRecord).where(ModelRegistryRecord.model_id == model_id)
        )
        
        record = result.scalar_one_or_none()
        return record.to_metadata() if record else None
    
    async def cleanup_old_models(self, days: int = 90) -> int:
        """Clean up old inactive models."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get models to clean up
        result = await self.db.execute(
            select(ModelRegistryRecord)
            .where(ModelRegistryRecord.status.in_([ModelStatus.INACTIVE.value, ModelStatus.DEPRECATED.value]))
            .where(ModelRegistryRecord.created_at < cutoff_date)
        )
        
        models_to_cleanup = result.scalars().all()
        cleanup_count = 0
        
        for model in models_to_cleanup:
            try:
                # Check if file_paths is not empty before processing
                if model.file_paths:
                    # Remove model files
                    for file_path in model.file_paths.values():
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    
                    # Remove model directory if empty
                    model_dir = os.path.dirname(list(model.file_paths.values())[0])
                    if os.path.exists(model_dir) and not os.listdir(model_dir):
                        os.rmdir(model_dir)
                
                # Remove database record
                await self.db.delete(model)
                cleanup_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to cleanup model {model.model_id}: {e}")
        
        await self.db.commit()
        logger.info(f"Cleaned up {cleanup_count} old models")
        
        return cleanup_count
    
    async def get_registry_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        # Model counts by type and status
        result = await self.db.execute(
            select(
                ModelRegistryRecord.model_type,
                ModelRegistryRecord.status,
                func.count(ModelRegistryRecord.id)
            )
            .group_by(ModelRegistryRecord.model_type, ModelRegistryRecord.status)
        )
        
        model_counts = {}
        for model_type, status, count in result.fetchall():
            if model_type not in model_counts:
                model_counts[model_type] = {}
            model_counts[model_type][status] = count
        
        # A/B test counts
        ab_test_result = await self.db.execute(
            select(ABTestRecord.status, func.count(ABTestRecord.id))
            .group_by(ABTestRecord.status)
        )
        
        ab_test_counts = dict(ab_test_result.fetchall())
        
        # Storage usage
        total_size = 0
        if os.path.exists(self.registry_storage_path):
            for root, dirs, files in os.walk(self.registry_storage_path):
                total_size += sum(os.path.getsize(os.path.join(root, file)) for file in files)
        
        return {
            "model_counts": model_counts,
            "ab_test_counts": ab_test_counts,
            "storage_size_bytes": total_size,
            "active_ab_tests": len(self.active_ab_tests),
            "registry_path": self.registry_storage_path
        }