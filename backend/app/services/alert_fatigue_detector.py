"""Alert fatigue detection and threshold suggestion service."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.orm import selectinload
import logging
import numpy as np
from collections import defaultdict, Counter
from dataclasses import dataclass

from app.models.user_behavior import (
    UserAction, BehaviorPattern, AlertFatigueMetric, LearningLoopState
)
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class FatigueIndicators:
    """Data class for fatigue indicators."""
    dismissal_rate: float
    consecutive_dismissals: int
    response_time_trend: str  # "increasing", "stable", "decreasing"
    engagement_score: float
    is_fatigued: bool
    confidence: float


@dataclass
class ThresholdSuggestion:
    """Data class for threshold adjustment suggestions."""
    current_threshold: Optional[float]
    suggested_threshold: float
    adjustment_type: str  # "increase", "decrease", "maintain"
    confidence: float
    reason: str
    expected_impact: str


class AlertFatigueDetector:
    """Service for detecting alert fatigue and suggesting threshold adjustments."""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        
        # Fatigue detection thresholds
        self.high_dismissal_threshold = 0.75
        self.consecutive_dismissal_threshold = 5
        self.low_engagement_threshold = 0.3
        self.response_time_increase_threshold = 1.5  # 50% increase
        
        # Threshold suggestion parameters
        self.min_actions_for_suggestion = 20
        self.suggestion_confidence_threshold = 0.6
    
    async def detect_alert_fatigue(
        self, 
        user_id: str, 
        period_days: int = 7
    ) -> FatigueIndicators:
        """Detect if a user is experiencing alert fatigue."""
        
        try:
            period_start = datetime.utcnow() - timedelta(days=period_days)
            
            # Get recent alert-related actions
            alert_actions = await self._get_alert_actions(user_id, period_start)
            
            if len(alert_actions) < 5:
                # Not enough data for fatigue detection
                return FatigueIndicators(
                    dismissal_rate=0.0,
                    consecutive_dismissals=0,
                    response_time_trend="stable",
                    engagement_score=1.0,
                    is_fatigued=False,
                    confidence=0.0
                )
            
            # Calculate fatigue indicators
            dismissal_rate = self._calculate_dismissal_rate(alert_actions)
            consecutive_dismissals = self._calculate_consecutive_dismissals(alert_actions)
            response_time_trend = self._analyze_response_time_trend(alert_actions)
            engagement_score = self._calculate_engagement_score(alert_actions)
            
            # Determine if user is fatigued
            is_fatigued, confidence = self._determine_fatigue_status(
                dismissal_rate, consecutive_dismissals, response_time_trend, engagement_score
            )
            
            indicators = FatigueIndicators(
                dismissal_rate=dismissal_rate,
                consecutive_dismissals=consecutive_dismissals,
                response_time_trend=response_time_trend,
                engagement_score=engagement_score,
                is_fatigued=is_fatigued,
                confidence=confidence
            )
            
            # Store fatigue metrics
            await self._store_fatigue_metrics(user_id, period_start, indicators, alert_actions)
            
            logger.info(f"Fatigue detection for user {user_id}: fatigued={is_fatigued}, confidence={confidence:.2f}")
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to detect alert fatigue for user {user_id}: {e}")
            return FatigueIndicators(
                dismissal_rate=0.0,
                consecutive_dismissals=0,
                response_time_trend="stable",
                engagement_score=1.0,
                is_fatigued=False,
                confidence=0.0
            )
    
    async def suggest_threshold_adjustment(
        self, 
        user_id: str, 
        current_threshold: Optional[float] = None
    ) -> Optional[ThresholdSuggestion]:
        """Suggest threshold adjustments based on user behavior patterns."""
        
        try:
            # Get user's behavior patterns and recent actions
            patterns = await self._get_user_patterns(user_id)
            recent_actions = await self._get_alert_actions(user_id, datetime.utcnow() - timedelta(days=30))
            
            if len(recent_actions) < self.min_actions_for_suggestion:
                logger.info(f"Insufficient actions for threshold suggestion: {len(recent_actions)} for user {user_id}")
                return None
            
            # Analyze current behavior
            dismissal_rate = self._calculate_dismissal_rate(recent_actions)
            action_rate = self._calculate_action_rate(recent_actions)
            
            # Get fatigue indicators
            fatigue_indicators = await self.detect_alert_fatigue(user_id)
            
            # Determine threshold adjustment
            suggestion = self._calculate_threshold_suggestion(
                current_threshold, dismissal_rate, action_rate, fatigue_indicators, patterns
            )
            
            if suggestion and suggestion.confidence >= self.suggestion_confidence_threshold:
                logger.info(f"Threshold suggestion for user {user_id}: {suggestion.adjustment_type} to {suggestion.suggested_threshold}")
                return suggestion
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to suggest threshold adjustment for user {user_id}: {e}")
            return None
    
    async def _get_alert_actions(self, user_id: str, since: datetime) -> List[UserAction]:
        """Get alert-related actions for a user since a specific date."""
        
        query = select(UserAction).where(
            and_(
                UserAction.user_id == user_id,
                UserAction.target_type.in_(["alert", "impact_card", "notification"]),
                UserAction.timestamp >= since
            )
        ).order_by(UserAction.timestamp)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def _get_user_patterns(self, user_id: str) -> List[BehaviorPattern]:
        """Get user's behavior patterns."""
        
        query = select(BehaviorPattern).where(BehaviorPattern.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    def _calculate_dismissal_rate(self, actions: List[UserAction]) -> float:
        """Calculate the rate of alert dismissals."""
        
        if not actions:
            return 0.0
        
        dismissals = len([a for a in actions if a.action_type == "dismiss"])
        return dismissals / len(actions)
    
    def _calculate_action_rate(self, actions: List[UserAction]) -> float:
        """Calculate the rate of meaningful actions (not dismissals)."""
        
        if not actions:
            return 0.0
        
        meaningful_actions = len([a for a in actions if a.action_type in ["act", "escalate", "share"]])
        return meaningful_actions / len(actions)
    
    def _calculate_consecutive_dismissals(self, actions: List[UserAction]) -> int:
        """Calculate the maximum consecutive dismissals."""
        
        if not actions:
            return 0
        
        # Sort by timestamp
        sorted_actions = sorted(actions, key=lambda x: x.timestamp)
        
        max_consecutive = 0
        current_consecutive = 0
        
        for action in sorted_actions:
            if action.action_type == "dismiss":
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def _analyze_response_time_trend(self, actions: List[UserAction]) -> str:
        """Analyze if response times are increasing, decreasing, or stable."""
        
        # Filter actions with response times
        timed_actions = [a for a in actions if a.response_time_ms is not None]
        
        if len(timed_actions) < 5:
            return "stable"
        
        # Sort by timestamp and calculate trend
        sorted_actions = sorted(timed_actions, key=lambda x: x.timestamp)
        response_times = [a.response_time_ms for a in sorted_actions]
        
        # Simple trend analysis: compare first half vs second half
        mid_point = len(response_times) // 2
        first_half_avg = np.mean(response_times[:mid_point])
        second_half_avg = np.mean(response_times[mid_point:])
        
        if second_half_avg > first_half_avg * self.response_time_increase_threshold:
            return "increasing"
        elif first_half_avg > second_half_avg * self.response_time_increase_threshold:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_engagement_score(self, actions: List[UserAction]) -> float:
        """Calculate overall engagement score (0-1, higher = more engaged)."""
        
        if not actions:
            return 1.0
        
        # Weight different action types
        action_weights = {
            "dismiss": 0.0,
            "view": 0.2,
            "act": 1.0,
            "escalate": 0.8,
            "share": 0.9,
            "comment": 0.7
        }
        
        total_weight = 0
        total_actions = len(actions)
        
        for action in actions:
            weight = action_weights.get(action.action_type, 0.5)
            total_weight += weight
        
        # Normalize to 0-1 scale
        max_possible_weight = total_actions * 1.0  # If all actions were "act"
        engagement_score = total_weight / max_possible_weight if max_possible_weight > 0 else 0
        
        return min(max(engagement_score, 0.0), 1.0)
    
    def _determine_fatigue_status(
        self, 
        dismissal_rate: float, 
        consecutive_dismissals: int, 
        response_time_trend: str, 
        engagement_score: float
    ) -> Tuple[bool, float]:
        """Determine if user is fatigued and confidence level."""
        
        fatigue_indicators = 0
        confidence_factors = []
        
        # High dismissal rate
        if dismissal_rate >= self.high_dismissal_threshold:
            fatigue_indicators += 1
            confidence_factors.append(dismissal_rate)
        
        # Too many consecutive dismissals
        if consecutive_dismissals >= self.consecutive_dismissal_threshold:
            fatigue_indicators += 1
            confidence_factors.append(min(consecutive_dismissals / 10, 1.0))
        
        # Increasing response times
        if response_time_trend == "increasing":
            fatigue_indicators += 1
            confidence_factors.append(0.7)
        
        # Low engagement
        if engagement_score <= self.low_engagement_threshold:
            fatigue_indicators += 1
            confidence_factors.append(1.0 - engagement_score)
        
        # Determine fatigue status
        is_fatigued = fatigue_indicators >= 2  # Need at least 2 indicators
        
        # Calculate confidence
        if confidence_factors:
            confidence = np.mean(confidence_factors)
        else:
            confidence = 0.0
        
        return is_fatigued, confidence
    
    def _calculate_threshold_suggestion(
        self,
        current_threshold: Optional[float],
        dismissal_rate: float,
        action_rate: float,
        fatigue_indicators: FatigueIndicators,
        patterns: List[BehaviorPattern]
    ) -> Optional[ThresholdSuggestion]:
        """Calculate threshold adjustment suggestion."""
        
        # Default threshold if not provided
        if current_threshold is None:
            current_threshold = 0.7
        
        suggested_threshold = current_threshold
        adjustment_type = "maintain"
        reason = "Current threshold appears appropriate"
        confidence = 0.5
        expected_impact = "No change expected"
        
        # High dismissal rate suggests threshold should be increased
        if dismissal_rate > 0.8:
            suggested_threshold = min(current_threshold + 0.1, 0.95)
            adjustment_type = "increase"
            reason = f"High dismissal rate ({dismissal_rate:.1%}) indicates too many low-value alerts"
            confidence = min(dismissal_rate, 0.9)
            expected_impact = f"Reduce alerts by ~{int((suggested_threshold - current_threshold) * 100)}%"
        
        # Very low dismissal rate with high action rate suggests threshold could be lowered
        elif dismissal_rate < 0.2 and action_rate > 0.6:
            suggested_threshold = max(current_threshold - 0.1, 0.3)
            adjustment_type = "decrease"
            reason = f"Low dismissal rate ({dismissal_rate:.1%}) and high action rate ({action_rate:.1%}) suggest missing valuable alerts"
            confidence = min(action_rate, 0.8)
            expected_impact = f"Increase alerts by ~{int((current_threshold - suggested_threshold) * 100)}%"
        
        # Alert fatigue detected
        elif fatigue_indicators.is_fatigued:
            suggested_threshold = min(current_threshold + 0.15, 0.9)
            adjustment_type = "increase"
            reason = f"Alert fatigue detected (confidence: {fatigue_indicators.confidence:.1%})"
            confidence = fatigue_indicators.confidence
            expected_impact = "Reduce alert volume to prevent burnout"
        
        # Check behavior patterns for additional insights
        alert_patterns = [p for p in patterns if p.pattern_type == "alert_response"]
        if alert_patterns:
            pattern = alert_patterns[0]
            if pattern.suggested_threshold and pattern.threshold_confidence > confidence:
                suggested_threshold = pattern.suggested_threshold
                confidence = pattern.threshold_confidence
                reason += f" (reinforced by behavior pattern analysis)"
        
        # Only suggest if there's meaningful change
        if abs(suggested_threshold - current_threshold) < 0.05:
            adjustment_type = "maintain"
            suggested_threshold = current_threshold
        
        return ThresholdSuggestion(
            current_threshold=current_threshold,
            suggested_threshold=suggested_threshold,
            adjustment_type=adjustment_type,
            confidence=confidence,
            reason=reason,
            expected_impact=expected_impact
        )
    
    async def _store_fatigue_metrics(
        self,
        user_id: str,
        period_start: datetime,
        indicators: FatigueIndicators,
        actions: List[UserAction]
    ):
        """Store fatigue metrics in the database."""
        
        try:
            period_end = datetime.utcnow()
            
            # Calculate alert counts
            alerts_received = len(actions)
            alerts_dismissed = len([a for a in actions if a.action_type == "dismiss"])
            alerts_acted_upon = len([a for a in actions if a.action_type == "act"])
            alerts_escalated = len([a for a in actions if a.action_type == "escalate"])
            
            # Calculate time to first action
            time_to_first_action = None
            if actions:
                first_action = min(actions, key=lambda x: x.timestamp)
                if first_action.response_time_ms:
                    time_to_first_action = first_action.response_time_ms / 1000
            
            # Create fatigue metric record
            fatigue_metric = AlertFatigueMetric(
                user_id=user_id,
                period_start=period_start,
                period_end=period_end,
                period_type="weekly",
                alerts_received=alerts_received,
                alerts_dismissed=alerts_dismissed,
                alerts_acted_upon=alerts_acted_upon,
                alerts_escalated=alerts_escalated,
                dismissal_rate=indicators.dismissal_rate,
                consecutive_dismissals=indicators.consecutive_dismissals,
                time_to_first_action=time_to_first_action,
                engagement_score=indicators.engagement_score,
                is_fatigue_detected=indicators.is_fatigued,
                created_at=datetime.utcnow()
            )
            
            self.db.add(fatigue_metric)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to store fatigue metrics for user {user_id}: {e}")
            await self.db.rollback()
    
    async def get_fatigue_history(
        self, 
        user_id: str, 
        days: int = 30
    ) -> List[AlertFatigueMetric]:
        """Get fatigue history for a user."""
        
        since = datetime.utcnow() - timedelta(days=days)
        
        query = select(AlertFatigueMetric).where(
            and_(
                AlertFatigueMetric.user_id == user_id,
                AlertFatigueMetric.period_start >= since
            )
        ).order_by(desc(AlertFatigueMetric.period_start))
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_threshold_suggestions_for_all_users(self) -> Dict[str, ThresholdSuggestion]:
        """Get threshold suggestions for all users with sufficient data."""
        
        try:
            # Get all users with recent actions
            since = datetime.utcnow() - timedelta(days=30)
            
            query = select(UserAction.user_id).where(
                and_(
                    UserAction.timestamp >= since,
                    UserAction.target_type.in_(["alert", "impact_card", "notification"])
                )
            ).group_by(UserAction.user_id).having(func.count(UserAction.id) >= self.min_actions_for_suggestion)
            
            result = await self.db.execute(query)
            user_ids = [row[0] for row in result.fetchall()]
            
            suggestions = {}
            
            for user_id in user_ids:
                suggestion = await self.suggest_threshold_adjustment(user_id)
                if suggestion:
                    suggestions[user_id] = suggestion
            
            logger.info(f"Generated threshold suggestions for {len(suggestions)} users")
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get threshold suggestions for all users: {e}")
            return {}