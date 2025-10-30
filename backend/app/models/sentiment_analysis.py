"""Sentiment Analysis models for the Advanced Intelligence Suite."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class SentimentAnalysis(Base):
    """Model for storing sentiment analysis results."""
    
    __tablename__ = "sentiment_analyses"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String, nullable=False, index=True)
    content_type = Column(String, nullable=False)  # news, social, report
    entity_name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)  # company, product, market
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    sentiment_label = Column(String, nullable=False)  # positive, negative, neutral
    confidence = Column(Float, nullable=False)
    processing_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    source_url = Column(String)
    content_text = Column(Text)
    analysis_metadata = Column(JSON)
    
    # Relationships
    trends = relationship("SentimentTrend", back_populates="sentiment_analysis")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_sentiment_entity_time', 'entity_name', 'processing_timestamp'),
        Index('idx_sentiment_content_type', 'content_type', 'processing_timestamp'),
        Index('idx_sentiment_score_confidence', 'sentiment_score', 'confidence'),
    )


class SentimentTrend(Base):
    """Model for storing aggregated sentiment trends over time."""
    
    __tablename__ = "sentiment_trends"

    id = Column(Integer, primary_key=True, index=True)
    entity_name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)  # daily, weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    average_sentiment = Column(Float, nullable=False)
    sentiment_volatility = Column(Float, nullable=False)
    total_mentions = Column(Integer, nullable=False)
    positive_mentions = Column(Integer, default=0)
    negative_mentions = Column(Integer, default=0)
    neutral_mentions = Column(Integer, default=0)
    trend_direction = Column(String)  # improving, declining, stable
    trend_strength = Column(Float)  # 0.0 to 1.0
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign key to link back to individual analyses (optional)
    sentiment_analysis_id = Column(Integer, ForeignKey("sentiment_analyses.id"))
    sentiment_analysis = relationship("SentimentAnalysis", back_populates="trends")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_trend_entity_timeframe', 'entity_name', 'timeframe', 'period_start'),
        Index('idx_trend_period', 'period_start', 'period_end'),
        Index('idx_trend_direction', 'trend_direction', 'trend_strength'),
    )


class SentimentAlert(Base):
    """Model for storing sentiment alerts and notifications."""
    
    __tablename__ = "sentiment_alerts"

    id = Column(Integer, primary_key=True, index=True)
    entity_name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # shift, threshold, anomaly
    alert_severity = Column(String, nullable=False)  # low, medium, high, critical
    current_sentiment = Column(Float, nullable=False)
    previous_sentiment = Column(Float)
    sentiment_change = Column(Float)  # percentage change
    threshold_value = Column(Float)
    confidence = Column(Float, nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime)
    is_resolved = Column(Boolean, default=False)
    notification_sent = Column(Boolean, default=False)
    alert_metadata = Column(JSON)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_alert_entity_severity', 'entity_name', 'alert_severity'),
        Index('idx_alert_triggered', 'triggered_at', 'is_resolved'),
        Index('idx_alert_type', 'alert_type', 'triggered_at'),
    )


class SentimentProcessingQueue(Base):
    """Model for managing sentiment processing queue."""
    
    __tablename__ = "sentiment_processing_queue"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String, nullable=False, unique=True)
    content_type = Column(String, nullable=False)
    content_text = Column(Text, nullable=False)
    source_url = Column(String)
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high, 4=critical
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    queue_metadata = Column(JSON)
    
    # Indexes for efficient queue processing
    __table_args__ = (
        Index('idx_queue_status_priority', 'status', 'priority', 'created_at'),
        Index('idx_queue_processing', 'status', 'started_at'),
    )