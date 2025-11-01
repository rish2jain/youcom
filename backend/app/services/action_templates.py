"""
Action Templates for Decision Engine

This module contains rule-based action templates for different competitive scenarios,
organized by risk score ranges and impact areas.
"""

from typing import Dict, List, Any
from enum import Enum

class ActionCategory(str, Enum):
    IMMEDIATE = "immediate"
    SHORT_TERM = "short-term"
    STRATEGIC = "strategic"

class ActionPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class BudgetImpact(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ActionTemplateManager:
    """Manages action templates and provides rule-based action generation."""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.impact_area_templates = self._initialize_impact_area_templates()
        self.timeline_estimates = self._initialize_timeline_estimates()
    
    def _initialize_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize rule-based action templates by risk score range."""
        return {
            "critical": [  # Risk score 90-100
                {
                    "id": "critical_001",
                    "title": "Emergency Competitive Response",
                    "description": "Launch immediate competitive response to counter {competitor_name}'s critical threat to market position.",
                    "category": ActionCategory.IMMEDIATE,
                    "priority": ActionPriority.HIGH,
                    "timeline": "1-2 weeks",
                    "estimated_hours": 120,
                    "team_members_required": 6,
                    "budget_impact": BudgetImpact.HIGH,
                    "dependencies": [
                        "Executive approval",
                        "Legal review",
                        "Marketing team availability",
                        "PR team coordination"
                    ],
                    "reasoning": [
                        "Critical risk score indicates severe competitive threat",
                        "Immediate action needed to prevent market share loss",
                        "High confidence in threat assessment requires urgent response"
                    ],
                    "success_criteria": [
                        "Response launched within 2 weeks",
                        "Market position stabilized",
                        "Competitive threat neutralized"
                    ]
                },
                {
                    "id": "critical_002", 
                    "title": "Emergency Product Strategy Pivot",
                    "description": "Execute emergency pivot of product strategy to address critical competitive threat from {competitor_name}.",
                    "category": ActionCategory.IMMEDIATE,
                    "priority": ActionPriority.HIGH,
                    "timeline": "3-5 days",
                    "estimated_hours": 80,
                    "team_members_required": 4,
                    "budget_impact": BudgetImpact.HIGH,
                    "dependencies": [
                        "Product team availability",
                        "Engineering leadership",
                        "Competitive analysis data",
                        "Executive decision"
                    ],
                    "reasoning": [
                        "Product strategy requires immediate adjustment",
                        "Critical threat demands strategic reassessment",
                        "Time-sensitive opportunity to maintain competitive advantage"
                    ],
                    "success_criteria": [
                        "Strategy pivot approved within 5 days",
                        "Implementation plan created",
                        "Resource allocation confirmed"
                    ]
                },
                {
                    "id": "critical_003",
                    "title": "Crisis Communication Plan",
                    "description": "Activate crisis communication plan to address market concerns about {competitor_name}'s competitive moves.",
                    "category": ActionCategory.IMMEDIATE,
                    "priority": ActionPriority.HIGH,
                    "timeline": "24-48 hours",
                    "estimated_hours": 40,
                    "team_members_required": 3,
                    "budget_impact": BudgetImpact.MEDIUM,
                    "dependencies": [
                        "PR team availability",
                        "Executive messaging approval",
                        "Legal review of communications"
                    ],
                    "reasoning": [
                        "Market confidence needs immediate reinforcement",
                        "Proactive communication prevents speculation",
                        "Stakeholder reassurance is critical"
                    ],
                    "success_criteria": [
                        "Communication plan activated within 48 hours",
                        "Key stakeholders informed",
                        "Market confidence maintained"
                    ]
                }
            ],
            "high": [  # Risk score 80-89
                {
                    "id": "high_001",
                    "title": "Accelerated Feature Development",
                    "description": "Fast-track development of competitive features to counter {competitor_name}'s product advantages.",
                    "category": ActionCategory.SHORT_TERM,
                    "priority": ActionPriority.HIGH,
                    "timeline": "4-6 weeks",
                    "estimated_hours": 200,
                    "team_members_required": 5,
                    "budget_impact": BudgetImpact.HIGH,
                    "dependencies": [
                        "Engineering capacity",
                        "Product requirements finalization",
                        "Design resources",
                        "QA testing capacity"
                    ],
                    "reasoning": [
                        "High risk score indicates significant competitive pressure",
                        "Feature development needed to maintain competitive parity",
                        "Time-to-market advantage is critical"
                    ],
                    "success_criteria": [
                        "Features delivered within 6 weeks",
                        "Competitive parity achieved",
                        "User adoption targets met"
                    ]
                },
                {
                    "id": "high_002",
                    "title": "Enhanced Competitive Monitoring",
                    "description": "Implement comprehensive monitoring system to track {competitor_name}'s activities and market moves.",
                    "category": ActionCategory.IMMEDIATE,
                    "priority": ActionPriority.MEDIUM,
                    "timeline": "1-2 weeks",
                    "estimated_hours": 30,
                    "team_members_required": 2,
                    "budget_impact": BudgetImpact.LOW,
                    "dependencies": [
                        "Monitoring tools setup",
                        "Analyst availability",
                        "Data source access"
                    ],
                    "reasoning": [
                        "Enhanced visibility needed for competitor activities",
                        "Early warning system prevents surprises",
                        "Data-driven decision making requires better intelligence"
                    ],
                    "success_criteria": [
                        "Monitoring system operational within 2 weeks",
                        "Daily intelligence reports generated",
                        "Alert thresholds configured"
                    ]
                },
                {
                    "id": "high_003",
                    "title": "Strategic Partnership Acceleration",
                    "description": "Accelerate strategic partnerships to strengthen position against {competitor_name}'s market expansion.",
                    "category": ActionCategory.SHORT_TERM,
                    "priority": ActionPriority.MEDIUM,
                    "timeline": "6-8 weeks",
                    "estimated_hours": 100,
                    "team_members_required": 3,
                    "budget_impact": BudgetImpact.MEDIUM,
                    "dependencies": [
                        "Business development team",
                        "Legal support",
                        "Partner identification",
                        "Executive approval"
                    ],
                    "reasoning": [
                        "Strategic partnerships provide competitive advantage",
                        "Market expansion requires ecosystem support",
                        "Partnership velocity is competitive differentiator"
                    ],
                    "success_criteria": [
                        "2-3 strategic partnerships signed",
                        "Market coverage expanded",
                        "Competitive moat strengthened"
                    ]
                }
            ],
            "medium": [  # Risk score 70-79
                {
                    "id": "medium_001",
                    "title": "Comprehensive Competitive Analysis",
                    "description": "Conduct deep-dive analysis of {competitor_name}'s strategy, strengths, and potential vulnerabilities.",
                    "category": ActionCategory.SHORT_TERM,
                    "priority": ActionPriority.MEDIUM,
                    "timeline": "3-4 weeks",
                    "estimated_hours": 80,
                    "team_members_required": 3,
                    "budget_impact": BudgetImpact.MEDIUM,
                    "dependencies": [
                        "Research resources",
                        "Analyst time",
                        "External data sources",
                        "Stakeholder interviews"
                    ],
                    "reasoning": [
                        "Medium risk requires deeper understanding",
                        "Analysis will inform strategic response options",
                        "Vulnerability identification creates opportunities"
                    ],
                    "success_criteria": [
                        "Comprehensive analysis completed",
                        "Strategic recommendations delivered",
                        "Vulnerability assessment documented"
                    ]
                },
                {
                    "id": "medium_002",
                    "title": "Strategic Response Planning",
                    "description": "Develop multiple strategic response scenarios for potential competitive moves by {competitor_name}.",
                    "category": ActionCategory.STRATEGIC,
                    "priority": ActionPriority.MEDIUM,
                    "timeline": "4-6 weeks",
                    "estimated_hours": 120,
                    "team_members_required": 4,
                    "budget_impact": BudgetImpact.MEDIUM,
                    "dependencies": [
                        "Strategy team availability",
                        "Market research data",
                        "Executive input",
                        "Cross-functional collaboration"
                    ],
                    "reasoning": [
                        "Proactive planning enables rapid response",
                        "Multiple scenarios prepare for uncertainty",
                        "Strategic options should be evaluated in advance"
                    ],
                    "success_criteria": [
                        "3-5 response scenarios developed",
                        "Implementation plans created",
                        "Resource requirements estimated"
                    ]
                },
                {
                    "id": "medium_003",
                    "title": "Market Position Reinforcement",
                    "description": "Strengthen market position and customer relationships to defend against {competitor_name}'s advances.",
                    "category": ActionCategory.STRATEGIC,
                    "priority": ActionPriority.MEDIUM,
                    "timeline": "8-10 weeks",
                    "estimated_hours": 150,
                    "team_members_required": 5,
                    "budget_impact": BudgetImpact.MEDIUM,
                    "dependencies": [
                        "Customer success team",
                        "Marketing resources",
                        "Sales team coordination",
                        "Product enhancement"
                    ],
                    "reasoning": [
                        "Strong customer relationships create switching costs",
                        "Market position defense is proactive strategy",
                        "Customer loyalty is competitive advantage"
                    ],
                    "success_criteria": [
                        "Customer satisfaction scores improved",
                        "Churn rate reduced",
                        "Market share maintained or grown"
                    ]
                }
            ]
        }
    
    def _initialize_impact_area_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize templates specific to impact areas."""
        return {
            "product": {
                "title": "Product Competitive Response to {competitor_name}",
                "description": "Develop product strategy to counter {competitor_name}'s product initiatives and maintain competitive advantage.",
                "category": ActionCategory.SHORT_TERM,
                "priority": ActionPriority.HIGH,
                "timeline": "6-8 weeks",
                "estimated_hours": 160,
                "team_members_required": 4,
                "budget_impact": BudgetImpact.HIGH,
                "dependencies": ["Product team", "Engineering", "Design", "User research"],
                "reasoning": ["Product differentiation is key competitive advantage"]
            },
            "pricing": {
                "title": "Pricing Strategy Adjustment for {competitor_name}",
                "description": "Review and optimize pricing strategy in response to {competitor_name}'s pricing moves.",
                "category": ActionCategory.IMMEDIATE,
                "priority": ActionPriority.HIGH,
                "timeline": "2-3 weeks",
                "estimated_hours": 60,
                "team_members_required": 3,
                "budget_impact": BudgetImpact.MEDIUM,
                "dependencies": ["Pricing team", "Finance", "Sales", "Market research"],
                "reasoning": ["Pricing is immediate competitive lever"]
            },
            "market": {
                "title": "Market Expansion Defense Against {competitor_name}",
                "description": "Strengthen market position and expand presence to counter {competitor_name}'s market expansion.",
                "category": ActionCategory.STRATEGIC,
                "priority": ActionPriority.MEDIUM,
                "timeline": "10-12 weeks",
                "estimated_hours": 200,
                "team_members_required": 6,
                "budget_impact": BudgetImpact.HIGH,
                "dependencies": ["Marketing", "Sales", "Business development", "Operations"],
                "reasoning": ["Market presence creates competitive barriers"]
            },
            "technology": {
                "title": "Technology Innovation Response to {competitor_name}",
                "description": "Accelerate technology development to maintain innovation leadership against {competitor_name}.",
                "category": ActionCategory.STRATEGIC,
                "priority": ActionPriority.HIGH,
                "timeline": "12-16 weeks",
                "estimated_hours": 300,
                "team_members_required": 8,
                "budget_impact": BudgetImpact.HIGH,
                "dependencies": ["Engineering", "Research", "Product", "Architecture"],
                "reasoning": ["Technology leadership is sustainable competitive advantage"]
            },
            "brand": {
                "title": "Brand Positioning Response to {competitor_name}",
                "description": "Strengthen brand positioning and messaging to counter {competitor_name}'s brand initiatives.",
                "category": ActionCategory.SHORT_TERM,
                "priority": ActionPriority.MEDIUM,
                "timeline": "4-6 weeks",
                "estimated_hours": 80,
                "team_members_required": 3,
                "budget_impact": BudgetImpact.MEDIUM,
                "dependencies": ["Marketing", "Brand", "PR", "Creative"],
                "reasoning": ["Brand differentiation influences customer choice"]
            }
        }
    
    def _initialize_timeline_estimates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize timeline estimation rules."""
        return {
            ActionCategory.IMMEDIATE: {
                "min_days": 1,
                "max_days": 14,
                "typical_range": "1-2 weeks"
            },
            ActionCategory.SHORT_TERM: {
                "min_days": 14,
                "max_days": 84,
                "typical_range": "2-12 weeks"
            },
            ActionCategory.STRATEGIC: {
                "min_days": 56,
                "max_days": 168,
                "typical_range": "8-24 weeks"
            }
        }
    
    def get_templates_for_risk_score(self, risk_score: int) -> List[Dict[str, Any]]:
        """Get action templates for a given risk score."""
        if risk_score >= 90:
            return self.templates["critical"]
        elif risk_score >= 80:
            return self.templates["high"]
        elif risk_score >= 70:
            return self.templates["medium"]
        else:
            return []  # No templates for low risk scores
    
    def get_impact_area_template(self, impact_area: str) -> Dict[str, Any]:
        """Get template for specific impact area."""
        area_key = impact_area.lower()
        for key, template in self.impact_area_templates.items():
            if key in area_key:
                return template
        return None
    
    def estimate_timeline(self, category: ActionCategory, complexity_factor: float = 1.0) -> str:
        """Estimate timeline based on category and complexity."""
        timeline_info = self.timeline_estimates.get(category)
        if not timeline_info:
            return "4-6 weeks"
        
        # Adjust timeline based on complexity
        min_days = int(timeline_info["min_days"] * complexity_factor)
        max_days = int(timeline_info["max_days"] * complexity_factor)
        
        # Convert to human-readable format
        if max_days <= 7:
            return f"{min_days}-{max_days} days"
        elif max_days <= 28:
            min_weeks = max(1, min_days // 7)
            max_weeks = max_days // 7
            return f"{min_weeks}-{max_weeks} weeks"
        else:
            min_months = max(1, min_days // 30)
            max_months = max_days // 30
            return f"{min_months}-{max_months} months"
    
    def estimate_resources(
        self, 
        category: ActionCategory, 
        budget_impact: BudgetImpact,
        complexity_factor: float = 1.0
    ) -> Dict[str, Any]:
        """Estimate resource requirements."""
        
        # Base resource estimates
        base_estimates = {
            ActionCategory.IMMEDIATE: {
                BudgetImpact.LOW: {"hours": 20, "team": 2},
                BudgetImpact.MEDIUM: {"hours": 40, "team": 3},
                BudgetImpact.HIGH: {"hours": 80, "team": 5}
            },
            ActionCategory.SHORT_TERM: {
                BudgetImpact.LOW: {"hours": 60, "team": 2},
                BudgetImpact.MEDIUM: {"hours": 120, "team": 4},
                BudgetImpact.HIGH: {"hours": 200, "team": 6}
            },
            ActionCategory.STRATEGIC: {
                BudgetImpact.LOW: {"hours": 100, "team": 3},
                BudgetImpact.MEDIUM: {"hours": 200, "team": 5},
                BudgetImpact.HIGH: {"hours": 400, "team": 8}
            }
        }
        
        base = base_estimates.get(category, {}).get(budget_impact, {"hours": 80, "team": 3})
        
        return {
            "estimated_hours": int(base["hours"] * complexity_factor),
            "team_members_required": int(base["team"] * complexity_factor),
            "budget_impact": budget_impact
        }