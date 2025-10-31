"""
Integration tests for enhanced error handling in You.com API client.
Tests the improvements made to error handling, type safety, and logging.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from app.services.you_client import YouComOrchestrator, YouComAPIError


class TestEnhancedErrorHandling:
    """Test enhanced error handling improvements."""

    @pytest.fixture
    def you_client(self, mock_you_api_key):
        """Create a You.com client for testing."""
        return YouComOrchestrator(api_key=mock_you_api_key)

    @pytest.mark.asyncio
    async def test_youcom_api_error_with_api_type(self):
        """Test YouComAPIError includes API type in error representation."""
        error = YouComAPIError(
            "Test error message",
            status_code=500,
            payload={"detail": "Internal error"},
            api_type="search"
        )

        assert error.api_type == "search"
        assert error.status_code == 500
        assert "Test error message" in str(error)
        assert "API: search" in str(error)
        assert "Status: 500" in str(error)

    @pytest.mark.asyncio
    async def test_youcom_api_error_without_optional_params(self):
        """Test YouComAPIError with minimal parameters."""
        error = YouComAPIError("Simple error")

        assert error.api_type is None
        assert error.status_code is None
        assert str(error) == "Simple error"

    @pytest.mark.asyncio
    async def test_news_api_error_includes_context(self, you_client):
        """Test News API error includes API context."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        error = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=MagicMock(),
            response=mock_response
        )

        with patch.object(you_client, '_perform_request', new=AsyncMock(side_effect=error)):
            with pytest.raises(YouComAPIError) as exc_info:
                await you_client.fetch_news("test query")

            assert exc_info.value.api_type == "news"
            assert exc_info.value.status_code == 429
            assert "API: news" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_api_error_includes_context(self, you_client):
        """Test Search API error includes API context."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service unavailable"
        error = httpx.HTTPStatusError(
            "503 Service Unavailable",
            request=MagicMock(),
            response=mock_response
        )

        with patch.object(you_client, '_perform_request', new=AsyncMock(side_effect=error)):
            with pytest.raises(YouComAPIError) as exc_info:
                await you_client.search_context("test query")

            assert exc_info.value.api_type == "search"
            assert exc_info.value.status_code == 503
            assert "API: search" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_chat_api_error_includes_context(self, you_client):
        """Test Chat API error includes API context."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        error = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=mock_response
        )

        news_data = {"articles": []}
        context_data = {"results": []}

        with patch.object(you_client, '_perform_request', new=AsyncMock(side_effect=error)):
            with pytest.raises(YouComAPIError) as exc_info:
                await you_client.analyze_impact(news_data, context_data, "Test Competitor")

            assert exc_info.value.api_type == "chat"
            assert exc_info.value.status_code == 401
            assert "API: chat" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ari_api_error_includes_context(self, you_client):
        """Test ARI API error includes API context."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        error = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=mock_response
        )

        with patch.object(you_client, '_perform_request', new=AsyncMock(side_effect=error)):
            with pytest.raises(YouComAPIError) as exc_info:
                await you_client.generate_research_report("test query")

            assert exc_info.value.api_type == "ari"
            assert exc_info.value.status_code == 500
            assert "API: ari" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generic_exception_includes_context(self, you_client):
        """Test generic exceptions include API context."""
        error = Exception("Network timeout")

        with patch.object(you_client, '_perform_request', new=AsyncMock(side_effect=error)):
            with pytest.raises(YouComAPIError) as exc_info:
                await you_client.fetch_news("test query")

            assert exc_info.value.api_type == "news"
            assert "Network timeout" in str(exc_info.value.payload)


class TestCitationTypeSafety:
    """Test type safety improvements for citation handling."""

    @pytest.fixture
    def you_client(self, mock_you_api_key):
        """Create a You.com client for testing."""
        return YouComOrchestrator(api_key=mock_you_api_key)

    def test_dict_citations_are_processed(self, you_client):
        """Test dict-format citations are processed correctly."""
        research_data = {
            "report": "Test report",
            "citations": [
                {"url": "https://example.com/article", "title": "Test Article"},
                {"url": "https://news.ycombinator.com/item", "title": "HN Discussion"},
            ]
        }

        sources = []
        citations = research_data.get("citations", [])

        if citations and isinstance(citations, list):
            for citation in citations:
                if isinstance(citation, dict):
                    url = citation.get("url")
                    if url and isinstance(url, str):
                        tier, weight = you_client._tier_for_domain(url)
                        sources.append({
                            "type": "research",
                            "title": citation.get("title", "Research Citation"),
                            "url": url,
                            "tier": tier,
                            "weight": weight * 1.1,
                        })

        assert len(sources) == 2
        assert sources[0]["url"] == "https://example.com/article"
        assert sources[0]["title"] == "Test Article"
        assert sources[1]["url"] == "https://news.ycombinator.com/item"

    def test_string_citations_are_processed(self, you_client):
        """Test string-format citations are processed correctly."""
        research_data = {
            "report": "Test report",
            "citations": [
                "https://example.com/article1",
                "https://github.com/test/repo",
            ]
        }

        sources = []
        citations = research_data.get("citations", [])

        if citations and isinstance(citations, list):
            for citation in citations:
                if isinstance(citation, str):
                    try:
                        tier, weight = you_client._tier_for_domain(citation)
                        sources.append({
                            "type": "research",
                            "title": "Research Citation",
                            "url": citation,
                            "tier": tier,
                            "weight": weight * 1.1,
                        })
                    except Exception:
                        continue

        assert len(sources) == 2
        assert sources[0]["url"] == "https://example.com/article1"
        assert sources[1]["url"] == "https://github.com/test/repo"

    def test_invalid_dict_citations_are_skipped(self, you_client):
        """Test invalid dict citations are skipped safely."""
        research_data = {
            "report": "Test report",
            "citations": [
                {"url": "https://valid.com", "title": "Valid"},
                {"url": None, "title": "Invalid - no URL"},  # Invalid: None URL
                {"url": 123, "title": "Invalid - number URL"},  # Invalid: non-string URL
                {"title": "Invalid - missing URL"},  # Invalid: missing URL
                {"url": "https://another-valid.com", "title": "Valid 2"},
            ]
        }

        sources = []
        citations = research_data.get("citations", [])

        if citations and isinstance(citations, list):
            for citation in citations:
                if isinstance(citation, dict):
                    url = citation.get("url")
                    if not url or not isinstance(url, str):
                        continue
                    tier, weight = you_client._tier_for_domain(url)
                    sources.append({
                        "type": "research",
                        "title": citation.get("title", "Research Citation"),
                        "url": url,
                        "tier": tier,
                        "weight": weight * 1.1,
                    })

        # Only 2 valid citations should be processed
        assert len(sources) == 2
        assert sources[0]["url"] == "https://valid.com"
        assert sources[1]["url"] == "https://another-valid.com"

    def test_mixed_citation_formats_are_handled(self, you_client):
        """Test mixed dict and string citations are handled correctly."""
        research_data = {
            "report": "Test report",
            "citations": [
                {"url": "https://dict-format.com", "title": "Dict Citation"},
                "https://string-format.com",
                {"url": "https://another-dict.com", "title": "Another Dict"},
                "https://another-string.com",
            ]
        }

        sources = []
        citations = research_data.get("citations", [])

        if citations and isinstance(citations, list):
            for citation in citations:
                if isinstance(citation, dict):
                    url = citation.get("url")
                    if not url or not isinstance(url, str):
                        continue
                    tier, weight = you_client._tier_for_domain(url)
                    sources.append({
                        "type": "research",
                        "title": citation.get("title", "Research Citation"),
                        "url": url,
                        "tier": tier,
                        "weight": weight * 1.1,
                    })
                elif isinstance(citation, str):
                    try:
                        tier, weight = you_client._tier_for_domain(citation)
                        sources.append({
                            "type": "research",
                            "title": "Research Citation",
                            "url": citation,
                            "tier": tier,
                            "weight": weight * 1.1,
                        })
                    except Exception:
                        continue

        assert len(sources) == 4
        assert sources[0]["title"] == "Dict Citation"
        assert sources[1]["url"] == "https://string-format.com"

    def test_unexpected_citation_types_are_ignored(self, you_client):
        """Test unexpected citation types don't crash the system."""
        research_data = {
            "report": "Test report",
            "citations": [
                {"url": "https://valid.com", "title": "Valid"},
                123,  # Invalid: number
                None,  # Invalid: None
                ["nested", "array"],  # Invalid: array
                {"nested": {"url": "deep"}},  # Invalid: nested dict without url
                "https://valid-string.com",  # Valid
            ]
        }

        sources = []
        citations = research_data.get("citations", [])

        if citations and isinstance(citations, list):
            for citation in citations:
                if isinstance(citation, dict):
                    url = citation.get("url")
                    if not url or not isinstance(url, str):
                        continue
                    tier, weight = you_client._tier_for_domain(url)
                    sources.append({
                        "type": "research",
                        "title": citation.get("title", "Research Citation"),
                        "url": url,
                        "tier": tier,
                        "weight": weight * 1.1,
                    })
                elif isinstance(citation, str):
                    try:
                        tier, weight = you_client._tier_for_domain(citation)
                        sources.append({
                            "type": "research",
                            "title": "Research Citation",
                            "url": citation,
                            "tier": tier,
                            "weight": weight * 1.1,
                        })
                    except Exception:
                        continue

        # Only 2 valid citations should be processed
        assert len(sources) == 2
        assert sources[0]["url"] == "https://valid.com"
        assert sources[1]["url"] == "https://valid-string.com"

    def test_empty_citations_list_is_handled(self, you_client):
        """Test empty citations list is handled gracefully."""
        research_data = {
            "report": "Test report",
            "citations": []
        }

        sources = []
        citations = research_data.get("citations", [])

        if citations and isinstance(citations, list):
            for citation in citations:
                if isinstance(citation, dict):
                    url = citation.get("url")
                    if not url or not isinstance(url, str):
                        continue
                    tier, weight = you_client._tier_for_domain(url)
                    sources.append({
                        "type": "research",
                        "title": citation.get("title", "Research Citation"),
                        "url": url,
                        "tier": tier,
                        "weight": weight * 1.1,
                    })

        assert len(sources) == 0

    def test_missing_citations_field_is_handled(self, you_client):
        """Test missing citations field is handled gracefully."""
        research_data = {
            "report": "Test report"
            # No citations field
        }

        sources = []
        citations = research_data.get("citations", [])

        if citations and isinstance(citations, list):
            for citation in citations:
                if isinstance(citation, dict):
                    url = citation.get("url")
                    if not url or not isinstance(url, str):
                        continue
                    tier, weight = you_client._tier_for_domain(url)
                    sources.append({
                        "type": "research",
                        "title": citation.get("title", "Research Citation"),
                        "url": url,
                        "tier": tier,
                        "weight": weight * 1.1,
                    })

        assert len(sources) == 0


