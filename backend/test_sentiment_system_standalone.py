"""
Standalone unit tests for Sentiment Analysis System

This module tests the sentiment analysis system components without importing the full app.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import select

# Import only the models and services we need for testing

from app.database import Base
from app.models.sentiment_analysis import (
    SentimentAnalysis, SentimentTrend, SentimentAlert, SentimentProcessingQueue
)
from app.services.sentiment_classifier import (
    EntityRecognizer, SentimentClassifier, EntityRecognitionResult, 
    SentimentClassificationResult
)
from app.services.sentiment_processor import (
    SentimentProcessor, SentimentResult, EntityMention
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


@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

class TestSentimentAnalysisModels:
    """Test sentiment analysis database models."""

    @pytest.mark.asyncio
    async def test_sentiment_analysis_creation(self, db_session: AsyncSession):
        """Test SentimentAnalysis model creation and constraints."""
        sentiment = SentimentAnalysis(
            content_id="news_123",
            content_type="news",
            entity_name="Microsoft",
            entity_type="company",
            sentiment_score=0.75,
            sentiment_label="positive",
            confidence=0.85,
            processing_timestamp=datetime.utcnow(),
            source_url="https://example.com/news",
            content_text="Microsoft announced strong quarterly earnings...",
            analysis_metadata={
                "entity_confidence": 0.9,
                "sentiment_reasoning": "Positive earnings announcement",
                "processing_version": "2.0"
            }
        )
        
        db_session.add(sentiment)
        await db_session.commit()
        await db_session.refresh(sentiment)
        
        assert sentiment.id is not None
        assert sentiment.content_id == "news_123"
        assert sentiment.entity_name == "Microsoft"
        assert sentiment.sentiment_score == 0.75
        assert sentiment.sentiment_label == "positive"
        assert sentiment.confidence == 0.85
        assert sentiment.analysis_metadata["processing_version"] == "2.0"

    @pytest.mark.asyncio
    async def test_sentiment_trend_creation(self, db_session: AsyncSession):
        """Test SentimentTrend model creation."""
        trend = SentimentTrend(
            entity_name="Apple",
            entity_type="company",
            timeframe="daily",
            period_start=datetime.utcnow() - timedelta(days=1),
            period_end=datetime.utcnow(),
            average_sentiment=0.65,
            sentiment_volatility=0.15,
            total_mentions=25,
            positive_mentions=15,
            negative_mentions=5,
            neutral_mentions=5,
            trend_direction="improving",
            trend_strength=0.7
        )
        
        db_session.add(trend)
        await db_session.commit()
        await db_session.refresh(trend)
        
        assert trend.id is not None
        assert trend.entity_name == "Apple"
        assert trend.average_sentiment == 0.65
        assert trend.total_mentions == 25
        assert trend.trend_direction == "improving"
        assert trend.positive_mentions + trend.negative_mentions + trend.neutral_mentions == trend.total_mentions

    @pytest.mark.asyncio
    async def test_sentiment_alert_creation(self, db_session: AsyncSession):
        """Test SentimentAlert model creation."""
        alert = SentimentAlert(
            entity_name="Tesla",
            entity_type="company",
            alert_type="shift",
            alert_severity="high",
            current_sentiment=0.2,
            previous_sentiment=0.7,
            sentiment_change=-71.4,  # Percentage change
            threshold_value=0.5,
            confidence=0.9,
            triggered_at=datetime.utcnow(),
            is_resolved=False,
            notification_sent=True,
            alert_metadata={
                "trigger_reason": "Significant sentiment drop",
                "affected_mentions": 15
            }
        )
        
        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)
        
        assert alert.id is not None
        assert alert.entity_name == "Tesla"
        assert alert.alert_type == "shift"
        assert alert.sentiment_change == -71.4
        assert alert.is_resolved is False
        assert alert.notification_sent is True

    @pytest.mark.asyncio
    async def test_sentiment_processing_queue_creation(self, db_session: AsyncSession):
        """Test SentimentProcessingQueue model creation."""
        queue_item = SentimentProcessingQueue(
            content_id="queue_item_123",
            content_type="social",
            content_text="Breaking: Company X announces major partnership with Company Y",
            source_url="https://twitter.com/example",
            priority=3,  # High priority
            status="pending",
            created_at=datetime.utcnow(),
            retry_count=0,
            max_retries=3,
            queue_metadata={
                "source_platform": "twitter",
                "urgency": "high"
            }
        )
        
        db_session.add(queue_item)
        await db_session.commit()
        await db_session.refresh(queue_item)
        
        assert queue_item.id is not None
        assert queue_item.content_id == "queue_item_123"
        assert queue_item.priority == 3
        assert queue_item.status == "pending"
        assert queue_item.retry_count == 0


class TestEntityRecognizer:
    """Test entity recognition functionality."""

    def test_entity_recognizer_initialization(self):
        """Test EntityRecognizer initialization."""
        # Mock YouComClient to avoid API dependency
        with patch('app.services.sentiment_classifier.YouComClient'):
            recognizer = EntityRecognizer()
            
            assert len(recognizer.company_patterns) > 0
            assert len(recognizer.product_patterns) > 0
            assert len(recognizer.market_patterns) > 0

    def test_company_name_validation(self):
        """Test company name validation logic."""
        with patch('app.services.sentiment_classifier.YouComClient'):
            recognizer = EntityRecognizer()
            
            # Valid company names
            assert recognizer._is_valid_company_name("Microsoft") is True
            assert recognizer._is_valid_company_name("Apple Inc") is True
            assert recognizer._is_valid_company_name("Alphabet") is True
            
            # Invalid company names
            assert recognizer._is_valid_company_name("the") is False
            assert recognizer._is_valid_company_name("and") is False
            assert recognizer._is_valid_company_name("123") is False

    def test_product_name_validation(self):
        """Test product name validation logic."""
        with patch('app.services.sentiment_classifier.YouComClient'):
            recognizer = EntityRecognizer()
            
            # Valid product names
            assert recognizer._is_valid_product_name("iPhone") is True
            assert recognizer._is_valid_product_name("Azure") is True
            assert recognizer._is_valid_product_name("ChatGPT") is True
            
            # Invalid product names
            assert recognizer._is_valid_product_name("a") is False
            assert recognizer._is_valid_product_name("the") is False

    def test_context_extraction(self):
        """Test context extraction around entity mentions."""
        with patch('app.services.sentiment_classifier.YouComClient'):
            recognizer = EntityRecognizer()
            
            text = "Microsoft announced strong quarterly earnings with revenue growth of 15%"
            context = recognizer._extract_context(text, 0, 9, window=20)  # "Microsoft"
            
            assert "Microsoft announced strong" in context
            assert len(context) <= 49  # 9 + 20*2

    @pytest.mark.asyncio
    async def test_pattern_based_recognition(self):
        """Test pattern-based entity recognition."""
        with patch('app.services.sentiment_classifier.YouComClient'):
            recognizer = EntityRecognizer()
            
            text = "Microsoft Corp announced that Azure platform gained 25% market share in cloud computing"
            entities = await recognizer._pattern_based_recognition(text)
            
            # Should find Microsoft as a company
            company_entities = [e for e in entities if e.entity_type == "company"]
            assert len(company_entities) > 0
            
            microsoft_entity = next((e for e in company_entities if "Microsoft" in e.name), None)
            assert microsoft_entity is not None
            assert microsoft_entity.confidence > 0.5

    def test_entity_deduplication(self):
        """Test entity deduplication logic."""
        with patch('app.services.sentiment_classifier.YouComClient'):
            recognizer = EntityRecognizer()
            
            # Create duplicate entities with different confidence scores
            entities = [
                EntityRecognitionResult("Microsoft", "company", 0.7, "context1", 0, 9, {}),
                EntityRecognitionResult("microsoft", "company", 0.9, "context2", 10, 19, {}),  # Same company, different case
                EntityRecognitionResult("Apple", "company", 0.8, "context3", 20, 25, {}),
            ]
            
            deduplicated = recognizer._deduplicate_entities(entities)
            
            # Should have 2 unique entities (Microsoft with higher confidence, Apple)
            assert len(deduplicated) == 2
            
            microsoft_entity = next((e for e in deduplicated if e.name.lower() == "microsoft"), None)
            assert microsoft_entity is not None
            assert microsoft_entity.confidence == 0.9  # Higher confidence version kept


class TestSentimentClassifier:
    """Test sentiment classification functionality."""

    def test_sentiment_classifier_initialization(self):
        """Test SentimentClassifier initialization."""
        with patch('app.services.sentiment_classifier.YouComClient'):
            classifier = SentimentClassifier()
            
            assert len(classifier.positive_indicators) > 0
            assert len(classifier.negative_indicators) > 0
            assert "excellent" in classifier.positive_indicators
            assert "terrible" in classifier.negative_indicators

    def test_rule_based_sentiment_classification(self):
        """Test rule-based sentiment classification."""
        with patch('app.services.sentiment_classifier.YouComClient'):
            classifier = SentimentClassifier()
            
            # Positive text
            positive_text = "Microsoft announced excellent quarterly results with outstanding revenue growth"
            positive_result = classifier._rule_based_sentiment_classification(positive_text, [])
            
            assert positive_result.sentiment_label == "positive"
            assert positive_result.sentiment_score > 0
            assert positive_result.confidence > 0.3
            
            # Negative text
            negative_text = "The company reported terrible losses and awful performance this quarter"
            negative_result = classifier._rule_based_sentiment_classification(negative_text, [])
            
            assert negative_result.sentiment_label == "negative"
            assert negative_result.sentiment_score < 0
            assert negative_result.confidence > 0.3
            
            # Neutral text
            neutral_text = "The company held a meeting to discuss quarterly planning"
            neutral_result = classifier._rule_based_sentiment_classification(neutral_text, [])
            
            assert neutral_result.sentiment_label == "neutral"
            assert abs(neutral_result.sentiment_score) < 0.3

    def test_sentiment_result_combination(self):
        """Test combining AI and rule-based sentiment results."""
        with patch('app.services.sentiment_classifier.YouComClient'):
            classifier = SentimentClassifier()
            
            ai_result = SentimentClassificationResult(
                sentiment_score=0.8,
                sentiment_label="positive",
                confidence=0.9,
                reasoning="AI analysis",
                metadata={"method": "ai"}
            )
            
            rule_result = SentimentClassificationResult(
                sentiment_score=0.6,
                sentiment_label="positive",
                confidence=0.7,
                reasoning="Rule analysis",
                metadata={"method": "rule"}
            )
            
            combined = classifier._combine_sentiment_results(ai_result, rule_result)
            
            assert combined.sentiment_label == "positive"
            assert 0.6 < combined.sentiment_score < 0.8  # Weighted average
            assert combined.confidence > 0.7
            assert "Combined analysis" in combined.reasoning


class TestSentimentProcessor:
    """Test sentiment processing pipeline."""

    @pytest.mark.asyncio
    async def test_sentiment_processor_initialization(self):
        """Test SentimentProcessor initialization."""
        processor = SentimentProcessor()
        # Should initialize without errors
        assert processor is not None

    @pytest.mark.asyncio
    async def test_queue_content_for_processing(self, db_session: AsyncSession):
        """Test queuing content for processing."""
        processor = SentimentProcessor()
        
        # Mock the database session
        with patch('app.services.sentiment_processor.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__.return_value = db_session
            
            success = await processor.queue_content_for_processing(
                content_id="test_content_123",
                content_text="Test content for sentiment analysis",
                content_type="news",
                source_url="https://example.com",
                priority=2
            )
            
            assert success is True
            
            # Verify item was added to queue
            result = await db_session.execute(
                select(SentimentProcessingQueue).where(
                    SentimentProcessingQueue.content_id == "test_content_123"
                )
            )
            queue_item = result.scalar_one_or_none()
            
            assert queue_item is not None
            assert queue_item.content_type == "news"
            assert queue_item.priority == 2
            assert queue_item.status == "pending"

    @pytest.mark.asyncio
    async def test_queue_duplicate_content(self, db_session: AsyncSession):
        """Test queuing duplicate content (should be rejected)."""
        processor = SentimentProcessor()
        
        # Add initial item
        queue_item = SentimentProcessingQueue(
            content_id="duplicate_test",
            content_type="news",
            content_text="Test content",
            status="pending"
        )
        db_session.add(queue_item)
        await db_session.commit()
        
        # Try to add duplicate
        with patch('app.services.sentiment_processor.AsyncSessionLocal') as mock_session:
            mock_session.return_value.__aenter__.return_value = db_session
            
            success = await processor.queue_content_for_processing(
                content_id="duplicate_test",
                content_text="Different content text",
                content_type="social"
            )
            
            assert success is False  # Should reject duplicate


class TestSentimentDataTypes:
    """Test sentiment analysis data types and structures."""

    def test_entity_recognition_result_dataclass(self):
        """Test EntityRecognitionResult dataclass."""
        result = EntityRecognitionResult(
            name="Microsoft",
            entity_type="company",
            confidence=0.85,
            context="Microsoft announced strong earnings",
            start_pos=0,
            end_pos=9,
            metadata={"method": "pattern", "pattern": "company_pattern"}
        )
        
        assert result.name == "Microsoft"
        assert result.entity_type == "company"
        assert result.confidence == 0.85
        assert result.start_pos == 0
        assert result.end_pos == 9
        assert result.metadata["method"] == "pattern"

    def test_sentiment_classification_result_dataclass(self):
        """Test SentimentClassificationResult dataclass."""
        result = SentimentClassificationResult(
            sentiment_score=0.75,
            sentiment_label="positive",
            confidence=0.9,
            reasoning="Strong positive indicators in earnings announcement",
            metadata={"method": "ai", "model": "custom_agent"}
        )
        
        assert result.sentiment_score == 0.75
        assert result.sentiment_label == "positive"
        assert result.confidence == 0.9
        assert "earnings announcement" in result.reasoning
        assert result.metadata["method"] == "ai"

    def test_sentiment_result_dataclass(self):
        """Test SentimentResult dataclass."""
        entities = [
            {"name": "Microsoft", "type": "company", "confidence": 0.9, "context": "earnings"},
            {"name": "Azure", "type": "product", "confidence": 0.8, "context": "cloud platform"}
        ]
        
        result = SentimentResult(
            sentiment_score=0.65,
            sentiment_label="positive",
            confidence=0.85,
            entities=entities,
            processing_time=1.25
        )
        
        assert result.sentiment_score == 0.65
        assert result.sentiment_label == "positive"
        assert result.confidence == 0.85
        assert len(result.entities) == 2
        assert result.processing_time == 1.25

    def test_entity_mention_dataclass(self):
        """Test EntityMention dataclass."""
        mention = EntityMention(
            name="Apple",
            entity_type="company",
            confidence=0.95,
            context="Apple reported record iPhone sales"
        )
        
        assert mention.name == "Apple"
        assert mention.entity_type == "company"
        assert mention.confidence == 0.95
        assert "iPhone sales" in mention.context


class TestSentimentAnalysisIntegration:
    """Test sentiment analysis system integration."""

    @pytest.mark.asyncio
    async def test_sentiment_analysis_workflow(self, db_session: AsyncSession):
        """Test complete sentiment analysis workflow."""
        # Create sample sentiment analysis records
        sentiments = []
        entities = ["Microsoft", "Apple", "Google"]
        
        for i, entity in enumerate(entities):
            sentiment = SentimentAnalysis(
                content_id=f"content_{i}",
                content_type="news",
                entity_name=entity,
                entity_type="company",
                sentiment_score=0.5 + (i * 0.2),  # 0.5, 0.7, 0.9
                sentiment_label="positive",
                confidence=0.8 + (i * 0.05),  # 0.8, 0.85, 0.9
                processing_timestamp=datetime.utcnow() - timedelta(hours=i),
                source_url=f"https://example.com/news/{i}",
                content_text=f"News about {entity} performance",
                analysis_metadata={"test": True}
            )
            sentiments.append(sentiment)
        
        db_session.add_all(sentiments)
        await db_session.commit()
        
        # Query back and verify
        result = await db_session.execute(
            select(SentimentAnalysis).where(
                SentimentAnalysis.entity_type == "company"
            ).order_by(SentimentAnalysis.sentiment_score.desc())
        )
        stored_sentiments = result.scalars().all()
        
        assert len(stored_sentiments) == 3
        assert stored_sentiments[0].entity_name == "Google"  # Highest sentiment score
        assert stored_sentiments[0].sentiment_score == 0.9

    @pytest.mark.asyncio
    async def test_sentiment_trend_aggregation(self, db_session: AsyncSession):
        """Test sentiment trend aggregation."""
        # Create trend data for different time periods
        trends = []
        entity_name = "Tesla"
        
        for i in range(7):  # 7 days of data
            trend = SentimentTrend(
                entity_name=entity_name,
                entity_type="company",
                timeframe="daily",
                period_start=datetime.utcnow() - timedelta(days=i+1),
                period_end=datetime.utcnow() - timedelta(days=i),
                average_sentiment=0.3 + (i * 0.1),  # Improving trend
                sentiment_volatility=0.2 - (i * 0.02),  # Decreasing volatility
                total_mentions=10 + i,
                positive_mentions=5 + i,
                negative_mentions=3,
                neutral_mentions=2,
                trend_direction="improving",
                trend_strength=0.6 + (i * 0.05)
            )
            trends.append(trend)
        
        db_session.add_all(trends)
        await db_session.commit()
        
        # Query trends for analysis
        result = await db_session.execute(
            select(SentimentTrend).where(
                SentimentTrend.entity_name == entity_name
            ).order_by(SentimentTrend.period_start.desc())
        )
        stored_trends = result.scalars().all()
        
        assert len(stored_trends) == 7
        assert all(t.trend_direction == "improving" for t in stored_trends)
        
        # Verify trend is actually improving (most recent should have highest sentiment)
        most_recent = stored_trends[0]
        oldest = stored_trends[-1]
        assert most_recent.average_sentiment > oldest.average_sentiment

    @pytest.mark.asyncio
    async def test_sentiment_alert_system(self, db_session: AsyncSession):
        """Test sentiment alert system."""
        # Create alerts with different severities
        alerts = []
        entities = ["Company A", "Company B", "Company C"]
        severities = ["low", "medium", "high"]
        
        for i, (entity, severity) in enumerate(zip(entities, severities)):
            alert = SentimentAlert(
                entity_name=entity,
                entity_type="company",
                alert_type="threshold",
                alert_severity=severity,
                current_sentiment=0.2 - (i * 0.1),  # Decreasing sentiment
                previous_sentiment=0.8,
                sentiment_change=-75.0 + (i * 10),  # Different change amounts
                threshold_value=0.5,
                confidence=0.9,
                triggered_at=datetime.utcnow() - timedelta(minutes=i*10),
                is_resolved=False,
                notification_sent=True,
                alert_metadata={"trigger_reason": f"Sentiment below threshold for {entity}"}
            )
            alerts.append(alert)
        
        db_session.add_all(alerts)
        await db_session.commit()
        
        # Query high severity alerts
        result = await db_session.execute(
            select(SentimentAlert).where(
                SentimentAlert.alert_severity == "high"
            )
        )
        high_alerts = result.scalars().all()
        
        assert len(high_alerts) == 1
        assert high_alerts[0].entity_name == "Company C"
        assert high_alerts[0].is_resolved is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])