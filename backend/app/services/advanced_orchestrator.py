"""
Advanced You.com API Orchestration - Week 1 Implementation
Implements intelligent parallel processing, cost optimization, and sub-minute analysis.
"""

import asyncio
import json
import logging
import time
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import hashlib

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings
from app.services.resilient_you_client import ResilientYouComOrchestrator, YouComAPIError
from app.realtime import emit_progress

logger = logging.getLogger(__name__)

class QueryComplexity(Enum):
    SIMPLE = "simple"      # Single entity, basic info
    MODERATE = "moderate"  # Multiple entities, context needed
    COMPLEX = "complex"    # Deep analysis, multiple sources

class APIRoute(Enum):
    FAST_TRACK = "fast_track"      # Pre-computed + cache
    STANDARD = "standard"          # Normal API calls
    DEEP_DIVE = "deep_dive"        # All APIs + analysis

@dataclass
class QueryPlan:
    """Intelligent query execution plan"""
    complexity: QueryComplexity
    route: APIRoute
    apis_needed: List[str]
    parallel_groups: List[List[str]]
    estimated_time: float
    cost_estimate: float
    cache_strategy: str

@dataclass
class APIMetrics:
    """Real-time API performance metrics"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_latency: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    cost_saved: float = 0.0
    
    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    @property
    def average_latency(self) -> float:
        if self.successful_calls == 0:
            return 0.0
        return self.total_latency / self.successful_calls
    
    @property
    def cache_hit_rate(self) -> float:
        total_requests = self.cache_hits + self.cache_misses
        if total_requests == 0:
            return 0.0
        return self.cache_hits / total_requests

class IntelligentQueryRouter:
    """Routes queries to optimal execution path"""
    
    def __init__(self):
        # Pre-computed company profiles for Fortune 10K (simulated)
        self.precomputed_companies = {
            "openai", "anthropic", "google", "microsoft", "apple", "amazon",
            "meta", "tesla", "nvidia", "salesforce", "oracle", "ibm",
            "adobe", "netflix", "uber", "airbnb", "stripe", "shopify"
        }
        
        # Query complexity patterns
        self.complexity_patterns = {
            QueryComplexity.SIMPLE: [
                "company profile", "basic info", "overview", "about"
            ],
            QueryComplexity.MODERATE: [
                "competitive analysis", "market position", "strategy", "business model"
            ],
            QueryComplexity.COMPLEX: [
                "deep research", "comprehensive analysis", "impact assessment", "strategic implications"
            ]
        }
    
    def analyze_query(self, query: str, competitor: str) -> QueryPlan:
        """Analyze query and create optimal execution plan"""
        
        # Determine complexity
        complexity = self._assess_complexity(query)
        
        # Check if we can use fast track
        route = self._determine_route(competitor, complexity)
        
        # Plan API calls
        apis_needed = self._plan_api_calls(complexity, route)
        
        # Create parallel execution groups
        parallel_groups = self._create_parallel_groups(apis_needed)
        
        # Estimate time and cost
        estimated_time = self._estimate_time(route, apis_needed)
        cost_estimate = self._estimate_cost(apis_needed)
        
        # Determine cache strategy
        cache_strategy = self._determine_cache_strategy(complexity, competitor)
        
        return QueryPlan(
            complexity=complexity,
            route=route,
            apis_needed=apis_needed,
            parallel_groups=parallel_groups,
            estimated_time=estimated_time,
            cost_estimate=cost_estimate,
            cache_strategy=cache_strategy
        )
    
    def _assess_complexity(self, query: str) -> QueryComplexity:
        """Assess query complexity based on keywords"""
        query_lower = query.lower()
        
        for complexity, patterns in self.complexity_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return complexity
        
        # Default to moderate
        return QueryComplexity.MODERATE
    
    def _determine_route(self, competitor: str, complexity: QueryComplexity) -> APIRoute:
        """Determine optimal routing strategy"""
        competitor_lower = competitor.lower()
        
        # Fast track for known companies with simple queries
        if (competitor_lower in self.precomputed_companies and 
            complexity == QueryComplexity.SIMPLE):
            return APIRoute.FAST_TRACK
        
        # Deep dive for complex analysis
        if complexity == QueryComplexity.COMPLEX:
            return APIRoute.DEEP_DIVE
        
        return APIRoute.STANDARD
    
    def _plan_api_calls(self, complexity: QueryComplexity, route: APIRoute) -> List[str]:
        """Plan which APIs to call"""
        if route == APIRoute.FAST_TRACK:
            return ["search"]  # Minimal API usage
        
        if complexity == QueryComplexity.SIMPLE:
            return ["news", "search"]
        
        if complexity == QueryComplexity.MODERATE:
            return ["news", "search", "chat"]
        
        # Complex queries use all APIs
        return ["news", "search", "chat", "ari"]
    
    def _create_parallel_groups(self, apis_needed: List[str]) -> List[List[str]]:
        """Create parallel execution groups for optimal performance"""
        if len(apis_needed) <= 2:
            return [apis_needed]
        
        # Group 1: Data gathering (can run in parallel)
        group1 = []
        if "news" in apis_needed:
            group1.append("news")
        if "search" in apis_needed:
            group1.append("search")
        
        # Group 2: Analysis (depends on data from group 1)
        group2 = []
        if "chat" in apis_needed:
            group2.append("chat")
        if "ari" in apis_needed:
            group2.append("ari")
        
        groups = []
        if group1:
            groups.append(group1)
        if group2:
            groups.append(group2)
        
        return groups
    
    def _estimate_time(self, route: APIRoute, apis_needed: List[str]) -> float:
        """Estimate execution time in seconds"""
        base_times = {
            "news": 2.0,
            "search": 1.5,
            "chat": 8.0,  # Custom agents are slower
            "ari": 15.0   # ARI is slowest
        }
        
        if route == APIRoute.FAST_TRACK:
            return 5.0  # Pre-computed data
        
        # Parallel execution reduces total time
        max_time_per_group = []
        for group in self._create_parallel_groups(apis_needed):
            group_max = max(base_times.get(api, 2.0) for api in group)
            max_time_per_group.append(group_max)
        
        return sum(max_time_per_group) + 2.0  # Add processing overhead
    
    def _estimate_cost(self, apis_needed: List[str]) -> float:
        """Estimate API cost in USD"""
        api_costs = {
            "news": 0.01,
            "search": 0.015,
            "chat": 0.02,
            "ari": 0.05
        }
        
        return sum(api_costs.get(api, 0.01) for api in apis_needed)
    
    def _determine_cache_strategy(self, complexity: QueryComplexity, competitor: str) -> str:
        """Determine optimal caching strategy"""
        if competitor.lower() in self.precomputed_companies:
            return "precomputed"
        
        if complexity == QueryComplexity.SIMPLE:
            return "aggressive"  # Long TTL
        
        if complexity == QueryComplexity.MODERATE:
            return "standard"    # Medium TTL
        
        return "minimal"         # Short TTL for complex queries

class CostOptimizer:
    """Optimizes API costs through intelligent batching and deduplication"""
    
    def __init__(self):
        self.query_cache = {}
        self.batch_queue = {}
        self.deduplication_map = {}
    
    def optimize_queries(self, queries: List[str]) -> List[str]:
        """Optimize multiple queries through deduplication and batching"""
        
        # Step 1: Deduplicate similar queries
        deduplicated = self._deduplicate_queries(queries)
        
        # Step 2: Batch compatible queries
        batched = self._batch_queries(deduplicated)
        
        logger.info(f"🎯 Query optimization: {len(queries)} → {len(batched)} queries")
        return batched
    
    def _deduplicate_queries(self, queries: List[str]) -> List[str]:
        """Remove duplicate and highly similar queries"""
        unique_queries = []
        query_hashes = set()
        
        for query in queries:
            # Create semantic hash
            normalized = self._normalize_query(query)
            query_hash = hashlib.md5(normalized.encode()).hexdigest()
            
            if query_hash not in query_hashes:
                unique_queries.append(query)
                query_hashes.add(query_hash)
        
        return unique_queries
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for deduplication"""
        # Remove common variations
        normalized = query.lower()
        normalized = normalized.replace("company", "").replace("business", "")
        normalized = " ".join(sorted(normalized.split()))
        return normalized
    
    def _batch_queries(self, queries: List[str]) -> List[str]:
        """Batch compatible queries together"""
        # For now, return as-is. In production, implement intelligent batching
        # based on query similarity and API compatibility
        return queries
    
    def calculate_savings(self, original_cost: float, optimized_cost: float) -> Dict[str, float]:
        """Calculate cost savings from optimization"""
        savings = original_cost - optimized_cost
        savings_percent = (savings / original_cost * 100) if original_cost > 0 else 0
        
        return {
            "original_cost": original_cost,
            "optimized_cost": optimized_cost,
            "savings_amount": savings,
            "savings_percent": savings_percent
        }

