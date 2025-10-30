"""Background worker for sentiment processing queue."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.services.sentiment_processor import sentiment_processor
from app.database import AsyncSessionLocal
from app.models.sentiment_analysis import SentimentProcessingQueue
from sqlalchemy import select, and_, delete, func

logger = logging.getLogger(__name__)


class SentimentQueueWorker:
    """Background worker for processing sentiment analysis queue."""
    
    def __init__(self, batch_size: int = 10, poll_interval: int = 30):
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the queue worker."""
        if self.is_running:
            logger.warning("Sentiment queue worker is already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._worker_loop())
        logger.info("Sentiment queue worker started")

    async def stop(self):
        """Stop the queue worker."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Sentiment queue worker stopped")

    async def _worker_loop(self):
        """Main worker loop."""
        while self.is_running:
            try:
                # Process a batch of items
                processed_count = await sentiment_processor.process_queue_batch(self.batch_size)
                
                if processed_count > 0:
                    logger.info(f"Processed {processed_count} sentiment analysis items")
                
                # Clean up old completed/failed items
                await self._cleanup_old_items()
                
                # Wait before next iteration
                await asyncio.sleep(self.poll_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sentiment queue worker loop: {str(e)}")
                await asyncio.sleep(self.poll_interval)

    async def _cleanup_old_items(self, retention_days: int = 7):
        """Clean up old completed and failed items from the queue."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
            
            async with AsyncSessionLocal() as db:
                # Delete old completed and failed items with bulk delete
                result = await db.execute(
                    delete(SentimentProcessingQueue)
                    .where(
                        and_(
                            SentimentProcessingQueue.status.in_(["completed", "failed"]),
                            SentimentProcessingQueue.completed_at < cutoff_date
                        )
                    )
                )
                
                deleted_count = result.rowcount
                await db.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old sentiment processing items")
                
        except Exception as e:
            logger.error(f"Error cleaning up old queue items: {str(e)}")

    async def get_queue_status(self) -> dict:
        """Get current queue status."""
        try:
            async with AsyncSessionLocal() as db:
                # Count items by status with single aggregated query
                result = await db.execute(
                    select(
                        SentimentProcessingQueue.status,
                        func.count(SentimentProcessingQueue.id).label('count')
                    )
                    .group_by(SentimentProcessingQueue.status)
                )
                
                # Build status counts dict
                status_counts = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
                total = 0
                
                for status, count in result:
                    count = int(count)
                    if status in status_counts:
                        status_counts[status] = count
                    total += count
                
                return {
                    "is_running": self.is_running,
                    "pending": status_counts["pending"],
                    "processing": status_counts["processing"],
                    "completed": status_counts["completed"],
                    "failed": status_counts["failed"],
                    "total": total
                }
                
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            return {
                "is_running": self.is_running,
                "error": str(e)
            }


# Global worker instance
sentiment_queue_worker = SentimentQueueWorker()