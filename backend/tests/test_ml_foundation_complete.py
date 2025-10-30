"""
Complete unit tests for ML Foundation Components

This module provides comprehensive testing for all ML foundation components
including areas not covered by existing tests.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select

# Import models and services
from app.database import Base
from app.models.ml_training import FeedbackRecord, ModelPerformanceMetric, TrainingJob
from app.models.impact_card import ImpactCard
from app.models.ml_model_registry import FeatureStoreRecord
from app.services.feature_extractor import (
    FeatureExtractor, FeatureSet, ExtractedFeature, FeatureType
)
from app.services.feature_store import FeatureStore
from app.schemas.ml_feedback import (
    FeedbackCreate, FeedbackType, ExpertiseLevel, FeedbackBatch, 
    OneClickFeedback, FeedbackFilter, FeedbackStats
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

@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for each test."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
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


class TestAdvancedFeatureExtraction:
    """Test advanced feature extraction functionality."""

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
    async def test_impact_areas_feature_extraction(self, db_session: AsyncSession):
        """Test feature extraction from impact areas."""
        extractor = FeatureExtractor(db_session)
        impact_areas = [
            {"category": "Product Development", "impact": 80},
            {"category": "Market Position", "impact": 70},
            {"category": "Product Development", "impact": 75}  # Duplicate category
        ]
        
        features = extractor._extract_impact_areas_features(impact_areas)
        
        feature_names = {f.name for f in features}
        assert "impact_areas_count" in feature_names
        assert "has_impact_category_product_development" in feature_names
        assert "has_impact_category_market_position" in feature_names
        
        # Check count
        count_feature = next(f for f in features if f.name == "impact_areas_count")
        assert count_feature.value == 3.0

    @pytest.mark.asyncio
    async def test_insights_feature_extraction(self, db_session: AsyncSession):
        """Test feature extraction from key insights."""
        extractor = FeatureExtractor(db_session)
        insights = [
            {"text": "Short insight"},
            {"text": "This is a much longer insight with more detailed information"},
            "Simple string insight"
        ]
        
        features = extractor._extract_insights_features(insights)
        
        feature_names = {f.name for f in features}
        assert "insights_count" in feature_names
        assert "avg_insight_length" in feature_names
        
        count_feature = next(f for f in features if f.name == "insights_count")
        assert count_feature.value == 3.0
        
        avg_length_feature = next(f for f in features if f.name == "avg_insight_length")
        expected_avg = (len("Short insight") + len("This is a much longer insight with more detailed information") + len("Simple string insight")) / 3
        assert avg_length_feature.value == expected_avg

    @pytest.mark.asyncio
    async def test_source_features_extraction(self, db_session: AsyncSession):
        """Test feature extraction from source breakdown."""
        extractor = FeatureExtractor(db_session)
        source_breakdown = {
            "news_articles": 15,
            "search_results": 10,
            "research_citations": 5
        }
        
        features = extractor._extract_source_features(source_breakdown)
        
        feature_names = {f.name for f in features}
        assert "source_diversity" in feature_names
        assert "source_news_articles_count" in feature_names
        assert "source_search_results_count" in feature_names
        assert "source_research_citations_count" in feature_names
        
        diversity_feature = next(f for f in features if f.name == "source_diversity")
        assert diversity_feature.value == 3.0

    @pytest.mark.asyncio
    async def test_textual_features_extraction(self, db_session: AsyncSession, sample_impact_card_data):
        """Test textual feature extraction."""
        impact_card = ImpactCard(**sample_impact_card_data)
        
        extractor = FeatureExtractor(db_session)
        features = extractor._extract_textual_features(impact_card)
        
        feature_names = {f.name for f in features}
        assert "competitor_name_length" in feature_names
        assert "processing_time_seconds" in feature_names
        
        name_length_feature = next(f for f in features if f.name == "competitor_name_length")
        assert name_length_feature.value == len("Test Competitor")
        
        # Test processing time parsing
        time_feature = next(f for f in features if f.name == "processing_time_seconds")
        assert time_feature.value == 4.2  # "4.2 seconds" should parse to 4.2

    @pytest.mark.asyncio
    async def test_feature_hash_computation(self, db_session: AsyncSession):
        """Test feature hash computation for caching."""
        extractor = FeatureExtractor(db_session)
        
        features1 = [
            ExtractedFeature("test1", 1.0, FeatureType.NUMERICAL, 1.0, {}),
            ExtractedFeature("test2", "cat", FeatureType.CATEGORICAL, 0.9, {})
        ]
        
        features2 = [
            ExtractedFeature("test1", 1.0, FeatureType.NUMERICAL, 1.0, {}),
            ExtractedFeature("test2", "cat", FeatureType.CATEGORICAL, 0.9, {})
        ]
        
        features3 = [
            ExtractedFeature("test1", 2.0, FeatureType.NUMERICAL, 1.0, {}),  # Different value
            ExtractedFeature("test2", "cat", FeatureType.CATEGORICAL, 0.9, {})
        ]
        
        hash1 = extractor._compute_feature_hash(features1)
        hash2 = extractor._compute_feature_hash(features2)
        hash3 = extractor._compute_feature_hash(features3)
        
        assert hash1 == hash2  # Same features should have same hash
        assert hash1 != hash3  # Different features should have different hash

    @pytest.mark.asyncio
    async def test_feature_normalization_ranges(self, db_session: AsyncSession):
        """Test feature normalization with known ranges."""
        extractor = FeatureExtractor(db_session)
        
        # Test various features with known normalization ranges
        test_cases = [
            ("risk_score", 50.0, 0.5),  # 50 out of 100 = 0.5
            ("confidence_score", 75.0, 0.75),  # 75 out of 100 = 0.75
            ("credibility_score", 0.8, 0.8),  # Already in [0,1] range
            ("total_sources", 25.0, 0.5),  # 25 out of 50 max = 0.5
            ("creation_hour", 12.0, 12.0/23.0),  # 12 out of 23 max
        ]
        
        for feature_name, input_value, expected_output in test_cases:
            normalized = extractor._normalize_numerical_feature(feature_name, input_value)
            assert abs(normalized - expected_output) < 0.01, f"Failed for {feature_name}: expected {expected_output}, got {normalized}"

    @pytest.mark.asyncio
    async def test_batch_feature_extraction_error_handling(self, db_session: AsyncSession):
        """Test batch feature extraction with some invalid entity IDs."""
        extractor = FeatureExtractor(db_session)
        
        # Mix of valid and invalid entity IDs
        entity_ids = ["1", "999", "invalid", "2"]
        
        # Should not raise exception, just skip invalid IDs
        feature_sets = await extractor.extract_batch_features("impact_card", entity_ids, use_cache=False)
        
        # Should return empty list since no valid impact cards exist
        assert len(feature_sets) == 0


class TestFeatureStore:
    """Test feature store functionality."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_features_db_only(self, db_session: AsyncSession, sample_impact_card_data):
        """Test storing and retrieving features from database only (no Redis)."""
        # Create impact card and extract features
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        extractor = FeatureExtractor(db_session)
        feature_set = await extractor.extract_impact_card_features(impact_card)

        # Mock Redis to be unavailable
        with patch('app.services.feature_store.redis.from_url', side_effect=Exception("Redis unavailable")):
            feature_store = FeatureStore(db_session)
            
            # Store features (should work with DB only)
            success = await feature_store.store_features(feature_set)
            assert success is True

            # Retrieve features (should work with DB only)
            retrieved_features = await feature_store.retrieve_features(
                feature_set.entity_id, 
                feature_set.entity_type,
                use_cache=False
            )

            assert retrieved_features is not None
            assert retrieved_features.entity_id == feature_set.entity_id
            assert len(retrieved_features.features) == len(feature_set.features)

    @pytest.mark.asyncio
    async def test_feature_store_record_creation(self, db_session: AsyncSession):
        """Test FeatureStoreRecord model creation and constraints."""
        # Create a feature store record
        features_data = [
            {
                "name": "test_feature",
                "value": 0.5,
                "feature_type": "numerical",
                "confidence": 0.9,
                "metadata": {"source": "test"}
            }
        ]
        
        record = FeatureStoreRecord(
            entity_id="test_entity_1",
            entity_type="test_type",
            feature_hash="test_hash_123",
            features_json=features_data,
            extraction_timestamp=datetime.utcnow(),
            feature_count=1,
            avg_confidence=0.9,
            feature_types=["numerical"]
        )
        
        db_session.add(record)
        await db_session.commit()
        await db_session.refresh(record)
        
        assert record.id is not None
        assert record.entity_id == "test_entity_1"
        assert record.feature_count == 1
        assert record.avg_confidence == 0.9
        assert "numerical" in record.feature_types

    @pytest.mark.asyncio
    async def test_feature_statistics_calculation(self, db_session: AsyncSession):
        """Test feature statistics calculation."""
        feature_store = FeatureStore(db_session)
        
        # Create multiple feature store records
        records_data = [
            ("entity_1", "impact_card", 5, 0.8, ["numerical", "categorical"]),
            ("entity_2", "impact_card", 7, 0.9, ["numerical", "temporal"]),
            ("entity_3", "feedback", 3, 0.7, ["categorical"]),
        ]
        
        for entity_id, entity_type, count, confidence, types in records_data:
            record = FeatureStoreRecord(
                entity_id=entity_id,
                entity_type=entity_type,
                feature_hash=f"hash_{entity_id}",
                features_json=[],
                extraction_timestamp=datetime.utcnow(),
                feature_count=count,
                avg_confidence=confidence,
                feature_types=types
            )
            db_session.add(record)
        
        await db_session.commit()
        
        # Get statistics
        stats = await feature_store.get_feature_statistics(days=30)
        
        assert stats["total_records"] == 3
        assert stats["entity_types"]["impact_card"] == 2
        assert stats["entity_types"]["feedback"] == 1
        assert stats["avg_feature_count"] == (5 + 7 + 3) / 3
        assert stats["avg_confidence"] == (0.8 + 0.9 + 0.7) / 3
        assert "numerical" in stats["feature_types"]
        assert "categorical" in stats["feature_types"]
        assert "temporal" in stats["feature_types"]

    @pytest.mark.asyncio
    async def test_cleanup_old_features(self, db_session: AsyncSession):
        """Test cleanup of old feature records."""
        feature_store = FeatureStore(db_session)
        
        # Create old and new records
        old_timestamp = datetime.utcnow() - timedelta(days=100)
        new_timestamp = datetime.utcnow() - timedelta(days=10)
        
        old_record = FeatureStoreRecord(
            entity_id="old_entity",
            entity_type="test",
            feature_hash="old_hash",
            features_json=[],
            extraction_timestamp=old_timestamp,
            feature_count=1,
            avg_confidence=0.5,
            feature_types=["numerical"],
            created_at=old_timestamp
        )
        
        new_record = FeatureStoreRecord(
            entity_id="new_entity",
            entity_type="test",
            feature_hash="new_hash",
            features_json=[],
            extraction_timestamp=new_timestamp,
            feature_count=1,
            avg_confidence=0.5,
            feature_types=["numerical"],
            created_at=new_timestamp
        )
        
        db_session.add(old_record)
        db_session.add(new_record)
        await db_session.commit()
        
        # Cleanup records older than 90 days
        deleted_count = await feature_store.cleanup_old_features(days=90)
        
        assert deleted_count == 1
        
        # Verify only new record remains
        result = await db_session.execute(select(FeatureStoreRecord))
        remaining_records = result.scalars().all()
        assert len(remaining_records) == 1
        assert remaining_records[0].entity_id == "new_entity"

    @pytest.mark.asyncio
    async def test_batch_feature_retrieval(self, db_session: AsyncSession):
        """Test batch feature retrieval."""
        feature_store = FeatureStore(db_session)
        
        # Create multiple feature records
        entity_ids = ["entity_1", "entity_2", "entity_3"]
        for entity_id in entity_ids:
            record = FeatureStoreRecord(
                entity_id=entity_id,
                entity_type="test_type",
                feature_hash=f"hash_{entity_id}",
                features_json=[
                    {
                        "name": "test_feature",
                        "value": 0.5,
                        "feature_type": "numerical",
                        "confidence": 0.9,
                        "metadata": {}
                    }
                ],
                extraction_timestamp=datetime.utcnow(),
                feature_count=1,
                avg_confidence=0.9,
                feature_types=["numerical"]
            )
            db_session.add(record)
        
        await db_session.commit()
        
        # Retrieve batch
        results = await feature_store.retrieve_batch_features(
            entity_ids, "test_type", use_cache=False
        )
        
        assert len(results) == 3
        for entity_id in entity_ids:
            assert entity_id in results
            assert results[entity_id].entity_id == entity_id
            assert len(results[entity_id].features) == 1


