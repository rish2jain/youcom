from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.models.ml_training import FeedbackRecord
from app.schemas.ml_feedback import (
    FeedbackCreate, FeedbackResponse, FeedbackBatch, FeedbackStats,
    OneClickFeedback, FeedbackFilter, FeedbackType, ExpertiseLevel
)

router = APIRouter(prefix="/api/ml-feedback", tags=["ML Feedback"])

@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback: FeedbackCreate,
    user_id: str = Query(..., description="User ID providing feedback"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new feedback record for ML model improvement."""
    try:
        # Validate that the impact card exists
        from app.models.impact_card import ImpactCard
        result = await db.execute(select(ImpactCard).where(ImpactCard.id == feedback.impact_card_id))
        impact_card = result.scalar_one_or_none()
        
        if not impact_card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Impact card with ID {feedback.impact_card_id} not found"
            )

        # Create feedback record
        db_feedback = FeedbackRecord(
            user_id=user_id,
            impact_card_id=feedback.impact_card_id,
            feedback_type=feedback.feedback_type.value,
            original_value=feedback.original_value,
            corrected_value=feedback.corrected_value,
            confidence=feedback.confidence,
            feedback_context=feedback.feedback_context,
            user_expertise_level=feedback.user_expertise_level.value
        )
        
        db.add(db_feedback)
        await db.commit()
        await db.refresh(db_feedback)
        
        return FeedbackResponse.from_orm(db_feedback)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create feedback: {str(e)}"
        )

@router.post("/batch", response_model=List[FeedbackResponse], status_code=status.HTTP_201_CREATED)
async def create_feedback_batch(
    feedback_batch: FeedbackBatch,
    user_id: str = Query(..., description="User ID providing feedback"),
    db: AsyncSession = Depends(get_db)
):
    """Create multiple feedback records in a single batch operation."""
    try:
        # Validate all impact cards exist
        impact_card_ids = [item.impact_card_id for item in feedback_batch.feedback_items]
        from app.models.impact_card import ImpactCard
        result = await db.execute(
            select(ImpactCard.id).where(ImpactCard.id.in_(impact_card_ids))
        )
        existing_ids = {row[0] for row in result.fetchall()}
        
        missing_ids = set(impact_card_ids) - existing_ids
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Impact cards not found: {list(missing_ids)}"
            )

        # Create all feedback records
        db_feedback_records = []
        for feedback_item in feedback_batch.feedback_items:
            db_feedback = FeedbackRecord(
                user_id=user_id,
                impact_card_id=feedback_item.impact_card_id,
                feedback_type=feedback_item.feedback_type.value,
                original_value=feedback_item.original_value,
                corrected_value=feedback_item.corrected_value,
                confidence=feedback_item.confidence,
                feedback_context=feedback_item.feedback_context,
                user_expertise_level=feedback_item.user_expertise_level.value
            )
            db_feedback_records.append(db_feedback)
            db.add(db_feedback)
        
        await db.commit()
        
        # Refresh all records to get IDs and timestamps
        for record in db_feedback_records:
            await db.refresh(record)
        
        return [FeedbackResponse.from_orm(record) for record in db_feedback_records]
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create feedback batch: {str(e)}"
        )

@router.post("/one-click", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_one_click_feedback(
    one_click: OneClickFeedback,
    user_id: str = Query(..., description="User ID providing feedback"),
    db: AsyncSession = Depends(get_db)
):
    """Create feedback from one-click user actions."""
    try:
        # Map one-click actions to structured feedback
        feedback_mapping = {
            'thumbs_up': {'type': FeedbackType.ACCURACY, 'confidence': 0.8, 'context': {'rating': 'positive'}},
            'thumbs_down': {'type': FeedbackType.ACCURACY, 'confidence': 0.8, 'context': {'rating': 'negative'}},
            'too_high': {'type': FeedbackType.SEVERITY, 'confidence': 0.7, 'context': {'adjustment': 'decrease'}},
            'too_low': {'type': FeedbackType.SEVERITY, 'confidence': 0.7, 'context': {'adjustment': 'increase'}},
            'just_right': {'type': FeedbackType.SEVERITY, 'confidence': 0.9, 'context': {'rating': 'correct'}},
            'relevant': {'type': FeedbackType.RELEVANCE, 'confidence': 0.8, 'context': {'rating': 'relevant'}},
            'not_relevant': {'type': FeedbackType.RELEVANCE, 'confidence': 0.8, 'context': {'rating': 'not_relevant'}},
            'correct_category': {'type': FeedbackType.CATEGORY, 'confidence': 0.8, 'context': {'rating': 'correct'}},
            'wrong_category': {'type': FeedbackType.CATEGORY, 'confidence': 0.8, 'context': {'rating': 'incorrect'}}
        }
        
        if one_click.feedback_action not in feedback_mapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid one-click action: {one_click.feedback_action}"
            )
        
        mapping = feedback_mapping[one_click.feedback_action]
        
        # Create structured feedback
        feedback = FeedbackCreate(
            impact_card_id=one_click.impact_card_id,
            feedback_type=mapping['type'],
            confidence=mapping['confidence'],
            feedback_context={
                **mapping['context'],
                'source': 'one_click',
                'action': one_click.feedback_action
            }
        )
        
        return await create_feedback(feedback, user_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process one-click feedback: {str(e)}"
        )

@router.get("/", response_model=List[FeedbackResponse])
async def get_feedback_records(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    feedback_filter: FeedbackFilter = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve feedback records with optional filtering."""
    try:
        query = select(FeedbackRecord)
        
        # Apply filters
        conditions = []
        if feedback_filter.feedback_type:
            conditions.append(FeedbackRecord.feedback_type == feedback_filter.feedback_type.value)
        if feedback_filter.processed is not None:
            conditions.append(FeedbackRecord.processed == feedback_filter.processed)
        if feedback_filter.user_expertise_level:
            conditions.append(FeedbackRecord.user_expertise_level == feedback_filter.user_expertise_level.value)
        if feedback_filter.start_date:
            conditions.append(FeedbackRecord.feedback_timestamp >= feedback_filter.start_date)
        if feedback_filter.end_date:
            conditions.append(FeedbackRecord.feedback_timestamp <= feedback_filter.end_date)
        if feedback_filter.impact_card_id:
            conditions.append(FeedbackRecord.impact_card_id == feedback_filter.impact_card_id)
        if feedback_filter.min_confidence:
            conditions.append(FeedbackRecord.confidence >= feedback_filter.min_confidence)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Apply pagination and ordering
        query = query.order_by(FeedbackRecord.feedback_timestamp.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        feedback_records = result.scalars().all()
        
        return [FeedbackResponse.from_orm(record) for record in feedback_records]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback records: {str(e)}"
        )

@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to include in statistics"),
    db: AsyncSession = Depends(get_db)
):
    """Get feedback statistics for the specified time period."""
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total feedback count
        total_result = await db.execute(
            select(func.count(FeedbackRecord.id)).where(
                FeedbackRecord.feedback_timestamp >= start_date
            )
        )
        total_count = total_result.scalar() or 0
        
        # Feedback by type
        type_result = await db.execute(
            select(FeedbackRecord.feedback_type, func.count(FeedbackRecord.id))
            .where(FeedbackRecord.feedback_timestamp >= start_date)
            .group_by(FeedbackRecord.feedback_type)
        )
        feedback_by_type = {row[0]: row[1] for row in type_result.fetchall()}
        
        # Feedback by expertise level
        expertise_result = await db.execute(
            select(FeedbackRecord.user_expertise_level, func.count(FeedbackRecord.id))
            .where(FeedbackRecord.feedback_timestamp >= start_date)
            .group_by(FeedbackRecord.user_expertise_level)
        )
        feedback_by_expertise = {row[0]: row[1] for row in expertise_result.fetchall()}
        
        # Processed vs pending counts
        processed_result = await db.execute(
            select(func.count(FeedbackRecord.id)).where(
                and_(
                    FeedbackRecord.feedback_timestamp >= start_date,
                    FeedbackRecord.processed == True
                )
            )
        )
        processed_count = processed_result.scalar() or 0
        pending_count = total_count - processed_count
        
        # Average confidence
        confidence_result = await db.execute(
            select(func.avg(FeedbackRecord.confidence)).where(
                FeedbackRecord.feedback_timestamp >= start_date
            )
        )
        average_confidence = float(confidence_result.scalar() or 0.0)
        
        return FeedbackStats(
            total_feedback_count=total_count,
            feedback_by_type=feedback_by_type,
            feedback_by_expertise=feedback_by_expertise,
            processed_count=processed_count,
            pending_count=pending_count,
            average_confidence=average_confidence
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve feedback statistics: {str(e)}"
        )

@router.put("/{feedback_id}/process", response_model=FeedbackResponse)
async def mark_feedback_processed(
    feedback_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Mark a feedback record as processed."""
    try:
        result = await db.execute(select(FeedbackRecord).where(FeedbackRecord.id == feedback_id))
        feedback_record = result.scalar_one_or_none()
        
        if not feedback_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback record with ID {feedback_id} not found"
            )
        
        feedback_record.processed = True
        feedback_record.processed_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(feedback_record)
        
        return FeedbackResponse.from_orm(feedback_record)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark feedback as processed: {str(e)}"
        )