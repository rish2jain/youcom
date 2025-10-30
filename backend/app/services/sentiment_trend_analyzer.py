"""Sentiment trend detection and alerting system."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.sentiment_analysis import (
    SentimentAnalysis, SentimentTrend, SentimentAlert
)
from app.models.notification import NotificationRule, NotificationLog
from app.realtime import emit_progress

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend direction enumeration."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TrendAnalysisResult:
    """Result of trend analysis."""
    entity_name: str
    entity_type: str
    timeframe: str
    current_sentiment: float
    previous_sentiment: float
    sentiment_change: float
    trend_direction: TrendDirection
    trend_strength: float
    volatility: float
    total_mentions: int
    confidence: float


@dataclass
class AlertTrigger:
    """Alert trigger configuration."""
    entity_name: str
    entity_type: str
    alert_type: str
    threshold_value: float
    severity: AlertSeverity
    current_value: float
    previous_value: Optional[float]
    change_percentage: float


class SentimentTrendAnalyzer:
    """Analyzes sentiment trends and generates alerts."""
    
    def __init__(self):
        self.trend_thresholds = {
            "shift_threshold": 0.20,  # 20% change triggers alert
            "volatility_threshold": 0.15,  # High volatility threshold
            "minimum_mentions": 3,  # Minimum mentions for reliable trend
            "confidence_threshold": 0.7  # Minimum confidence for alerts
        }
        
    async def analyze_trends(self, timeframe: str = "daily", 
                           entity_filter: Optional[str] = None) -> List[TrendAnalysisResult]:
        """Analyze sentiment trends for entities."""
        try:
            async with AsyncSessionLocal() as db:
                # Get time range for analysis
                end_time = datetime.now(timezone.utc)
                if timeframe == "daily":
                    start_time = end_time - timedelta(days=1)
                    previous_start = start_time - timedelta(days=1)
                elif timeframe == "weekly":
                    start_time = end_time - timedelta(days=7)
                    previous_start = start_time - timedelta(days=7)
                elif timeframe == "monthly":
                    start_time = end_time - timedelta(days=30)
                    previous_start = start_time - timedelta(days=30)
                else:
                    raise ValueError(f"Invalid timeframe: {timeframe}")
                
                # Build query for current period
                query = select(
                    SentimentAnalysis.entity_name,
                    SentimentAnalysis.entity_type,
                    func.avg(SentimentAnalysis.sentiment_score).label('avg_sentiment'),
                    func.stddev(SentimentAnalysis.sentiment_score).label('volatility'),
                    func.count(SentimentAnalysis.id).label('mention_count'),
                    func.avg(SentimentAnalysis.confidence).label('avg_confidence')
                ).where(
                    and_(
                        SentimentAnalysis.processing_timestamp >= start_time,
                        SentimentAnalysis.processing_timestamp <= end_time
                    )
                ).group_by(
                    SentimentAnalysis.entity_name,
                    SentimentAnalysis.entity_type
                )
                
                if entity_filter:
                    query = query.where(SentimentAnalysis.entity_name.ilike(f"%{entity_filter}%"))
                
                current_results = await db.execute(query)
                current_data = current_results.all()
                
                # Build query for previous period
                prev_query = select(
                    SentimentAnalysis.entity_name,
                    SentimentAnalysis.entity_type,
                    func.avg(SentimentAnalysis.sentiment_score).label('avg_sentiment'),
                    func.count(SentimentAnalysis.id).label('mention_count')
                ).where(
                    and_(
                        SentimentAnalysis.processing_timestamp >= previous_start,
                        SentimentAnalysis.processing_timestamp < start_time
                    )
                ).group_by(
                    SentimentAnalysis.entity_name,
                    SentimentAnalysis.entity_type
                )
                
                if entity_filter:
                    prev_query = prev_query.where(SentimentAnalysis.entity_name.ilike(f"%{entity_filter}%"))
                
                previous_results = await db.execute(prev_query)
                previous_data = {(row.entity_name, row.entity_type): row for row in previous_results.all()}
                
                # Analyze trends
                trend_results = []
                for row in current_data:
                    if row.mention_count < self.trend_thresholds["minimum_mentions"]:
                        continue
                    
                    entity_key = (row.entity_name, row.entity_type)
                    previous_row = previous_data.get(entity_key)
                    
                    if previous_row:
                        sentiment_change = row.avg_sentiment - previous_row.avg_sentiment
                        change_percentage = abs(sentiment_change / max(abs(previous_row.avg_sentiment), 0.1))
                    else:
                        sentiment_change = 0.0
                        change_percentage = 0.0
                        previous_row = type('obj', (object,), {'avg_sentiment': 0.0})()
                    
                    # Determine trend direction and strength
                    trend_direction, trend_strength = self._calculate_trend_direction(
                        sentiment_change, change_percentage, row.volatility or 0.0
                    )
                    
                    trend_result = TrendAnalysisResult(
                        entity_name=row.entity_name,
                        entity_type=row.entity_type,
                        timeframe=timeframe,
                        current_sentiment=float(row.avg_sentiment),
                        previous_sentiment=float(previous_row.avg_sentiment),
                        sentiment_change=float(sentiment_change),
                        trend_direction=trend_direction,
                        trend_strength=trend_strength,
                        volatility=float(row.volatility or 0.0),
                        total_mentions=row.mention_count,
                        confidence=float(row.avg_confidence or 0.0)
                    )
                    
                    trend_results.append(trend_result)
                
                # Store trend analysis results
                await self._store_trend_results(db, trend_results, start_time, end_time)
                
                return trend_results
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment trends: {str(e)}")
            return []

    def _calculate_trend_direction(self, sentiment_change: float, 
                                 change_percentage: float, volatility: float) -> Tuple[TrendDirection, float]:
        """Calculate trend direction and strength."""
        
        # High volatility indicates unstable trend
        if volatility > self.trend_thresholds["volatility_threshold"]:
            return TrendDirection.VOLATILE, volatility
        
        # Significant positive change
        if sentiment_change > 0 and change_percentage > self.trend_thresholds["shift_threshold"]:
            return TrendDirection.IMPROVING, change_percentage
        
        # Significant negative change
        if sentiment_change < 0 and change_percentage > self.trend_thresholds["shift_threshold"]:
            return TrendDirection.DECLINING, change_percentage
        
        # Stable trend
        return TrendDirection.STABLE, change_percentage

    async def _store_trend_results(self, db: AsyncSession, trend_results: List[TrendAnalysisResult],
                                 start_time: datetime, end_time: datetime):
        """Store trend analysis results in database."""
        try:
            for result in trend_results:
                trend_record = SentimentTrend(
                    entity_name=result.entity_name,
                    entity_type=result.entity_type,
                    timeframe=result.timeframe,
                    period_start=start_time,
                    period_end=end_time,
                    average_sentiment=result.current_sentiment,
                    sentiment_volatility=result.volatility,
                    total_mentions=result.total_mentions,
                    positive_mentions=0,  # Will be calculated separately if needed
                    negative_mentions=0,  # Will be calculated separately if needed
                    neutral_mentions=0,   # Will be calculated separately if needed
                    trend_direction=result.trend_direction.value,
                    trend_strength=result.trend_strength,
                    created_at=datetime.now(timezone.utc)
                )
                
                db.add(trend_record)
            
            await db.commit()
            logger.info(f"Stored {len(trend_results)} trend analysis results")
            
        except Exception as e:
            logger.error(f"Error storing trend results: {str(e)}")
            await db.rollback()

    async def detect_sentiment_shifts(self, minimum_change: float = 0.20) -> List[AlertTrigger]:
        """Detect significant sentiment shifts that warrant alerts."""
        try:
            trend_results = await self.analyze_trends("daily")
            alert_triggers = []
            
            for result in trend_results:
                # Skip if confidence is too low
                if result.confidence < self.trend_thresholds["confidence_threshold"]:
                    continue
                
                change_percentage = abs(result.sentiment_change / max(abs(result.previous_sentiment), 0.1))
                
                # Check for significant sentiment shift
                if change_percentage >= minimum_change:
                    severity = self._calculate_alert_severity(change_percentage, result.volatility)
                    
                    alert_trigger = AlertTrigger(
                        entity_name=result.entity_name,
                        entity_type=result.entity_type,
                        alert_type="shift",
                        threshold_value=minimum_change,
                        severity=severity,
                        current_value=result.current_sentiment,
                        previous_value=result.previous_sentiment,
                        change_percentage=change_percentage
                    )
                    
                    alert_triggers.append(alert_trigger)
            
            return alert_triggers
            
        except Exception as e:
            logger.error(f"Error detecting sentiment shifts: {str(e)}")
            return []

    def _calculate_alert_severity(self, change_percentage: float, volatility: float) -> AlertSeverity:
        """Calculate alert severity based on change magnitude and volatility."""
        
        # Critical: Very large changes (>50%) or high volatility with significant change
        if change_percentage > 0.5 or (volatility > 0.3 and change_percentage > 0.3):
            return AlertSeverity.CRITICAL
        
        # High: Large changes (>35%) or moderate volatility with significant change
        if change_percentage > 0.35 or (volatility > 0.2 and change_percentage > 0.25):
            return AlertSeverity.HIGH
        
        # Medium: Moderate changes (>25%)
        if change_percentage > 0.25:
            return AlertSeverity.MEDIUM
        
        # Low: Smaller but notable changes
        return AlertSeverity.LOW

    async def create_sentiment_alerts(self, alert_triggers: List[AlertTrigger]) -> List[int]:
        """Create sentiment alerts in the database."""
        alert_ids = []
        
        try:
            async with AsyncSessionLocal() as db:
                for trigger in alert_triggers:
                    # Check if similar alert already exists and is unresolved
                    existing_alert = await db.execute(
                        select(SentimentAlert).where(
                            and_(
                                SentimentAlert.entity_name == trigger.entity_name,
                                SentimentAlert.entity_type == trigger.entity_type,
                                SentimentAlert.alert_type == trigger.alert_type,
                                SentimentAlert.is_resolved == False,
                                SentimentAlert.triggered_at > datetime.now(timezone.utc) - timedelta(hours=24)
                            )
                        )
                    )
                    
                    if existing_alert.scalar_one_or_none():
                        logger.info(f"Similar alert already exists for {trigger.entity_name}")
                        continue
                    
                    # Create new alert
                    alert = SentimentAlert(
                        entity_name=trigger.entity_name,
                        entity_type=trigger.entity_type,
                        alert_type=trigger.alert_type,
                        alert_severity=trigger.severity.value,
                        current_sentiment=trigger.current_value,
                        previous_sentiment=trigger.previous_value,
                        sentiment_change=trigger.change_percentage,
                        threshold_value=trigger.threshold_value,
                        confidence=0.8,  # Default confidence for trend-based alerts
                        triggered_at=datetime.now(timezone.utc),
                        is_resolved=False,
                        notification_sent=False,
                        alert_metadata={
                            "detection_method": "trend_analysis",
                            "timeframe": "daily",
                            "change_percentage": trigger.change_percentage
                        }
                    )
                    
                    db.add(alert)
                    await db.flush()  # Get the ID
                    alert_ids.append(alert.id)
                
                await db.commit()
                logger.info(f"Created {len(alert_ids)} sentiment alerts")
                
        except Exception as e:
            logger.error(f"Error creating sentiment alerts: {str(e)}")
        
        return alert_ids

    async def send_alert_notifications(self, alert_ids: List[int]):
        """Send notifications for sentiment alerts."""
        try:
            async with AsyncSessionLocal() as db:
                for alert_id in alert_ids:
                    alert = await db.get(SentimentAlert, alert_id)
                    if not alert or alert.notification_sent:
                        continue
                    
                    # Emit real-time notification
                    await emit_progress(
                        "sentiment_alert",
                        {
                            "alert_id": alert.id,
                            "entity_name": alert.entity_name,
                            "entity_type": alert.entity_type,
                            "severity": alert.alert_severity,
                            "current_sentiment": alert.current_sentiment,
                            "previous_sentiment": alert.previous_sentiment,
                            "change_percentage": alert.sentiment_change,
                            "message": self._generate_alert_message(alert)
                        }
                    )
                    
                    # Mark notification as sent
                    alert.notification_sent = True
                
                await db.commit()
                logger.info(f"Sent notifications for {len(alert_ids)} alerts")
                
        except Exception as e:
            logger.error(f"Error sending alert notifications: {str(e)}")

    def _generate_alert_message(self, alert: SentimentAlert) -> str:
        """Generate human-readable alert message."""
        change_direction = "improved" if alert.sentiment_change > 0 else "declined"
        change_magnitude = "significantly" if abs(alert.sentiment_change) > 0.3 else "moderately"
        
        return (f"Sentiment for {alert.entity_name} has {change_magnitude} {change_direction} "
                f"from {alert.previous_sentiment:.2f} to {alert.current_sentiment:.2f} "
                f"({alert.sentiment_change:.1%} change)")

    async def get_sentiment_visualization_data(self, entity_name: str, 
                                             days: int = 30) -> Dict[str, Any]:
        """Get sentiment data for visualization (7-day, 30-day, 90-day views)."""
        try:
            async with AsyncSessionLocal() as db:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(days=days)
                
                # Get daily sentiment data
                query = select(
                    func.date(SentimentAnalysis.processing_timestamp).label('date'),
                    func.avg(SentimentAnalysis.sentiment_score).label('avg_sentiment'),
                    func.count(SentimentAnalysis.id).label('mention_count'),
                    func.stddev(SentimentAnalysis.sentiment_score).label('volatility')
                ).where(
                    and_(
                        SentimentAnalysis.entity_name == entity_name,
                        SentimentAnalysis.processing_timestamp >= start_time,
                        SentimentAnalysis.processing_timestamp <= end_time
                    )
                ).group_by(
                    func.date(SentimentAnalysis.processing_timestamp)
                ).order_by(
                    func.date(SentimentAnalysis.processing_timestamp)
                )
                
                result = await db.execute(query)
                daily_data = result.all()
                
                # Format data for visualization
                visualization_data = {
                    "entity_name": entity_name,
                    "timeframe": f"{days}_days",
                    "data_points": [
                        {
                            "date": row.date.isoformat(),
                            "sentiment": float(row.avg_sentiment),
                            "mentions": row.mention_count,
                            "volatility": float(row.volatility or 0.0)
                        }
                        for row in daily_data
                    ],
                    "summary": {
                        "total_mentions": sum(row.mention_count for row in daily_data),
                        "avg_sentiment": sum(row.avg_sentiment for row in daily_data) / len(daily_data) if daily_data else 0.0,
                        "trend": self._calculate_overall_trend(daily_data)
                    }
                }
                
                return visualization_data
                
        except Exception as e:
            logger.error(f"Error getting visualization data: {str(e)}")
            return {"error": str(e)}

    def _calculate_overall_trend(self, daily_data: List) -> str:
        """Calculate overall trend from daily data."""
        if len(daily_data) < 2:
            return "insufficient_data"
        
        first_half = daily_data[:len(daily_data)//2]
        second_half = daily_data[len(daily_data)//2:]
        
        first_avg = sum(row.avg_sentiment for row in first_half) / len(first_half)
        second_avg = sum(row.avg_sentiment for row in second_half) / len(second_half)
        
        change = second_avg - first_avg
        
        if abs(change) < 0.1:
            return "stable"
        elif change > 0:
            return "improving"
        else:
            return "declining"

    async def cleanup_old_alerts(self, retention_days: int = 30):
        """Clean up old resolved alerts."""
        try:
            async with AsyncSessionLocal() as db:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
                
                # Delete old resolved alerts
                result = await db.execute(
                    select(SentimentAlert).where(
                        and_(
                            SentimentAlert.is_resolved == True,
                            SentimentAlert.resolved_at < cutoff_date
                        )
                    )
                )
                
                old_alerts = result.scalars().all()
                
                if old_alerts:
                    for alert in old_alerts:
                        await db.delete(alert)
                    
                    await db.commit()
                    logger.info(f"Cleaned up {len(old_alerts)} old sentiment alerts")
                
        except Exception as e:
            logger.error(f"Error cleaning up old alerts: {str(e)}")


# Global trend analyzer instance
sentiment_trend_analyzer = SentimentTrendAnalyzer()