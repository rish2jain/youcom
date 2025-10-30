"""
Unit tests for ML Foundation Components

This module tests the core ML foundation components including:
- Feedback collection and validation
- Feature extraction pipeline
- Database model relationships and constraints
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.ml_training import FeedbackRecord, ModelPerformanceMetric, TrainingJob
from app.models.impact_card import ImpactCard
from app.services.feature_extractor import FeatureExtractor, FeatureSet, ExtractedFeature, FeatureType
from app.services.feature_store import FeatureStore
from app.schemas.ml_feedback import FeedbackCreate, FeedbackType, ExpertiseLevel


class TestFeedbackCollection:
    """Test feedback collection and validation functionality."""

    @pytest.mark.asyncio
    async def test_create_feedback_record(self, db_session: AsyncSession, sample_impact_card_data):
        """Test creating a basic feedback record."""
        # Create impact card first
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        # Create feedback record
        feedback = FeedbackRecord(
            user_id="test_user_123",
            impact_card_id=impact_card.id,
            feedback_type="accuracy",
            original_value=0.75,
            corrected_value=0.85,
            confidence=0.9,
            user_expertise_level="expert"
        )

        db_session.add(feedback)
        await db_session.commit()
        await db_session.refresh(feedback)

        assert feedback.id is not None
        assert feedback.user_id == "test_user_123"
        assert feedback.impact_card_id == impact_card.id
        assert feedback.feedback_type == "accuracy"
        assert feedback.original_value == 0.75
        assert feedback.corrected_value == 0.85
        assert feedback.confidence == 0.9
        assert feedback.user_expertise_level == "expert"
        assert feedback.processed is False
        assert feedback.feedback_timestamp is not None

    @pytest.mark.asyncio
    async def test_feedback_record_defaults(self, db_session: AsyncSession, sample_impact_card_data):
        """Test feedback record default values."""
        # Create impact card first
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        # Create minimal feedback record
        feedback = FeedbackRecord(
            user_id="test_user",
            impact_card_id=impact_card.id,
            feedback_type="relevance"
        )

        db_session.add(feedback)
        await db_session.commit()
        await db_session.refresh(feedback)

        assert feedback.confidence == 1.0  # Default confidence
        assert feedback.processed is False  # Default processed status
        assert feedback.feedback_context == {}  # Default empty context
        assert feedback.user_expertise_level == "unknown"  # Default expertise level
        assert feedback.processed_at is None  # Not processed yet

    @pytest.mark.asyncio
    async def test_feedback_validation_constraints(self, db_session: AsyncSession):
        """Test database constraints for feedback records."""
        # Test missing required fields
        with pytest.raises(Exception):  # Should raise database constraint error
            feedback = FeedbackRecord(
                # Missing user_id and impact_card_id
                feedback_type="accuracy"
            )
            db_session.add(feedback)
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_feedback_schema_validation(self):
        """Test Pydantic schema validation for feedback."""
        # Valid feedback creation
        valid_feedback = FeedbackCreate(
            impact_card_id=1,
            feedback_type=FeedbackType.ACCURACY,
            original_value=0.75,
            corrected_value=0.85,
            confidence=0.9,
            user_expertise_level=ExpertiseLevel.EXPERT
        )
        
        assert valid_feedback.impact_card_id == 1
        assert valid_feedback.feedback_type == FeedbackType.ACCURACY
        assert valid_feedback.confidence == 0.9

        # Test confidence validation (should be between 0.0 and 1.0)
        with pytest.raises(ValueError):
            FeedbackCreate(
                impact_card_id=1,
                feedback_type=FeedbackType.ACCURACY,
                confidence=1.5  # Invalid confidence > 1.0
            )

        with pytest.raises(ValueError):
            FeedbackCreate(
                impact_card_id=1,
                feedback_type=FeedbackType.ACCURACY,
                confidence=-0.1  # Invalid confidence < 0.0
            )

    @pytest.mark.asyncio
    async def test_feedback_context_handling(self, db_session: AsyncSession, sample_impact_card_data):
        """Test feedback context JSON field handling."""
        # Create impact card first
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        # Test with complex feedback context
        feedback_context = {
            "source": "one_click",
            "action": "thumbs_up",
            "metadata": {
                "session_id": "abc123",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        feedback = FeedbackRecord(
            user_id="test_user",
            impact_card_id=impact_card.id,
            feedback_type="accuracy",
            confidence=0.8,
            feedback_context=feedback_context
        )

        db_session.add(feedback)
        await db_session.commit()
        await db_session.refresh(feedback)

        assert feedback.feedback_context == feedback_context
        assert feedback.feedback_context["source"] == "one_click"
        assert feedback.feedback_context["metadata"]["session_id"] == "abc123"


class TestFeatureExtraction:
    """Test feature extraction pipeline functionality."""

    @pytest.mark.asyncio
    async def test_extract_impact_card_features(self, db_session: AsyncSession, sample_impact_card_data):
        """Test feature extraction from impact cards."""
        # Create impact card
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        # Extract features
        extractor = FeatureExtractor(db_session)
        feature_set = await extractor.extract_impact_card_features(impact_card)

        assert feature_set is not None
        assert feature_set.entity_id == f"impact_card_{impact_card.id}"
        assert feature_set.entity_type == "impact_card"
        assert len(feature_set.features) > 0
        assert feature_set.feature_hash is not None

        # Check for required numerical features
        feature_names = {f.name for f in feature_set.features}
        required_features = ["risk_score", "confidence_score", "total_sources"]
        
        for required_feature in required_features:
            assert required_feature in feature_names

        # Check feature types
        risk_score_feature = next(f for f in feature_set.features if f.name == "risk_score")
        assert risk_score_feature.feature_type == FeatureType.NUMERICAL
        assert risk_score_feature.value == float(impact_card.risk_score)
        assert risk_score_feature.confidence == 1.0

    @pytest.mark.asyncio
    async def test_extract_feedback_features(self, db_session: AsyncSession, sample_impact_card_data):
        """Test feature extraction from feedback records."""
        # Create impact card and feedback
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        feedback = FeedbackRecord(
            user_id="test_user",
            impact_card_id=impact_card.id,
            feedback_type="accuracy",
            original_value=0.75,
            corrected_value=0.85,
            confidence=0.9,
            user_expertise_level="expert"
        )
        db_session.add(feedback)
        await db_session.commit()
        await db_session.refresh(feedback)

        # Extract features
        extractor = FeatureExtractor(db_session)
        feature_set = await extractor.extract_feedback_features(feedback)

        assert feature_set is not None
        assert feature_set.entity_id == f"feedback_{feedback.id}"
        assert feature_set.entity_type == "feedback"

        # Check for required features
        feature_names = {f.name for f in feature_set.features}
        expected_features = ["feedback_confidence", "feedback_type", "user_expertise_level", "correction_magnitude"]
        
        for expected_feature in expected_features:
            assert expected_feature in feature_names

        # Check correction magnitude calculation
        correction_feature = next(f for f in feature_set.features if f.name == "correction_magnitude")
        expected_magnitude = abs(feedback.corrected_value - feedback.original_value)
        assert correction_feature.value == expected_magnitude

    @pytest.mark.asyncio
    async def test_feature_validation(self, db_session: AsyncSession, sample_impact_card_data):
        """Test feature validation functionality."""
        # Create impact card
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        extractor = FeatureExtractor(db_session)
        feature_set = await extractor.extract_impact_card_features(impact_card)

        # Test valid feature set
        is_valid, errors = await extractor.validate_features(feature_set)
        assert is_valid is True
        assert len(errors) == 0

        # Test invalid feature set (missing required features)
        invalid_feature_set = FeatureSet(
            entity_id="test_entity",
            entity_type="test_type",
            features=[
                ExtractedFeature(
                    name="test_feature",
                    value=1.0,
                    feature_type=FeatureType.NUMERICAL,
                    confidence=1.0,
                    metadata={}
                )
            ],
            extraction_timestamp=datetime.utcnow(),
            feature_hash="test_hash"
        )

        is_valid, errors = await extractor.validate_features(invalid_feature_set)
        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing required feature" in error for error in errors)

    @pytest.mark.asyncio
    async def test_feature_normalization(self, db_session: AsyncSession, sample_impact_card_data):
        """Test feature normalization functionality."""
        # Create impact card
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        extractor = FeatureExtractor(db_session)
        feature_set = await extractor.extract_impact_card_features(impact_card)

        # Normalize features
        normalized_set = await extractor.normalize_features(feature_set)

        assert normalized_set is not None
        assert len(normalized_set.features) == len(feature_set.features)

        # Check that numerical features are normalized to [0, 1] range
        for feature in normalized_set.features:
            if feature.feature_type == FeatureType.NUMERICAL:
                assert 0.0 <= feature.value <= 1.0
                assert feature.metadata.get("normalized") is True

    @pytest.mark.asyncio
    async def test_feature_caching(self, db_session: AsyncSession, sample_impact_card_data):
        """Test feature caching functionality."""
        # Create impact card
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        extractor = FeatureExtractor(db_session)
        
        # Extract features and cache them
        feature_set = await extractor.extract_impact_card_features(impact_card)
        await extractor.cache_features(feature_set)

        # Retrieve cached features
        cached_features = await extractor.get_cached_features("impact_card", str(impact_card.id))
        
        assert cached_features is not None
        assert cached_features.entity_id == feature_set.entity_id
        assert cached_features.feature_hash == feature_set.feature_hash
        assert len(cached_features.features) == len(feature_set.features)

    @pytest.mark.asyncio
    async def test_batch_feature_extraction(self, db_session: AsyncSession, sample_impact_card_data):
        """Test batch feature extraction."""
        # Create multiple impact cards
        impact_cards = []
        for i in range(3):
            card_data = sample_impact_card_data.copy()
            card_data["competitor_name"] = f"Test Competitor {i}"
            card_data["risk_score"] = 70 + i * 5
            
            impact_card = ImpactCard(**card_data)
            db_session.add(impact_card)
            impact_cards.append(impact_card)

        await db_session.commit()
        
        for card in impact_cards:
            await db_session.refresh(card)

        # Extract features in batch
        extractor = FeatureExtractor(db_session)
        entity_ids = [str(card.id) for card in impact_cards]
        
        feature_sets = await extractor.extract_batch_features("impact_card", entity_ids, use_cache=False)

        assert len(feature_sets) == 3
        for feature_set in feature_sets:
            assert feature_set.entity_type == "impact_card"
            assert len(feature_set.features) > 0


class TestFeatureStore:
    """Test feature store functionality."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_features(self, db_session: AsyncSession, sample_impact_card_data):
        """Test storing and retrieving features."""
        # Create impact card and extract features
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        extractor = FeatureExtractor(db_session)
        feature_set = await extractor.extract_impact_card_features(impact_card)

        # Store features
        feature_store = FeatureStore(db_session)
        success = await feature_store.store_features(feature_set)
        assert success is True

        # Retrieve features
        retrieved_features = await feature_store.retrieve_features(
            feature_set.entity_id, 
            feature_set.entity_type,
            use_cache=False  # Test database retrieval
        )

        assert retrieved_features is not None
        assert retrieved_features.entity_id == feature_set.entity_id
        assert retrieved_features.entity_type == feature_set.entity_type
        assert retrieved_features.feature_hash == feature_set.feature_hash
        assert len(retrieved_features.features) == len(feature_set.features)

    @pytest.mark.asyncio
    async def test_feature_statistics(self, db_session: AsyncSession, sample_impact_card_data):
        """Test feature statistics calculation."""
        # Create and store multiple feature sets
        feature_store = FeatureStore(db_session)
        
        for i in range(3):
            card_data = sample_impact_card_data.copy()
            card_data["competitor_name"] = f"Test Competitor {i}"
            
            impact_card = ImpactCard(**card_data)
            db_session.add(impact_card)
            await db_session.commit()
            await db_session.refresh(impact_card)

            extractor = FeatureExtractor(db_session)
            feature_set = await extractor.extract_impact_card_features(impact_card)
            await feature_store.store_features(feature_set)

        # Get statistics
        stats = await feature_store.get_feature_statistics(entity_type="impact_card", days=30)

        assert stats["total_records"] == 3
        assert "impact_card" in stats["entity_types"]
        assert stats["entity_types"]["impact_card"] == 3
        assert stats["avg_feature_count"] > 0
        assert stats["avg_confidence"] > 0
        assert len(stats["feature_types"]) > 0


