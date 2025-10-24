"""
Tests for Pydantic schemas
"""

import pytest
from pydantic import ValidationError
from app.schemas.watch import WatchItemCreate, WatchItemUpdate, WatchItem
from app.schemas.impact_card import ImpactCardGenerate, ImpactCardCreate, ImpactArea, RecommendedAction
from app.schemas.company_research import CompanyResearchRequest, CompanyResearchCreate

class TestWatchSchemas:
    """Test watchlist-related schemas."""

    def test_watch_item_create_valid(self):
        """Test valid WatchItemCreate schema."""
        data = {
            "competitor_name": "Test Competitor",
            "keywords": ["AI", "ML", "API"],
            "description": "A test competitor",
            "check_frequency": 300,
            "risk_threshold": 80
        }
        
        schema = WatchItemCreate(**data)
        assert schema.competitor_name == "Test Competitor"
        assert schema.keywords == ["AI", "ML", "API"]
        assert schema.check_frequency == 300
        assert schema.risk_threshold == 80

    def test_watch_item_create_minimal(self):
        """Test WatchItemCreate with minimal required fields."""
        data = {"competitor_name": "Test Competitor"}
        
        schema = WatchItemCreate(**data)
        assert schema.competitor_name == "Test Competitor"
        assert schema.keywords == []
        assert schema.check_frequency == 120
        assert schema.risk_threshold == 70

    def test_watch_item_create_invalid_name(self):
        """Test WatchItemCreate with invalid competitor name."""
        with pytest.raises(ValidationError) as exc_info:
            WatchItemCreate(competitor_name="")
        
        errors = exc_info.value.errors()
        assert any("at least 1 character" in str(error) for error in errors)

    def test_watch_item_create_invalid_frequency(self):
        """Test WatchItemCreate with invalid check frequency."""
        with pytest.raises(ValidationError) as exc_info:
            WatchItemCreate(competitor_name="Test", check_frequency=30)
        
        errors = exc_info.value.errors()
        assert any("greater than or equal to 60" in str(error) for error in errors)

    def test_watch_item_create_invalid_threshold(self):
        """Test WatchItemCreate with invalid risk threshold."""
        with pytest.raises(ValidationError) as exc_info:
            WatchItemCreate(competitor_name="Test", risk_threshold=150)
        
        errors = exc_info.value.errors()
        assert any("less than or equal to 100" in str(error) for error in errors)

    def test_watch_item_update_partial(self):
        """Test WatchItemUpdate with partial data."""
        data = {"description": "Updated description"}
        
        schema = WatchItemUpdate(**data)
        assert schema.description == "Updated description"
        assert schema.competitor_name is None
        assert schema.keywords is None

class TestImpactCardSchemas:
    """Test Impact Card-related schemas."""

    def test_impact_area_valid(self):
        """Test valid ImpactArea schema."""
        data = {
            "area": "product",
            "impact_score": 85,
            "description": "Significant product impact"
        }
        
        schema = ImpactArea(**data)
        assert schema.area == "product"
        assert schema.impact_score == 85
        assert schema.description == "Significant product impact"

    def test_impact_area_invalid_score(self):
        """Test ImpactArea with invalid score."""
        with pytest.raises(ValidationError) as exc_info:
            ImpactArea(area="product", impact_score=150, description="Test")
        
        errors = exc_info.value.errors()
        assert any("less than or equal to 100" in str(error) for error in errors)

    def test_recommended_action_valid(self):
        """Test valid RecommendedAction schema."""
        data = {
            "action": "Monitor competitor closely",
            "priority": "high",
            "timeline": "immediate"
        }
        
        schema = RecommendedAction(**data)
        assert schema.action == "Monitor competitor closely"
        assert schema.priority == "high"
        assert schema.timeline == "immediate"

    def test_recommended_action_invalid_priority(self):
        """Test RecommendedAction with invalid priority."""
        with pytest.raises(ValidationError) as exc_info:
            RecommendedAction(
                action="Test action",
                priority="urgent",  # Invalid priority
                timeline="immediate"
            )
        
        errors = exc_info.value.errors()
        assert any("string does not match expected pattern" in str(error) for error in errors)

    def test_recommended_action_invalid_timeline(self):
        """Test RecommendedAction with invalid timeline."""
        with pytest.raises(ValidationError) as exc_info:
            RecommendedAction(
                action="Test action",
                priority="high",
                timeline="asap"  # Invalid timeline
            )
        
        errors = exc_info.value.errors()
        assert any("string does not match expected pattern" in str(error) for error in errors)

    def test_impact_card_generate_valid(self):
        """Test valid ImpactCardGenerate schema."""
        data = {
            "competitor_name": "Test Competitor",
            "keywords": ["AI", "ML"]
        }
        
        schema = ImpactCardGenerate(**data)
        assert schema.competitor_name == "Test Competitor"
        assert schema.keywords == ["AI", "ML"]

    def test_impact_card_generate_minimal(self):
        """Test ImpactCardGenerate with minimal data."""
        data = {"competitor_name": "Test Competitor"}
        
        schema = ImpactCardGenerate(**data)
        assert schema.competitor_name == "Test Competitor"
        assert schema.keywords == []

    def test_impact_card_create_valid(self):
        """Test valid ImpactCardCreate schema."""
        data = {
            "watch_item_id": 1,
            "competitor_name": "Test Competitor",
            "risk_score": 75,
            "risk_level": "high",
            "confidence_score": 85,
            "impact_areas": [
                {
                    "area": "product",
                    "impact_score": 80,
                    "description": "Product impact"
                }
            ],
            "key_insights": ["Insight 1", "Insight 2"],
            "recommended_actions": [
                {
                    "action": "Monitor closely",
                    "priority": "high",
                    "timeline": "immediate"
                }
            ],
            "total_sources": 25,
            "source_breakdown": {
                "news_articles": 10,
                "search_results": 8,
                "research_citations": 7
            },
            "api_usage": {
                "news_calls": 2,
                "search_calls": 2,
                "chat_calls": 1,
                "ari_calls": 1,
                "total_calls": 6
            }
        }
        
        schema = ImpactCardCreate(**data)
        assert schema.watch_item_id == 1
        assert schema.competitor_name == "Test Competitor"
        assert schema.risk_score == 75
        assert schema.risk_level == "high"
        assert len(schema.impact_areas) == 1
        assert len(schema.key_insights) == 2
        assert len(schema.recommended_actions) == 1

    def test_impact_card_create_invalid_risk_level(self):
        """Test ImpactCardCreate with invalid risk level."""
        with pytest.raises(ValidationError) as exc_info:
            ImpactCardCreate(
                watch_item_id=1,
                competitor_name="Test",
                risk_score=75,
                risk_level="extreme",  # Invalid risk level
                confidence_score=85
            )
        
        errors = exc_info.value.errors()
        assert any("string does not match expected pattern" in str(error) for error in errors)

