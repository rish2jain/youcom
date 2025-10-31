from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.database import Base

class CompanyResearch(Base):
    __tablename__ = "company_research"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    
    # Research data
    search_results = Column(JSON, default=dict)  # You.com Search API results
    research_report = Column(JSON, default=dict)  # You.com ARI results

    # Status and metadata
    status = Column(String(50), default="completed", nullable=False)  # completed, processing, failed
    summary = Column(Text, nullable=True)  # Brief summary of research
    confidence_score = Column(Integer, default=85)  # Confidence percentage

    # Metrics
    total_sources = Column(Integer, default=0)
    api_usage = Column(JSON, default=dict)  # Track You.com API calls
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CompanyResearch(id={self.id}, company='{self.company_name}')>"