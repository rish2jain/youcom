"""Behavior pattern analysis service for user learning loop."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.orm import selectinload
import logging
import numpy as np
from collections import defaultdict, Counter
import json

from app.models.user_behavior import (
    UserAction, BehaviorPattern, AlertFatigueMetric, LearningLoopState
)
from app.models.user import User

logger = logging.getLogger(__name__)


class BehaviorPatternAnalyzer:
    """Service for analyzing user behavior patterns and clustering similar behaviors."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.min_actions_for_pattern = 5
        self.pattern_confidence_threshold = 0.6
    
    async def analyze_user_patterns(self, user_id: str) -> List[BehaviorPattern]:
        """Comprehensive analysis of user behavior patterns."""
        
        try:
            # Get user actions from the last 30 days
            since = datetime.utcnow() - timedelta(days=30)
            actions = await self._get_user_actions(user_id, since)
            
            if len(actions) < self.min_actions_for_pattern:
                logger.info(f"Insufficient actions for pattern analysis: {len(actions)} for user {user_id}")
                return []
            
            patterns = []
            
            # Analyze temporal patterns
            temporal_pattern = await self._analyze_temporal_patterns(user_id, actions)
            if temporal_pattern:
                patterns.append(temporal_pattern)
            
            # Analyze response time patterns
            response_pattern = await self._analyze_response_time_patterns(user_id, actions)
            if response_pattern:
                patterns.append(response_pattern)
            
            # Analyze content preference patterns
            content_patterns = await self._analyze_content_preferences(user_id, actions)
            patterns.extend(content_patterns)
            
            # Analyze sequential behavior patterns
            sequential_patterns = await self._analyze_sequential_patterns(user_id, actions)
            patterns.extend(sequential_patterns)
            
            logger.info(f"Identified {len(patterns)} behavior patterns for user {user_id}")
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze user patterns for {user_id}: {e}")
            return []
    
    async def cluster_similar_behaviors(self, user_ids: List[str]) -> Dict[str, List[str]]:
        """Cluster users with similar behavior patterns."""
        
        try:
            user_features = {}
            
            # Extract behavior features for each user
            for user_id in user_ids:
                features = await self._extract_behavior_features(user_id)
                if features:
                    user_features[user_id] = features
            
            if len(user_features) < 2:
                return {}
            
            # Simple clustering based on behavior similarity
            clusters = self._perform_behavior_clustering(user_features)
            
            logger.info(f"Created {len(clusters)} behavior clusters from {len(user_ids)} users")
            return clusters
            
        except Exception as e:
            logger.error(f"Failed to cluster user behaviors: {e}")
            return {}
    
    async def _get_user_actions(self, user_id: str, since: datetime) -> List[UserAction]:
        """Get user actions since a specific date."""
        
        query = select(UserAction).where(
            and_(
                UserAction.user_id == user_id,
                UserAction.timestamp >= since
            )
        ).order_by(UserAction.timestamp)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _analyze_temporal_patterns(self, user_id: str, actions: List[UserAction]) -> Optional[BehaviorPattern]:
        """Analyze when users are most active and responsive."""
        
        if len(actions) < 10:
            return None
        
        # Extract hour and day patterns
        hours = [action.timestamp.hour for action in actions]
        days = [action.timestamp.weekday() for action in actions]  # 0=Monday, 6=Sunday
        
        # Find peak activity hours
        hour_counts = Counter(hours)
        peak_hours = [hour for hour, count in hour_counts.most_common(3)]
        
        # Find peak activity days
        day_counts = Counter(days)
        peak_days = [day for day, count in day_counts.most_common(3)]
        
        # Calculate activity distribution consistency
        hour_distribution = np.array(list(hour_counts.values()))
        hour_consistency = 1 - (np.std(hour_distribution) / np.mean(hour_distribution)) if np.mean(hour_distribution) > 0 else 0
        
        # Calculate pattern strength
        pattern_strength = min(max(hour_consistency, 0.0), 1.0)
        
        # Create or update temporal pattern
        pattern = await self._get_or_create_pattern(
            user_id=user_id,
            pattern_type="temporal_activity",
            target_type="general"
        )
        
        pattern.total_interactions = len(actions)
        pattern.peak_activity_hours = peak_hours
        pattern.pattern_strength = pattern_strength
        pattern.context = {
            "peak_days": peak_days,
            "hour_distribution": dict(hour_counts),
            "day_distribution": dict(day_counts),
            "consistency_score": hour_consistency
        }
        
        await self.db.commit()
        return pattern
    
    async def _analyze_response_time_patterns(self, user_id: str, actions: List[UserAction]) -> Optional[BehaviorPattern]:
        """Analyze user response time patterns."""
        
        # Filter actions with response times
        timed_actions = [a for a in actions if a.response_time_ms is not None]
        
        if len(timed_actions) < 5:
            return None
        
        response_times = [a.response_time_ms / 1000 for a in timed_actions]  # Convert to seconds
        
        # Calculate response time statistics
        avg_response_time = np.mean(response_times)
        median_response_time = np.median(response_times)
        std_response_time = np.std(response_times)
        
        # Categorize response speed
        if avg_response_time < 5:
            speed_category = "fast"
        elif avg_response_time < 30:
            speed_category = "moderate"
        else:
            speed_category = "slow"
        
        # Calculate consistency (lower std relative to mean = more consistent)
        consistency = 1 - min(std_response_time / avg_response_time, 1.0) if avg_response_time > 0 else 0
        
        # Create or update response time pattern
        pattern = await self._get_or_create_pattern(
            user_id=user_id,
            pattern_type="response_time",
            target_type="general"
        )
        
        pattern.total_interactions = len(timed_actions)
        pattern.average_response_time = avg_response_time
        pattern.pattern_strength = consistency
        pattern.context = {
            "median_response_time": median_response_time,
            "std_response_time": std_response_time,
            "speed_category": speed_category,
            "consistency_score": consistency
        }
        
        await self.db.commit()
        return pattern
    
    async def _analyze_content_preferences(self, user_id: str, actions: List[UserAction]) -> List[BehaviorPattern]:
        """Analyze user preferences for different content types."""
        
        patterns = []
        
        # Group actions by target type
        target_groups = defaultdict(list)
        for action in actions:
            target_groups[action.target_type].append(action)
        
        for target_type, target_actions in target_groups.items():
            if len(target_actions) < 3:
                continue
            
            # Calculate engagement metrics
            total_actions = len(target_actions)
            dismissals = len([a for a in target_actions if a.action_type == "dismiss"])
            engagements = len([a for a in target_actions if a.action_type in ["act", "escalate", "share"]])
            
            dismissal_rate = dismissals / total_actions if total_actions > 0 else 0
            engagement_rate = engagements / total_actions if total_actions > 0 else 0
            
            # Determine preference strength
            if dismissal_rate > 0.7:
                preference = "low"
                strength = dismissal_rate
            elif engagement_rate > 0.5:
                preference = "high"
                strength = engagement_rate
            else:
                preference = "neutral"
                strength = 0.5
            
            # Create or update content preference pattern
            pattern = await self._get_or_create_pattern(
                user_id=user_id,
                pattern_type="content_preference",
                target_type=target_type
            )
            
            pattern.total_interactions = total_actions
            pattern.dismissal_rate = dismissal_rate
            pattern.action_rate = engagement_rate
            pattern.pattern_strength = strength
            pattern.context = {
                "preference_level": preference,
                "engagement_types": Counter([a.action_type for a in target_actions])
            }
            
            patterns.append(pattern)
        
        await self.db.commit()
        return patterns
    
    async def _analyze_sequential_patterns(self, user_id: str, actions: List[UserAction]) -> List[BehaviorPattern]:
        """Analyze sequential behavior patterns (action chains)."""
        
        if len(actions) < 10:
            return []
        
        patterns = []
        
        # Sort actions by timestamp
        sorted_actions = sorted(actions, key=lambda x: x.timestamp)
        
        # Find common action sequences
        sequences = []
        window_size = 3  # Look at sequences of 3 actions
        
        for i in range(len(sorted_actions) - window_size + 1):
            window = sorted_actions[i:i + window_size]
            
            # Check if actions are within reasonable time window (1 hour)
            time_span = window[-1].timestamp - window[0].timestamp
            if time_span <= timedelta(hours=1):
                sequence = tuple(a.action_type for a in window)
                sequences.append(sequence)
        
        # Find most common sequences
        sequence_counts = Counter(sequences)
        common_sequences = sequence_counts.most_common(5)
        
        for sequence, count in common_sequences:
            if count < 3:  # Need at least 3 occurrences
                continue
            
            sequence_str = " -> ".join(sequence)
            frequency = count / len(sequences) if sequences else 0
            
            # Create sequential pattern
            pattern = await self._get_or_create_pattern(
                user_id=user_id,
                pattern_type="sequential_behavior",
                target_type="sequence"
            )
            
            pattern.total_interactions = count
            pattern.pattern_strength = frequency
            pattern.context = {
                "sequence": sequence,
                "sequence_string": sequence_str,
                "frequency": frequency,
                "total_sequences_analyzed": len(sequences)
            }
            
            patterns.append(pattern)
        
        await self.db.commit()
        return patterns
    
    async def _get_or_create_pattern(
        self, 
        user_id: str, 
        pattern_type: str, 
        target_type: str
    ) -> BehaviorPattern:
        """Get existing pattern or create new one."""
        
        # Try to find existing pattern
        query = select(BehaviorPattern).where(
            and_(
                BehaviorPattern.user_id == user_id,
                BehaviorPattern.pattern_type == pattern_type,
                BehaviorPattern.target_type == target_type
            )
        )
        
        result = await self.db.execute(query)
        existing_pattern = result.scalar_one_or_none()
        
        if existing_pattern:
            existing_pattern.last_updated = datetime.utcnow()
            return existing_pattern
        else:
            # Create new pattern
            new_pattern = BehaviorPattern(
                user_id=user_id,
                pattern_type=pattern_type,
                target_type=target_type,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            self.db.add(new_pattern)
            await self.db.flush()  # Get the ID
            return new_pattern
    
    async def _extract_behavior_features(self, user_id: str) -> Optional[Dict[str, float]]:
        """Extract numerical features representing user behavior."""
        
        try:
            # Get user's behavior patterns
            query = select(BehaviorPattern).where(BehaviorPattern.user_id == user_id)
            result = await self.db.execute(query)
            patterns = result.scalars().all()
            
            if not patterns:
                return None
            
            features = {
                "avg_dismissal_rate": 0.0,
                "avg_action_rate": 0.0,
                "avg_escalation_rate": 0.0,
                "avg_response_time": 0.0,
                "pattern_consistency": 0.0,
                "content_diversity": 0.0,
                "temporal_consistency": 0.0
            }
            
            # Calculate average rates
            dismissal_rates = [p.dismissal_rate for p in patterns if p.dismissal_rate is not None]
            action_rates = [p.action_rate for p in patterns if p.action_rate is not None]
            escalation_rates = [p.escalation_rate for p in patterns if p.escalation_rate is not None]
            response_times = [p.average_response_time for p in patterns if p.average_response_time is not None]
            pattern_strengths = [p.pattern_strength for p in patterns if p.pattern_strength is not None]
            
            if dismissal_rates:
                features["avg_dismissal_rate"] = np.mean(dismissal_rates)
            if action_rates:
                features["avg_action_rate"] = np.mean(action_rates)
            if escalation_rates:
                features["avg_escalation_rate"] = np.mean(escalation_rates)
            if response_times:
                features["avg_response_time"] = np.mean(response_times)
            if pattern_strengths:
                features["pattern_consistency"] = np.mean(pattern_strengths)
            
            # Calculate content diversity (how many different content types user engages with)
            content_types = set(p.target_type for p in patterns)
            features["content_diversity"] = len(content_types) / 10.0  # Normalize to 0-1
            
            # Find temporal consistency pattern
            temporal_patterns = [p for p in patterns if p.pattern_type == "temporal_activity"]
            if temporal_patterns:
                features["temporal_consistency"] = temporal_patterns[0].pattern_strength
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to extract behavior features for user {user_id}: {e}")
            return None
    
    def _perform_behavior_clustering(self, user_features: Dict[str, Dict[str, float]]) -> Dict[str, List[str]]:
        """Perform simple clustering of users based on behavior features."""
        
        try:
            # Convert features to numpy array
            user_ids = list(user_features.keys())
            feature_names = list(next(iter(user_features.values())).keys())
            
            feature_matrix = np.array([
                [user_features[user_id][feature] for feature in feature_names]
                for user_id in user_ids
            ])
            
            # Simple k-means-like clustering
            clusters = self._simple_kmeans(feature_matrix, k=min(3, len(user_ids)))
            
            # Group users by cluster
            clustered_users = defaultdict(list)
            for i, user_id in enumerate(user_ids):
                cluster_id = f"cluster_{clusters[i]}"
                clustered_users[cluster_id].append(user_id)
            
            return dict(clustered_users)
            
        except Exception as e:
            logger.error(f"Failed to perform behavior clustering: {e}")
            return {}
    
    def _simple_kmeans(self, data: np.ndarray, k: int, max_iters: int = 10) -> List[int]:
        """Simple k-means clustering implementation."""
        
        if len(data) <= k:
            return list(range(len(data)))
        
        # Initialize centroids randomly
        n_features = data.shape[1]
        centroids = np.random.rand(k, n_features)
        
        for _ in range(max_iters):
            # Assign points to closest centroid
            distances = np.sqrt(((data - centroids[:, np.newaxis])**2).sum(axis=2))
            assignments = np.argmin(distances, axis=0)
            
            # Update centroids
            new_centroids = np.array([
                data[assignments == i].mean(axis=0) if np.any(assignments == i) else centroids[i]
                for i in range(k)
            ])
            
            # Check for convergence
            if np.allclose(centroids, new_centroids):
                break
            
            centroids = new_centroids
        
        return assignments.tolist()
    
    async def get_similar_users(self, user_id: str, limit: int = 5) -> List[str]:
        """Find users with similar behavior patterns."""
        
        try:
            # Get all users with behavior patterns
            query = select(BehaviorPattern.user_id).distinct()
            result = await self.db.execute(query)
            all_user_ids = [row[0] for row in result.fetchall()]
            
            if user_id not in all_user_ids:
                return []
            
            # Cluster users
            clusters = await self.cluster_similar_behaviors(all_user_ids)
            
            # Find which cluster the target user belongs to
            target_cluster = None
            for cluster_id, users in clusters.items():
                if user_id in users:
                    target_cluster = cluster_id
                    break
            
            if not target_cluster:
                return []
            
            # Return other users in the same cluster
            similar_users = [uid for uid in clusters[target_cluster] if uid != user_id]
            return similar_users[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar users for {user_id}: {e}")
            return []