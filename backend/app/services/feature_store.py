"""
Feature Store Service for ML Accuracy Engine

This service provides persistent storage and retrieval of extracted features
for ML model training and inference. Features are stored in Redis for fast
access and PostgreSQL for persistence.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float, Boolean, select, and_

from app.config import settings
from app.services.feature_extractor import FeatureSet, ExtractedFeature, FeatureType
from app.models.ml_model_registry import FeatureStoreRecord

logger = logging.getLogger(__name__)

class FeatureStore:
    """Service for storing and retrieving extracted features."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis_client: Optional[redis.Redis] = None
        self.redis_ttl = timedelta(hours=24)  # Cache features for 24 hours
        self.redis_prefix = "ml_features:"
    
    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Feature caching disabled.")
                self.redis_client = None
        
        return self.redis_client
    
    async def store_features(self, feature_set: FeatureSet) -> bool:
        """Store features in both Redis cache and PostgreSQL."""
        try:
            # Store in PostgreSQL for persistence
            await self._store_features_db(feature_set)
            
            # Store in Redis for fast access
            await self._store_features_redis(feature_set)
            
            logger.info(f"Stored {len(feature_set.features)} features for {feature_set.entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store features for {feature_set.entity_id}: {e}")
            return False
    
    async def _store_features_db(self, feature_set: FeatureSet) -> None:
        """Store features in PostgreSQL database."""
        # Convert features to JSON-serializable format
        features_data = []
        feature_types = set()
        confidences = []
        
        for feature in feature_set.features:
            feature_data = {
                "name": feature.name,
                "value": feature.value,
                "feature_type": feature.feature_type.value,
                "confidence": feature.confidence,
                "metadata": feature.metadata
            }
            features_data.append(feature_data)
            feature_types.add(feature.feature_type.value)
            confidences.append(feature.confidence)
        
        # Calculate metadata
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Check if record already exists
        existing_result = await self.db.execute(
            select(FeatureStoreRecord).where(
                and_(
                    FeatureStoreRecord.entity_id == feature_set.entity_id,
                    FeatureStoreRecord.entity_type == feature_set.entity_type,
                    FeatureStoreRecord.feature_hash == feature_set.feature_hash
                )
            )
        )
        existing_record = existing_result.scalar_one_or_none()
        
        if existing_record:
            # Update existing record
            existing_record.features_json = features_data
            existing_record.extraction_timestamp = feature_set.extraction_timestamp
            existing_record.feature_count = len(feature_set.features)
            existing_record.avg_confidence = avg_confidence
            existing_record.feature_types = list(feature_types)
        else:
            # Create new record
            db_record = FeatureStoreRecord(
                entity_id=feature_set.entity_id,
                entity_type=feature_set.entity_type,
                feature_hash=feature_set.feature_hash,
                features_json=features_data,
                extraction_timestamp=feature_set.extraction_timestamp,
                feature_count=len(feature_set.features),
                avg_confidence=avg_confidence,
                feature_types=list(feature_types)
            )
            self.db.add(db_record)
        
        await self.db.commit()
    
    async def _store_features_redis(self, feature_set: FeatureSet) -> None:
        """Store features in Redis cache."""
        redis_client = await self._get_redis_client()
        if not redis_client:
            return
        
        try:
            cache_key = f"{self.redis_prefix}{feature_set.entity_type}:{feature_set.entity_id}"
            
            # Serialize feature set
            cache_data = {
                "entity_id": feature_set.entity_id,
                "entity_type": feature_set.entity_type,
                "feature_hash": feature_set.feature_hash,
                "extraction_timestamp": feature_set.extraction_timestamp.isoformat(),
                "features": [asdict(feature) for feature in feature_set.features]
            }
            
            # Store with TTL
            await redis_client.setex(
                cache_key,
                int(self.redis_ttl.total_seconds()),
                json.dumps(cache_data, default=str)
            )
            
        except Exception as e:
            logger.warning(f"Failed to cache features in Redis: {e}")
    
    async def retrieve_features(
        self, 
        entity_id: str, 
        entity_type: str,
        use_cache: bool = True
    ) -> Optional[FeatureSet]:
        """Retrieve features from cache or database."""
        
        # Try Redis cache first
        if use_cache:
            cached_features = await self._retrieve_features_redis(entity_id, entity_type)
            if cached_features:
                return cached_features
        
        # Fall back to database
        return await self._retrieve_features_db(entity_id, entity_type)
    
    async def _retrieve_features_redis(
        self, 
        entity_id: str, 
        entity_type: str
    ) -> Optional[FeatureSet]:
        """Retrieve features from Redis cache."""
        redis_client = await self._get_redis_client()
        if not redis_client:
            return None
        
        try:
            cache_key = f"{self.redis_prefix}{entity_type}:{entity_id}"
            cached_data = await redis_client.get(cache_key)
            
            if not cached_data:
                return None
            
            data = json.loads(cached_data)
            
            # Reconstruct features
            features = []
            for feature_data in data["features"]:
                feature = ExtractedFeature(
                    name=feature_data["name"],
                    value=feature_data["value"],
                    feature_type=FeatureType(feature_data["feature_type"]),
                    confidence=feature_data["confidence"],
                    metadata=feature_data["metadata"]
                )
                features.append(feature)
            
            return FeatureSet(
                entity_id=data["entity_id"],
                entity_type=data["entity_type"],
                features=features,
                extraction_timestamp=datetime.fromisoformat(data["extraction_timestamp"]),
                feature_hash=data["feature_hash"]
            )
            
        except Exception as e:
            logger.warning(f"Failed to retrieve features from Redis: {e}")
            return None
    
    async def _retrieve_features_db(
        self, 
        entity_id: str, 
        entity_type: str
    ) -> Optional[FeatureSet]:
        """Retrieve features from PostgreSQL database."""
        try:
            result = await self.db.execute(
                select(FeatureStoreRecord)
                .where(
                    and_(
                        FeatureStoreRecord.entity_id == entity_id,
                        FeatureStoreRecord.entity_type == entity_type
                    )
                )
                .order_by(FeatureStoreRecord.extraction_timestamp.desc())
                .limit(1)
            )
            
            record = result.scalar_one_or_none()
            if not record:
                return None
            
            # Reconstruct features
            features = []
            for feature_data in record.features_json:
                feature = ExtractedFeature(
                    name=feature_data["name"],
                    value=feature_data["value"],
                    feature_type=FeatureType(feature_data["feature_type"]),
                    confidence=feature_data["confidence"],
                    metadata=feature_data["metadata"]
                )
                features.append(feature)
            
            feature_set = FeatureSet(
                entity_id=record.entity_id,
                entity_type=record.entity_type,
                features=features,
                extraction_timestamp=record.extraction_timestamp,
                feature_hash=record.feature_hash
            )
            
            # Cache in Redis for future requests
            await self._store_features_redis(feature_set)
            
            return feature_set
            
        except Exception as e:
            logger.error(f"Failed to retrieve features from database: {e}")
            return None
    
    async def retrieve_batch_features(
        self, 
        entity_ids: List[str], 
        entity_type: str,
        use_cache: bool = True
    ) -> Dict[str, FeatureSet]:
        """Retrieve features for multiple entities."""
        results = {}
        
        for entity_id in entity_ids:
            feature_set = await self.retrieve_features(entity_id, entity_type, use_cache)
            if feature_set:
                results[entity_id] = feature_set
        
        return results
    
    async def get_feature_statistics(
        self, 
        entity_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get statistics about stored features."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Build query
            query = select(FeatureStoreRecord).where(
                FeatureStoreRecord.created_at >= start_date
            )
            
            if entity_type:
                query = query.where(FeatureStoreRecord.entity_type == entity_type)
            
            result = await self.db.execute(query)
            records = result.scalars().all()
            
            if not records:
                return {
                    "total_records": 0,
                    "entity_types": {},
                    "avg_feature_count": 0,
                    "avg_confidence": 0,
                    "feature_types": {}
                }
            
            # Calculate statistics
            total_records = len(records)
            entity_type_counts = {}
            feature_counts = []
            confidences = []
            all_feature_types = set()
            
            for record in records:
                # Entity type distribution
                entity_type_counts[record.entity_type] = entity_type_counts.get(record.entity_type, 0) + 1
                
                # Feature counts and confidences
                feature_counts.append(record.feature_count)
                confidences.append(record.avg_confidence)
                
                # Feature types
                all_feature_types.update(record.feature_types)
            
            return {
                "total_records": total_records,
                "entity_types": entity_type_counts,
                "avg_feature_count": sum(feature_counts) / len(feature_counts),
                "avg_confidence": sum(confidences) / len(confidences),
                "feature_types": list(all_feature_types),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get feature statistics: {e}")
            return {}
    
    async def cleanup_old_features(self, days: int = 90) -> int:
        """Clean up old feature records from database."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Count records to be deleted
            count_result = await self.db.execute(
                select(FeatureStoreRecord)
                .where(FeatureStoreRecord.created_at < cutoff_date)
            )
            records_to_delete = len(count_result.scalars().all())
            
            # Delete old records
            await self.db.execute(
                FeatureStoreRecord.__table__.delete()
                .where(FeatureStoreRecord.created_at < cutoff_date)
            )
            await self.db.commit()
            
            logger.info(f"Cleaned up {records_to_delete} old feature records")
            return records_to_delete
            
        except Exception as e:
            logger.error(f"Failed to cleanup old features: {e}")
            await self.db.rollback()
            return 0
    
    async def invalidate_cache(self, entity_id: str, entity_type: str) -> bool:
        """Invalidate cached features for a specific entity."""
        redis_client = await self._get_redis_client()
        if not redis_client:
            return False
        
        try:
            cache_key = f"{self.redis_prefix}{entity_type}:{entity_id}"
            deleted = await redis_client.delete(cache_key)
            return deleted > 0
            
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
            return False