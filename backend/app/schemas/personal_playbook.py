"""
Pydantic schemas for personal playbooks and persona presets.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class PersonaPresetBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    category: str = Field(..., description="individual, enterprise, research")
    default_data_slices: Optional[Dict[str, Any]] = None
    export_templates: Optional[Dict[str, Any]] = None
    follow_up_tasks: Optional[List[str]] = None
    key_questions: Optional[List[str]] = None
    priority_sources: Optional[List[str]] = None
    analysis_depth: str = Field(default="medium", description="quick, medium, deep")
    dashboard_layout: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None

class PersonaPresetCreate(PersonaPresetBase):
    pass

class PersonaPreset(PersonaPresetBase):
    id: int
    is_active: bool = True
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserPlaybookBase(BaseModel):
    persona_preset_id: int
    custom_name: Optional[str] = Field(None, max_length=100)
    custom_config: Optional[Dict[str, Any]] = None
    is_favorite: bool = False

class UserPlaybookCreate(UserPlaybookBase):
    user_id: int

class UserPlaybook(UserPlaybookBase):
    id: int
    user_id: int
    last_used: Optional[datetime] = None
    usage_count: int = 0
    current_step: int = 0
    completed_tasks: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    # Related data
    persona_preset: PersonaPreset
    
    class Config:
        from_attributes = True

class PlaybookExecutionBase(BaseModel):
    target_company: Optional[str] = Field(None, max_length=255)
    execution_type: str = Field(..., description="research, monitoring, analysis")
    estimated_duration_minutes: Optional[int] = None

class PlaybookExecutionCreate(PlaybookExecutionBase):
    user_playbook_id: int

class PlaybookExecution(PlaybookExecutionBase):
    id: int
    user_playbook_id: int
    generated_artifacts: Optional[Dict[str, Any]] = None
    completion_status: str = "in_progress"
    completion_percentage: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None
    user_satisfaction_score: Optional[int] = Field(None, ge=1, le=5)
    time_saved_minutes: Optional[int] = None
    execution_notes: Optional[str] = None
    
    class Config:
        from_attributes = True

class PlaybookTemplateBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    category: str = Field(..., description="individual, enterprise, research")
    template_config: Dict[str, Any]
    customization_options: Optional[Dict[str, Any]] = None
    is_public: bool = True

class PlaybookTemplateCreate(PlaybookTemplateBase):
    created_by_user_id: Optional[int] = None

class PlaybookTemplate(PlaybookTemplateBase):
    id: int
    created_by_user_id: Optional[int] = None
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Response models for complex operations

class PlaybookRecommendation(BaseModel):
    """Recommended playbook for a user's current context."""
    persona_preset: PersonaPreset
    match_score: float = Field(..., ge=0.0, le=1.0)
    match_reasons: List[str]
    estimated_time_minutes: int
    key_benefits: List[str]

class PlaybookExecutionPlan(BaseModel):
    """Execution plan for a playbook."""
    playbook: UserPlaybook
    steps: List[Dict[str, Any]]
    estimated_duration: int
    required_inputs: List[str]
    expected_outputs: List[str]
    success_criteria: List[str]

class PlaybookResults(BaseModel):
    """Results from playbook execution."""
    execution: PlaybookExecution
    artifacts: List[Dict[str, Any]]  # Generated reports, cards, etc.
    insights: List[str]
    next_steps: List[str]
    time_saved_estimate: int
    satisfaction_prompt: Optional[str] = None

# Built-in persona presets data

BUILTIN_PERSONAS = {
    "investor_dd": {
        "name": "Investor Due Diligence",
        "description": "Comprehensive company analysis for investment decisions",
        "category": "individual",
        "default_data_slices": {
            "focus_areas": ["funding_history", "market_position", "competitive_landscape", "growth_metrics"],
            "time_horizon": "2_years",
            "risk_assessment": True
        },
        "export_templates": {
            "primary": "investment_memo",
            "formats": ["pdf", "presentation"]
        },
        "follow_up_tasks": [
            "Schedule management team interview",
            "Review financial statements",
            "Analyze customer references",
            "Assess market size and growth",
            "Evaluate competitive positioning"
        ],
        "key_questions": [
            "What is the company's competitive moat?",
            "How sustainable is their growth rate?",
            "What are the key risks to the business model?",
            "Who are the main competitors and how do they compare?",
            "What is the total addressable market?"
        ],
        "priority_sources": ["tier_1", "tier_2", "financial_data"],
        "analysis_depth": "deep"
    },
    "interview_prep": {
        "name": "Interview Preparation",
        "description": "Quick company research for job interview preparation",
        "category": "individual",
        "default_data_slices": {
            "focus_areas": ["company_culture", "recent_news", "leadership", "products", "challenges"],
            "time_horizon": "6_months",
            "risk_assessment": False
        },
        "export_templates": {
            "primary": "interview_notes",
            "formats": ["markdown", "pdf"]
        },
        "follow_up_tasks": [
            "Prepare questions about company culture",
            "Research interviewer backgrounds",
            "Practice discussing relevant experience",
            "Prepare examples of problem-solving",
            "Research salary and benefits"
        ],
        "key_questions": [
            "What are the company's main products and services?",
            "What challenges is the company currently facing?",
            "Who are the key leaders and what are their backgrounds?",
            "What is the company culture like?",
            "What recent developments should I know about?"
        ],
        "priority_sources": ["company_website", "news", "employee_reviews"],
        "analysis_depth": "quick"
    },
    "founder_pitch": {
        "name": "Founder Pitch Research",
        "description": "Market and competitive analysis for startup pitches",
        "category": "individual",
        "default_data_slices": {
            "focus_areas": ["market_size", "competitors", "trends", "opportunities", "threats"],
            "time_horizon": "5_years",
            "risk_assessment": True
        },
        "export_templates": {
            "primary": "pitch_deck_research",
            "formats": ["presentation", "pdf"]
        },
        "follow_up_tasks": [
            "Quantify total addressable market",
            "Map competitive landscape",
            "Identify market trends and drivers",
            "Assess regulatory environment",
            "Validate customer pain points"
        ],
        "key_questions": [
            "How large is the total addressable market?",
            "Who are the main competitors and how do we differentiate?",
            "What market trends support our thesis?",
            "What are the key barriers to entry?",
            "What regulatory considerations exist?"
        ],
        "priority_sources": ["market_research", "tier_1", "tier_2"],
        "analysis_depth": "deep"
    },
    "competitive_monitoring": {
        "name": "Competitive Monitoring",
        "description": "Ongoing competitive intelligence for product teams",
        "category": "enterprise",
        "default_data_slices": {
            "focus_areas": ["product_launches", "pricing", "partnerships", "funding", "hiring"],
            "time_horizon": "ongoing",
            "risk_assessment": True
        },
        "export_templates": {
            "primary": "competitive_brief",
            "formats": ["email", "slack", "pdf"]
        },
        "follow_up_tasks": [
            "Analyze competitive feature gaps",
            "Update competitive positioning",
            "Brief product team on threats",
            "Update pricing strategy",
            "Monitor hiring patterns"
        ],
        "key_questions": [
            "What new features have competitors launched?",
            "How has competitive pricing changed?",
            "What partnerships are competitors forming?",
            "What talent are competitors hiring?",
            "What funding activities indicate strategic shifts?"
        ],
        "priority_sources": ["news", "product_updates", "job_postings"],
        "analysis_depth": "medium"
    }
}