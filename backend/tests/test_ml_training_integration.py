"""
Integration tests for ML Training Pipeline

This module tests the complete ML training workflow including:
- End-to-end training from feedback to model deployment
- Performance benchmarking for model inference
- Model rollback and recovery procedures
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import patch, AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.ml_training import FeedbackRecord, ModelPerformanceMetric, TrainingJob
from app.models.ml_model_registry import ModelRegistryRecord, ABTestRecord
from app.models.impact_card import ImpactCard
from app.services.ml_training_service import MLTrainingService, ModelType, TriggerType
from app.services.ml_prediction_service import MLPredictionService, PredictionRequest, PredictionType
from app.services.ml_model_registry import MLModelRegistry, ModelStatus, DeploymentStrategy
from app.services.feature_extractor import FeatureExtractor
from app.services.feature_store import FeatureStore


class TestMLTrainingIntegration:
    """Integration tests for the complete ML training pipeline."""

    @pytest.fixture
    async def ml_training_service(self, db_session: AsyncSession):
        """Create ML training service with temporary storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock settings to use temporary directory
            with patch('app.services.ml_training_service.settings') as mock_settings:
                mock_settings.data_dir = temp_dir
                service = MLTrainingService(db_session)
                yield service

    @pytest.fixture
    async def ml_prediction_service(self, db_session: AsyncSession):
        """Create ML prediction service with temporary storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.services.ml_prediction_service.settings') as mock_settings:
                mock_settings.data_dir = temp_dir
                mock_settings.redis_url = "redis://localhost:6379/1"  # Test Redis DB
                service = MLPredictionService(db_session)
                yield service

    @pytest.fixture
    async def ml_model_registry(self, db_session: AsyncSession):
        """Create ML model registry with temporary storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.services.ml_model_registry.settings') as mock_settings:
                mock_settings.data_dir = temp_dir
                registry = MLModelRegistry(db_session)
                yield registry

    @pytest.fixture
    async def sample_training_data(self, db_session: AsyncSession, sample_impact_card_data):
        """Create sample training data with impact cards and feedback."""
        impact_cards = []
        feedback_records = []
        
        # Create multiple impact cards with varying characteristics
        for i in range(50):  # Minimum training samples
            card_data = sample_impact_card_data.copy()
            card_data["competitor_name"] = f"Test Competitor {i}"
            card_data["risk_score"] = 50 + (i % 50)  # Vary risk scores
            card_data["confidence_score"] = 70 + (i % 30)  # Vary confidence
            card_data["total_sources"] = 5 + (i % 20)  # Vary source counts
            
            impact_card = ImpactCard(**card_data)
            db_session.add(impact_card)
            impact_cards.append(impact_card)
        
        await db_session.commit()
        
        # Refresh all impact cards to get IDs
        for card in impact_cards:
            await db_session.refresh(card)
        
        # Create feedback records for training
        feedback_types = ["accuracy", "relevance", "severity", "category"]
        for i, card in enumerate(impact_cards):
            feedback_type = feedback_types[i % len(feedback_types)]
            
            # Create realistic feedback based on card characteristics
            if feedback_type == "accuracy":
                original_value = 0.7 + (i % 3) * 0.1
                corrected_value = min(1.0, original_value + 0.1)
            elif feedback_type == "severity":
                original_value = card.risk_score / 100
                corrected_value = min(1.0, original_value + 0.05)
            else:
                original_value = 0.6 + (i % 4) * 0.1
                corrected_value = min(1.0, original_value + 0.1)
            
            feedback = FeedbackRecord(
                user_id=f"test_user_{i % 5}",  # Multiple users
                impact_card_id=card.id,
                feedback_type=feedback_type,
                original_value=original_value,
                corrected_value=corrected_value,
                confidence=0.8 + (i % 2) * 0.1,
                user_expertise_level="expert" if i % 3 == 0 else "intermediate",
                processed=False
            )
            
            db_session.add(feedback)
            feedback_records.append(feedback)
        
        await db_session.commit()
        
        return {
            "impact_cards": impact_cards,
            "feedback_records": feedback_records
        }

    @pytest.mark.asyncio
    async def test_end_to_end_training_workflow(
        self, 
        db_session: AsyncSession,
        ml_training_service: MLTrainingService,
        ml_model_registry: MLModelRegistry,
        sample_training_data: Dict[str, List]
    ):
        """Test complete training workflow from feedback to model deployment."""
        
        # Step 1: Check retraining triggers
        triggers = await ml_training_service.check_retraining_triggers()
        
        # Should have feedback threshold triggers due to unprocessed feedback
        assert len(triggers) > 0
        feedback_triggers = [t for t in triggers if t[1] == TriggerType.FEEDBACK_THRESHOLD]
        assert len(feedback_triggers) > 0
        
        # Step 2: Start training job for impact classifier
        model_type = ModelType.IMPACT_CLASSIFIER
        trigger_type = TriggerType.FEEDBACK_THRESHOLD
        
        # Mock the actual model training to avoid sklearn dependencies in tests
        with patch.object(ml_training_service, '_train_model') as mock_train:
            mock_train.return_value = MagicMock(
                success=True,
                model_version="test_model_v1",
                performance_metrics={
                    "f1_score": 0.87,
                    "accuracy": 0.85,
                    "precision": 0.88,
                    "recall": 0.86
                },
                training_time=120.5,
                error_message=None
            )
            
            # Mock file operations
            with patch('os.path.exists', return_value=True), \
                 patch('joblib.dump'), \
                 patch('joblib.load'):
                
                job_id = await ml_training_service.start_training_job(
                    model_type, trigger_type
                )
                
                assert job_id is not None
                
                # Wait for training job to complete (mocked)
                await asyncio.sleep(0.1)
                
                # Step 3: Verify training job was created and completed
                job_status = await ml_training_service.get_training_job_status(job_id)
                assert job_status is not None
                assert job_status["model_type"] == model_type.value
                assert job_status["trigger_type"] == trigger_type.value
                
                # Step 4: Verify performance metrics were stored
                result = await db_session.execute(
                    select(ModelPerformanceMetric)
                    .where(ModelPerformanceMetric.model_version == "test_model_v1")
                )
                metrics = result.scalars().all()
                assert len(metrics) > 0
                
                # Check for key metrics
                metric_names = {m.metric_name for m in metrics}
                assert "f1_score" in metric_names
                assert "accuracy" in metric_names
                
                # Step 5: Verify feedback was marked as processed
                result = await db_session.execute(
                    select(func.count(FeedbackRecord.id))
                    .where(FeedbackRecord.processed == True)
                    .where(FeedbackRecord.feedback_type.in_(["accuracy", "category"]))
                )
                processed_count = result.scalar()
                assert processed_count > 0
                
                # Step 6: Register model in registry
                model_id = await ml_model_registry.register_model(
                    model_type=model_type,
                    version="test_model_v1",
                    file_paths={
                        "model": "/tmp/test_model_v1.joblib",
                        "scaler": "/tmp/test_model_v1_scaler.joblib"
                    },
                    performance_metrics={
                        "f1_score": 0.87,
                        "accuracy": 0.85
                    },
                    training_config={"test": True},
                    description="Test model for integration testing"
                )
                
                assert model_id is not None
                
                # Step 7: Deploy model
                with patch.object(ml_model_registry, '_copy_to_registry') as mock_copy, \
                     patch.object(ml_model_registry, '_calculate_model_checksum') as mock_checksum:
                    
                    mock_copy.return_value = {
                        "model": "/tmp/registry/test_model_v1.joblib",
                        "scaler": "/tmp/registry/test_model_v1_scaler.joblib"
                    }
                    mock_checksum.return_value = "test_checksum_123"
                    
                    deployment_success = await ml_model_registry.deploy_model(
                        model_id, DeploymentStrategy.IMMEDIATE
                    )
                    
                    assert deployment_success is True
                    
                    # Verify model status is active
                    result = await db_session.execute(
                        select(ModelRegistryRecord)
                        .where(ModelRegistryRecord.model_id == model_id)
                    )
                    model_record = result.scalar_one()
                    assert model_record.status == ModelStatus.ACTIVE.value
                    assert model_record.deployed_at is not None

    @pytest.mark.asyncio
    async def test_model_performance_benchmarking(
        self,
        db_session: AsyncSession,
        ml_prediction_service: MLPredictionService,
        sample_training_data: Dict[str, List]
    ):
        """Test performance benchmarking for model inference."""
        
        # Create a mock trained model for testing
        with patch.object(ml_prediction_service, '_load_model') as mock_load_model:
            # Mock model info
            mock_model = MagicMock()
            mock_model.predict.return_value = [0.85]
            mock_model.predict_proba.return_value = [[0.15, 0.85]]
            
            mock_scaler = MagicMock()
            mock_scaler.transform.return_value = [[0.5, 0.3, 0.8, 0.6]]
            mock_scaler.feature_names_in_ = ["risk_score", "confidence_score", "total_sources", "credibility_score"]
            
            from app.services.ml_prediction_service import ModelInfo
            mock_model_info = ModelInfo(
                model=mock_model,
                scaler=mock_scaler,
                version="test_model_v1",
                model_type=ModelType.IMPACT_CLASSIFIER,
                performance_metrics={"f1_score": 0.87, "accuracy": 0.85},
                loaded_at=datetime.utcnow()
            )
            
            mock_load_model.return_value = mock_model_info
            
            # Test single prediction performance
            impact_card = sample_training_data["impact_cards"][0]
            
            request = PredictionRequest(
                entity_id=str(impact_card.id),
                entity_type="impact_card",
                prediction_type=PredictionType.IMPACT_CLASSIFICATION,
                use_cache=False
            )
            
            # Benchmark single prediction
            start_time = datetime.utcnow()
            result = await ml_prediction_service.predict(request)
            end_time = datetime.utcnow()
            
            prediction_time = (end_time - start_time).total_seconds() * 1000
            
            # Verify prediction result
            assert result.success is True
            assert result.predicted_value == 0.85
            assert 0.0 <= result.confidence_score <= 1.0
            assert result.model_version == "test_model_v1"
            assert result.fallback_used is False
            
            # Performance assertions
            assert prediction_time < 1000  # Should be under 1 second
            assert result.processing_time_ms < 500  # Should be under 500ms
            
            # Test batch prediction performance
            requests = []
            for i in range(10):
                card = sample_training_data["impact_cards"][i]
                req = PredictionRequest(
                    entity_id=str(card.id),
                    entity_type="impact_card",
                    prediction_type=PredictionType.IMPACT_CLASSIFICATION,
                    use_cache=False
                )
                requests.append(req)
            
            # Benchmark batch predictions
            batch_start_time = datetime.utcnow()
            batch_results = await ml_prediction_service.predict_batch(requests)
            batch_end_time = datetime.utcnow()
            
            batch_time = (batch_end_time - batch_start_time).total_seconds() * 1000
            
            # Verify batch results
            assert len(batch_results) == 10
            for batch_result in batch_results:
                assert batch_result.success is True
                assert batch_result.predicted_value == 0.85
                assert batch_result.fallback_used is False
            
            # Performance assertions for batch
            avg_time_per_prediction = batch_time / 10
            assert avg_time_per_prediction < 200  # Should be under 200ms per prediction in batch
            
            # Test fallback performance
            with patch.object(ml_prediction_service, '_load_model', return_value=None):
                fallback_start_time = datetime.utcnow()
                fallback_result = await ml_prediction_service.predict(request)
                fallback_end_time = datetime.utcnow()
                
                fallback_time = (fallback_end_time - fallback_start_time).total_seconds() * 1000
                
                # Verify fallback result
                assert fallback_result.fallback_used is True
                assert fallback_result.model_version == "fallback"
                assert 0.0 <= fallback_result.confidence_score <= 1.0
                
                # Fallback should be fast
                assert fallback_time < 100  # Should be under 100ms

    @pytest.mark.asyncio
    async def test_model_rollback_and_recovery(
        self,
        db_session: AsyncSession,
        ml_model_registry: MLModelRegistry,
        ml_training_service: MLTrainingService
    ):
        """Test model rollback and recovery procedures."""
        
        model_type = ModelType.IMPACT_CLASSIFIER
        
        # Step 1: Create and deploy initial model (v1)
        with patch.object(ml_model_registry, '_copy_to_registry') as mock_copy, \
             patch.object(ml_model_registry, '_calculate_model_checksum') as mock_checksum, \
             patch('os.path.exists', return_value=True), \
             patch('shutil.copy2'):
            
            mock_copy.return_value = {
                "model": "/tmp/registry/model_v1.joblib",
                "scaler": "/tmp/registry/model_v1_scaler.joblib"
            }
            mock_checksum.return_value = "checksum_v1"
            
            # Register and deploy v1
            model_v1_id = await ml_model_registry.register_model(
                model_type=model_type,
                version="model_v1",
                file_paths={
                    "model": "/tmp/model_v1.joblib",
                    "scaler": "/tmp/model_v1_scaler.joblib"
                },
                performance_metrics={"f1_score": 0.85, "accuracy": 0.83},
                training_config={"version": 1},
                description="Initial model version"
            )
            
            deploy_success = await ml_model_registry.deploy_model(
                model_v1_id, DeploymentStrategy.IMMEDIATE
            )
            assert deploy_success is True
            
            # Step 2: Create and deploy newer model (v2) with better performance
            mock_copy.return_value = {
                "model": "/tmp/registry/model_v2.joblib",
                "scaler": "/tmp/registry/model_v2_scaler.joblib"
            }
            mock_checksum.return_value = "checksum_v2"
            
            model_v2_id = await ml_model_registry.register_model(
                model_type=model_type,
                version="model_v2",
                file_paths={
                    "model": "/tmp/model_v2.joblib",
                    "scaler": "/tmp/model_v2_scaler.joblib"
                },
                performance_metrics={"f1_score": 0.89, "accuracy": 0.87},
                training_config={"version": 2},
                description="Improved model version"
            )
            
            deploy_success = await ml_model_registry.deploy_model(
                model_v2_id, DeploymentStrategy.IMMEDIATE
            )
            assert deploy_success is True
            
            # Verify v2 is active
            active_version = await ml_model_registry.get_model_version(model_type)
            assert active_version == "model_v2"
            
            # Step 3: Simulate model failure requiring rollback
            # Create a failing model (v3)
            mock_copy.return_value = {
                "model": "/tmp/registry/model_v3.joblib",
                "scaler": "/tmp/registry/model_v3_scaler.joblib"
            }
            mock_checksum.return_value = "checksum_v3"
            
            model_v3_id = await ml_model_registry.register_model(
                model_type=model_type,
                version="model_v3",
                file_paths={
                    "model": "/tmp/model_v3.joblib",
                    "scaler": "/tmp/model_v3_scaler.joblib"
                },
                performance_metrics={"f1_score": 0.65, "accuracy": 0.63},  # Poor performance
                training_config={"version": 3},
                description="Failing model version"
            )
            
            deploy_success = await ml_model_registry.deploy_model(
                model_v3_id, DeploymentStrategy.IMMEDIATE
            )
            assert deploy_success is True
            
            # Step 4: Detect performance degradation and trigger rollback
            # Simulate performance monitoring detecting the issue
            current_performance = 0.65  # Poor F1 score
            threshold = 0.80
            
            if current_performance < threshold:
                # Perform rollback to previous version (v2)
                rollback_success = await ml_model_registry.rollback_model(
                    model_type=model_type,
                    target_version="model_v2",
                    reason="Performance degradation detected"
                )
                
                assert rollback_success is True
                
                # Verify rollback was successful
                active_version = await ml_model_registry.get_model_version(model_type)
                assert active_version == "model_v2"
                
                # Verify model statuses
                result = await db_session.execute(
                    select(ModelRegistryRecord)
                    .where(ModelRegistryRecord.model_type == model_type.value)
                    .where(ModelRegistryRecord.version == "model_v2")
                )
                v2_record = result.scalar_one()
                assert v2_record.status == ModelStatus.ACTIVE.value
                
                result = await db_session.execute(
                    select(ModelRegistryRecord)
                    .where(ModelRegistryRecord.model_type == model_type.value)
                    .where(ModelRegistryRecord.version == "model_v3")
                )
                v3_record = result.scalar_one()
                assert v3_record.status == ModelStatus.INACTIVE.value
                assert v3_record.deprecated_at is not None
            
            # Step 5: Test automatic rollback to last known good version
            rollback_success = await ml_model_registry.rollback_model(
                model_type=model_type,
                reason="Automatic rollback test"
            )
            
            assert rollback_success is True
            
            # Should rollback to v1 (previous to current active v2)
            active_version = await ml_model_registry.get_model_version(model_type)
            assert active_version == "model_v1"
            
            # Step 6: Test recovery by redeploying v2
            deploy_success = await ml_model_registry.deploy_model(
                model_v2_id, DeploymentStrategy.IMMEDIATE
            )
            assert deploy_success is True
            
            active_version = await ml_model_registry.get_model_version(model_type)
            assert active_version == "model_v2"

    @pytest.mark.asyncio
    async def test_training_pipeline_error_handling(
        self,
        db_session: AsyncSession,
        ml_training_service: MLTrainingService
    ):
        """Test error handling in the training pipeline."""
        
        # Test insufficient training data
        model_type = ModelType.IMPACT_CLASSIFIER
        trigger_type = TriggerType.MANUAL
        
        # Mock insufficient training data
        with patch.object(ml_training_service, '_prepare_training_data', return_value=None):
            job_id = await ml_training_service.start_training_job(model_type, trigger_type)
            
            # Wait for job to fail
            await asyncio.sleep(0.1)
            
            job_status = await ml_training_service.get_training_job_status(job_id)
            assert job_status["status"] == "failed"
            assert "Insufficient training data" in job_status["error_message"]
        
        # Test training failure
        with patch.object(ml_training_service, '_prepare_training_data') as mock_prepare, \
             patch.object(ml_training_service, '_train_model') as mock_train:
            
            # Mock successful data preparation
            mock_prepare.return_value = MagicMock()
            
            # Mock training failure
            mock_train.side_effect = Exception("Training failed due to memory error")
            
            job_id = await ml_training_service.start_training_job(model_type, trigger_type)
            
            # Wait for job to fail
            await asyncio.sleep(0.1)
            
            job_status = await ml_training_service.get_training_job_status(job_id)
            assert job_status["status"] == "failed"
            assert "Training failed due to memory error" in job_status["error_message"]

    @pytest.mark.asyncio
    async def test_concurrent_training_jobs(
        self,
        db_session: AsyncSession,
        ml_training_service: MLTrainingService,
        sample_training_data: Dict[str, List]
    ):
        """Test handling of concurrent training jobs."""
        
        # Mock successful training
        with patch.object(ml_training_service, '_train_model') as mock_train:
            mock_train.return_value = MagicMock(
                success=True,
                model_version="concurrent_test_model",
                performance_metrics={"f1_score": 0.85},
                training_time=60.0,
                error_message=None
            )
            
            with patch('os.path.exists', return_value=True), \
                 patch('joblib.dump'), \
                 patch('joblib.load'):
                
                # Start multiple training jobs concurrently
                job_ids = []
                for i in range(3):
                    job_id = await ml_training_service.start_training_job(
                        ModelType.IMPACT_CLASSIFIER,
                        TriggerType.MANUAL
                    )
                    job_ids.append(job_id)
                
                # Wait for all jobs to complete
                await asyncio.sleep(0.2)
                
                # Verify all jobs were created
                assert len(job_ids) == 3
                assert len(set(job_ids)) == 3  # All unique
                
                # Check job statuses
                for job_id in job_ids:
                    job_status = await ml_training_service.get_training_job_status(job_id)
                    assert job_status is not None
                    assert job_status["model_type"] == ModelType.IMPACT_CLASSIFIER.value

    @pytest.mark.asyncio
    async def test_ab_testing_integration(
        self,
        db_session: AsyncSession,
        ml_model_registry: MLModelRegistry
    ):
        """Test A/B testing integration with model deployment."""
        
        model_type = ModelType.IMPACT_CLASSIFIER
        
        with patch.object(ml_model_registry, '_copy_to_registry') as mock_copy, \
             patch.object(ml_model_registry, '_calculate_model_checksum') as mock_checksum, \
             patch('os.path.exists', return_value=True):
            
            # Register two models for A/B testing
            mock_copy.return_value = {"model": "/tmp/model_a.joblib", "scaler": "/tmp/scaler_a.joblib"}
            mock_checksum.return_value = "checksum_a"
            
            model_a_id = await ml_model_registry.register_model(
                model_type=model_type,
                version="model_a",
                file_paths={"model": "/tmp/model_a.joblib", "scaler": "/tmp/scaler_a.joblib"},
                performance_metrics={"f1_score": 0.85},
                training_config={},
                description="Model A for A/B testing"
            )
            
            mock_copy.return_value = {"model": "/tmp/model_b.joblib", "scaler": "/tmp/scaler_b.joblib"}
            mock_checksum.return_value = "checksum_b"
            
            model_b_id = await ml_model_registry.register_model(
                model_type=model_type,
                version="model_b",
                file_paths={"model": "/tmp/model_b.joblib", "scaler": "/tmp/scaler_b.joblib"},
                performance_metrics={"f1_score": 0.87},
                training_config={},
                description="Model B for A/B testing"
            )
            
            # Create A/B test configuration
            from app.services.ml_model_registry import ABTestConfig
            ab_test_config = ABTestConfig(
                test_id="test_ab_001",
                model_a_version="model_a",
                model_b_version="model_b",
                traffic_split=0.5,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=7),
                success_metrics=["f1_score", "accuracy"],
                minimum_samples=100
            )
            
            # Deploy model B with A/B testing
            deploy_success = await ml_model_registry.deploy_model(
                model_b_id,
                DeploymentStrategy.AB_TEST,
                ab_test_config
            )
            
            assert deploy_success is True
            
            # Verify A/B test record was created
            result = await db_session.execute(
                select(ABTestRecord)
                .where(ABTestRecord.test_id == "test_ab_001")
            )
            ab_test_record = result.scalar_one()
            
            assert ab_test_record.model_a_version == "model_a"
            assert ab_test_record.model_b_version == "model_b"
            assert ab_test_record.traffic_split == 0.5
            assert ab_test_record.status == "active"
            
            # Test model version selection for A/B test
            # This should return either model_a or model_b based on traffic split
            version = await ml_model_registry.get_model_version(model_type, for_ab_test=True)
            assert version in ["model_a", "model_b"]

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(
        self,
        db_session: AsyncSession,
        ml_training_service: MLTrainingService,
        sample_training_data: Dict[str, List]
    ):
        """Test integration with performance monitoring and automatic retraining."""
        
        model_type = ModelType.IMPACT_CLASSIFIER
        
        # Create initial performance metrics (good performance)
        good_metric = ModelPerformanceMetric(
            model_version="good_model_v1",
            model_type=model_type.value,
            metric_name="f1_score",
            metric_value=0.90,  # Above threshold
            dataset_size=100
        )
        db_session.add(good_metric)
        await db_session.commit()
        
        # Check triggers - should not trigger performance drop
        triggers = await ml_training_service.check_retraining_triggers()
        performance_triggers = [t for t in triggers if t[1] == TriggerType.PERFORMANCE_DROP]
        assert len(performance_triggers) == 0
        
        # Create poor performance metrics
        poor_metric = ModelPerformanceMetric(
            model_version="poor_model_v1",
            model_type=model_type.value,
            metric_name="f1_score",
            metric_value=0.70,  # Below threshold (0.85)
            dataset_size=100
        )
        db_session.add(poor_metric)
        await db_session.commit()
        
        # Check triggers - should trigger performance drop
        triggers = await ml_training_service.check_retraining_triggers()
        performance_triggers = [t for t in triggers if t[1] == TriggerType.PERFORMANCE_DROP]
        assert len(performance_triggers) > 0
        
        # Verify the correct model type is triggered
        triggered_model_types = [t[0] for t in performance_triggers]
        assert model_type in triggered_model_types
        
        # Test scheduled retraining trigger
        # Create old training job
        old_job = TrainingJob(
            job_id="old_job_123",
            model_type=model_type.value,
            trigger_type="manual",
            status="completed",
            completed_at=datetime.utcnow() - timedelta(days=8)  # 8 days ago
        )
        db_session.add(old_job)
        await db_session.commit()
        
        # Check triggers - should trigger scheduled retraining
        triggers = await ml_training_service.check_retraining_triggers()
        scheduled_triggers = [t for t in triggers if t[1] == TriggerType.SCHEDULED]
        assert len(scheduled_triggers) > 0
        
        # Test feedback threshold trigger
        # Already have unprocessed feedback from sample_training_data
        triggers = await ml_training_service.check_retraining_triggers()
        feedback_triggers = [t for t in triggers if t[1] == TriggerType.FEEDBACK_THRESHOLD]
        assert len(feedback_triggers) > 0

    @pytest.mark.asyncio
    async def test_model_registry_cleanup(
        self,
        db_session: AsyncSession,
        ml_model_registry: MLModelRegistry
    ):
        """Test model registry cleanup functionality."""
        
        with patch.object(ml_model_registry, '_copy_to_registry') as mock_copy, \
             patch.object(ml_model_registry, '_calculate_model_checksum') as mock_checksum, \
             patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove, \
             patch('os.rmdir') as mock_rmdir, \
             patch('os.listdir', return_value=[]):
            
            mock_copy.return_value = {"model": "/tmp/old_model.joblib"}
            mock_checksum.return_value = "old_checksum"
            
            # Create old inactive model
            old_model_id = await ml_model_registry.register_model(
                model_type=ModelType.IMPACT_CLASSIFIER,
                version="old_model",
                file_paths={"model": "/tmp/old_model.joblib"},
                performance_metrics={"f1_score": 0.80},
                training_config={},
                description="Old model for cleanup testing"
            )
            
            # Manually set creation date to be old
            result = await db_session.execute(
                select(ModelRegistryRecord)
                .where(ModelRegistryRecord.model_id == old_model_id)
            )
            old_record = result.scalar_one()
            old_record.created_at = datetime.utcnow() - timedelta(days=100)
            old_record.status = ModelStatus.INACTIVE.value
            await db_session.commit()
            
            # Run cleanup
            cleanup_count = await ml_model_registry.cleanup_old_models(days=90)
            
            assert cleanup_count == 1
            
            # Verify model was removed from database
            result = await db_session.execute(
                select(ModelRegistryRecord)
                .where(ModelRegistryRecord.model_id == old_model_id)
            )
            assert result.scalar_one_or_none() is None
            
            # Verify file removal was attempted
            mock_remove.assert_called()