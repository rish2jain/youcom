"""
Advanced Cache Manager for Intelligence Suite

This service provides comprehensive caching strategies for sentiment analysis,
templates, industry data, and benchmark calculations with appropriate TTL values.
"""

import asyncio
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import gzip

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.models.sentiment_analysis import SentimentAnalysis, SentimentTrend
from app.models.industry_template import IndustryTemplate, TemplateApplication
from app.models.benchmarking import BenchmarkResult, MetricsSnapshot
from app.config import settings

logger = logging.getLogger(__name__)

class CacheType(str, Enum):
    """Types of cached data."""
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    SENTIMENT_TRENDS = "sentiment_trends"
    INDUSTRY_TEMPLATES = "industry_templates"
    TEMPLATE_DATA = "template_data"
    BENCHMARK_RESULTS = "benchmark_results"
    TREND_ANALYSIS = "trend_analysis"
    METRICS_AGGREGATION = "metrics_aggregation"
    PREDICTION_RESULTS = "prediction_results"

class CacheStrategy(str, Enum):
    """Caching strategies."""
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    CACHE_ASIDE = "cache_aside"
    REFRESH_AHEAD = "refresh_ahead"

@dataclass
class CacheConfig:
    """Configuration for cache behavior."""
    cache_type: CacheType
    ttl_seconds: int
    max_size_mb: int
    compression_enabled: bool
    strategy: CacheStrategy
    refresh_threshold: float  # Refresh when TTL < threshold * ttl_seconds
    batch_size: int

@dataclass
class CacheStats:
    """Cache statistics."""
    cache_type: CacheType
    hit_count: int
    miss_count: int
    hit_rate: float
    total_size_mb: float
    entry_count: int
    avg_ttl_seconds: float
    last_refresh: datetime

