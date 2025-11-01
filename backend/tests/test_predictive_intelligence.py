"""
Tests for Predictive Intelligence Engine
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.predictive_intelligence import CompetitorPattern, PredictedEvent, PatternEvent
from app.models.impact_card import ImpactCard
from app.services.predictive_intelligence import PredictiveIntelligenceEngine
from app.services.ml_prediction_service import MLPredictionService
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


@pytest.fixture
def sync_db_session():
    """Create a synchronous test database session."""
    from app.models.predictive_intelligence import CompetitorPattern, PredictedEvent, PatternEvent
    from app.models.impact_card import ImpactCard
    from app.models.watch import WatchItem
    from sqlalchemy import MetaData
    
    # Create sync engine and session
    sync_engine = create_engine("sqlite:///:memory:")
    
    # Create only the tables we need for testing
    metadata = MetaData()
    
    # Create tables manually to avoid UUID issues
    ImpactCard.__table__.create(sync_engine, checkfirst=True)
    WatchItem.__table__.create(sync_engine, checkfirst=True)
    CompetitorPattern.__table__.create(sync_engine, checkfirst=True)
    PredictedEvent.__table__.create(sync_engine, checkfirst=True)
    PatternEvent.__table__.create(sync_engine, checkfirst=True)
    
    SessionLocal = sessionmaker(bind=sync_engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_impact_cards():
    """Sample impact cards for pattern analysis testing."""
    base_date = datetime.utcnow() - timedelta(days=100)
    
    cards = []
    for i in range(5):
        card = ImpactCard(
            competitor_name="TestCorp",
            risk_score=70 + i * 5,
            risk_level="high",
            confidence_score=80 + i * 2,
            key_insights=[f"Product launch insight {i}", f"Market expansion insight {i}"],
            impact_areas=[{"area": "product", "impact_score": 75 + i * 3}],
            recommended_actions=[{
                "action": f"Monitor product launch {i}",
                "priority": "high",
                "timeline": "immediate"
            }],
            total_sources=10 + i * 2,
            created_at=base_date + timedelta(days=i * 20)
        )
        cards.append(card)
    
    return cards


@pytest.fixture
def sample_competitor_pattern():
    """Sample competitor pattern for testing."""
    return CompetitorPattern(
        competitor_name="TestCorp",
        pattern_type="product_launch",
        sequence=[
            {
                "date": (datetime.utcnow() - timedelta(days=60)).isoformat(),
                "risk_score": 75,
                "key_insights": ["Product development completed"],
                "impact_areas": ["product"]
            },
            {
                "date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "risk_score": 80,
                "key_insights": ["Marketing campaign started"],
                "impact_areas": ["product", "marketing"]
            }
        ],
        frequency=2,
        confidence=0.8,
        average_duration=30,
        typical_intervals=[30, 35],
        first_observed=datetime.utcnow() - timedelta(days=60),
        last_observed=datetime.utcnow() - timedelta(days=30),
        contributing_factors=["high_risk_events", "product_development"],
        success_indicators=["increasing_risk_trend"]
    )


@pytest.fixture
def sample_predicted_event():
    """Sample predicted event for testing."""
    return PredictedEvent(
        pattern_id=1,
        competitor_name="TestCorp",
        event_type="product_launch",
        description="TestCorp is likely to announce a new product or feature",
        probability=0.75,
        confidence=0.8,
        predicted_date=datetime.utcnow() + timedelta(days=15),
        timeframe="within 1 month",
        earliest_date=datetime.utcnow() + timedelta(days=8),
        latest_date=datetime.utcnow() + timedelta(days=22),
        reasoning=[
            "Pattern observed 2 times with 80% consistency",
            "Average interval between occurrences: 30 days",
            "Last occurrence: 30 days ago"
        ],
        trigger_events=["Development completion", "Market opportunity"],
        supporting_evidence=[{"event": "previous_launch", "date": "2024-01-01"}],
        expires_at=datetime.utcnow() + timedelta(days=90)
    )


class TestPredictiveIntelligenceEngine:
    """Test the main predictive intelligence engine."""

    @pytest.mark.asyncio
    async def test_engine_initialization(self, db_session: AsyncSession):
        """Test engine initialization."""
        engine = PredictiveIntelligenceEngine(db_session)
        
        assert engine.db == db_session
        assert engine.min_pattern_frequency == 2
        assert engine.pattern_confidence_threshold == 0.6
        assert engine.prediction_horizon_days == 90
        assert "product_launch" in engine.event_type_keywords
        assert "pricing_change" in engine.event_type_keywords

    def test_analyze_competitor_patterns_insufficient_data(self, sync_db_session):
        """Test pattern analysis with insufficient data."""
        engine = PredictiveIntelligenceEngine(sync_db_session)
        
        # Create only one impact card (below minimum)
        impact_card = ImpactCard(
            competitor_name="TestCorp",
            risk_score=75,
            risk_level="high",
            confidence_score=80
        )
        sync_db_session.add(impact_card)
        sync_db_session.commit()
        
        patterns = engine.analyze_competitor_patterns("TestCorp")
        assert len(patterns) == 0

    def test_analyze_competitor_patterns_success(self, sync_db_session, sample_impact_cards):
        """Test successful pattern analysis."""
        engine = PredictiveIntelligenceEngine(sync_db_session)
        
        # Add sample impact cards to database
        for card in sample_impact_cards:
            sync_db_session.add(card)
        sync_db_session.commit()
        
        patterns = engine.analyze_competitor_patterns("TestCorp")
        
        assert len(patterns) > 0
        pattern = patterns[0]
        assert pattern.competitor_name == "TestCorp"
        assert pattern.frequency >= 2
        assert pattern.confidence >= 0.0
        assert len(pattern.sequence) >= 2

    def test_classify_event_type(self, sync_db_session):
        """Test event type classification."""
        engine = PredictiveIntelligenceEngine(sync_db_session)
        
        # Test product launch classification
        impact_card = ImpactCard(
            competitor_name="TestCorp",
            risk_score=75,
            risk_level="high",
            confidence_score=80,
            key_insights=["Company announces new product launch", "Product release scheduled"],
            recommended_actions=[{
                "description": "Monitor the product launch announcement closely"
            }]
        )
        
        event_type = engine._classify_event_type(impact_card)
        assert event_type == "product_launch"
        
        # Test pricing change classification
        pricing_card = ImpactCard(
            competitor_name="TestCorp",
            risk_score=70,
            risk_level="high",
            confidence_score=75,
            key_insights=["Pricing strategy update", "New discount model"],
            recommended_actions=[{
                "description": "Analyze pricing changes and competitive response"
            }]
        )
        
        pricing_type = engine._classify_event_type(pricing_card)
        assert pricing_type == "pricing_change"

    def test_generate_predictions(self, sync_db_session, sample_competitor_pattern):
        """Test prediction generation."""
        engine = PredictiveIntelligenceEngine(sync_db_session)
        
        # Add pattern to database
        sync_db_session.add(sample_competitor_pattern)
        sync_db_session.commit()
        sync_db_session.refresh(sample_competitor_pattern)
        
        predictions = engine.generate_predictions("TestCorp")
        
        assert len(predictions) > 0
        prediction = predictions[0]
        assert prediction.competitor_name == "TestCorp"
        assert prediction.pattern_id == sample_competitor_pattern.id
        assert prediction.probability > 0.0
        assert prediction.confidence > 0.0
        assert prediction.predicted_date is not None
        assert len(prediction.reasoning) > 0

    def test_validate_prediction(self, sync_db_session, sample_predicted_event):
        """Test prediction validation."""
        engine = PredictiveIntelligenceEngine(sync_db_session)
        
        # Add predicted event to database
        sync_db_session.add(sample_predicted_event)
        sync_db_session.commit()
        sync_db_session.refresh(sample_predicted_event)
        
        # Validate the prediction
        success = engine.validate_prediction(
            sample_predicted_event.id,
            "Product was successfully launched as predicted",
            0.85
        )
        
        assert success is True
        
        # Check that prediction was updated
        sync_db_session.refresh(sample_predicted_event)
        assert sample_predicted_event.status == "validated"
        assert sample_predicted_event.accuracy_score == 0.85
        assert sample_predicted_event.actual_outcome == "Product was successfully launched as predicted"
        assert sample_predicted_event.validation_date is not None

    def test_get_active_predictions(self, sync_db_session, sample_predicted_event):
        """Test getting active predictions."""
        engine = PredictiveIntelligenceEngine(sync_db_session)
        
        # Add predicted event to database
        sync_db_session.add(sample_predicted_event)
        sync_db_session.commit()
        
        # Get active predictions
        predictions = engine.get_active_predictions("TestCorp")
        
        assert len(predictions) == 1
        assert predictions[0].competitor_name == "TestCorp"
        assert predictions[0].status == "pending"

    def test_get_pattern_accuracy_metrics(self, sync_db_session):
        """Test pattern accuracy metrics calculation."""
        engine = PredictiveIntelligenceEngine(sync_db_session)
        
        # Create validated predictions with different accuracy scores
        predictions = [
            PredictedEvent(
                pattern_id=1,
                competitor_name="TestCorp",
                event_type="product_launch",
                description="Test prediction 1",
                probability=0.8,
                confidence=0.7,
                timeframe="1 month",
                status="validated",
                accuracy_score=0.9
            ),
            PredictedEvent(
                pattern_id=1,
                competitor_name="TestCorp",
                event_type="pricing_change",
                description="Test prediction 2",
                probability=0.6,
                confidence=0.8,
                timeframe="2 weeks",
                status="validated",
                accuracy_score=0.4
            ),
            PredictedEvent(
                pattern_id=1,
                competitor_name="TestCorp",
                event_type="product_launch",
                description="Test prediction 3",
                probability=0.7,
                confidence=0.75,
                timeframe="1 month",
                status="invalidated",
                accuracy_score=0.2
            )
        ]
        
        for pred in predictions:
            sync_db_session.add(pred)
        sync_db_session.commit()
        
        metrics = engine.get_pattern_accuracy_metrics()
        
        assert metrics["total_predictions"] == 3
        assert metrics["accurate_predictions"] == 1  # Only one with accuracy > 0.5
        assert metrics["overall_accuracy"] == 1/3
        assert "product_launch" in metrics["type_metrics"]
        assert "pricing_change" in metrics["type_metrics"]


class TestMLPredictionService:
    """Test the ML prediction service."""

    def test_ml_service_initialization(self, sync_db_session):
        """Test ML service initialization."""
        service = MLPredictionService(sync_db_session)
        
        assert service.db == db_session
        assert service.min_training_samples == 20
        assert service.feature_window_days == 30
        assert service.prediction_confidence_threshold == 0.6

    def test_extract_prediction_features(self, sync_db_session, sample_competitor_pattern):
        """Test feature extraction for ML prediction."""
        service = MLPredictionService(sync_db_session)
        
        # Create a mock prediction object
        mock_prediction = type('obj', (object,), {
            'created_at': datetime.utcnow(),
            'pattern_id': 1
        })()
        
        features = service._extract_prediction_features(sample_competitor_pattern, mock_prediction)
        
        assert "days_since_last" in features
        assert "pattern_frequency" in features
        assert "pattern_confidence" in features
        assert "avg_risk_score" in features
        assert "risk_trend" in features
        assert "time_consistency" in features
        assert "impact_diversity" in features
        assert "seasonal_factor" in features
        
        # Check feature values are reasonable
        assert features["pattern_frequency"] == sample_competitor_pattern.frequency
        assert features["pattern_confidence"] == sample_competitor_pattern.confidence
        assert 0.0 <= features["seasonal_factor"] <= 1.0

    def test_calculate_time_consistency(self, sync_db_session):
        """Test time consistency calculation."""
        service = MLPredictionService(sync_db_session)
        
        # Create pattern with consistent intervals
        consistent_pattern = CompetitorPattern(
            competitor_name="TestCorp",
            pattern_type="product_launch",
            typical_intervals=[30, 32, 28, 31],  # Consistent ~30 day intervals
            confidence=0.8,
            frequency=4
        )
        
        consistency = service._calculate_time_consistency(consistent_pattern)
        assert consistency > 0.8  # Should be high consistency
        
        # Create pattern with inconsistent intervals
        inconsistent_pattern = CompetitorPattern(
            competitor_name="TestCorp",
            pattern_type="product_launch",
            typical_intervals=[10, 60, 15, 90],  # Very inconsistent intervals
            confidence=0.8,
            frequency=4
        )
        
        consistency = service._calculate_time_consistency(inconsistent_pattern)
        assert consistency < 0.5  # Should be low consistency

    def test_calculate_impact_diversity(self, sync_db_session):
        """Test impact diversity calculation."""
        service = MLPredictionService(sync_db_session)
        
        # Create pattern with diverse impacts
        diverse_pattern = CompetitorPattern(
            competitor_name="TestCorp",
            pattern_type="product_launch",
            sequence=[
                {"impact_areas": ["product", "marketing"]},
                {"impact_areas": ["product", "sales", "strategy"]},
                {"impact_areas": ["marketing", "brand"]}
            ]
        )
        
        diversity = service._calculate_impact_diversity(diverse_pattern)
        assert diversity > 0.5  # Should have good diversity
        
        # Create pattern with limited impacts
        limited_pattern = CompetitorPattern(
            competitor_name="TestCorp",
            pattern_type="product_launch",
            sequence=[
                {"impact_areas": ["product", "product"]},
                {"impact_areas": ["product"]},
                {"impact_areas": ["product", "product"]}
            ]
        )
        
        diversity = service._calculate_impact_diversity(limited_pattern)
        assert diversity <= 0.5  # Should have low diversity

    def test_enhance_prediction_no_models(self, sync_db_session, sample_competitor_pattern):
        """Test prediction enhancement when ML models are not loaded."""
        service = MLPredictionService(sync_db_session)
        
        base_prediction = {
            "probability": 0.7,
            "confidence": 0.8,
            "predicted_date": datetime.utcnow() + timedelta(days=30),
            "timeframe": "within 1 month"
        }
        
        # Should return original prediction when models not loaded
        enhanced = service.enhance_prediction(sample_competitor_pattern, base_prediction)
        assert enhanced == base_prediction

    def test_get_model_performance_metrics_no_models(self, sync_db_session):
        """Test getting performance metrics when models are not loaded."""
        service = MLPredictionService(sync_db_session)
        
        metrics = service.get_model_performance_metrics()
        assert metrics["status"] == "models_not_loaded"


class TestPredictiveIntelligenceModels:
    """Test the predictive intelligence database models."""

    def test_competitor_pattern_model(self, sync_db_session, sample_competitor_pattern):
        """Test CompetitorPattern model."""
        sync_db_session.add(sample_competitor_pattern)
        sync_db_session.commit()
        sync_db_session.refresh(sample_competitor_pattern)
        
        assert sample_competitor_pattern.id is not None
        assert sample_competitor_pattern.competitor_name == "TestCorp"
        assert sample_competitor_pattern.pattern_type == "product_launch"
        assert sample_competitor_pattern.frequency == 2
        assert sample_competitor_pattern.confidence == 0.8
        assert sample_competitor_pattern.is_active is True
        assert sample_competitor_pattern.created_at is not None

    def test_predicted_event_model(self, sync_db_session, sample_competitor_pattern, sample_predicted_event):
        """Test PredictedEvent model."""
        # First add the pattern
        sync_db_session.add(sample_competitor_pattern)
        sync_db_session.commit()
        sync_db_session.refresh(sample_competitor_pattern)
        
        # Update predicted event with correct pattern ID
        sample_predicted_event.pattern_id = sample_competitor_pattern.id
        
        sync_db_session.add(sample_predicted_event)
        sync_db_session.commit()
        sync_db_session.refresh(sample_predicted_event)
        
        assert sample_predicted_event.id is not None
        assert sample_predicted_event.pattern_id == sample_competitor_pattern.id
        assert sample_predicted_event.competitor_name == "TestCorp"
        assert sample_predicted_event.event_type == "product_launch"
        assert sample_predicted_event.probability == 0.75
        assert sample_predicted_event.confidence == 0.8
        assert sample_predicted_event.status == "pending"
        assert sample_predicted_event.created_at is not None

    def test_pattern_event_model(self, sync_db_session, sample_competitor_pattern, sample_impact_cards):
        """Test PatternEvent model."""
        # Add pattern and impact card
        sync_db_session.add(sample_competitor_pattern)
        sync_db_session.add(sample_impact_cards[0])
        sync_db_session.commit()
        sync_db_session.refresh(sample_competitor_pattern)
        sync_db_session.refresh(sample_impact_cards[0])
        
        # Create pattern event
        pattern_event = PatternEvent(
            pattern_id=sample_competitor_pattern.id,
            impact_card_id=sample_impact_cards[0].id,
            event_type="product_launch",
            description="Product launch event detected",
            event_date=datetime.utcnow(),
            risk_score=75,
            impact_areas=["product", "marketing"],
            key_metrics={"risk_increase": 10},
            sources=[{"url": "https://example.com", "title": "News Article"}],
            confidence=0.8
        )
        
        sync_db_session.add(pattern_event)
        sync_db_session.commit()
        sync_db_session.refresh(pattern_event)
        
        assert pattern_event.id is not None
        assert pattern_event.pattern_id == sample_competitor_pattern.id
        assert pattern_event.impact_card_id == sample_impact_cards[0].id
        assert pattern_event.event_type == "product_launch"
        assert pattern_event.risk_score == 75
        assert pattern_event.confidence == 0.8

    def test_model_relationships(self, sync_db_session, sample_competitor_pattern):
        """Test relationships between predictive intelligence models."""
        # Add pattern
        sync_db_session.add(sample_competitor_pattern)
        sync_db_session.commit()
        sync_db_session.refresh(sample_competitor_pattern)
        
        # Add predicted events
        for i in range(3):
            predicted_event = PredictedEvent(
                pattern_id=sample_competitor_pattern.id,
                competitor_name="TestCorp",
                event_type="product_launch",
                description=f"Prediction {i}",
                probability=0.7 + i * 0.1,
                confidence=0.8,
                timeframe="1 month",
                expires_at=datetime.utcnow() + timedelta(days=90)
            )
            sync_db_session.add(predicted_event)
        
        sync_db_session.commit()
        
        # Test relationship
        related_predictions = sync_db_session.query(PredictedEvent).filter(
            PredictedEvent.pattern_id == sample_competitor_pattern.id
        ).all()
        
        assert len(related_predictions) == 3
        for pred in related_predictions:
            assert pred.pattern_id == sample_competitor_pattern.id


class TestPredictiveIntelligenceIntegration:
    """Test integration of predictive intelligence with existing systems."""

    def test_pattern_analysis_with_real_impact_cards(self, sync_db_session):
        """Test pattern analysis using realistic impact card data."""
        engine = PredictiveIntelligenceEngine(sync_db_session)
        
        # Create realistic impact cards with product launch pattern
        base_date = datetime.utcnow() - timedelta(days=120)
        
        # Simulate a pattern: product announcements every ~45 days
        launch_dates = [0, 45, 92]  # Days from base_date
        
        for i, days_offset in enumerate(launch_dates):
            impact_card = ImpactCard(
                competitor_name="RealCorp",
                risk_score=75 + i * 5,
                risk_level="high",
                confidence_score=80 + i * 2,
                key_insights=[
                    f"RealCorp announces new product version {i+1}",
                    f"Product launch scheduled for Q{i+1}",
                    "Significant market impact expected"
                ],
                impact_areas=[{
                    "area": "product",
                    "impact_score": 80 + i * 3,
                    "description": f"Product launch impact {i+1}"
                }],
                recommended_actions=[{
                    "action": f"Monitor product launch {i+1}",
                    "priority": "high",
                    "timeline": "immediate",
                    "owner": "Product Team",
                    "okr_goal": "Competitive Response",
                    "impact_score": 85,
                    "effort_score": 40,
                    "score": 2.1,
                    "evidence": [],
                    "index": 0
                }],
                total_sources=15 + i * 3,
                created_at=base_date + timedelta(days=days_offset)
            )
            sync_db_session.add(impact_card)
        
        sync_db_session.commit()
        
        # Analyze patterns
        patterns = engine.analyze_competitor_patterns("RealCorp")
        
        assert len(patterns) > 0
        product_patterns = [p for p in patterns if p.pattern_type == "product_launch"]
        assert len(product_patterns) > 0
        
        pattern = product_patterns[0]
        assert pattern.frequency == 3
        assert pattern.confidence > 0.5
        assert pattern.average_duration > 0
        
        # Generate predictions based on the pattern
        predictions = engine.generate_predictions("RealCorp")
        assert len(predictions) > 0
        
        prediction = predictions[0]
        assert prediction.event_type == "product_launch"
        assert prediction.probability > 0.0
        assert prediction.predicted_date is not None

    def test_prediction_accuracy_tracking(self, sync_db_session):
        """Test end-to-end prediction accuracy tracking."""
        engine = PredictiveIntelligenceEngine(sync_db_session)
        
        # Create a pattern
        pattern = CompetitorPattern(
            competitor_name="AccuracyCorp",
            pattern_type="product_launch",
            sequence=[{"date": "2024-01-01", "risk_score": 75}],
            frequency=2,
            confidence=0.8,
            average_duration=30,
            first_observed=datetime.utcnow() - timedelta(days=60),
            last_observed=datetime.utcnow() - timedelta(days=30)
        )
        sync_db_session.add(pattern)
        sync_db_session.commit()
        sync_db_session.refresh(pattern)
        
        # Generate prediction
        predictions = engine.generate_predictions("AccuracyCorp")
        assert len(predictions) > 0
        
        prediction = predictions[0]
        
        # Simulate prediction validation
        success = engine.validate_prediction(
            prediction.id,
            "Product was launched successfully on predicted date",
            0.9
        )
        assert success is True
        
        # Check accuracy metrics
        metrics = engine.get_pattern_accuracy_metrics()
        assert metrics["total_predictions"] >= 1
        assert metrics["overall_accuracy"] > 0.0