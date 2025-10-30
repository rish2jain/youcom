"""Sentiment processing pipeline for real-time sentiment analysis."""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

import httpx
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.sentiment_analysis import (
    SentimentAnalysis, SentimentTrend, SentimentAlert, SentimentProcessingQueue
)
# Removed circular import - YouComClient not actually used in this file
from app.services.sentiment_classifier import get_entity_recognizer, get_sentiment_classifier
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Result of sentiment analysis processing."""
    sentiment_score: float  # -1.0 to 1.0
    sentiment_label: str    # positive, negative, neutral
    confidence: float       # 0.0 to 1.0
    entities: List[Dict[str, Any]]
    processing_time: float


@dataclass
class EntityMention:
    """Extracted entity mention from content."""
    name: str
    entity_type: str  # company, product, market
    confidence: float
    context: str


class SentimentProcessor:
    """Main sentiment processing pipeline."""
    
    def __init__(self):
        # YouComClient not needed for sentiment processing
        pass

    async def process_content(self, content_id: str, content_text: str, 
                            content_type: str = "news", source_url: Optional[str] = None) -> SentimentResult:
        """Process content for sentiment analysis."""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Extract entities from content using advanced recognizer
            entity_results = await get_entity_recognizer().recognize_entities(content_text)
            
            # Classify sentiment using advanced classifier
            sentiment_result = await get_sentiment_classifier().classify_sentiment(content_text, entity_results)
            
            # Store results in database
            async with AsyncSessionLocal() as db:
                for entity in entity_results:
                    sentiment_analysis = SentimentAnalysis(
                        content_id=content_id,
                        content_type=content_type,
                        entity_name=entity.name,
                        entity_type=entity.entity_type,
                        sentiment_score=sentiment_result.sentiment_score,
                        sentiment_label=sentiment_result.sentiment_label,
                        confidence=sentiment_result.confidence,
                        processing_timestamp=datetime.now(timezone.utc),
                        source_url=source_url,
                        content_text=content_text[:1000],  # Truncate for storage
                        analysis_metadata={
                            "entity_confidence": entity.confidence,
                            "entity_context": entity.context,
                            "sentiment_reasoning": sentiment_result.reasoning,
                            "sentiment_metadata": sentiment_result.metadata,
                            "processing_version": "2.0"
                        }
                    )
                    db.add(sentiment_analysis)
                
                await db.commit()
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Convert entity results to dict format for backward compatibility
            entities_dict = [
                {
                    "name": e.name,
                    "type": e.entity_type,
                    "confidence": e.confidence,
                    "context": e.context
                }
                for e in entity_results
            ]
            
            return SentimentResult(
                sentiment_score=sentiment_result.sentiment_score,
                sentiment_label=sentiment_result.sentiment_label,
                confidence=sentiment_result.confidence,
                entities=entities_dict,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing sentiment for content {content_id}: {str(e)}")
            raise



    async def queue_content_for_processing(self, content_id: str, content_text: str, 
                                         content_type: str = "news", source_url: Optional[str] = None,
                                         priority: int = 1) -> bool:
        """Add content to processing queue."""
        try:
            async with AsyncSessionLocal() as db:
                # Check if content already exists in queue
                existing = await db.execute(
                    select(SentimentProcessingQueue).where(
                        SentimentProcessingQueue.content_id == content_id
                    )
                )
                if existing.scalar_one_or_none():
                    logger.info(f"Content {content_id} already in processing queue")
                    return False
                
                queue_item = SentimentProcessingQueue(
                    content_id=content_id,
                    content_type=content_type,
                    content_text=content_text,
                    source_url=source_url,
                    priority=priority,
                    status="pending",
                    created_at=datetime.now(timezone.utc)
                )
                
                db.add(queue_item)
                await db.commit()
                
                logger.info(f"Added content {content_id} to sentiment processing queue")
                return True
                
        except Exception as e:
            logger.error(f"Error queuing content for processing: {str(e)}")
            return False

    async def process_queue_batch(self, batch_size: int = 10) -> int:
        """Process a batch of items from the processing queue."""
        processed_count = 0
        
        try:
            async with AsyncSessionLocal() as db:
                # Get pending items ordered by priority and creation time
                result = await db.execute(
                    select(SentimentProcessingQueue)
                    .where(SentimentProcessingQueue.status == "pending")
                    .order_by(desc(SentimentProcessingQueue.priority), SentimentProcessingQueue.created_at)
                    .limit(batch_size)
                )
                
                queue_items = result.scalars().all()
                
                for item in queue_items:
                    try:
                        # Update status to processing
                        item.status = "processing"
                        item.started_at = datetime.now(timezone.utc)
                        await db.commit()
                        
                        # Process the content
                        await self.process_content(
                            content_id=item.content_id,
                            content_text=item.content_text,
                            content_type=item.content_type,
                            source_url=item.source_url
                        )
                        
                        # Mark as completed
                        item.status = "completed"
                        item.completed_at = datetime.now(timezone.utc)
                        await db.commit()
                        
                        processed_count += 1
                        logger.info(f"Successfully processed content {item.content_id}")
                        
                    except Exception as e:
                        # Mark as failed and increment retry count
                        item.status = "failed"
                        item.error_message = str(e)
                        item.retry_count += 1
                        item.completed_at = datetime.now(timezone.utc)
                        
                        # Requeue if under retry limit
                        if item.retry_count < item.max_retries:
                            item.status = "pending"
                            item.completed_at = None
                        
                        await db.commit()
                        logger.error(f"Failed to process content {item.content_id}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error processing queue batch: {str(e)}")
        
        return processed_count


# Global sentiment processor instance
sentiment_processor = SentimentProcessor()