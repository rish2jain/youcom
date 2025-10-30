"""
Benchmarking Integration Service for Advanced Intelligence Suite

This service integrates advanced benchmarking with existing performance monitoring,
connects benchmark alerts with the alert system, and wires benchmark metrics
with existing metrics collection.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.models.benchmarking import BenchmarkResult, BenchmarkComparison, MetricsSnapshot
from app.models.notification import NotificationRule, NotificationLog
from app.services.benchmark_calculator import benchmark_calculator, BenchmarkResult
from app.services.metrics_aggregator import metrics_aggregator, MetricDataPoint
from app.services.performance_monitor import (
    metrics_collector, performance_analyzer, real_time_monitor, PerformanceMetric
)
from app.realtime import emit_progress

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkAlert:
    """Benchmark-based alert."""
    metric_name: str
    entity_id: str
    entity_type: str
    alert_type: str  # performance_drop, benchmark_deviation, trend_anomaly
    severity: str    # low, medium, high, critical
    current_value: float
    benchmark_value: float
    percentile_rank: float
    deviation_percentage: float
    triggered_at: datetime
    recommendations: List[str]

@dataclass
class BenchmarkIntegrationMetrics:
    """Metrics for benchmarking integration."""
    benchmarks_calculated: int
    alerts_triggered: int
    performance_improvements_detected: int
    integration_health: str
    last_benchmark_update: datetime

class BenchmarkingIntegrationService:
    """Service for integrating benchmarking with performance monitoring."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Integration configuration
        self.auto_benchmarking_enabled = True
        self.benchmark_alert_thresholds = {
            "critical": 10.0,  # Bottom 10th percentile
            "high": 25.0,      # Bottom quartile
            "medium": 50.0,    # Below median
            "low": 75.0        # Below 75th percentile
        }
        self.deviation_alert_threshold = 20.0  # 20% deviation from benchmark
        
        # Performance tracking
        self.integration_metrics = {
            "benchmarks_calculated": 0,
            "alerts_triggered": 0,
            "performance_improvements_detected": 0,
            "last_benchmark_update": datetime.utcnow()
        }
    
    async def integrate_with_performance_monitor(self) -> Dict[str, Any]:
        """Integrate benchmarking with existing performance monitoring."""
        try:
            logger.info("🔗 Integrating benchmarking with performance monitoring")
            
            # Get current performance metrics from the monitor
            current_metrics = await self._collect_current_performance_metrics()
            
            # Convert to benchmark metrics and store
            benchmark_metrics = await self._convert_to_benchmark_metrics(current_metrics)
            
            if benchmark_metrics:
                await metrics_aggregator.store_metrics(benchmark_metrics)
                logger.info(f"Stored {len(benchmark_metrics)} benchmark metrics")
            
            # Calculate benchmarks for key performance metrics
            benchmark_results = await self._calculate_performance_benchmarks()
            
            # Check for benchmark alerts
            alerts = await self._check_benchmark_alerts(benchmark_results)
            
            # Update performance analyzer with benchmark insights
            await self._enhance_performance_analysis(benchmark_results)
            
            # Record integration metrics
            self.integration_metrics["benchmarks_calculated"] += len(benchmark_results)
            self.integration_metrics["alerts_triggered"] += len(alerts)
            self.integration_metrics["last_benchmark_update"] = datetime.utcnow()
            
            integration_status = {
                "status": "active",
                "benchmarks_calculated": len(benchmark_results),
                "alerts_triggered": len(alerts),
                "performance_metrics_integrated": len(current_metrics),
                "last_updated": datetime.utcnow().isoformat(),
                "key_insights": self._generate_integration_insights(benchmark_results),
                "recommendations": self._generate_integration_recommendations(benchmark_results, alerts)
            }
            
            logger.info("✅ Benchmarking integration completed successfully")
            return integration_status
            
        except Exception as e:
            logger.error(f"❌ Error integrating benchmarking with performance monitoring: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def _collect_current_performance_metrics(self) -> List[PerformanceMetric]:
        """Collect current performance metrics from the performance monitor."""
        try:
            current_metrics = []
            
            # Get metrics from the performance monitor's metrics collector
            metric_names = [
                "api_latency_news", "api_latency_search", "api_latency_chat", "api_latency_ari",
                "success_rate_news", "success_rate_search", "success_rate_chat", "success_rate_ari",
                "cache_hit_rate", "ml_f1_score"
            ]
            
            for metric_name in metric_names:
                try:
                    # Get recent metrics (last hour)
                    metrics = await metrics_collector.get_metrics(metric_name, 60)
                    current_metrics.extend(metrics)
                except Exception as e:
                    logger.warning(f"Failed to get metrics for {metric_name}: {e}")
            
            return current_metrics
            
        except Exception as e:
            logger.error(f"Error collecting current performance metrics: {e}")
            return []
    
    async def _convert_to_benchmark_metrics(
        self, 
        performance_metrics: List[PerformanceMetric]
    ) -> List[MetricDataPoint]:
        """Convert performance metrics to benchmark metric format."""
        try:
            benchmark_metrics = []
            
            for perf_metric in performance_metrics:
                # Determine category based on metric name
                if "api_latency" in perf_metric.name:
                    category = "performance"
                    unit = "milliseconds"
                elif "success_rate" in perf_metric.name:
                    category = "quality"
                    unit = "percentage"
                elif "cache_hit_rate" in perf_metric.name:
                    category = "efficiency"
                    unit = "percentage"
                elif "ml_" in perf_metric.name:
                    category = "ml_performance"
                    unit = "score"
                else:
                    category = "general"
                    unit = "value"
                
                benchmark_metric = MetricDataPoint(
                    metric_name=perf_metric.name,
                    value=perf_metric.value,
                    timestamp=perf_metric.timestamp,
                    source_system="cia",
                    category=category,
                    unit=unit,
                    metadata=perf_metric.metadata
                )
                
                benchmark_metrics.append(benchmark_metric)
            
            return benchmark_metrics
            
        except Exception as e:
            logger.error(f"Error converting to benchmark metrics: {e}")
            return []
    
    async def _calculate_performance_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """Calculate benchmarks for key performance metrics."""
        try:
            benchmark_results = {}
            
            # Define key metrics to benchmark
            key_metrics = [
                "api_latency_news", "api_latency_search", "api_latency_chat", "api_latency_ari",
                "success_rate_news", "success_rate_search", "success_rate_chat", "success_rate_ari",
                "cache_hit_rate", "ml_f1_score"
            ]
            
            # Calculate benchmarks for the last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            for metric_name in key_metrics:
                try:
                    # Use system-wide benchmarking (no specific entity)
                    result = await benchmark_calculator.calculate_entity_benchmark(
                        entity_id="system",
                        entity_type="system",
                        metric_name=metric_name,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    benchmark_results[metric_name] = result
                    
                except Exception as e:
                    logger.warning(f"Failed to calculate benchmark for {metric_name}: {e}")
            
            return benchmark_results
            
        except Exception as e:
            logger.error(f"Error calculating performance benchmarks: {e}")
            return {}
    
    async def _check_benchmark_alerts(
        self, 
        benchmark_results: Dict[str, BenchmarkResult]
    ) -> List[BenchmarkAlert]:
        """Check for benchmark-based alerts."""
        try:
            alerts = []
            
            for metric_name, result in benchmark_results.items():
                # Check percentile rank against thresholds
                alert_severity = None
                
                if result.percentile_rank <= self.benchmark_alert_thresholds["critical"]:
                    alert_severity = "critical"
                elif result.percentile_rank <= self.benchmark_alert_thresholds["high"]:
                    alert_severity = "high"
                elif result.percentile_rank <= self.benchmark_alert_thresholds["medium"]:
                    alert_severity = "medium"
                elif result.percentile_rank <= self.benchmark_alert_thresholds["low"]:
                    alert_severity = "low"
                
                # Check deviation from benchmark
                if result.benchmark_value > 0:
                    deviation_percentage = abs(
                        (result.entity_value - result.benchmark_value) / result.benchmark_value * 100
                    )
                    
                    if (deviation_percentage >= self.deviation_alert_threshold and 
                        result.entity_value < result.benchmark_value):
                        
                        if not alert_severity or alert_severity == "low":
                            alert_severity = "medium"
                
                # Create alert if needed
                if alert_severity:
                    alert = BenchmarkAlert(
                        metric_name=metric_name,
                        entity_id=result.entity_id,
                        entity_type=result.entity_type,
                        alert_type="benchmark_deviation",
                        severity=alert_severity,
                        current_value=result.entity_value,
                        benchmark_value=result.benchmark_value,
                        percentile_rank=result.percentile_rank,
                        deviation_percentage=deviation_percentage if 'deviation_percentage' in locals() else 0.0,
                        triggered_at=datetime.utcnow(),
                        recommendations=result.improvement_recommendations
                    )
                    
                    alerts.append(alert)
                    
                    # Emit real-time alert
                    await self._emit_benchmark_alert(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking benchmark alerts: {e}")
            return []
    
    async def _emit_benchmark_alert(self, alert: BenchmarkAlert) -> None:
        """Emit real-time benchmark alert."""
        try:
            await emit_progress(
                "benchmark_alert",
                {
                    "metric_name": alert.metric_name,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "current_value": alert.current_value,
                    "benchmark_value": alert.benchmark_value,
                    "percentile_rank": alert.percentile_rank,
                    "deviation_percentage": alert.deviation_percentage,
                    "recommendations": alert.recommendations[:3]  # Limit for real-time
                }
            )
            
            # Record alert metric
            await metrics_collector.record_metric(
                f"benchmark_alert_{alert.severity}",
                1.0,
                {
                    "metric_name": alert.metric_name,
                    "percentile_rank": alert.percentile_rank,
                    "deviation": alert.deviation_percentage
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to emit benchmark alert: {e}")
    
    async def _enhance_performance_analysis(
        self, 
        benchmark_results: Dict[str, BenchmarkResult]
    ) -> None:
        """Enhance performance analysis with benchmark insights."""
        try:
            # Add benchmark insights to performance analyzer thresholds
            for metric_name, result in benchmark_results.items():
                # Update thresholds based on benchmark data
                if hasattr(performance_analyzer, 'thresholds'):
                    if metric_name in performance_analyzer.thresholds:
                        # Adjust thresholds based on benchmark percentiles
                        if result.percentile_rank < 25:
                            # Performance is poor, tighten thresholds
                            current_threshold = performance_analyzer.thresholds[metric_name]
                            if "warning" in current_threshold:
                                current_threshold["warning"] *= 0.8  # 20% stricter
                            if "critical" in current_threshold:
                                current_threshold["critical"] *= 0.9  # 10% stricter
                        elif result.percentile_rank > 75:
                            # Performance is good, relax thresholds slightly
                            current_threshold = performance_analyzer.thresholds[metric_name]
                            if "warning" in current_threshold:
                                current_threshold["warning"] *= 1.1  # 10% more lenient
                            if "critical" in current_threshold:
                                current_threshold["critical"] *= 1.05  # 5% more lenient
            
            logger.info("Enhanced performance analysis with benchmark insights")
            
        except Exception as e:
            logger.warning(f"Failed to enhance performance analysis: {e}")
    
    def _generate_integration_insights(
        self, 
        benchmark_results: Dict[str, BenchmarkResult]
    ) -> List[str]:
        """Generate insights from benchmark integration."""
        insights = []
        
        try:
            if not benchmark_results:
                insights.append("No benchmark data available for analysis")
                return insights
            
            # Overall performance assessment
            percentile_ranks = [result.percentile_rank for result in benchmark_results.values()]
            avg_percentile = sum(percentile_ranks) / len(percentile_ranks)
            
            if avg_percentile >= 75:
                insights.append(f"System performance is above average (top {100-avg_percentile:.0f}%)")
            elif avg_percentile >= 50:
                insights.append(f"System performance is average ({avg_percentile:.0f}th percentile)")
            else:
                insights.append(f"System performance needs improvement ({avg_percentile:.0f}th percentile)")
            
            # Identify best and worst performing metrics
            best_metric = max(benchmark_results.items(), key=lambda x: x[1].percentile_rank)
            worst_metric = min(benchmark_results.items(), key=lambda x: x[1].percentile_rank)
            
            insights.append(f"Best performing metric: {best_metric[0]} ({best_metric[1].percentile_rank:.0f}th percentile)")
            insights.append(f"Needs attention: {worst_metric[0]} ({worst_metric[1].percentile_rank:.0f}th percentile)")
            
            # Performance trends
            improving_metrics = [
                name for name, result in benchmark_results.items()
                if result.percentile_rank >= 75
            ]
            
            if improving_metrics:
                insights.append(f"Strong performance in: {', '.join(improving_metrics[:3])}")
            
            return insights
            
        except Exception as e:
            logger.warning(f"Error generating integration insights: {e}")
            return ["Error generating insights"]
    
    def _generate_integration_recommendations(
        self, 
        benchmark_results: Dict[str, BenchmarkResult],
        alerts: List[BenchmarkAlert]
    ) -> List[str]:
        """Generate recommendations from benchmark integration."""
        recommendations = []
        
        try:
            # Priority recommendations based on alerts
            critical_alerts = [a for a in alerts if a.severity == "critical"]
            if critical_alerts:
                recommendations.append(f"Urgent: Address {len(critical_alerts)} critical performance issues")
            
            high_alerts = [a for a in alerts if a.severity == "high"]
            if high_alerts:
                recommendations.append(f"High priority: Improve {len(high_alerts)} underperforming metrics")
            
            # General recommendations based on benchmark results
            poor_performers = [
                name for name, result in benchmark_results.items()
                if result.percentile_rank < 25
            ]
            
            if poor_performers:
                recommendations.append(f"Focus improvement efforts on: {', '.join(poor_performers[:3])}")
            
            # Specific metric recommendations
            for name, result in benchmark_results.items():
                if result.percentile_rank < 50 and result.improvement_recommendations:
                    recommendations.extend(result.improvement_recommendations[:1])  # Take top recommendation
            
            # Limit recommendations
            return recommendations[:5]
            
        except Exception as e:
            logger.warning(f"Error generating integration recommendations: {e}")
            return ["Review system performance and optimize key metrics"]
    
    async def connect_with_alert_system(self) -> Dict[str, Any]:
        """Connect benchmark alerts with existing alert system."""
        try:
            # Get recent benchmark alerts
            recent_alerts = await self._get_recent_benchmark_alerts()
            
            # Check notification rules for benchmark alerts
            notifications_sent = 0
            
            for alert in recent_alerts:
                # Check if there are notification rules for this type of alert
                result = await self.db.execute(
                    select(NotificationRule)
                    .where(
                        and_(
                            NotificationRule.active == True,
                            NotificationRule.condition_type == "performance_threshold"
                        )
                    )
                )
                
                rules = result.scalars().all()
                
                for rule in rules:
                    # Check if alert meets rule criteria
                    if self._alert_matches_rule(alert, rule):
                        # Create notification log
                        notification_log = NotificationLog(
                            rule_id=rule.id,
                            competitor_name=f"System-{alert.metric_name}",
                            channel=rule.channel,
                            target=rule.target,
                            message=f"Benchmark alert: {alert.metric_name} performance is {alert.severity} ({alert.percentile_rank:.0f}th percentile)",
                            notification_metadata={
                                "alert_type": alert.alert_type,
                                "severity": alert.severity,
                                "metric_name": alert.metric_name,
                                "current_value": alert.current_value,
                                "benchmark_value": alert.benchmark_value,
                                "percentile_rank": alert.percentile_rank
                            }
                        )
                        
                        self.db.add(notification_log)
                        rule.last_triggered_at = datetime.utcnow()
                        notifications_sent += 1
            
            await self.db.commit()
            
            return {
                "status": "connected",
                "recent_alerts": len(recent_alerts),
                "notifications_sent": notifications_sent,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error connecting with alert system: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def _get_recent_benchmark_alerts(self, hours: int = 24) -> List[BenchmarkAlert]:
        """Get recent benchmark alerts (simulated from stored comparisons)."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get recent benchmark comparisons that indicate poor performance
            result = await self.db.execute(
                select(BenchmarkComparison)
                .where(
                    and_(
                        BenchmarkComparison.created_at >= cutoff_time,
                        BenchmarkComparison.percentile_rank <= 25  # Bottom quartile
                    )
                )
                .order_by(desc(BenchmarkComparison.created_at))
            )
            
            comparisons = result.scalars().all()
            
            # Convert to benchmark alerts
            alerts = []
            for comp in comparisons:
                severity = "critical" if comp.percentile_rank <= 10 else "high"
                
                alert = BenchmarkAlert(
                    metric_name=comp.metric_name,
                    entity_id=comp.entity_id,
                    entity_type=comp.entity_type,
                    alert_type="benchmark_deviation",
                    severity=severity,
                    current_value=comp.entity_value,
                    benchmark_value=comp.benchmark_value,
                    percentile_rank=comp.percentile_rank,
                    deviation_percentage=abs((comp.entity_value - comp.benchmark_value) / comp.benchmark_value * 100) if comp.benchmark_value > 0 else 0,
                    triggered_at=comp.created_at,
                    recommendations=comp.improvement_recommendations or []
                )
                
                alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting recent benchmark alerts: {e}")
            return []
    
    def _alert_matches_rule(self, alert: BenchmarkAlert, rule: NotificationRule) -> bool:
        """Check if a benchmark alert matches a notification rule."""
        try:
            # Check threshold value
            if rule.threshold_value:
                if alert.percentile_rank > rule.threshold_value:
                    return False
            
            # Check competitor name (for system alerts, use metric name)
            if rule.competitor_name and rule.competitor_name not in alert.metric_name:
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error matching alert to rule: {e}")
            return False
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status."""
        try:
            # Get recent benchmark metrics count
            recent_metrics = await self.db.execute(
                select(func.count(BenchmarkResult.id))
                .where(BenchmarkResult.measurement_timestamp >= datetime.utcnow() - timedelta(hours=24))
            )
            
            metrics_24h = recent_metrics.scalar() or 0
            
            # Get recent benchmark comparisons
            recent_comparisons = await self.db.execute(
                select(func.count(BenchmarkComparison.id))
                .where(BenchmarkComparison.created_at >= datetime.utcnow() - timedelta(hours=24))
            )
            
            comparisons_24h = recent_comparisons.scalar() or 0
            
            # Determine integration health
            if metrics_24h > 50 and comparisons_24h > 0:
                health = "excellent"
            elif metrics_24h > 20 and comparisons_24h > 0:
                health = "good"
            elif metrics_24h > 0:
                health = "fair"
            else:
                health = "poor"
            
            return {
                "integration_health": health,
                "metrics": {
                    "benchmark_metrics_24h": metrics_24h,
                    "benchmark_comparisons_24h": comparisons_24h,
                    "benchmarks_calculated": self.integration_metrics["benchmarks_calculated"],
                    "alerts_triggered": self.integration_metrics["alerts_triggered"],
                    "performance_improvements_detected": self.integration_metrics["performance_improvements_detected"]
                },
                "configuration": {
                    "auto_benchmarking_enabled": self.auto_benchmarking_enabled,
                    "deviation_alert_threshold": self.deviation_alert_threshold,
                    "benchmark_alert_thresholds": self.benchmark_alert_thresholds
                },
                "last_benchmark_update": self.integration_metrics["last_benchmark_update"].isoformat(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting integration status: {e}")
            return {
                "integration_health": "error",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def get_integration_metrics(self) -> BenchmarkIntegrationMetrics:
        """Get comprehensive integration metrics."""
        try:
            return BenchmarkIntegrationMetrics(
                benchmarks_calculated=self.integration_metrics["benchmarks_calculated"],
                alerts_triggered=self.integration_metrics["alerts_triggered"],
                performance_improvements_detected=self.integration_metrics["performance_improvements_detected"],
                integration_health="good" if self.integration_metrics["benchmarks_calculated"] > 0 else "poor",
                last_benchmark_update=self.integration_metrics["last_benchmark_update"]
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting integration metrics: {e}")
            return BenchmarkIntegrationMetrics(
                benchmarks_calculated=0,
                alerts_triggered=0,
                performance_improvements_detected=0,
                integration_health="error",
                last_benchmark_update=datetime.utcnow()
            )