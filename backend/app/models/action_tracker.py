"""
Action Tracker models for lightweight task management on Impact Cards.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, Enum, func
from sqlalchemy.orm import relationship
import enum

from .base import Base

class ActionStatus(enum.Enum):
    """Action status enumeration."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class ActionPriority(enum.Enum):
    """Action priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ActionItem(Base):
    """Individual action items for Impact Cards."""
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    impact_card_id = Column(Integer, ForeignKey("impact_cards.id"), nullable=False)
    
    # Action details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # "research", "strategy", "product", "marketing"
    
    # Status and priority
    status = Column(Enum(ActionStatus), default=ActionStatus.PLANNED, nullable=False)
    priority = Column(Enum(ActionPriority), default=ActionPriority.MEDIUM, nullable=False)
    
    # Assignment and ownership
    assigned_to = Column(String(255), nullable=True)  # Email or user identifier
    owner_type = Column(String(50), default="individual")  # "individual", "team", "role"
    
    # Timing
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)  # 0-100
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    
    # Context and evidence
    source_insight = Column(Text, nullable=True)  # Which insight generated this action
    evidence_links = Column(JSON, nullable=True)  # Links to supporting evidence
    success_criteria = Column(JSON, nullable=True)  # How to measure success
    
    # Notes and updates
    notes = Column(Text, nullable=True)
    status_updates = Column(JSON, nullable=True)  # History of status changes
    
    # Metadata
    ai_generated = Column(Boolean, default=True)  # Whether this was AI-generated
    user_modified = Column(Boolean, default=False)  # Whether user has modified it
    
    # Relationships
    impact_card = relationship("ImpactCard", back_populates="action_items")
    reminders = relationship("ActionReminder", back_populates="action_item", cascade="all, delete-orphan")
    
    @property
    def is_overdue(self) -> bool:
        """Check if action is overdue."""
        if not self.due_date or self.status in [ActionStatus.DONE, ActionStatus.CANCELLED]:
            return False
        return datetime.now(timezone.utc) > self.due_date
    
    @property
    def days_until_due(self) -> Optional[int]:
        """Calculate days until due date."""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.now(timezone.utc)
        return delta.days

class ActionReminder(Base):
    """Reminders for action items."""
    __tablename__ = "action_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    action_item_id = Column(Integer, ForeignKey("action_items.id"), nullable=False)
    
    # Reminder details
    reminder_type = Column(String(50), nullable=False)  # "email", "calendar", "notification"
    reminder_time = Column(DateTime, nullable=False)
    message = Column(Text, nullable=True)
    
    # Status
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Configuration
    recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(100), nullable=True)  # "daily", "weekly", "monthly"
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    action_item = relationship("ActionItem", back_populates="reminders")

class ActionBoard(Base):
    """Kanban-style board for organizing actions."""
    __tablename__ = "action_boards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Owner of the board
    
    # Board details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    board_type = Column(String(50), default="personal")  # "personal", "team", "project"
    
    # Configuration
    columns = Column(JSON, nullable=False)  # Column definitions
    filters = Column(JSON, nullable=True)   # Default filters
    sort_order = Column(JSON, nullable=True)  # Default sort order
    
    # Sharing and permissions
    is_shared = Column(Boolean, default=False)
    shared_with = Column(JSON, nullable=True)  # List of user IDs or emails
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    board_items = relationship("ActionBoardItem", back_populates="board", cascade="all, delete-orphan")

class ActionBoardItem(Base):
    """Items on an action board (references to action items)."""
    __tablename__ = "action_board_items"
    
    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("action_boards.id"), nullable=False)
    action_item_id = Column(Integer, ForeignKey("action_items.id"), nullable=False)
    
    # Board-specific properties
    column_id = Column(String(100), nullable=False)  # Which column this item is in
    position = Column(Integer, default=0)  # Position within column
    
    # Display customization
    custom_title = Column(String(500), nullable=True)  # Override title for this board
    custom_color = Column(String(20), nullable=True)   # Custom color
    tags = Column(JSON, nullable=True)  # Board-specific tags
    
    # Metadata
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    moved_at = Column(DateTime(timezone=True), nullable=True)  # Last time moved between columns
    
    # Relationships
    board = relationship("ActionBoard", back_populates="board_items")
    action_item = relationship("ActionItem", backref="board_items")

class ActionTemplate(Base):
    """Templates for common action patterns."""
    __tablename__ = "action_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Template details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    
    # Template configuration
    template_actions = Column(JSON, nullable=False)  # List of action templates
    default_assignments = Column(JSON, nullable=True)  # Default ownership patterns
    estimated_timeline = Column(JSON, nullable=True)  # Timeline estimates
    
    # Usage and sharing
    is_public = Column(Boolean, default=True)
    created_by_user_id = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)