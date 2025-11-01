"""
Tests for the Explainability Engine
"""

import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.explainability_engine import ExplainabilityEngine
from app.models.explainability import ReasoningStep, SourceCredibilityAnalysis, UncertaintyDetection
from app.models.impact_card import ImpactCard


@pytest.fixture
def sample_analysis_data():
    """Sample analysis data for testing"""
    return {
        "risk_score": 75,
        "risk_level": "high",
        "confidence_score": 80,
        "impact_areas": [
            {
                "area": "Product Launch",
                "impact_score": 85,
                "description": "New AI-powered feature directly competes with our core offering"
            },
            {
                "area": "Market Share",
                "impact_score": 70,
                "description": "Potential market share impact in key segments"
            }
        ],
        "key_insights": [
            "Competitor launched advanced AI feature",
            "Direct competition with our flagship product"
        ],
        "reasoning": "High risk due to direct product competition and strong market positioning"
    }


@pytest.fixture
def sample_source_data():
    """Sample source data for testing"""
    return {
        "source_quality": {
            "score": 0.75,
            "total": 5,
            "tiers": {"tier1": 2, "tier2": 2, "tier3": 1},
            "top_sources": [
                {
                    "title": "TechCrunch: Competitor Launches AI Feature",
                    "url": "https://techcrunch.com/competitor-launch",
                    "tier": "tier2",
                    "weight": 0.75,
                    "type": "news"
                },
                {
                    "title": "Reuters: Market Analysis",
                    "url": "https://reuters.com/market-analysis",
                    "tier": "tier1",
                    "weight": 0.95,
                    "type": "news"
                },
                {
                    "title": "Blog Post: Opinion on Launch",
                    "url": "https://blog.example.com/opinion",
                    "tier": "tier3",
                    "weight": 0.35,
                    "type": "search"
                }
            ]
        },
        "total_sources": 5,
        "source_breakdown": {
            "news_articles": 3,
            "search_results": 2,
            "research_citations": 0
        }
    }


async def create_test_impact_card(db_session: AsyncSession):
    """Helper function to create a test impact card"""
    impact_card = ImpactCard(
        competitor_name="Test Competitor",
        risk_score=75,
        risk_level="high",
        confidence_score=85,
        impact_areas=[],
        key_insights=[],
        recommended_actions=[],
        total_sources=0,
        source_breakdown={},
        api_usage={},
        raw_data={}
    )
    db_session.add(impact_card)
    await db_session.commit()
    await db_session.refresh(impact_card)
    return impact_card


