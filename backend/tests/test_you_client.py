"""
Tests for You.com API client integration
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from app.services.you_client import YouComOrchestrator, YouComAPIError

class TestYouComOrchestrator:
    """Test the You.com API orchestration client."""

    @pytest.fixture
    def you_client(self, mock_you_api_key):
        """Create a You.com client for testing."""
        return YouComOrchestrator(api_key=mock_you_api_key)

    @pytest.mark.asyncio
    async def test_client_initialization(self, mock_you_api_key):
        """Test client initialization with API key."""
        client = YouComOrchestrator(api_key=mock_you_api_key)
        assert client.api_key == mock_you_api_key
        assert client.api_usage["total_calls"] == 0

    @pytest.mark.asyncio
    async def test_client_initialization_without_key(self):
        """Test client initialization fails without API key."""
        with patch('app.services.you_client.settings.you_api_key', ''):
            with pytest.raises(ValueError, match="You.com API key is required"):
                YouComOrchestrator()

    @pytest.mark.asyncio
    async def test_fetch_news_success(self, you_client, mock_you_api_responses):
        """Test successful news API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"news": mock_you_api_responses["news"]["articles"]}
        mock_response.status_code = 200

        with patch.object(you_client, '_perform_request', new=AsyncMock(return_value=mock_response)) as mock_request:
            result = await you_client.fetch_news("test query")
            
            assert result["query"] == "test query"
            assert result["api_type"] == "news"
            assert len(result["articles"]) == 1
            assert you_client.api_usage["news_calls"] == 1
            assert you_client.api_usage["total_calls"] == 1
            
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_news_http_error(self, you_client):
        """Test news API call with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        error = httpx.HTTPStatusError("500 Server Error", request=MagicMock(), response=mock_response)

        with patch.object(you_client, '_perform_request', new=AsyncMock(side_effect=error)):
            with pytest.raises(YouComAPIError, match="News API error"):
                await you_client.fetch_news("test query")

    @pytest.mark.asyncio
    async def test_search_context_success(self, you_client, mock_you_api_responses):
        """Test successful search API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": {"web": mock_you_api_responses["search"]["results"]}}
        mock_response.status_code = 200

        with patch.object(you_client, '_perform_request', new=AsyncMock(return_value=mock_response)) as mock_request:
            result = await you_client.search_context("test query")
            
            assert result["query"] == "test query"
            assert result["api_type"] == "search"
            assert len(result["results"]) == 1
            assert you_client.api_usage["search_calls"] == 1
            
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_impact_success(self, you_client, mock_you_api_responses):
        """Test successful chat API call for impact analysis."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": mock_you_api_responses["chat"]["response"],
            "citations": []
        }
        mock_response.status_code = 200

        news_data = mock_you_api_responses["news"]
        context_data = mock_you_api_responses["search"]

        with patch.object(you_client, '_perform_request', new=AsyncMock(return_value=mock_response)) as mock_request:
            result = await you_client.analyze_impact(news_data, context_data, "Test Competitor")
            
            assert result["competitor"] == "Test Competitor"
            assert result["api_type"] == "chat"
            assert result["analysis"]["risk_score"] == 75
            assert you_client.api_usage["chat_calls"] == 1
            
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_research_report_success(self, you_client, mock_you_api_responses):
        """Test successful ARI API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": mock_you_api_responses["ari"]["report"],
            "citations": mock_you_api_responses["ari"]["citations"]
        }
        mock_response.status_code = 200

        with patch.object(you_client, '_perform_request', new=AsyncMock(return_value=mock_response)) as mock_request:
            result = await you_client.generate_research_report("test query")
            
            assert result["query"] == "test query"
            assert result["api_type"] == "ari"
            assert result["source_count"] == 1
            assert you_client.api_usage["ari_calls"] == 1
            
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_impact_card_full_workflow(self, you_client, mock_you_api_responses):
        """Test the complete impact card generation workflow using all 4 APIs."""
        # Mock all API responses
        news_response = MagicMock()
        news_response.json.return_value = {"news": mock_you_api_responses["news"]["articles"]}
        news_response.raise_for_status.return_value = None

        search_response = MagicMock()
        search_response.json.return_value = {"results": {"web": mock_you_api_responses["search"]["results"]}}
        search_response.raise_for_status.return_value = None

        chat_response = MagicMock()
        chat_response.json.return_value = {
            "response": mock_you_api_responses["chat"]["response"],
            "citations": []
        }
        chat_response.raise_for_status.return_value = None

        ari_response = MagicMock()
        ari_response.json.return_value = {
            "response": mock_you_api_responses["ari"]["report"],
            "citations": mock_you_api_responses["ari"]["citations"]
        }
        ari_response.raise_for_status.return_value = None

        with patch.object(you_client, '_perform_request', new=AsyncMock(side_effect=[
            news_response,
            search_response,
            chat_response,
            ari_response,
        ])) as mock_request:

            result = await you_client.generate_impact_card("Test Competitor", ["AI", "ML"])
            
            # Verify the complete workflow
            assert result["competitor"] == "Test Competitor"
            assert result["risk_score"] == 75
            assert result["risk_level"] == "high"
            assert result["confidence_score"] == 85
            assert result["total_sources"] == 3  # 1 news + 1 search + 1 ari
            assert "credibility_score" in result
            assert isinstance(result["recommended_actions"], list)
            if result["recommended_actions"]:
                assert "owner" in result["recommended_actions"][0]
            
            # Verify all APIs were called
            assert you_client.api_usage["news_calls"] == 1
            assert you_client.api_usage["search_calls"] == 1
            assert you_client.api_usage["chat_calls"] == 1
            assert you_client.api_usage["ari_calls"] == 1
            assert you_client.api_usage["total_calls"] == 4
            
            # Verify API calls were made
            assert mock_request.await_count == 4

    @pytest.mark.asyncio
    async def test_quick_company_research(self, you_client, mock_you_api_responses):
        """Test quick company research for individual users."""
        search_response = MagicMock()
        search_response.json.return_value = {"results": {"web": mock_you_api_responses["search"]["results"]}}
        search_response.raise_for_status.return_value = None

        ari_response = MagicMock()
        ari_response.json.return_value = {
            "response": mock_you_api_responses["ari"]["report"],
            "citations": mock_you_api_responses["ari"]["citations"]
        }
        ari_response.raise_for_status.return_value = None

        with patch.object(you_client, '_perform_request', new=AsyncMock(side_effect=[
            search_response,
            ari_response,
        ])) as mock_request:

            result = await you_client.quick_company_research("Test Company")
            
            assert result["company"] == "Test Company"
            assert result["total_sources"] == 2  # 1 search + 1 ari
            assert you_client.api_usage["search_calls"] == 1
            assert you_client.api_usage["ari_calls"] == 1
            
            assert mock_request.await_count == 2

    @pytest.mark.asyncio
    async def test_parse_analysis_response_json_error(self, you_client):
        """Test analysis response parsing with invalid JSON."""
        news_data = {"articles": []}
        context_data = {"results": []}
        
        # Test with invalid JSON response
        invalid_response = {"response": "invalid json string"}

        with pytest.raises(YouComAPIError, match="invalid JSON"):
            you_client._parse_analysis_response(invalid_response, "Test Competitor")

    @pytest.mark.asyncio
    async def test_create_analysis_prompt(self, you_client):
        """Test analysis prompt creation."""
        news_data = {
            "articles": [
                {"title": "Test News", "snippet": "Test snippet"}
            ]
        }
        context_data = {
            "results": [
                {"title": "Test Result", "snippet": "Test context"}
            ]
        }
        
        prompt = you_client._create_analysis_prompt(news_data, context_data, "Test Competitor")
        
        assert "Test Competitor" in prompt
        assert "RECENT NEWS:" in prompt
        assert "CONTEXT INFORMATION:" in prompt
        assert "risk_score" in prompt
        assert "impact_areas" in prompt

    @pytest.mark.asyncio
    async def test_assemble_impact_card(self, you_client, mock_you_api_responses):
        """Test impact card assembly from API responses."""
        news_data = mock_you_api_responses["news"]
        context_data = mock_you_api_responses["search"]
        analysis_data = {
            "analysis": mock_you_api_responses["chat"]["response"],
            "api_type": "chat"
        }
        research_data = mock_you_api_responses["ari"]
        
        result = you_client.assemble_impact_card(
            news_data, context_data, analysis_data, research_data, "Test Competitor"
        )
        
        assert result["competitor"] == "Test Competitor"
        assert result["risk_score"] == 75
        assert result["risk_level"] == "high"
        assert result["confidence_score"] == 85
        assert result["total_sources"] == 3
        assert "powered_by" in result
        assert "You.com APIs" in result["powered_by"]

    @pytest.mark.asyncio
    async def test_api_usage_tracking(self, you_client):
        """Test API usage tracking functionality."""
        initial_calls = you_client.api_usage["total_calls"]
        
        you_client._track_usage("news")
        assert you_client.api_usage["news_calls"] == 1
        assert you_client.api_usage["total_calls"] == initial_calls + 1
        
        you_client._track_usage("search")
        assert you_client.api_usage["search_calls"] == 1
        assert you_client.api_usage["total_calls"] == initial_calls + 2

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_you_api_key):
        """Test You.com client as async context manager."""
        async with YouComOrchestrator(api_key=mock_you_api_key) as client:
            assert client.api_key == mock_you_api_key
            assert hasattr(client, 'client')
        
        # Client should be closed after context exit
        # Note: In real implementation, we'd check if client is closed
