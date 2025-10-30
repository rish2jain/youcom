"""
Configurable Rules Engine for Enterprise CIA
Processes rules.yaml to apply business logic for competitive intelligence
"""

import yaml
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class RulesEngine:
    """Configurable rules engine for competitive intelligence"""
    
    def __init__(self, rules_file: str = "backend/app/rules/rules.yaml"):
        self.rules_file = Path(rules_file)
        self.rules = self._load_rules()
        
    def _load_rules(self) -> Dict[str, Any]:
        """Load rules from YAML configuration file"""
        try:
            if not self.rules_file.exists():
                logger.warning(f"Rules file not found: {self.rules_file}")
                return self._get_default_rules()
                
            with open(self.rules_file, 'r') as f:
                rules = yaml.safe_load(f)
                logger.info(f"✅ Loaded rules from {self.rules_file}")
                return rules
                
        except Exception as e:
            logger.error(f"❌ Failed to load rules: {e}")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> Dict[str, Any]:
        """Default rules if YAML file is not available"""
        return {
            "risk_scoring": [
                {
                    "condition": {"event_type": "product_launch"},
                    "then": {"base_risk_score": 75, "risk_level": "high"}
                }
            ],
            "alert_thresholds": {
                "critical": 85,
                "high": 70,
                "medium": 50,
                "low": 30
            },
            "competitor_tiers": {
                "tier1": ["OpenAI", "Anthropic", "Google AI"],
                "tier2": ["Mistral AI", "Cohere"],
                "tier3": ["Perplexity AI"]
            }
        }
    
    def get_competitor_tier(self, competitor: str) -> str:
        """Determine competitor tier for risk scoring"""
        competitor_tiers = self.rules.get("competitor_tiers", {})
        
        for tier, competitors in competitor_tiers.items():
            if competitor in competitors:
                return tier
                
        # Default to tier3 for unknown competitors
        return "tier3"
    
    def calculate_risk_score(self, 
                           event_type: str, 
                           competitor: str, 
                           base_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk score based on configurable rules"""
        
        competitor_tier = self.get_competitor_tier(competitor)
        base_score = base_analysis.get("risk_score", 50)
        
        # Apply risk scoring rules
        risk_rules = self.rules.get("risk_scoring", [])
        
        for rule in risk_rules:
            condition = rule.get("condition", {})
            
            # Check if rule matches
            matches = True
            if "event_type" in condition and condition["event_type"] != event_type:
                matches = False
            if "competitor_tier" in condition and condition["competitor_tier"] != competitor_tier:
                matches = False
                
            if matches:
                then_clause = rule.get("then", {})
                if "base_risk_score" in then_clause:
                    base_score = then_clause["base_risk_score"]
                break
        
        # Apply tier-based adjustments
        tier_multipliers = {"tier1": 1.2, "tier2": 1.0, "tier3": 0.8}
        adjusted_score = int(base_score * tier_multipliers.get(competitor_tier, 1.0))
        adjusted_score = min(100, max(0, adjusted_score))  # Clamp to 0-100
        
        # Determine risk level
        risk_level = self.get_risk_level(adjusted_score)
        
        return {
            "risk_score": adjusted_score,
            "risk_level": risk_level,
            "competitor_tier": competitor_tier,
            "rule_applied": True
        }
    
    def get_risk_level(self, risk_score: int) -> str:
        """Get risk level based on score and thresholds"""
        thresholds = self.rules.get("alert_thresholds", {})
        
        if risk_score >= thresholds.get("critical", 85):
            return "critical"
        elif risk_score >= thresholds.get("high", 70):
            return "high"
        elif risk_score >= thresholds.get("medium", 50):
            return "medium"
        else:
            return "low"
    
    def assign_action_owner(self, action: str) -> Dict[str, str]:
        """Assign owner and OKR based on action keywords"""
        action_lower = action.lower()
        assignment_rules = self.rules.get("action_assignment", [])
        
        for rule in assignment_rules:
            keywords = rule.get("keywords", [])
            if any(keyword in action_lower for keyword in keywords):
                return {
                    "owner": rule.get("owner", "Strategy Team"),
                    "okr": rule.get("okr", "Drive competitive differentiation")
                }
        
        # Default assignment
        return {
            "owner": "Strategy Team",
            "okr": "Drive competitive differentiation"
        }
    
    def should_require_review(self, 
                            risk_score: int, 
                            confidence_score: int, 
                            credibility_score: float,
                            total_sources: int) -> bool:
        """Determine if impact card requires human review"""
        
        review_rules = self.rules.get("quality_assurance", {}).get("review_required", [])
        
        for rule in review_rules:
            # Parse rule conditions
            if "risk_score" in rule:
                condition = rule["risk_score"]
                if condition.startswith(">=") and risk_score >= int(condition[2:].strip()):
                    return True
                elif condition.startswith("<=") and risk_score <= int(condition[2:].strip()):
                    return True
                elif condition.startswith(">") and risk_score > int(condition[1:].strip()):
                    return True
                elif condition.startswith("<") and risk_score < int(condition[1:].strip()):
                    return True
                    
            if "credibility_score" in rule:
                condition = rule["credibility_score"]
                if condition.startswith("<") and credibility_score < float(condition[1:].strip()):
                    return True
                    
            if "confidence_score" in rule:
                condition = rule["confidence_score"]
                if condition.startswith("<") and confidence_score < int(condition[1:].strip()):
                    return True
                    
            if "total_sources" in rule:
                condition = rule["total_sources"]
                if condition.startswith("<") and total_sources < int(condition[1:].strip()):
                    return True
        
        return False
    
    def get_cache_ttl(self, api_type: str) -> int:
        """Get cache TTL for specific API type"""
        cache_settings = self.rules.get("processing", {}).get("cache_ttl", {})
        
        defaults = {
            "news": 900,      # 15 minutes
            "search": 3600,   # 1 hour
            "analysis": 1800, # 30 minutes
            "research": 604800 # 7 days
        }
        
        return cache_settings.get(api_type, defaults.get(api_type, 3600))
    
    def get_rate_limit(self, api_type: str) -> int:
        """Get rate limit for specific API type"""
        rate_limits = self.rules.get("processing", {}).get("rate_limits", {})
        
        defaults = {
            "news_per_hour": 100,
            "search_per_hour": 200,
            "chat_per_hour": 50,
            "ari_per_hour": 20
        }
        
        return rate_limits.get(f"{api_type}_per_hour", defaults.get(f"{api_type}_per_hour", 100))
    
    def format_notification_message(self, 
                                  template_type: str, 
                                  context: Dict[str, Any]) -> Dict[str, str]:
        """Format notification message using templates"""
        
        templates = self.rules.get("notification_templates", {})
        template = templates.get(template_type, {})
        
        if not template:
            return {
                "subject": f"Alert: {context.get('competitor', 'Unknown')}",
                "body": f"Alert triggered for {context.get('competitor', 'Unknown')}"
            }
        
        # Format subject and body with context variables
        subject = template.get("subject", "").format(**context)
        body = template.get("body", "").format(**context)
        
        return {"subject": subject, "body": body}
    
    def validate_source_quality(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate source quality based on diversity and credibility rules"""
        
        qa_rules = self.rules.get("quality_assurance", {})
        source_diversity = qa_rules.get("source_diversity", {})
        
        # Count sources by tier
        tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
        domain_counts = {}
        
        for source in sources:
            tier = source.get("tier", "tier3")
            tier_counts[tier] += 1
            
            domain = source.get("domain", "unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Check requirements
        issues = []
        
        min_tier1 = source_diversity.get("min_tier1_sources", 2)
        if tier_counts["tier1"] < min_tier1:
            issues.append(f"Need at least {min_tier1} tier-1 sources (have {tier_counts['tier1']})")
        
        min_total = source_diversity.get("min_total_sources", 5)
        if len(sources) < min_total:
            issues.append(f"Need at least {min_total} total sources (have {len(sources)})")
        
        max_single_domain = source_diversity.get("max_single_domain_percentage", 40)
        if sources:
            max_domain_count = max(domain_counts.values())
            max_domain_pct = (max_domain_count / len(sources)) * 100
            if max_domain_pct > max_single_domain:
                issues.append(f"Too many sources from single domain ({max_domain_pct:.1f}% > {max_single_domain}%)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "tier_counts": tier_counts,
            "domain_counts": domain_counts,
            "total_sources": len(sources)
        }
    
    def reload_rules(self):
        """Reload rules from file (for dynamic updates)"""
        self.rules = self._load_rules()
        logger.info("🔄 Rules reloaded from configuration file")

# Global rules engine instance
rules_engine = RulesEngine()

def get_rules_engine() -> RulesEngine:
    """Get the global rules engine instance"""
    return rules_engine