class AdvancedCacheManager:
    """Advanced caching service for Intelligence Suite components."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client: Optional[redis.Redis] = None
        
        # Cache configurations
        self.cache_configs = {
            CacheType.SENTIMENT_ANALYSIS: CacheConfig(
                cache_type=CacheType.SENTIMENT_ANALYSIS,
                ttl_seconds=900,  # 15 minutes
                max_size_mb=100,
                compression_enabled=True,
                strategy=CacheStrategy.WRITE_THROUGH,
                refresh_threshold=0.2,
                batch_size=50
            ),
            CacheType.SENTIMENT_TRENDS: CacheConfig(
                cache_type=CacheType.SENTIMENT_TRENDS,
                ttl_seconds=1800,  # 30 minutes
                max_size_mb=50,
                compression_enabled=True,
                strategy=CacheStrategy.CACHE_ASIDE,
                refresh_threshold=0.3,
                batch_size=20
            ),
            CacheType.INDUSTRY_TEMPLATES: CacheConfig(
                cache_type=CacheType.INDUSTRY_TEMPLATES,
                ttl_seconds=86400,  # 24 hours
                max_size_mb=25,
                compression_enabled=False,
                strategy=CacheStrategy.REFRESH_AHEAD,
                refresh_threshold=0.1,
                batch_size=10
            ),
            CacheType.TEMPLATE_DATA: CacheConfig(
                cache_type=CacheType.TEMPLATE_DATA,
                ttl_seconds=43200,  # 12 hours
                max_size_mb=75,
                compression_enabled=True,
                strategy=CacheStrategy.WRITE_THROUGH,
                refresh_threshold=0.2,
                batch_size=25
            ),
            CacheType.BENCHMARK_RESULTS: CacheConfig(
                cache_type=CacheType.BENCHMARK_RESULTS,
                ttl_seconds=3600,  # 1 hour
                max_size_mb=150,
                compression_enabled=True,
                strategy=CacheStrategy.CACHE_ASIDE,
                refresh_threshold=0.25,
                batch_size=30
            ),
            CacheType.TREND_ANALYSIS: CacheConfig(
                cache_type=CacheType.TREND_ANALYSIS,
                ttl_seconds=7200,  # 2 hours
                max_size_mb=100,
                compression_enabled=True,
                strategy=CacheStrategy.REFRESH_AHEAD,
                refresh_threshold=0.15,
                batch_size=20
            )
        }
        
        # Cache statistics
        self.cache_stats: Dict[CacheType, CacheStats] = {}
        self.stats_update_interval = timedelta(minutes=5)
        self.last_stats_update = datetime.min
        
        # Background refresh tasks
        self.refresh_tasks: Dict[CacheType, asyncio.Task] = {}
        self.refresh_running = False
        
        # Local cache for frequently accessed small items
        self.local_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.local_cache_ttl = timedelta(minutes=5)
        self.max_local_cache_size = 1000
    
    async def initialize(self) -> None:
        """Initialize the cache manager."""
        try:
            # Connect to Redis
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=False  # We'll handle encoding ourselves for binary data
            )
            await self.redis_client.ping()
            
            # Initialize cache statistics
            await self._initialize_cache_stats()
            
            # Start background refresh tasks
            await self._start_refresh_tasks()
            
            logger.info("Advanced cache manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            raise
    
    async def get_sentiment_analysis(
        self, 
        entity_name: str, 
        entity_type: str,
        timeframe_hours: int = 24
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached sentiment analysis results."""
        cache_key = f"sentiment:{entity_type}:{entity_name}:{timeframe_hours}"
        
        # Try cache first
        cached_data = await self._get_from_cache(CacheType.SENTIMENT_ANALYSIS, cache_key)
        if cached_data:
            await self._record_cache_hit(CacheType.SENTIMENT_ANALYSIS)
            return cached_data
        
        await self._record_cache_miss(CacheType.SENTIMENT_ANALYSIS)
        
        # Load from database
        cutoff_time = datetime.utcnow() - timedelta(hours=timeframe_hours)
        
        result = await self.db.execute(
            select(SentimentAnalysis)
            .where(SentimentAnalysis.entity_name == entity_name)
            .where(SentimentAnalysis.entity_type == entity_type)
            .where(SentimentAnalysis.processing_timestamp >= cutoff_time)
            .order_by(desc(SentimentAnalysis.processing_timestamp))
        )
        
        sentiment_records = result.scalars().all()
        
        # Convert to serializable format
        sentiment_data = [
            {
                "id": record.id,
                "content_id": record.content_id,
                "content_type": record.content_type,
                "sentiment_score": record.sentiment_score,
                "sentiment_label": record.sentiment_label,
                "confidence": record.confidence,
                "processing_timestamp": record.processing_timestamp.isoformat(),
                "source_url": record.source_url,
                "metadata": record.metadata
            }
            for record in sentiment_records
        ]
        
        # Cache the results
        await self._set_in_cache(CacheType.SENTIMENT_ANALYSIS, cache_key, sentiment_data)
        
        return sentiment_data
    
    async def get_sentiment_trends(
        self, 
        entity_name: str, 
        entity_type: str,
        timeframe: str = "daily",
        days: int = 30
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached sentiment trend data."""
        cache_key = f"sentiment_trends:{entity_type}:{entity_name}:{timeframe}:{days}"
        
        # Try cache first
        cached_data = await self._get_from_cache(CacheType.SENTIMENT_TRENDS, cache_key)
        if cached_data:
            await self._record_cache_hit(CacheType.SENTIMENT_TRENDS)
            return cached_data
        
        await self._record_cache_miss(CacheType.SENTIMENT_TRENDS)
        
        # Load from database
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(SentimentTrend)
            .where(SentimentTrend.entity_name == entity_name)
            .where(SentimentTrend.entity_type == entity_type)
            .where(SentimentTrend.timeframe == timeframe)
            .where(SentimentTrend.period_start >= cutoff_time)
            .order_by(SentimentTrend.period_start)
        )
        
        trend_records = result.scalars().all()
        
        # Convert to serializable format
        trend_data = [
            {
                "id": record.id,
                "timeframe": record.timeframe,
                "period_start": record.period_start.isoformat(),
                "period_end": record.period_end.isoformat(),
                "average_sentiment": record.average_sentiment,
                "sentiment_volatility": record.sentiment_volatility,
                "total_mentions": record.total_mentions,
                "trend_direction": record.trend_direction
            }
            for record in trend_records
        ]
        
        # Cache the results
        await self._set_in_cache(CacheType.SENTIMENT_TRENDS, cache_key, trend_data)
        
        return trend_data
    
    async def get_industry_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get cached industry template."""
        cache_key = f"template:{template_id}"
        
        # Try local cache first for templates (they're small and frequently accessed)
        local_data = self._get_from_local_cache(cache_key)
        if local_data:
            await self._record_cache_hit(CacheType.INDUSTRY_TEMPLATES)
            return local_data
        
        # Try Redis cache
        cached_data = await self._get_from_cache(CacheType.INDUSTRY_TEMPLATES, cache_key)
        if cached_data:
            # Store in local cache too
            self._set_in_local_cache(cache_key, cached_data)
            await self._record_cache_hit(CacheType.INDUSTRY_TEMPLATES)
            return cached_data
        
        await self._record_cache_miss(CacheType.INDUSTRY_TEMPLATES)
        
        # Load from database
        result = await self.db.execute(
            select(IndustryTemplate).where(IndustryTemplate.id == template_id)
        )
        
        template = result.scalar_one_or_none()
        if not template:
            return None
        
        # Convert to serializable format
        template_data = {
            "id": template.id,
            "name": template.name,
            "industry_sector": template.industry_sector,
            "description": template.description,
            "template_config": template.template_config,
            "default_competitors": template.default_competitors,
            "default_keywords": template.default_keywords,
            "risk_categories": template.risk_categories,
            "kpi_metrics": template.kpi_metrics,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
            "usage_count": template.usage_count,
            "rating": template.rating
        }
        
        # Cache the results
        await self._set_in_cache(CacheType.INDUSTRY_TEMPLATES, cache_key, template_data)
        self._set_in_local_cache(cache_key, template_data)
        
        return template_data
    
    async def get_industry_templates_by_sector(self, sector: str) -> List[Dict[str, Any]]:
        """Get cached industry templates by sector."""
        cache_key = f"templates_by_sector:{sector}"
        
        # Try cache first
        cached_data = await self._get_from_cache(CacheType.TEMPLATE_DATA, cache_key)
        if cached_data:
            await self._record_cache_hit(CacheType.TEMPLATE_DATA)
            return cached_data
        
        await self._record_cache_miss(CacheType.TEMPLATE_DATA)
        
        # Load from database
        result = await self.db.execute(
            select(IndustryTemplate)
            .where(IndustryTemplate.industry_sector == sector)
            .order_by(desc(IndustryTemplate.rating), desc(IndustryTemplate.usage_count))
        )
        
        templates = result.scalars().all()
        
        # Convert to serializable format
        templates_data = [
            {
                "id": template.id,
                "name": template.name,
                "industry_sector": template.industry_sector,
                "description": template.description,
                "usage_count": template.usage_count,
                "rating": template.rating,
                "created_at": template.created_at.isoformat()
            }
            for template in templates
        ]
        
        # Cache the results
        await self._set_in_cache(CacheType.TEMPLATE_DATA, cache_key, templates_data)
        
        return templates_data
    
    async def get_benchmark_results(
        self, 
        metric_type: str,
        timeframe_hours: int = 24,
        entity_filter: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached benchmark results."""
        cache_key = f"benchmark:{metric_type}:{timeframe_hours}:{entity_filter or 'all'}"
        
        # Try cache first
        cached_data = await self._get_from_cache(CacheType.BENCHMARK_RESULTS, cache_key)
        if cached_data:
            await self._record_cache_hit(CacheType.BENCHMARK_RESULTS)
            return cached_data
        
        await self._record_cache_miss(CacheType.BENCHMARK_RESULTS)
        
        # Load from database (assuming BenchmarkResult model exists)
        cutoff_time = datetime.utcnow() - timedelta(hours=timeframe_hours)
        
        query = select(BenchmarkResult).where(
            and_(
                BenchmarkResult.metric_type == metric_type,
                BenchmarkResult.calculated_at >= cutoff_time
            )
        )
        
        if entity_filter:
            query = query.where(BenchmarkResult.entity_name == entity_filter)
        
        query = query.order_by(desc(BenchmarkResult.calculated_at))
        
        result = await self.db.execute(query)
        benchmark_records = result.scalars().all()
        
        # Convert to serializable format
        benchmark_data = [
            {
                "id": record.id,
                "metric_type": record.metric_type,
                "entity_name": record.entity_name,
                "metric_value": record.metric_value,
                "percentile_rank": record.percentile_rank,
                "industry_average": record.industry_average,
                "calculated_at": record.calculated_at.isoformat(),
                "metadata": record.metadata
            }
            for record in benchmark_records
        ]
        
        # Cache the results
        await self._set_in_cache(CacheType.BENCHMARK_RESULTS, cache_key, benchmark_data)
        
        return benchmark_data
    
    async def get_trend_analysis(
        self, 
        analysis_type: str,
        entity_name: str,
        days: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Get cached trend analysis results."""
        cache_key = f"trend_analysis:{analysis_type}:{entity_name}:{days}"
        
        # Try cache first
        cached_data = await self._get_from_cache(CacheType.TREND_ANALYSIS, cache_key)
        if cached_data:
            await self._record_cache_hit(CacheType.TREND_ANALYSIS)
            return cached_data
        
        await self._record_cache_miss(CacheType.TREND_ANALYSIS)
        
        # This would typically involve complex calculations
        # For now, return a placeholder structure
        trend_data = {
            "analysis_type": analysis_type,
            "entity_name": entity_name,
            "timeframe_days": days,
            "trend_direction": "stable",
            "confidence": 0.75,
            "key_metrics": {},
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        # Cache the results
        await self._set_in_cache(CacheType.TREND_ANALYSIS, cache_key, trend_data)
        
        return trend_data
    
    async def invalidate_cache(
        self, 
        cache_type: CacheType,
        pattern: Optional[str] = None
    ) -> int:
        """Invalidate cache entries."""
        if not self.redis_client:
            return 0
        
        try:
            prefix = f"cache:{cache_type.value}:"
            search_pattern = f"{prefix}{pattern or '*'}"
            
            # Find matching keys
            keys = []
            cursor = 0
            while True:
                cursor, batch_keys = await self.redis_client.scan(
                    cursor=cursor, 
                    match=search_pattern, 
                    count=100
                )
                keys.extend(batch_keys)
                if cursor == 0:
                    break
            
            # Delete keys in batches
            deleted_count = 0
            if keys:
                batch_size = 100
                for i in range(0, len(keys), batch_size):
                    batch = keys[i:i + batch_size]
                    deleted_count += await self.redis_client.delete(*batch)
            
            logger.info(f"Invalidated {deleted_count} cache entries for {cache_type.value}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return 0
    
    async def _get_from_cache(self, cache_type: CacheType, key: str) -> Optional[Any]:
        """Get data from Redis cache."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"cache:{cache_type.value}:{key}"
            cached_data = await self.redis_client.get(cache_key)
            
            if not cached_data:
                return None
            
            config = self.cache_configs[cache_type]
            
            # Decompress if needed
            if config.compression_enabled:
                try:
                    cached_data = gzip.decompress(cached_data)
                except (OSError, EOFError, gzip.BadGzipFile) as e:
                    # Fallback for non-compressed data
                    logger.debug(f"Failed to decompress cache data, using as-is: {e}")
                    pass
            
            # Deserialize
            try:
                return pickle.loads(cached_data)
            except (pickle.UnpicklingError, EOFError, AttributeError, ImportError, IndexError) as e:
                # Fallback to JSON
                logger.debug(f"Failed to unpickle cache data, trying JSON: {e}")
                if isinstance(cached_data, bytes):
                    return json.loads(cached_data.decode('utf-8'))
                else:
                    return json.loads(cached_data)
            
        except Exception as e:
            logger.warning(f"Failed to get from cache {cache_type.value}:{key}: {e}")
            return None
    
    async def _set_in_cache(
        self, 
        cache_type: CacheType, 
        key: str, 
        data: Any
    ) -> bool:
        """Set data in Redis cache."""
        if not self.redis_client:
            return False
        
        try:
            config = self.cache_configs[cache_type]
            cache_key = f"cache:{cache_type.value}:{key}"
            
            # Serialize data
            try:
                serialized_data = pickle.dumps(data)
            except (pickle.PicklingError, TypeError) as e:
                # Fallback to JSON
                logger.debug(f"Failed to pickle data, using JSON: {e}")
                serialized_data = json.dumps(data, default=str).encode('utf-8')
            
            # Compress if enabled
            if config.compression_enabled:
                serialized_data = gzip.compress(serialized_data)
            
            # Set with TTL
            await self.redis_client.setex(
                cache_key,
                config.ttl_seconds,
                serialized_data
            )
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to set cache {cache_type.value}:{key}: {e}")
            return False
    
    def _get_from_local_cache(self, key: str) -> Optional[Any]:
        """Get data from local cache."""
        if key not in self.local_cache:
            return None
        
        data, timestamp = self.local_cache[key]
        
        # Check if expired
        if datetime.utcnow() - timestamp > self.local_cache_ttl:
            del self.local_cache[key]
            return None
        
        return data
    
    def _set_in_local_cache(self, key: str, data: Any) -> None:
        """Set data in local cache."""
        # Evict old entries if cache is full
        if len(self.local_cache) >= self.max_local_cache_size:
            # Remove oldest entry
            oldest_key = min(self.local_cache.keys(), 
                           key=lambda k: self.local_cache[k][1])
            del self.local_cache[oldest_key]
        
        self.local_cache[key] = (data, datetime.utcnow())
    
    async def _record_cache_hit(self, cache_type: CacheType) -> None:
        """Record a cache hit for statistics."""
        if cache_type not in self.cache_stats:
            self.cache_stats[cache_type] = CacheStats(
                cache_type=cache_type,
                hit_count=0,
                miss_count=0,
                hit_rate=0.0,
                total_size_mb=0.0,
                entry_count=0,
                avg_ttl_seconds=0.0,
                last_refresh=datetime.utcnow()
            )
        
        stats = self.cache_stats[cache_type]
        stats.hit_count += 1
        stats.hit_rate = stats.hit_count / (stats.hit_count + stats.miss_count)
    
    async def _record_cache_miss(self, cache_type: CacheType) -> None:
        """Record a cache miss for statistics."""
        if cache_type not in self.cache_stats:
            self.cache_stats[cache_type] = CacheStats(
                cache_type=cache_type,
                hit_count=0,
                miss_count=0,
                hit_rate=0.0,
                total_size_mb=0.0,
                entry_count=0,
                avg_ttl_seconds=0.0,
                last_refresh=datetime.utcnow()
            )
        
        stats = self.cache_stats[cache_type]
        stats.miss_count += 1
        stats.hit_rate = stats.hit_count / (stats.hit_count + stats.miss_count)
    
    async def _initialize_cache_stats(self) -> None:
        """Initialize cache statistics."""
        for cache_type in CacheType:
            self.cache_stats[cache_type] = CacheStats(
                cache_type=cache_type,
                hit_count=0,
                miss_count=0,
                hit_rate=0.0,
                total_size_mb=0.0,
                entry_count=0,
                avg_ttl_seconds=0.0,
                last_refresh=datetime.utcnow()
            )
    
    async def _start_refresh_tasks(self) -> None:
        """Start background refresh tasks for refresh-ahead caches."""
        self.refresh_running = True
        
        for cache_type, config in self.cache_configs.items():
            if config.strategy == CacheStrategy.REFRESH_AHEAD:
                task = asyncio.create_task(self._refresh_ahead_loop(cache_type))
                self.refresh_tasks[cache_type] = task
        
        logger.info(f"Started {len(self.refresh_tasks)} refresh-ahead tasks")
    
    async def _refresh_ahead_loop(self, cache_type: CacheType) -> None:
        """Background loop for refresh-ahead caching."""
        config = self.cache_configs[cache_type]
        
        while self.refresh_running:
            try:
                # Check for keys that need refresh
                await self._refresh_expiring_keys(cache_type)
                
                # Sleep for a portion of the TTL
                sleep_time = min(300, config.ttl_seconds * 0.1)  # Max 5 minutes
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Refresh-ahead loop error for {cache_type.value}: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _refresh_expiring_keys(self, cache_type: CacheType) -> None:
        """Refresh keys that are about to expire."""
        if not self.redis_client:
            return
        
        try:
            config = self.cache_configs[cache_type]
            prefix = f"cache:{cache_type.value}:"
            
            # Find keys for this cache type
            keys = []
            cursor = 0
            while True:
                cursor, batch_keys = await self.redis_client.scan(
                    cursor=cursor,
                    match=f"{prefix}*",
                    count=100
                )
                keys.extend(batch_keys)
                if cursor == 0:
                    break
            
            # Check TTL for each key and refresh if needed
            refresh_threshold = config.ttl_seconds * config.refresh_threshold
            
            for key in keys:
                try:
                    ttl = await self.redis_client.ttl(key)
                    if 0 < ttl < refresh_threshold:
                        # Key is about to expire, refresh it
                        await self._refresh_cache_key(cache_type, key)
                except Exception as e:
                    logger.warning(f"Failed to check TTL for {key}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to refresh expiring keys for {cache_type.value}: {e}")
    
    async def _refresh_cache_key(self, cache_type: CacheType, cache_key: str) -> None:
        """Refresh a specific cache key."""
        try:
            # Extract the original key from the cache key
            prefix = f"cache:{cache_type.value}:"
            if not cache_key.startswith(prefix):
                return
            
            original_key = cache_key[len(prefix):]
            
            # Refresh based on cache type
            if cache_type == CacheType.INDUSTRY_TEMPLATES:
                if original_key.startswith("template:"):
                    template_id = int(original_key.split(":")[1])
                    await self.get_industry_template(template_id)
            
            elif cache_type == CacheType.TEMPLATE_DATA:
                if original_key.startswith("templates_by_sector:"):
                    sector = original_key.split(":", 1)[1]
                    await self.get_industry_templates_by_sector(sector)
            
            # Add more refresh logic for other cache types as needed
            
        except Exception as e:
            logger.warning(f"Failed to refresh cache key {cache_key}: {e}")
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        # Update statistics if needed
        if datetime.utcnow() - self.last_stats_update > self.stats_update_interval:
            await self._update_cache_statistics()
        
        stats_dict = {}
        for cache_type, stats in self.cache_stats.items():
            stats_dict[cache_type.value] = asdict(stats)
        
        return {
            "cache_stats": stats_dict,
            "local_cache_size": len(self.local_cache),
            "refresh_tasks_running": len(self.refresh_tasks),
            "redis_connected": self.redis_client is not None
        }
    
    async def _update_cache_statistics(self) -> None:
        """Update cache statistics from Redis."""
        if not self.redis_client:
            return
        
        try:
            for cache_type in CacheType:
                prefix = f"cache:{cache_type.value}:"
                
                # Count keys and estimate size
                keys = []
                cursor = 0
                while True:
                    cursor, batch_keys = await self.redis_client.scan(
                        cursor=cursor,
                        match=f"{prefix}*",
                        count=100
                    )
                    keys.extend(batch_keys)
                    if cursor == 0:
                        break
                
                # Update statistics
                stats = self.cache_stats[cache_type]
                stats.entry_count = len(keys)
                
                # Estimate total size (sample a few keys)
                if keys:
                    sample_size = min(10, len(keys))
                    sample_keys = keys[:sample_size]
                    total_sample_size = 0
                    
                    for key in sample_keys:
                        try:
                            size = await self.redis_client.memory_usage(key)
                            if size:
                                total_sample_size += size
                        except:
                            pass
                    
                    if total_sample_size > 0:
                        avg_size = total_sample_size / sample_size
                        stats.total_size_mb = (avg_size * len(keys)) / (1024 * 1024)
            
            self.last_stats_update = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to update cache statistics: {e}")
    
    async def cleanup_expired_entries(self) -> Dict[str, int]:
        """Clean up expired cache entries."""
        cleanup_counts = {}
        
        if not self.redis_client:
            return cleanup_counts
        
        try:
            for cache_type in CacheType:
                prefix = f"cache:{cache_type.value}:"
                
                # Find all keys for this cache type
                keys = []
                cursor = 0
                while True:
                    cursor, batch_keys = await self.redis_client.scan(
                        cursor=cursor,
                        match=f"{prefix}*",
                        count=100
                    )
                    keys.extend(batch_keys)
                    if cursor == 0:
                        break
                
                # Check each key and delete if expired
                expired_keys = []
                for key in keys:
                    try:
                        ttl = await self.redis_client.ttl(key)
                        if ttl == -2:  # Key doesn't exist or expired
                            expired_keys.append(key)
                    except:
                        pass
                
                # Delete expired keys
                if expired_keys:
                    await self.redis_client.delete(*expired_keys)
                
                cleanup_counts[cache_type.value] = len(expired_keys)
            
            logger.info(f"Cleaned up expired cache entries: {cleanup_counts}")
            return cleanup_counts
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")
            return cleanup_counts
    
    async def shutdown(self) -> None:
        """Shutdown the cache manager."""
        try:
            # Stop refresh tasks
            self.refresh_running = False
            
            for task in self.refresh_tasks.values():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Cache manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during cache manager shutdown: {e}")