"""
Production Monitoring and Alerting Service

This service provides comprehensive health checks, performance metrics collection,
and alerting for all Advanced Intelligence Suite components.
"""

import asyncio
import logging
import time
import psutil
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
import redis.asyncio as redis

from app.models.ml_training import TrainingJob, ModelPerformanceMetric
from app.models.sentiment_analysis import SentimentAnalysis
from app.models.industry_template import IndustryTemplate
from app.models.benchmarking import BenchmarkResult, PerformanceAlert
from app.models.hubspot_integration import HubSpotIntegration
from app.models.obsidian_integration import ObsidianIntegration
from app.config import settings

logger = logging.getLogger(__name__)

class HealthStatus(str, Enum):
    """Health check status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"

class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ComponentType(str, Enum):
    """Types of components to monitor."""
    ML_TRAINING = "ml_training"
    ML_PREDICTION = "ml_prediction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    INDUSTRY_TEMPLATES = "industry_templates"
    BENCHMARKING = "benchmarking"
    HUBSPOT_INTEGRATION = "hubspot_integration"
    OBSIDIAN_INTEGRATION = "obsidian_integration"
    DATABASE = "database"
    REDIS = "redis"
    SYSTEM = "system"

@dataclass
class HealthCheck:
    """Health check result."""
    component: ComponentType
    status: HealthStatus
    message: str
    response_time_ms: float
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    component: ComponentType
    metric_name: str
    metric_value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]

@dataclass
class Alert:
    """Alert notification."""
    alert_id: str
    component: ComponentType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    resolved: bool
    metadata: Dict[str, Any]

class ProductionMonitor:
    """Production monitoring and alerting service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client: Optional[redis.Redis] = None
        
        # Monitoring configuration
        self.check_interval = 60  # seconds
        self.metric_retention_days = 30
        self.alert_cooldown_minutes = 15
        
        # Health check thresholds
        self.thresholds = {
            "response_time_ms": 5000,
            "error_rate_percent": 5.0,
            "cpu_usage_percent": 80.0,
            "memory_usage_percent": 85.0,
            "disk_usage_percent": 90.0,
            "ml_training_failure_rate": 10.0,
            "prediction_latency_ms": 1000,
            "sentiment_processing_delay_minutes": 10,
            "integration_sync_delay_minutes": 30
        }
        
        # Component health checks
        self.health_checks: Dict[ComponentType, Callable] = {
            ComponentType.ML_TRAINING: self._check_ml_training_health,
            ComponentType.ML_PREDICTION: self._check_ml_prediction_health,
            ComponentType.SENTIMENT_ANALYSIS: self._check_sentiment_analysis_health,
            ComponentType.INDUSTRY_TEMPLATES: self._check_templates_health,
            ComponentType.BENCHMARKING: self._check_benchmarking_health,
            ComponentType.HUBSPOT_INTEGRATION: self._check_hubspot_health,
            ComponentType.OBSIDIAN_INTEGRATION: self._check_obsidian_health,
            ComponentType.DATABASE: self._check_database_health,
            ComponentType.REDIS: self._check_redis_health,
            ComponentType.SYSTEM: self._check_system_health
        }
        
        # Active alerts
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.max_alert_history = 1000
        
        # Performance metrics storage
        self.metrics_buffer: List[PerformanceMetric] = []
        self.metrics_buffer_size = 1000
        
        # Monitoring state
        self.monitoring_active = False
        self.last_health_check = datetime.min.replace(tzinfo=timezone.utc)
        self.health_check_results: Dict[ComponentType, HealthCheck] = {}
        
        # Task tracking
        self._monitoring_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None
        
        # Notification settings
        self.email_enabled = getattr(settings, 'email_notifications_enabled', False)
        self.webhook_enabled = getattr(settings, 'webhook_notifications_enabled', False)
        self.webhook_url = getattr(settings, 'webhook_notification_url', None)
    
    async def initialize(self) -> None:
        """Initialize the production monitor."""
        try:
            # Connect to Redis for metrics storage
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            
            logger.info("Production monitor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize production monitor: {e}")
            raise
    
    async def start_monitoring(self) -> None:
        """Start the monitoring service."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start monitoring tasks (only if not already running)
        if self._monitoring_task is None or self._monitoring_task.done():
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        if self._metrics_task is None or self._metrics_task.done():
            self._metrics_task = asyncio.create_task(self._metrics_collection_loop())
        if self._alert_task is None or self._alert_task.done():
            self._alert_task = asyncio.create_task(self._alert_processing_loop())
        
        logger.info("Production monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop the monitoring service."""
        self.monitoring_active = False
        
        # Cancel and await all tasks
        tasks_to_cancel = []
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            tasks_to_cancel.append(self._monitoring_task)
        if self._metrics_task and not self._metrics_task.done():
            self._metrics_task.cancel()
            tasks_to_cancel.append(self._metrics_task)
        if self._alert_task and not self._alert_task.done():
            self._alert_task.cancel()
            tasks_to_cancel.append(self._alert_task)
        
        if tasks_to_cancel:
            try:
                await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
            except Exception as e:
                logger.warning(f"Error while cancelling monitoring tasks: {e}")
        
        # Clear task references
        self._monitoring_task = None
        self._metrics_task = None
        self._alert_task = None
        
        logger.info("Production monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Run health checks
                await self._run_health_checks()
                
                # Process alerts
                await self._process_health_alerts()
                
                # Sleep until next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(10)
    
    async def _run_health_checks(self) -> None:
        """Run all health checks."""
        check_tasks = []
        
        for component_type, check_func in self.health_checks.items():
            task = asyncio.create_task(self._run_single_health_check(component_type, check_func))
            check_tasks.append(task)
        
        # Wait for all checks to complete
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Store results
        for i, result in enumerate(results):
            component_type = list(self.health_checks.keys())[i]
            
            if isinstance(result, Exception):
                # Health check failed
                self.health_check_results[component_type] = HealthCheck(
                    component=component_type,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {result}",
                    response_time_ms=0.0,
                    timestamp=datetime.utcnow(),
                    metadata={"error": str(result)}
                )
            else:
                self.health_check_results[component_type] = result
        
        self.last_health_check = datetime.utcnow()
    
    async def _run_single_health_check(
        self, 
        component_type: ComponentType, 
        check_func: Callable
    ) -> HealthCheck:
        """Run a single health check with timing."""
        start_time = time.time()
        
        try:
            result = await check_func()
            response_time = (time.time() - start_time) * 1000
            
            if isinstance(result, HealthCheck):
                result.response_time_ms = response_time
                return result
            else:
                # Convert simple result to HealthCheck
                return HealthCheck(
                    component=component_type,
                    status=HealthStatus.HEALTHY,
                    message="OK",
                    response_time_ms=response_time,
                    timestamp=datetime.utcnow(),
                    metadata=result if isinstance(result, dict) else {}
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                component=component_type,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {e}",
                response_time_ms=response_time,
                timestamp=datetime.utcnow(),
                metadata={"error": str(e)}
            )
    
    async def _check_ml_training_health(self) -> HealthCheck:
        """Check ML training service health."""
        try:
            # Check recent training jobs
            result = await self.db.execute(
                select(TrainingJob)
                .where(TrainingJob.created_at >= datetime.utcnow() - timedelta(hours=24))
                .order_by(desc(TrainingJob.created_at))
                .limit(10)
            )
            
            recent_jobs = result.scalars().all()
            
            if not recent_jobs:
                return HealthCheck(
                    component=ComponentType.ML_TRAINING,
                    status=HealthStatus.WARNING,
                    message="No recent training jobs found",
                    response_time_ms=0.0,
                    timestamp=datetime.utcnow(),
                    metadata={"job_count": 0}
                )
            
            # Calculate failure rate
            failed_jobs = [job for job in recent_jobs if job.status == "failed"]
            failure_rate = (len(failed_jobs) / len(recent_jobs)) * 100
            
            status = HealthStatus.HEALTHY
            message = f"Training jobs: {len(recent_jobs)}, Failure rate: {failure_rate:.1f}%"
            
            if failure_rate > self.thresholds["ml_training_failure_rate"]:
                status = HealthStatus.CRITICAL
                message = f"High training failure rate: {failure_rate:.1f}%"
            elif failure_rate > 5.0:
                status = HealthStatus.WARNING
            
            return HealthCheck(
                component=ComponentType.ML_TRAINING,
                status=status,
                message=message,
                response_time_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={
                    "total_jobs": len(recent_jobs),
                    "failed_jobs": len(failed_jobs),
                    "failure_rate": failure_rate
                }
            )
            
        except Exception as e:
            raise Exception(f"ML training health check failed: {e}")
    
    async def _check_ml_prediction_health(self) -> HealthCheck:
        """Check ML prediction service health."""
        try:
            # Check recent model performance metrics
            result = await self.db.execute(
                select(ModelPerformanceMetric)
                .where(ModelPerformanceMetric.evaluation_timestamp >= datetime.utcnow() - timedelta(hours=24))
                .where(ModelPerformanceMetric.metric_name == "f1_score")
                .order_by(desc(ModelPerformanceMetric.evaluation_timestamp))
                .limit(5)
            )
            
            recent_metrics = result.scalars().all()
            
            if not recent_metrics:
                return HealthCheck(
                    component=ComponentType.ML_PREDICTION,
                    status=HealthStatus.WARNING,
                    message="No recent performance metrics found",
                    response_time_ms=0.0,
                    timestamp=datetime.utcnow(),
                    metadata={"metrics_count": 0}
                )
            
            # Check if any models are performing poorly
            poor_performance = [m for m in recent_metrics if m.metric_value < 0.7]
            avg_performance = sum(m.metric_value for m in recent_metrics) / len(recent_metrics)
            
            status = HealthStatus.HEALTHY
            message = f"Models: {len(recent_metrics)}, Avg F1: {avg_performance:.3f}"
            
            if poor_performance:
                status = HealthStatus.WARNING
                message = f"Models with poor performance: {len(poor_performance)}"
            
            if avg_performance < 0.6:
                status = HealthStatus.CRITICAL
                message = f"Critical: Average F1 score too low: {avg_performance:.3f}"
            
            return HealthCheck(
                component=ComponentType.ML_PREDICTION,
                status=status,
                message=message,
                response_time_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={
                    "model_count": len(recent_metrics),
                    "avg_f1_score": avg_performance,
                    "poor_performance_count": len(poor_performance)
                }
            )
            
        except Exception as e:
            raise Exception(f"ML prediction health check failed: {e}")
    
    async def _check_sentiment_analysis_health(self) -> HealthCheck:
        """Check sentiment analysis service health."""
        try:
            # Check recent sentiment analyses
            result = await self.db.execute(
                select(func.count(SentimentAnalysis.id))
                .where(SentimentAnalysis.processing_timestamp >= datetime.utcnow() - timedelta(hours=1))
            )
            
            recent_count = result.scalar() or 0
            
            # Check processing delay
            latest_result = await self.db.execute(
                select(SentimentAnalysis.processing_timestamp)
                .order_by(desc(SentimentAnalysis.processing_timestamp))
                .limit(1)
            )
            
            latest_timestamp = latest_result.scalar_one_or_none()
            
            status = HealthStatus.HEALTHY
            message = f"Recent analyses: {recent_count}"
            
            if latest_timestamp:
                delay_minutes = (datetime.utcnow() - latest_timestamp).total_seconds() / 60
                
                if delay_minutes > self.thresholds["sentiment_processing_delay_minutes"]:
                    status = HealthStatus.CRITICAL
                    message = f"Processing delayed by {delay_minutes:.1f} minutes"
                elif delay_minutes > 5:
                    status = HealthStatus.WARNING
                    message = f"Processing delay: {delay_minutes:.1f} minutes"
            
            return HealthCheck(
                component=ComponentType.SENTIMENT_ANALYSIS,
                status=status,
                message=message,
                response_time_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={
                    "recent_count": recent_count,
                    "last_processing": latest_timestamp.isoformat() if latest_timestamp else None
                }
            )
            
        except Exception as e:
            raise Exception(f"Sentiment analysis health check failed: {e}")
    
    async def _check_templates_health(self) -> HealthCheck:
        """Check industry templates service health."""
        try:
            # Check template count and recent usage
            template_count_result = await self.db.execute(
                select(func.count(IndustryTemplate.id))
            )
            template_count = template_count_result.scalar() or 0
            
            # Check for recent template applications
            recent_usage_result = await self.db.execute(
                select(func.count(IndustryTemplate.id))
                .where(IndustryTemplate.updated_at >= datetime.utcnow() - timedelta(days=7))
            )
            recent_usage = recent_usage_result.scalar() or 0
            
            status = HealthStatus.HEALTHY
            message = f"Templates: {template_count}, Recent usage: {recent_usage}"
            
            if template_count == 0:
                status = HealthStatus.CRITICAL
                message = "No templates available"
            elif template_count < 5:
                status = HealthStatus.WARNING
                message = f"Low template count: {template_count}"
            
            return HealthCheck(
                component=ComponentType.INDUSTRY_TEMPLATES,
                status=status,
                message=message,
                response_time_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={
                    "template_count": template_count,
                    "recent_usage": recent_usage
                }
            )
            
        except Exception as e:
            raise Exception(f"Templates health check failed: {e}")
    
    async def _check_benchmarking_health(self) -> HealthCheck:
        """Check benchmarking service health."""
        try:
            # Check recent benchmark calculations
            result = await self.db.execute(
                select(func.count(BenchmarkResult.id))
                .where(BenchmarkResult.calculated_at >= datetime.utcnow() - timedelta(hours=24))
            )
            
            recent_benchmarks = result.scalar() or 0
            
            status = HealthStatus.HEALTHY
            message = f"Recent benchmarks: {recent_benchmarks}"
            
            if recent_benchmarks == 0:
                status = HealthStatus.WARNING
                message = "No recent benchmark calculations"
            
            return HealthCheck(
                component=ComponentType.BENCHMARKING,
                status=status,
                message=message,
                response_time_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={"recent_benchmarks": recent_benchmarks}
            )
            
        except Exception as e:
            raise Exception(f"Benchmarking health check failed: {e}")
    
    async def _check_hubspot_health(self) -> HealthCheck:
        """Check HubSpot integration health."""
        try:
            # Check active integrations
            result = await self.db.execute(
                select(HubSpotIntegration)
                .where(HubSpotIntegration.sync_enabled == True)
            )
            
            active_integrations = result.scalars().all()
            
            if not active_integrations:
                return HealthCheck(
                    component=ComponentType.HUBSPOT_INTEGRATION,
                    status=HealthStatus.HEALTHY,
                    message="No active HubSpot integrations",
                    response_time_ms=0.0,
                    timestamp=datetime.utcnow(),
                    metadata={"active_count": 0}
                )
            
            # Check sync delays
            delayed_syncs = []
            for integration in active_integrations:
                if integration.last_sync:
                    delay_minutes = (datetime.utcnow() - integration.last_sync).total_seconds() / 60
                    if delay_minutes > self.thresholds["integration_sync_delay_minutes"]:
                        delayed_syncs.append(integration)
            
            status = HealthStatus.HEALTHY
            message = f"Active integrations: {len(active_integrations)}"
            
            if delayed_syncs:
                status = HealthStatus.WARNING
                message = f"Delayed syncs: {len(delayed_syncs)}/{len(active_integrations)}"
            
            return HealthCheck(
                component=ComponentType.HUBSPOT_INTEGRATION,
                status=status,
                message=message,
                response_time_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={
                    "active_count": len(active_integrations),
                    "delayed_count": len(delayed_syncs)
                }
            )
            
        except Exception as e:
            raise Exception(f"HubSpot health check failed: {e}")
    
    async def _check_obsidian_health(self) -> HealthCheck:
        """Check Obsidian integration health."""
        try:
            # Check active integrations
            result = await self.db.execute(
                select(ObsidianIntegration)
                .where(ObsidianIntegration.sync_enabled == True)
            )
            
            active_integrations = result.scalars().all()
            
            status = HealthStatus.HEALTHY
            message = f"Active integrations: {len(active_integrations)}"
            
            return HealthCheck(
                component=ComponentType.OBSIDIAN_INTEGRATION,
                status=status,
                message=message,
                response_time_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={"active_count": len(active_integrations)}
            )
            
        except Exception as e:
            raise Exception(f"Obsidian health check failed: {e}")
    
    async def _check_database_health(self) -> HealthCheck:
        """Check database health."""
        try:
            # Simple query to test database connectivity
            result = await self.db.execute(select(1))
            result.scalar()
            
            return HealthCheck(
                component=ComponentType.DATABASE,
                status=HealthStatus.HEALTHY,
                message="Database connection OK",
                response_time_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={}
            )
            
        except Exception as e:
            raise Exception(f"Database health check failed: {e}")
    
    async def _check_redis_health(self) -> HealthCheck:
        """Check Redis health."""
        try:
            if not self.redis_client:
                raise Exception("Redis client not initialized")
            
            # Test Redis connectivity
            await self.redis_client.ping()
            
            # Get Redis info
            info = await self.redis_client.info()
            memory_usage = info.get('used_memory_human', 'unknown')
            
            return HealthCheck(
                component=ComponentType.REDIS,
                status=HealthStatus.HEALTHY,
                message=f"Redis OK, Memory: {memory_usage}",
                response_time_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={"memory_usage": memory_usage}
            )
            
        except Exception as e:
            raise Exception(f"Redis health check failed: {e}")
    
    async def _check_system_health(self) -> HealthCheck:
        """Check system resource health."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            issues = []
            
            if cpu_percent > self.thresholds["cpu_usage_percent"]:
                status = HealthStatus.CRITICAL
                issues.append(f"High CPU: {cpu_percent:.1f}%")
            elif cpu_percent > 60:
                status = HealthStatus.WARNING
                issues.append(f"CPU: {cpu_percent:.1f}%")
            
            if memory.percent > self.thresholds["memory_usage_percent"]:
                status = HealthStatus.CRITICAL
                issues.append(f"High Memory: {memory.percent:.1f}%")
            elif memory.percent > 70:
                status = HealthStatus.WARNING
                issues.append(f"Memory: {memory.percent:.1f}%")
            
            if disk.percent > self.thresholds["disk_usage_percent"]:
                status = HealthStatus.CRITICAL
                issues.append(f"High Disk: {disk.percent:.1f}%")
            elif disk.percent > 80:
                status = HealthStatus.WARNING
                issues.append(f"Disk: {disk.percent:.1f}%")
            
            message = "System OK" if not issues else ", ".join(issues)
            
            return HealthCheck(
                component=ComponentType.SYSTEM,
                status=status,
                message=message,
                response_time_ms=0.0,
                timestamp=datetime.utcnow(),
                metadata={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                }
            )
            
        except Exception as e:
            raise Exception(f"System health check failed: {e}")
    
    async def _process_health_alerts(self) -> None:
        """Process health check results and generate alerts."""
        for component, health_check in self.health_check_results.items():
            alert_id = f"{component.value}_health"
            
            # Check if we should create an alert
            should_alert = (
                health_check.status in [HealthStatus.WARNING, HealthStatus.CRITICAL] and
                alert_id not in self.active_alerts
            )
            
            # Check if we should resolve an alert
            should_resolve = (
                health_check.status == HealthStatus.HEALTHY and
                alert_id in self.active_alerts
            )
            
            if should_alert:
                severity = AlertSeverity.WARNING if health_check.status == HealthStatus.WARNING else AlertSeverity.CRITICAL
                
                alert = Alert(
                    alert_id=alert_id,
                    component=component,
                    severity=severity,
                    title=f"{component.value.replace('_', ' ').title()} Health Issue",
                    message=health_check.message,
                    timestamp=datetime.utcnow(),
                    resolved=False,
                    metadata=health_check.metadata
                )
                
                await self._create_alert(alert)
            
            elif should_resolve:
                await self._resolve_alert(alert_id, "Health check returned to normal")
    
    async def _create_alert(self, alert: Alert) -> None:
        """Create and send a new alert."""
        try:
            # Store alert
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)
            
            # Trim history if needed
            if len(self.alert_history) > self.max_alert_history:
                self.alert_history = self.alert_history[-self.max_alert_history:]
            
            # Send notifications
            await self._send_alert_notifications(alert)
            
            logger.warning(f"Alert created: {alert.title} - {alert.message}")
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
    
    async def _resolve_alert(self, alert_id: str, resolution_message: str) -> None:
        """Resolve an active alert."""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.metadata["resolved_at"] = datetime.utcnow().isoformat()
                alert.metadata["resolution_message"] = resolution_message
                
                # Remove from active alerts
                del self.active_alerts[alert_id]
                
                logger.info(f"Alert resolved: {alert.title} - {resolution_message}")
                
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
    
    async def _send_alert_notifications(self, alert: Alert) -> None:
        """Send alert notifications via configured channels."""
        try:
            # Send email notification
            if self.email_enabled:
                await self._send_email_alert(alert)
            
            # Send webhook notification
            if self.webhook_enabled and self.webhook_url:
                await self._send_webhook_alert(alert)
                
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")
    
    async def _send_email_alert(self, alert: Alert) -> None:
        """Send email alert notification."""
        try:
            # This is a simplified implementation
            # In production, use proper email service configuration
            
            subject = f"[{alert.severity.upper()}] {alert.title}"
            body = f"""
Alert Details:
- Component: {alert.component.value}
- Severity: {alert.severity.value}
- Message: {alert.message}
- Timestamp: {alert.timestamp.isoformat()}

Metadata:
{json.dumps(alert.metadata, indent=2)}
"""
            
            # Would send email here using configured SMTP settings
            logger.info(f"Email alert would be sent: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, alert: Alert) -> None:
        """Send webhook alert notification."""
        try:
            payload = {
                "alert_id": alert.alert_id,
                "component": alert.component.value,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "metadata": alert.metadata
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent successfully: {alert.alert_id}")
                    else:
                        logger.warning(f"Webhook alert failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    async def _metrics_collection_loop(self) -> None:
        """Background loop for collecting performance metrics."""
        while self.monitoring_active:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Collect application metrics
                await self._collect_application_metrics()
                
                # Store metrics in Redis
                await self._store_metrics()
                
                # Sleep for metrics collection interval
                await asyncio.sleep(30)  # Collect metrics every 30 seconds
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)
    
    async def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            timestamp = datetime.utcnow()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_buffer.append(PerformanceMetric(
                component=ComponentType.SYSTEM,
                metric_name="cpu_usage_percent",
                metric_value=cpu_percent,
                unit="percent",
                timestamp=timestamp,
                tags={"type": "system"}
            ))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics_buffer.append(PerformanceMetric(
                component=ComponentType.SYSTEM,
                metric_name="memory_usage_percent",
                metric_value=memory.percent,
                unit="percent",
                timestamp=timestamp,
                tags={"type": "system"}
            ))
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.metrics_buffer.append(PerformanceMetric(
                component=ComponentType.SYSTEM,
                metric_name="disk_usage_percent",
                metric_value=disk.percent,
                unit="percent",
                timestamp=timestamp,
                tags={"type": "system"}
            ))
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    async def _collect_application_metrics(self) -> None:
        """Collect application-specific metrics."""
        try:
            timestamp = datetime.utcnow()
            
            # Database connection pool metrics (if available)
            # This would depend on your database connection pool implementation
            
            # Redis metrics
            if self.redis_client:
                try:
                    info = await self.redis_client.info()
                    connected_clients = info.get('connected_clients', 0)
                    
                    self.metrics_buffer.append(PerformanceMetric(
                        component=ComponentType.REDIS,
                        metric_name="connected_clients",
                        metric_value=float(connected_clients),
                        unit="count",
                        timestamp=timestamp,
                        tags={"type": "redis"}
                    ))
                except Exception as e:
                    logger.warning(f"Failed to collect Redis metrics: {e}")
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
    
    async def _store_metrics(self) -> None:
        """Store collected metrics in Redis."""
        if not self.redis_client or not self.metrics_buffer:
            return
        
        try:
            # Store metrics in Redis with TTL
            pipe = self.redis_client.pipeline()
            
            for metric in self.metrics_buffer:
                key = f"metrics:{metric.component.value}:{metric.metric_name}:{int(metric.timestamp.timestamp())}"
                value = json.dumps({
                    "value": metric.metric_value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat(),
                    "tags": metric.tags
                })
                
                # Store with TTL based on retention policy
                ttl_seconds = self.metric_retention_days * 24 * 3600
                pipe.setex(key, ttl_seconds, value)
            
            await pipe.execute()
            
            # Clear buffer
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    async def _alert_processing_loop(self) -> None:
        """Background loop for processing alerts."""
        while self.monitoring_active:
            try:
                # Check for alert cooldowns and cleanup
                await self._cleanup_resolved_alerts()
                
                # Sleep for alert processing interval
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_resolved_alerts(self) -> None:
        """Clean up old resolved alerts."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Remove old resolved alerts from history
            self.alert_history = [
                alert for alert in self.alert_history
                if not alert.resolved or alert.timestamp > cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Failed to cleanup resolved alerts: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of all components."""
        overall_status = HealthStatus.HEALTHY
        
        # Determine overall status
        for health_check in self.health_check_results.values():
            if health_check.status == HealthStatus.CRITICAL:
                overall_status = HealthStatus.CRITICAL
                break
            elif health_check.status == HealthStatus.WARNING and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.WARNING
        
        return {
            "overall_status": overall_status.value,
            "last_check": self.last_health_check.isoformat(),
            "components": {
                component.value: asdict(health_check)
                for component, health_check in self.health_check_results.items()
            },
            "active_alerts": len(self.active_alerts),
            "monitoring_active": self.monitoring_active
        }
    
    async def get_alerts(self, include_resolved: bool = False) -> List[Dict[str, Any]]:
        """Get current alerts."""
        alerts = list(self.active_alerts.values())
        
        if include_resolved:
            resolved_alerts = [alert for alert in self.alert_history if alert.resolved]
            alerts.extend(resolved_alerts[-50:])  # Last 50 resolved alerts
        
        return [asdict(alert) for alert in alerts]
    
    async def get_metrics(
        self, 
        component: Optional[ComponentType] = None,
        metric_name: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get performance metrics."""
        if not self.redis_client:
            return []
        
        try:
            # Build search pattern
            pattern_parts = ["metrics"]
            if component:
                pattern_parts.append(component.value)
            else:
                pattern_parts.append("*")
            
            if metric_name:
                pattern_parts.append(metric_name)
            else:
                pattern_parts.append("*")
            
            pattern_parts.append("*")
            pattern = ":".join(pattern_parts)
            
            # Find matching keys
            keys = []
            cursor = 0
            while True:
                cursor, batch_keys = await self.redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                keys.extend(batch_keys)
                if cursor == 0:
                    break
            
            # Filter by time range
            cutoff_timestamp = int((datetime.utcnow() - timedelta(hours=hours)).timestamp())
            filtered_keys = []
            
            for key in keys:
                try:
                    timestamp_str = key.split(":")[-1]
                    if int(timestamp_str) >= cutoff_timestamp:
                        filtered_keys.append(key)
                except (ValueError, IndexError):
                    continue
            
            # Get metric values
            metrics = []
            if filtered_keys:
                values = await self.redis_client.mget(filtered_keys)
                
                for key, value in zip(filtered_keys, values):
                    if value:
                        try:
                            metric_data = json.loads(value)
                            key_parts = key.split(":")
                            
                            metrics.append({
                                "component": key_parts[1],
                                "metric_name": key_parts[2],
                                "timestamp": metric_data["timestamp"],
                                "value": metric_data["value"],
                                "unit": metric_data["unit"],
                                "tags": metric_data["tags"]
                            })
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
            
            # Sort by timestamp
            metrics.sort(key=lambda x: x["timestamp"])
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return []
    
    async def shutdown(self) -> None:
        """Shutdown the production monitor."""
        try:
            await self.stop_monitoring()
            
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Production monitor shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during production monitor shutdown: {e}")