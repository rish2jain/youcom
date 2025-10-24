"""
Integration tests for the complete Enterprise CIA workflow
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock
from app.models.watch import WatchItem

class TestEnterpriseWorkflow:
    """Test the complete enterprise competitive intelligence workflow."""

    @pytest.mark.asyncio
    async def test_complete_enterprise_workflow(self, client: AsyncClient, db_session: AsyncSession, mock_you_api_responses):
        """Test the complete enterprise workflow: Create watchlist → Generate Impact Card."""
        
        # Step 1: Create a competitor watchlist
        competitor_data = {
            "competitor_name": "OpenAI",
            "keywords": ["GPT", "ChatGPT", "API"],
            "description": "Leading AI company with ChatGPT"
        }
        
        response = await client.post("/api/v1/watch/", json=competitor_data)
        assert response.status_code == 201
        watch_item = response.json()
        watch_id = watch_item["id"]
        
        # Step 2: Generate Impact Card for the watchlist item
        with patch('app.api.impact.get_you_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_impact_card.return_value = {
                "competitor": "OpenAI",
                "risk_score": 85,
                "risk_level": "high",
                "confidence_score": 92,
                "credibility_score": 0.82,
                "requires_review": False,
                "impact_areas": [
                    {
                        "area": "product",
                        "impact_score": 90,
                        "description": "GPT-4 Turbo poses significant competitive threat"
                    }
                ],
                "key_insights": [
                    "OpenAI announced GPT-4 Turbo with 128K context window",
                    "Strong enterprise adoption with Fortune 500 companies"
                ],
                "recommended_actions": [
                    {
                        "action": "Accelerate long-context model development",
                        "priority": "high",
                        "timeline": "immediate"
                    }
                ],
                "next_steps_plan": [],
                "total_sources": 47,
                "source_breakdown": {
                    "news_articles": 12,
                    "search_results": 15,
                    "research_citations": 20
                },
                "source_quality": {"score": 0.82, "tiers": {"tier1": 2, "tier2": 1, "tier3": 0}, "total": 3, "top_sources": []},
                "api_usage": {
                    "news_calls": 3,
                    "search_calls": 2,
                    "chat_calls": 1,
                    "ari_calls": 1,
                    "total_calls": 7
                },
                "processing_time": "4.32s",
                "raw_data": {"demo": True},
                "explainability": {"reasoning": "", "impact_areas": [], "key_insights": [], "source_summary": {}},
            }
            async def mock_dependency():
                yield mock_client
            mock_get_client.side_effect = mock_dependency
            
            response = await client.post(f"/api/v1/impact/watch/{watch_id}/generate")
            assert response.status_code == 201
            impact_card = response.json()
            
            # Verify Impact Card data
            assert impact_card["competitor_name"] == "OpenAI"
            assert impact_card["risk_score"] == 85
            assert impact_card["risk_level"] == "high"
            assert impact_card["total_sources"] == 47
            assert impact_card["watch_item_id"] == watch_id
            
            # Verify You.com API usage tracking
            api_usage = impact_card["api_usage"]
            assert api_usage["news_calls"] == 3
            assert api_usage["search_calls"] == 2
            assert api_usage["chat_calls"] == 1
            assert api_usage["ari_calls"] == 1
            assert api_usage["total_calls"] == 7
        
        # Step 3: Retrieve the generated Impact Card
        response = await client.get(f"/api/v1/impact/{impact_card['id']}")
        assert response.status_code == 200
        retrieved_card = response.json()
        assert retrieved_card["id"] == impact_card["id"]
        
        # Step 4: List all Impact Cards for the watch item
        response = await client.get(f"/api/v1/impact/watch/{watch_id}")
        assert response.status_code == 200
        cards_list = response.json()
        assert cards_list["total"] == 1
        assert len(cards_list["items"]) == 1

class TestIndividualWorkflow:
    """Test the complete individual user workflow."""

    @pytest.mark.asyncio
    async def test_complete_individual_workflow(self, client: AsyncClient, mock_you_api_responses):
        """Test the complete individual workflow: Company research → Export results."""
        
        # Step 1: Research a company
        research_request = {"company_name": "Perplexity AI"}
        
        with patch('app.api.research.get_you_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.quick_company_research.return_value = {
                "company": "Perplexity AI",
                "search_results": {
                    "query": "Perplexity AI company profile",
                    "results": [
                        {
                            "title": "Perplexity AI - AI-Powered Search Engine",
                            "snippet": "Perplexity AI is an AI-powered search engine...",
                            "url": "https://perplexity.ai"
                        }
                    ],
                    "total_count": 15,
                    "api_type": "search"
                },
                "research_report": {
                    "query": "Comprehensive analysis of Perplexity AI",
                    "report": "Perplexity AI is a conversational search engine...",
                    "citations": [
                        {"title": "Company Overview", "url": "https://perplexity.ai/about"}
                    ],
                    "source_count": 25,
                    "api_type": "ari"
                },
                "total_sources": 40,
                "api_usage": {
                    "search_calls": 2,
                    "ari_calls": 1,
                    "total_calls": 3
                }
            }
            async def mock_dependency():
                yield mock_client
            mock_get_client.side_effect = mock_dependency
            
            response = await client.post("/api/v1/research/company", json=research_request)
            assert response.status_code == 201
            research_data = response.json()
            
            # Verify research data
            assert research_data["company_name"] == "Perplexity AI"
            assert research_data["total_sources"] == 40
            
            # Verify You.com API usage
            api_usage = research_data["api_usage"]
            assert api_usage["search_calls"] == 2
            assert api_usage["ari_calls"] == 1
            assert api_usage["total_calls"] == 3
        
        # Step 2: Retrieve the research by company name
        response = await client.get("/api/v1/research/company/Perplexity AI")
        assert response.status_code == 200
        research_list = response.json()
        assert len(research_list) == 1
        assert research_list[0]["company_name"] == "Perplexity AI"
        
        # Step 3: Get specific research by ID
        research_id = research_data["id"]
        response = await client.get(f"/api/v1/research/{research_id}")
        assert response.status_code == 200
        retrieved_research = response.json()
        assert retrieved_research["id"] == research_id

class TestDualMarketIntegration:
    """Test the integration between enterprise and individual features."""

    @pytest.mark.asyncio
    async def test_api_usage_tracking_across_modes(self, client: AsyncClient, db_session: AsyncSession):
        """Test that API usage is properly tracked across both enterprise and individual modes."""
        
        # Enterprise mode: Generate Impact Card
        competitor_data = {
            "competitor_name": "Anthropic",
            "keywords": ["Claude", "AI assistant"]
        }
        
        with patch('app.api.impact.get_you_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_impact_card.return_value = {
                "competitor": "Anthropic",
                "risk_score": 72,
                "risk_level": "high",
                "confidence_score": 88,
                "credibility_score": 0.76,
                "requires_review": False,
                "impact_areas": [],
                "key_insights": [],
                "recommended_actions": [],
                "next_steps_plan": [],
                "total_sources": 38,
                "source_breakdown": {"news_articles": 8, "search_results": 12, "research_citations": 18},
                "source_quality": {"score": 0.76, "tiers": {"tier1": 1, "tier2": 1, "tier3": 0}, "total": 2, "top_sources": []},
                "api_usage": {"news_calls": 2, "search_calls": 2, "chat_calls": 1, "ari_calls": 1, "total_calls": 6},
                "processing_time": "3.90s",
                "raw_data": {"demo": True},
                "explainability": {"reasoning": "", "impact_areas": [], "key_insights": [], "source_summary": {}},
            }
            async def enterprise_dependency():
                yield mock_client
            mock_get_client.side_effect = enterprise_dependency
            
            response = await client.post("/api/v1/impact/generate", json=competitor_data)
            assert response.status_code == 201
            impact_card = response.json()
            
            enterprise_api_calls = impact_card["api_usage"]["total_calls"]
            assert enterprise_api_calls == 6
        
        # Individual mode: Company research
        research_request = {"company_name": "Stripe"}
        
        with patch('app.api.research.get_you_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.quick_company_research.return_value = {
                "company": "Stripe",
                "search_results": {"results": [], "api_type": "search"},
                "research_report": {"report": "Stripe analysis...", "api_type": "ari"},
                "total_sources": 50,
                "api_usage": {"search_calls": 2, "ari_calls": 1, "total_calls": 3}
            }
            async def individual_dependency():
                yield mock_client
            mock_get_client.side_effect = individual_dependency
            
            response = await client.post("/api/v1/research/company", json=research_request)
            assert response.status_code == 201
            research_data = response.json()
            
            individual_api_calls = research_data["api_usage"]["total_calls"]
            assert individual_api_calls == 3
        
        # Verify both modes work independently with proper API tracking
        assert enterprise_api_calls + individual_api_calls == 9

class TestErrorHandlingIntegration:
    """Test error handling across the complete system."""

    @pytest.mark.asyncio
    async def test_you_api_error_handling(self, client: AsyncClient):
        """Test that You.com API errors are properly handled and reported."""
        
        request_data = {
            "competitor_name": "Test Competitor",
            "keywords": ["test"]
        }
        
        # Mock You.com API to raise an error
        with patch('app.api.impact.get_you_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.generate_impact_card.side_effect = Exception("You.com API rate limit exceeded")
            async def failing_dependency():
                yield mock_client
            mock_get_client.side_effect = failing_dependency
            
            response = await client.post("/api/v1/impact/generate", json=request_data)
            assert response.status_code == 500
            error_data = response.json()
            assert "error" in error_data
            assert "Enterprise CIA" in error_data["service"]

    @pytest.mark.asyncio
    async def test_database_error_handling(self, client: AsyncClient):
        """Test handling of database-related errors."""
        
        # Try to get a non-existent watch item
        response = await client.get("/api/v1/watch/99999")
        assert response.status_code == 404
        error_data = response.json()
        assert "not found" in error_data["detail"].lower()
        
        # Try to generate Impact Card for non-existent watch item
        response = await client.post("/api/v1/impact/watch/99999/generate")
        assert response.status_code == 404

class TestPerformanceIntegration:
    """Test performance aspects of the integrated system."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client: AsyncClient):
        """Test that the system can handle concurrent requests."""
        import asyncio
        
        # Create multiple concurrent requests
        async def create_watch_item(name: str):
            data = {
                "competitor_name": f"Competitor {name}",
                "keywords": ["AI", "test"],
                "description": f"Test competitor {name}"
            }
            return await client.post("/api/v1/watch/", json=data)
        
        # Run 5 concurrent requests
        tasks = [create_watch_item(str(i)) for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 201
        
        # Verify all items were created
        response = await client.get("/api/v1/watch/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5

    @pytest.mark.asyncio
    async def test_large_data_handling(self, client: AsyncClient):
        """Test handling of large data sets."""
        
        # Create a watch item with many keywords
        large_keywords = [f"keyword_{i}" for i in range(100)]
        data = {
            "competitor_name": "Large Data Competitor",
            "keywords": large_keywords,
            "description": "A" * 1000  # Large description
        }
        
        response = await client.post("/api/v1/watch/", json=data)
        assert response.status_code == 201
        
        created_item = response.json()
        assert len(created_item["keywords"]) == 100
        assert len(created_item["description"]) == 1000
