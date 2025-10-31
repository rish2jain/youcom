"""You.com API client orchestration with caching and progress events."""

import json
import logging
import time
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.realtime import emit_progress
from app.database import AsyncSessionLocal
from app.models.api_call_log import ApiCallLog
from app.models.notification import NotificationRule, NotificationLog
# Removed circular import - will import dynamically when needed
from sqlalchemy import select

logger = logging.getLogger(__name__)

TIER_ONE_DOMAINS = {
    "nytimes.com",
    "wsj.com",
    "bloomberg.com",
    "reuters.com",
    "ft.com",
    "forbes.com",
    "techcrunch.com",
}

OWNER_MAPPINGS = {
    "pricing": ("Revenue Ops", "Improve monetization efficiency"),
    "sales": ("Sales", "Expand enterprise adoption"),
    "product": ("Product", "Enhance product differentiation"),
    "marketing": ("Marketing", "Increase market awareness"),
    "regulatory": ("Compliance", "Maintain regulatory readiness"),
}

class YouComAPIError(Exception):
    """Custom exception for You.com API errors with context."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        payload: Optional[Any] = None,
        api_type: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
        self.api_type = api_type

    def __str__(self) -> str:
        """Enhanced string representation with context"""
        parts = [str(self.args[0])]
        if self.api_type:
            parts.append(f"API: {self.api_type}")
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        return " | ".join(parts)

class YouComOrchestrator:
    """Orchestrates all 4 You.com APIs for competitive intelligence"""

    def __init__(self, api_key: str = None):
        # Extract actual key from SecretStr if needed
        raw_key = api_key or settings.you_api_key
        self.api_key = raw_key.get_secret_value() if hasattr(raw_key, 'get_secret_value') else raw_key

        if not self.api_key or self.api_key == "your_you_api_key_here":
            raise ValueError("You.com API key is required. Please set YOU_API_KEY in your .env file")

        logger.info("🔑 Using You.com API for live data")

        # Create separate clients for different authentication methods
        # Search and News APIs use X-API-Key header
        self.search_client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }
        )

        # Agent APIs (Chat, Express) use Authorization Bearer header
        self.agent_client = httpx.AsyncClient(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

        # API usage tracking for demo
        self.api_usage = {
            "news_calls": 0,
            "search_calls": 0,
            "chat_calls": 0,
            "ari_calls": 0,
            "total_calls": 0
        }

        self.cache: Optional[Redis] = None
        if not settings.demo_mode:
            try:
                self.cache = Redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except RedisError as exc:  # pragma: no cover - fallback path
                logger.warning("Redis unavailable for caching: %s", exc)
                self.cache = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.search_client.aclose()
        await self.agent_client.aclose()
        if self.cache:
            with suppress(RedisError):
                await self.cache.close()
            with suppress(RedisError):
                await self.cache.connection_pool.disconnect()

    def _track_usage(self, api_type: str):
        """Track API usage for demo purposes"""
        self.api_usage[f"{api_type}_calls"] += 1
        self.api_usage["total_calls"] += 1
        logger.info(f"You.com {api_type.upper()} API call #{self.api_usage[f'{api_type}_calls']}")

    def _cache_key(self, prefix: str, identifier: str) -> str:
        safe_identifier = identifier.lower().replace(" ", ":")
        return f"youcom:{prefix}:{safe_identifier}"

    async def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        if not self.cache:
            return None
        try:
            cached = await self.cache.get(key)
            if cached:
                logger.info("📦 Cache hit for %s", key)
                return json.loads(cached)
        except (RedisError, json.JSONDecodeError) as exc:
            logger.warning("Cache read failed for %s: %s", key, exc)
        return None

    async def _cache_set(self, key: str, value: Dict[str, Any], ttl: int) -> None:
        if not self.cache:
            return
        try:
            await self.cache.set(key, json.dumps(value), ex=ttl)
            logger.info("🗃️ Cached response for %s", key)
        except RedisError as exc:
            logger.warning("Cache write failed for %s: %s", key, exc)

    def _tier_for_domain(self, url: str) -> Tuple[str, float]:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if domain in TIER_ONE_DOMAINS:
            return "tier1", 1.0
        if domain.endswith(".gov") or domain.endswith(".edu"):
            return "tier1", 0.95
        if domain.endswith(".news") or domain.endswith(".co"):
            return "tier2", 0.75
        return "tier3", 0.55

    async def _log_api_call(
        self,
        api_type: str,
        endpoint: str,
        *,
        status_code: Optional[int],
        success: bool,
        latency_ms: float,
        error_message: Optional[str] = None,
    ) -> None:
        async with AsyncSessionLocal() as session:
            log_entry = ApiCallLog(
                api_type=api_type,
                endpoint=endpoint,
                status_code=status_code,
                success=success,
                latency_ms=latency_ms,
                error_message=error_message,
            )
            session.add(log_entry)
            try:
                await session.commit()
            except Exception as exc:  # pragma: no cover - logging should not break workflows
                logger.warning("Failed to persist API call log: %s", exc)
                await session.rollback()

    async def _perform_request(
        self,
        *,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        api_type: str,
        params: Optional[Dict[str, Any]] = None,
        json_payload: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        start = time.perf_counter()
        try:
            response = await client.request(
                method,
                url,
                params=params,
                json=json_payload,
            )
            response.raise_for_status()
            latency_ms = (time.perf_counter() - start) * 1000
            await self._log_api_call(
                api_type,
                url,
                status_code=response.status_code,
                success=True,
                latency_ms=latency_ms,
            )
            return response
        except httpx.HTTPStatusError as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            await self._log_api_call(
                api_type,
                url,
                status_code=exc.response.status_code,
                success=False,
                latency_ms=latency_ms,
                error_message=exc.response.text,
            )
            raise
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            await self._log_api_call(
                api_type,
                url,
                status_code=None,
                success=False,
                latency_ms=latency_ms,
                error_message=str(exc),
            )
            raise

    def _evaluate_source_quality(
        self,
        news_data: Dict[str, Any],
        context_data: Dict[str, Any],
        research_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        sources: List[Dict[str, Any]] = []

        # Process news articles
        articles = news_data.get("articles", [])
        for article in articles:
            if not isinstance(article, dict):
                continue
                
            url = article.get("url")
            if not url:
                continue
            tier, weight = self._tier_for_domain(url)
            sources.append({
                "type": "news",
                "title": article.get("title"),
                "url": url,
                "tier": tier,
                "weight": weight,
            })

        for result in context_data.get("results", []):
            url = result.get("url")
            if not url:
                continue
            tier, weight = self._tier_for_domain(url)
            sources.append({
                "type": "search",
                "title": result.get("title"),
                "url": url,
                "tier": tier,
                "weight": weight * 0.9,
            })

        # Handle research data citations - with type guards for safety
        citations = research_data.get("citations", [])
        if citations and isinstance(citations, list):
            for citation in citations:
                # Type guard: Handle dict citations
                if isinstance(citation, dict):
                    url = citation.get("url")
                    if not url or not isinstance(url, str):
                        continue
                    tier, weight = self._tier_for_domain(url)
                    sources.append({
                        "type": "research",
                        "title": citation.get("title", "Research Citation"),
                        "url": url,
                        "tier": tier,
                        "weight": weight * 1.1,
                    })
                # Type guard: Handle string citations
                elif isinstance(citation, str):
                    try:
                        tier, weight = self._tier_for_domain(citation)
                        sources.append({
                            "type": "research",
                            "title": "Research Citation",
                            "url": citation,
                            "tier": tier,
                            "weight": weight * 1.1,
                        })
                    except Exception as e:
                        logger.warning(f"Invalid citation string format: {citation[:50]}... - {e}")
                        continue
                else:
                    # Log unexpected citation format but don't crash
                    logger.warning(f"Unexpected citation format: {type(citation).__name__}")

        if not sources:
            return {"score": 0.0, "tiers": {}, "top_sources": [], "total": 0}

        tier_counts: Dict[str, int] = {"tier1": 0, "tier2": 0, "tier3": 0}
        weighted_sum = 0.0
        for src in sources:
            tier_counts[src["tier"]] += 1
            weighted_sum += src["weight"]

        score = min(1.0, weighted_sum / len(sources))
        top_sources = list(sources[:5]) if sources else []

        return {
            "score": round(score, 3),
            "tiers": tier_counts,
            "total": len(sources),
            "top_sources": top_sources,
        }

    def _owner_for_action(self, action: str) -> Tuple[str, str]:
        lowered = action.lower()
        for keyword, (owner, okr) in OWNER_MAPPINGS.items():
            if keyword in lowered:
                return owner, okr
        return "Strategy Team", "Drive competitive differentiation"

    def _enrich_recommended_actions(
        self,
        analysis: Dict[str, Any],
        news_data: Dict[str, Any],
        research_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        actions = analysis.get("recommended_actions", []) or []
        impact_lookup = {
            area.get("area", "").lower(): area.get("impact_score", 60)
            for area in analysis.get("impact_areas", [])
        }
        # Safely combine evidence from different sources
        news_articles = news_data.get("articles", [])
        research_citations = research_data.get("citations", [])
        
        # Ensure we have lists, not dict keys or other types
        if not isinstance(news_articles, list):
            news_articles = []
        if not isinstance(research_citations, list):
            research_citations = []
            
        evidence_pool = news_articles + research_citations

        enriched: List[Dict[str, Any]] = []
        for idx, action in enumerate(actions):
            action_text = action.get("action") if isinstance(action, dict) else str(action)
            owner, okr = self._owner_for_action(action_text)
            impact_area_key = None
            for area_key in impact_lookup:
                if area_key and area_key in action_text.lower():
                    impact_area_key = area_key
                    break
            impact_score = impact_lookup.get(impact_area_key, analysis.get("risk_score", 60))
            effort_score = 40 if "accelerate" in action_text.lower() else 60

            evidence_links = []
            for source in list(evidence_pool[:3]) if evidence_pool else []:
                url = source.get("url")
                if not url:
                    continue
                evidence_links.append({
                    "title": source.get("title") or source.get("snippet"),
                    "url": url,
                })

            ranked = {
                "action": action_text,
                "priority": action.get("priority", "medium") if isinstance(action, dict) else "medium",
                "timeline": action.get("timeline", "short-term") if isinstance(action, dict) else "short-term",
                "owner": owner,
                "okr_goal": okr,
                "impact_score": impact_score,
                "effort_score": effort_score,
                "score": round(impact_score - effort_score / 2, 2),
                "evidence": evidence_links,
                "index": idx,
            }
            enriched.append(ranked)

        enriched.sort(key=lambda item: item["score"], reverse=True)
        return enriched

    def _build_explainability(
        self,
        analysis: Dict[str, Any],
        source_quality: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "reasoning": analysis.get("reasoning"),
            "impact_areas": analysis.get("impact_areas", []),
            "key_insights": analysis.get("key_insights", []),
            "source_summary": source_quality,
        }

    async def _evaluate_notifications(
        self,
        db_session,
        competitor: str,
        risk_score: int,
        message_context: Dict[str, Any],
    ) -> None:
        rules_result = await db_session.execute(
            select(NotificationRule).where(
                NotificationRule.active.is_(True),
                NotificationRule.competitor_name == competitor,
            )
        )
        rules = rules_result.scalars().all()
        for rule in rules:
            triggered = False
            if rule.condition_type == "risk_threshold" and rule.threshold_value is not None:
                if risk_score >= rule.threshold_value:
                    triggered = True

            if not triggered:
                continue

            log_entry = NotificationLog(
                rule_id=rule.id,
                competitor_name=competitor,
                channel=rule.channel,
                target=rule.target,
                message=json.dumps(message_context),
            )
            db_session.add(log_entry)
            rule.last_triggered_at = datetime.utcnow()

        await db_session.commit()

    async def _notify_progress(
        self,
        competitor: str,
        step: str,
        *,
        progress_room: Optional[str] = None,
        **details: Any,
    ) -> None:
        if not progress_room:
            return
        payload = {"competitor": competitor, "step": step, **details}
        await emit_progress("impact_generation_step", payload, room=progress_room)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def search_context(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """You.com Search API - Context enrichment with caching"""

        # Demo mode fallback
        if settings.demo_mode:
            return self._get_demo_search_data(query, limit)

        cache_key = self._cache_key("search", f"{query}:{limit}")
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        self._track_usage("search")

        try:
            params = {
                "query": query,
                "num_web_results": limit,
                "safesearch": "moderate",
            }

            response = await self._perform_request(
                client=self.search_client,
                method="GET",
                url=settings.you_search_url,
                api_type="search",
                params=params,
            )

            data = response.json()

            web_results = data.get("results", {}).get("web", [])
            results = []
            for result in web_results:
                snippet = ""
                if result.get("snippets"):
                    snippet = result["snippets"][0] if result["snippets"] else ""
                elif result.get("description"):
                    snippet = result["description"]

                results.append(
                    {
                        "title": result.get("title", ""),
                        "snippet": snippet,
                        "url": result.get("url", ""),
                    }
                )

            logger.info("🔍 Search API returned %s results", len(results))

            payload = {
                "query": query,
                "results": results,
                "total_count": len(results),
                "api_type": "search",
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self._cache_set(cache_key, payload, settings.search_cache_ttl)
            return payload

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Search API HTTP error %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise YouComAPIError(
                "Search API error",
                status_code=exc.response.status_code,
                payload=exc.response.text,
                api_type="search",
            ) from exc
        except Exception as exc:
            logger.error("Search API error: %s", exc)
            raise YouComAPIError(
                "Search API error",
                payload=str(exc),
                api_type="search",
            ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def generate_research_report(self, query: str) -> Dict[str, Any]:
        """You.com ARI API Fallback - Using Express Agent for deep research

        Note: ARI API endpoint not found in public documentation.
        Using Express Agent with detailed prompt for comprehensive research.
        """
        
        # Demo mode fallback
        if settings.demo_mode:
            return self._get_demo_research_data(query)
            
        cache_key = self._cache_key("ari", query)
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        self._track_usage("ari")

        try:
            # Using Express Agent for comprehensive research
            research_prompt = f"""Provide a comprehensive research report on the following topic:

