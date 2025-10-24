from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text
from sqlalchemy.sql import func
from app.database import Base

class WatchItem(Base):
    __tablename__ = "watch_items"

    id = Column(Integer, primary_key=True, index=True)
    competitor_name = Column(String(255), nullable=False, index=True)
    keywords = Column(JSON, default=list)  # List of keywords to monitor
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_checked = Column(DateTime(timezone=True), nullable=True)
    
    # Monitoring configuration
    check_frequency = Column(Integer, default=120)  # Check every 2 minutes
    risk_threshold = Column(Integer, default=70)  # Alert threshold
    
    def __repr__(self):
        return f"<WatchItem(id={self.id}, competitor='{self.competitor_name}', active={self.is_active})>"