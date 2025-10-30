from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.services.feature_extractor import FeatureExtractor
from app.services.feature_store import FeatureStore
from app.models.impact_card import ImpactCard
from app.models.ml_training import FeedbackRecord
from sqlalchemy import select

router = APIRouter(prefix="/api/ml-features", tags=["ML Features"])

@router.post("/extract/impact-card/{impact_card_id}")
async def extract_impact_card_features(
    impact_card_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Extract features from a specific impact card."""
    try:
        # Get the impact card
        result = await db.execute(select(ImpactCard).where(ImpactCard.id == impact_card_id))
        impact_card = result.scalar_one_or_none()
        
        if not impact_card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Impact card with ID {impact_card_id} not found"
            )
        
        # Extract features
        extractor = FeatureExtractor(db)
        feature_set = await extractor.extract_impact_card_features(impact_card)
        
        # Validate features
        is_valid, errors = await extractor.validate_features(feature_set)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Feature validation failed: {errors}"
            )
        
        # Normalize features
        normalized_features = await extractor.normalize_features(feature_set)
        
        # Store features
        feature_store = FeatureStore(db)
        stored = await feature_store.store_features(normalized_features)
        
        if not stored:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store extracted features"
            )
        
        return {
            "entity_id": normalized_features.entity_id,
            "entity_type": normalized_features.entity_type,
            "feature_count": len(normalized_features.features),
            "feature_hash": normalized_features.feature_hash,
            "extraction_timestamp": normalized_features.extraction_timestamp,
            "features": [
                {
                    "name": f.name,
                    "value": f.value,
                    "type": f.feature_type.value,
                    "confidence": f.confidence,
                    "metadata": f.metadata
                }
                for f in normalized_features.features
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract features: {str(e)}"
        )

@router.post("/extract/feedback/{feedback_id}")
async def extract_feedback_features(
    feedback_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Extract features from a specific feedback record."""
    try:
        # Get the feedback record
        result = await db.execute(select(FeedbackRecord).where(FeedbackRecord.id == feedback_id))
        feedback = result.scalar_one_or_none()
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Feedback record with ID {feedback_id} not found"
            )
        
        # Extract features
        extractor = FeatureExtractor(db)
        feature_set = await extractor.extract_feedback_features(feedback)
        
        # Validate and normalize features
        is_valid, errors = await extractor.validate_features(feature_set)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Feature validation failed: {errors}"
            )
        
        normalized_features = await extractor.normalize_features(feature_set)
        
        # Store features
        feature_store = FeatureStore(db)
        stored = await feature_store.store_features(normalized_features)
        
        if not stored:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store extracted features"
            )
        
        return {
            "entity_id": normalized_features.entity_id,
            "entity_type": normalized_features.entity_type,
            "feature_count": len(normalized_features.features),
            "feature_hash": normalized_features.feature_hash,
            "extraction_timestamp": normalized_features.extraction_timestamp,
            "features": [
                {
                    "name": f.name,
                    "value": f.value,
                    "type": f.feature_type.value,
                    "confidence": f.confidence,
                    "metadata": f.metadata
                }
                for f in normalized_features.features
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract features: {str(e)}"
        )

@router.post("/extract/batch")
async def extract_batch_features(
    entity_type: str = Query(..., description="Type of entities (impact_card, feedback)"),
    entity_ids: List[int] = Query(..., description="List of entity IDs"),
    use_cache: bool = Query(True, description="Whether to use cached features"),
    db: AsyncSession = Depends(get_db)
):
    """Extract features for multiple entities in batch."""
    try:
        if len(entity_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 entities allowed per batch"
            )
        
        extractor = FeatureExtractor(db)
        feature_store = FeatureStore(db)
        
        # Convert IDs to strings for the extractor
        str_entity_ids = [str(eid) for eid in entity_ids]
        
        # Extract features
        feature_sets = await extractor.extract_batch_features(
            entity_type, str_entity_ids, use_cache
        )
        
        # Store all feature sets
        stored_count = 0
        results = []
        
        for feature_set in feature_sets:
            # Validate and normalize
            is_valid, errors = await extractor.validate_features(feature_set)
            if is_valid:
                normalized_features = await extractor.normalize_features(feature_set)
                stored = await feature_store.store_features(normalized_features)
                
                if stored:
                    stored_count += 1
                    results.append({
                        "entity_id": normalized_features.entity_id,
                        "feature_count": len(normalized_features.features),
                        "feature_hash": normalized_features.feature_hash,
                        "status": "success"
                    })
                else:
                    results.append({
                        "entity_id": feature_set.entity_id,
                        "status": "storage_failed"
                    })
            else:
                results.append({
                    "entity_id": feature_set.entity_id,
                    "status": "validation_failed",
                    "errors": errors
                })
        
        return {
            "total_requested": len(entity_ids),
            "total_processed": len(feature_sets),
            "total_stored": stored_count,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract batch features: {str(e)}"
        )

@router.get("/retrieve/{entity_type}/{entity_id}")
async def retrieve_features(
    entity_type: str,
    entity_id: str,
    use_cache: bool = Query(True, description="Whether to use cached features"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve stored features for a specific entity."""
    try:
        feature_store = FeatureStore(db)
        feature_set = await feature_store.retrieve_features(entity_id, entity_type, use_cache)
        
        if not feature_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No features found for {entity_type} {entity_id}"
            )
        
        return {
            "entity_id": feature_set.entity_id,
            "entity_type": feature_set.entity_type,
            "feature_count": len(feature_set.features),
            "feature_hash": feature_set.feature_hash,
            "extraction_timestamp": feature_set.extraction_timestamp,
            "features": [
                {
                    "name": f.name,
                    "value": f.value,
                    "type": f.feature_type.value,
                    "confidence": f.confidence,
                    "metadata": f.metadata
                }
                for f in feature_set.features
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve features: {str(e)}"
        )

@router.get("/stats")
async def get_feature_statistics(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics about stored features."""
    try:
        feature_store = FeatureStore(db)
        stats = await feature_store.get_feature_statistics(entity_type, days)
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feature statistics: {str(e)}"
        )

@router.delete("/cleanup")
async def cleanup_old_features(
    days: int = Query(90, ge=30, le=365, description="Delete features older than this many days"),
    db: AsyncSession = Depends(get_db)
):
    """Clean up old feature records."""
    try:
        feature_store = FeatureStore(db)
        deleted_count = await feature_store.cleanup_old_features(days)
        
        return {
            "deleted_count": deleted_count,
            "cutoff_days": days,
            "message": f"Cleaned up {deleted_count} feature records older than {days} days"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup features: {str(e)}"
        )

@router.delete("/cache/{entity_type}/{entity_id}")
async def invalidate_feature_cache(
    entity_type: str,
    entity_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Invalidate cached features for a specific entity."""
    try:
        feature_store = FeatureStore(db)
        invalidated = await feature_store.invalidate_cache(entity_id, entity_type)
        
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "cache_invalidated": invalidated
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invalidate cache: {str(e)}"
        )