"""
Tests for API endpoints
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock
from app.models.watch import WatchItem
from app.models.impact_card import ImpactCard
from app.models.company_research import CompanyResearch

class TestWatchlistEndpoints:
    """Test watchlist API endpoints."""

    @pytest.mark.asyncio
    async def test_create_watch_item(self, client: AsyncClient, sample_competitor_data):
        """Test creating a new watchlist item."""
        response = await client.post("/api/v1/watch/", json=sample_competitor_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["competitor_name"] == sample_competitor_data["competitor_name"]
        assert data["keywords"] == sample_competitor_data["keywords"]
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_watch_items_empty(self, client: AsyncClient):
        """Test getting watchlist items when none exist."""
        response = await client.get("/api/v1/watch/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_watch_items_with_data(self, client: AsyncClient, db_session: AsyncSession, sample_competitor_data):
        """Test getting watchlist items with existing data."""
        # Create a watch item in the database
        watch_item = WatchItem(**sample_competitor_data)
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        response = await client.get("/api/v1/watch/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["competitor_name"] == sample_competitor_data["competitor_name"]

    @pytest.mark.asyncio
    async def test_get_watch_item_by_id(self, client: AsyncClient, db_session: AsyncSession, sample_competitor_data):
        """Test getting a specific watchlist item by ID."""
        # Create a watch item
        watch_item = WatchItem(**sample_competitor_data)
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        response = await client.get(f"/api/v1/watch/{watch_item.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == watch_item.id
        assert data["competitor_name"] == sample_competitor_data["competitor_name"]

    @pytest.mark.asyncio
    async def test_get_watch_item_not_found(self, client: AsyncClient):
        """Test getting a non-existent watchlist item."""
        response = await client.get("/api/v1/watch/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_watch_item(self, client: AsyncClient, db_session: AsyncSession, sample_competitor_data):
        """Test updating a watchlist item."""
        # Create a watch item
        watch_item = WatchItem(**sample_competitor_data)
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        update_data = {"description": "Updated description"}
        response = await client.put(f"/api/v1/watch/{watch_item.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_watch_item(self, client: AsyncClient, db_session: AsyncSession, sample_competitor_data):
        """Test deleting a watchlist item."""
        # Create a watch item
        watch_item = WatchItem(**sample_competitor_data)
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        response = await client.delete(f"/api/v1/watch/{watch_item.id}")
        
        assert response.status_code == 204

        # Verify it's deleted
        response = await client.get(f"/api/v1/watch/{watch_item.id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_activate_watch_item(self, client: AsyncClient, db_session: AsyncSession, sample_competitor_data):
        """Test activating a watchlist item."""
        # Create an inactive watch item
        sample_competitor_data["is_active"] = False
        watch_item = WatchItem(**sample_competitor_data)
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        response = await client.post(f"/api/v1/watch/{watch_item.id}/activate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_deactivate_watch_item(self, client: AsyncClient, db_session: AsyncSession, sample_competitor_data):
        """Test deactivating a watchlist item."""
        # Create an active watch item
        watch_item = WatchItem(**sample_competitor_data)
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        response = await client.post(f"/api/v1/watch/{watch_item.id}/deactivate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

class TestImpactCardEndpoints:
    """Test Impact Card API endpoints."""

    @pytest.mark.asyncio
    async def test_generate_impact_card_success(self, client: AsyncClient, mock_you_api_responses):
        """Test successful Impact Card generation."""
        request_data = {
            "competitor_name": "Test Competitor",
            "keywords": ["AI", "ML"]
        }

        # Mock the You.com client
        with patch('app.api.impact.get_you_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_impact_card.return_value = {
                "competitor": "Test Competitor",
                "risk_score": 75,
                "risk_level": "high",
                "confidence_score": 85,
                "credibility_score": 0.8,
                "requires_review": False,
                "impact_areas": [],
                "key_insights": [],
                "recommended_actions": [],
                "next_steps_plan": [],
                "total_sources": 25,
                "source_breakdown": {"news_articles": 10, "search_results": 8, "research_citations": 7},
                "source_quality": {"score": 0.8, "tiers": {"tier1": 2, "tier2": 1, "tier3": 0}, "total": 3, "top_sources": []},
                "api_usage": {"news_calls": 2, "search_calls": 2, "chat_calls": 1, "ari_calls": 1, "total_calls": 6},
                "processing_time": "3.75s",
                "raw_data": {"demo": True},
                "explainability": {"reasoning": "", "impact_areas": [], "key_insights": [], "source_summary": {}},
            }
            async def mock_dependency():
                yield mock_client
            mock_get_client.side_effect = mock_dependency

            response = await client.post("/api/v1/impact/generate", json=request_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["competitor_name"] == "Test Competitor"
            assert data["risk_score"] == 75
            assert data["risk_level"] == "high"

    @pytest.mark.asyncio
    async def test_generate_impact_card_api_error(self, client: AsyncClient):
        """Test Impact Card generation with You.com API error."""
        request_data = {
            "competitor_name": "Test Competitor",
            "keywords": ["AI"]
        }

        # Mock the You.com client to raise an error
        with patch('app.api.impact.get_you_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_impact_card.side_effect = Exception("You.com API error")
            async def mock_dependency():
                yield mock_client
            mock_get_client.side_effect = mock_dependency

            response = await client.post("/api/v1/impact/generate", json=request_data)
            
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_impact_cards_empty(self, client: AsyncClient):
        """Test getting Impact Cards when none exist."""
        response = await client.get("/api/v1/impact/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_impact_cards_with_data(self, client: AsyncClient, db_session: AsyncSession, sample_impact_card_data):
        """Test getting Impact Cards with existing data."""
        # Create an impact card in the database
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        response = await client.get("/api/v1/impact/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["competitor_name"] == sample_impact_card_data["competitor_name"]

    @pytest.mark.asyncio
    async def test_get_impact_card_by_id(self, client: AsyncClient, db_session: AsyncSession, sample_impact_card_data):
        """Test getting a specific Impact Card by ID."""
        # Create an impact card
        impact_card = ImpactCard(**sample_impact_card_data)
        db_session.add(impact_card)
        await db_session.commit()
        await db_session.refresh(impact_card)

        response = await client.get(f"/api/v1/impact/{impact_card.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == impact_card.id
        assert data["competitor_name"] == sample_impact_card_data["competitor_name"]

    @pytest.mark.asyncio
    async def test_generate_impact_card_for_watch(self, client: AsyncClient, db_session: AsyncSession, sample_competitor_data):
        """Test generating Impact Card for a specific watch item."""
        # Create a watch item
        watch_item = WatchItem(**sample_competitor_data)
        db_session.add(watch_item)
        await db_session.commit()
        await db_session.refresh(watch_item)

        # Mock the You.com client
        with patch('app.api.impact.get_you_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_impact_card.return_value = {
                "competitor": sample_competitor_data["competitor_name"],
                "risk_score": 75,
                "risk_level": "high",
                "confidence_score": 85,
                "credibility_score": 0.78,
                "requires_review": False,
                "impact_areas": [],
                "key_insights": [],
                "recommended_actions": [],
                "next_steps_plan": [],
                "total_sources": 25,
                "source_breakdown": {"news_articles": 10, "search_results": 8, "research_citations": 7},
                "source_quality": {"score": 0.78, "tiers": {"tier1": 1, "tier2": 1, "tier3": 0}, "total": 2, "top_sources": []},
                "api_usage": {"news_calls": 2, "search_calls": 2, "chat_calls": 1, "ari_calls": 1, "total_calls": 6},
                "processing_time": "4.25s",
                "raw_data": {"demo": True},
                "explainability": {"reasoning": "", "impact_areas": [], "key_insights": [], "source_summary": {}},
            }
            async def mock_dependency():
                yield mock_client
            mock_get_client.side_effect = mock_dependency

            response = await client.post(f"/api/v1/impact/watch/{watch_item.id}/generate")
            
            assert response.status_code == 201
            data = response.json()
            assert data["watch_item_id"] == watch_item.id
            assert data["competitor_name"] == sample_competitor_data["competitor_name"]

class TestCompanyResearchEndpoints:
    """Test Company Research API endpoints."""

    @pytest.mark.asyncio
    async def test_research_company_success(self, client: AsyncClient, mock_you_api_responses):
        """Test successful company research."""
        request_data = {"company_name": "Test Company"}

        # Mock the You.com client
        with patch('app.api.research.get_you_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.quick_company_research.return_value = {
                "company": "Test Company",
                "search_results": mock_you_api_responses["search"],
                "research_report": mock_you_api_responses["ari"],
                "total_sources": 25,
                "api_usage": {"search_calls": 2, "ari_calls": 1, "total_calls": 3}
            }
            async def mock_dependency():
                yield mock_client
            mock_get_client.side_effect = mock_dependency

            response = await client.post("/api/v1/research/company", json=request_data)
            
            assert response.status_code == 201
            data = response.json()
            assert data["company_name"] == "Test Company"
            assert data["total_sources"] == 25

    @pytest.mark.asyncio
    async def test_get_company_research_empty(self, client: AsyncClient):
        """Test getting company research when none exists."""
        response = await client.get("/api/v1/research/")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_get_company_research_with_data(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting company research with existing data."""
        # Create company research in the database
        research_data = {
            "company_name": "Test Company",
            "search_results": {"results": []},
            "research_report": {"report": "Test report"},
            "total_sources": 10,
            "api_usage": {"search_calls": 1, "ari_calls": 1, "total_calls": 2}
        }
        research = CompanyResearch(**research_data)
        db_session.add(research)
        await db_session.commit()
        await db_session.refresh(research)

        response = await client.get("/api/v1/research/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company_name"] == "Test Company"

    @pytest.mark.asyncio
    async def test_get_company_research_by_id(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting specific company research by ID."""
        # Create company research
        research_data = {
            "company_name": "Test Company",
            "search_results": {"results": []},
            "research_report": {"report": "Test report"},
            "total_sources": 10,
            "api_usage": {"search_calls": 1, "ari_calls": 1, "total_calls": 2}
        }
        research = CompanyResearch(**research_data)
        db_session.add(research)
        await db_session.commit()
        await db_session.refresh(research)

        response = await client.get(f"/api/v1/research/{research.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == research.id
        assert data["company_name"] == "Test Company"

    @pytest.mark.asyncio
    async def test_get_research_by_company_name(self, client: AsyncClient, db_session: AsyncSession):
        """Test getting research by company name."""
        # Create company research
        research_data = {
            "company_name": "Test Company",
            "search_results": {"results": []},
            "research_report": {"report": "Test report"},
            "total_sources": 10,
            "api_usage": {"search_calls": 1, "ari_calls": 1, "total_calls": 2}
        }
        research = CompanyResearch(**research_data)
        db_session.add(research)
        await db_session.commit()

        response = await client.get("/api/v1/research/company/Test Company")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company_name"] == "Test Company"

class TestHealthAndDemoEndpoints:
    """Test health check and demo endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "Enterprise CIA" in data["service"]

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "Enterprise CIA" in data["message"]
        assert "You.com APIs" in data["description"]

    @pytest.mark.asyncio
    async def test_demo_you_apis_endpoint(self, client: AsyncClient):
        """Test You.com APIs demo endpoint."""
        response = await client.get("/api/v1/demo/you-apis")
        
        assert response.status_code == 200
        data = response.json()
        assert "You.com API" in data["message"]
        assert "apis" in data
        assert "workflow" in data
        
        # Check all 4 APIs are mentioned
        apis = data["apis"]
        assert "news" in apis
        assert "search" in apis
        assert "chat" in apis
        assert "ari" in apis
