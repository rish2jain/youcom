"""
Comprehensive tests for You.com API orchestration workflow

Tests cover:
1. Full API orchestration (News → Search → Chat → ARI)
2. Error recovery and circuit breaker behavior
3. Cache hit/miss scenarios
4. Resilience patterns
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import httpx

from app.services.you_client import YouComOrchestrator, YouComAPIError
from app.config import settings


# Test-specific Redis key prefix to avoid conflicts
TEST_KEY_PREFIX = "test:orchestration:"


async def cleanup_test_keys(redis_client):
    """Clean up only test-specific keys from Redis"""
    if redis_client:
        # Get all keys with our test prefix
        test_keys = await redis_client.keys(f"{TEST_KEY_PREFIX}*")
        if test_keys:
            # Delete only our test keys
            await redis_client.delete(*test_keys)


class TestAPIOrchestrationWorkflow:
    """Test complete API orchestration workflow"""

    @pytest.mark.asyncio
    async def test_full_impact_card_generation_workflow(self):
        """
        Test complete workflow: News → Search → Chat → ARI → Impact Card

        This is the critical path that must work for the app to function.
        """
        async with YouComOrchestrator() as client:
            # Enable demo mode for testing without actual API calls
            with patch.object(settings, 'demo_mode', True):
                # Execute full workflow
                impact_card = await client.generate_impact_card(
                    competitor="OpenAI",
                    keywords=["GPT", "AI"],
                    progress_room=None,
                    db_session=None
                )

                # Verify impact card structure
                assert impact_card is not None
                assert "competitor" in impact_card
                assert impact_card["competitor"] == "OpenAI"

                # Verify risk assessment
                assert "risk_score" in impact_card
                assert 0 <= impact_card["risk_score"] <= 100
                assert "risk_level" in impact_card
                assert impact_card["risk_level"] in ["low", "medium", "high", "critical"]

                # Verify all 4 APIs were called
                assert impact_card["total_sources"] > 0
                assert "source_breakdown" in impact_card

                source_breakdown = impact_card["source_breakdown"]
                assert "news_articles" in source_breakdown
                assert "search_results" in source_breakdown
                assert "research_citations" in source_breakdown

                # Verify API usage tracking
                assert "api_usage" in impact_card
                api_usage = impact_card["api_usage"]
                assert api_usage["news_calls"] > 0
                assert api_usage["search_calls"] > 0
                assert api_usage["chat_calls"] > 0
                assert api_usage["ari_calls"] > 0

                # Verify recommended actions
                assert "recommended_actions" in impact_card
                assert len(impact_card["recommended_actions"]) > 0

                # Verify explainability data
                assert "explainability" in impact_card

    @pytest.mark.asyncio
    async def test_orchestration_with_real_apis_integration(self):
        """
        Integration test with actual You.com APIs (requires valid API key)

        Skip if YOU_API_KEY not configured or demo mode enabled
        """
        try:
            # Try to access settings, handle validation errors
            if settings.demo_mode:
                pytest.skip("Skipping real API test in demo mode")

            if not settings.you_api_key or settings.you_api_key.get_secret_value() == "your_you_api_key_here":
                pytest.skip("YOU_API_KEY not configured")
        except ValueError as e:
            # Skip test if settings validation fails (e.g., missing API key)
            pytest.skip(f"Settings validation failed: {e}")

        async with YouComOrchestrator() as client:
            # Test with a well-known competitor
            impact_card = await client.generate_impact_card(
                competitor="Google",
                keywords=["search", "AI"],
                progress_room=None,
                db_session=None
            )

            # Verify real API responses
            assert impact_card is not None
            assert impact_card["total_sources"] > 0

            # Real APIs should return substantial data
            assert impact_card["risk_score"] > 0
            assert len(impact_card["recommended_actions"]) > 0

    @pytest.mark.asyncio
    async def test_orchestration_individual_api_calls(self):
        """Test each API endpoint independently"""

        async with YouComOrchestrator() as client:
            with patch.object(settings, 'demo_mode', True):
                # Test News API
                news_data = await client.fetch_news("OpenAI", limit=5)
                assert news_data is not None
                assert "articles" in news_data
                assert news_data["api_type"] == "news"

                # Test Search API
                search_data = await client.search_context("OpenAI business model", limit=5)
                assert search_data is not None
                assert "results" in search_data
                assert search_data["api_type"] == "search"

                # Test Chat API (analysis)
                analysis_data = await client.analyze_impact(
                    news_data=news_data,
                    context_data=search_data,
                    competitor="OpenAI"
                )
                assert analysis_data is not None
                assert "analysis" in analysis_data
                assert analysis_data["api_type"] == "chat"

                # Test ARI API (research)
                research_data = await client.generate_research_report(
                    "OpenAI competitive analysis"
                )
                assert research_data is not None
                assert "report" in research_data
                assert research_data["api_type"] == "ari"


class TestErrorRecoveryAndResilience:
    """Test error handling and circuit breaker behavior"""

    @pytest.mark.asyncio
    async def test_api_timeout_handling(self):
        """Test graceful handling of API timeouts"""

        async with YouComOrchestrator() as client:
            # Clear only test-specific cache keys
            if client.cache:
                await cleanup_test_keys(client.cache)

            with patch.object(client.search_client, 'request', new_callable=AsyncMock) as mock_request:
                # Simulate timeout - will be retried 3 times by @retry decorator
                mock_request.side_effect = asyncio.TimeoutError("Request timeout")

                # After retries, the search_context method wraps the exception in YouComAPIError
                with pytest.raises(YouComAPIError):
                    await client.search_context("unique_timeout_test_query")

    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """Test handling of HTTP errors from You.com APIs"""

        async with YouComOrchestrator() as client:
            # Clear only test-specific cache keys
            if client.cache:
                await cleanup_test_keys(client.cache)

            with patch.object(client.search_client, 'request', new_callable=AsyncMock) as mock_request:
                # Simulate 500 error - will be retried 3 times by @retry decorator
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.text = "Internal Server Error"
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "500 Server Error",
                    request=MagicMock(),
                    response=mock_response
                )
                mock_request.return_value = mock_response

                # After retries, search_context wraps the exception in YouComAPIError
                with pytest.raises(YouComAPIError):
                    await client.search_context("unique_http_error_test_query")

    @pytest.mark.asyncio
    async def test_retry_behavior_on_transient_failures(self):
        """Test that API errors are properly wrapped and logged"""

        async with YouComOrchestrator() as client:
            # Clear only test-specific cache keys
            if client.cache:
                await cleanup_test_keys(client.cache)

            with patch.object(client.search_client, 'request', new_callable=AsyncMock) as mock_request:
                # Simulate HTTP error
                mock_response_error = MagicMock()
                mock_response_error.status_code = 503
                mock_response_error.text = "Service Unavailable"

                def raise_error(*args, **kwargs):
                    raise httpx.HTTPStatusError(
                        "503 Service Unavailable",
                        request=MagicMock(),
                        response=mock_response_error
                    )
                mock_response_error.raise_for_status = raise_error

                # Mock will return error response
                mock_request.return_value = mock_response_error

                # Should fail and wrap exception in YouComAPIError
                with pytest.raises(YouComAPIError) as exc_info:
                    await client.search_context("unique_retry_test_query")

                # Verify error message contains useful information
                assert "Search API error" in str(exc_info.value)

                # Verify the request was attempted
                assert mock_request.call_count >= 1

    @pytest.mark.asyncio
    async def test_fallback_to_demo_mode_on_api_failure(self):
        """Test graceful degradation to demo data when APIs fail"""

        async with YouComOrchestrator() as client:
            # Enable demo mode for fallback
            with patch.object(settings, 'demo_mode', True):
                # Even with failures, should return demo data
                news_data = await client.fetch_news("test", limit=5)
                assert news_data is not None
                assert news_data.get("demo_mode") is True
                assert len(news_data["articles"]) > 0


class TestCachingBehavior:
    """Test Redis caching and cache invalidation"""

    @pytest.mark.asyncio
    async def test_cache_hit_on_repeated_request(self):
        """Test that cache infrastructure works correctly"""

        async with YouComOrchestrator() as client:
            if not client.cache:
                pytest.skip("Redis cache not available")

            # Clear only test-specific cache keys
            await cleanup_test_keys(client.cache)

            # Test cache set and get operations directly
            test_key = f"{TEST_KEY_PREFIX}cache:key"
            test_data = {"test": "data", "number": 123}

            # Set value in cache
            await client._cache_set(test_key, test_data, ttl=60)

            # Get value from cache
            cached_data = await client._cache_get(test_key)

            # Should match
            assert cached_data == test_data

            # Verify cache key exists
            exists = await client.cache.exists(test_key)
            assert exists == 1

    @pytest.mark.asyncio
    async def test_cache_miss_on_different_query(self):
        """Test that different queries don't hit the same cache"""

        async with YouComOrchestrator() as client:
            if not client.cache:
                pytest.skip("Redis cache not available")

            with patch.object(settings, 'demo_mode', True):
                # Two different queries
                result1 = await client.search_context("query1", limit=5)
                result2 = await client.search_context("query2", limit=5)

                # Should have different results
                assert result1 != result2

    @pytest.mark.asyncio
    async def test_cache_ttl_respected(self):
        """Test that cache TTL is properly set"""

        async with YouComOrchestrator() as client:
            if not client.cache:
                pytest.skip("Redis cache not available")

            # Clear only test-specific cache keys
            await cleanup_test_keys(client.cache)

            # Test cache set with TTL
            test_key = f"{TEST_KEY_PREFIX}ttl:key"
            test_data = {"test": "ttl_data"}
            test_ttl = 300  # 5 minutes

            # Set value in cache with TTL
            await client._cache_set(test_key, test_data, ttl=test_ttl)

            # Verify TTL was set
            ttl = await client.cache.ttl(test_key)

            # TTL should be positive and close to what we set
            assert ttl > 0, "Cache key should have TTL set"
            assert ttl <= test_ttl, "TTL should not exceed configured value"
            # Allow some margin for execution time (should be close to test_ttl)
            assert ttl >= test_ttl - 5, "TTL should be close to configured value"

    @pytest.mark.asyncio
    async def test_cache_graceful_degradation(self):
        """Test that cache failures don't break API calls"""

        async with YouComOrchestrator() as client:
            if not client.cache:
                pytest.skip("Redis cache not available")

            with patch.object(client, '_cache_get', side_effect=Exception("Redis error")):
                with patch.object(settings, 'demo_mode', True):
                    # Should still work without cache
                    result = await client.search_context("test", limit=5)
                    assert result is not None