class TestCompanyResearchSchemas:
    """Test Company Research-related schemas."""

    def test_company_research_request_valid(self):
        """Test valid CompanyResearchRequest schema."""
        data = {"company_name": "Test Company"}
        
        schema = CompanyResearchRequest(**data)
        assert schema.company_name == "Test Company"

    def test_company_research_request_invalid(self):
        """Test CompanyResearchRequest with invalid data."""
        with pytest.raises(ValidationError) as exc_info:
            CompanyResearchRequest(company_name="")
        
        errors = exc_info.value.errors()
        assert any("at least 1 character" in str(error) for error in errors)

    def test_company_research_create_valid(self):
        """Test valid CompanyResearchCreate schema."""
        data = {
            "company_name": "Test Company",
            "search_results": {"results": []},
            "research_report": {"report": "Test report"},
            "total_sources": 15,
            "api_usage": {"search_calls": 2, "ari_calls": 1, "total_calls": 3}
        }
        
        schema = CompanyResearchCreate(**data)
        assert schema.company_name == "Test Company"
        assert schema.search_results == {"results": []}
        assert schema.research_report == {"report": "Test report"}
        assert schema.total_sources == 15

    def test_company_research_create_minimal(self):
        """Test CompanyResearchCreate with minimal data."""
        data = {"company_name": "Test Company"}
        
        schema = CompanyResearchCreate(**data)
        assert schema.company_name == "Test Company"
        assert schema.search_results == {}
        assert schema.research_report == {}
        assert schema.total_sources == 0
        assert schema.api_usage == {}

class TestSchemaValidationEdgeCases:
    """Test edge cases and boundary conditions for schemas."""

    def test_very_long_competitor_name(self):
        """Test competitor name at maximum length."""
        long_name = "A" * 255
        
        schema = WatchItemCreate(competitor_name=long_name)
        assert schema.competitor_name == long_name

    def test_competitor_name_too_long(self):
        """Test competitor name exceeding maximum length."""
        with pytest.raises(ValidationError) as exc_info:
            WatchItemCreate(competitor_name="A" * 256)
        
        errors = exc_info.value.errors()
        assert any("at most 255 characters" in str(error) for error in errors)

    def test_many_keywords(self):
        """Test watchlist with many keywords."""
        many_keywords = [f"keyword_{i}" for i in range(100)]
        
        schema = WatchItemCreate(
            competitor_name="Test Competitor",
            keywords=many_keywords
        )
        assert len(schema.keywords) == 100

    def test_boundary_risk_scores(self):
        """Test risk scores at boundaries."""
        # Test minimum risk score
        schema = ImpactCardCreate(
            watch_item_id=1,
            competitor_name="Test",
            risk_score=0,
            risk_level="low",
            confidence_score=0
        )
        assert schema.risk_score == 0
        assert schema.confidence_score == 0
        
        # Test maximum risk score
        schema = ImpactCardCreate(
            watch_item_id=1,
            competitor_name="Test",
            risk_score=100,
            risk_level="critical",
            confidence_score=100
        )
        assert schema.risk_score == 100
        assert schema.confidence_score == 100

    def test_empty_lists_and_dicts(self):
        """Test schemas with empty lists and dictionaries."""
        schema = ImpactCardCreate(
            watch_item_id=1,
            competitor_name="Test",
            risk_score=50,
            risk_level="medium",
            confidence_score=75,
            impact_areas=[],
            key_insights=[],
            recommended_actions=[],
            source_breakdown={},
            api_usage={}
        )
        
        assert schema.impact_areas == []
        assert schema.key_insights == []
        assert schema.recommended_actions == []
        assert schema.source_breakdown.news_articles == 0
        assert schema.api_usage.total_calls == 0