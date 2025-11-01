"""Shared watchlist schemas for collaborative monitoring"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SharedWatchlistCreate(BaseModel):
    """Schema for creating shared watchlists"""
    name: str = Field(..., min_length=1, max_length=255, description="Watchlist name")
    description: Optional[str] = Field(None, max_length=1000, description="Watchlist description")
    watch_item_id: int = Field(..., description="ID of the watch item to share")
    is_public: bool = Field(False, description="Whether watchlist is public within workspace")


class SharedWatchlistUpdate(BaseModel):
    """Schema for updating shared watchlists"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated name")
    description: Optional[str] = Field(None, max_length=1000, description="Updated description")
    is_public: Optional[bool] = Field(None, description="Updated public status")
    is_active: Optional[bool] = Field(None, description="Updated active status")


class SharedWatchlistResponse(BaseModel):
    """Schema for shared watchlist responses"""
    id: int
    workspace_id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    watch_item_id: int
    created_by: int
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SharedWatchlistWithDetails(SharedWatchlistResponse):
    """Shared watchlist with additional details"""
    creator_name: str
    creator_email: str
    watch_item_name: str
    watch_item_query: str
    assigned_users_count: int
    comments_count: int


class WatchlistAssignment(BaseModel):
    """Schema for watchlist user assignments"""
    user_ids: List[int] = Field(..., min_items=1, description="List of user IDs to assign")


class WatchlistAssignmentResponse(BaseModel):
    """Response for watchlist assignments"""
    shared_watchlist_id: int
    user_id: int
    assigned_at: datetime

    class Config:
        from_attributes = True


class SharedWatchlistStats(BaseModel):
    """Statistics for shared watchlists"""
    total_watchlists: int
    active_watchlists: int
    public_watchlists: int
    private_watchlists: int
    by_creator: dict[str, int]
    assignment_stats: dict[str, int]


class WatchlistPermissionCheck(BaseModel):
    """Schema for checking watchlist permissions"""
    can_view: bool
    can_edit: bool
    can_delete: bool
    can_assign_users: bool
    is_creator: bool
    workspace_role: str


class BulkWatchlistOperation(BaseModel):
    """Schema for bulk watchlist operations"""
    watchlist_ids: List[int] = Field(..., min_items=1, description="List of watchlist IDs")
    operation: str = Field(..., pattern="^(activate|deactivate|delete|make_public|make_private)$", description="Operation to perform")


class WatchlistActivityLog(BaseModel):
    """Schema for watchlist activity logging"""
    id: int
    shared_watchlist_id: int
    user_id: int
    action: str
    details: Optional[dict] = None
    timestamp: datetime
    user_name: str

    class Config:
        from_attributes = True