"""
ML Model Training Service for Advanced Intelligence Suite

This service handles automated model training, retraining triggers, data preprocessing,
and model validation for the ML Accuracy Engine. It supports multiple model types
and provides comprehensive performance monitoring.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score, mean_squared_error
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.ml_training import TrainingJob, ModelPerformanceMetric, FeedbackRecord
from app.models.impact_card import ImpactCard
from app.services.feature_extractor import FeatureExtractor, FeatureSet
from app.services.feature_store import FeatureStore
from app.config import settings

logger = logging.getLogger(__name__)

class ModelType(str, Enum):
    """Types of ML models supported by the training service."""
    IMPACT_CLASSIFIER = "impact_classifier"
    RISK_SCORER = "risk_scorer"
    CONFIDENCE_PREDICTOR = "confidence_predictor"
    RELEVANCE_CLASSIFIER = "relevance_classifier"

class TriggerType(str, Enum):
    """Types of triggers that can initiate model training."""
    SCHEDULED = "scheduled"
    PERFORMANCE_DROP = "performance_drop"
    FEEDBACK_THRESHOLD = "feedback_threshold"
    MANUAL = "manual"

@dataclass
class TrainingConfig:
    """Configuration for model training."""
    model_type: ModelType
    hyperparameters: Dict[str, Any]
    validation_split: float = 0.2
    min_training_samples: int = 100
    performance_threshold: float = 0.85
    max_training_time: int = 3600  # seconds

@dataclass
class TrainingResult:
    """Result of a model training job."""
    job_id: str
    model_type: ModelType
    success: bool
    model_version: str
    performance_metrics: Dict[str, float]
    training_time: float
    error_message: Optional[str] = None

class MLTrainingService:
    """Service for automated ML model training and management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.feature_extractor = FeatureExtractor(db)
        self.feature_store = FeatureStore(db)
        self.model_storage_path = os.path.join(settings.data_dir, "ml_models")
        self.scalers_storage_path = os.path.join(settings.data_dir, "ml_scalers")
        
        # Ensure storage directories exist
        os.makedirs(self.model_storage_path, exist_ok=True)
        os.makedirs(self.scalers_storage_path, exist_ok=True)
        
        # Training configurations for different model types
        self.training_configs = {
            ModelType.IMPACT_CLASSIFIER: TrainingConfig(
                model_type=ModelType.IMPACT_CLASSIFIER,
                hyperparameters={
                    "n_estimators": 100,
                    "max_depth": 10,
                    "min_samples_split": 5,
                    "random_state": 42
                },
                min_training_samples=200,
                performance_threshold=0.85
            ),
            ModelType.RISK_SCORER: TrainingConfig(
                model_type=ModelType.RISK_SCORER,
                hyperparameters={
                    "n_estimators": 150,
                    "learning_rate": 0.1,
                    "max_depth": 8,
                    "random_state": 42
                },
                min_training_samples=150,
                performance_threshold=0.80
            ),
            ModelType.CONFIDENCE_PREDICTOR: TrainingConfig(
                model_type=ModelType.CONFIDENCE_PREDICTOR,
                hyperparameters={
                    "C": 1.0,
                    "random_state": 42,
                    "max_iter": 1000
                },
                min_training_samples=100,
                performance_threshold=0.75
            ),
            ModelType.RELEVANCE_CLASSIFIER: TrainingConfig(
                model_type=ModelType.RELEVANCE_CLASSIFIER,
                hyperparameters={
                    "n_estimators": 100,
                    "max_depth": 10,
                    "min_samples_split": 5,
                    "random_state": 42
                },
                min_training_samples=150,
                performance_threshold=0.80
            )
        }
    
    async def check_retraining_triggers(self) -> List[Tuple[ModelType, TriggerType]]:
        """Check if any models need retraining based on various triggers."""
        triggers = []
        
        # Check performance drop triggers
        performance_triggers = await self._check_performance_triggers()
        triggers.extend(performance_triggers)
        
        # Check feedback threshold triggers
        feedback_triggers = await self._check_feedback_triggers()
        triggers.extend(feedback_triggers)
        
        # Check scheduled triggers
        scheduled_triggers = await self._check_scheduled_triggers()
        triggers.extend(scheduled_triggers)
        
        return triggers
    
    async def _check_performance_triggers(self) -> List[Tuple[ModelType, TriggerType]]:
        """Check for models with performance below threshold."""
        triggers = []
        
        for model_type in ModelType:
            try:
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
                    config = self.training_configs.get(model_type)
                    if config and latest_metric.metric_value < config.performance_threshold:
                        triggers.append((model_type, TriggerType.PERFORMANCE_DROP))
                        logger.info(f"Performance trigger for {model_type.value}: {latest_metric.metric_value} < {config.performance_threshold}")
                
            except Exception as e:
                logger.error(f"Error checking performance trigger for {model_type.value}: {e}")
        
        return triggers
    
    async def _check_feedback_triggers(self) -> List[Tuple[ModelType, TriggerType]]:
        """Check for models with sufficient new feedback for retraining."""
        triggers = []
        
        # Check for unprocessed feedback
        result = await self.db.execute(
            select(func.count(FeedbackRecord.id))
            .where(FeedbackRecord.processed == False)
        )
        
        unprocessed_count = result.scalar() or 0
        
        # Trigger retraining if we have 50+ new feedback records
        if unprocessed_count >= 50:
            # Determine which model types need retraining based on feedback types
            feedback_types_result = await self.db.execute(
                select(FeedbackRecord.feedback_type, func.count(FeedbackRecord.id))
                .where(FeedbackRecord.processed == False)
                .group_by(FeedbackRecord.feedback_type)
            )
            
            feedback_counts = dict(feedback_types_result.fetchall())
            
            # Map feedback types to model types
            feedback_to_model = {
                "accuracy": ModelType.IMPACT_CLASSIFIER,
                "relevance": ModelType.RELEVANCE_CLASSIFIER,
                "severity": ModelType.RISK_SCORER,
                "category": ModelType.IMPACT_CLASSIFIER
            }
            
            for feedback_type, count in feedback_counts.items():
                if count >= 20 and feedback_type in feedback_to_model:
                    model_type = feedback_to_model[feedback_type]
                    triggers.append((model_type, TriggerType.FEEDBACK_THRESHOLD))
                    logger.info(f"Feedback trigger for {model_type.value}: {count} new {feedback_type} feedback")
        
        return triggers
    
    async def _check_scheduled_triggers(self) -> List[Tuple[ModelType, TriggerType]]:
        """Check for models that need scheduled retraining."""
        triggers = []
        
        # Check when each model was last trained
        for model_type in ModelType:
            try:
                result = await self.db.execute(
                    select(TrainingJob)
                    .where(TrainingJob.model_type == model_type.value)
                    .where(TrainingJob.status == "completed")
                    .order_by(desc(TrainingJob.completed_at))
                    .limit(1)
                )
                
                last_training = result.scalar_one_or_none()
                
                # Schedule retraining every 7 days
                if not last_training or (datetime.utcnow() - last_training.completed_at).days >= 7:
                    triggers.append((model_type, TriggerType.SCHEDULED))
                    logger.info(f"Scheduled trigger for {model_type.value}")
                
            except Exception as e:
                logger.error(f"Error checking scheduled trigger for {model_type.value}: {e}")
        
        return triggers
    
    async def start_training_job(
        self, 
        model_type: ModelType, 
        trigger_type: TriggerType,
        config_override: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new model training job."""
        job_id = str(uuid.uuid4())
        
        try:
            # Get current model version for comparison
            current_version = await self._get_current_model_version(model_type)
            new_version = f"{model_type.value}_v{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Create training job record
            training_job = TrainingJob(
                job_id=job_id,
                model_type=model_type.value,
                trigger_type=trigger_type.value,
                status="pending",
                previous_model_version=current_version,
                new_model_version=new_version,
                training_config=config_override or {}
            )
            
            self.db.add(training_job)
            await self.db.commit()
            
            # Start training in background
            asyncio.create_task(self._execute_training_job(job_id))
            
            logger.info(f"Started training job {job_id} for {model_type.value}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to start training job: {e}")
            raise
    
    async def _execute_training_job(self, job_id: str) -> None:
        """Execute a training job asynchronously."""
        try:
            # Update job status
            await self._update_job_status(job_id, "running", started_at=datetime.utcnow())
            
            # Get job details
            result = await self.db.execute(
                select(TrainingJob).where(TrainingJob.job_id == job_id)
            )
            job = result.scalar_one()
            
            model_type = ModelType(job.model_type)
            
            # Prepare training data
            training_data = await self._prepare_training_data(model_type)
            
            if not training_data:
                raise ValueError(f"Insufficient training data for {model_type.value}")
            
            # Train model
            training_result = await self._train_model(model_type, training_data, job.new_model_version)
            
            # Update job with results
            await self._update_job_with_results(job_id, training_result)
            
            # Mark feedback as processed
            await self._mark_feedback_processed(model_type)
            
            logger.info(f"Training job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Training job {job_id} failed: {e}")
            await self._update_job_status(
                job_id, 
                "failed", 
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def _prepare_training_data(self, model_type: ModelType) -> Optional[pd.DataFrame]:
        """Prepare training data for the specified model type."""
        try:
            # Get impact cards with feedback
            result = await self.db.execute(
                select(ImpactCard, FeedbackRecord)
                .join(FeedbackRecord, ImpactCard.id == FeedbackRecord.impact_card_id)
                .where(FeedbackRecord.processed == False)
                .limit(1000)  # Limit to prevent memory issues
            )
            
            training_records = result.fetchall()
            
            if len(training_records) < self.training_configs[model_type].min_training_samples:
                logger.warning(f"Insufficient training data for {model_type.value}: {len(training_records)} samples")
                return None
            
            # Extract features for each record
            training_data = []
            
            for impact_card, feedback in training_records:
                # Extract features from impact card
                feature_set = await self.feature_extractor.extract_impact_card_features(impact_card)
                
                # Create feature vector
                feature_vector = {}
                for feature in feature_set.features:
                    if feature.feature_type.value in ["numerical", "categorical"]:
                        feature_vector[feature.name] = feature.value
                
                # Add target variable based on model type
                target = self._get_target_variable(model_type, impact_card, feedback)
                if target is not None:
                    feature_vector["target"] = target
                    training_data.append(feature_vector)
            
            if not training_data:
                return None
            
            df = pd.DataFrame(training_data)
            logger.info(f"Prepared {len(df)} training samples for {model_type.value}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to prepare training data for {model_type.value}: {e}")
            return None
    
    def _get_target_variable(
        self, 
        model_type: ModelType, 
        impact_card: ImpactCard, 
        feedback: FeedbackRecord
    ) -> Optional[float]:
        """Get the target variable for training based on model type."""
        if model_type == ModelType.IMPACT_CLASSIFIER:
            if feedback.feedback_type == "accuracy":
                return 1.0 if feedback.corrected_value > 0.8 else 0.0
            elif feedback.feedback_type == "category":
                return 1.0 if feedback.corrected_value == feedback.original_value else 0.0
        
        elif model_type == ModelType.RISK_SCORER:
            if feedback.feedback_type == "severity":
                return feedback.corrected_value if feedback.corrected_value is not None else None
        
        elif model_type == ModelType.CONFIDENCE_PREDICTOR:
            return feedback.confidence
        
        elif model_type == ModelType.RELEVANCE_CLASSIFIER:
            if feedback.feedback_type == "relevance":
                return 1.0 if feedback.corrected_value > 0.5 else 0.0
        
        return None
    
    async def _train_model(
        self, 
        model_type: ModelType, 
        training_data: pd.DataFrame,
        model_version: str
    ) -> TrainingResult:
        """Train a model with the prepared data."""
        start_time = datetime.utcnow()
        
        try:
            # Prepare features and target
            feature_columns = [col for col in training_data.columns if col != "target"]
            X = training_data[feature_columns]
            y = training_data["target"]
            
            # Handle categorical variables
            X_processed = self._preprocess_features(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_processed, y, test_size=0.2, random_state=42, stratify=y if model_type != ModelType.RISK_SCORER else None
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = self._create_model(model_type)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            performance_metrics = self._calculate_metrics(model_type, y_test, y_pred)
            
            # Save model and scaler
            model_path = os.path.join(self.model_storage_path, f"{model_version}.joblib")
            scaler_path = os.path.join(self.scalers_storage_path, f"{model_version}_scaler.joblib")
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            
            # Store performance metrics
            await self._store_performance_metrics(model_version, model_type, performance_metrics)
            
            training_time = (datetime.utcnow() - start_time).total_seconds()
            
            return TrainingResult(
                job_id="",  # Will be set by caller
                model_type=model_type,
                success=True,
                model_version=model_version,
                performance_metrics=performance_metrics,
                training_time=training_time
            )
            
        except Exception as e:
            training_time = (datetime.utcnow() - start_time).total_seconds()
            return TrainingResult(
                job_id="",
                model_type=model_type,
                success=False,
                model_version=model_version,
                performance_metrics={},
                training_time=training_time,
                error_message=str(e)
            )
    
    def _preprocess_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Preprocess features for training."""
        X_processed = X.copy()
        
        # Handle categorical variables
        categorical_columns = X_processed.select_dtypes(include=['object']).columns
        
        for col in categorical_columns:
            le = LabelEncoder()
            X_processed[col] = le.fit_transform(X_processed[col].astype(str))
        
        # Fill missing values
        X_processed = X_processed.fillna(0)
        
        return X_processed
    
    def _create_model(self, model_type: ModelType):
        """Create a model instance based on type."""
        config = self.training_configs[model_type]
        
        if model_type in [ModelType.IMPACT_CLASSIFIER, ModelType.RELEVANCE_CLASSIFIER]:
            return RandomForestClassifier(**config.hyperparameters)
        elif model_type == ModelType.RISK_SCORER:
            return GradientBoostingRegressor(**config.hyperparameters)
        elif model_type == ModelType.CONFIDENCE_PREDICTOR:
            return LogisticRegression(**config.hyperparameters)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _calculate_metrics(self, model_type: ModelType, y_true, y_pred) -> Dict[str, float]:
        """Calculate performance metrics based on model type."""
        metrics = {}
        
        if model_type in [ModelType.IMPACT_CLASSIFIER, ModelType.RELEVANCE_CLASSIFIER]:
            # Classification metrics
            metrics["accuracy"] = accuracy_score(y_true, y_pred)
            metrics["precision"] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
            metrics["recall"] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
            metrics["f1_score"] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        elif model_type in [ModelType.RISK_SCORER, ModelType.CONFIDENCE_PREDICTOR]:
            # Regression metrics
            metrics["mse"] = mean_squared_error(y_true, y_pred)
            metrics["rmse"] = np.sqrt(metrics["mse"])
            
            # R-squared
            ss_res = np.sum((y_true - y_pred) ** 2)
            ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
            metrics["r2_score"] = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            # For compatibility, use R² as f1_score equivalent
            metrics["f1_score"] = max(0, metrics["r2_score"])
        
        return metrics
    
    async def _store_performance_metrics(
        self, 
        model_version: str, 
        model_type: ModelType, 
        metrics: Dict[str, float]
    ) -> None:
        """Store performance metrics in database."""
        for metric_name, metric_value in metrics.items():
            metric_record = ModelPerformanceMetric(
                model_version=model_version,
                model_type=model_type.value,
                metric_name=metric_name,
                metric_value=metric_value,
                evaluation_type="validation"
            )
            self.db.add(metric_record)
        
        await self.db.commit()
    
    async def _get_current_model_version(self, model_type: ModelType) -> Optional[str]:
        """Get the current active model version."""
        result = await self.db.execute(
            select(TrainingJob.new_model_version)
            .where(TrainingJob.model_type == model_type.value)
            .where(TrainingJob.status == "completed")
            .order_by(desc(TrainingJob.completed_at))
            .limit(1)
        )
        
        return result.scalar_one_or_none()
    
    async def _update_job_status(
        self, 
        job_id: str, 
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update training job status."""
        result = await self.db.execute(
            select(TrainingJob).where(TrainingJob.job_id == job_id)
        )
        job = result.scalar_one()
        
        job.status = status
        if started_at:
            job.started_at = started_at
        if completed_at:
            job.completed_at = completed_at
        if error_message:
            job.error_message = error_message
        
        await self.db.commit()
    
    async def _update_job_with_results(self, job_id: str, result: TrainingResult) -> None:
        """Update training job with results."""
        job_result = await self.db.execute(
            select(TrainingJob).where(TrainingJob.job_id == job_id)
        )
        job = job_result.scalar_one()
        
        job.status = "completed" if result.success else "failed"
        job.completed_at = datetime.utcnow()
        job.performance_improvement = result.performance_metrics.get("f1_score", 0.0)
        job.new_metric_value = result.performance_metrics.get("f1_score", 0.0)
        job.error_message = result.error_message
        
        await self.db.commit()
    
    async def _mark_feedback_processed(self, model_type: ModelType) -> None:
        """Mark relevant feedback as processed after training."""
        # Map model types to feedback types
        model_to_feedback = {
            ModelType.IMPACT_CLASSIFIER: ["accuracy", "category"],
            ModelType.RISK_SCORER: ["severity"],
            ModelType.CONFIDENCE_PREDICTOR: ["confidence"],
            ModelType.RELEVANCE_CLASSIFIER: ["relevance"]
        }
        
        feedback_types = model_to_feedback.get(model_type, [])
        
        if feedback_types:
            result = await self.db.execute(
                select(FeedbackRecord)
                .where(FeedbackRecord.processed == False)
                .where(FeedbackRecord.feedback_type.in_(feedback_types))
            )
            
            feedback_records = result.scalars().all()
            
            for record in feedback_records:
                record.processed = True
                record.processed_at = datetime.utcnow()
            
            await self.db.commit()
            logger.info(f"Marked {len(feedback_records)} feedback records as processed for {model_type.value}")
    
    async def get_training_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a training job."""
        result = await self.db.execute(
            select(TrainingJob).where(TrainingJob.job_id == job_id)
        )
        
        job = result.scalar_one_or_none()
        if not job:
            return None
        
        return {
            "job_id": job.job_id,
            "model_type": job.model_type,
            "status": job.status,
            "trigger_type": job.trigger_type,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "model_version": job.new_model_version,
            "performance_improvement": job.performance_improvement,
            "error_message": job.error_message
        }
    
    async def get_model_performance_history(
        self, 
        model_type: ModelType, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get performance history for a model type."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(ModelPerformanceMetric)
            .where(ModelPerformanceMetric.model_type == model_type.value)
            .where(ModelPerformanceMetric.evaluation_timestamp >= start_date)
            .order_by(ModelPerformanceMetric.evaluation_timestamp)
        )
        
        metrics = result.scalars().all()
        
        return [
            {
                "model_version": metric.model_version,
                "metric_name": metric.metric_name,
                "metric_value": metric.metric_value,
                "evaluation_timestamp": metric.evaluation_timestamp.isoformat(),
                "dataset_size": metric.dataset_size
            }
            for metric in metrics
        ]