"""
Enhanced You.com API client with resilience patterns based on Discord hackathon insights.
Implements circuit breakers, query optimization, and robust error handling.
"""

import asyncio
import json
import logging
import time
from contextlib import suppress
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings
from app.services.you_client import YouComOrchestrator, YouComAPIError

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit breaker tripped
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 2  # For half-open state

@dataclass
class CircuitBreakerState:
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None

class APICircuitBreaker:
    """Circuit breaker for individual API endpoints"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState()
        
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state.state == CircuitState.CLOSED:
            return True
            
        if self.state.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state.state = CircuitState.HALF_OPEN
                self.state.success_count = 0
                logger.info(f"🔄 Circuit breaker {self.name} moving to HALF_OPEN")
                return True
            return False
            
        # HALF_OPEN state
        return True
    
    def record_success(self):
        """Record successful API call"""
        self.state.last_success_time = datetime.now(timezone.utc)
        
        if self.state.state == CircuitState.HALF_OPEN:
            self.state.success_count += 1
            if self.state.success_count >= self.config.success_threshold:
                self.state.state = CircuitState.CLOSED
                self.state.failure_count = 0
                logger.info(f"✅ Circuit breaker {self.name} CLOSED - service recovered")
        else:
            self.state.failure_count = 0
    
    def record_failure(self):
        """Record failed API call"""
        self.state.last_failure_time = datetime.now(timezone.utc)
        self.state.failure_count += 1
        
        if self.state.failure_count >= self.config.failure_threshold:
            self.state.state = CircuitState.OPEN
            logger.warning(f"🚨 Circuit breaker {self.name} OPEN - service degraded")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.state.last_failure_time:
            return True
        
        elapsed = datetime.now(timezone.utc) - self.state.last_failure_time
        return elapsed.total_seconds() >= self.config.recovery_timeout

class QueryOptimizer:
    """Optimizes queries based on Discord insights about boolean operators"""
    
    @staticmethod
    def simplify_query(query: str) -> List[str]:
        """Break complex queries into simpler sub-queries"""
        # Remove problematic boolean operators that don't work well
        simplified = query.replace(" AND ", " ").replace(" OR ", " ")
        
        # Split into meaningful chunks
        words = simplified.split()
        if len(words) <= 3:
            return [query]
        
        # Create sub-queries for better reliability
        sub_queries = []
        
        # Main query with key terms
        key_terms = words[:3]
        sub_queries.append(" ".join(key_terms))
        
        # Additional context queries
        if len(words) > 3:
            context_terms = words[3:6]
            sub_queries.append(" ".join(context_terms))
        
        return sub_queries
    
    @staticmethod
    def optimize_for_api(query: str, api_type: str) -> str:
        """Optimize query for specific API based on known limitations"""
        if api_type == "news":
            # News API works better with specific terms
            return query.replace(" company", "").replace(" business", "")
        
        if api_type == "search":
            # Search API handles longer queries better
            return query
        
        if api_type == "chat":
            # Custom agents prefer structured prompts
            return f"Analyze: {query}"
        
        return query

class ResilientYouComOrchestrator(YouComOrchestrator):
    """Enhanced You.com client with resilience patterns"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        
        # Initialize circuit breakers for each API
        self.circuit_breakers = {
            "news": APICircuitBreaker("news", CircuitBreakerConfig(
                failure_threshold=3,  # News API is more sensitive
                recovery_timeout=30
            )),
            "search": APICircuitBreaker("search", CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60
            )),
            "chat": APICircuitBreaker("chat", CircuitBreakerConfig(
                failure_threshold=2,  # Custom agents hang frequently
                recovery_timeout=120  # Longer recovery for agent issues
            )),
            "ari": APICircuitBreaker("ari", CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=180  # ARI needs more time
            ))
        }
        
        self.query_optimizer = QueryOptimizer()
        
        # Rate limiting state
        self.last_request_time = {}
        self.min_request_interval = {
            "news": 2.0,    # 2 seconds between news requests
            "search": 1.5,  # 1.5 seconds between search requests
            "chat": 5.0,    # 5 seconds between chat requests (they hang)
            "ari": 10.0     # 10 seconds between ARI requests
        }
    
    async def _wait_for_rate_limit(self, api_type: str):
        """Implement aggressive rate limiting based on Discord insights"""
        last_time = self.last_request_time.get(api_type, 0)
        min_interval = self.min_request_interval.get(api_type, 1.0)
        
        elapsed = time.time() - last_time
        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            logger.info(f"⏱️ Rate limiting {api_type}: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        
        self.last_request_time[api_type] = time.time()
    
    async def _execute_with_circuit_breaker(
        self,
        api_type: str,
        operation,
        *args,
        **kwargs
    ):
        """Execute API call with circuit breaker protection"""
        circuit_breaker = self.circuit_breakers[api_type]
        
        if not circuit_breaker.can_execute():
            logger.warning(f"🚫 Circuit breaker {api_type} is OPEN - using fallback")
            return await self._get_fallback_data(api_type, *args, **kwargs)
        
        # Apply rate limiting
        await self._wait_for_rate_limit(api_type)
        
        try:
            result = await operation(*args, **kwargs)
            circuit_breaker.record_success()
            return result
            
        except Exception as e:
            circuit_breaker.record_failure()
            logger.error(f"❌ {api_type} API failed: {str(e)}")
            
            # Return fallback data instead of failing completely
            return await self._get_fallback_data(api_type, *args, **kwargs)
    
    async def _get_fallback_data(self, api_type: str, *args, **kwargs) -> Dict[str, Any]:
        """Get fallback data when APIs fail"""
        if api_type == "news":
            query = args[0] if args else "fallback"
            limit = args[1] if len(args) > 1 else 10
            return self._get_demo_news_data(query, limit)
        
        elif api_type == "search":
            query = args[0] if args else "fallback"
            limit = args[1] if len(args) > 1 else 10
            return self._get_demo_search_data(query, limit)
        
        elif api_type == "chat":
            competitor = args[2] if len(args) > 2 else "Unknown"
            news_data = args[0] if args else {}
            context_data = args[1] if len(args) > 1 else {}
            return self._get_demo_analysis_data(competitor, news_data, context_data)
        
        elif api_type == "ari":
            query = args[0] if args else "fallback research"
            return self._get_demo_research_data(query)
        
        return {"error": "fallback_data", "api_type": api_type}
    
    async def fetch_news(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Enhanced news fetching with query optimization and resilience"""
        
        # Optimize query for news API
        optimized_query = self.query_optimizer.optimize_for_api(query, "news")
        
        # Try simplified queries if main query fails
        sub_queries = self.query_optimizer.simplify_query(optimized_query)
        
        for attempt, sub_query in enumerate(sub_queries):
            try:
                logger.info(f"📰 News API attempt {attempt + 1}: {sub_query}")
                
                result = await self._execute_with_circuit_breaker(
                    "news",
                    super().fetch_news,
                    sub_query,
                    limit
                )
                
                # If we got results, return them
                if result.get("articles"):
                    result["query_optimization"] = {
                        "original_query": query,
                        "optimized_query": optimized_query,
                        "successful_query": sub_query,
                        "attempt": attempt + 1
                    }
                    return result
                    
            except Exception as e:
                logger.warning(f"News API sub-query failed: {sub_query} - {str(e)}")
                continue
        
        # All queries failed, return fallback
        logger.warning("All news queries failed, using fallback data")
        return await self._get_fallback_data("news", query, limit)
    
    async def search_context(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Enhanced search with query optimization and resilience"""
        
        optimized_query = self.query_optimizer.optimize_for_api(query, "search")
        
        return await self._execute_with_circuit_breaker(
            "search",
            super().search_context,
            optimized_query,
            limit
        )
    
    async def analyze_impact(self, news_data: Dict, context_data: Dict, competitor: str) -> Dict[str, Any]:
        """Enhanced impact analysis with timeout and fallback"""
        
        # Custom agents are known to hang - implement timeout
        try:
            result = await asyncio.wait_for(
                self._execute_with_circuit_breaker(
                    "chat",
                    super().analyze_impact,
                    news_data,
                    context_data,
                    competitor
                ),
                timeout=30.0  # 30 second timeout for custom agents
            )
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"🕐 Chat API timeout for {competitor} - using fallback")
            return await self._get_fallback_data("chat", news_data, context_data, competitor)
    
    async def generate_research_report(self, query: str) -> Dict[str, Any]:
        """Enhanced research report generation with resilience"""
        
        optimized_query = self.query_optimizer.optimize_for_api(query, "ari")
        
        # ARI/Express agent needs longer timeout
        try:
            result = await asyncio.wait_for(
                self._execute_with_circuit_breaker(
                    "ari",
                    super().generate_research_report,
                    optimized_query
                ),
                timeout=60.0  # 60 second timeout for ARI
            )
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"🕐 ARI API timeout for {query} - using fallback")
            return await self._get_fallback_data("ari", query)
    
    async def generate_impact_card(
        self,
        competitor: str,
        keywords: Optional[List[str]] = None,
        *,
        progress_room: Optional[str] = None,
        db_session=None,
    ) -> Dict[str, Any]:
        """Enhanced impact card generation with comprehensive error handling"""
        
        logger.info(f"🚀 Starting resilient Impact Card generation for {competitor}")
        start_time = time.perf_counter()
        
        # Track which APIs succeeded/failed
        api_status = {
            "news": "pending",
            "search": "pending", 
            "chat": "pending",
            "ari": "pending"
        }
        
        try:
            # Step 1: News API with resilience
            logger.info("📰 Step 1: Fetching news with resilience...")
            news_query = f"{competitor} announcement launch product"
            if keywords:
                news_query += " " + " ".join(keywords)
            
            news_data = await self.fetch_news(news_query)
            api_status["news"] = "success" if not news_data.get("demo_mode") else "fallback"
            
            await self._notify_progress(
                competitor,
                "news",
                progress_room=progress_room,
                articles=len(news_data.get("articles", [])),
                status=api_status["news"]
            )
            
            # Step 2: Search API with resilience
            logger.info("🔍 Step 2: Searching context with resilience...")
            search_query = f"{competitor} business model strategy competitive analysis"
            context_data = await self.search_context(search_query)
            api_status["search"] = "success" if not context_data.get("demo_mode") else "fallback"
            
            await self._notify_progress(
                competitor,
                "search",
                progress_room=progress_room,
                results=context_data.get("total_count", 0),
                status=api_status["search"]
            )
            
            # Step 3: Chat API with timeout protection
            logger.info("🤖 Step 3: Analyzing impact with timeout protection...")
            analysis_data = await self.analyze_impact(news_data, context_data, competitor)
            api_status["chat"] = "success" if not analysis_data.get("demo_mode") else "fallback"
            
            await self._notify_progress(
                competitor,
                "analysis",
                progress_room=progress_room,
                risk_score=analysis_data.get("analysis", {}).get("risk_score"),
                status=api_status["chat"]
            )
            
            # Step 4: ARI API with extended timeout
            logger.info("📊 Step 4: Generating research with extended timeout...")
            research_query = f"Competitive analysis of {competitor} strategic positioning market impact"
            research_data = await self.generate_research_report(research_query)
            api_status["ari"] = "success" if not research_data.get("demo_mode") else "fallback"
            
            await self._notify_progress(
                competitor,
                "research",
                progress_room=progress_room,
                citations=len(research_data.get("citations", [])),
                status=api_status["ari"]
            )
            
            # Step 5: Assemble with status information
            logger.info("🎯 Step 5: Assembling resilient Impact Card...")
            impact_card = self.assemble_impact_card(
                news_data,
                context_data,
                analysis_data,
                research_data,
                competitor,
            )
            
            # Add resilience metadata
            elapsed = time.perf_counter() - start_time
            impact_card["processing_time"] = f"{elapsed:.2f}s"
            impact_card["api_status"] = api_status
            impact_card["resilience_score"] = self._calculate_resilience_score(api_status)
            impact_card["circuit_breaker_status"] = {
                name: cb.state.state.value 
                for name, cb in self.circuit_breakers.items()
            }
            
            # Determine if manual review is needed
            success_count = sum(1 for status in api_status.values() if status == "success")
            impact_card["requires_review"] = (
                success_count < 2 or  # Less than 2 APIs succeeded
                impact_card["risk_score"] >= 85 or
                impact_card.get("credibility_score", 1.0) < 0.8
            )
            
            logger.info(f"✅ Resilient Impact Card generated for {competitor}")
            logger.info(f"📊 API Status: {api_status}")
            
            return impact_card
            
        except Exception as e:
            logger.error(f"❌ Critical error in resilient impact card generation: {str(e)}")
            
            # Return minimal fallback card
            return {
                "competitor": competitor,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "risk_score": 50,
                "risk_level": "medium",
                "confidence_score": 30,
                "error": "Critical system error - manual review required",
                "api_status": api_status,
                "requires_review": True,
                "processing_time": f"{time.perf_counter() - start_time:.2f}s"
            }
    
    def _calculate_resilience_score(self, api_status: Dict[str, str]) -> float:
        """Calculate resilience score based on API success rates"""
        weights = {"news": 0.2, "search": 0.2, "chat": 0.4, "ari": 0.2}
        score = 0.0
        
        for api, status in api_status.items():
            if status == "success":
                score += weights.get(api, 0.25)
            elif status == "fallback":
                score += weights.get(api, 0.25) * 0.5  # Half credit for fallback
        
        return round(score, 2)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of all APIs"""
        return {
            "circuit_breakers": {
                name: {
                    "state": cb.state.state.value,
                    "failure_count": cb.state.failure_count,
                    "last_failure": cb.state.last_failure_time.isoformat() if cb.state.last_failure_time else None,
                    "last_success": cb.state.last_success_time.isoformat() if cb.state.last_success_time else None
                }
                for name, cb in self.circuit_breakers.items()
            },
            "rate_limiting": {
                api: {
                    "last_request": self.last_request_time.get(api, 0),
                    "min_interval": interval
                }
                for api, interval in self.min_request_interval.items()
            }
        }

async def get_resilient_you_client():
    """FastAPI dependency for resilient You.com client"""
    async with ResilientYouComOrchestrator() as client:
        yield client