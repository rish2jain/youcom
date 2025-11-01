"""Annotation schemas for API requests and responses"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AnnotationPosition(BaseModel):
    """Position data for annotation placement"""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    width: Optional[float] = Field(None, description="Width of highlighted area")
    height: Optional[float] = Field(None, description="Height of highlighted area")


class AnnotationCreate(BaseModel):
    """Schema for creating new annotations"""
    content: str = Field(..., min_length=1, max_length=2000, description="Annotation content")
    annotation_type: str = Field(..., pattern="^(insight|question|concern|action)$", description="Type of annotation")
    position: Optional[AnnotationPosition] = Field(None, description="Position data for UI")
    target_element: Optional[str] = Field(None, max_length=255, description="CSS selector or element ID")
    target_text: Optional[str] = Field(None, max_length=1000, description="Selected text for highlighting")


class AnnotationUpdate(BaseModel):
    """Schema for updating annotations"""
    content: Optional[str] = Field(None, min_length=1, max_length=2000, description="Updated content")
    annotation_type: Optional[str] = Field(None, pattern="^(insight|question|concern|action)$", description="Updated type")
    position: Optional[AnnotationPosition] = Field(None, description="Updated position")
    target_element: Optional[str] = Field(None, max_length=255, description="Updated target element")
    target_text: Optional[str] = Field(None, max_length=1000, description="Updated target text")
    is_resolved: Optional[int] = Field(None, ge=0, le=1, description="Resolution status")


class AnnotationResponse(BaseModel):
    """Schema for annotation responses"""
    id: int
    user_id: int
    impact_card_id: int
    content: str
    annotation_type: str
    position: Optional[Dict[str, Any]] = None
    target_element: Optional[str] = None
    target_text: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_resolved: int
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnnotationWithUser(AnnotationResponse):
    """Annotation response with user information"""
    user_name: str
    user_email: str
    resolver_name: Optional[str] = None


class AnnotationStats(BaseModel):
    """Statistics for annotations"""
    total_annotations: int
    by_type: Dict[str, int]
    resolved_count: int
    pending_count: int
    by_user: Dict[str, int]


class BulkAnnotationOperation(BaseModel):
    """Schema for bulk annotation operations"""
    annotation_ids: list[int] = Field(..., min_length=1, description="List of annotation IDs")
    operation: str = Field(..., pattern="^(resolve|unresolve|delete)$", description="Operation to perform")
    resolved_by: Optional[int] = Field(None, description="User ID resolving annotations")