"""
Resilience configuration based on Discord hackathon insights.
Configurable settings for circuit breakers, rate limiting, and fallback strategies.
"""

from dataclasses import dataclass
from typing import Dict, Any
import os
import copy

@dataclass
class APIResilienceConfig:
    """Configuration for individual API resilience"""
    failure_threshold: int
    recovery_timeout: int
    success_threshold: int
    min_request_interval: float
    timeout: float

# Default configurations based on Discord insights
DEFAULT_API_CONFIGS = {
    "news": APIResilienceConfig(
        failure_threshold=3,        # News API is sensitive to rate limits
        recovery_timeout=30,        # Quick recovery
        success_threshold=2,        # Need 2 successes to close circuit
        min_request_interval=2.0,   # 2 seconds between requests
        timeout=15.0               # 15 second timeout
    ),
    "search": APIResilienceConfig(
        failure_threshold=5,        # Search API is more reliable
        recovery_timeout=60,        # Standard recovery
        success_threshold=2,
        min_request_interval=1.5,   # 1.5 seconds between requests
        timeout=20.0               # 20 second timeout
    ),
    "chat": APIResilienceConfig(
        failure_threshold=2,        # Custom agents hang frequently
        recovery_timeout=120,       # Longer recovery for agent issues
        success_threshold=3,        # Need more successes due to instability
        min_request_interval=5.0,   # 5 seconds between requests (they hang)
        timeout=30.0               # 30 second timeout
    ),
    "ari": APIResilienceConfig(
        failure_threshold=3,        # ARI/Express agent issues
        recovery_timeout=180,       # Longest recovery time
        success_threshold=2,
        min_request_interval=10.0,  # 10 seconds between requests
        timeout=60.0               # 60 second timeout for comprehensive research
    )
}

class ResilienceSettings:
    """Global resilience settings"""
    
    def __init__(self):
        # Load from environment or use defaults
        self.enable_circuit_breakers = os.getenv("ENABLE_CIRCUIT_BREAKERS", "true").lower() == "true"
        self.enable_rate_limiting = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
        self.enable_query_optimization = os.getenv("ENABLE_QUERY_OPTIMIZATION", "true").lower() == "true"
        self.enable_fallback_data = os.getenv("ENABLE_FALLBACK_DATA", "true").lower() == "true"
        
        # Aggressive mode for hackathon (more conservative settings)
        self.hackathon_mode = os.getenv("HACKATHON_MODE", "true").lower() == "true"
        
        # Create instance-specific copy of configs
        self.api_configs = copy.deepcopy(DEFAULT_API_CONFIGS)
        
        if self.hackathon_mode:
            # More conservative settings for demo reliability
            for config in self.api_configs.values():
                config.failure_threshold = max(1, config.failure_threshold - 1)
                config.min_request_interval *= 1.5
                config.timeout *= 0.8  # Shorter timeouts for demo
    
    def get_api_config(self, api_type: str) -> APIResilienceConfig:
        """Get configuration for specific API"""
        return self.api_configs.get(api_type, self.api_configs["search"])
    
    def get_fallback_strategy(self, api_type: str) -> str:
        """Get fallback strategy for API"""
        strategies = {
            "news": "demo_data",      # Use demo news articles
            "search": "demo_data",    # Use demo search results
            "chat": "simplified",     # Use simplified analysis
            "ari": "cached_report"    # Use cached or demo report
        }
        return strategies.get(api_type, "demo_data")

# Global instance
resilience_settings = ResilienceSettings()

# Query optimization patterns based on Discord insights
QUERY_OPTIMIZATION_PATTERNS = {
    "boolean_operators": {
        # These don't work well according to Discord
        "avoid": ["AND", "OR", "NOT", "+", "-"],
        "replace_with": " "
    },
    "api_specific": {
        "news": {
            "remove_words": ["company", "business", "corporation"],
            "prefer_terms": ["announcement", "launch", "update", "news"]
        },
        "search": {
            "add_context": ["overview", "analysis", "information"],
            "max_length": 100
        },
        "chat": {
            "prefix": "Analyze the competitive impact of:",
            "structure": True
        },
        "ari": {
            "prefix": "Comprehensive research report on:",
            "add_context": ["market analysis", "strategic positioning"]
        }
    }
}

# Fallback data templates
FALLBACK_DATA_TEMPLATES = {
    "news": {
        "template": "Recent developments from {competitor} show continued market activity",
        "confidence": 0.3
    },
    "search": {
        "template": "Market information about {competitor} indicates competitive positioning",
        "confidence": 0.4
    },
    "chat": {
        "template": "Analysis suggests {competitor} represents moderate competitive impact",
        "risk_score_range": (40, 70),
        "confidence": 0.5
    },
    "ari": {
        "template": "Research indicates {competitor} maintains strategic market presence",
        "confidence": 0.4
    }
}

def get_resilience_config() -> Dict[str, Any]:
    """Get complete resilience configuration"""
    return {
        "settings": {
            "circuit_breakers_enabled": resilience_settings.enable_circuit_breakers,
            "rate_limiting_enabled": resilience_settings.enable_rate_limiting,
            "query_optimization_enabled": resilience_settings.enable_query_optimization,
            "fallback_data_enabled": resilience_settings.enable_fallback_data,
            "hackathon_mode": resilience_settings.hackathon_mode
        },
        "api_configs": {
            api: {
                "failure_threshold": config.failure_threshold,
                "recovery_timeout": config.recovery_timeout,
                "success_threshold": config.success_threshold,
                "min_request_interval": config.min_request_interval,
                "timeout": config.timeout
            }
            for api, config in DEFAULT_API_CONFIGS.items()
        },
        "optimization_patterns": QUERY_OPTIMIZATION_PATTERNS,
        "fallback_templates": FALLBACK_DATA_TEMPLATES
    }