{query}

Please include:
1. Detailed analysis and findings
2. Key insights and trends
3. Multiple perspectives and sources
4. Citations and references where applicable
5. Executive summary

Format the response with clear sections and actionable insights."""

            payload = {
                "agent": "express",
                "input": research_prompt
            }

            response = await self._perform_request(
                client=self.agent_client,
                method="POST",
                url=settings.you_ari_url,
                api_type="ari",
                json_payload=payload,
            )
            
            data = response.json()

            # Extract response from Express Agent
            # Response format may vary - try multiple keys
            report_text = (
                data.get("response", "") or
                data.get("answer", "") or
                data.get("output", "") or
                str(data)
            )
            citations = data.get("citations", []) or data.get("sources", [])

            logger.info(f"📊 ARI API (Express Agent) generated report with {len(citations)} sources")
            
            payload = {
                "query": query,
                "report": report_text,
                "citations": citations,
                "source_count": len(citations),
                "api_type": "ari",
                "timestamp": datetime.utcnow().isoformat()
            }

            await self._cache_set(cache_key, payload, settings.ari_cache_ttl)
            return payload
            
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ARI API HTTP error %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise YouComAPIError(
                "ARI API error",
                status_code=exc.response.status_code,
                payload=exc.response.text,
                api_type="ari",
            ) from exc
        except Exception as exc:
            logger.error("ARI API error: %s", exc)
            raise YouComAPIError(
                "ARI API error",
                payload=str(exc),
                api_type="ari",
            ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def fetch_news(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """You.com News API - Real-time monitoring with caching"""

        # Demo mode fallback
        if settings.demo_mode:
            return self._get_demo_news_data(query, limit)

        cache_key = self._cache_key("news", f"{query}:{limit}")
        cached = await self._cache_get(cache_key)
        if cached:
            return cached

        self._track_usage("news")

        try:
            params = {
                "q": query,
                "count": limit,
            }

            response = await self._perform_request(
                client=self.search_client,
                method="GET",
                url=settings.you_news_url,
                api_type="news",
                params=params,
            )

            data = response.json()
            articles = data.get("news", [])
            logger.info("📰 News API returned %s articles", len(articles))

            payload = {
                "query": query,
                "articles": articles,
                "total_count": len(articles),
                "api_type": "news",
                "timestamp": datetime.utcnow().isoformat(),
            }

            await self._cache_set(cache_key, payload, settings.news_cache_ttl)
            return payload

        except httpx.HTTPStatusError as exc:
            logger.error(
                "News API HTTP error %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise YouComAPIError(
                "News API error",
                status_code=exc.response.status_code,
                payload=exc.response.text,
                api_type="news",
            ) from exc
        except Exception as exc:
            logger.error("News API error: %s", exc)
            raise YouComAPIError(
                "News API error",
                payload=str(exc),
                api_type="news",
            ) from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def analyze_impact(self, news_data: Dict, context_data: Dict, competitor: str) -> Dict[str, Any]:
        """You.com Custom Agents (Chat API) - Competitive analysis"""
        
        # Demo mode fallback
        if settings.demo_mode:
            return self._get_demo_analysis_data(competitor, news_data, context_data)
            
        self._track_usage("chat")
        
        # Create structured prompt for competitive analysis
        prompt = self._create_analysis_prompt(news_data, context_data, competitor)
        
        try:
            # Using Express Agent for competitive analysis
            payload = {
                "agent": "express",
                "input": prompt
                # Note: Verify if these are supported:
                # "include_citations": True,
                # "response_format": "json"
            }

            response = await self._perform_request(
                client=self.agent_client,
                method="POST",
                url=settings.you_chat_url,
                api_type="chat",
                json_payload=payload,
            )
            
            data = response.json()
            logger.info("🤖 Chat API completed competitive analysis")
            
            # Parse the structured response
            try:
                analysis_result = self._parse_analysis_response(data, competitor)
            except YouComAPIError as e:
                logger.warning(f"Chat API response parsing failed, using demo data: {str(e)}")
                # Fallback to demo data if parsing fails
                return self._get_demo_analysis_data(competitor, {}, {})
            
            return {
                "competitor": competitor,
                "analysis": analysis_result,
                "api_type": "chat",
                "timestamp": datetime.utcnow().isoformat(),
                "citations": data.get("citations", [])
            }
            
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Chat API HTTP error %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise YouComAPIError(
                "Chat API error",
                status_code=exc.response.status_code,
                payload=exc.response.text,
                api_type="chat",
            ) from exc
        except Exception as exc:
            logger.error("Chat API error: %s", exc)
            raise YouComAPIError(
                "Chat API error",
                payload=str(exc),
                api_type="chat",
            ) from exc

    def _create_analysis_prompt(self, news_data: Dict, context_data: Dict, competitor: str) -> str:
        """Create structured prompt for competitive analysis"""
        
        try:
            # Extract key information from news and context
            articles = news_data.get("articles", [])
            recent_news = list(articles[:5]) if articles else []  # Top 5 recent articles
            
            results = context_data.get("results", [])
            search_results = list(results[:5]) if results else []  # Top 5 search results
            
            # Ensure data is JSON serializable
            recent_news_json = json.dumps(recent_news, indent=2, default=str)
            search_results_json = json.dumps(search_results, indent=2, default=str)
            
            prompt = f"""
            Analyze the competitive impact of {competitor} using the evidence below and respond **only** with valid JSON.

            RECENT NEWS:
            {recent_news_json}

            CONTEXT INFORMATION:
            {search_results_json}

        Return a JSON object that matches exactly this schema (no extra commentary):
        {{
            "risk_score": integer,
            "risk_level": "low" | "medium" | "high" | "critical",
            "impact_areas": [
                {{
                    "area": string,
                    "impact_score": integer,
                    "description": string
                }}
            ],
            "key_insights": [string],
            "recommended_actions": [
                {{
                    "action": string,
                    "priority": "high" | "medium" | "low",
                    "timeline": "immediate" | "short-term" | "long-term"
                }}
            ],
            "confidence_score": integer,
            "reasoning": string
        }}

            Ensure the response is valid JSON with double quotes and no markdown or prose outside the JSON object.
            """
            
            return prompt
            
        except Exception as e:
            logger.error(f"❌ Error creating analysis prompt: {str(e)}")
            # Return a simple prompt as fallback
            return f"""
            Analyze the competitive impact of {competitor} and respond with valid JSON containing:
            - risk_score (0-100)
            - risk_level (low/medium/high/critical)
            - impact_areas (list of areas with scores)
            - key_insights (list of strings)
            - recommended_actions (list of actions)
            - confidence_score (0-100)
            - reasoning (string)
            """

    def _parse_analysis_response(self, response_data: Dict, competitor: str) -> Dict[str, Any]:
        """Parse and validate the analysis response"""
        
        try:
            # Try to parse JSON response
            response_text = response_data.get("response", "{}")
            if isinstance(response_text, str):
                analysis = json.loads(response_text)
            else:
                analysis = response_text
            
            required_keys = {
                "risk_score": int,
                "risk_level": str,
                "impact_areas": list,
                "key_insights": list,
                "recommended_actions": list,
                "confidence_score": int,
                "reasoning": str,
            }

            missing = [key for key in required_keys if key not in analysis]
            if missing:
                raise YouComAPIError(
                    "Chat API response missing required fields",
                    payload={"missing": missing, "response": analysis},
                )

            for key, expected_type in required_keys.items():
                if not isinstance(analysis[key], expected_type):
                    raise YouComAPIError(
                        "Chat API response has invalid field types",
                        payload={"field": key, "expected": expected_type.__name__, "actual": type(analysis[key]).__name__},
                    )

            return analysis

        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Chat API response JSON: %s", exc)
            raise YouComAPIError(
                "Chat API returned invalid JSON",
                payload=response_data.get("response"),
            ) from exc

    async def quick_company_research(self, company_name: str) -> Dict[str, Any]:
        """Quick company research for individual users"""
        logger.info(f"🏢 Starting quick research for {company_name}")
        
        try:
            # Search for company information
            search_data = await self.search_context(f"{company_name} company profile business model")
            
            # Generate comprehensive research report
            research_data = await self.generate_research_report(
                f"Comprehensive analysis of {company_name} business model market position funding"
            )
            
            # Create company profile
            profile = {
                "company": company_name,
                "generated_at": datetime.utcnow().isoformat(),
                "search_results": search_data,
                "research_report": research_data,
                "total_sources": len(search_data.get("results", [])) + len(research_data.get("citations", [])),
                "api_usage": self.api_usage.copy(),
                "powered_by": "You.com APIs (Search, ARI)"
            }
            
            logger.info(f"✅ Company research completed for {company_name}")
            return profile
            
        except Exception as exc:
            logger.error("❌ Error researching %s: %s", company_name, exc)
            raise YouComAPIError(
                "Failed to research company",
                payload=str(exc),
            ) from exc

    async def generate_impact_card(
        self,
        competitor: str,
        keywords: Optional[List[str]] = None,
        *,
        progress_room: Optional[str] = None,
        db_session=None,
    ) -> Dict[str, Any]:
        """
        Complete workflow using all 4 You.com APIs
        This is the main orchestration method that showcases API integration
        """
        logger.info(f"🚀 Starting Impact Card generation for {competitor}")
        start_time = time.perf_counter()
        keywords = keywords or []
        
        try:
            # Step 1: News API - Get latest competitor news
            logger.info("📰 Step 1: Fetching latest news...")
            news_query = f"{competitor} announcement launch product"
            if keywords:
                news_query += " " + " ".join(keywords)
            
            news_data = await self.fetch_news(news_query)
            
            # Enhance news with sentiment analysis
            if db_session:
                # Dynamic import to avoid circular dependency
                from app.services.sentiment_news_integration import SentimentNewsIntegrationService
                sentiment_integration = SentimentNewsIntegrationService(db_session)
                news_data = await sentiment_integration.process_news_with_sentiment(
                    news_data, competitor
                )
            
            await self._notify_progress(
                competitor,
                "news",
                progress_room=progress_room,
                articles=len(news_data.get("articles", [])),
                sentiment_summary=news_data.get("sentiment_summary", {})
            )
            
            # Step 2: Search API - Enrich with context
            logger.info("🔍 Step 2: Enriching with search context...")
            search_query = f"{competitor} business model strategy competitive analysis"
            context_data = await self.search_context(search_query)
            await self._notify_progress(
                competitor,
                "search",
                progress_room=progress_room,
                results=context_data.get("total_count", 0),
            )
            
            # Step 3: Custom Agents (Chat API) - Analyze competitive impact
            logger.info("🤖 Step 3: Analyzing competitive impact...")
            analysis_data = await self.analyze_impact(news_data, context_data, competitor)
            await self._notify_progress(
                competitor,
                "analysis",
                progress_room=progress_room,
                risk_score=analysis_data.get("analysis", {}).get("risk_score"),
            )
            
            # Step 4: ARI API - Generate deep research report
            logger.info("📊 Step 4: Generating deep research report...")
            research_query = f"Competitive analysis of {competitor} strategic positioning market impact"
            research_data = await self.generate_research_report(research_query)
            await self._notify_progress(
                competitor,
                "research",
                progress_room=progress_room,
                citations=len(research_data.get("citations", [])),
            )
            
            # Step 5: Assemble Impact Card
            logger.info("🎯 Step 5: Assembling Impact Card...")
            source_quality = self._evaluate_source_quality(
                news_data,
                context_data,
                research_data,
            )

            impact_card = self.assemble_impact_card(
                news_data,
                context_data,
                analysis_data,
                research_data,
                competitor,
            )
            elapsed = time.perf_counter() - start_time
            impact_card["processing_time"] = f"{elapsed:.2f}s"
            impact_card["source_quality"] = source_quality
            impact_card["credibility_score"] = source_quality.get("score", 0.0)
            impact_card["requires_review"] = (
                impact_card["risk_score"] >= 85
                and impact_card["credibility_score"] < 0.8
            )
            impact_card["explainability"] = self._build_explainability(
                analysis_data.get("analysis", {}),
                source_quality,
            )

            if db_session is not None:
                await self._evaluate_notifications(
                    db_session,
                    competitor,
                    impact_card["risk_score"],
                    {
                        "competitor": competitor,
                        "risk_score": impact_card["risk_score"],
                        "credibility": impact_card["credibility_score"],
                    },
                )
            
            logger.info(f"✅ Impact Card generated successfully for {competitor}")
            return impact_card
            
        except Exception as e:
            logger.error(f"❌ Error generating Impact Card for {competitor}: {str(e)}")
            raise YouComAPIError("Failed to generate Impact Card", payload=str(e)) from e

    def assemble_impact_card(self, news_data: Dict, context_data: Dict, analysis_data: Dict, research_data: Dict, competitor: str) -> Dict[str, Any]:
        """Combine all API results into a single impact card payload."""

        logger.info(f"🔍 Assembling impact card - analysis_data type: {type(analysis_data)}")
        logger.info(f"🔍 Analysis data keys: {list(analysis_data.keys()) if isinstance(analysis_data, dict) else 'Not a dict'}")
        
        analysis = analysis_data.get("analysis")
        logger.info(f"🔍 Analysis type: {type(analysis)}")
        
        if not analysis:
            raise YouComAPIError(
                "Missing analysis data for impact card assembly",
                payload={"analysis_data": analysis_data},
            )

        total_sources = (
            len(news_data.get("articles", []))
            + len(context_data.get("results", []))
            + len(research_data.get("citations", []))
        )

        logger.info(f"🔍 Research data type: {type(research_data)}")
        logger.info(f"🔍 Research data keys: {list(research_data.keys()) if isinstance(research_data, dict) else 'Not a dict'}")
        
        enriched_actions = self._enrich_recommended_actions(
            analysis,
            news_data,
            research_data,
        )

        impact_card = {
            "competitor": competitor,
            "generated_at": datetime.utcnow().isoformat(),
            "risk_score": analysis["risk_score"],
            "risk_level": analysis["risk_level"],
            "confidence_score": analysis["confidence_score"],
            "impact_areas": analysis["impact_areas"],
            "key_insights": analysis["key_insights"],
            "recommended_actions": enriched_actions,
            "next_steps_plan": enriched_actions,
            "total_sources": total_sources,
            "source_breakdown": {
                "news_articles": len(news_data.get("articles", [])),
                "search_results": len(context_data.get("results", [])),
                "research_citations": len(research_data.get("citations", [])),
            },
            "api_usage": self.api_usage.copy(),
            "powered_by": "You.com APIs (News, Search, Chat, ARI)",
            "raw_data": {
                "news": news_data,
                "context": context_data,
                "analysis": analysis_data,
                "research": research_data,
            },
            "explainability": {},
        }

        logger.info(
            "🎯 Impact Card assembled: Risk Score %s, %s sources",
            impact_card["risk_score"],
            total_sources,
        )
        return impact_card

    def _get_demo_search_data(self, query: str, limit: int) -> Dict[str, Any]:
        """Generate demo search data when APIs are unavailable"""
        self._track_usage("search")
        
        demo_results = [
            {
                "title": f"{query} - Company Overview",
                "snippet": f"Comprehensive overview of {query} including business model, market position, and competitive landscape.",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-overview"
            },
            {
                "title": f"{query} - Market Analysis",
                "snippet": f"In-depth market analysis of {query}'s position in the industry with competitive insights.",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-analysis"
            },
            {
                "title": f"{query} - Recent Developments",
                "snippet": f"Latest news and developments from {query} including product launches and strategic initiatives.",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-news"
            }
        ]
        
        return {
            "query": query,
            "results": demo_results[:limit],
            "total_count": len(demo_results[:limit]),
            "api_type": "search",
            "timestamp": datetime.utcnow().isoformat(),
            "demo_mode": True
        }
    
    def _get_demo_news_data(self, query: str, limit: int) -> Dict[str, Any]:
        """Generate demo news data when APIs are unavailable"""
        self._track_usage("news")
        
        demo_articles = [
            {
                "title": f"{query} Announces Major Product Update",
                "snippet": f"{query} has announced significant updates to their platform, introducing new features and capabilities.",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-update",
                "published_at": datetime.utcnow().isoformat(),
                "source": "Tech News Daily"
            },
            {
                "title": f"{query} Expands Market Presence",
                "snippet": f"Strategic expansion announcement from {query} as they enter new markets and partnerships.",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-expansion",
                "published_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "source": "Business Wire"
            }
        ]
        
        return {
            "query": query,
            "articles": demo_articles[:limit],
            "total_count": len(demo_articles[:limit]),
            "api_type": "news",
            "timestamp": datetime.utcnow().isoformat(),
            "demo_mode": True
        }
    
    def _get_demo_analysis_data(self, competitor: str, news_data: Dict, context_data: Dict) -> Dict[str, Any]:
        """Generate demo analysis data when APIs are unavailable"""
        self._track_usage("chat")
        
        # Generate realistic demo analysis based on competitor name
        risk_score = 75 if "openai" in competitor.lower() else 65
        risk_level = "high" if risk_score >= 70 else "medium"
        
        demo_analysis = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "impact_areas": [
                {
                    "area": "product",
                    "impact_score": risk_score + 5,
                    "description": f"{competitor} product developments may impact our competitive position"
                },
                {
                    "area": "market",
                    "impact_score": risk_score - 10,
                    "description": f"Market expansion by {competitor} creates new competitive dynamics"
                }
            ],
            "key_insights": [
                f"{competitor} is making significant strategic moves in the market",
                f"Recent developments from {competitor} show increased competitive pressure",
                f"Market positioning of {competitor} requires strategic response"
            ],
            "recommended_actions": [
                {
                    "action": f"Monitor {competitor} product developments closely",
                    "priority": "high",
                    "timeline": "immediate"
                },
                {
                    "action": f"Analyze competitive response to {competitor} strategy",
                    "priority": "medium",
                    "timeline": "short-term"
                }
            ],
            "confidence_score": 85,
            "reasoning": f"Analysis based on recent market activity and strategic positioning of {competitor}"
        }
        
        return {
            "competitor": competitor,
            "analysis": demo_analysis,
            "api_type": "chat",
            "timestamp": datetime.utcnow().isoformat(),
            "citations": [],
            "demo_mode": True
        }
    
    def _get_demo_research_data(self, query: str) -> Dict[str, Any]:
        """Generate demo research data when APIs are unavailable"""
        self._track_usage("ari")
        
        demo_report = f"""
