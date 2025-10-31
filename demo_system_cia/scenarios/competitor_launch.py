"""Competitor Product Launch scenario for Enterprise CIA demos.

This scenario demonstrates detecting and analyzing a major product launch
from a competitor using all 4 You.com APIs.
"""

from typing import Any, Dict

from demo_system_cia.scenarios.base import CIADemoScenario


class CompetitorProductLaunchScenario(CIADemoScenario):
    """
    Scenario: Detecting and analyzing a competitor product launch.

    Timeline: 45 seconds
    APIs Used: News, Search, Chat (Custom Agents), ARI
    Focus: Product announcements, market impact, recommended actions
    """

    def __init__(self):
        super().__init__(
            name="competitor_product_launch",
            description="Detect and analyze competitor product launch announcements",
            duration_seconds=45,
            expected_apis=["news", "search", "chat", "ari"],
        )

    def get_scenario_config(self) -> Dict[str, Any]:
        """Get scenario configuration for product launch detection."""
        return {
            "competitor": "OpenAI",
            "search_terms": [
                "OpenAI product launch",
                "OpenAI new features",
                "GPT updates",
            ],
            "analysis_focus": "product_launch",
            "expected_insights": [
                "product_features",
                "market_positioning",
                "competitive_threat",
                "recommended_actions",
            ],
            "demo_mode": False,  # Use real APIs
        }

    def get_visual_timeline(self) -> list[Dict[str, Any]]:
        """Get visual timeline for video recording."""
        return [
            {
                "timestamp": 0,
                "action": "load",
                "target": "dashboard",
                "narration": "Enterprise CIA Dashboard",
            },
            {
                "timestamp": 3,
                "action": "wait",
                "target": "hero_section",
                "narration": "Real-time Competitive Intelligence",
            },
            {
                "timestamp": 8,
                "action": "scroll",
                "target": "watchlist",
                "distance": 400,
                "duration": 2,
                "narration": "Monitoring OpenAI for new announcements",
            },
            {
                "timestamp": 12,
                "action": "highlight",
                "target": "impact_card",
                "narration": "New product launch detected!",
            },
            {
                "timestamp": 15,
                "action": "click",
                "target": "impact_card_expand",
                "narration": "Let's analyze the impact...",
            },
            {
                "timestamp": 18,
                "action": "wait",
                "target": "news_tab",
                "narration": "News API: 12 sources detected the launch",
            },
            {
                "timestamp": 22,
                "action": "click",
                "target": "analysis_tab",
                "narration": "Custom Agents analyze strategic implications",
            },
            {
                "timestamp": 27,
                "action": "wait",
                "target": "analysis_content",
                "narration": "Market impact assessment complete",
            },
            {
                "timestamp": 32,
                "action": "click",
                "target": "actions_tab",
                "narration": "Recommended response actions",
            },
            {
                "timestamp": 37,
                "action": "scroll",
                "target": "actions_list",
                "distance": 200,
                "duration": 1.5,
                "narration": "Prioritized action items for your team",
            },
            {
                "timestamp": 42,
                "action": "wait",
                "target": "complete",
                "narration": "All 4 You.com APIs working together",
            },
        ]
