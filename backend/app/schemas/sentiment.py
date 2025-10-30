"""Pydantic schemas for sentiment analysis models."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class SentimentAnalysisBase(BaseModel):
    """Base schema for sentiment analysis."""
    content_id: str
    content_type: str
    entity_name: str
    entity_type: str
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str = Field(..., pattern="^(positive|negative|neutral)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_url: Optional[str] = None
    content_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SentimentAnalysisCreate(SentimentAnalysisBase):
    """Schema for creating sentiment analysis."""
    processing_timestamp: Optional[datetime] = None


class SentimentAnalysisUpdate(BaseModel):
    """Schema for updating sentiment analysis."""
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    sentiment_label: Optional[str] = Field(None, pattern="^(positive|negative|neutral)$")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None


class SentimentAnalysisResponse(SentimentAnalysisBase):
    """Schema for sentiment analysis response."""
    id: int
    processing_timestamp: datetime

    class Config:
        from_attributes = True


class SentimentTrendBase(BaseModel):
    """Base schema for sentiment trend."""
    entity_name: str
    entity_type: str
    timeframe: str = Field(..., pattern="^(daily|weekly|monthly)$")
    period_start: datetime
    period_end: datetime
    average_sentiment: float = Field(..., ge=-1.0, le=1.0)
    sentiment_volatility: float = Field(..., ge=0.0)
    total_mentions: int = Field(..., ge=0)
    positive_mentions: int = Field(default=0, ge=0)
    negative_mentions: int = Field(default=0, ge=0)
    neutral_mentions: int = Field(default=0, ge=0)
    trend_direction: Optional[str] = Field(None, pattern="^(improving|declining|stable|volatile)$")
    trend_strength: Optional[float] = Field(None, ge=0.0, le=1.0)


class SentimentTrendCreate(SentimentTrendBase):
    """Schema for creating sentiment trend."""
    sentiment_analysis_id: Optional[int] = None


class SentimentTrendResponse(SentimentTrendBase):
    """Schema for sentiment trend response."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SentimentAlertBase(BaseModel):
    """Base schema for sentiment alert."""
    entity_name: str
    entity_type: str
    alert_type: str = Field(..., pattern="^(shift|threshold|anomaly)$")
    alert_severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    current_sentiment: float = Field(..., ge=-1.0, le=1.0)
    previous_sentiment: Optional[float] = Field(None, ge=-1.0, le=1.0)
    sentiment_change: Optional[float] = None
    threshold_value: Optional[float] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None


class SentimentAlertCreate(SentimentAlertBase):
    """Schema for creating sentiment alert."""
    triggered_at: Optional[datetime] = None
    is_resolved: bool = False
    notification_sent: bool = False


class SentimentAlertUpdate(BaseModel):
    """Schema for updating sentiment alert."""
    is_resolved: Optional[bool] = None
    resolved_at: Optional[datetime] = None
    notification_sent: Optional[bool] = None


class SentimentAlertResponse(SentimentAlertBase):
    """Schema for sentiment alert response."""
    id: int
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    is_resolved: bool
    notification_sent: bool

    class Config:
        from_attributes = True


class SentimentProcessingQueueBase(BaseModel):
    """Base schema for sentiment processing queue."""
    content_id: str
    content_type: str
    content_text: str
    source_url: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=4)
    status: str = Field(default="pending", pattern="^(pending|processing|completed|failed)$")
    error_message: Optional[str] = None
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=1)
    metadata: Optional[Dict[str, Any]] = None


class SentimentProcessingQueueCreate(SentimentProcessingQueueBase):
    """Schema for creating processing queue item."""
    created_at: Optional[datetime] = None


class SentimentProcessingQueueUpdate(BaseModel):
    """Schema for updating processing queue item."""
    status: Optional[str] = Field(None, pattern="^(pending|processing|completed|failed)$")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = Field(None, ge=0)


class SentimentProcessingQueueResponse(SentimentProcessingQueueBase):
    """Schema for processing queue response."""
    id: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Additional response schemas for API endpoints

class EntitySentimentSummary(BaseModel):
    """Summary of sentiment for an entity."""
    entity_name: str
    entity_type: str
    current_sentiment: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str
    total_mentions: int
    confidence: float = Field(..., ge=0.0, le=1.0)
    last_updated: datetime
    trend_direction: Optional[str] = None


class SentimentVisualizationData(BaseModel):
    """Data for sentiment visualization."""
    entity_name: str
    timeframe: str
    data_points: List[Dict[str, Any]]
    summary: Dict[str, Any]


class SentimentAnalysisStats(BaseModel):
    """Statistics for sentiment analysis system."""
    total_analyses: int
    entities_tracked: int
    active_alerts: int
    processing_queue_size: int
    average_confidence: float
    sentiment_distribution: Dict[str, int]  # positive, negative, neutral counts


class BulkSentimentRequest(BaseModel):
    """Request for bulk sentiment analysis."""
    content_items: List[Dict[str, Any]] = Field(..., min_items=1, max_items=100)
    content_type: str = Field(default="news")
    priority: int = Field(default=1, ge=1, le=4)


class BulkSentimentResponse(BaseModel):
    """Response for bulk sentiment analysis."""
    total_items: int
    queued_items: int
    failed_items: int
    batch_id: str
    estimated_completion: datetime


class SentimentWebSocketMessage(BaseModel):
    """WebSocket message for real-time sentiment updates."""
    type: str = Field(..., pattern="^(sentiment_update|alert|trend_change|ping_response)$")
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class SentimentSystemHealth(BaseModel):
    """Health status of sentiment analysis system."""
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$")
    timestamp: datetime
    worker_status: Dict[str, Any]
    services: Dict[str, str]
    error: Optional[str] = None