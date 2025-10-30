"""
Microsoft Teams Integration Service - Week 2 Implementation
Complete Teams integration with webhooks, notifications, and bot capabilities.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import base64

import httpx
from app.config import settings

logger = logging.getLogger(__name__)

class TeamsError(Exception):
    """Microsoft Teams integration error"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code

class TeamsService:
    """Microsoft Teams integration service"""
    
    def __init__(self):
        self.webhook_urls = {}  # Store webhook URLs per workspace/channel
        self.bot_token = settings.teams_bot_token
        self.app_id = settings.teams_app_id
        self.app_password = settings.teams_app_password
        
        # Teams API endpoints
        self.graph_base_url = "https://graph.microsoft.com/v1.0"
        self.bot_framework_url = "https://smba.trafficmanager.net/apis"
        
        if not all([self.bot_token, self.app_id, self.app_password]):
            logger.warning("Microsoft Teams not fully configured - some features may be unavailable")
    
    async def send_impact_card(
        self,
        team_id: str,
        channel_id: str,
        impact_card: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send impact card to Teams channel"""
        logger.info(f"📤 Sending impact card to Teams channel {channel_id}")
        
        try:
            # Create adaptive card for impact card
            adaptive_card = self._create_impact_card_adaptive_card(impact_card)
            
            if webhook_url:
                # Use webhook for simple posting
                return await self._send_webhook_message(webhook_url, adaptive_card)
            else:
                # Use Graph API for more advanced features
                return await self._send_graph_message(team_id, channel_id, adaptive_card)
        
        except Exception as e:
            logger.error(f"❌ Failed to send impact card to Teams: {str(e)}")
            raise TeamsError(f"Failed to send impact card: {str(e)}")
    
    async def create_channel_alert(
        self,
        team_id: str,
        channel_id: str,
        alert: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create alert notification in Teams channel"""
        logger.info(f"🚨 Creating alert in Teams channel {channel_id}")
        
        try:
            # Create alert adaptive card
            adaptive_card = self._create_alert_adaptive_card(alert)
            
            # Send via Graph API
            return await self._send_graph_message(team_id, channel_id, adaptive_card)
        
        except Exception as e:
            logger.error(f"❌ Failed to create Teams alert: {str(e)}")
            raise TeamsError(f"Failed to create alert: {str(e)}")
    
    async def schedule_briefing(
        self,
        team_id: str,
        channel_id: str,
        briefing_data: Dict[str, Any],
        schedule: str
    ) -> Dict[str, Any]:
        """Schedule automated executive briefing"""
        logger.info(f"📅 Scheduling briefing for Teams channel {channel_id}")
        
        try:
            # Create briefing adaptive card
            adaptive_card = self._create_briefing_adaptive_card(briefing_data, schedule)
            
            # Send briefing
            result = await self._send_graph_message(team_id, channel_id, adaptive_card)
            
            # In a real implementation, you would also schedule recurring briefings
            # using a task scheduler or Teams app manifest
            
            return {
                "status": "scheduled",
                "team_id": team_id,
                "channel_id": channel_id,
                "schedule": schedule,
                "message_id": result.get("id"),
                "next_briefing": self._calculate_next_briefing_time(schedule)
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to schedule Teams briefing: {str(e)}")
            raise TeamsError(f"Failed to schedule briefing: {str(e)}")
    
    async def register_webhook(
        self,
        workspace_id: str,
        webhook_url: str,
        channel_name: str = "General"
    ) -> Dict[str, Any]:
        """Register Teams webhook for workspace"""
        logger.info(f"🔗 Registering Teams webhook for workspace {workspace_id}")
        
        try:
            # Validate webhook URL
            await self._validate_webhook(webhook_url)
            
            # Store webhook configuration
            self.webhook_urls[workspace_id] = {
                "url": webhook_url,
                "channel_name": channel_name,
                "registered_at": datetime.utcnow().isoformat(),
                "active": True
            }
            
            # Send test message
            test_card = {
                "type": "AdaptiveCard",
                "version": "1.3",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "🎉 Enterprise CIA Teams Integration Active",
                        "weight": "Bolder",
                        "size": "Medium"
                    },
                    {
                        "type": "TextBlock",
                        "text": "Your workspace is now connected to Microsoft Teams. You'll receive competitive intelligence updates here.",
                        "wrap": True
                    }
                ]
            }
            
            await self._send_webhook_message(webhook_url, test_card)
            
            return {
                "status": "registered",
                "workspace_id": workspace_id,
                "webhook_url": webhook_url,
                "channel_name": channel_name,
                "test_message_sent": True
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to register Teams webhook: {str(e)}")
            raise TeamsError(f"Failed to register webhook: {str(e)}")
    
    async def execute_action(
        self,
        action: str,
        payload: Dict[str, Any],
        configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Teams integration action"""
        logger.info(f"⚡ Executing Teams action: {action}")
        
        try:
            if action == "send_notification":
                return await self._handle_send_notification(payload, configuration)
            
            elif action == "send_impact_card":
                return await self._handle_send_impact_card(payload, configuration)
            
            elif action == "create_alert":
                return await self._handle_create_alert(payload, configuration)
            
            elif action == "schedule_briefing":
                return await self._handle_schedule_briefing(payload, configuration)
            
            else:
                raise TeamsError(f"Unknown action: {action}")
        
        except Exception as e:
            logger.error(f"❌ Teams action execution failed: {str(e)}")
            raise TeamsError(f"Action execution failed: {str(e)}")
    
    def _create_impact_card_adaptive_card(self, impact_card: Dict[str, Any]) -> Dict[str, Any]:
        """Create adaptive card for impact card"""
        
        # Determine risk color
        risk_score = impact_card.get("risk_score", 0)
        if risk_score >= 80:
            risk_color = "Attention"
        elif risk_score >= 60:
            risk_color = "Warning"
        else:
            risk_color = "Good"
        
        # Create adaptive card
        card = {
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": [
                {
                    "type": "Container",
                    "style": risk_color,
                    "items": [
                        {
                            "type": "ColumnSet",
                            "columns": [
                                {
                                    "type": "Column",
                                    "width": "stretch",
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": f"🎯 {impact_card.get('competitor', 'Unknown')} Impact Card",
                                            "weight": "Bolder",
                                            "size": "Medium"
                                        },
                                        {
                                            "type": "TextBlock",
                                            "text": f"Risk Level: {impact_card.get('risk_level', 'Unknown').title()}",
                                            "spacing": "None"
                                        }
                                    ]
                                },
                                {
                                    "type": "Column",
                                    "width": "auto",
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": f"{risk_score}/100",
                                            "weight": "Bolder",
                                            "size": "Large",
                                            "horizontalAlignment": "Right"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {
                            "title": "Confidence:",
                            "value": f"{impact_card.get('confidence_score', 0)}%"
                        },
                        {
                            "title": "Sources:",
                            "value": str(impact_card.get('total_sources', 0))
                        },
                        {
                            "title": "Generated:",
                            "value": impact_card.get('generated_at', 'Unknown')[:16]
                        }
                    ]
                }
            ]
        }
        
        # Add key insights
        insights = impact_card.get('key_insights', [])
        if insights:
            card["body"].append({
                "type": "TextBlock",
                "text": "🔍 Key Insights:",
                "weight": "Bolder",
                "spacing": "Medium"
            })
            
            for insight in insights[:3]:  # Limit to 3 insights
                card["body"].append({
                    "type": "TextBlock",
                    "text": f"• {insight}",
                    "wrap": True,
                    "spacing": "Small"
                })
        
        # Add actions
        actions = impact_card.get('recommended_actions', [])
        if actions:
            card["body"].append({
                "type": "TextBlock",
                "text": "⚡ Recommended Actions:",
                "weight": "Bolder",
                "spacing": "Medium"
            })
            
            for action in actions[:2]:  # Limit to 2 actions
                action_text = action.get('action') if isinstance(action, dict) else str(action)
                card["body"].append({
                    "type": "TextBlock",
                    "text": f"• {action_text}",
                    "wrap": True,
                    "spacing": "Small"
                })
        
        # Add action buttons
        card["actions"] = [
            {
                "type": "Action.OpenUrl",
                "title": "View Full Report",
                "url": f"{settings.frontend_url}/impact-cards/{impact_card.get('id', '')}"
            },
            {
                "type": "Action.OpenUrl",
                "title": "Enterprise CIA Dashboard",
                "url": settings.frontend_url or "http://localhost:3000"
            }
        ]
        
        return card
    
    def _create_alert_adaptive_card(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Create adaptive card for alerts"""
        
        alert_type = alert.get("type", "info")
        alert_color = {
            "critical": "Attention",
            "warning": "Warning",
            "info": "Default"
        }.get(alert_type, "Default")
        
        return {
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": [
                {
                    "type": "Container",
                    "style": alert_color,
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"🚨 {alert.get('title', 'Alert')}",
                            "weight": "Bolder",
                            "size": "Medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": alert.get('message', 'No message provided'),
                            "wrap": True,
                            "spacing": "Small"
                        }
                    ]
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {
                            "title": "Type:",
                            "value": alert_type.title()
                        },
                        {
                            "title": "Time:",
                            "value": alert.get('timestamp', datetime.utcnow().isoformat())[:16]
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "View Details",
                    "url": f"{settings.frontend_url}/alerts/{alert.get('id', '')}"
                }
            ]
        }
    
    def _create_briefing_adaptive_card(
        self,
        briefing_data: Dict[str, Any],
        schedule: str
    ) -> Dict[str, Any]:
        """Create adaptive card for executive briefings"""
        
        return {
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "📊 Executive Briefing",
                    "weight": "Bolder",
                    "size": "Large"
                },
                {
                    "type": "TextBlock",
                    "text": f"Scheduled: {schedule}",
                    "spacing": "Small"
                },
                {
                    "type": "TextBlock",
                    "text": "📈 Key Metrics:",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {
                            "title": "New Impact Cards:",
                            "value": str(briefing_data.get('new_impact_cards', 0))
                        },
                        {
                            "title": "High Risk Items:",
                            "value": str(briefing_data.get('high_risk_items', 0))
                        },
                        {
                            "title": "Action Items:",
                            "value": str(briefing_data.get('action_items', 0))
                        }
                    ]
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "View Full Briefing",
                    "url": f"{settings.frontend_url}/briefings/latest"
                }
            ]
        }
    
    async def _send_webhook_message(
        self,
        webhook_url: str,
        adaptive_card: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send message via Teams webhook"""
        
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": adaptive_card
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
            
            return {
                "status": "sent",
                "webhook_url": webhook_url,
                "response_status": response.status_code
            }
    
    async def _send_graph_message(
        self,
        team_id: str,
        channel_id: str,
        adaptive_card: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send message via Microsoft Graph API"""
        
        if not self.bot_token:
            raise TeamsError("Bot token not configured for Graph API access")
        
        url = f"{self.graph_base_url}/teams/{team_id}/channels/{channel_id}/messages"
        
        payload = {
            "body": {
                "contentType": "html",
                "content": "<attachment id=\"adaptive_card\"></attachment>"
            },
            "attachments": [
                {
                    "id": "adaptive_card",
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": json.dumps(adaptive_card)
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            return response.json()
    
    async def _validate_webhook(self, webhook_url: str) -> bool:
        """Validate Teams webhook URL"""
        
        test_payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "version": "1.3",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "🔍 Webhook Validation Test",
                                "weight": "Bolder"
                            }
                        ]
                    }
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=test_payload)
            response.raise_for_status()
            return True
    
    def _calculate_next_briefing_time(self, schedule: str) -> str:
        """Calculate next briefing time based on schedule"""
        # Simplified implementation - in production, use proper scheduling library
        from datetime import datetime, timedelta
        
        if schedule == "daily":
            next_time = datetime.utcnow() + timedelta(days=1)
        elif schedule == "weekly":
            next_time = datetime.utcnow() + timedelta(weeks=1)
        elif schedule == "monthly":
            next_time = datetime.utcnow() + timedelta(days=30)
        else:
            next_time = datetime.utcnow() + timedelta(hours=1)
        
        return next_time.isoformat()
    
    # Action handlers
    async def _handle_send_notification(
        self,
        payload: Dict[str, Any],
        configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle send notification action"""
        
        webhook_url = configuration.get("webhook_url")
        if not webhook_url:
            raise TeamsError("Webhook URL not configured")
        
        message = payload.get("message", "Notification from Enterprise CIA")
        title = payload.get("title", "Notification")
        
        card = {
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "text": title,
                    "weight": "Bolder",
                    "size": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": message,
                    "wrap": True
                }
            ]
        }
        
        return await self._send_webhook_message(webhook_url, card)
    
    async def _handle_send_impact_card(
        self,
        payload: Dict[str, Any],
        configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle send impact card action"""
        
        webhook_url = configuration.get("webhook_url")
        team_id = configuration.get("team_id")
        channel_id = configuration.get("channel_id")
        
        impact_card = payload.get("impact_card", {})
        
        return await self.send_impact_card(
            team_id=team_id,
            channel_id=channel_id,
            impact_card=impact_card,
            webhook_url=webhook_url
        )
    
    async def _handle_create_alert(
        self,
        payload: Dict[str, Any],
        configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle create alert action"""
        
        team_id = configuration.get("team_id")
        channel_id = configuration.get("channel_id")
        
        alert = payload.get("alert", {})
        
        return await self.create_channel_alert(
            team_id=team_id,
            channel_id=channel_id,
            alert=alert
        )
    
    async def _handle_schedule_briefing(
        self,
        payload: Dict[str, Any],
        configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle schedule briefing action"""
        
        team_id = configuration.get("team_id")
        channel_id = configuration.get("channel_id")
        
        briefing_data = payload.get("briefing_data", {})
        schedule = payload.get("schedule", "daily")
        
        return await self.schedule_briefing(
            team_id=team_id,
            channel_id=channel_id,
            briefing_data=briefing_data,
            schedule=schedule
        )