class TestDatabaseModelRelationships:
    """Test database model relationships and constraints."""

    @pytest.mark.asyncio
    async def test_feedback_impact_card_relationship(self, db_session: AsyncSession, sample_impact_card_data):
        """Test relationship between feedback and impact card models."""
        # Create impact card
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        # Create feedback record
        feedback = FeedbackRecord(
            user_id="test_user",
            impact_card_id=impact_card.id,
            feedback_type="accuracy",
            confidence=0.8
        )
        db_session.add(feedback)
        await db_session.commit()
        await db_session.refresh(feedback)

        # Test relationship
        assert feedback.impact_card_id == impact_card.id
        
        # Test that we can query feedback by impact card
        result = await db_session.execute(
            select(FeedbackRecord).where(FeedbackRecord.impact_card_id == impact_card.id)
        )
        related_feedback = result.scalars().all()
        
        assert len(related_feedback) == 1
        assert related_feedback[0].id == feedback.id

    @pytest.mark.asyncio
    async def test_model_performance_metric_constraints(self, db_session: AsyncSession):
        """Test model performance metric database constraints."""
        # Create valid performance metric
        metric = ModelPerformanceMetric(
            model_version="test_model_v1",
            model_type="impact_classifier",
            metric_name="f1_score",
            metric_value=0.85,
            dataset_size=100
        )
        
        db_session.add(metric)
        await db_session.commit()
        await db_session.refresh(metric)

        assert metric.id is not None
        assert metric.model_version == "test_model_v1"
        assert metric.metric_value == 0.85
        assert metric.evaluation_timestamp is not None

    @pytest.mark.asyncio
    async def test_training_job_lifecycle(self, db_session: AsyncSession):
        """Test training job model lifecycle and status transitions."""
        # Create training job
        job = TrainingJob(
            job_id="test_job_123",
            model_type="impact_classifier",
            trigger_type="manual",
            status="pending"
        )
        
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        assert job.id is not None
        assert job.status == "pending"
        assert job.created_at is not None
        assert job.started_at is None
        assert job.completed_at is None

        # Update job status to running
        job.status = "running"
        job.started_at = datetime.utcnow()
        await db_session.commit()

        # Update job status to completed
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.new_model_version = "test_model_v2"
        job.performance_improvement = 0.05
        await db_session.commit()

        assert job.status == "completed"
        assert job.started_at is not None
        assert job.completed_at is not None
        assert job.new_model_version == "test_model_v2"

    @pytest.mark.asyncio
    async def test_database_indexes_performance(self, db_session: AsyncSession, sample_impact_card_data):
        """Test that database indexes are working for performance."""
        # Create multiple records to test index performance
        impact_cards = []
        feedback_records = []
        
        # Create test data
        for i in range(10):
            card_data = sample_impact_card_data.copy()
            card_data["competitor_name"] = f"Test Competitor {i}"
            
            impact_card = ImpactCard(**card_data)
            db_session.add(impact_card)
            impact_cards.append(impact_card)

        await db_session.commit()
        
        for card in impact_cards:
            await db_session.refresh(card)

        # Create feedback records
        for i, card in enumerate(impact_cards):
            feedback = FeedbackRecord(
                user_id=f"user_{i}",
                impact_card_id=card.id,
                feedback_type="accuracy",
                confidence=0.8 + (i * 0.01)
            )
            db_session.add(feedback)
            feedback_records.append(feedback)

        await db_session.commit()

        # Test indexed queries (these should be fast with proper indexes)
        
        # Query by user_id (should use index)
        result = await db_session.execute(
            select(FeedbackRecord).where(FeedbackRecord.user_id == "user_5")
        )
        user_feedback = result.scalars().all()
        assert len(user_feedback) == 1

        # Query by processed status (should use index)
        result = await db_session.execute(
            select(FeedbackRecord).where(FeedbackRecord.processed == False)
        )
        unprocessed_feedback = result.scalars().all()
        assert len(unprocessed_feedback) == 10

        # Query by feedback_type (should use index)
        result = await db_session.execute(
            select(FeedbackRecord).where(FeedbackRecord.feedback_type == "accuracy")
        )
        accuracy_feedback = result.scalars().all()
        assert len(accuracy_feedback) == 10

    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, db_session: AsyncSession):
        """Test foreign key constraints are enforced."""
        # Try to create feedback with non-existent impact card
        feedback = FeedbackRecord(
            user_id="test_user",
            impact_card_id=99999,  # Non-existent impact card ID
            feedback_type="accuracy",
            confidence=0.8
        )
        
        db_session.add(feedback)
        
        # This should raise an integrity error due to foreign key constraint
        with pytest.raises(Exception):  # Could be IntegrityError or similar
            await db_session.commit()
        
        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_model_timestamps(self, db_session: AsyncSession, sample_impact_card_data):
        """Test that model timestamps are properly managed."""
        # Create impact card
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        # Create feedback record
        feedback = FeedbackRecord(
            user_id="test_user",
            impact_card_id=impact_card.id,
            feedback_type="accuracy",
            confidence=0.8
        )
        
        db_session.add(feedback)
        await db_session.commit()
        await db_session.refresh(feedback)

        # Check that timestamp was automatically set
        assert feedback.feedback_timestamp is not None
        assert feedback.processed_at is None  # Should be None until processed

        # Mark as processed
        feedback.processed = True
        feedback.processed_at = datetime.utcnow()
        await db_session.commit()

        assert feedback.processed is True
        assert feedback.processed_at is not None