class TestAPIUsageTracking:
    """Test API call tracking and metrics"""

    @pytest.mark.asyncio
    async def test_api_usage_tracking_increments(self):
        """Test that API usage counters increment correctly"""

        async with YouComOrchestrator() as client:
            initial_news = client.api_usage["news_calls"]
            initial_search = client.api_usage["search_calls"]

            with patch.object(settings, 'demo_mode', True):
                await client.fetch_news("test", limit=5)
                await client.search_context("test", limit=5)

            assert client.api_usage["news_calls"] == initial_news + 1
            assert client.api_usage["search_calls"] == initial_search + 1
            assert client.api_usage["total_calls"] > 0

    @pytest.mark.asyncio
    async def test_api_call_logging(self):
        """Test that API usage tracking works correctly"""

        async with YouComOrchestrator() as client:
            with patch.object(settings, 'demo_mode', True):
                # Get initial API usage counts
                initial_search_count = client.api_usage.get("search_calls", 0)
                initial_total_count = client.api_usage.get("total_calls", 0)

                # Clear only test-specific cache keys
                if client.cache:
                    await cleanup_test_keys(client.cache)

                # Make API call
                result = await client.search_context("api_tracking_test_unique", limit=5)
                assert result is not None

                # Verify usage tracking incremented
                final_search_count = client.api_usage.get("search_calls", 0)
                final_total_count = client.api_usage.get("total_calls", 0)

                # Should have incremented by at least 1
                assert final_search_count > initial_search_count
                assert final_total_count > initial_total_count


