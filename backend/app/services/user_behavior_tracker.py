"""User behavior tracking service for learning loop functionality."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
import logging
import json

from app.models.user_behavior import (
    UserAction, BehaviorPattern, AlertFatigueMetric, LearningLoopState
)
from app.models.user import User

logger = logging.getLogger(__name__)


class UserBehaviorTracker:
    """Service for tracking and analyzing user behavior patterns."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def record_action(
        self,
        user_id: str,
        session_id: str,
        action_type: str,
        target_type: str,
        target_id: str,
        context: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        outcome: Optional[str] = None,
        confidence: Optional[float] = None,
        response_time_ms: Optional[int] = None,
        page_load_time_ms: Optional[int] = None
    ) -> UserAction:
        """Record a user action for behavior analysis."""
        
        try:
            action = UserAction(
                user_id=user_id,
                session_id=session_id,
                action_type=action_type,
                target_type=target_type,
                target_id=target_id,
                context=context or {},
                reason=reason,
                outcome=outcome,
                confidence=confidence,
                response_time_ms=response_time_ms,
                page_load_time_ms=page_load_time_ms,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(action)
            await self.db.commit()
            await self.db.refresh(action)
            
            # Update learning loop state synchronously within the request context
            await self._update_learning_state(user_id)
            
            logger.info(f"Recorded user action: {action_type} on {target_type} by user {user_id}")
            return action
            
        except Exception as e:
            logger.error(f"Failed to record user action: {e}")
            await self.db.rollback()
            raise
    
    async def get_user_actions(
        self,
        user_id: str,
        action_type: Optional[str] = None,
        target_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[UserAction]:
        """Retrieve user actions with optional filtering."""
        
        query = select(UserAction).where(UserAction.user_id == user_id)
        
        if action_type:
            query = query.where(UserAction.action_type == action_type)
        
        if target_type:
            query = query.where(UserAction.target_type == target_type)
        
        if since:
            query = query.where(UserAction.timestamp >= since)
        
        query = query.order_by(desc(UserAction.timestamp)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def analyze_behavior_patterns(self, user_id: str) -> List[BehaviorPattern]:
        """Analyze user behavior and update/create behavior patterns."""
        
        try:
            # Get recent actions (last 30 days)
            since = datetime.utcnow() - timedelta(days=30)
            actions = await self.get_user_actions(user_id, since=since, limit=1000)
            
            if len(actions) < 5:  # Need minimum actions for pattern analysis
                logger.info(f"Insufficient actions for pattern analysis: {len(actions)} for user {user_id}")
                return []
            
            patterns = []
            
            # Analyze patterns by target type
            target_types = set(action.target_type for action in actions)
            
            for target_type in target_types:
                pattern = await self._analyze_target_type_pattern(user_id, target_type, actions)
                if pattern:
                    patterns.append(pattern)
            
            # Analyze overall alert response patterns
            alert_pattern = await self._analyze_alert_response_pattern(user_id, actions)
            if alert_pattern:
                patterns.append(alert_pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze behavior patterns for user {user_id}: {e}")
            return []
    
    async def _analyze_target_type_pattern(
        self, 
        user_id: str, 
        target_type: str, 
        actions: List[UserAction]
    ) -> Optional[BehaviorPattern]:
        """Analyze behavior pattern for a specific target type."""
        
        # Filter actions for this target type
        target_actions = [a for a in actions if a.target_type == target_type]
        
        if len(target_actions) < 3:
            return None
        
        # Calculate metrics
        total_interactions = len(target_actions)
        dismissals = len([a for a in target_actions if a.action_type == "dismiss"])
        actions_taken = len([a for a in target_actions if a.action_type == "act"])
        escalations = len([a for a in target_actions if a.action_type == "escalate"])
        
        dismissal_rate = dismissals / total_interactions if total_interactions > 0 else 0
        action_rate = actions_taken / total_interactions if total_interactions > 0 else 0
        escalation_rate = escalations / total_interactions if total_interactions > 0 else 0
        
        # Calculate average response time
        response_times = [a.response_time_ms for a in target_actions if a.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        avg_response_time_seconds = avg_response_time / 1000 if avg_response_time > 0 else 0
        
        # Calculate peak activity hours
        hours = [a.timestamp.hour for a in target_actions]
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_activity_hours = [hour for hour, count in peak_hours]
        
        # Calculate pattern strength (how consistent the behavior is)
        pattern_strength = self._calculate_pattern_strength(target_actions)
        
        # Check if pattern already exists
        existing_pattern = await self._get_existing_pattern(user_id, "target_behavior", target_type)
        
        if existing_pattern:
            # Update existing pattern
            existing_pattern.total_interactions = total_interactions
            existing_pattern.dismissal_rate = dismissal_rate
            existing_pattern.action_rate = action_rate
            existing_pattern.escalation_rate = escalation_rate
            existing_pattern.average_response_time = avg_response_time_seconds
            existing_pattern.peak_activity_hours = peak_activity_hours
            existing_pattern.pattern_strength = pattern_strength
            existing_pattern.last_updated = datetime.utcnow()
            
            await self.db.commit()
            return existing_pattern
        else:
            # Create new pattern
            pattern = BehaviorPattern(
                user_id=user_id,
                pattern_type="target_behavior",
                target_type=target_type,
                total_interactions=total_interactions,
                dismissal_rate=dismissal_rate,
                action_rate=action_rate,
                escalation_rate=escalation_rate,
                average_response_time=avg_response_time_seconds,
                peak_activity_hours=peak_activity_hours,
                pattern_strength=pattern_strength
            )
            
            self.db.add(pattern)
            await self.db.commit()
            await self.db.refresh(pattern)
            return pattern
    
    async def _analyze_alert_response_pattern(
        self, 
        user_id: str, 
        actions: List[UserAction]
    ) -> Optional[BehaviorPattern]:
        """Analyze overall alert response patterns for threshold suggestions."""
        
        # Filter for alert-related actions
        alert_actions = [a for a in actions if a.target_type in ["alert", "impact_card"]]
        
        if len(alert_actions) < 5:
            return None
        
        # Calculate dismissal patterns
        dismissals = [a for a in alert_actions if a.action_type == "dismiss"]
        dismissal_rate = len(dismissals) / len(alert_actions)
        
        # Analyze dismissal reasons to suggest threshold adjustments
        dismissal_reasons = [a.reason for a in dismissals if a.reason]
        
        # Simple threshold suggestion logic
        suggested_threshold = None
        threshold_confidence = 0.0
        
        if dismissal_rate > 0.7:  # High dismissal rate
            # Suggest increasing threshold to reduce noise
            suggested_threshold = 0.8  # Suggest higher threshold
            threshold_confidence = min(dismissal_rate, 0.9)
        elif dismissal_rate < 0.2:  # Low dismissal rate
            # User finds most alerts useful, could lower threshold
            suggested_threshold = 0.6  # Suggest lower threshold
            threshold_confidence = min(1 - dismissal_rate, 0.8)
        
        # Check for existing alert response pattern
        existing_pattern = await self._get_existing_pattern(user_id, "alert_response", "alert")
        
        pattern_data = {
            "total_interactions": len(alert_actions),
            "dismissal_rate": dismissal_rate,
            "action_rate": len([a for a in alert_actions if a.action_type == "act"]) / len(alert_actions),
            "escalation_rate": len([a for a in alert_actions if a.action_type == "escalate"]) / len(alert_actions),
            "suggested_threshold": suggested_threshold,
            "threshold_confidence": threshold_confidence,
            "pattern_strength": self._calculate_pattern_strength(alert_actions)
        }
        
        if existing_pattern:
            for key, value in pattern_data.items():
                setattr(existing_pattern, key, value)
            existing_pattern.last_updated = datetime.utcnow()
            await self.db.commit()
            return existing_pattern
        else:
            pattern = BehaviorPattern(
                user_id=user_id,
                pattern_type="alert_response",
                target_type="alert",
                **pattern_data
            )
            self.db.add(pattern)
            await self.db.commit()
            await self.db.refresh(pattern)
            return pattern
    
    async def _get_existing_pattern(
        self, 
        user_id: str, 
        pattern_type: str, 
        target_type: str
    ) -> Optional[BehaviorPattern]:
        """Get existing behavior pattern."""
        
        query = select(BehaviorPattern).where(
            and_(
                BehaviorPattern.user_id == user_id,
                BehaviorPattern.pattern_type == pattern_type,
                BehaviorPattern.target_type == target_type
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    def _calculate_pattern_strength(self, actions: List[UserAction]) -> float:
        """Calculate how consistent/strong a behavior pattern is."""
        
        if len(actions) < 3:
            return 0.0
        
        # Simple consistency measure based on action type distribution
        action_types = [a.action_type for a in actions]
        type_counts = {}
        for action_type in action_types:
            type_counts[action_type] = type_counts.get(action_type, 0) + 1
        
        # Calculate entropy (lower entropy = more consistent pattern)
        import math
        total = len(actions)
        entropy = 0.0
        for count in type_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        # Convert to strength score (0-1, higher = stronger pattern)
        max_entropy = math.log2(len(type_counts)) if len(type_counts) > 1 else 1.0
        strength = 1.0 - (entropy / max_entropy) if max_entropy > 0 else 0.0
        
        return min(max(strength, 0.0), 1.0)
    
    async def _update_learning_state(self, user_id: str):
        """Update the learning loop state for a user."""
        
        try:
            # Get or create learning state
            query = select(LearningLoopState).where(LearningLoopState.user_id == user_id)
            result = await self.db.execute(query)
            learning_state = result.scalar_one_or_none()
            
            if not learning_state:
                learning_state = LearningLoopState(user_id=user_id)
                self.db.add(learning_state)
            
            # Update action count
            action_count_query = select(func.count(UserAction.id)).where(UserAction.user_id == user_id)
            action_count_result = await self.db.execute(action_count_query)
            total_actions = action_count_result.scalar() or 0
            
            # Update pattern count
            pattern_count_query = select(func.count(BehaviorPattern.id)).where(BehaviorPattern.user_id == user_id)
            pattern_count_result = await self.db.execute(pattern_count_query)
            patterns_identified = pattern_count_result.scalar() or 0
            
            # Update learning state
            learning_state.total_actions_recorded = total_actions
            learning_state.patterns_identified = patterns_identified
            
            # Determine learning phase
            if total_actions < 10:
                learning_state.learning_phase = "initialization"
                learning_state.confidence_level = 0.0
            elif total_actions < 50:
                learning_state.learning_phase = "learning"
                learning_state.confidence_level = min(total_actions / 50, 0.7)
            else:
                learning_state.learning_phase = "optimizing"
                learning_state.confidence_level = min(0.7 + (patterns_identified * 0.1), 1.0)
            
            learning_state.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update learning state for user {user_id}: {e}")
            await self.db.rollback()
    
    async def get_behavior_patterns(self, user_id: str) -> List[BehaviorPattern]:
        """Get all behavior patterns for a user."""
        
        query = select(BehaviorPattern).where(BehaviorPattern.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_learning_state(self, user_id: str) -> Optional[LearningLoopState]:
        """Get the learning loop state for a user."""
        
        query = select(LearningLoopState).where(LearningLoopState.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()