"""
Unit tests for Decision Engine
"""

import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.decision_engine import DecisionEngine
from app.services.action_templates import ActionTemplateManager, ActionCategory, ActionPriority, BudgetImpact
from app.schemas.action_recommendation import (
    DecisionEngineRequest,
    DecisionEngineResponse,
    ActionRecommendationCreate
)
from app.models.action_recommendation import ActionRecommendation, ResourceEstimate
from app.models.impact_card import ImpactCard


class TestDecisionEngine:
    """Test cases for DecisionEngine class."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def decision_engine(self, mock_db_session):
        """Create DecisionEngine instance with mocked database."""
        return DecisionEngine(mock_db_session)
    
    @pytest.fixture
    def sample_decision_request(self):
        """Sample decision engine request."""
        return DecisionEngineRequest(
            risk_score=85,
            competitor_name="Test Competitor",
            impact_areas=[
                {
                    "area": "product",
                    "impact_score": 80,
                    "description": "Significant product impact"
                },
                {
                    "area": "pricing", 
                    "impact_score": 75,
                    "description": "Pricing pressure detected"
                }
            ],
            key_insights=[
                "Competitor launched new AI product",
                "Aggressive pricing strategy observed"
            ],
            confidence_score=85,
            context={
                "sources": [
                    {
                        "title": "Test News Article",
                        "url": "https://example.com/news",
                        "source": "TechCrunch"
                    }
                ]
            }
        )
    
    @pytest.mark.asyncio
    async def test_generate_recommendations_high_risk(self, decision_engine, sample_decision_request):
        """Test recommendation generation for high risk score."""
        response = await decision_engine.generate_recommendations(sample_decision_request)
        
        assert isinstance(response, DecisionEngineResponse)
        assert response.total_recommendations > 0
        assert response.confidence_level > 0
        assert response.processing_time_ms >= 0  # Processing time can be 0 for fast operations
        assert len(response.reasoning_summary) > 0
        
        # Check that recommendations are generated
        assert len(response.recommendations) <= 3  # Max 3 recommendations
        
        # Verify recommendation structure
        for rec in response.recommendations:
            assert rec.title
            assert rec.description
            assert rec.category in ["immediate", "short-term", "strategic"]
            assert rec.priority in ["high", "medium", "low"]
            assert rec.budget_impact in ["low", "medium", "high"]
            assert 0 <= rec.confidence_score <= 1
            assert 0 <= rec.impact_score <= 1
            assert 0 <= rec.effort_score <= 1
            assert 0 <= rec.overall_score <= 1
    
    @pytest.mark.asyncio
    async def test_generate_recommendations_critical_risk(self, decision_engine):
        """Test recommendation generation for critical risk score."""
        request = DecisionEngineRequest(
            risk_score=95,
            competitor_name="Critical Competitor",
            impact_areas=[],
            key_insights=["Critical threat detected"],
            confidence_score=90
        )
        
        response = await decision_engine.generate_recommendations(request)
        
        assert response.total_recommendations > 0
        assert response.confidence_level > 0.8  # High confidence for critical risk
        
        # Critical risk should generate immediate actions
        immediate_actions = [
            rec for rec in response.recommendations 
            if rec.category == "immediate"
        ]
        assert len(immediate_actions) > 0
    
    @pytest.mark.asyncio
    async def test_generate_recommendations_medium_risk(self, decision_engine):
        """Test recommendation generation for medium risk score."""
        request = DecisionEngineRequest(
            risk_score=75,
            competitor_name="Medium Competitor",
            impact_areas=[],
            key_insights=["Moderate threat detected"],
            confidence_score=70
        )
        
        response = await decision_engine.generate_recommendations(request)
        
        assert response.total_recommendations > 0
        
        # Medium risk should generate strategic actions
        strategic_actions = [
            rec for rec in response.recommendations 
            if rec.category == "strategic"
        ]
        assert len(strategic_actions) > 0
    
    @pytest.mark.asyncio
    async def test_generate_recommendations_low_risk(self, decision_engine):
        """Test recommendation generation for low risk score."""
        request = DecisionEngineRequest(
            risk_score=50,
            competitor_name="Low Competitor",
            impact_areas=[],
            key_insights=["Minor activity detected"],
            confidence_score=60
        )
        
        response = await decision_engine.generate_recommendations(request)
        
        # Low risk should generate fewer or no recommendations
        assert response.total_recommendations >= 0
    
    @pytest.mark.asyncio
    async def test_context_specific_recommendations(self, decision_engine):
        """Test generation of context-specific recommendations based on impact areas."""
        request = DecisionEngineRequest(
            risk_score=80,
            competitor_name="Context Competitor",
            impact_areas=[
                {
                    "area": "product",
                    "impact_score": 85,
                    "description": "Major product threat"
                },
                {
                    "area": "pricing",
                    "impact_score": 75,
                    "description": "Pricing competition"
                }
            ],
            key_insights=["Product launch detected"],
            confidence_score=80
        )
        
        response = await decision_engine.generate_recommendations(request)
        
        # Should generate recommendations for high-impact areas
        product_recommendations = [
            rec for rec in response.recommendations
            if "product" in rec.title.lower() or "product" in rec.description.lower()
        ]
        
        pricing_recommendations = [
            rec for rec in response.recommendations
            if "pricing" in rec.title.lower() or "pricing" in rec.description.lower()
        ]
        
        # At least one recommendation should be context-specific
        assert len(product_recommendations) > 0 or len(pricing_recommendations) > 0
    
    def test_categorize_risk(self, decision_engine):
        """Test risk score categorization."""
        assert decision_engine._categorize_risk(95) == "critical"
        assert decision_engine._categorize_risk(85) == "high"
        assert decision_engine._categorize_risk(75) == "medium"
        assert decision_engine._categorize_risk(65) == "low"
    
    def test_calculate_confidence_score(self, decision_engine, sample_decision_request):
        """Test confidence score calculation."""
        template = {
            "category": "immediate",
            "priority": "high"
        }
        
        confidence = decision_engine._calculate_confidence_score(template, sample_decision_request)
        
        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be reasonably confident for high risk
    
    def test_calculate_impact_score(self, decision_engine, sample_decision_request):
        """Test impact score calculation."""
        template = {
            "category": "immediate",
            "priority": "high"
        }
        
        impact = decision_engine._calculate_impact_score(template, sample_decision_request)
        
        assert 0 <= impact <= 1
        assert impact > 0.5  # Should have significant impact for high risk
    
    def test_calculate_effort_score(self, decision_engine):
        """Test effort score calculation."""
        template = {
            "estimated_hours": 40,
            "team_members_required": 2
        }
        
        effort = decision_engine._calculate_effort_score(template)
        
        assert 0 <= effort <= 1
    
    def test_calculate_overall_score(self, decision_engine):
        """Test overall score calculation."""
        confidence = 0.8
        impact = 0.9
        effort = 0.7
        
        overall = decision_engine._calculate_overall_score(confidence, impact, effort)
        
        assert 0 <= overall <= 1
        # Overall score should be weighted combination
        expected = (impact * 0.5) + (confidence * 0.3) + (effort * 0.2)
        assert abs(overall - expected) < 0.01
    
    def test_generate_evidence_links(self, decision_engine, sample_decision_request):
        """Test evidence link generation."""
        evidence_links = decision_engine._generate_evidence_links(sample_decision_request)
        
        assert isinstance(evidence_links, list)
        if evidence_links:
            for link in evidence_links:
                assert "title" in link
                assert "url" in link
                assert "source" in link
    
    def test_calculate_overall_confidence(self, decision_engine, sample_decision_request):
        """Test overall confidence calculation."""
        recommendations = [
            ActionRecommendationCreate(
                impact_card_id=1,
                title="Test Action",
                description="Test description",
                category="immediate",
                priority="high",
                timeline="1 week",
                budget_impact="medium",
                confidence_score=0.8,
                impact_score=0.7,
                effort_score=0.6,
                overall_score=0.7
            )
        ]
        
        confidence = decision_engine._calculate_overall_confidence(
            recommendations, sample_decision_request
        )
        
        assert 0 <= confidence <= 1
    
    def test_generate_reasoning_summary(self, decision_engine, sample_decision_request):
        """Test reasoning summary generation."""
        recommendations = [
            ActionRecommendationCreate(
                impact_card_id=1,
                title="Test Action",
                description="Test description",
                category="immediate",
                priority="high",
                timeline="1 week",
                budget_impact="medium",
                confidence_score=0.8,
                impact_score=0.7,
                effort_score=0.6,
                overall_score=0.7
            )
        ]
        
        summary = decision_engine._generate_reasoning_summary(
            recommendations, sample_decision_request, "high"
        )
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "high risk score" in summary.lower()
        assert str(sample_decision_request.risk_score) in summary
    
    @pytest.mark.asyncio
    async def test_save_recommendations(self, decision_engine, mock_db_session):
        """Test saving recommendations to database."""
        recommendations = [
            ActionRecommendationCreate(
                impact_card_id=1,
                title="Test Action",
                description="Test description",
                category="immediate",
                priority="high",
                timeline="1 week",
                budget_impact="medium",
                confidence_score=0.8,
                impact_score=0.7,
                effort_score=0.6,
                overall_score=0.7
            )
        ]
        
        # Mock database operations
        mock_db_session.add = Mock()
        mock_db_session.flush = AsyncMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        saved_recs = await decision_engine.save_recommendations(recommendations, 1)
        
        assert len(saved_recs) == len(recommendations)
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called_once()


class TestActionTemplateManager:
    """Test cases for ActionTemplateManager class."""
    
    @pytest.fixture
    def template_manager(self):
        """Create ActionTemplateManager instance."""
        return ActionTemplateManager()
    
    def test_get_templates_for_risk_score(self, template_manager):
        """Test getting templates for different risk scores."""
        # Critical risk
        critical_templates = template_manager.get_templates_for_risk_score(95)
        assert len(critical_templates) > 0
        assert all(template["id"].startswith("critical_") for template in critical_templates)
        
        # High risk
        high_templates = template_manager.get_templates_for_risk_score(85)
        assert len(high_templates) > 0
        assert all(template["id"].startswith("high_") for template in high_templates)
        
        # Medium risk
        medium_templates = template_manager.get_templates_for_risk_score(75)
        assert len(medium_templates) > 0
        assert all(template["id"].startswith("medium_") for template in medium_templates)
        
        # Low risk
        low_templates = template_manager.get_templates_for_risk_score(65)
        assert len(low_templates) == 0
    
    def test_get_impact_area_template(self, template_manager):
        """Test getting templates for specific impact areas."""
        # Product area
        product_template = template_manager.get_impact_area_template("product")
        assert product_template is not None
        assert "product" in product_template["title"].lower()
        
        # Pricing area
        pricing_template = template_manager.get_impact_area_template("pricing")
        assert pricing_template is not None
        assert "pricing" in pricing_template["title"].lower()
        
        # Unknown area
        unknown_template = template_manager.get_impact_area_template("unknown_area")
        assert unknown_template is None
    
    def test_estimate_timeline(self, template_manager):
        """Test timeline estimation."""
        # Immediate category
        immediate_timeline = template_manager.estimate_timeline(ActionCategory.IMMEDIATE)
        assert "days" in immediate_timeline or "weeks" in immediate_timeline
        
        # Strategic category
        strategic_timeline = template_manager.estimate_timeline(ActionCategory.STRATEGIC)
        assert "weeks" in strategic_timeline or "months" in strategic_timeline
        
        # With complexity factor
        complex_timeline = template_manager.estimate_timeline(
            ActionCategory.IMMEDIATE, complexity_factor=2.0
        )
        assert isinstance(complex_timeline, str)
    
    def test_estimate_resources(self, template_manager):
        """Test resource estimation."""
        resources = template_manager.estimate_resources(
            ActionCategory.SHORT_TERM,
            BudgetImpact.MEDIUM,
            complexity_factor=1.0
        )
        
        assert "estimated_hours" in resources
        assert "team_members_required" in resources
        assert "budget_impact" in resources
        assert resources["estimated_hours"] > 0
        assert resources["team_members_required"] > 0
        assert resources["budget_impact"] == BudgetImpact.MEDIUM
        
        # Test with complexity factor
        complex_resources = template_manager.estimate_resources(
            ActionCategory.SHORT_TERM,
            BudgetImpact.MEDIUM,
            complexity_factor=2.0
        )
        
        assert complex_resources["estimated_hours"] > resources["estimated_hours"]
        assert complex_resources["team_members_required"] >= resources["team_members_required"]
    
    def test_template_structure(self, template_manager):
        """Test that all templates have required structure."""
        for risk_level, templates in template_manager.templates.items():
            for template in templates:
                # Required fields
                assert "id" in template
                assert "title" in template
                assert "description" in template
                assert "category" in template
                assert "priority" in template
                assert "timeline" in template
                assert "budget_impact" in template
                assert "dependencies" in template
                assert "reasoning" in template
                
                # Valid enum values
                assert template["category"] in [cat.value for cat in ActionCategory]
                assert template["priority"] in [pri.value for pri in ActionPriority]
                assert template["budget_impact"] in [bi.value for bi in BudgetImpact]
                
                # Reasonable values
                assert template["estimated_hours"] > 0
                assert template["team_members_required"] > 0
                assert isinstance(template["dependencies"], list)
                assert isinstance(template["reasoning"], list)
    
    def test_impact_area_template_structure(self, template_manager):
        """Test that impact area templates have required structure."""
        for area, template in template_manager.impact_area_templates.items():
            # Required fields
            assert "title" in template
            assert "description" in template
            assert "category" in template
            assert "priority" in template
            assert "timeline" in template
            assert "budget_impact" in template
            assert "dependencies" in template
            assert "reasoning" in template
            
            # Template should contain placeholder for competitor name
            assert "{competitor_name}" in template["title"]
            assert "{competitor_name}" in template["description"]