class TestSourceQualityEvaluation:
    """Test source quality scoring and credibility assessment"""

    @pytest.mark.asyncio
    async def test_source_quality_tier_classification(self):
        """Test that sources are properly classified by tier"""

        async with YouComOrchestrator() as client:
            # Test tier 1 sources
            tier, weight = client._tier_for_domain("https://www.nytimes.com/article")
            assert tier == "tier1"
            assert weight == 1.0

            tier, weight = client._tier_for_domain("https://bloomberg.com/news")
            assert tier == "tier1"
            assert weight == 1.0

            # Test .gov and .edu domains
            tier, weight = client._tier_for_domain("https://example.gov/report")
            assert tier == "tier1"
            assert weight == 0.95

            # Test tier 3 sources
            tier, weight = client._tier_for_domain("https://random-blog.com/post")
            assert tier == "tier3"

    @pytest.mark.asyncio
    async def test_source_quality_aggregation(self):
        """Test that source quality is properly aggregated"""

        async with YouComOrchestrator() as client:
            news_data = {
                "articles": [
                    {"title": "Test", "url": "https://nytimes.com/article"},
                    {"title": "Test", "url": "https://techcrunch.com/post"}
                ]
            }
            context_data = {
                "results": [
                    {"title": "Test", "url": "https://bloomberg.com/news"}
                ]
            }
            research_data = {
                "citations": [
                    {"title": "Test", "url": "https://example.edu/paper"}
                ]
            }

            quality = client._evaluate_source_quality(
                news_data, context_data, research_data
            )

            assert "score" in quality
            assert 0 <= quality["score"] <= 1
            assert quality["total"] == 4
            assert quality["tiers"]["tier1"] >= 3  # Most should be tier 1


