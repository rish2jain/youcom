"""
Simplified unit tests for ML Foundation Components

This module tests the core ML foundation components without importing the full app
to avoid circular import issues during testing.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select

# Import only the models and services we need for testing
from app.database import Base
from app.models.ml_training import FeedbackRecord, ModelPerformanceMetric, TrainingJob
from app.models.impact_card import ImpactCard
from app.schemas.ml_feedback import FeedbackCreate, FeedbackType, ExpertiseLevel

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


class TestFeatureExtractionBasics:
    """Test basic feature extraction functionality without complex dependencies."""

    def test_feature_type_enum(self):
        """Test FeatureType enum values."""
        from app.services.feature_extractor import FeatureType
        
        assert FeatureType.TEXTUAL == "textual"
        assert FeatureType.NUMERICAL == "numerical"
        assert FeatureType.CATEGORICAL == "categorical"
        assert FeatureType.TEMPORAL == "temporal"
        assert FeatureType.STRUCTURAL == "structural"

    def test_extracted_feature_creation(self):
        """Test ExtractedFeature dataclass creation."""
        from app.services.feature_extractor import ExtractedFeature, FeatureType
        
        feature = ExtractedFeature(
            name="test_feature",
            value=0.85,
            feature_type=FeatureType.NUMERICAL,
            confidence=0.9,
            metadata={"source": "test"}
        )
        
        assert feature.name == "test_feature"
        assert feature.value == 0.85
        assert feature.feature_type == FeatureType.NUMERICAL
        assert feature.confidence == 0.9
        assert feature.metadata["source"] == "test"

    def test_feature_set_creation(self):
        """Test FeatureSet dataclass creation."""
        from app.services.feature_extractor import FeatureSet, ExtractedFeature, FeatureType
        
        features = [
            ExtractedFeature(
                name="feature1",
                value=0.5,
                feature_type=FeatureType.NUMERICAL,
                confidence=1.0,
                metadata={}
            ),
            ExtractedFeature(
                name="feature2",
                value="category_a",
                feature_type=FeatureType.CATEGORICAL,
                confidence=0.8,
                metadata={}
            )
        ]
        
        feature_set = FeatureSet(
            entity_id="test_entity_1",
            entity_type="test_type",
            features=features,
            extraction_timestamp=datetime.utcnow(),
            feature_hash="test_hash_123"
        )
        
        assert feature_set.entity_id == "test_entity_1"
        assert feature_set.entity_type == "test_type"
        assert len(feature_set.features) == 2
        assert feature_set.feature_hash == "test_hash_123"