"""
Standalone unit tests for ML Foundation Components

This module tests the core ML foundation components without importing the full app.
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select

# Import only the models and services we need for testing
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base
from app.models.ml_training import FeedbackRecord, ModelPerformanceMetric, TrainingJob
from app.models.impact_card import ImpactCard
from app.services.feature_extractor import (
    FeatureExtractor, FeatureSet, ExtractedFeature, FeatureType
)
from app.schemas.ml_feedback import (
    FeedbackCreate, FeedbackType, ExpertiseLevel, FeedbackBatch, 
    OneClickFeedback, FeedbackFilter
)

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def sample_impact_card_data():
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
                "description": "Significant product impact",
                "category": "Product Development"
            }
        ],
        "key_insights": [
            {"text": "Test insight 1", "confidence": 0.9},
            {"text": "Test insight 2", "confidence": 0.8}
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
        "processing_time": "4.2 seconds",
        "raw_data": {},
        "explainability": {"reasoning": "", "impact_areas": [], "key_insights": [], "source_summary": {}},
    }


class TestMLFoundationComponents:
    """Test ML foundation components."""

    @pytest.mark.asyncio
    async def test_feedback_record_creation(self, db_session: AsyncSession, sample_impact_card_data):
        """Test creating a feedback record."""
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
    async def test_feature_extraction_basic(self, db_session: AsyncSession, sample_impact_card_data):
        """Test basic feature extraction from impact cards."""
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

    @pytest.mark.asyncio
    async def test_temporal_feature_extraction(self, db_session: AsyncSession):
        """Test temporal feature extraction from timestamps."""
        extractor = FeatureExtractor(db_session)
        test_timestamp = datetime(2024, 3, 15, 14, 30, 0)  # Friday, 2:30 PM
        
        features = extractor._extract_temporal_features(test_timestamp, "test")
        
        feature_names = {f.name for f in features}
        assert "test_hour" in feature_names
        assert "test_day_of_week" in feature_names
        assert "test_days_since_epoch" in feature_names
        
        # Check specific values
        hour_feature = next(f for f in features if f.name == "test_hour")
        assert hour_feature.value == 14.0
        assert hour_feature.feature_type == FeatureType.TEMPORAL
        
        day_feature = next(f for f in features if f.name == "test_day_of_week")
        assert day_feature.value == 4.0  # Friday is day 4 (0-indexed)

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

    def test_feedback_schema_validation(self):
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

    def test_one_click_feedback_validation(self):
        """Test one-click feedback schema validation."""
        # Valid actions
        valid_actions = [
            'thumbs_up', 'thumbs_down',
            'too_high', 'too_low', 'just_right',
            'relevant', 'not_relevant',
            'correct_category', 'wrong_category'
        ]
        
        for action in valid_actions:
            feedback = OneClickFeedback(
                impact_card_id=1,
                feedback_action=action
            )
            assert feedback.feedback_action == action

        # Invalid action should fail
        with pytest.raises(ValueError, match="Invalid feedback action"):
            OneClickFeedback(
                impact_card_id=1,
                feedback_action="invalid_action"
            )

    @pytest.mark.asyncio
    async def test_model_performance_metric_creation(self, db_session: AsyncSession):
        """Test model performance metric creation."""
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
        job.started_at = datetime.now(timezone.utc)
        await db_session.commit()

        # Update job status to completed
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.new_model_version = "test_model_v2"
        job.performance_improvement = 0.05
        await db_session.commit()

        assert job.status == "completed"
        assert job.started_at is not None
        assert job.completed_at is not None
        assert job.new_model_version == "test_model_v2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])