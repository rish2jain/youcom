"""
Sentiment-News Integration Service for Advanced Intelligence Suite

This service integrates sentiment analysis with the existing You.com News API ingestion,
connects sentiment alerts with the notification system, and wires sentiment trends
with the analytics dashboard.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.models.sentiment_analysis import SentimentAnalysis, SentimentTrend, SentimentAlert
from app.models.notification import NotificationRule, NotificationLog
from app.models.api_call_log import ApiCallLog
from app.services.sentiment_processor import sentiment_processor
from app.services.sentiment_trend_analyzer import sentiment_trend_analyzer
from app.services.sentiment_alert_worker import sentiment_alert_worker
from app.services.performance_monitor import metrics_collector
from app.realtime import emit_progress

logger = logging.getLogger(__name__)

@dataclass
class NewsWithSentiment:
    """News article enhanced with sentiment analysis."""
    article_id: str
    title: str
    content: str
    url: str
    published_at: datetime
    sentiment_score: float
    sentiment_label: str
    confidence: float
    entities: List[Dict[str, Any]]
    processing_time: float

@dataclass
class SentimentIntegrationMetrics:
    """Metrics for sentiment-news integration."""
    articles_processed: int
    sentiment_analyses_created: int
    alerts_triggered: int
    trends_detected: int
    average_processing_time: float
    integration_health: str

class SentimentNewsIntegrationService:
    """Service for integrating sentiment analysis with news processing."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Integration configuration
        self.auto_sentiment_analysis = True
        self.sentiment_threshold_alert = 0.3  # Trigger alerts for sentiment changes > 30%
        self.batch_processing_size = 20
        
        # Performance tracking
        self.integration_metrics = {
            "articles_processed": 0,
            "sentiment_analyses_created": 0,
            "alerts_triggered": 0,
            "trends_detected": 0,
            "processing_times": []
        }
    
    async def process_news_with_sentiment(
        self, 
        news_data: Dict[str, Any],
        competitor: str
    ) -> Dict[str, Any]:
        """Process news data and enhance with sentiment analysis."""
        try:
            logger.info(f"🔍 Processing news with sentiment analysis for {competitor}")
            
            articles = news_data.get("articles", [])
            if not articles:
                return news_data
            
            # Process articles in batches
            enhanced_articles = []
            batch_size = min(self.batch_processing_size, len(articles))
            
            for i in range(0, len(articles), batch_size):
                batch = articles[i:i + batch_size]
                batch_results = await self._process_article_batch(batch, competitor)
                enhanced_articles.extend(batch_results)
            
            # Update news data with sentiment information
            enhanced_news_data = news_data.copy()
            enhanced_news_data["articles"] = enhanced_articles
            enhanced_news_data["sentiment_summary"] = self._calculate_sentiment_summary(enhanced_articles)
            
            # Record integration metrics
            await self._record_integration_metrics("news_processing", len(enhanced_articles))
            
            logger.info(f"✅ Processed {len(enhanced_articles)} articles with sentiment for {competitor}")
            return enhanced_news_data
            
        except Exception as e:
            logger.error(f"❌ Error processing news with sentiment for {competitor}: {e}")
            # Return original data if sentiment processing fails
            return news_data
    
    async def _process_article_batch(
        self, 
        articles: List[Dict[str, Any]], 
        competitor: str
    ) -> List[Dict[str, Any]]:
        """Process a batch of articles with sentiment analysis."""
        enhanced_articles = []
        
        # Process articles concurrently
        tasks = []
        for article in articles:
            task = self._process_single_article(article, competitor)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to process article {i}: {result}")
                # Use original article if sentiment processing fails
                enhanced_articles.append(articles[i])
            else:
                enhanced_articles.append(result)
        
        return enhanced_articles
    
    async def _process_single_article(
        self, 
        article: Dict[str, Any], 
        competitor: str
    ) -> Dict[str, Any]:
        """Process a single article with sentiment analysis."""
        try:
            # Extract article content
            title = article.get("title", "")
            snippet = article.get("snippet", "")
            content = f"{title}. {snippet}".strip()
            
            if not content or len(content) < 10:
                return article
            
            # Generate unique content ID
            article_url = article.get("url", "")
            content_id = f"news_{hash(article_url)}_{int(datetime.utcnow().timestamp())}"
            
            # Process sentiment
            sentiment_result = await sentiment_processor.process_content(
                content_id=content_id,
                content_text=content,
                content_type="news",
                source_url=article_url
            )
            
            # Enhance article with sentiment data
            enhanced_article = article.copy()
            enhanced_article.update({
                "sentiment_score": sentiment_result.sentiment_score,
                "sentiment_label": sentiment_result.sentiment_label,
                "sentiment_confidence": sentiment_result.confidence,
                "sentiment_entities": sentiment_result.entities,
                "sentiment_processing_time": sentiment_result.processing_time,
                "content_id": content_id
            })
            
            # Check for sentiment alerts
            await self._check_sentiment_alerts(
                competitor, 
                sentiment_result.entities, 
                sentiment_result.sentiment_score,
                sentiment_result.confidence
            )
            
            self.integration_metrics["articles_processed"] += 1
            self.integration_metrics["sentiment_analyses_created"] += len(sentiment_result.entities)
            self.integration_metrics["processing_times"].append(sentiment_result.processing_time)
            
            return enhanced_article
            
        except Exception as e:
            logger.warning(f"Failed to process article sentiment: {e}")
            return article
    
    async def _check_sentiment_alerts(
        self, 
        competitor: str, 
        entities: List[Dict[str, Any]], 
        sentiment_score: float,
        confidence: float
    ) -> None:
        """Check if sentiment analysis should trigger alerts."""
        try:
            # Check for significant sentiment changes
            for entity in entities:
                entity_name = entity.get("name", "")
                entity_type = entity.get("type", "company")
                
                if not entity_name:
                    continue
                
                # Get recent sentiment history for this entity
                recent_sentiment = await self._get_recent_entity_sentiment(entity_name, entity_type)
                
                if recent_sentiment and confidence >= 0.7:
                    sentiment_change = abs(sentiment_score - recent_sentiment)
                    
                    if sentiment_change >= self.sentiment_threshold_alert:
                        await self._trigger_sentiment_alert(
                            entity_name,
                            entity_type,
                            sentiment_score,
                            recent_sentiment,
                            sentiment_change,
                            confidence
                        )
                        
                        self.integration_metrics["alerts_triggered"] += 1
                        
        except Exception as e:
            logger.warning(f"Error checking sentiment alerts: {e}")
    
    async def _get_recent_entity_sentiment(
        self, 
        entity_name: str, 
        entity_type: str,
        hours: int = 24
    ) -> Optional[float]:
        """Get recent average sentiment for an entity."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            result = await self.db.execute(
                select(func.avg(SentimentAnalysis.sentiment_score))
                .where(
                    and_(
                        SentimentAnalysis.entity_name == entity_name,
                        SentimentAnalysis.entity_type == entity_type,
                        SentimentAnalysis.processing_timestamp >= cutoff_time
                    )
                )
            )
            
            avg_sentiment = result.scalar()
            return float(avg_sentiment) if avg_sentiment is not None else None
            
        except Exception as e:
            logger.warning(f"Error getting recent entity sentiment: {e}")
            return None
    
    async def _trigger_sentiment_alert(
        self,
        entity_name: str,
        entity_type: str,
        current_sentiment: float,
        previous_sentiment: float,
        sentiment_change: float,
        confidence: float
    ) -> None:
        """Trigger a sentiment alert."""
        try:
            # Determine alert severity
            if sentiment_change >= 0.6:
                severity = "critical"
            elif sentiment_change >= 0.4:
                severity = "high"
            elif sentiment_change >= 0.3:
                severity = "medium"
            else:
                severity = "low"
            
            # Determine alert type
            alert_type = "sentiment_spike" if current_sentiment > previous_sentiment else "sentiment_drop"
            
            # Create sentiment alert
            sentiment_alert = SentimentAlert(
                entity_name=entity_name,
                entity_type=entity_type,
                alert_type=alert_type,
                alert_severity=severity,
                current_sentiment=current_sentiment,
                previous_sentiment=previous_sentiment,
                sentiment_change=sentiment_change,
                confidence=confidence,
                triggered_at=datetime.utcnow(),
                is_resolved=False,
                alert_metadata={
                    "integration_source": "news_processing",
                    "threshold": self.sentiment_threshold_alert,
                    "processing_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            self.db.add(sentiment_alert)
            await self.db.commit()
            
            # Emit real-time alert
            await emit_progress(
                "sentiment_alert",
                {
                    "entity_name": entity_name,
                    "entity_type": entity_type,
                    "alert_type": alert_type,
                    "severity": severity,
                    "current_sentiment": current_sentiment,
                    "sentiment_change": sentiment_change,
                    "confidence": confidence
                }
            )
            
            # Check for notification rules
            await self._check_notification_rules(sentiment_alert)
            
            logger.info(f"🚨 Sentiment alert triggered for {entity_name}: {alert_type} ({severity})")
            
        except Exception as e:
            logger.error(f"Error triggering sentiment alert: {e}")
    
    async def _check_notification_rules(self, sentiment_alert: SentimentAlert) -> None:
        """Check if sentiment alert should trigger notifications."""
        try:
            # Get notification rules for sentiment alerts
            result = await self.db.execute(
                select(NotificationRule)
                .where(
                    and_(
                        NotificationRule.active,
                        NotificationRule.condition_type == "sentiment_change",
                        NotificationRule.competitor_name == sentiment_alert.entity_name
                    )
                )
            )
            
            rules = result.scalars().all()
            
            for rule in rules:
                # Check if alert meets rule criteria
                if (rule.threshold_value is not None and 
                    sentiment_alert.sentiment_change is not None and
                    sentiment_alert.sentiment_change >= rule.threshold_value):
                    
                    # Create notification log
                    notification_log = NotificationLog(
                        rule_id=rule.id,
                        competitor_name=sentiment_alert.entity_name,
                        channel=rule.channel,
                        target=rule.target,
                        message=f"Sentiment alert: {sentiment_alert.entity_name} sentiment changed by {sentiment_alert.sentiment_change:.2f}",
                        notification_metadata={
                            "alert_id": sentiment_alert.id,
                            "alert_type": sentiment_alert.alert_type,
                            "severity": sentiment_alert.alert_severity,
                            "current_sentiment": sentiment_alert.current_sentiment
                        }
                    )
                    
                    self.db.add(notification_log)
                    rule.last_triggered_at = datetime.utcnow()
            
            await self.db.commit()
            
        except Exception as e:
            logger.warning(f"Error checking notification rules: {e}")
    
    def _calculate_sentiment_summary(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate sentiment summary for processed articles."""
        try:
            sentiment_scores = []
            sentiment_labels = {"positive": 0, "negative": 0, "neutral": 0}
            total_entities = 0
            
            for article in articles:
                if "sentiment_score" in article:
                    sentiment_scores.append(article["sentiment_score"])
                    
                    label = article.get("sentiment_label", "neutral")
                    if label in sentiment_labels:
                        sentiment_labels[label] += 1
                    
                    entities = article.get("sentiment_entities", [])
                    total_entities += len(entities)
            
            if not sentiment_scores:
                return {
                    "average_sentiment": 0.0,
                    "sentiment_distribution": sentiment_labels,
                    "total_entities": 0,
                    "articles_with_sentiment": 0
                }
            
            return {
                "average_sentiment": sum(sentiment_scores) / len(sentiment_scores),
                "sentiment_distribution": sentiment_labels,
                "total_entities": total_entities,
                "articles_with_sentiment": len(sentiment_scores),
                "sentiment_range": {
                    "min": min(sentiment_scores),
                    "max": max(sentiment_scores)
                }
            }
            
        except Exception as e:
            logger.warning(f"Error calculating sentiment summary: {e}")
            return {
                "average_sentiment": 0.0,
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                "total_entities": 0,
                "articles_with_sentiment": 0
            }
    
    async def connect_with_analytics_dashboard(self) -> Dict[str, Any]:
        """Connect sentiment trends with existing analytics dashboard."""
        try:
            # Get recent sentiment trends
            result = await self.db.execute(
                select(SentimentTrend)
                .where(SentimentTrend.created_at >= datetime.utcnow() - timedelta(days=7))
                .order_by(desc(SentimentTrend.created_at))
                .limit(50)
            )
            
            trends = result.scalars().all()
            
            # Get active sentiment alerts
            alerts_result = await self.db.execute(
                select(SentimentAlert)
                .where(
                    and_(
                        SentimentAlert.is_resolved == False,
                        SentimentAlert.triggered_at >= datetime.utcnow() - timedelta(days=1)
                    )
                )
                .order_by(desc(SentimentAlert.triggered_at))
            )
            
            active_alerts = alerts_result.scalars().all()
            
            # Calculate analytics metrics
            analytics_data = {
                "sentiment_trends": [
                    {
                        "entity_name": trend.entity_name,
                        "entity_type": trend.entity_type,
                        "timeframe": trend.timeframe,
                        "average_sentiment": trend.average_sentiment,
                        "trend_direction": trend.trend_direction,
                        "volatility": trend.sentiment_volatility,
                        "total_mentions": trend.total_mentions,
                        "period_start": trend.period_start.isoformat(),
                        "period_end": trend.period_end.isoformat()
                    }
                    for trend in trends
                ],
                "active_alerts": [
                    {
                        "entity_name": alert.entity_name,
                        "entity_type": alert.entity_type,
                        "alert_type": alert.alert_type,
                        "severity": alert.alert_severity,
                        "current_sentiment": alert.current_sentiment,
                        "sentiment_change": alert.sentiment_change,
                        "triggered_at": alert.triggered_at.isoformat()
                    }
                    for alert in active_alerts
                ],
                "summary_metrics": {
                    "total_trends": len(trends),
                    "active_alerts": len(active_alerts),
                    "critical_alerts": len([a for a in active_alerts if a.alert_severity == "critical"]),
                    "entities_monitored": len(set(t.entity_name for t in trends))
                },
                "integration_status": "active",
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Record metrics
            await metrics_collector.record_metric(
                "sentiment_analytics_integration",
                1.0,
                {
                    "trends_count": len(trends),
                    "alerts_count": len(active_alerts),
                    "entities_count": len(set(t.entity_name for t in trends))
                }
            )
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"❌ Error connecting with analytics dashboard: {e}")
            return {
                "error": str(e),
                "integration_status": "error",
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def _record_integration_metrics(self, operation: str, count: int) -> None:
        """Record integration performance metrics."""
        try:
            # Calculate average processing time
            avg_processing_time = 0.0
            if self.integration_metrics["processing_times"]:
                avg_processing_time = sum(self.integration_metrics["processing_times"]) / len(self.integration_metrics["processing_times"])
                
                # Keep only recent processing times to prevent memory growth
                if len(self.integration_metrics["processing_times"]) > 100:
                    self.integration_metrics["processing_times"] = self.integration_metrics["processing_times"][-50:]
            
            # Record metrics
            await metrics_collector.record_metric(
                f"sentiment_news_integration_{operation}",
                count,
                {
                    "articles_processed": self.integration_metrics["articles_processed"],
                    "sentiment_analyses": self.integration_metrics["sentiment_analyses_created"],
                    "alerts_triggered": self.integration_metrics["alerts_triggered"],
                    "avg_processing_time": avg_processing_time
                }
            )
            
        except Exception as e:
            logger.warning(f"Failed to record integration metrics: {e}")
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status."""
        try:
            # Get recent processing statistics
            recent_analyses = await self.db.execute(
                select(func.count(SentimentAnalysis.id))
                .where(SentimentAnalysis.processing_timestamp >= datetime.utcnow() - timedelta(hours=24))
            )
            
            analyses_24h = recent_analyses.scalar() or 0
            
            # Get recent alerts
            recent_alerts = await self.db.execute(
                select(func.count(SentimentAlert.id))
                .where(SentimentAlert.triggered_at >= datetime.utcnow() - timedelta(hours=24))
            )
            
            alerts_24h = recent_alerts.scalar() or 0
            
            # Calculate integration health
            avg_processing_time = 0.0
            if self.integration_metrics["processing_times"]:
                avg_processing_time = sum(self.integration_metrics["processing_times"]) / len(self.integration_metrics["processing_times"])
            
            # Determine health status
            if avg_processing_time < 2.0 and analyses_24h > 0:
                health = "excellent"
            elif avg_processing_time < 5.0 and analyses_24h > 0:
                health = "good"
            elif analyses_24h > 0:
                health = "fair"
            else:
                health = "poor"
            
            return {
                "integration_health": health,
                "metrics": {
                    "articles_processed_24h": analyses_24h,
                    "alerts_triggered_24h": alerts_24h,
                    "average_processing_time": avg_processing_time,
                    "total_articles_processed": self.integration_metrics["articles_processed"],
                    "total_sentiment_analyses": self.integration_metrics["sentiment_analyses_created"],
                    "total_alerts_triggered": self.integration_metrics["alerts_triggered"]
                },
                "configuration": {
                    "auto_sentiment_analysis": self.auto_sentiment_analysis,
                    "sentiment_threshold_alert": self.sentiment_threshold_alert,
                    "batch_processing_size": self.batch_processing_size
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting integration status: {e}")
            return {
                "integration_health": "error",
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def get_integration_metrics(self) -> SentimentIntegrationMetrics:
        """Get comprehensive integration metrics."""
        try:
            avg_processing_time = 0.0
            if self.integration_metrics["processing_times"]:
                avg_processing_time = sum(self.integration_metrics["processing_times"]) / len(self.integration_metrics["processing_times"])
            
            # Determine integration health
            if avg_processing_time < 2.0 and self.integration_metrics["articles_processed"] > 0:
                health = "excellent"
            elif avg_processing_time < 5.0 and self.integration_metrics["articles_processed"] > 0:
                health = "good"
            elif self.integration_metrics["articles_processed"] > 0:
                health = "fair"
            else:
                health = "poor"
            
            return SentimentIntegrationMetrics(
                articles_processed=self.integration_metrics["articles_processed"],
                sentiment_analyses_created=self.integration_metrics["sentiment_analyses_created"],
                alerts_triggered=self.integration_metrics["alerts_triggered"],
                trends_detected=self.integration_metrics["trends_detected"],
                average_processing_time=avg_processing_time,
                integration_health=health
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting integration metrics: {e}")
            return SentimentIntegrationMetrics(
                articles_processed=0,
                sentiment_analyses_created=0,
                alerts_triggered=0,
                trends_detected=0,
                average_processing_time=0.0,
                integration_health="error"
            )