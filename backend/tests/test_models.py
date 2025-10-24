"""
Tests for database models
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.watch import WatchItem
from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch

class TestWatchItemModel:
    """Test WatchItem database model."""

    @pytest.mark.asyncio
    async def test_create_watch_item(self, db_session: AsyncSession, sample_competitor_data):
        """Test creating a watch item."""
        watch_item = WatchItem(**sample_competitor_data)
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        assert watch_item.id is not None
        assert watch_item.competitor_name == sample_competitor_data["competitor_name"]
        assert watch_item.keywords == sample_competitor_data["keywords"]
        assert watch_item.description == sample_competitor_data["description"]
        assert watch_item.is_active is True
        assert watch_item.created_at is not None

    @pytest.mark.asyncio
    async def test_watch_item_defaults(self, db_session: AsyncSession):
        """Test watch item default values."""
        watch_item = WatchItem(competitor_name="Test Competitor")
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        assert watch_item.keywords == []
        assert watch_item.is_active is True
        assert watch_item.check_frequency == 120
        assert watch_item.risk_threshold == 70

    @pytest.mark.asyncio
    async def test_watch_item_repr(self, sample_competitor_data):
        """Test watch item string representation."""
        watch_item = WatchItem(**sample_competitor_data)
        watch_item.id = 1

        repr_str = repr(watch_item)
        assert "WatchItem" in repr_str
        assert "id=1" in repr_str
        assert sample_competitor_data["competitor_name"] in repr_str

class TestImpactCardModel:
    """Test ImpactCard database model."""

    @pytest.mark.asyncio
    async def test_create_impact_card(self, db_session: AsyncSession, sample_impact_card_data):
        """Test creating an impact card."""
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        assert impact_card.id is not None
        assert impact_card.competitor_name == sample_impact_card_data["competitor_name"]
        assert impact_card.risk_score == sample_impact_card_data["risk_score"]
        assert impact_card.risk_level == sample_impact_card_data["risk_level"]
        assert impact_card.confidence_score == sample_impact_card_data["confidence_score"]
        assert impact_card.created_at is not None

    @pytest.mark.asyncio
    async def test_impact_card_defaults(self, db_session: AsyncSession):
        """Test impact card default values."""
        impact_card = ImpactCard(
            competitor_name="Test Competitor",
            risk_score=50,
            risk_level="medium",
            confidence_score=75
        )
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        assert impact_card.impact_areas == []
        assert impact_card.key_insights == []
        assert impact_card.recommended_actions == []
        assert impact_card.total_sources == 0
        assert impact_card.source_breakdown == {}
        assert impact_card.api_usage == {}
        assert impact_card.raw_data == {}

    @pytest.mark.asyncio
    async def test_impact_card_with_watch_item(self, db_session: AsyncSession, sample_competitor_data, sample_impact_card_data):
        """Test impact card with associated watch item."""
        # Create watch item first
        watch_item = WatchItem(**sample_competitor_data)
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        # Create impact card with watch item reference
        sample_impact_card_data["watch_item_id"] = watch_item.id
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        assert impact_card.watch_item_id == watch_item.id
        # Test relationship (if properly configured)
        # assert impact_card.watch_item.competitor_name == watch_item.competitor_name

    @pytest.mark.asyncio
    async def test_impact_card_repr(self, sample_impact_card_data):
        """Test impact card string representation."""
        impact_card = ImpactCard(**sample_impact_card_data)
        impact_card.id = 1

        repr_str = repr(impact_card)
        assert "ImpactCard" in repr_str
        assert "id=1" in repr_str
        assert sample_impact_card_data["competitor_name"] in repr_str
        assert str(sample_impact_card_data["risk_score"]) in repr_str

class TestCompanyResearchModel:
    """Test CompanyResearch database model."""

    @pytest.mark.asyncio
    async def test_create_company_research(self, db_session: AsyncSession):
        """Test creating company research."""
        research_data = {
            "company_name": "Test Company",
            "search_results": {"results": [{"title": "Test"}]},
            "research_report": {"report": "Test report"},
            "total_sources": 15,
            "api_usage": {"search_calls": 2, "ari_calls": 1, "total_calls": 3}
        }

        research = CompanyResearch(**research_data)
        db_session.add(research)
        await db_session.commit()
        await db_session.refresh(research)

        assert research.id is not None
        assert research.company_name == "Test Company"
        assert research.search_results == {"results": [{"title": "Test"}]}
        assert research.research_report == {"report": "Test report"}
        assert research.total_sources == 15
        assert research.created_at is not None

    @pytest.mark.asyncio
    async def test_company_research_defaults(self, db_session: AsyncSession):
        """Test company research default values."""
        research = CompanyResearch(company_name="Test Company")
        db_session.add(research)
        await db_session.commit()
        await db_session.refresh(research)

        assert research.search_results == {}
        assert research.research_report == {}
        assert research.total_sources == 0
        assert research.api_usage == {}

    @pytest.mark.asyncio
    async def test_company_research_repr(self):
        """Test company research string representation."""
        research = CompanyResearch(company_name="Test Company")
        research.id = 1

        repr_str = repr(research)
        assert "CompanyResearch" in repr_str
        assert "id=1" in repr_str
        assert "Test Company" in repr_str

class TestModelRelationships:
    """Test relationships between models."""

    @pytest.mark.asyncio
    async def test_watch_item_impact_cards_relationship(self, db_session: AsyncSession, sample_competitor_data, sample_impact_card_data):
        """Test the relationship between watch items and impact cards."""
        # Create watch item
        watch_item = WatchItem(**sample_competitor_data)
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        # Create multiple impact cards for the watch item
        for i in range(3):
            impact_data = sample_impact_card_data.copy()
            impact_data["watch_item_id"] = watch_item.id
            impact_data["risk_score"] = 70 + i * 5
            impact_card = ImpactCard(**impact_data)
            db_session.add(impact_card)

        await db_session.commit()

        # Test that we can query impact cards by watch item
        from sqlalchemy import select
        result = await db_session.execute(
            select(ImpactCard).where(ImpactCard.watch_item_id == watch_item.id)
        )
        impact_cards = result.scalars().all()

        assert len(impact_cards) == 3
        for card in impact_cards:
            assert card.watch_item_id == watch_item.id

    @pytest.mark.asyncio
    async def test_model_timestamps(self, db_session: AsyncSession, sample_competitor_data):
        """Test that model timestamps are properly set."""
        watch_item = WatchItem(**sample_competitor_data)
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        assert watch_item.created_at is not None
        
        # Update the item
        original_created = watch_item.created_at
        watch_item.description = "Updated description"
        await db_session.commit()
        await db_session.refresh(watch_item)

        # Created timestamp should remain the same
        assert watch_item.created_at == original_created
        # Updated timestamp should be set (if the model supports it)
        # Note: This depends on the actual model implementation