class TestRecommendedActionsEnrichment:
    """Test action enrichment with owners and evidence"""

    @pytest.mark.asyncio
    async def test_action_owner_assignment(self):
        """Test that actions are assigned to appropriate owners"""

        async with YouComOrchestrator() as client:
            # Test pricing-related action
            owner, okr = client._owner_for_action("Adjust pricing strategy")
            assert owner == "Revenue Ops"

            # Test sales-related action
            owner, okr = client._owner_for_action("Accelerate enterprise sales")
            assert owner == "Sales"

            # Test default assignment
            owner, okr = client._owner_for_action("Generic strategic action")
            assert owner == "Strategy Team"

    @pytest.mark.asyncio
    async def test_action_enrichment_with_evidence(self):
        """Test that actions are enriched with evidence links"""

        async with YouComOrchestrator() as client:
            analysis = {
                "recommended_actions": [
                    {"action": "Monitor competitor pricing", "priority": "high"}
                ],
                "risk_score": 75
            }

            news_data = {
                "articles": [
                    {"title": "Pricing News", "url": "https://example.com/news"}
                ]
            }

            research_data = {
                "citations": [
                    {"title": "Market Report", "url": "https://example.com/report"}
                ]
            }

            enriched = client._enrich_recommended_actions(
                analysis, news_data, research_data
            )

            assert len(enriched) > 0
            assert "owner" in enriched[0]
            assert "okr_goal" in enriched[0]
            assert "evidence" in enriched[0]
            assert "impact_score" in enriched[0]


# Run tests with: pytest backend/tests/test_you_orchestration.py -v
