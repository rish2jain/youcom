"""
Feature Extraction Pipeline for ML Accuracy Engine

This service extracts features from competitive intelligence data for ML model training.
Features are extracted from impact cards, news articles, and user feedback to improve
model accuracy over time.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.impact_card import ImpactCard
from app.models.ml_training import FeedbackRecord
from app.models.company_research import CompanyResearch

logger = logging.getLogger(__name__)

class FeatureType(str, Enum):
    """Types of features that can be extracted."""
    TEXTUAL = "textual"
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    STRUCTURAL = "structural"

@dataclass
class ExtractedFeature:
    """Container for a single extracted feature."""
    name: str
    value: Any
    feature_type: FeatureType
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class FeatureSet:
    """Container for a complete set of extracted features."""
    entity_id: str
    entity_type: str  # impact_card, news_article, etc.
    features: List[ExtractedFeature]
    extraction_timestamp: datetime
    feature_hash: str

class FeatureExtractor:
    """Main feature extraction service for competitive intelligence data."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.feature_cache: Dict[str, FeatureSet] = {}
        self.cache_ttl = timedelta(hours=1)
    
    async def extract_impact_card_features(self, impact_card: ImpactCard) -> FeatureSet:
        """Extract features from an impact card for ML training."""
        features = []
        
        # Basic numerical features
        features.extend([
            ExtractedFeature(
                name="risk_score",
                value=float(impact_card.risk_score),
                feature_type=FeatureType.NUMERICAL,
                confidence=1.0,
                metadata={"source": "impact_card", "field": "risk_score"}
            ),
            ExtractedFeature(
                name="confidence_score",
                value=float(impact_card.confidence_score),
                feature_type=FeatureType.NUMERICAL,
                confidence=1.0,
                metadata={"source": "impact_card", "field": "confidence_score"}
            ),
            ExtractedFeature(
                name="credibility_score",
                value=float(impact_card.credibility_score or 0.0),
                feature_type=FeatureType.NUMERICAL,
                confidence=0.9,
                metadata={"source": "impact_card", "field": "credibility_score"}
            ),
            ExtractedFeature(
                name="total_sources",
                value=float(impact_card.total_sources or 0),
                feature_type=FeatureType.NUMERICAL,
                confidence=1.0,
                metadata={"source": "impact_card", "field": "total_sources"}
            )
        ])
        
        # Categorical features
        features.append(
            ExtractedFeature(
                name="risk_level",
                value=impact_card.risk_level,
                feature_type=FeatureType.CATEGORICAL,
                confidence=1.0,
                metadata={"source": "impact_card", "field": "risk_level"}
            )
        )
        
        # Temporal features
        if impact_card.created_at:
            features.extend(self._extract_temporal_features(impact_card.created_at, "creation"))
        
        # Structural features from JSON fields
        if impact_card.impact_areas:
            features.extend(self._extract_impact_areas_features(impact_card.impact_areas))
        
        if impact_card.key_insights:
            features.extend(self._extract_insights_features(impact_card.key_insights))
        
        if impact_card.source_breakdown:
            features.extend(self._extract_source_features(impact_card.source_breakdown))
        
        # Textual features
        features.extend(self._extract_textual_features(impact_card))
        
        # Create feature set
        feature_set = FeatureSet(
            entity_id=f"impact_card_{impact_card.id}",
            entity_type="impact_card",
            features=features,
            extraction_timestamp=datetime.utcnow(),
            feature_hash=self._compute_feature_hash(features)
        )
        
        return feature_set
    
    def _extract_temporal_features(self, timestamp: datetime, prefix: str) -> List[ExtractedFeature]:
        """Extract temporal features from a timestamp."""
        features = []
        
        # Hour of day (0-23)
        features.append(
            ExtractedFeature(
                name=f"{prefix}_hour",
                value=float(timestamp.hour),
                feature_type=FeatureType.TEMPORAL,
                confidence=1.0,
                metadata={"source": "timestamp", "type": "hour_of_day"}
            )
        )
        
        # Day of week (0-6)
        features.append(
            ExtractedFeature(
                name=f"{prefix}_day_of_week",
                value=float(timestamp.weekday()),
                feature_type=FeatureType.TEMPORAL,
                confidence=1.0,
                metadata={"source": "timestamp", "type": "day_of_week"}
            )
        )
        
        # Days since epoch (for trend analysis)
        epoch = datetime(2020, 1, 1)
        days_since_epoch = (timestamp - epoch).days
        features.append(
            ExtractedFeature(
                name=f"{prefix}_days_since_epoch",
                value=float(days_since_epoch),
                feature_type=FeatureType.TEMPORAL,
                confidence=1.0,
                metadata={"source": "timestamp", "type": "days_since_epoch"}
            )
        )
        
        return features
    
    def _extract_impact_areas_features(self, impact_areas: List[Dict]) -> List[ExtractedFeature]:
        """Extract features from impact areas."""
        features = []
        
        if not impact_areas:
            return features
        
        # Number of impact areas
        features.append(
            ExtractedFeature(
                name="impact_areas_count",
                value=float(len(impact_areas)),
                feature_type=FeatureType.NUMERICAL,
                confidence=1.0,
                metadata={"source": "impact_areas", "type": "count"}
            )
        )
        
        # Impact area categories (one-hot encoding)
        categories = set()
        for area in impact_areas:
            if isinstance(area, dict) and 'category' in area:
                categories.add(area['category'])
        
        for category in categories:
            features.append(
                ExtractedFeature(
                    name=f"has_impact_category_{category.lower().replace(' ', '_')}",
                    value=1.0,
                    feature_type=FeatureType.CATEGORICAL,
                    confidence=0.9,
                    metadata={"source": "impact_areas", "category": category}
                )
            )
        
        return features
    
    def _extract_insights_features(self, insights: List[Dict]) -> List[ExtractedFeature]:
        """Extract features from key insights."""
        features = []
        
        if not insights:
            return features
        
        # Number of insights
        features.append(
            ExtractedFeature(
                name="insights_count",
                value=float(len(insights)),
                feature_type=FeatureType.NUMERICAL,
                confidence=1.0,
                metadata={"source": "insights", "type": "count"}
            )
        )
        
        # Average insight length (if text available)
        text_lengths = []
        for insight in insights:
            if isinstance(insight, dict) and 'text' in insight:
                text_lengths.append(len(insight['text']))
            elif isinstance(insight, str):
                text_lengths.append(len(insight))
        
        if text_lengths:
            features.append(
                ExtractedFeature(
                    name="avg_insight_length",
                    value=float(np.mean(text_lengths)),
                    feature_type=FeatureType.NUMERICAL,
                    confidence=0.8,
                    metadata={"source": "insights", "type": "avg_length"}
                )
            )
        
        return features
    
    def _extract_source_features(self, source_breakdown: Dict) -> List[ExtractedFeature]:
        """Extract features from source breakdown."""
        features = []
        
        if not source_breakdown:
            return features
        
        # Source diversity (number of different source types)
        features.append(
            ExtractedFeature(
                name="source_diversity",
                value=float(len(source_breakdown)),
                feature_type=FeatureType.NUMERICAL,
                confidence=1.0,
                metadata={"source": "source_breakdown", "type": "diversity"}
            )
        )
        
        # Specific source type counts
        for source_type, count in source_breakdown.items():
            if isinstance(count, (int, float)):
                features.append(
                    ExtractedFeature(
                        name=f"source_{source_type.lower().replace(' ', '_')}_count",
                        value=float(count),
                        feature_type=FeatureType.NUMERICAL,
                        confidence=0.9,
                        metadata={"source": "source_breakdown", "source_type": source_type}
                    )
                )
        
        return features
    
    def _extract_textual_features(self, impact_card: ImpactCard) -> List[ExtractedFeature]:
        """Extract textual features from impact card."""
        features = []
        
        # Competitor name length
        if impact_card.competitor_name:
            features.append(
                ExtractedFeature(
                    name="competitor_name_length",
                    value=float(len(impact_card.competitor_name)),
                    feature_type=FeatureType.TEXTUAL,
                    confidence=0.7,
                    metadata={"source": "competitor_name", "type": "length"}
                )
            )
        
        # Processing time (if available)
        if impact_card.processing_time:
            try:
                # Extract numeric value from processing time string
                time_str = impact_card.processing_time.lower()
                if 'second' in time_str:
                    time_value = float(time_str.split()[0])
                elif 'minute' in time_str:
                    time_value = float(time_str.split()[0]) * 60
                else:
                    time_value = 0.0
                
                features.append(
                    ExtractedFeature(
                        name="processing_time_seconds",
                        value=time_value,
                        feature_type=FeatureType.NUMERICAL,
                        confidence=0.8,
                        metadata={"source": "processing_time", "type": "duration"}
                    )
                )
            except (ValueError, IndexError):
                pass
        
        return features
    
    def _compute_feature_hash(self, features: List[ExtractedFeature]) -> str:
        """Compute a hash of the feature set for caching and versioning."""
        feature_data = []
        for feature in features:
            feature_data.append({
                'name': feature.name,
                'value': str(feature.value),
                'type': feature.feature_type.value
            })
        
        feature_json = json.dumps(feature_data, sort_keys=True)
        return hashlib.md5(feature_json.encode()).hexdigest()
    
    async def extract_feedback_features(self, feedback: FeedbackRecord) -> FeatureSet:
        """Extract features from user feedback for training data."""
        features = []
        
        # Basic feedback features
        features.extend([
            ExtractedFeature(
                name="feedback_confidence",
                value=float(feedback.confidence),
                feature_type=FeatureType.NUMERICAL,
                confidence=1.0,
                metadata={"source": "feedback", "field": "confidence"}
            ),
            ExtractedFeature(
                name="feedback_type",
                value=feedback.feedback_type,
                feature_type=FeatureType.CATEGORICAL,
                confidence=1.0,
                metadata={"source": "feedback", "field": "feedback_type"}
            ),
            ExtractedFeature(
                name="user_expertise_level",
                value=feedback.user_expertise_level,
                feature_type=FeatureType.CATEGORICAL,
                confidence=0.9,
                metadata={"source": "feedback", "field": "user_expertise_level"}
            )
        ])
        
        # Correction magnitude (if applicable)
        if feedback.original_value is not None and feedback.corrected_value is not None:
            correction_magnitude = abs(feedback.corrected_value - feedback.original_value)
            features.append(
                ExtractedFeature(
                    name="correction_magnitude",
                    value=float(correction_magnitude),
                    feature_type=FeatureType.NUMERICAL,
                    confidence=1.0,
                    metadata={"source": "feedback", "type": "correction_magnitude"}
                )
            )
        
        # Temporal features
        if feedback.feedback_timestamp:
            features.extend(self._extract_temporal_features(feedback.feedback_timestamp, "feedback"))
        
        # Create feature set
        feature_set = FeatureSet(
            entity_id=f"feedback_{feedback.id}",
            entity_type="feedback",
            features=features,
            extraction_timestamp=datetime.utcnow(),
            feature_hash=self._compute_feature_hash(features)
        )
        
        return feature_set
    
    async def validate_features(self, feature_set: FeatureSet) -> Tuple[bool, List[str]]:
        """Validate extracted features for quality and completeness."""
        errors = []
        
        # Check for required features
        required_features = ["risk_score", "confidence_score"]
        feature_names = {f.name for f in feature_set.features}
        
        for required in required_features:
            if required not in feature_names:
                errors.append(f"Missing required feature: {required}")
        
        # Check for feature value ranges
        for feature in feature_set.features:
            if feature.feature_type == FeatureType.NUMERICAL:
                if not isinstance(feature.value, (int, float)):
                    errors.append(f"Feature {feature.name} should be numerical but got {type(feature.value)}")
                elif np.isnan(feature.value) or np.isinf(feature.value):
                    errors.append(f"Feature {feature.name} has invalid numerical value: {feature.value}")
        
        # Check confidence scores
        for feature in feature_set.features:
            if not 0.0 <= feature.confidence <= 1.0:
                errors.append(f"Feature {feature.name} has invalid confidence: {feature.confidence}")
        
        return len(errors) == 0, errors
    
    async def normalize_features(self, feature_set: FeatureSet) -> FeatureSet:
        """Normalize features for consistent ML model input."""
        normalized_features = []
        
        for feature in feature_set.features:
            if feature.feature_type == FeatureType.NUMERICAL:
                # Apply min-max normalization for known ranges
                normalized_value = self._normalize_numerical_feature(feature.name, feature.value)
                normalized_features.append(
                    ExtractedFeature(
                        name=feature.name,
                        value=normalized_value,
                        feature_type=feature.feature_type,
                        confidence=feature.confidence,
                        metadata={**feature.metadata, "normalized": True}
                    )
                )
            else:
                # Keep non-numerical features as-is
                normalized_features.append(feature)
        
        return FeatureSet(
            entity_id=feature_set.entity_id,
            entity_type=feature_set.entity_type,
            features=normalized_features,
            extraction_timestamp=feature_set.extraction_timestamp,
            feature_hash=self._compute_feature_hash(normalized_features)
        )
    
    def _normalize_numerical_feature(self, feature_name: str, value: float) -> float:
        """Normalize a numerical feature based on known ranges."""
        normalization_ranges = {
            "risk_score": (0, 100),
            "confidence_score": (0, 100),
            "credibility_score": (0, 1),
            "total_sources": (0, 50),  # Reasonable upper bound
            "processing_time_seconds": (0, 300),  # 5 minutes max
            "creation_hour": (0, 23),
            "creation_day_of_week": (0, 6),
            "impact_areas_count": (0, 10),
            "insights_count": (0, 20),
            "source_diversity": (0, 10)
        }
        
        if feature_name in normalization_ranges:
            min_val, max_val = normalization_ranges[feature_name]
            # Min-max normalization to [0, 1]
            normalized = (value - min_val) / (max_val - min_val)
            return max(0.0, min(1.0, normalized))  # Clamp to [0, 1]
        
        # For unknown features, return as-is
        return value
    
    async def cache_features(self, feature_set: FeatureSet) -> None:
        """Cache extracted features for reuse."""
        cache_key = f"{feature_set.entity_type}_{feature_set.entity_id}"
        self.feature_cache[cache_key] = feature_set
        
        # Clean up old cache entries
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, cached_set in self.feature_cache.items()
            if current_time - cached_set.extraction_timestamp > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.feature_cache[key]
    
    async def get_cached_features(self, entity_type: str, entity_id: str) -> Optional[FeatureSet]:
        """Retrieve cached features if available and not expired."""
        cache_key = f"{entity_type}_{entity_id}"
        
        if cache_key in self.feature_cache:
            cached_set = self.feature_cache[cache_key]
            if datetime.utcnow() - cached_set.extraction_timestamp <= self.cache_ttl:
                return cached_set
            else:
                # Remove expired entry
                del self.feature_cache[cache_key]
        
        return None
    
    async def extract_batch_features(
        self, 
        entity_type: str, 
        entity_ids: List[str],
        use_cache: bool = True
    ) -> List[FeatureSet]:
        """Extract features for multiple entities in batch."""
        feature_sets = []
        
        for entity_id in entity_ids:
            try:
                # Check cache first
                if use_cache:
                    cached_features = await self.get_cached_features(entity_type, entity_id)
                    if cached_features:
                        feature_sets.append(cached_features)
                        continue
                
                # Extract features based on entity type
                if entity_type == "impact_card":
                    result = await self.db.execute(
                        select(ImpactCard).where(ImpactCard.id == int(entity_id))
                    )
                    entity = result.scalar_one_or_none()
                    if entity:
                        feature_set = await self.extract_impact_card_features(entity)
                        feature_sets.append(feature_set)
                        if use_cache:
                            await self.cache_features(feature_set)
                
                elif entity_type == "feedback":
                    result = await self.db.execute(
                        select(FeedbackRecord).where(FeedbackRecord.id == int(entity_id))
                    )
                    entity = result.scalar_one_or_none()
                    if entity:
                        feature_set = await self.extract_feedback_features(entity)
                        feature_sets.append(feature_set)
                        if use_cache:
                            await self.cache_features(feature_set)
                
            except Exception as e:
                logger.error(f"Failed to extract features for {entity_type} {entity_id}: {e}")
                continue
        
        return feature_sets