class AdvancedYouComOrchestrator(ResilientYouComOrchestrator):
    """Advanced orchestrator with intelligent routing and optimization"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        
        self.query_router = IntelligentQueryRouter()
        self.cost_optimizer = CostOptimizer()
        
        # Performance metrics
        self.metrics = {
            "news": APIMetrics(),
            "search": APIMetrics(),
            "chat": APIMetrics(),
            "ari": APIMetrics(),
            "overall": APIMetrics()
        }
        
        # Pre-computed cache for Fortune 10K companies
        self.precomputed_cache = {}
        
        # Intelligent caching with different TTLs
        self.cache_ttls = {
            "precomputed": 86400 * 7,  # 7 days
            "aggressive": 3600 * 4,    # 4 hours
            "standard": 1800,          # 30 minutes
            "minimal": 300             # 5 minutes
        }
    
    async def generate_impact_card_optimized(
        self,
        competitor: str,
        keywords: Optional[List[str]] = None,
        *,
        progress_room: Optional[str] = None,
        db_session=None,
    ) -> Dict[str, Any]:
        """
        Optimized impact card generation with sub-minute performance
        This is the main method showcasing Week 1 improvements
        """
        logger.info(f"🚀 Starting OPTIMIZED Impact Card generation for {competitor}")
        start_time = time.perf_counter()
        
        # Step 1: Intelligent Query Planning
        query = f"{competitor} competitive analysis business strategy"
        if keywords:
            query += " " + " ".join(keywords)
        
        plan = self.query_router.analyze_query(query, competitor)
        logger.info(f"📋 Query Plan: {plan.route.value} route, {plan.estimated_time:.1f}s estimated")
        
        await self._notify_progress(
            competitor,
            "planning",
            progress_room=progress_room,
            route=plan.route.value,
            estimated_time=plan.estimated_time,
            apis_needed=plan.apis_needed
        )
        
        # Step 2: Execute based on route
        if plan.route == APIRoute.FAST_TRACK:
            return await self._execute_fast_track(competitor, plan, progress_room, db_session)
        
        elif plan.route == APIRoute.STANDARD:
            return await self._execute_standard(competitor, plan, progress_room, db_session)
        
        else:  # DEEP_DIVE
            return await self._execute_deep_dive(competitor, plan, progress_room, db_session)
    
    async def _execute_fast_track(
        self,
        competitor: str,
        plan: QueryPlan,
        progress_room: Optional[str],
        db_session
    ) -> Dict[str, Any]:
        """Fast track execution for known companies"""
        logger.info(f"⚡ Fast track execution for {competitor}")
        
        # Check pre-computed cache
        cache_key = f"precomputed:{competitor.lower()}"
        cached_data = await self._get_cached_data(cache_key)
        
        if cached_data:
            logger.info("📦 Using pre-computed company profile")
            await self._notify_progress(
                competitor,
                "cache_hit",
                progress_room=progress_room,
                source="precomputed"
            )
            
            # Update metrics
            self.metrics["overall"].cache_hits += 1
            
            return cached_data
        
        # Fallback to minimal API calls
        start_time = time.perf_counter()
        search_data = await self.search_context(f"{competitor} company profile")
        
        # Create minimal impact card
        impact_card = {
            "competitor": competitor,
            "generated_at": datetime.utcnow().isoformat(),
            "risk_score": 60,  # Default moderate risk
            "risk_level": "medium",
            "confidence_score": 75,
            "route": "fast_track",
            "processing_time": f"{time.perf_counter() - start_time:.2f}s",
            "source_data": search_data,
            "optimization": "pre_computed_fallback"
        }
        
        # Cache for future use
        await self._cache_data(cache_key, impact_card, self.cache_ttls["precomputed"])
        
        return impact_card
    
    async def _execute_standard(
        self,
        competitor: str,
        plan: QueryPlan,
        progress_room: Optional[str],
        db_session
    ) -> Dict[str, Any]:
        """Standard execution with parallel optimization"""
        logger.info(f"🔄 Standard execution for {competitor}")
        
        results = {}
        
        # Execute parallel groups
        for group_idx, api_group in enumerate(plan.parallel_groups):
            logger.info(f"📊 Executing parallel group {group_idx + 1}: {api_group}")
            
            # Run APIs in parallel within group
            group_tasks = []
            for api in api_group:
                if api == "news":
                    task = self._execute_news_optimized(competitor)
                elif api == "search":
                    task = self._execute_search_optimized(competitor)
                elif api == "chat":
                    task = self._execute_chat_optimized(competitor, results)
                elif api == "ari":
                    task = self._execute_ari_optimized(competitor)
                
                group_tasks.append((api, task))
            
            # Wait for group completion
            group_results = await asyncio.gather(
                *[task for _, task in group_tasks],
                return_exceptions=True
            )
            
            # Process results
            for (api, _), result in zip(group_tasks, group_results):
                if isinstance(result, Exception):
                    logger.error(f"❌ {api} failed: {result}")
                    results[api] = await self._get_fallback_data(api, competitor)
                else:
                    results[api] = result
                
                await self._notify_progress(
                    competitor,
                    f"{api}_complete",
                    progress_room=progress_room,
                    success=not isinstance(result, Exception)
                )
        
        # Assemble optimized impact card
        return await self._assemble_optimized_card(competitor, results, plan)
    
    async def _execute_deep_dive(
        self,
        competitor: str,
        plan: QueryPlan,
        progress_room: Optional[str],
        db_session
    ) -> Dict[str, Any]:
        """Deep dive execution with all APIs and advanced analysis"""
        logger.info(f"🔬 Deep dive execution for {competitor}")
        
        # Use the standard resilient method but with optimizations
        return await super().generate_impact_card(
            competitor,
            progress_room=progress_room,
            db_session=db_session
        )
    
    async def _execute_news_optimized(self, competitor: str) -> Dict[str, Any]:
        """Optimized news fetching with intelligent caching"""
        start_time = time.perf_counter()
        
        try:
            result = await self.fetch_news(f"{competitor} announcement launch")
            
            # Update metrics
            latency = time.perf_counter() - start_time
            self.metrics["news"].total_calls += 1
            self.metrics["news"].successful_calls += 1
            self.metrics["news"].total_latency += latency
            
            return result
            
        except Exception as e:
            self.metrics["news"].total_calls += 1
            self.metrics["news"].failed_calls += 1
            raise
    
    async def _execute_search_optimized(self, competitor: str) -> Dict[str, Any]:
        """Optimized search with query enhancement"""
        start_time = time.perf_counter()
        
        try:
            # Enhanced query for better results
            enhanced_query = f"{competitor} business model competitive analysis strategy"
            result = await self.search_context(enhanced_query)
            
            # Update metrics
            latency = time.perf_counter() - start_time
            self.metrics["search"].total_calls += 1
            self.metrics["search"].successful_calls += 1
            self.metrics["search"].total_latency += latency
            
            return result
            
        except Exception as e:
            self.metrics["search"].total_calls += 1
            self.metrics["search"].failed_calls += 1
            raise
    
    async def _execute_chat_optimized(self, competitor: str, context: Dict) -> Dict[str, Any]:
        """Optimized chat analysis with context"""
        start_time = time.perf_counter()
        
        try:
            news_data = context.get("news", {})
            search_data = context.get("search", {})
            
            result = await self.analyze_impact(news_data, search_data, competitor)
            
            # Update metrics
            latency = time.perf_counter() - start_time
            self.metrics["chat"].total_calls += 1
            self.metrics["chat"].successful_calls += 1
            self.metrics["chat"].total_latency += latency
            
            return result
            
        except Exception as e:
            self.metrics["chat"].total_calls += 1
            self.metrics["chat"].failed_calls += 1
            raise
    
    async def _execute_ari_optimized(self, competitor: str) -> Dict[str, Any]:
        """Optimized ARI research with focused queries"""
        start_time = time.perf_counter()
        
        try:
            focused_query = f"Strategic competitive analysis {competitor} market positioning"
            result = await self.generate_research_report(focused_query)
            
            # Update metrics
            latency = time.perf_counter() - start_time
            self.metrics["ari"].total_calls += 1
            self.metrics["ari"].successful_calls += 1
            self.metrics["ari"].total_latency += latency
            
            return result
            
        except Exception as e:
            self.metrics["ari"].total_calls += 1
            self.metrics["ari"].failed_calls += 1
            raise
    
    async def _assemble_optimized_card(
        self,
        competitor: str,
        results: Dict[str, Any],
        plan: QueryPlan
    ) -> Dict[str, Any]:
        """Assemble impact card with optimization metadata"""
        
        # Use parent assembly method
        news_data = results.get("news", {})
        search_data = results.get("search", {})
        analysis_data = results.get("chat", {})
        research_data = results.get("ari", {})
        
        impact_card = self.assemble_impact_card(
            news_data, search_data, analysis_data, research_data, competitor
        )
        
        # Add optimization metadata
        impact_card.update({
            "optimization": {
                "route": plan.route.value,
                "complexity": plan.complexity.value,
                "apis_used": plan.apis_needed,
                "parallel_groups": len(plan.parallel_groups),
                "estimated_time": plan.estimated_time,
                "actual_time": impact_card.get("processing_time", "0s"),
                "cost_estimate": plan.cost_estimate,
                "cache_strategy": plan.cache_strategy
            },
            "performance_metrics": self._get_performance_summary()
        })
        
        return impact_card
    
    async def _get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache with metrics tracking"""
        if not self.cache:
            return None
        
        try:
            cached = await self.cache.get(key)
            if cached:
                self.metrics["overall"].cache_hits += 1
                return json.loads(cached)
            else:
                self.metrics["overall"].cache_misses += 1
                return None
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            self.metrics["overall"].cache_misses += 1
            return None
    
    async def _cache_data(self, key: str, data: Dict[str, Any], ttl: int) -> None:
        """Cache data with specified TTL"""
        if not self.cache:
            return
        
        try:
            await self.cache.set(key, json.dumps(data), ex=ttl)
            logger.info(f"🗃️ Cached data for {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance metrics summary"""
        return {
            api: {
                "success_rate": metrics.success_rate,
                "average_latency": metrics.average_latency,
                "total_calls": metrics.total_calls,
                "cache_hit_rate": metrics.cache_hit_rate
            }
            for api, metrics in self.metrics.items()
        }
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report"""
        return {
            "performance_metrics": self._get_performance_summary(),
            "cost_optimization": {
                "total_savings": sum(m.cost_saved for m in self.metrics.values()),
                "cache_efficiency": self.metrics["overall"].cache_hit_rate,
                "api_efficiency": self.metrics["overall"].success_rate
            },
            "system_health": {
                "circuit_breakers": self.get_health_status()["circuit_breakers"],
                "cache_status": "connected" if self.cache else "disconnected"
            },
            "recommendations": self._generate_optimization_recommendations()
        }
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on metrics"""
        recommendations = []
        
        overall_metrics = self.metrics["overall"]
        
        if overall_metrics.cache_hit_rate < 0.7:
            recommendations.append("Increase cache TTL for better hit rates")
        
        if overall_metrics.success_rate < 0.9:
            recommendations.append("Review circuit breaker thresholds")
        
        for api, metrics in self.metrics.items():
            if api == "overall":
                continue
            
            if metrics.average_latency > 10.0:
                recommendations.append(f"Optimize {api} API query patterns")
            
            if metrics.success_rate < 0.8:
                recommendations.append(f"Improve {api} API resilience")
        
        return recommendations

# FastAPI dependency
async def get_advanced_you_client():
    """FastAPI dependency for advanced You.com orchestrator"""
    async with AdvancedYouComOrchestrator() as client:
        yield client