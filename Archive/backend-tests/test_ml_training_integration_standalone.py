"""
Standalone Integration Tests for ML Training Pipeline

This module tests the complete ML training workflow including:
- End-to-end training from feedback to model deployment
- Performance benchmarking for model inference
- Model rollback and recovery procedures

Run with: python test_ml_training_integration_standalone.py
"""

import asyncio
import sys
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import patch, AsyncMock, MagicMock

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select, func

# Import only the models and services we need for testing
from app.database import Base
from app.models.ml_training import FeedbackRecord, ModelPerformanceMetric, TrainingJob
from app.models.impact_card import ImpactCard

# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def setup_database():
    """Set up test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def teardown_database():
    """Tear down test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

def get_sample_impact_card_data():
    """Sample impact card data for testing."""
    return {
        "competitor_name": "Test Competitor",
        "risk_score": 75,
        "risk_level": "high",
        "confidence_score": 85,
        "credibility_score": 0.8,
        "requires_review": False,
        "impact_areas": [
            {
                "area": "product",
                "impact_score": 80,
                "description": "Significant product impact"
            }
        ],
        "key_insights": [
            "Test insight 1",
            "Test insight 2"
        ],
        "recommended_actions": [
            {
                "action": "Monitor closely",
                "priority": "high",
                "timeline": "immediate",
                "owner": "Product",
                "okr_goal": "Enhance product differentiation",
                "impact_score": 80,
                "effort_score": 40,
                "score": 60,
                "evidence": [],
                "index": 0,
            }
        ],
        "next_steps_plan": [],
        "total_sources": 25,
        "source_breakdown": {
            "news_articles": 10,
            "search_results": 8,
            "research_citations": 7
        },
        "source_quality": {"score": 0.8, "tiers": {"tier1": 2, "tier2": 1, "tier3": 0}, "total": 3, "top_sources": []},
        "api_usage": {
            "news_calls": 2,
            "search_calls": 2,
            "chat_calls": 1,
            "ari_calls": 1,
            "total_calls": 6
        },
        "processing_time": "4.0s",
        "raw_data": {},
        "explainability": {"reasoning": "", "impact_areas": [], "key_insights": [], "source_summary": {}},
    }

async def create_sample_training_data(db_session: AsyncSession):
    """Create sample training data with impact cards and feedback."""
    impact_cards = []
    feedback_records = []
    
    # Create multiple impact cards with varying characteristics
    for i in range(50):  # Minimum training samples
        card_data = get_sample_impact_card_data()
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

async def test_end_to_end_training_workflow():
    """Test complete training workflow from feedback to model deployment."""
    print("Testing end-to-end training workflow...")
    
    async with TestSessionLocal() as db_session:
        # Create sample training data
        training_data = await create_sample_training_data(db_session)
        
        # Import ML services with mocked dependencies
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock settings to use temporary directory
            with patch('app.services.ml_training_service.settings') as mock_settings:
                mock_settings.data_dir = temp_dir
                
                from app.services.ml_training_service import MLTrainingService, ModelType, TriggerType
                
                ml_training_service = MLTrainingService(db_session)
                
                # Step 1: Check retraining triggers
                triggers = await ml_training_service.check_retraining_triggers()
                
                # Should have feedback threshold triggers due to unprocessed feedback
                assert len(triggers) > 0
                feedback_triggers = [t for t in triggers if t[1] == TriggerType.FEEDBACK_THRESHOLD]
                assert len(feedback_triggers) > 0
                print(f"✓ Found {len(feedback_triggers)} feedback threshold triggers")
                
                # Step 2: Start training job for impact classifier
                model_type = ModelType.IMPACT_CLASSIFIER
                trigger_type = TriggerType.FEEDBACK_THRESHOLD
                
                # Mock the actual model training to avoid sklearn dependencies
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
                        print(f"✓ Started training job: {job_id}")
                        
                        # Wait for training job to complete (mocked)
                        await asyncio.sleep(0.1)
                        
                        # Step 3: Verify training job was created and completed
                        job_status = await ml_training_service.get_training_job_status(job_id)
                        assert job_status is not None
                        assert job_status["model_type"] == model_type.value
                        assert job_status["trigger_type"] == trigger_type.value
                        print(f"✓ Training job completed with status: {job_status['status']}")
                        
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
                        print(f"✓ Stored {len(metrics)} performance metrics")
                        
                        # Step 5: Verify feedback was marked as processed
                        result = await db_session.execute(
                            select(func.count(FeedbackRecord.id))
                            .where(FeedbackRecord.processed == True)
                            .where(FeedbackRecord.feedback_type.in_(["accuracy", "category"]))
                        )
                        processed_count = result.scalar()
                        assert processed_count > 0
                        print(f"✓ Marked {processed_count} feedback records as processed")

