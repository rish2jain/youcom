"""
Pydantic schemas for action tracking and task management.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class ActionStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class ActionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ActionItemBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    status: ActionStatus = ActionStatus.PLANNED
    priority: ActionPriority = ActionPriority.MEDIUM
    assigned_to: Optional[str] = Field(None, max_length=255)
    owner_type: str = Field(default="individual", description="individual, team, role")
    due_date: Optional[datetime] = None
    progress_percentage: int = Field(default=0, ge=0, le=100)
    estimated_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    source_insight: Optional[str] = None
    evidence_links: Optional[List[str]] = None
    success_criteria: Optional[List[str]] = None
    notes: Optional[str] = None

class ActionItemCreate(ActionItemBase):
    impact_card_id: int

class ActionItemUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    status: Optional[ActionStatus] = None
    priority: Optional[ActionPriority] = None
    assigned_to: Optional[str] = Field(None, max_length=255)
    due_date: Optional[datetime] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    estimated_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None

class ActionItem(ActionItemBase):
    id: int
    impact_card_id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    status_updates: Optional[List[Dict[str, Any]]] = None
    ai_generated: bool = True
    user_modified: bool = False
    
    # Computed properties
    is_overdue: bool = Field(..., description="Whether the action is overdue")
    days_until_due: Optional[int] = Field(None, description="Days until due date")
    
    class Config:
        from_attributes = True

class ActionReminderBase(BaseModel):
    reminder_type: str = Field(..., description="email, calendar, notification")
    reminder_time: datetime
    message: Optional[str] = None
    recurring: bool = False
    recurrence_pattern: Optional[str] = Field(None, description="daily, weekly, monthly")

class ActionReminderCreate(ActionReminderBase):
    action_item_id: int

class ActionReminder(ActionReminderBase):
    id: int
    action_item_id: int
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ActionBoardBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    board_type: str = Field(default="personal", description="personal, team, project")
    columns: List[Dict[str, Any]] = Field(..., description="Column definitions")
    filters: Optional[Dict[str, Any]] = None
    sort_order: Optional[Dict[str, Any]] = None
    is_shared: bool = False
    shared_with: Optional[List[str]] = None

class ActionBoardCreate(ActionBoardBase):
    user_id: int

class ActionBoard(ActionBoardBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    last_accessed: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ActionBoardItemBase(BaseModel):
    column_id: str = Field(..., max_length=100)
    position: int = Field(default=0, ge=0)
    custom_title: Optional[str] = Field(None, max_length=500)
    custom_color: Optional[str] = Field(None, max_length=20)
    tags: Optional[List[str]] = None

class ActionBoardItemCreate(ActionBoardItemBase):
    board_id: int
    action_item_id: int

class ActionBoardItem(ActionBoardItemBase):
    id: int
    board_id: int
    action_item_id: int
    added_at: datetime
    moved_at: Optional[datetime] = None
    
    # Related data
    action_item: ActionItem
    
    class Config:
        from_attributes = True

class ActionTemplateBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    category: str = Field(..., max_length=100)
    template_actions: List[Dict[str, Any]] = Field(..., description="Action templates")
    default_assignments: Optional[Dict[str, Any]] = None
    estimated_timeline: Optional[Dict[str, Any]] = None
    is_public: bool = True

class ActionTemplateCreate(ActionTemplateBase):
    created_by_user_id: Optional[int] = None

class ActionTemplate(ActionTemplateBase):
    id: int
    created_by_user_id: Optional[int] = None
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Response models for complex operations

class ActionSummary(BaseModel):
    """Summary of actions for an Impact Card."""
    total_actions: int
    by_status: Dict[ActionStatus, int]
    by_priority: Dict[ActionPriority, int]
    overdue_count: int
    completed_this_week: int
    estimated_total_hours: int
    actual_total_hours: int

class ActionBoardView(BaseModel):
    """Complete board view with items."""
    board: ActionBoard
    items_by_column: Dict[str, List[ActionBoardItem]]
    summary: ActionSummary

class ActionInsights(BaseModel):
    """Insights and analytics for actions."""
    completion_rate: float = Field(..., ge=0.0, le=1.0)
    average_completion_time_days: Optional[float] = None
    most_common_categories: List[Dict[str, Any]]
    productivity_trends: List[Dict[str, Any]]
    recommendations: List[str]

# Built-in action templates

BUILTIN_ACTION_TEMPLATES = {
    "competitive_response": {
        "name": "Competitive Response",
        "description": "Standard response to competitive threats",
        "category": "competitive_intelligence",
        "template_actions": [
            {
                "title": "Analyze competitive threat",
                "description": "Deep dive into competitor's new capability or announcement",
                "category": "research",
                "priority": "high",
                "estimated_hours": 4,
                "success_criteria": ["Threat level assessed", "Impact on our position quantified"]
            },
            {
                "title": "Brief leadership team",
                "description": "Present findings and recommendations to leadership",
                "category": "communication",
                "priority": "high",
                "estimated_hours": 2,
                "success_criteria": ["Leadership briefed", "Strategic direction confirmed"]
            },
            {
                "title": "Update competitive positioning",
                "description": "Revise positioning and messaging based on new competitive landscape",
                "category": "strategy",
                "priority": "medium",
                "estimated_hours": 6,
                "success_criteria": ["Positioning updated", "Sales team briefed"]
            },
            {
                "title": "Monitor competitor response",
                "description": "Set up ongoing monitoring for competitor's next moves",
                "category": "monitoring",
                "priority": "medium",
                "estimated_hours": 1,
                "success_criteria": ["Monitoring alerts configured", "Review schedule set"]
            }
        ],
        "default_assignments": {
            "research": "analyst",
            "communication": "product_manager",
            "strategy": "strategy_team",
            "monitoring": "analyst"
        },
        "estimated_timeline": {
            "total_days": 14,
            "critical_path": ["analyze", "brief", "update", "monitor"]
        }
    },
    "product_launch_response": {
        "name": "Product Launch Response",
        "description": "Response to competitor product launches",
        "category": "product_strategy",
        "template_actions": [
            {
                "title": "Feature gap analysis",
                "description": "Compare new competitor features with our roadmap",
                "category": "product",
                "priority": "urgent",
                "estimated_hours": 8,
                "success_criteria": ["Gap analysis completed", "Roadmap impact assessed"]
            },
            {
                "title": "Customer impact assessment",
                "description": "Evaluate potential customer churn risk",
                "category": "customer_success",
                "priority": "high",
                "estimated_hours": 4,
                "success_criteria": ["At-risk customers identified", "Retention plan created"]
            },
            {
                "title": "Accelerate roadmap items",
                "description": "Fast-track competing features in our roadmap",
                "category": "product",
                "priority": "high",
                "estimated_hours": 16,
                "success_criteria": ["Priority features identified", "Timeline accelerated"]
            },
            {
                "title": "Update sales battlecards",
                "description": "Refresh competitive battlecards with new information",
                "category": "sales_enablement",
                "priority": "medium",
                "estimated_hours": 3,
                "success_criteria": ["Battlecards updated", "Sales team trained"]
            }
        ]
    },
    "market_research": {
        "name": "Market Research",
        "description": "Comprehensive market analysis workflow",
        "category": "research",
        "template_actions": [
            {
                "title": "Define research scope",
                "description": "Clarify research questions and success criteria",
                "category": "planning",
                "priority": "high",
                "estimated_hours": 2,
                "success_criteria": ["Research questions defined", "Success metrics set"]
            },
            {
                "title": "Gather primary data",
                "description": "Collect data from surveys, interviews, and observations",
                "category": "research",
                "priority": "high",
                "estimated_hours": 12,
                "success_criteria": ["Primary data collected", "Sample size targets met"]
            },
            {
                "title": "Analyze secondary sources",
                "description": "Review industry reports, competitor analysis, and market data",
                "category": "research",
                "priority": "medium",
                "estimated_hours": 8,
                "success_criteria": ["Secondary sources analyzed", "Key insights extracted"]
            },
            {
                "title": "Synthesize findings",
                "description": "Combine all research into actionable insights",
                "category": "analysis",
                "priority": "high",
                "estimated_hours": 6,
                "success_criteria": ["Findings synthesized", "Recommendations developed"]
            },
            {
                "title": "Present results",
                "description": "Create presentation and share with stakeholders",
                "category": "communication",
                "priority": "medium",
                "estimated_hours": 4,
                "success_criteria": ["Presentation delivered", "Stakeholder feedback collected"]
            }
        ]
    }
}