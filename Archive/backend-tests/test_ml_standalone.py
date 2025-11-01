"""
Standalone unit tests for ML Foundation Components

This module tests the core ML foundation components without pytest configuration
to avoid circular import issues.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Use proper package imports instead of sys.path manipulation

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


async def test_create_feedback_record():
    """Test creating a basic feedback record."""
    print("Testing feedback record creation...")
    
    async with TestSessionLocal() as db_session:
        # Create impact card first
        sample_data = get_sample_impact_card_data()
        impact_card = ImpactCard(**sample_data)
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

        # Assertions
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
        
        print("✓ Feedback record creation test passed")


async def test_feedback_record_defaults():
    """Test feedback record default values."""
    print("Testing feedback record defaults...")
    
    async with TestSessionLocal() as db_session:
        # Create impact card first
        sample_data = get_sample_impact_card_data()
        impact_card = ImpactCard(**sample_data)
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

        # Assertions
        assert feedback.confidence == 1.0  # Default confidence
        assert feedback.processed is False  # Default processed status
        assert feedback.feedback_context == {}  # Default empty context
        assert feedback.user_expertise_level == "unknown"  # Default expertise level
        assert feedback.processed_at is None  # Not processed yet
        
        print("✓ Feedback record defaults test passed")


async def test_feedback_context_handling():
    """Test feedback context JSON field handling."""
    print("Testing feedback context handling...")
    
    async with TestSessionLocal() as db_session:
        # Create impact card first
        sample_data = get_sample_impact_card_data()
        impact_card = ImpactCard(**sample_data)
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

        # Assertions
        assert feedback.feedback_context == feedback_context
        assert feedback.feedback_context["source"] == "one_click"
        assert feedback.feedback_context["metadata"]["session_id"] == "abc123"
        
        print("✓ Feedback context handling test passed")


def test_feedback_schema_validation():
    """Test Pydantic schema validation for feedback."""
    print("Testing feedback schema validation...")
    
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
    try:
        FeedbackCreate(
            impact_card_id=1,
            feedback_type=FeedbackType.ACCURACY,
            confidence=1.5  # Invalid confidence > 1.0
        )
        assert False, "Should have raised ValueError for confidence > 1.0"
    except ValueError:
        pass  # Expected

    try:
        FeedbackCreate(
            impact_card_id=1,
            feedback_type=FeedbackType.ACCURACY,
            confidence=-0.1  # Invalid confidence < 0.0
        )
        assert False, "Should have raised ValueError for confidence < 0.0"
    except ValueError:
        pass  # Expected
    
    print("✓ Feedback schema validation test passed")


async def test_feedback_impact_card_relationship():
    """Test relationship between feedback and impact card models."""
    print("Testing feedback-impact card relationship...")
    
    async with TestSessionLocal() as db_session:
        # Create impact card
        sample_data = get_sample_impact_card_data()
        impact_card = ImpactCard(**sample_data)
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
        
        print("✓ Feedback-impact card relationship test passed")


async def test_model_performance_metric_constraints():
    """Test model performance metric database constraints."""
    print("Testing model performance metric constraints...")
    
    async with TestSessionLocal() as db_session:
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
        
        print("✓ Model performance metric constraints test passed")


async def test_training_job_lifecycle():
    """Test training job model lifecycle and status transitions."""
    print("Testing training job lifecycle...")
    
    async with TestSessionLocal() as db_session:
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
        
        print("✓ Training job lifecycle test passed")


def test_feature_type_enum():
    """Test FeatureType enum values."""
    print("Testing FeatureType enum...")
    
    from app.services.feature_extractor import FeatureType
    
    assert FeatureType.TEXTUAL == "textual"
    assert FeatureType.NUMERICAL == "numerical"
    assert FeatureType.CATEGORICAL == "categorical"
    assert FeatureType.TEMPORAL == "temporal"
    assert FeatureType.STRUCTURAL == "structural"
    
    print("✓ FeatureType enum test passed")


def test_extracted_feature_creation():
    """Test ExtractedFeature dataclass creation."""
    print("Testing ExtractedFeature creation...")
    
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
    
    print("✓ ExtractedFeature creation test passed")


def test_feature_set_creation():
    """Test FeatureSet dataclass creation."""
    print("Testing FeatureSet creation...")
    
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
    
    print("✓ FeatureSet creation test passed")


async def run_all_tests():
    """Run all tests."""
    print("Setting up test database...")
    await setup_database()
    
    try:
        print("\n=== Running ML Foundation Component Tests ===\n")
        
        # Test feedback collection and validation
        print("1. Feedback Collection and Validation Tests:")
        await test_create_feedback_record()
        await test_feedback_record_defaults()
        await test_feedback_context_handling()
        test_feedback_schema_validation()
        
        print("\n2. Database Model Relationships and Constraints Tests:")
        await test_feedback_impact_card_relationship()
        await test_model_performance_metric_constraints()
        await test_training_job_lifecycle()
        
        print("\n3. Feature Extraction Pipeline Tests:")
        test_feature_type_enum()
        test_extracted_feature_creation()
        test_feature_set_creation()
        
        print("\n=== All Tests Passed! ===")
        
    finally:
        print("\nTearing down test database...")
        await teardown_database()


if __name__ == "__main__":
    asyncio.run(run_all_tests())