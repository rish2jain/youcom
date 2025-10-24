"""Pydantic schemas for workspace management"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.workspace import WorkspaceRole


class WorkspaceBase(BaseModel):
    """Base workspace schema"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    max_members: int = Field(default=10, ge=1, le=1000)
    allow_guest_access: bool = False


class WorkspaceCreate(WorkspaceBase):
    """Create workspace schema"""
    slug: str = Field(..., min_length=3, max_length=50)

    @validator('slug')
    def slug_valid(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must be alphanumeric (hyphens and underscores allowed)')
        return v.lower()


class WorkspaceUpdate(BaseModel):
    """Update workspace schema"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    max_members: Optional[int] = Field(None, ge=1, le=1000)
    allow_guest_access: Optional[bool] = None
    is_active: Optional[bool] = None


class WorkspaceResponse(WorkspaceBase):
    """Workspace response schema"""
    id: int
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    member_count: Optional[int] = 0

    class Config:
        from_attributes = True


# Workspace Member schemas
class WorkspaceMemberBase(BaseModel):
    """Base workspace member schema"""
    user_id: int
    role: WorkspaceRole


class WorkspaceMemberInvite(BaseModel):
    """Invite member to workspace"""
    user_id: int
    role: WorkspaceRole = WorkspaceRole.MEMBER


class WorkspaceMemberUpdate(BaseModel):
    """Update workspace member"""
    role: WorkspaceRole


class WorkspaceMemberResponse(BaseModel):
    """Workspace member response"""
    id: int
    workspace_id: int
    user_id: int
    role: WorkspaceRole
    joined_at: datetime
    user_email: Optional[str] = None
    user_username: Optional[str] = None
    user_full_name: Optional[str] = None

    class Config:
        from_attributes = True
