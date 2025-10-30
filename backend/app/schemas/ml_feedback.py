from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class FeedbackType(str, Enum):
    """Enumeration of feedback types."""
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    SEVERITY = "severity"
    CATEGORY = "category"

class ExpertiseLevel(str, Enum):
    """User expertise levels for feedback weighting."""
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"
    UNKNOWN = "unknown"

class FeedbackCreate(BaseModel):
    """Schema for creating new feedback records."""
    impact_card_id: int = Field(..., description="ID of the impact card being reviewed")
    feedback_type: FeedbackType = Field(..., description="Type of feedback being provided")
    original_value: Optional[float] = Field(None, description="Original ML prediction value")
    corrected_value: Optional[float] = Field(None, description="User-corrected value")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="User confidence in feedback (0.0-1.0)")
    feedback_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional feedback context")
    user_expertise_level: ExpertiseLevel = Field(ExpertiseLevel.UNKNOWN, description="User's expertise level")

    @validator('corrected_value')
    def validate_corrected_value(cls, v, values):
        """Ensure corrected_value is provided when original_value exists."""
        if 'original_value' in values and values['original_value'] is not None and v is None:
            raise ValueError("corrected_value is required when original_value is provided")
        return v

    @validator('feedback_context')
    def validate_feedback_context(cls, v):
        """Ensure feedback_context is a valid dictionary."""
        if v is None:
            return {}
        return v

class FeedbackResponse(BaseModel):
    """Schema for feedback record responses."""
    id: int
    user_id: str
    impact_card_id: int
    feedback_type: FeedbackType
    original_value: Optional[float]
    corrected_value: Optional[float]
    confidence: float
    feedback_context: Dict[str, Any]
    user_expertise_level: ExpertiseLevel
    feedback_timestamp: datetime
    processed: bool
    processed_at: Optional[datetime]

    class Config:
        orm_mode = True

class FeedbackBatch(BaseModel):
    """Schema for batch feedback submission."""
    feedback_items: List[FeedbackCreate] = Field(..., description="List of feedback items to submit")

    @validator('feedback_items')
    def validate_feedback_items(cls, v):
        """Ensure at least one feedback item is provided."""
        if not v:
            raise ValueError("At least one feedback item is required")
        if len(v) > 50:  # Reasonable batch size limit
            raise ValueError("Maximum 50 feedback items allowed per batch")
        return v

class FeedbackStats(BaseModel):
    """Schema for feedback statistics."""
    total_feedback_count: int
    feedback_by_type: Dict[str, int]
    feedback_by_expertise: Dict[str, int]
    processed_count: int
    pending_count: int
    average_confidence: float

class OneClickFeedback(BaseModel):
    """Schema for simplified one-click feedback mechanisms."""
    impact_card_id: int = Field(..., description="ID of the impact card")
    feedback_action: str = Field(..., description="One-click action taken")
    
    @validator('feedback_action')
    def validate_feedback_action(cls, v):
        """Validate one-click feedback actions."""
        valid_actions = [
            'thumbs_up', 'thumbs_down',
            'too_high', 'too_low', 'just_right',
            'relevant', 'not_relevant',
            'correct_category', 'wrong_category'
        ]
        if v not in valid_actions:
            raise ValueError(f"Invalid feedback action. Must be one of: {valid_actions}")
        return v

class FeedbackFilter(BaseModel):
    """Schema for filtering feedback records."""
    feedback_type: Optional[FeedbackType] = None
    processed: Optional[bool] = None
    user_expertise_level: Optional[ExpertiseLevel] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    impact_card_id: Optional[int] = None
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Ensure end_date is after start_date."""
        if v and 'start_date' in values and values['start_date'] and v < values['start_date']:
            raise ValueError("end_date must be after start_date")
        return v