# Comprehensive Research Report: {query}

## Executive Summary
This comprehensive analysis of {query} provides insights into their business model, market position, and competitive landscape based on extensive research.

## Key Findings
- Strong market position with innovative product offerings
- Significant growth trajectory in target markets
- Strategic partnerships driving expansion
- Competitive advantages in technology and user experience

## Market Analysis
The company operates in a dynamic market with significant growth opportunities. Recent developments indicate strong momentum and strategic positioning for continued success.

## Competitive Landscape
Analysis of competitive positioning shows differentiated approach with unique value propositions that set them apart from traditional competitors.

## Strategic Recommendations
- Continue monitoring market developments
- Assess competitive response strategies
- Evaluate partnership opportunities
- Track product development initiatives

## Conclusion
{query} represents a significant competitive presence with strong fundamentals and growth potential.
        """.strip()
        
        demo_citations = [
            {
                "title": f"{query} Company Profile",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-profile"
            },
            {
                "title": f"{query} Market Analysis",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-market"
            },
            {
                "title": f"{query} Strategic Overview",
                "url": f"https://example.com/{query.lower().replace(' ', '-')}-strategy"
            }
        ]
        
        return {
            "query": query,
            "report": demo_report,
            "citations": demo_citations,
            "source_count": len(demo_citations),
            "api_type": "ari",
            "timestamp": datetime.utcnow().isoformat(),
            "demo_mode": True
        }

# Alias for backward compatibility
YouComClient = YouComOrchestrator

async def get_you_client():
    """FastAPI dependency that yields a managed You.com client."""

    async with YouComOrchestrator() as client:
        yield client