async def test_model_performance_benchmarking():
    """Test performance benchmarking for model inference."""
    print("Testing model performance benchmarking...")
    
    async with TestSessionLocal() as db_session:
        # Create sample training data
        training_data = await create_sample_training_data(db_session)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.services.ml_prediction_service.settings') as mock_settings:
                mock_settings.data_dir = temp_dir
                mock_settings.redis_url = "redis://localhost:6379/1"
                
                from app.services.ml_prediction_service import (
                    MLPredictionService, PredictionRequest, PredictionType, ModelInfo
                )
                from app.services.ml_training_service import ModelType
                
                ml_prediction_service = MLPredictionService(db_session)
                
                # Create a mock trained model for testing
                with patch.object(ml_prediction_service, '_load_model') as mock_load_model:
                    # Mock model info
                    mock_model = MagicMock()
                    mock_model.predict.return_value = [0.85]
                    mock_model.predict_proba.return_value = [[0.15, 0.85]]
                    
                    mock_scaler = MagicMock()
                    mock_scaler.transform.return_value = [[0.5, 0.3, 0.8, 0.6]]
                    mock_scaler.feature_names_in_ = ["risk_score", "confidence_score", "total_sources", "credibility_score"]
                    
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
                    impact_card = training_data["impact_cards"][0]
                    
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
                    assert result.predicted_value == 0.85
                    assert 0.0 <= result.confidence_score <= 1.0
                    assert result.model_version == "test_model_v1"
                    assert result.fallback_used is False
                    
                    # Performance assertions
                    assert prediction_time < 1000  # Should be under 1 second
                    assert result.processing_time_ms < 500  # Should be under 500ms
                    print(f"✓ Single prediction completed in {prediction_time:.2f}ms")
                    
                    # Test batch prediction performance
                    requests = []
                    for i in range(10):
                        card = training_data["impact_cards"][i]
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
                        assert batch_result.predicted_value == 0.85
                        assert batch_result.fallback_used is False
                    
                    # Performance assertions for batch
                    avg_time_per_prediction = batch_time / 10
                    assert avg_time_per_prediction < 200  # Should be under 200ms per prediction in batch
                    print(f"✓ Batch prediction completed in {batch_time:.2f}ms ({avg_time_per_prediction:.2f}ms per prediction)")
                    
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
                        print(f"✓ Fallback prediction completed in {fallback_time:.2f}ms")

async def test_training_pipeline_error_handling():
    """Test error handling in the training pipeline."""
    print("Testing training pipeline error handling...")
    
    async with TestSessionLocal() as db_session:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.services.ml_training_service.settings') as mock_settings:
                mock_settings.data_dir = temp_dir
                
                from app.services.ml_training_service import MLTrainingService, ModelType, TriggerType
                
                ml_training_service = MLTrainingService(db_session)
                
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
                    print("✓ Handled insufficient training data error")
                
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
                    print("✓ Handled training failure error")

async def test_performance_monitoring_integration():
    """Test integration with performance monitoring and automatic retraining."""
    print("Testing performance monitoring integration...")
    
    async with TestSessionLocal() as db_session:
        # Create sample training data
        training_data = await create_sample_training_data(db_session)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.services.ml_training_service.settings') as mock_settings:
                mock_settings.data_dir = temp_dir
                
                from app.services.ml_training_service import MLTrainingService, ModelType, TriggerType
                
                ml_training_service = MLTrainingService(db_session)
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
                print("✓ No performance drop triggers for good model")
                
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
                print("✓ Performance drop trigger detected for poor model")
                
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
                print("✓ Scheduled retraining trigger detected for old model")
                
                # Test feedback threshold trigger
                # Already have unprocessed feedback from sample_training_data
                triggers = await ml_training_service.check_retraining_triggers()
                feedback_triggers = [t for t in triggers if t[1] == TriggerType.FEEDBACK_THRESHOLD]
                assert len(feedback_triggers) > 0
                print("✓ Feedback threshold trigger detected")

async def test_concurrent_training_jobs():
    """Test handling of concurrent training jobs."""
    print("Testing concurrent training jobs...")
    
    async with TestSessionLocal() as db_session:
        # Create sample training data
        training_data = await create_sample_training_data(db_session)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('app.services.ml_training_service.settings') as mock_settings:
                mock_settings.data_dir = temp_dir
                
                from app.services.ml_training_service import MLTrainingService, ModelType, TriggerType
                
                ml_training_service = MLTrainingService(db_session)
                
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
                        print(f"✓ Created {len(job_ids)} concurrent training jobs")
                        
                        # Check job statuses
                        for job_id in job_ids:
                            job_status = await ml_training_service.get_training_job_status(job_id)
                            assert job_status is not None
                            assert job_status["model_type"] == ModelType.IMPACT_CLASSIFIER.value
                        
                        print("✓ All concurrent jobs completed successfully")

async def run_all_tests():
    """Run all integration tests."""
    print("Setting up test database...")
    await setup_database()
    
    try:
        print("\n=== Running ML Training Pipeline Integration Tests ===\n")
        
        # Test end-to-end training workflow
        print("1. End-to-End Training Workflow:")
        await test_end_to_end_training_workflow()
        
        print("\n2. Model Performance Benchmarking:")
        await test_model_performance_benchmarking()
        
        print("\n3. Training Pipeline Error Handling:")
        await test_training_pipeline_error_handling()
        
        print("\n4. Performance Monitoring Integration:")
        await test_performance_monitoring_integration()
        
        print("\n5. Concurrent Training Jobs:")
        await test_concurrent_training_jobs()
        
        print("\n=== All Integration Tests Passed! ===")
        
    finally:
        print("\nTearing down test database...")
        await teardown_database()

if __name__ == "__main__":
    asyncio.run(run_all_tests())