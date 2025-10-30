"""
Metrics Aggregation Service for Advanced Benchmarking Dashboard
Collects performance data from various sources and stores in TimescaleDB
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import statistics
import json

from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.database import AsyncSessionLocal
from app.config import settings
from app.models.benchmarking import BenchmarkMetric, IndustryBenchmark
from app.models.api_call_log import ApiCallLog
from app.models.impact_card import ImpactCard
from app.models.watch import WatchItem
from app.models.ml_training import ModelPerformanceMetric
# Removed circular import - will import dynamically when needed

logger = logging.getLogger(__name__)


@dataclass
class MetricDataPoint:
    """Individual metric data point"""
    metric_name: str
    value: float
    timestamp: datetime
    source_system: str
    category: str
    unit: str
    workspace_id: Optional[str] = None
    user_id: Optional[str] = None
    industry_sector: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AggregatedMetrics:
    """Aggregated metrics with statistical measures"""
    metric_name: str
    count: int
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentiles: Dict[int, float]  # 25, 50, 75, 90, 95, 99
    time_period: str
    period_start: datetime
    period_end: datetime


class MetricsCollector:
    """Collects performance metrics from various system sources"""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self._redis_initialized = False
    
    async def _initialize_redis(self):
        """Initialize Redis connection for caching"""
        if self._redis_initialized:
            return
            
        try:
            self.redis_client = Redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test the connection
            await self.redis_client.ping()
            self._redis_initialized = True
        except Exception as e:
            logger.warning(f"Redis unavailable for metrics caching: {e}")
            self.redis_client = None
            self._redis_initialized = True
    
    async def collect_api_performance_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        workspace_id: Optional[str] = None
    ) -> List[MetricDataPoint]:
        """Collect API performance metrics from API call logs"""
        metrics = []
        
        async with AsyncSessionLocal() as session:
            # Build query conditions
            conditions = [
                ApiCallLog.created_at >= start_time,
                ApiCallLog.created_at <= end_time
            ]
            
            if workspace_id:
                conditions.append(ApiCallLog.workspace_id == workspace_id)
            
            # Get API call data
            result = await session.execute(
                select(ApiCallLog)
                .where(and_(*conditions))
                .order_by(ApiCallLog.created_at)
            )
            
            api_calls = result.scalars().all()
            
            # Process API calls into metrics
            for call in api_calls:
                # Response time metric
                if call.response_time_ms:
                    metrics.append(MetricDataPoint(
                        metric_name=f"api_response_time_{call.api_endpoint}",
                        value=call.response_time_ms,
                        timestamp=call.created_at,
                        source_system="cia",
                        category="performance",
                        unit="milliseconds",
                        workspace_id=call.workspace_id,
                        metadata={
                            "endpoint": call.api_endpoint,
                            "success": call.success,
                            "status_code": call.status_code
                        }
                    ))
                
                # Success rate metric (1.0 for success, 0.0 for failure)
                metrics.append(MetricDataPoint(
                    metric_name=f"api_success_rate_{call.api_endpoint}",
                    value=1.0 if call.success else 0.0,
                    timestamp=call.created_at,
                    source_system="cia",
                    category="quality",
                    unit="percentage",
                    workspace_id=call.workspace_id,
                    metadata={
                        "endpoint": call.api_endpoint,
                        "error_message": call.error_message
                    }
                ))
        
        logger.info(f"Collected {len(metrics)} API performance metrics")
        return metrics
    
    async def collect_intelligence_quality_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        workspace_id: Optional[str] = None
    ) -> List[MetricDataPoint]:
        """Collect intelligence quality metrics from impact cards"""
        metrics = []
        
        async with AsyncSessionLocal() as session:
            # Build query conditions
            conditions = [
                ImpactCard.created_at >= start_time,
                ImpactCard.created_at <= end_time
            ]
            
            if workspace_id:
                conditions.append(ImpactCard.workspace_id == workspace_id)
            
            # Get impact cards
            result = await session.execute(
                select(ImpactCard)
                .where(and_(*conditions))
                .order_by(ImpactCard.created_at)
            )
            
            impact_cards = result.scalars().all()
            
            # Process impact cards into metrics
            for card in impact_cards:
                # Risk score accuracy (based on confidence)
                if hasattr(card, 'confidence_score') and card.confidence_score:
                    metrics.append(MetricDataPoint(
                        metric_name="intelligence_confidence",
                        value=card.confidence_score * 100,  # Convert to percentage
                        timestamp=card.created_at,
                        source_system="cia",
                        category="quality",
                        unit="percentage",
                        workspace_id=card.workspace_id,
                        metadata={
                            "risk_level": card.risk_level,
                            "competitor": card.competitor_name
                        }
                    ))
                
                # Detection speed (time from news to impact card)
                if hasattr(card, 'detection_time_minutes'):
                    metrics.append(MetricDataPoint(
                        metric_name="detection_speed",
                        value=card.detection_time_minutes,
                        timestamp=card.created_at,
                        source_system="cia",
                        category="performance",
                        unit="minutes",
                        workspace_id=card.workspace_id,
                        metadata={
                            "risk_level": card.risk_level
                        }
                    ))
                
                # Source diversity (number of sources)
                source_count = len(card.sources) if card.sources else 1
                metrics.append(MetricDataPoint(
                    metric_name="source_diversity",
                    value=source_count,
                    timestamp=card.created_at,
                    source_system="cia",
                    category="coverage",
                    unit="count",
                    workspace_id=card.workspace_id,
                    metadata={
                        "risk_level": card.risk_level
                    }
                ))
        
        logger.info(f"Collected {len(metrics)} intelligence quality metrics")
        return metrics
    
    async def collect_ml_performance_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[MetricDataPoint]:
        """Collect ML model performance metrics"""
        metrics = []
        
        async with AsyncSessionLocal() as session:
            # Get ML performance metrics
            result = await session.execute(
                select(ModelPerformanceMetric)
                .where(
                    and_(
                        ModelPerformanceMetric.evaluation_timestamp >= start_time,
                        ModelPerformanceMetric.evaluation_timestamp <= end_time
                    )
                )
                .order_by(ModelPerformanceMetric.evaluation_timestamp)
            )
            
            ml_metrics = result.scalars().all()
            
            # Process ML metrics
            for ml_metric in ml_metrics:
                metrics.append(MetricDataPoint(
                    metric_name=f"ml_{ml_metric.metric_name}",
                    value=ml_metric.metric_value,
                    timestamp=ml_metric.evaluation_timestamp,
                    source_system="cia",
                    category="ml_performance",
                    unit="score",
                    metadata={
                        "model_version": ml_metric.model_version,
                        "model_type": ml_metric.model_type,
                        "dataset_size": ml_metric.dataset_size
                    }
                ))
        
        logger.info(f"Collected {len(metrics)} ML performance metrics")
        return metrics
    
    async def collect_coverage_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        workspace_id: Optional[str] = None
    ) -> List[MetricDataPoint]:
        """Collect competitive coverage metrics"""
        metrics = []
        
        async with AsyncSessionLocal() as session:
            # Get watchlist coverage
            conditions = []
            if workspace_id:
                conditions.append(WatchItem.workspace_id == workspace_id)
            
            # Count active watchlists
            query = select(func.count(WatchItem.id))
            if conditions:
                query = query.where(and_(*conditions))
            watchlist_result = await session.execute(query)
            
            watchlist_count = watchlist_result.scalar() or 0
            
            # Coverage completeness metric
            metrics.append(MetricDataPoint(
                metric_name="watchlist_coverage",
                value=watchlist_count,
                timestamp=datetime.utcnow(),
                source_system="cia",
                category="coverage",
                unit="count",
                workspace_id=workspace_id,
                metadata={
                    "measurement_type": "active_watchlists"
                }
            ))
            
            # Get impact card coverage for the period
            impact_conditions = [
                ImpactCard.created_at >= start_time,
                ImpactCard.created_at <= end_time
            ]
            
            if workspace_id:
                impact_conditions.append(ImpactCard.workspace_id == workspace_id)
            
            impact_result = await session.execute(
                select(func.count(ImpactCard.id))
                .where(and_(*impact_conditions))
            )
            
            impact_count = impact_result.scalar() or 0
            
            # Intelligence generation rate
            period_hours = (end_time - start_time).total_seconds() / 3600
            generation_rate = impact_count / period_hours if period_hours > 0 else 0
            
            metrics.append(MetricDataPoint(
                metric_name="intelligence_generation_rate",
                value=generation_rate,
                timestamp=datetime.utcnow(),
                source_system="cia",
                category="coverage",
                unit="cards_per_hour",
                workspace_id=workspace_id,
                metadata={
                    "period_hours": period_hours,
                    "total_cards": impact_count
                }
            ))
        
        logger.info(f"Collected {len(metrics)} coverage metrics")
        return metrics


class MetricsAggregator:
    """Aggregates collected metrics and stores them in the database"""
    
    def __init__(self):
        self.collector = MetricsCollector()
    
    async def aggregate_metrics(
        self,
        metric_name: str,
        data_points: List[MetricDataPoint],
        time_period: str = "hourly"
    ) -> AggregatedMetrics:
        """Aggregate metric data points into statistical summary"""
        if not data_points:
            raise ValueError(f"No data points provided for metric: {metric_name}")
        
        values = [dp.value for dp in data_points]
        
        # Calculate percentiles
        percentiles = {}
        if len(values) > 4:  # Need more than 4 points for meaningful percentiles
            percentiles = {
                25: statistics.quantiles(values, n=4)[0],
                50: statistics.median(values),
                75: statistics.quantiles(values, n=4)[2],
                90: statistics.quantiles(values, n=10)[8] if len(values) > 10 else max(values),
                95: statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values),
                99: statistics.quantiles(values, n=100)[98] if len(values) > 100 else max(values)
            }
        else:
            # For small datasets, use available values
            percentiles = {p: max(values) for p in [25, 50, 75, 90, 95, 99]}
        
        return AggregatedMetrics(
            metric_name=metric_name,
            count=len(values),
            mean=statistics.mean(values),
            median=statistics.median(values),
            std_dev=statistics.stdev(values) if len(values) > 1 else 0.0,
            min_value=min(values),
            max_value=max(values),
            percentiles=percentiles,
            time_period=time_period,
            period_start=min(dp.timestamp for dp in data_points),
            period_end=max(dp.timestamp for dp in data_points)
        )
    
    async def store_metrics(
        self,
        data_points: List[MetricDataPoint]
    ) -> int:
        """Store metric data points in the database"""
        if not data_points:
            return 0
        
        async with AsyncSessionLocal() as session:
            # Create BenchmarkMetric records
            metrics_to_store = []
            
            for dp in data_points:
                metric = BenchmarkMetric(
                    metric_name=dp.metric_name,
                    metric_category=dp.category,
                    source_system=dp.source_system,
                    metric_value=dp.value,
                    unit=dp.unit,
                    measurement_timestamp=dp.timestamp,
                    time_period="raw",  # Individual data points
                    workspace_id=dp.workspace_id,
                    user_id=dp.user_id,
                    industry_sector=dp.industry_sector,
                    metric_metadata=dp.metadata or {}
                )
                metrics_to_store.append(metric)
            
            # Batch insert
            session.add_all(metrics_to_store)
            await session.commit()
            
            logger.info(f"Stored {len(metrics_to_store)} metric data points")
            return len(metrics_to_store)
    
    async def store_aggregated_metrics(
        self,
        aggregated: AggregatedMetrics,
        source_system: str = "cia",
        category: str = "performance",
        workspace_id: Optional[str] = None
    ) -> int:
        """Store aggregated metrics in the database"""
        async with AsyncSessionLocal() as session:
            metrics_to_store = []
            
            # Store main aggregated values
            base_metadata = {
                "aggregation_type": "statistical_summary",
                "data_points_count": aggregated.count,
                "period_start": aggregated.period_start.isoformat(),
                "period_end": aggregated.period_end.isoformat()
            }
            
            # Mean
            metrics_to_store.append(BenchmarkMetric(
                metric_name=f"{aggregated.metric_name}_mean",
                metric_category=category,
                source_system=source_system,
                metric_value=aggregated.mean,
                unit="aggregated",
                measurement_timestamp=aggregated.period_end,
                time_period=aggregated.time_period,
                workspace_id=workspace_id,
                metric_metadata={**base_metadata, "statistic": "mean"}
            ))
            
            # Median
            metrics_to_store.append(BenchmarkMetric(
                metric_name=f"{aggregated.metric_name}_median",
                metric_category=category,
                source_system=source_system,
                metric_value=aggregated.median,
                unit="aggregated",
                measurement_timestamp=aggregated.period_end,
                time_period=aggregated.time_period,
                workspace_id=workspace_id,
                metric_metadata={**base_metadata, "statistic": "median"}
            ))
            
            # Percentiles
            for percentile, value in aggregated.percentiles.items():
                metrics_to_store.append(BenchmarkMetric(
                    metric_name=f"{aggregated.metric_name}_p{percentile}",
                    metric_category=category,
                    source_system=source_system,
                    metric_value=value,
                    unit="aggregated",
                    measurement_timestamp=aggregated.period_end,
                    time_period=aggregated.time_period,
                    workspace_id=workspace_id,
                    metric_metadata={**base_metadata, "statistic": f"p{percentile}"}
                ))
            
            # Batch insert
            session.add_all(metrics_to_store)
            await session.commit()
            
            logger.info(f"Stored {len(metrics_to_store)} aggregated metrics for {aggregated.metric_name}")
            return len(metrics_to_store)
    
    async def collect_and_aggregate_all_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        workspace_id: Optional[str] = None
    ) -> Dict[str, AggregatedMetrics]:
        """Collect and aggregate all metrics for a time period"""
        logger.info(f"Collecting metrics from {start_time} to {end_time}")
        
        # Collect all metric types
        all_metrics = []
        
        # API performance metrics
        api_metrics = await self.collector.collect_api_performance_metrics(
            start_time, end_time, workspace_id
        )
        all_metrics.extend(api_metrics)
        
        # Intelligence quality metrics
        quality_metrics = await self.collector.collect_intelligence_quality_metrics(
            start_time, end_time, workspace_id
        )
        all_metrics.extend(quality_metrics)
        
        # ML performance metrics
        ml_metrics = await self.collector.collect_ml_performance_metrics(
            start_time, end_time
        )
        all_metrics.extend(ml_metrics)
        
        # Coverage metrics
        coverage_metrics = await self.collector.collect_coverage_metrics(
            start_time, end_time, workspace_id
        )
        all_metrics.extend(coverage_metrics)
        
        # Store raw metrics
        await self.store_metrics(all_metrics)
        
        # Group metrics by name for aggregation
        metrics_by_name = {}
        for metric in all_metrics:
            if metric.metric_name not in metrics_by_name:
                metrics_by_name[metric.metric_name] = []
            metrics_by_name[metric.metric_name].append(metric)
        
        # Aggregate each metric type
        aggregated_results = {}
        for metric_name, data_points in metrics_by_name.items():
            if len(data_points) > 0:
                try:
                    aggregated = await self.aggregate_metrics(
                        metric_name, data_points, "hourly"
                    )
                    aggregated_results[metric_name] = aggregated
                    
                    # Store aggregated metrics
                    await self.store_aggregated_metrics(
                        aggregated,
                        source_system="cia",
                        category=data_points[0].category,
                        workspace_id=workspace_id
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to aggregate metric {metric_name}: {e}")
        
        logger.info(f"Aggregated {len(aggregated_results)} metric types")
        return aggregated_results


# Global instance
metrics_aggregator = MetricsAggregator()


async def run_metrics_collection(
    hours_back: int = 1,
    workspace_id: Optional[str] = None
) -> Dict[str, AggregatedMetrics]:
    """Run metrics collection for the specified time period"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours_back)
    
    return await metrics_aggregator.collect_and_aggregate_all_metrics(
        start_time, end_time, workspace_id
    )


async def schedule_metrics_collection():
    """Scheduled task to collect metrics periodically"""
    while True:
        try:
            logger.info("Starting scheduled metrics collection")
            
            # Collect metrics for the last hour
            await run_metrics_collection(hours_back=1)
            
            # Wait for next collection (every hour)
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"Error in scheduled metrics collection: {e}")
            # Wait 5 minutes before retrying
            await asyncio.sleep(300)