class TestExplainabilityEngine:
    """Test cases for ExplainabilityEngine"""

    @pytest.mark.asyncio
    async def test_initialization(self, db_session: AsyncSession):
        """Test ExplainabilityEngine initialization"""
        engine = ExplainabilityEngine(db_session)
        
        assert engine.db == db_session
        assert "tier1" in engine.tier_domains
        assert "critical" in engine.confidence_thresholds
        assert "product_impact" in engine.default_factor_weights

    @pytest.mark.asyncio
    async def test_generate_reasoning_chain(
        self, 
        db_session: AsyncSession, 
        sample_analysis_data,
        sample_source_data
    ):
        """Test reasoning chain generation"""
        impact_card = await create_test_impact_card(db_session)
        engine = ExplainabilityEngine(db_session)
        
        reasoning_steps = await engine.generate_reasoning_chain(
            impact_card.id,
            sample_analysis_data,
            sample_source_data
        )
        
        # Verify reasoning steps were created
        assert len(reasoning_steps) == 4  # source_assessment, 2 impact_analysis, risk_calculation, confidence_assessment
        
        # Verify step order
        step_orders = [step.step_order for step in reasoning_steps]
        assert step_orders == [1, 2, 3, 4]
        
        # Verify step types
        step_types = [step.step_type for step in reasoning_steps]
        expected_types = ["source_assessment", "impact_analysis", "impact_analysis", "risk_calculation"]
        assert step_types[:4] == expected_types
        
        # Verify database persistence
        db_steps = await db_session.execute(
            select(ReasoningStep).where(ReasoningStep.impact_card_id == impact_card.id)
        )
        db_steps_list = db_steps.scalars().all()
        assert len(db_steps_list) == len(reasoning_steps)

    @pytest.mark.asyncio
    async def test_source_assessment_step(
        self, 
        db_session: AsyncSession, 
        impact_card: ImpactCard,
        sample_source_data
    ):
        """Test source assessment step creation"""
        engine = ExplainabilityEngine(db_session)
        
        step = await engine._create_source_assessment_step(
            impact_card.id, 1, sample_source_data
        )
        
        assert step.step_type == "source_assessment"
        assert step.step_name == "Source Quality Assessment"
        assert step.factor_name == "Source Credibility"
        assert 0 <= step.factor_weight <= 0.3  # Max 30% weight for sources
        assert step.confidence_level == sample_source_data["source_quality"]["score"]
        assert len(step.evidence_sources) <= 3  # Top 3 sources
        
        # Verify reasoning text contains key information
        assert "5 sources" in step.reasoning_text
        assert "tier-1" in step.reasoning_text
        assert "tier-2" in step.reasoning_text

    @pytest.mark.asyncio
    async def test_impact_area_step(
        self, 
        db_session: AsyncSession, 
        impact_card: ImpactCard,
        sample_source_data
    ):
        """Test impact area step creation"""
        engine = ExplainabilityEngine(db_session)
        
        impact_area = {
            "area": "Product Launch",
            "impact_score": 85,
            "description": "New AI-powered feature directly competes with our core offering"
        }
        
        step = await engine._create_impact_area_step(
            impact_card.id, 2, impact_area, sample_source_data
        )
        
        assert step.step_type == "impact_analysis"
        assert step.step_name == "Impact Analysis: Product Launch"
        assert step.factor_name == "Product Launch"
        assert step.factor_weight > 0
        assert step.factor_contribution > 0
        assert "Product Launch" in step.reasoning_text
        assert "85/100" in step.reasoning_text

    @pytest.mark.asyncio
    async def test_risk_calculation_step(
        self, 
        db_session: AsyncSession, 
        impact_card: ImpactCard,
        sample_analysis_data
    ):
        """Test risk calculation step creation"""
        engine = ExplainabilityEngine(db_session)
        
        # Create mock previous steps
        previous_steps = [
            Mock(factor_contribution=20.0, confidence_level=0.8),
            Mock(factor_contribution=25.0, confidence_level=0.7),
        ]
        
        step = await engine._create_risk_calculation_step(
            impact_card.id, 3, sample_analysis_data, previous_steps
        )
        
        assert step.step_type == "risk_calculation"
        assert step.step_name == "Final Risk Score Calculation"
        assert step.factor_name == "Overall Risk Assessment"
        assert step.factor_weight == 1.0
        assert step.factor_contribution == sample_analysis_data["risk_score"]
        assert "75/100" in step.reasoning_text
        assert "high risk" in step.reasoning_text

    @pytest.mark.asyncio
    async def test_analyze_source_quality(
        self, 
        db_session: AsyncSession, 
        impact_card: ImpactCard,
        sample_source_data
    ):
        """Test source quality analysis"""
        engine = ExplainabilityEngine(db_session)
        
        analyses = await engine.analyze_source_quality(
            impact_card.id,
            sample_source_data
        )
        
        # Verify analyses were created
        assert len(analyses) == 3  # Number of top sources
        
        # Verify analysis properties
        for analysis in analyses:
            assert analysis.impact_card_id == impact_card.id
            assert analysis.credibility_score >= 0.0
            assert analysis.credibility_score <= 1.0
            assert analysis.tier_level in ["tier1", "tier2", "tier3"]
            assert analysis.validation_method is not None
        
        # Verify database persistence
        db_analyses = await db_session.execute(
            select(SourceCredibilityAnalysis).where(
                SourceCredibilityAnalysis.impact_card_id == impact_card.id
            )
        )
        db_analyses_list = db_analyses.scalars().all()
        assert len(db_analyses_list) == len(analyses)

    @pytest.mark.asyncio
    async def test_individual_source_analysis(
        self, 
        db_session: AsyncSession, 
        impact_card: ImpactCard
    ):
        """Test individual source analysis"""
        engine = ExplainabilityEngine(db_session)
        
        source = {
            "title": "TechCrunch: Competitor Launches AI Feature",
            "url": "https://techcrunch.com/competitor-launch",
            "tier": "tier2",
            "weight": 0.75,
            "type": "news"
        }
        
        analysis = await engine._analyze_individual_source(impact_card.id, source)
        
        assert analysis.impact_card_id == impact_card.id
        assert analysis.source_url == source["url"]
        assert analysis.source_title == source["title"]
        assert analysis.source_type == source["type"]
        assert analysis.tier_level == source["tier"]
        assert 0.0 <= analysis.credibility_score <= 1.0
        assert 0.0 <= analysis.authority_score <= 1.0
        assert 0.0 <= analysis.recency_score <= 1.0
        assert 0.0 <= analysis.relevance_score <= 1.0

    @pytest.mark.asyncio
    async def test_authority_score_calculation(self, db_session: AsyncSession):
        """Test authority score calculation"""
        engine = ExplainabilityEngine(db_session)
        
        # Test tier1 domain
        score1 = engine._calculate_authority_score("reuters.com", "tier1")
        assert score1 >= 0.9
        
        # Test tier2 domain
        score2 = engine._calculate_authority_score("techcrunch.com", "tier2")
        assert 0.6 <= score2 < 0.9
        
        # Test tier3 domain
        score3 = engine._calculate_authority_score("unknown.com", "tier3")
        assert score3 < 0.6

    @pytest.mark.asyncio
    async def test_detect_uncertainty(
        self, 
        db_session: AsyncSession, 
        impact_card: ImpactCard,
        sample_analysis_data
    ):
        """Test uncertainty detection"""
        engine = ExplainabilityEngine(db_session)
        
        # Create mock reasoning steps with varying confidence
        reasoning_steps = [
            Mock(confidence_level=0.4, step_type="impact_analysis", 
                 factor_contribution=25.0, factor_name="High Impact Factor",
                 evidence_sources=[]),  # Low confidence, high impact, low evidence
            Mock(confidence_level=0.8, step_type="source_assessment", 
                 factor_contribution=15.0, factor_name="Source Quality",
                 evidence_sources=[{"url": "test"}]),
        ]
        
        # Create mock source analyses with conflicts
        source_analyses = [
            Mock(conflict_severity="major", conflicts_with=[1]),
            Mock(conflict_severity="none", conflicts_with=[]),
        ]
        
        detections = await engine.detect_uncertainty(
            impact_card.id,
            sample_analysis_data,
            reasoning_steps,
            source_analyses
        )
        
        # Verify detections were created
        assert len(detections) > 0
        
        # Check for expected uncertainty types
        uncertainty_types = [d.uncertainty_type for d in detections]
        assert "low_confidence" in uncertainty_types or "medium_confidence" in uncertainty_types
        
        # Verify database persistence
        db_detections = await db_session.execute(
            select(UncertaintyDetection).where(
                UncertaintyDetection.impact_card_id == impact_card.id
            )
        )
        db_detections_list = db_detections.scalars().all()
        assert len(db_detections_list) == len(detections)

    @pytest.mark.asyncio
    async def test_uncertainty_detection_thresholds(
        self, 
        db_session: AsyncSession, 
        impact_card: ImpactCard,
        sample_analysis_data
    ):
        """Test uncertainty detection with different confidence thresholds"""
        engine = ExplainabilityEngine(db_session)
        
        # Test critical threshold
        critical_steps = [Mock(confidence_level=0.2)]  # Below critical threshold
        critical_detections = await engine.detect_uncertainty(
            impact_card.id, sample_analysis_data, critical_steps, []
        )
        
        critical_detection = next(
            (d for d in critical_detections if d.uncertainty_level == "critical"), None
        )
        assert critical_detection is not None
        assert critical_detection.human_validation_required is True
        assert critical_detection.validation_priority == "urgent"
        
        # Test high threshold
        high_steps = [Mock(confidence_level=0.4)]  # Below high threshold
        high_detections = await engine.detect_uncertainty(
            impact_card.id, sample_analysis_data, high_steps, []
        )
        
        high_detection = next(
            (d for d in high_detections if d.uncertainty_level == "high"), None
        )
        assert high_detection is not None
        assert high_detection.human_validation_required is True

    @pytest.mark.asyncio
    async def test_build_enhanced_explainability(
        self, 
        db_session: AsyncSession, 
        impact_card: ImpactCard,
        sample_analysis_data,
        sample_source_data
    ):
        """Test building complete enhanced explainability"""
        engine = ExplainabilityEngine(db_session)
        
        # First generate all components
        reasoning_steps = await engine.generate_reasoning_chain(
            impact_card.id, sample_analysis_data, sample_source_data
        )
        source_analyses = await engine.analyze_source_quality(
            impact_card.id, sample_source_data
        )
        uncertainty_detections = await engine.detect_uncertainty(
            impact_card.id, sample_analysis_data, reasoning_steps, source_analyses
        )
        
        # Build enhanced explainability
        enhanced = await engine.build_enhanced_explainability(impact_card.id)
        
        assert len(enhanced.reasoning_chain) == len(reasoning_steps)
        assert len(enhanced.source_analyses) == len(source_analyses)
        assert len(enhanced.uncertainty_detections) == len(uncertainty_detections)
        assert 0.0 <= enhanced.overall_confidence <= 1.0
        assert 0.0 <= enhanced.source_quality_score <= 1.0
        assert enhanced.uncertainty_level in ["low", "medium", "high", "critical"]
        assert isinstance(enhanced.human_validation_recommended, bool)

    @pytest.mark.asyncio
    async def test_create_visualization_data(
        self, 
        db_session: AsyncSession, 
        impact_card: ImpactCard,
        sample_analysis_data,
        sample_source_data
    ):
        """Test creating visualization data"""
        engine = ExplainabilityEngine(db_session)
        
        # Generate components first
        await engine.generate_reasoning_chain(
            impact_card.id, sample_analysis_data, sample_source_data
        )
        await engine.analyze_source_quality(impact_card.id, sample_source_data)
        
        # Create visualization data
        viz_data = await engine.create_visualization_data(impact_card.id)
        
        assert isinstance(viz_data.factor_weights, dict)
        assert isinstance(viz_data.contribution_breakdown, dict)
        assert isinstance(viz_data.source_quality_breakdown, dict)
        assert isinstance(viz_data.uncertainty_summary, dict)
        assert isinstance(viz_data.confidence_intervals, dict)
        
        # Verify structure
        assert "tier1" in viz_data.source_quality_breakdown
        assert "tier2" in viz_data.source_quality_breakdown
        assert "tier3" in viz_data.source_quality_breakdown

    @pytest.mark.asyncio
    async def test_source_conflict_detection(self, db_session: AsyncSession):
        """Test source conflict detection logic"""
        engine = ExplainabilityEngine(db_session)
        
        # Create mock analyses with potential conflicts
        analysis1 = Mock(
            source_url="https://example.com/article1",
            credibility_score=0.9,
            tier_level="tier1",
            conflicts_with=[],
            conflict_severity="none"
        )
        
        analysis2 = Mock(
            source_url="https://example.com/article2", 
            credibility_score=0.3,  # Large credibility difference
            tier_level="tier3",
            conflicts_with=[],
            conflict_severity="none"
        )
        
        analyses = [analysis1, analysis2]
        
        # Test conflict detection
        await engine._detect_source_conflicts(analyses)
        
        # Verify conflicts were detected due to credibility difference
        assert len(analysis1.conflicts_with) > 0 or len(analysis2.conflicts_with) > 0

    @pytest.mark.asyncio
    async def test_relevance_score_calculation(self, db_session: AsyncSession):
        """Test relevance score calculation"""
        engine = ExplainabilityEngine(db_session)
        
        # Test high relevance source
        high_relevance_source = {
            "title": "Product Launch Revenue Growth Market Competition Strategy"
        }
        high_score = engine._calculate_relevance_score(high_relevance_source)
        assert high_score > 0.5
        
        # Test low relevance source
        low_relevance_source = {
            "title": "Unrelated Topic About Weather"
        }
        low_score = engine._calculate_relevance_score(low_relevance_source)
        assert low_score <= 0.5

    @pytest.mark.asyncio
    async def test_uncertainty_creation_helper(
        self, 
        db_session: AsyncSession, 
        impact_card: ImpactCard
    ):
        """Test uncertainty detection creation helper"""
        engine = ExplainabilityEngine(db_session)
        
        detection = await engine._create_uncertainty_detection(
            impact_card.id,
            "test_uncertainty",
            "high",
            0.5,
            ["component1", "component2"],
            "Test uncertainty description",
            True,
            ["action1", "action2"],
            "high"
        )
        
        assert detection.impact_card_id == impact_card.id
        assert detection.uncertainty_type == "test_uncertainty"
        assert detection.uncertainty_level == "high"
        assert detection.confidence_threshold == 0.5
        assert detection.affected_components == ["component1", "component2"]
        assert detection.uncertainty_description == "Test uncertainty description"
        assert detection.human_validation_required is True
        assert detection.recommended_actions == ["action1", "action2"]
        assert detection.validation_priority == "high"
        assert detection.is_resolved is False

    @pytest.mark.asyncio
    async def test_source_relevance_check(self, db_session: AsyncSession):
        """Test source relevance checking"""
        engine = ExplainabilityEngine(db_session)
        
        # Test relevant source
        relevant_source = {
            "title": "Product Launch Analysis and Market Impact"
        }
        assert engine._is_source_relevant_to_area(relevant_source, "Product Launch") is True
        
        # Test irrelevant source
        irrelevant_source = {
            "title": "Weather Report for Tomorrow"
        }
        assert engine._is_source_relevant_to_area(irrelevant_source, "Product Launch") is False

    @pytest.mark.asyncio
    async def test_edge_cases(
        self, 
        db_session: AsyncSession, 
        impact_card: ImpactCard
    ):
        """Test edge cases and error handling"""
        engine = ExplainabilityEngine(db_session)
        
        # Test with empty data
        empty_analysis = {
            "risk_score": 0,
            "risk_level": "low",
            "confidence_score": 0,
            "impact_areas": [],
            "key_insights": [],
            "reasoning": ""
        }
        
        empty_source = {
            "source_quality": {"score": 0.0, "total": 0, "tiers": {}, "top_sources": []},
            "total_sources": 0,
            "source_breakdown": {}
        }
        
        # Should handle empty data gracefully
        reasoning_steps = await engine.generate_reasoning_chain(
            impact_card.id, empty_analysis, empty_source
        )
        
        # Should still create basic steps
        assert len(reasoning_steps) >= 2  # At least source assessment and risk calculation
        
        # Test with malformed source data
        malformed_source = {
            "source_quality": {
                "score": 0.5,
                "total": 1,
                "tiers": {"tier1": 1},
                "top_sources": [
                    {
                        "title": None,  # Missing title
                        "url": "",      # Empty URL
                        "tier": "invalid_tier",  # Invalid tier
                        "type": "unknown"
                    }
                ]
            }
        }
        
        # Should handle malformed data without crashing
        analyses = await engine.analyze_source_quality(impact_card.id, malformed_source)
        assert len(analyses) >= 0  # Should not crash