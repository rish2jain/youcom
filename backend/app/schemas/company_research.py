from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class CompanyResearchBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)

class CompanyResearchCreate(CompanyResearchBase):
    search_results: Dict[str, Any] = Field(default_factory=dict)
    research_report: Dict[str, Any] = Field(default_factory=dict)
    total_sources: int = 0
    api_usage: Dict[str, Any] = Field(default_factory=dict)

class CompanyResearch(CompanyResearchBase):
    id: int
    search_results: Dict[str, Any]
    research_report: Dict[str, Any]
    total_sources: int
    api_usage: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class CompanyResearchRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)