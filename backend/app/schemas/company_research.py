from pydantic import BaseModel, Field, field_validator
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
    status: str = "completed"
    summary: Optional[str] = None
    confidence_score: int = 85
    total_sources: int
    api_usage: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class CompanyResearchRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=100, description="Company name to research")

    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        """Validate and sanitize company name"""
        if not v or not v.strip():
            raise ValueError('Company name cannot be empty')
        # Strip whitespace and limit length
        sanitized = v.strip()[:100]
        if len(sanitized) < 2:
            raise ValueError('Company name must be at least 2 characters')
        return sanitized