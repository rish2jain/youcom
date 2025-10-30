"""
Performance Monitoring Framework - Week 1 Implementation
Real-time metrics, optimization tracking, and performance analytics.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.api_call_log import ApiCallLog
from app.models.ml_training import ModelPerformanceMetric, TrainingJob
# Removed circular import - will import dynamically when needed
from app.realtime import emit_progress

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemHealth:
    """Overall system health status"""
    status: str  # healthy, degraded, critical
    score: float  # 0-100
    issues: List[str]
    recommendations: List[str]
    last_updated: datetime

class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self):
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.redis_client: Optional[Redis] = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection for metrics storage"""
        try:
            self.redis_client = Redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis unavailable for metrics: {e}")
            self.redis_client = None
    
    async def record_metric(
        self,
        name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Store in memory buffer
        self.metrics_buffer[name].append(metric)
        
        # Store in Redis for persistence
        if self.redis_client:
            try:
                key = f"metrics:{name}:{int(time.time())}"
                data = {
                    "value": value,
                    "timestamp": metric.timestamp.isoformat(),
                    "metadata": metadata or {}
                }
                await self.redis_client.set(key, json.dumps(data), ex=3600)  # 1 hour TTL
            except RedisError as e:
                logger.warning(f"Failed to store metric in Redis: {e}")
    
    async def get_metrics(
        self,
        name: str,
        duration_minutes: int = 60
    ) -> List[PerformanceMetric]:
        """Get metrics for the specified duration"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=duration_minutes)
        
        # Get from memory buffer first
        memory_metrics = [
            metric for metric in self.metrics_buffer[name]
            if metric.timestamp >= cutoff_time
        ]
        
        if memory_metrics:
            return memory_metrics
        
        # Fallback to Redis if available
        if self.redis_client:
            try:
                pattern = f"metrics:{name}:*"
                keys = []
                cursor = 0
                while True:
                    cursor, batch_keys = await self.redis_client.scan(cursor=cursor, match=pattern, count=100)
                    keys.extend(batch_keys)
                    if cursor == 0:
                        break
                
                metrics = []
                for key in keys:
                    data = await self.redis_client.get(key)
                    if data:
                        parsed = json.loads(data)
                        timestamp = datetime.fromisoformat(parsed["timestamp"])
                        if timestamp >= cutoff_time:
                            metrics.append(PerformanceMetric(
                                name=name,
                                value=parsed["value"],
                                timestamp=timestamp,
                                metadata=parsed.get("metadata", {})
                            ))
                
                return sorted(metrics, key=lambda m: m.timestamp)
            
            except RedisError as e:
                logger.warning(f"Failed to retrieve metrics from Redis: {e}")
        
        return []
    
    async def get_aggregated_metrics(
        self,
        name: str,
        duration_minutes: int = 60
    ) -> Dict[str, float]:
        """Get aggregated metrics (avg, min, max, p95, p99)"""
        metrics = await self.get_metrics(name, duration_minutes)
        
        if not metrics:
            return {
                "count": 0,
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
        
        values = [m.value for m in metrics]
        
        return {
            "count": len(values),
            "avg": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "p95": statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
            "p99": statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values)
        }

class PerformanceAnalyzer:
    """Analyzes performance trends and identifies issues"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        
        # Performance thresholds
        self.thresholds = {
            "api_latency": {"warning": 5000, "critical": 10000},  # milliseconds
            "success_rate": {"warning": 0.95, "critical": 0.90},  # percentage
            "cache_hit_rate": {"warning": 0.70, "critical": 0.50},  # percentage
            "error_rate": {"warning": 0.05, "critical": 0.10},  # percentage
            "ml_f1_score": {"warning": 0.85, "critical": 0.75},  # ML model performance
        }
    
    async def analyze_system_health(self) -> SystemHealth:
        """Analyze overall system health"""
        issues = []
        recommendations = []
        scores = []
        
        # Analyze API latency
        latency_score, latency_issues, latency_recs = await self._analyze_latency()
        scores.append(latency_score)
        issues.extend(latency_issues)
        recommendations.extend(latency_recs)
        
        # Analyze success rates
        success_score, success_issues, success_recs = await self._analyze_success_rates()
        scores.append(success_score)
        issues.extend(success_issues)
        recommendations.extend(success_recs)
        
        # Analyze cache performance
        cache_score, cache_issues, cache_recs = await self._analyze_cache_performance()
        scores.append(cache_score)
        issues.extend(cache_issues)
        recommendations.extend(cache_recs)
        
        # Analyze ML model performance
        ml_score, ml_issues, ml_recs = await self._analyze_ml_performance()
        scores.append(ml_score)
        issues.extend(ml_issues)
        recommendations.extend(ml_recs)
        
        # Analyze benchmarking performance
        benchmark_score, benchmark_issues, benchmark_recs = await self._analyze_benchmark_performance()
        scores.append(benchmark_score)
        issues.extend(benchmark_issues)
        recommendations.extend(benchmark_recs)
        
        # Calculate overall score
        overall_score = statistics.mean(scores) if scores else 0.0
        
        # Determine status
        if overall_score >= 90:
            status = "healthy"
        elif overall_score >= 70:
            status = "degraded"
        else:
            status = "critical"
        
        return SystemHealth(
            status=status,
            score=overall_score,
            issues=issues,
            recommendations=recommendations,
            last_updated=datetime.utcnow()
        )
    
    async def _analyze_latency(self) -> Tuple[float, List[str], List[str]]:
        """Analyze API latency metrics"""
        issues = []
        recommendations = []
        
        # Get latency metrics for each API
        api_latencies = {}
        for api in ["news", "search", "chat", "ari"]:
            metrics = await self.metrics_collector.get_aggregated_metrics(
                f"api_latency_{api}", 60
            )
            api_latencies[api] = metrics
        
        # Calculate score based on latency thresholds
        scores = []
        for api, metrics in api_latencies.items():
            if metrics["count"] == 0:
                continue
            
            avg_latency = metrics["avg"]
            p95_latency = metrics["p95"]
            
            # Score based on p95 latency
            if p95_latency <= self.thresholds["api_latency"]["warning"]:
                score = 100
            elif p95_latency <= self.thresholds["api_latency"]["critical"]:
                score = 70
            else:
                score = 30
                issues.append(f"{api} API latency is critical (p95: {p95_latency:.0f}ms)")
                recommendations.append(f"Optimize {api} API queries and add caching")
            
            scores.append(score)
        
        overall_score = statistics.mean(scores) if scores else 100
        
        return overall_score, issues, recommendations
    
    async def _analyze_success_rates(self) -> Tuple[float, List[str], List[str]]:
        """Analyze API success rates"""
        issues = []
        recommendations = []
        
        # Get success rate metrics
        success_rates = {}
        for api in ["news", "search", "chat", "ari"]:
            metrics = await self.metrics_collector.get_aggregated_metrics(
                f"success_rate_{api}", 60
            )
            success_rates[api] = metrics
        
        scores = []
        for api, metrics in success_rates.items():
            if metrics["count"] == 0:
                continue
            
            success_rate = metrics["avg"]
            
            if success_rate >= self.thresholds["success_rate"]["warning"]:
                score = 100
            elif success_rate >= self.thresholds["success_rate"]["critical"]:
                score = 70
                issues.append(f"{api} API success rate is low ({success_rate:.1%})")
                recommendations.append(f"Review {api} API error patterns and improve resilience")
            else:
                score = 30
                issues.append(f"{api} API success rate is critical ({success_rate:.1%})")
                recommendations.append(f"Urgent: Fix {api} API reliability issues")
            
            scores.append(score)
        
        overall_score = statistics.mean(scores) if scores else 100
        
        return overall_score, issues, recommendations
    
    async def _analyze_cache_performance(self) -> Tuple[float, List[str], List[str]]:
        """Analyze cache performance"""
        issues = []
        recommendations = []
        
        # Get cache hit rate metrics
        cache_metrics = await self.metrics_collector.get_aggregated_metrics(
            "cache_hit_rate", 60
        )
        
        if cache_metrics["count"] == 0:
            return 100, [], []
        
        hit_rate = cache_metrics["avg"]
        
        if hit_rate >= self.thresholds["cache_hit_rate"]["warning"]:
            score = 100
        elif hit_rate >= self.thresholds["cache_hit_rate"]["critical"]:
            score = 70
            issues.append(f"Cache hit rate is low ({hit_rate:.1%})")
            recommendations.append("Optimize cache TTL settings and query patterns")
        else:
            score = 30
            issues.append(f"Cache hit rate is critical ({hit_rate:.1%})")
            recommendations.append("Urgent: Review cache strategy and increase TTL")
        
        return score, issues, recommendations
    
    async def _analyze_ml_performance(self) -> Tuple[float, List[str], List[str]]:
        """Analyze ML model performance"""
        issues = []
        recommendations = []
        
        try:
            async with AsyncSessionLocal() as session:
                # Get latest ML model performance metrics
                result = await session.execute(
                    select(ModelPerformanceMetric)
                    .where(ModelPerformanceMetric.metric_name == "f1_score")
                    .where(ModelPerformanceMetric.evaluation_timestamp >= datetime.utcnow() - timedelta(hours=24))
                    .order_by(desc(ModelPerformanceMetric.evaluation_timestamp))
                )
                
                recent_metrics = result.scalars().all()
                
                if not recent_metrics:
                    return 50, ["No recent ML model performance data"], ["Set up ML model monitoring"]
                
                # Calculate average F1 score across all models
                f1_scores = [metric.metric_value for metric in recent_metrics]
                avg_f1_score = sum(f1_scores) / len(f1_scores)
                
                # Check for failing models
                failing_models = []
                for metric in recent_metrics:
                    if metric.metric_value < self.thresholds["ml_f1_score"]["critical"]:
                        failing_models.append(metric.model_type)
                
                # Calculate score
                if avg_f1_score >= self.thresholds["ml_f1_score"]["warning"]:
                    score = 100
                elif avg_f1_score >= self.thresholds["ml_f1_score"]["critical"]:
                    score = 70
                    issues.append(f"ML model performance is degraded (avg F1: {avg_f1_score:.3f})")
                    recommendations.append("Review ML model training data and retrain models")
                else:
                    score = 30
                    issues.append(f"ML model performance is critical (avg F1: {avg_f1_score:.3f})")
                    recommendations.append("Urgent: Retrain ML models with fresh data")
                
                if failing_models:
                    issues.append(f"Failing ML models: {', '.join(set(failing_models))}")
                    recommendations.append("Investigate and retrain failing ML models")
                
                # Check for recent training failures
                training_result = await session.execute(
                    select(TrainingJob)
                    .where(TrainingJob.status == "failed")
                    .where(TrainingJob.created_at >= datetime.utcnow() - timedelta(hours=24))
                )
                
                failed_jobs = training_result.scalars().all()
                if failed_jobs:
                    issues.append(f"{len(failed_jobs)} ML training jobs failed in the last 24 hours")
                    recommendations.append("Review ML training job failures and fix issues")
                
                return score, issues, recommendations
                
        except Exception as e:
            logger.error(f"Error analyzing ML performance: {e}")
            return 50, ["ML performance analysis failed"], ["Check ML monitoring system"]
    
    async def _analyze_benchmark_performance(self) -> Tuple[float, List[str], List[str]]:
        """Analyze benchmarking system performance"""
        issues = []
        recommendations = []
        
        try:
            async with AsyncSessionLocal() as session:
                # Initialize benchmarking integration service (dynamic import to avoid circular dependency)
                from app.services.benchmarking_integration import BenchmarkingIntegrationService
                benchmark_integration = BenchmarkingIntegrationService(session)
                
                # Get integration status
                integration_status = await benchmark_integration.get_integration_status()
                
                health = integration_status.get("integration_health", "poor")
                metrics = integration_status.get("metrics", {})
                
                # Calculate score based on health and metrics
                if health == "excellent":
                    score = 100
                elif health == "good":
                    score = 80
                elif health == "fair":
                    score = 60
                    issues.append("Benchmarking system performance is fair")
                    recommendations.append("Increase benchmark data collection frequency")
                else:
                    score = 30
                    issues.append("Benchmarking system performance is poor")
                    recommendations.append("Review benchmarking system configuration")
                
                # Check specific metrics
                metrics_24h = metrics.get("benchmark_metrics_24h", 0)
                comparisons_24h = metrics.get("benchmark_comparisons_24h", 0)
                
                if metrics_24h == 0:
                    issues.append("No benchmark metrics collected in the last 24 hours")
                    recommendations.append("Check benchmark metrics collection process")
                
                if comparisons_24h == 0:
                    issues.append("No benchmark comparisons performed in the last 24 hours")
                    recommendations.append("Trigger benchmark comparison calculations")
                
                # Check for benchmark alerts
                alerts_triggered = metrics.get("alerts_triggered", 0)
                if alerts_triggered > 10:
                    issues.append(f"High number of benchmark alerts: {alerts_triggered}")
                    recommendations.append("Investigate performance issues causing benchmark alerts")
                
                return score, issues, recommendations
                
        except Exception as e:
            logger.error(f"Error analyzing benchmark performance: {e}")
            return 50, ["Benchmark performance analysis failed"], ["Check benchmarking system"]

class RealTimeMonitor:
    """Real-time performance monitoring and alerting"""
    
    def __init__(self, metrics_collector: MetricsCollector, analyzer: PerformanceAnalyzer):
        self.metrics_collector = metrics_collector
        self.analyzer = analyzer
        self.monitoring_active = False
        self.alert_thresholds = {
            "latency_spike": 15000,  # 15 seconds
            "error_burst": 5,        # 5 errors in 1 minute
            "cache_miss_spike": 0.9  # 90% cache misses
        }
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        logger.info("🔍 Starting real-time performance monitoring")
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_latency())
        asyncio.create_task(self._monitor_errors())
        asyncio.create_task(self._monitor_cache())
        asyncio.create_task(self._health_check_loop())
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        logger.info("⏹️ Stopping real-time performance monitoring")
    
    async def _monitor_latency(self):
        """Monitor for latency spikes"""
        while self.monitoring_active:
            try:
                for api in ["news", "search", "chat", "ari"]:
                    metrics = await self.metrics_collector.get_metrics(
                        f"api_latency_{api}", 5  # Last 5 minutes
                    )
                    
                    if metrics:
                        recent_latencies = [m.value for m in metrics[-10:]]  # Last 10 calls
                        if recent_latencies:
                            avg_latency = statistics.mean(recent_latencies)
                            
                            if avg_latency > self.alert_thresholds["latency_spike"]:
                                await self._send_alert(
                                    "latency_spike",
                                    f"{api} API latency spike: {avg_latency:.0f}ms",
                                    {"api": api, "latency": avg_latency}
                                )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in latency monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_errors(self):
        """Monitor for error bursts"""
        while self.monitoring_active:
            try:
                # Check database for recent errors
                async with AsyncSessionLocal() as session:
                    cutoff_time = datetime.utcnow() - timedelta(minutes=1)
                    
                    result = await session.execute(
                        select(func.count(ApiCallLog.id))
                        .where(
                            ApiCallLog.created_at >= cutoff_time,
                            ApiCallLog.success == False
                        )
                    )
                    
                    error_count = result.scalar() or 0
                    
                    if error_count >= self.alert_thresholds["error_burst"]:
                        await self._send_alert(
                            "error_burst",
                            f"Error burst detected: {error_count} errors in 1 minute",
                            {"error_count": error_count}
                        )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in error monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_cache(self):
        """Monitor cache performance"""
        while self.monitoring_active:
            try:
                cache_metrics = await self.metrics_collector.get_metrics(
                    "cache_hit_rate", 5  # Last 5 minutes
                )
                
                if cache_metrics:
                    recent_hit_rates = [m.value for m in cache_metrics[-10:]]
                    if recent_hit_rates:
                        avg_hit_rate = statistics.mean(recent_hit_rates)
                        
                        if avg_hit_rate < (1 - self.alert_thresholds["cache_miss_spike"]):
                            await self._send_alert(
                                "cache_miss_spike",
                                f"Cache miss spike: {(1-avg_hit_rate):.1%} miss rate",
                                {"hit_rate": avg_hit_rate}
                            )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in cache monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _health_check_loop(self):
        """Periodic health check and reporting"""
        while self.monitoring_active:
            try:
                health = await self.analyzer.analyze_system_health()
                
                # Emit health status via WebSocket
                await emit_progress(
                    "system_health",
                    {
                        "status": health.status,
                        "score": health.score,
                        "issues": health.issues,
                        "recommendations": health.recommendations,
                        "timestamp": health.last_updated.isoformat()
                    }
                )
                
                # Log health status
                logger.info(f"🏥 System Health: {health.status} ({health.score:.1f}/100)")
                
                if health.issues:
                    logger.warning(f"⚠️ Issues detected: {', '.join(health.issues)}")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                await asyncio.sleep(300)
    
    async def _send_alert(self, alert_type: str, message: str, metadata: Dict[str, Any]):
        """Send performance alert"""
        logger.warning(f"🚨 ALERT [{alert_type}]: {message}")
        
        # Emit alert via WebSocket
        await emit_progress(
            "performance_alert",
            {
                "type": alert_type,
                "message": message,
                "metadata": metadata,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Record alert metric
        await self.metrics_collector.record_metric(
            f"alert_{alert_type}",
            1.0,
            metadata
        )

class PerformanceOptimizer:
    """Automatically optimizes performance based on metrics"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.optimization_history = []
    
    async def optimize_cache_ttl(self) -> Dict[str, Any]:
        """Optimize cache TTL based on hit rates"""
        cache_metrics = await self.metrics_collector.get_aggregated_metrics(
            "cache_hit_rate", 60
        )
        
        if cache_metrics["count"] == 0:
            return {"status": "no_data", "action": "none"}
        
        hit_rate = cache_metrics["avg"]
        
        # Optimization logic
        if hit_rate < 0.6:
            # Low hit rate - increase TTL
            recommendation = {
                "action": "increase_ttl",
                "current_hit_rate": hit_rate,
                "recommended_multiplier": 1.5,
                "reason": "Low cache hit rate detected"
            }
        elif hit_rate > 0.9:
            # Very high hit rate - might be able to decrease TTL for fresher data
            recommendation = {
                "action": "decrease_ttl",
                "current_hit_rate": hit_rate,
                "recommended_multiplier": 0.8,
                "reason": "Very high hit rate - can afford fresher data"
            }
        else:
            recommendation = {
                "action": "maintain",
                "current_hit_rate": hit_rate,
                "reason": "Cache performance is optimal"
            }
        
        self.optimization_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "cache_ttl",
            "recommendation": recommendation
        })
        
        return recommendation
    
    async def optimize_query_routing(self) -> Dict[str, Any]:
        """Optimize query routing based on performance patterns"""
        # Analyze latency patterns for different query types
        routing_metrics = {}
        
        for route in ["fast_track", "standard", "deep_dive"]:
            metrics = await self.metrics_collector.get_aggregated_metrics(
                f"route_latency_{route}", 60
            )
            routing_metrics[route] = metrics
        
        # Find optimal routing thresholds
        recommendations = []
        
        for route, metrics in routing_metrics.items():
            if metrics["count"] > 0:
                if metrics["p95"] > 30000:  # 30 seconds
                    recommendations.append(f"Reduce {route} route usage - high latency")
                elif metrics["avg"] < 5000:  # 5 seconds
                    recommendations.append(f"Increase {route} route usage - good performance")
        
        optimization = {
            "routing_metrics": routing_metrics,
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.optimization_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": "query_routing",
            "optimization": optimization
        })
        
        return optimization
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report"""
        return {
            "cache_optimization": await self.optimize_cache_ttl(),
            "routing_optimization": await self.optimize_query_routing(),
            "optimization_history": self.optimization_history[-10:],  # Last 10 optimizations
            "generated_at": datetime.utcnow().isoformat()
        }

# Global instances
metrics_collector = MetricsCollector()
performance_analyzer = PerformanceAnalyzer(metrics_collector)
real_time_monitor = RealTimeMonitor(metrics_collector, performance_analyzer)
performance_optimizer = PerformanceOptimizer(metrics_collector)

# Startup function
async def start_performance_monitoring():
    """Start the performance monitoring system"""
    await real_time_monitor.start_monitoring()
    logger.info("🚀 Performance monitoring system started")

# Shutdown function
async def stop_performance_monitoring():
    """Stop the performance monitoring system"""
    await real_time_monitor.stop_monitoring()
    logger.info("⏹️ Performance monitoring system stopped")