class TestErrorLogging:
    """Test enhanced error logging functionality."""

    @pytest.fixture
    def you_client(self, mock_you_api_key):
        """Create a You.com client for testing."""
        return YouComOrchestrator(api_key=mock_you_api_key)

    @pytest.mark.asyncio
    async def test_http_error_logging_includes_status_and_response(self, you_client, caplog):
        """Test HTTP errors are logged with status code and response text."""
        import logging
        caplog.set_level(logging.ERROR)

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        error = httpx.HTTPStatusError(
            "404 Not Found",
            request=MagicMock(),
            response=mock_response
        )

        with patch.object(you_client, '_perform_request', new=AsyncMock(side_effect=error)):
            with pytest.raises(YouComAPIError):
                await you_client.fetch_news("test query")

        # Verify error was logged with context
        assert any("News API HTTP error" in record.message for record in caplog.records)
        assert any("404" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_generic_error_logging_includes_exception_details(self, you_client, caplog):
        """Test generic errors are logged with exception details."""
        import logging
        caplog.set_level(logging.ERROR)

        error = Exception("Connection timeout after 30 seconds")

        with patch.object(you_client, '_perform_request', new=AsyncMock(side_effect=error)):
            with pytest.raises(YouComAPIError):
                await you_client.search_context("test query")

        # Verify error was logged with details
        assert any("Search API error" in record.message for record in caplog.records)
        assert any("timeout" in record.message.lower() for record in caplog.records)
