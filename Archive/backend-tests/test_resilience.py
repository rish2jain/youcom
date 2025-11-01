#!/usr/bin/env python3
"""
Quick test script for resilient You.com API client.
Based on Discord insights - tests circuit breakers, rate limiting, and fallbacks.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.resilient_you_client import ResilientYouComOrchestrator
from app.config.resilience import resilience_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_individual_apis():
    """Test each API individually with resilience patterns"""
    
    logger.info("🧪 Testing individual APIs with resilience patterns")
    
    async with ResilientYouComOrchestrator() as client:
        
        # Test 1: News API with query optimization
        logger.info("\n📰 Testing News API...")
        try:
            news_result = await client.fetch_news("OpenAI ChatGPT announcement")
            logger.info(f"✅ News API: {len(news_result.get('articles', []))} articles")
            if news_result.get("query_optimization"):
                logger.info(f"🔧 Query optimized: {news_result['query_optimization']}")
        except Exception as e:
            logger.error(f"❌ News API failed: {e}")
        
        # Test 2: Search API
        logger.info("\n🔍 Testing Search API...")
        try:
            search_result = await client.search_context("competitive analysis OpenAI")
            logger.info(f"✅ Search API: {len(search_result.get('results', []))} results")
        except Exception as e:
            logger.error(f"❌ Search API failed: {e}")
        
        # Test 3: Chat API (Custom Agents) - known to hang
        logger.info("\n🤖 Testing Chat API (with timeout protection)...")
        try:
            chat_result = await client.analyze_impact(
                {"articles": [{"title": "OpenAI launches new model", "url": "https://example.com"}]},
                {"results": [{"title": "OpenAI overview", "url": "https://example.com"}]},
                "OpenAI"
            )
            logger.info(f"✅ Chat API: Risk score {chat_result.get('analysis', {}).get('risk_score', 'N/A')}")
        except Exception as e:
            logger.error(f"❌ Chat API failed: {e}")
        
        # Test 4: ARI API (Express Agent)
        logger.info("\n📊 Testing ARI API...")
        try:
            ari_result = await client.generate_research_report("OpenAI competitive analysis")
            logger.info(f"✅ ARI API: {len(ari_result.get('citations', []))} citations")
        except Exception as e:
            logger.error(f"❌ ARI API failed: {e}")
        
        # Show circuit breaker status
        health_status = client.get_health_status()
        logger.info("\n🔧 Circuit Breaker Status:")
        for api, status in health_status["circuit_breakers"].items():
            logger.info(f"  {api}: {status['state']} (failures: {status['failure_count']})")

async def test_rate_limiting():
    """Test rate limiting with rapid requests"""
    
    logger.info("\n⏱️ Testing rate limiting with rapid requests")
    
    async with ResilientYouComOrchestrator() as client:
        
        # Make rapid requests to trigger rate limiting
        for i in range(3):
            logger.info(f"Request {i+1}/3...")
            try:
                result = await client.search_context(f"test query {i}")
                logger.info(f"✅ Request {i+1} succeeded")
            except Exception as e:
                logger.error(f"❌ Request {i+1} failed: {e}")

async def test_full_workflow():
    """Test complete impact card generation with resilience"""
    
    logger.info("\n🚀 Testing full workflow with resilience")
    
    async with ResilientYouComOrchestrator() as client:
        try:
            impact_card = await client.generate_impact_card(
                competitor="OpenAI",
                keywords=["ChatGPT", "GPT-4"]
            )
            
            logger.info(f"✅ Impact Card Generated:")
            logger.info(f"  Competitor: {impact_card['competitor']}")
            logger.info(f"  Risk Score: {impact_card['risk_score']}")
            logger.info(f"  Processing Time: {impact_card['processing_time']}")
            logger.info(f"  API Status: {impact_card['api_status']}")
            logger.info(f"  Resilience Score: {impact_card['resilience_score']}")
            logger.info(f"  Requires Review: {impact_card['requires_review']}")
            
        except Exception as e:
            logger.error(f"❌ Full workflow failed: {e}")

async def test_circuit_breaker_simulation():
    """Simulate circuit breaker behavior"""
    
    logger.info("\n🔴 Testing circuit breaker simulation")
    
    async with ResilientYouComOrchestrator() as client:
        
        # Get a circuit breaker and simulate failures
        news_cb = client.circuit_breakers["news"]
        
        logger.info(f"Initial state: {news_cb.state.state.value}")
        
        # Simulate failures
        for i in range(4):
            news_cb.record_failure()
            logger.info(f"After failure {i+1}: {news_cb.state.state.value} (count: {news_cb.state.failure_count})")
        
        # Test if circuit is open
        can_execute = news_cb.can_execute()
        logger.info(f"Can execute after failures: {can_execute}")
        
        # Simulate recovery
        if news_cb.state.state.value == "open":
            logger.info("Simulating recovery...")
            # Fast-forward time simulation
            news_cb.state.last_failure_time = news_cb.state.last_failure_time.replace(
                year=news_cb.state.last_failure_time.year - 1
            )
            
            can_execute = news_cb.can_execute()
            logger.info(f"Can execute after time passage: {can_execute}")
            logger.info(f"State after reset attempt: {news_cb.state.state.value}")

async def main():
    """Run all resilience tests"""
    
    logger.info("🎯 Starting You.com API Resilience Tests")
    logger.info(f"Hackathon Mode: {resilience_settings.hackathon_mode}")
    logger.info(f"Circuit Breakers: {resilience_settings.enable_circuit_breakers}")
    logger.info(f"Rate Limiting: {resilience_settings.enable_rate_limiting}")
    logger.info(f"Query Optimization: {resilience_settings.enable_query_optimization}")
    logger.info(f"Fallback Data: {resilience_settings.enable_fallback_data}")
    
    try:
        # Run tests
        await test_individual_apis()
        await test_rate_limiting()
        await test_circuit_breaker_simulation()
        await test_full_workflow()
        
        logger.info("\n✅ All resilience tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())