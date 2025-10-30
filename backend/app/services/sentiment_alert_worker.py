"""Background worker for sentiment trend analysis and alerting."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.services.sentiment_trend_analyzer import sentiment_trend_analyzer
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class SentimentAlertWorker:
    """Background worker for sentiment trend analysis and alerting."""
    
    def __init__(self, analysis_interval: int = 300):  # 5 minutes default
        self.analysis_interval = analysis_interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.last_analysis = {}  # Track last analysis time per timeframe

    async def start(self):
        """Start the alert worker."""
        if self.is_running:
            logger.warning("Sentiment alert worker is already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._worker_loop())
        logger.info("Sentiment alert worker started")

    async def stop(self):
        """Stop the alert worker."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Sentiment alert worker stopped")

    async def _worker_loop(self):
        """Main worker loop."""
        while self.is_running:
            try:
                current_time = datetime.now(timezone.utc)
                
                # Run daily analysis every hour
                if self._should_run_analysis("daily", current_time, hours=1):
                    await self._run_daily_analysis()
                    self.last_analysis["daily"] = current_time
                
                # Run weekly analysis every 6 hours
                if self._should_run_analysis("weekly", current_time, hours=6):
                    await self._run_weekly_analysis()
                    self.last_analysis["weekly"] = current_time
                
                # Run monthly analysis every 24 hours
                if self._should_run_analysis("monthly", current_time, hours=24):
                    await self._run_monthly_analysis()
                    self.last_analysis["monthly"] = current_time
                
                # Clean up old data every 24 hours
                if self._should_run_analysis("cleanup", current_time, hours=24):
                    await self._run_cleanup()
                    self.last_analysis["cleanup"] = current_time
                
                # Wait before next iteration
                await asyncio.sleep(self.analysis_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sentiment alert worker loop: {str(e)}")
                await asyncio.sleep(self.analysis_interval)

    def _should_run_analysis(self, analysis_type: str, current_time: datetime, hours: int) -> bool:
        """Check if analysis should run based on last run time."""
        last_run = self.last_analysis.get(analysis_type)
        if not last_run:
            return True
        
        return current_time - last_run >= timedelta(hours=hours)

    async def _run_daily_analysis(self):
        """Run daily sentiment trend analysis and alerting."""
        try:
            logger.info("Running daily sentiment trend analysis")
            
            # Analyze daily trends
            trend_results = await sentiment_trend_analyzer.analyze_trends("daily")
            logger.info(f"Analyzed trends for {len(trend_results)} entities")
            
            # Detect sentiment shifts
            alert_triggers = await sentiment_trend_analyzer.detect_sentiment_shifts(minimum_change=0.20)
            logger.info(f"Detected {len(alert_triggers)} potential alerts")
            
            if alert_triggers:
                # Create alerts
                alert_ids = await sentiment_trend_analyzer.create_sentiment_alerts(alert_triggers)
                
                # Send notifications
                if alert_ids:
                    await sentiment_trend_analyzer.send_alert_notifications(alert_ids)
                    logger.info(f"Processed {len(alert_ids)} sentiment alerts")
            
        except Exception as e:
            logger.error(f"Error in daily sentiment analysis: {str(e)}")

    async def _run_weekly_analysis(self):
        """Run weekly sentiment trend analysis."""
        try:
            logger.info("Running weekly sentiment trend analysis")
            
            # Analyze weekly trends with lower threshold for longer-term shifts
            trend_results = await sentiment_trend_analyzer.analyze_trends("weekly")
            logger.info(f"Analyzed weekly trends for {len(trend_results)} entities")
            
            # Detect weekly sentiment shifts (lower threshold for longer timeframe)
            alert_triggers = await sentiment_trend_analyzer.detect_sentiment_shifts(minimum_change=0.15)
            
            if alert_triggers:
                # Filter for weekly-specific alerts (avoid duplicating daily alerts)
                weekly_alerts = [
                    trigger for trigger in alert_triggers 
                    if trigger.change_percentage >= 0.15 and trigger.change_percentage < 0.20
                ]
                
                if weekly_alerts:
                    alert_ids = await sentiment_trend_analyzer.create_sentiment_alerts(weekly_alerts)
                    if alert_ids:
                        await sentiment_trend_analyzer.send_alert_notifications(alert_ids)
                        logger.info(f"Processed {len(alert_ids)} weekly sentiment alerts")
            
        except Exception as e:
            logger.error(f"Error in weekly sentiment analysis: {str(e)}")

    async def _run_monthly_analysis(self):
        """Run monthly sentiment trend analysis."""
        try:
            logger.info("Running monthly sentiment trend analysis")
            
            # Analyze monthly trends
            trend_results = await sentiment_trend_analyzer.analyze_trends("monthly")
            logger.info(f"Analyzed monthly trends for {len(trend_results)} entities")
            
            # Monthly analysis is mainly for data storage and long-term trend tracking
            # Alerts are primarily handled by daily/weekly analysis
            
        except Exception as e:
            logger.error(f"Error in monthly sentiment analysis: {str(e)}")

    async def _run_cleanup(self):
        """Run cleanup of old data."""
        try:
            logger.info("Running sentiment data cleanup")
            
            # Clean up old alerts
            await sentiment_trend_analyzer.cleanup_old_alerts(retention_days=30)
            
            # Additional cleanup could be added here for old trend data
            
        except Exception as e:
            logger.error(f"Error in sentiment data cleanup: {str(e)}")

    async def trigger_immediate_analysis(self, entity_name: Optional[str] = None):
        """Trigger immediate sentiment analysis for specific entity or all entities."""
        try:
            logger.info(f"Triggering immediate sentiment analysis for {entity_name or 'all entities'}")
            
            # Run analysis with entity filter if specified
            trend_results = await sentiment_trend_analyzer.analyze_trends("daily", entity_filter=entity_name)
            
            # Detect and process alerts
            alert_triggers = await sentiment_trend_analyzer.detect_sentiment_shifts(minimum_change=0.15)
            
            if entity_name:
                # Filter alerts for specific entity
                alert_triggers = [
                    trigger for trigger in alert_triggers 
                    if trigger.entity_name.lower() == entity_name.lower()
                ]
            
            if alert_triggers:
                alert_ids = await sentiment_trend_analyzer.create_sentiment_alerts(alert_triggers)
                if alert_ids:
                    await sentiment_trend_analyzer.send_alert_notifications(alert_ids)
                    logger.info(f"Processed {len(alert_ids)} immediate sentiment alerts")
            
            return {
                "trends_analyzed": len(trend_results),
                "alerts_created": len(alert_triggers),
                "entity_filter": entity_name
            }
            
        except Exception as e:
            logger.error(f"Error in immediate sentiment analysis: {str(e)}")
            return {"error": str(e)}

    async def get_worker_status(self) -> dict:
        """Get current worker status."""
        return {
            "is_running": self.is_running,
            "analysis_interval": self.analysis_interval,
            "last_analysis": {
                timeframe: timestamp.isoformat() if timestamp else None
                for timeframe, timestamp in self.last_analysis.items()
            },
            "next_analysis": {
                "daily": self._get_next_analysis_time("daily", hours=1),
                "weekly": self._get_next_analysis_time("weekly", hours=6),
                "monthly": self._get_next_analysis_time("monthly", hours=24),
                "cleanup": self._get_next_analysis_time("cleanup", hours=24)
            }
        }

    def _get_next_analysis_time(self, analysis_type: str, hours: int) -> Optional[str]:
        """Get next scheduled analysis time."""
        last_run = self.last_analysis.get(analysis_type)
        if not last_run:
            return "immediate"
        
        next_run = last_run + timedelta(hours=hours)
        return next_run.isoformat()


# Global worker instance
sentiment_alert_worker = SentimentAlertWorker()