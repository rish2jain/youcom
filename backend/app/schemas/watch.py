from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class WatchItemBase(BaseModel):
    competitor_name: str = Field(..., min_length=1, max_length=255)
    keywords: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    check_frequency: int = Field(default=120, ge=60)  # Minimum 1 minute
    risk_threshold: int = Field(default=70, ge=0, le=100)

class WatchItemCreate(WatchItemBase):
    pass

class WatchItemUpdate(BaseModel):
    competitor_name: Optional[str] = Field(None, min_length=1, max_length=255)
    keywords: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    check_frequency: Optional[int] = Field(None, ge=60)
    risk_threshold: Optional[int] = Field(None, ge=0, le=100)

class WatchItem(WatchItemBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    last_checked: Optional[datetime]

    class Config:
        from_attributes = True

class WatchItemList(BaseModel):
    items: List[WatchItem]
    total: int