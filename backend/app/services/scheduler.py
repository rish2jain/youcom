"""
Background scheduler for automated alerts and digest generation.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.watch import WatchItem
from app.models.notification import NotificationRule, NotificationLog
from app.models.impact_card import ImpactCard
from app.services.you_client import YouComOrchestrator, YouComAPIError
from app.services.email_service import get_email_service
from app.config import settings

logger = logging.getLogger(__name__)

class AlertScheduler:
    """Automated alert scheduling and digest generation"""
    
    def __init__(self):
        self.running = False
        self.task = None
        
    async def start(self):
        """Start the background scheduler"""
        if self.running:
            return
            
        self.running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        logger.info("🔔 Alert scheduler started")
        
    async def stop(self):
        """Stop the background scheduler"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("🔔 Alert scheduler stopped")
        
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                await self._process_scheduled_alerts()
                await self._generate_daily_digest()
                
                # Run every 15 minutes
                await asyncio.sleep(900)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
                
    async def _process_scheduled_alerts(self):
        """Process scheduled alert rules"""
        async with AsyncSessionLocal() as session:
            # Get active notification rules
            result = await session.execute(
                select(NotificationRule).where(NotificationRule.active == True)
            )
            rules = result.scalars().all()
            
            for rule in rules:
                try:
                    await self._evaluate_rule(session, rule)
                except Exception as e:
                    logger.error(f"❌ Error evaluating rule {rule.id}: {e}")
                    
    async def _evaluate_rule(self, session: AsyncSession, rule: NotificationRule):
        """Evaluate a specific notification rule"""
        
        # Skip if rule was triggered recently (avoid spam)
        if rule.last_triggered_at:
            time_since_last = datetime.utcnow() - rule.last_triggered_at
            if time_since_last < timedelta(hours=1):  # Minimum 1 hour between alerts
                return
                
        # Get recent impact cards for this competitor
        cutoff = datetime.utcnow() - timedelta(hours=24)
        result = await session.execute(
            select(ImpactCard)
            .where(ImpactCard.competitor_name == rule.competitor_name)
            .where(ImpactCard.created_at >= cutoff)
            .order_by(ImpactCard.created_at.desc())
            .limit(5)
        )
        recent_cards = result.scalars().all()
        
        if not recent_cards:
            return
            
        # Evaluate rule conditions
        triggered = False
        alert_context = {}
        
        if rule.condition_type == "risk_threshold":
            latest_card = recent_cards[0]
            if latest_card.risk_score >= (rule.threshold_value or 80):
                triggered = True
                alert_context = {
                    "competitor": rule.competitor_name,
                    "risk_score": latest_card.risk_score,
                    "risk_level": latest_card.risk_level,
                    "confidence": latest_card.confidence_score,
                    "total_sources": latest_card.total_sources,
                    "key_insights": latest_card.key_insights[:3],  # Top 3 insights
                    "card_id": latest_card.id
                }
                
        elif rule.condition_type == "trend_change":
            if len(recent_cards) >= 2:
                current_risk = recent_cards[0].risk_score
                previous_risk = recent_cards[1].risk_score
                change = current_risk - previous_risk
                
                if abs(change) >= (rule.threshold_value or 20):
                    triggered = True
                    alert_context = {
                        "competitor": rule.competitor_name,
                        "current_risk": current_risk,
                        "previous_risk": previous_risk,
                        "change": change,
                        "trend": "increased" if change > 0 else "decreased"
                    }
                    
        if triggered:
            await self._send_alert(session, rule, alert_context)
            
    async def _send_alert(self, session: AsyncSession, rule: NotificationRule, context: Dict[str, Any]):
        """Send an alert notification"""
        
        # Create notification log
        log_entry = NotificationLog(
            rule_id=rule.id,
            competitor_name=rule.competitor_name,
            channel=rule.channel,
            target=rule.target,
            message=self._format_alert_message(rule, context),
            triggered_at=datetime.utcnow()
        )
        session.add(log_entry)
        
        # Update rule last triggered time
        rule.last_triggered_at = datetime.utcnow()
        
        # Send notification based on channel
        if rule.channel == "email":
            await self._send_email_alert(rule, context)
        elif rule.channel == "slack":
            await self._send_slack_alert(rule, context)
        elif rule.channel == "webhook":
            await self._send_webhook_alert(rule, context)
            
        await session.commit()
        logger.info(f"🔔 Alert sent for {rule.competitor_name} via {rule.channel}")
        
    def _format_alert_message(self, rule: NotificationRule, context: Dict[str, Any]) -> str:
        """Format alert message based on rule type"""
        
        if rule.condition_type == "risk_threshold":
            return f"""
🚨 HIGH RISK ALERT: {context['competitor']}

Risk Score: {context['risk_score']}/100 ({context['risk_level'].upper()})
Confidence: {context['confidence']}%
Sources: {context['total_sources']}

Key Insights:
{chr(10).join(f"• {insight}" for insight in context['key_insights'])}

View Impact Card: /impact/{context['card_id']}
            """.strip()
            
        elif rule.condition_type == "trend_change":
            return f"""
📈 RISK TREND ALERT: {context['competitor']}

Risk Score: {context['current_risk']}/100 (was {context['previous_risk']}/100)
Change: {context['change']:+d} points ({context['trend']})

This represents a significant change in competitive risk level.
            """.strip()
            
        return f"Alert triggered for {rule.competitor_name}"
        
    async def _send_email_alert(self, rule: NotificationRule, context: Dict[str, Any]):
        """Send email alert"""
        email_service = get_email_service(settings)
        if not email_service:
            logger.warning("Email service not configured, skipping email alert")
            return
            
        subject = f"🚨 Competitive Alert: {context.get('competitor', rule.competitor_name)}"
        message = self._format_alert_message(rule, context)
        
        try:
            await email_service.send_alert_email(
                to_email=rule.target,
                subject=subject,
                message=message,
                context=context
            )
        except Exception as e:
            logger.error(f"❌ Failed to send email alert: {e}")
            
    async def _send_slack_alert(self, rule: NotificationRule, context: Dict[str, Any]):
        """Send Slack alert (placeholder for future implementation)"""
        logger.info(f"📱 Slack alert would be sent to {rule.target}")
        # TODO: Implement Slack webhook integration
        
    async def _send_webhook_alert(self, rule: NotificationRule, context: Dict[str, Any]):
        """Send webhook alert (placeholder for future implementation)"""
        logger.info(f"🔗 Webhook alert would be sent to {rule.target}")
        # TODO: Implement webhook integration
        
    async def _generate_daily_digest(self):
        """Generate daily digest of competitive intelligence"""
        now = datetime.utcnow()
        
        # Only generate digest once per day at 9 AM UTC
        if now.hour != 9 or now.minute > 15:
            return
            
        async with AsyncSessionLocal() as session:
            # Get impact cards from last 24 hours
            cutoff = now - timedelta(hours=24)
            result = await session.execute(
                select(ImpactCard)
                .where(ImpactCard.created_at >= cutoff)
                .order_by(ImpactCard.risk_score.desc())
            )
            recent_cards = result.scalars().all()
            
            if not recent_cards:
                return
                
            digest_content = self._format_daily_digest(recent_cards)
            
            # Get email subscribers (users with digest notification rules)
            digest_rules = await session.execute(
                select(NotificationRule)
                .where(NotificationRule.active == True)
                .where(NotificationRule.condition_type == "daily_digest")
            )
            
            for rule in digest_rules.scalars():
                await self._send_digest_email(rule.target, digest_content)
                
            logger.info(f"📧 Daily digest generated with {len(recent_cards)} impact cards")
            
    def _format_daily_digest(self, cards: List[ImpactCard]) -> str:
        """Format daily digest content"""
        
        high_risk_cards = [c for c in cards if c.risk_score >= 80]
        medium_risk_cards = [c for c in cards if 60 <= c.risk_score < 80]
        
        digest = f"""
# Daily Competitive Intelligence Digest
*{datetime.utcnow().strftime('%B %d, %Y')}*

## Summary
- **{len(cards)}** total impact cards generated
- **{len(high_risk_cards)}** high-risk alerts
- **{len(medium_risk_cards)}** medium-risk updates

## High-Risk Alerts 🚨
"""
        
        for card in high_risk_cards[:5]:  # Top 5 high-risk
            digest += f"""
### {card.competitor_name} - Risk Score: {card.risk_score}/100
- **Risk Level**: {card.risk_level.upper()}
- **Confidence**: {card.confidence_score}%
- **Sources**: {card.total_sources}
- **Key Insight**: {card.key_insights[0] if card.key_insights else 'No insights available'}

"""
        
        if medium_risk_cards:
            digest += "\n## Medium-Risk Updates 📊\n"
            for card in medium_risk_cards[:3]:  # Top 3 medium-risk
                digest += f"- **{card.competitor_name}**: Risk {card.risk_score}/100 ({card.total_sources} sources)\n"
                
        digest += f"""

---
*Generated by Enterprise CIA - Powered by You.com APIs*
*View full dashboard: [Enterprise CIA Dashboard](/)*
"""
        
        return digest
        
    async def _send_digest_email(self, email: str, content: str):
        """Send daily digest email"""
        email_service = get_email_service(settings)
        if not email_service:
            return
            
        try:
            await email_service.send_digest_email(
                to_email=email,
                subject=f"Daily Competitive Intelligence Digest - {datetime.utcnow().strftime('%B %d, %Y')}",
                content=content
            )
        except Exception as e:
            logger.error(f"❌ Failed to send digest email: {e}")

# Global scheduler instance
alert_scheduler = AlertScheduler()

@asynccontextmanager
async def get_scheduler():
    """Context manager for scheduler lifecycle"""
    await alert_scheduler.start()
    try:
        yield alert_scheduler
    finally:
        await alert_scheduler.stop()