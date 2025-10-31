"""Market Expansion scenario for Enterprise CIA demos.

This scenario demonstrates tracking a competitor's expansion into new
markets or verticals.
"""

from typing import Any, Dict

from demo_system_cia.scenarios.base import CIADemoScenario


class MarketExpansionScenario(CIADemoScenario):
    """
    Scenario: Tracking competitor market expansion moves.

    Timeline: 40 seconds
    APIs Used: News, Search, Chat (Custom Agents), ARI
    Focus: Market entry signals, competitive positioning, threat assessment
    """

    def __init__(self):
        super().__init__(
            name="market_expansion",
            description="Track competitor expansion into new markets or verticals",
            duration_seconds=40,
            expected_apis=["news", "search", "chat", "ari"],
        )

    def get_scenario_config(self) -> Dict[str, Any]:
        """Get scenario configuration for market expansion tracking."""
        return {
            "competitor": "Anthropic",
            "search_terms": [
                "Anthropic enterprise partnerships",
                "Anthropic market expansion",
                "Claude enterprise deals",
            ],
            "analysis_focus": "market_expansion",
            "expected_insights": [
                "market_entry_signals",
                "partnership_announcements",
                "competitive_positioning",
                "threat_level",
                "defensive_actions",
            ],
            "demo_mode": False,  # Use real APIs
        }

    def get_visual_timeline(self) -> list[Dict[str, Any]]:
        """Get visual timeline for video recording."""
        return [
            {
                "timestamp": 0,
                "action": "scroll",
                "target": "impact_cards",
                "distance": 600,
                "duration": 2,
                "narration": "Monitoring Anthropic's market moves",
            },
            {
                "timestamp": 5,
                "action": "highlight",
                "target": "expansion_card",
                "narration": "Enterprise partnership detected",
            },
            {
                "timestamp": 10,
                "action": "click",
                "target": "expansion_card",
                "narration": "Analyzing market implications...",
            },
            {
                "timestamp": 13,
                "action": "wait",
                "target": "search_results",
                "narration": "Search API enriching with market data",
            },
            {
                "timestamp": 18,
                "action": "click",
                "target": "analysis_tab",
                "narration": "Strategic threat assessment",
            },
            {
                "timestamp": 23,
                "action": "wait",
                "target": "threat_level",
                "narration": "Impact: High threat to enterprise segment",
            },
            {
                "timestamp": 28,
                "action": "click",
                "target": "actions_tab",
                "narration": "Defensive strategy recommendations",
            },
            {
                "timestamp": 33,
                "action": "scroll",
                "target": "actions",
                "distance": 150,
                "duration": 1,
                "narration": "Prioritized response actions",
            },
            {
                "timestamp": 38,
                "action": "wait",
                "target": "complete",
                "narration": "Complete intelligence in 40 seconds",
            },
        ]
