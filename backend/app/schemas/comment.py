"""Comment schemas for threaded discussions"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class CommentCreate(BaseModel):
    """Schema for creating new comments"""
    content: str = Field(..., min_length=1, max_length=2000, description="Comment content")
    parent_comment_id: Optional[int] = Field(None, description="Parent comment ID for threading")
    annotations: Optional[Dict[str, Any]] = Field(None, description="Annotation data for highlighting")


class CommentUpdate(BaseModel):
    """Schema for updating comments"""
    content: Optional[str] = Field(None, min_length=1, max_length=2000, description="Updated content")
    annotations: Optional[Dict[str, Any]] = Field(None, description="Updated annotation data")


class CommentResponse(BaseModel):
    """Schema for comment responses"""
    id: int
    user_id: int
    shared_watchlist_id: Optional[int] = None
    impact_card_id: Optional[int] = None
    company_research_id: Optional[int] = None
    content: str
    annotations: Optional[Dict[str, Any]] = None
    parent_comment_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_edited: int

    class Config:
        from_attributes = True


class CommentWithUser(CommentResponse):
    """Comment response with user information"""
    user_name: str
    user_email: str
    replies_count: int = 0


class CommentThread(CommentWithUser):
    """Comment with nested replies"""
    replies: List['CommentThread'] = []


class CommentStats(BaseModel):
    """Statistics for comments"""
    total_comments: int
    total_threads: int  # Top-level comments
    total_replies: int
    by_user: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


class BulkCommentOperation(BaseModel):
    """Schema for bulk comment operations"""
    comment_ids: List[int] = Field(..., min_items=1, description="List of comment IDs")
    operation: str = Field(..., pattern="^(delete|hide|unhide)$", description="Operation to perform")


class CommentNotification(BaseModel):
    """Schema for comment notifications"""
    id: int
    recipient_id: int
    comment_id: int
    notification_type: str  # mention, reply, new_comment
    is_read: bool
    created_at: datetime
    comment_content: str
    author_name: str
    context_type: str  # impact_card, shared_watchlist, company_research
    context_id: int

    class Config:
        from_attributes = True


class MentionUser(BaseModel):
    """Schema for user mentions in comments"""
    user_id: int
    username: str
    display_name: str


class CommentMentions(BaseModel):
    """Schema for handling mentions in comments"""
    mentioned_users: List[MentionUser] = []
    content_with_mentions: str


# Update CommentThread to handle self-reference
CommentThread.model_rebuild()