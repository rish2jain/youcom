"""
Personal Playbook models for persona-driven presets and workflows.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, CheckConstraint
from sqlalchemy.orm import relationship

from .base import Base

class PersonaPreset(Base):
    """Predefined persona configurations for different user types."""
    __tablename__ = "persona_presets"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Persona details
    name = Column(String(100), nullable=False, unique=True)  # "Investor DD", "Interview Prep", etc.
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # "individual", "enterprise", "research"
    
    # Configuration
    default_data_slices = Column(JSON, nullable=True)  # Which data to focus on
    export_templates = Column(JSON, nullable=True)    # Export format preferences
    follow_up_tasks = Column(JSON, nullable=True)     # Suggested next steps
    
    # Research focus
    key_questions = Column(JSON, nullable=True)       # Questions this persona typically asks
    priority_sources = Column(JSON, nullable=True)   # Preferred source types
    analysis_depth = Column(String(20), default="medium")  # "quick", "medium", "deep"
    
    # UI preferences
    dashboard_layout = Column(JSON, nullable=True)    # Preferred dashboard configuration
    notification_preferences = Column(JSON, nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user_playbooks = relationship("UserPlaybook", back_populates="persona_preset")

class UserPlaybook(Base):
    """User's personalized playbook based on a persona preset."""
    __tablename__ = "user_playbooks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    persona_preset_id = Column(Integer, ForeignKey("persona_presets.id"), nullable=False)
    
    # Customization
    custom_name = Column(String(100), nullable=True)  # User's custom name for this playbook
    custom_config = Column(JSON, nullable=True)       # User's modifications to preset
    
    # Usage tracking
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    is_favorite = Column(Boolean, default=False)
    
    # Workflow state
    current_step = Column(Integer, default=0)         # Current step in workflow
    completed_tasks = Column(JSON, nullable=True)     # Completed follow-up tasks
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    persona_preset = relationship("PersonaPreset", back_populates="user_playbooks")
    # user = relationship("User", back_populates="playbooks")  # Uncomment when User model exists

class PlaybookExecution(Base):
    """Track execution of playbook workflows."""
    __tablename__ = "playbook_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_playbook_id = Column(Integer, ForeignKey("user_playbooks.id"), nullable=False)
    
    # Execution details
    target_company = Column(String(255), nullable=True)  # Company being researched
    execution_type = Column(String(50), nullable=False)  # "research", "monitoring", "analysis"
    
    # Results
    generated_artifacts = Column(JSON, nullable=True)    # IDs of generated reports, cards, etc.
    completion_status = Column(String(20), default="in_progress", nullable=False)  # "in_progress", "completed", "failed"
    completion_percentage = Column(Integer, default=0, nullable=False)
    
    # Add constraints
    __table_args__ = (
        CheckConstraint("completion_status IN ('in_progress', 'completed', 'failed')", name='check_completion_status'),
        CheckConstraint("completion_percentage >= 0 AND completion_percentage <= 100", name='check_completion_percentage'),
    )
    
    # Timing
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    
    # Quality metrics
    user_satisfaction_score = Column(Integer, nullable=True)  # 1-5 rating
    time_saved_minutes = Column(Integer, nullable=True)
    
    # Metadata
    execution_notes = Column(Text, nullable=True)
    
    # Relationships
    user_playbook = relationship("UserPlaybook", backref="executions")

class PlaybookTemplate(Base):
    """Templates for creating new persona presets."""
    __tablename__ = "playbook_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    
    # Template configuration
    template_config = Column(JSON, nullable=False)    # Base configuration
    customization_options = Column(JSON, nullable=True)  # Available customizations
    
    # Usage
    is_public = Column(Boolean, default=True)
    created_by_user_id = Column(Integer, nullable=True)  # If user-created
    usage_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)