class TestMLFeedbackSchemas:
    """Test ML feedback schema validation and edge cases."""

    def test_feedback_batch_validation(self):
        """Test feedback batch schema validation."""
        # Valid batch
        valid_batch = FeedbackBatch(
            feedback_items=[
                FeedbackCreate(
                    impact_card_id=1,
                    feedback_type=FeedbackType.ACCURACY,
                    confidence=0.8
                ),
                FeedbackCreate(
                    impact_card_id=2,
                    feedback_type=FeedbackType.RELEVANCE,
                    confidence=0.9
                )
            ]
        )
        assert len(valid_batch.feedback_items) == 2

        # Empty batch should fail
        with pytest.raises(ValueError, match="At least one feedback item is required"):
            FeedbackBatch(feedback_items=[])

        # Too many items should fail
        too_many_items = [
            FeedbackCreate(impact_card_id=i, feedback_type=FeedbackType.ACCURACY)
            for i in range(51)  # More than 50 items
        ]
        with pytest.raises(ValueError, match="Maximum 50 feedback items allowed"):
            FeedbackBatch(feedback_items=too_many_items)

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

    def test_feedback_filter_date_validation(self):
        """Test feedback filter date range validation."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        # Valid date range
        valid_filter = FeedbackFilter(
            start_date=start_date,
            end_date=end_date
        )
        assert valid_filter.start_date == start_date
        assert valid_filter.end_date == end_date

        # Invalid date range (end before start)
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            FeedbackFilter(
                start_date=end_date,
                end_date=start_date
            )

    def test_feedback_create_corrected_value_validation(self):
        """Test feedback creation with corrected value validation."""
        # Valid: both original and corrected values provided
        valid_feedback = FeedbackCreate(
            impact_card_id=1,
            feedback_type=FeedbackType.ACCURACY,
            original_value=0.7,
            corrected_value=0.8
        )
        assert valid_feedback.original_value == 0.7
        assert valid_feedback.corrected_value == 0.8

        # Invalid: original value provided but corrected value missing
        with pytest.raises(ValueError, match="corrected_value is required when original_value is provided"):
            FeedbackCreate(
                impact_card_id=1,
                feedback_type=FeedbackType.ACCURACY,
                original_value=0.7,
                corrected_value=None
            )

    def test_feedback_stats_schema(self):
        """Test feedback stats schema."""
        stats = FeedbackStats(
            total_feedback_count=100,
            feedback_by_type={"accuracy": 50, "relevance": 30, "severity": 20},
            feedback_by_expertise={"expert": 40, "intermediate": 35, "novice": 25},
            processed_count=80,
            pending_count=20,
            average_confidence=0.85
        )
        
        assert stats.total_feedback_count == 100
        assert stats.processed_count + stats.pending_count == 100
        assert stats.feedback_by_type["accuracy"] == 50
        assert stats.average_confidence == 0.85


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases in ML foundation components."""

    @pytest.mark.asyncio
    async def test_feature_extraction_with_missing_data(self, db_session: AsyncSession):
        """Test feature extraction when impact card has missing optional fields."""
        # Create impact card with minimal data
        minimal_card_data = {
            "competitor_name": "Minimal Competitor",
            "risk_score": 50,
            "risk_level": "medium",
            "confidence_score": 60,
            "requires_review": False,
            "impact_areas": [],  # Empty
            "key_insights": [],  # Empty
            "recommended_actions": [],
            "next_steps_plan": [],
            "total_sources": 0,  # Zero sources
            "source_breakdown": {},  # Empty
            "source_quality": {"score": 0.0, "tiers": {}, "total": 0, "top_sources": []},
            "api_usage": {"total_calls": 0},
            "processing_time": None,  # Missing
            "raw_data": {},
            "explainability": {},
        }
        
        impact_card = ImpactCard(**minimal_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        extractor = FeatureExtractor(db_session)
        feature_set = await extractor.extract_impact_card_features(impact_card)

        # Should still extract basic features
        assert feature_set is not None
        assert len(feature_set.features) > 0
        
        # Should have basic numerical features
        feature_names = {f.name for f in feature_set.features}
        assert "risk_score" in feature_names
        assert "confidence_score" in feature_names
        assert "total_sources" in feature_names

    @pytest.mark.asyncio
    async def test_feature_validation_with_invalid_values(self, db_session: AsyncSession):
        """Test feature validation with invalid numerical values."""
        extractor = FeatureExtractor(db_session)
        
        # Create feature set with invalid values
        invalid_features = [
            ExtractedFeature("nan_feature", float('nan'), FeatureType.NUMERICAL, 1.0, {}),
            ExtractedFeature("inf_feature", float('inf'), FeatureType.NUMERICAL, 1.0, {}),
            ExtractedFeature("invalid_confidence", 1.0, FeatureType.NUMERICAL, 1.5, {}),  # Invalid confidence
            ExtractedFeature("wrong_type", "text", FeatureType.NUMERICAL, 1.0, {}),  # Wrong type
        ]
        
        feature_set = FeatureSet(
            entity_id="test_invalid",
            entity_type="test",
            features=invalid_features,
            extraction_timestamp=datetime.utcnow(),
            feature_hash="test_hash"
        )
        
        is_valid, errors = await extractor.validate_features(feature_set)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("invalid numerical value" in error for error in errors)
        assert any("invalid confidence" in error for error in errors)
        assert any("should be numerical" in error for error in errors)

    @pytest.mark.asyncio
    async def test_feature_store_with_database_errors(self, db_session: AsyncSession):
        """Test feature store behavior with database errors."""
        feature_store = FeatureStore(db_session)
        
        # Create a valid feature set
        feature_set = FeatureSet(
            entity_id="test_entity",
            entity_type="test_type",
            features=[
                ExtractedFeature("test", 1.0, FeatureType.NUMERICAL, 1.0, {})
            ],
            extraction_timestamp=datetime.utcnow(),
            feature_hash="test_hash"
        )
        
        # Mock database session to raise an error
        with patch.object(db_session, 'commit', side_effect=Exception("Database error")):
            success = await feature_store.store_features(feature_set)
            assert success is False

    @pytest.mark.asyncio
    async def test_cache_expiration_handling(self, db_session: AsyncSession):
        """Test feature cache expiration handling."""
        extractor = FeatureExtractor(db_session)
        
        # Create feature set with old timestamp
        old_timestamp = datetime.utcnow() - timedelta(hours=2)
        feature_set = FeatureSet(
            entity_id="test_entity",
            entity_type="test_type",
            features=[ExtractedFeature("test", 1.0, FeatureType.NUMERICAL, 1.0, {})],
            extraction_timestamp=old_timestamp,
            feature_hash="test_hash"
        )
        
        # Cache the feature set
        await extractor.cache_features(feature_set)
        
        # Try to retrieve - should return None due to expiration
        cached = await extractor.get_cached_features("test_type", "test_entity")
        assert cached is None  # Should be expired and removed

    @pytest.mark.asyncio
    async def test_concurrent_feature_extraction(self, db_session: AsyncSession, sample_impact_card_data):
        """Test concurrent feature extraction doesn't cause issues."""
        # Create multiple impact cards
        impact_cards = []
        for i in range(5):
            card_data = sample_impact_card_data.copy()
            card_data["competitor_name"] = f"Concurrent Competitor {i}"
            
            impact_card = ImpactCard(**card_data)
            db_session.add(impact_card)
            impact_cards.append(impact_card)

        await db_session.commit()
        
        for card in impact_cards:
            await db_session.refresh(card)

        # Extract features concurrently
        extractor = FeatureExtractor(db_session)
        tasks = [
            extractor.extract_impact_card_features(card)
            for card in impact_cards
        ]
        
        feature_sets = await asyncio.gather(*tasks)
        
        assert len(feature_sets) == 5
        for feature_set in feature_sets:
            assert feature_set is not None
            assert len(feature_set.features) > 0