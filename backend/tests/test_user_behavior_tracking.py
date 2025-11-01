"""Tests for user behavior tracking system."""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.user_behavior import (
    UserAction, BehaviorPattern, AlertFatigueMetric, LearningLoopState
)
from app.services.user_behavior_tracker import UserBehaviorTracker
from app.services.behavior_pattern_analyzer import BehaviorPatternAnalyzer
from app.services.alert_fatigue_detector import AlertFatigueDetector, FatigueIndicators, ThresholdSuggestion


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password",
        role=UserRole.ANALYST,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def behavior_tracker(db_session: AsyncSession) -> UserBehaviorTracker:
    """Create a UserBehaviorTracker instance."""
    return UserBehaviorTracker(db_session)


@pytest.fixture
async def pattern_analyzer(db_session: AsyncSession) -> BehaviorPatternAnalyzer:
    """Create a BehaviorPatternAnalyzer instance."""
    return BehaviorPatternAnalyzer(db_session)


@pytest.fixture
async def fatigue_detector(db_session: AsyncSession) -> AlertFatigueDetector:
    """Create an AlertFatigueDetector instance."""
    return AlertFatigueDetector(db_session)


@pytest.fixture
async def sample_user_actions(
    db_session: AsyncSession, 
    test_user: User, 
    behavior_tracker: UserBehaviorTracker
) -> List[UserAction]:
    """Create sample user actions for testing."""
    actions = []
    base_time = datetime.utcnow() - timedelta(days=7)
    
    # Create a mix of actions
    action_data = [
        ("dismiss", "alert", "alert_1", None, 2000),
        ("act", "alert", "alert_2", "relevant", 5000),
        ("dismiss", "alert", "alert_3", "not_relevant", 1500),
        ("escalate", "impact_card", "card_1", None, 8000),
        ("dismiss", "alert", "alert_4", "duplicate", 1000),
        ("act", "impact_card", "card_2", "actionable", 6000),
        ("share", "alert", "alert_5", None, 3000),
        ("dismiss", "alert", "alert_6", "low_priority", 800),
        ("act", "alert", "alert_7", "critical", 4000),
        ("dismiss", "alert", "alert_8", "noise", 1200),
    ]
    
    for i, (action_type, target_type, target_id, reason, response_time) in enumerate(action_data):
        action = await behavior_tracker.record_action(
            user_id=str(test_user.id),
            session_id="test_session_1",
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            response_time_ms=response_time,
            context={"test": True, "sequence": i}
        )
        actions.append(action)
        
        # Add some time between actions
        await asyncio.sleep(0.01)
    
    return actions


class TestUserBehaviorTracker:
    """Test cases for UserBehaviorTracker."""
    
    @pytest.mark.asyncio
    async def test_record_action(self, behavior_tracker: UserBehaviorTracker, test_user: User):
        """Test recording a user action."""
        action = await behavior_tracker.record_action(
            user_id=str(test_user.id),
            session_id="test_session",
            action_type="dismiss",
            target_type="alert",
            target_id="alert_123",
            reason="not_relevant",
            confidence=0.8,
            response_time_ms=2500
        )
        
        assert action.user_id == str(test_user.id)
        assert action.action_type == "dismiss"
        assert action.target_type == "alert"
        assert action.target_id == "alert_123"
        assert action.reason == "not_relevant"
        assert action.confidence == 0.8
        assert action.response_time_ms == 2500
        assert action.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_get_user_actions(
        self, 
        behavior_tracker: UserBehaviorTracker, 
        test_user: User,
        sample_user_actions: List[UserAction]
    ):
        """Test retrieving user actions with filtering."""
        # Get all actions
        all_actions = await behavior_tracker.get_user_actions(str(test_user.id))
        assert len(all_actions) == 10
        
        # Filter by action type
        dismiss_actions = await behavior_tracker.get_user_actions(
            str(test_user.id), action_type="dismiss"
        )
        assert len(dismiss_actions) == 5
        assert all(a.action_type == "dismiss" for a in dismiss_actions)
        
        # Filter by target type
        alert_actions = await behavior_tracker.get_user_actions(
            str(test_user.id), target_type="alert"
        )
        assert len(alert_actions) == 8
        assert all(a.target_type == "alert" for a in alert_actions)
        
        # Filter by time
        recent_actions = await behavior_tracker.get_user_actions(
            str(test_user.id), since=datetime.utcnow() - timedelta(hours=1)
        )
        assert len(recent_actions) == 10  # All actions are recent
    
    @pytest.mark.asyncio
    async def test_analyze_behavior_patterns(
        self,
        behavior_tracker: UserBehaviorTracker,
        test_user: User,
        sample_user_actions: List[UserAction]
    ):
        """Test behavior pattern analysis."""
        patterns = await behavior_tracker.analyze_behavior_patterns(str(test_user.id))
        
        # Should have patterns for different target types
        assert len(patterns) >= 2
        
        # Check for alert pattern
        alert_patterns = [p for p in patterns if p.target_type == "alert"]
        assert len(alert_patterns) >= 1
        
        alert_pattern = alert_patterns[0]
        assert alert_pattern.dismissal_rate > 0  # Should have some dismissals
        assert alert_pattern.total_interactions > 0
        assert alert_pattern.pattern_strength >= 0
    
    @pytest.mark.asyncio
    async def test_learning_state_update(
        self,
        behavior_tracker: UserBehaviorTracker,
        test_user: User,
        sample_user_actions: List[UserAction]
    ):
        """Test learning state updates."""
        # Get learning state
        learning_state = await behavior_tracker.get_learning_state(str(test_user.id))
        
        assert learning_state is not None
        assert learning_state.total_actions_recorded >= 10
        assert learning_state.learning_phase in ["initialization", "learning", "optimizing"]
        assert 0 <= learning_state.confidence_level <= 1


class TestBehaviorPatternAnalyzer:
    """Test cases for BehaviorPatternAnalyzer."""
    
    async def test_analyze_user_patterns(
        self,
        pattern_analyzer: BehaviorPatternAnalyzer,
        test_user: User,
        sample_user_actions: List[UserAction]
    ):
        """Test comprehensive user pattern analysis."""
        patterns = await pattern_analyzer.analyze_user_patterns(str(test_user.id))
        
        assert len(patterns) > 0
        
        # Check for different pattern types
        pattern_types = set(p.pattern_type for p in patterns)
        expected_types = {"temporal_activity", "response_time", "content_preference"}
        assert len(pattern_types.intersection(expected_types)) > 0
    
    async def test_temporal_pattern_analysis(
        self,
        pattern_analyzer: BehaviorPatternAnalyzer,
        test_user: User,
        sample_user_actions: List[UserAction]
    ):
        """Test temporal pattern analysis."""
        patterns = await pattern_analyzer.analyze_user_patterns(str(test_user.id))
        
        temporal_patterns = [p for p in patterns if p.pattern_type == "temporal_activity"]
        if temporal_patterns:
            pattern = temporal_patterns[0]
            assert pattern.peak_activity_hours is not None
            assert len(pattern.peak_activity_hours) <= 3
            assert all(0 <= hour <= 23 for hour in pattern.peak_activity_hours)
    
    async def test_content_preference_analysis(
        self,
        pattern_analyzer: BehaviorPatternAnalyzer,
        test_user: User,
        sample_user_actions: List[UserAction]
    ):
        """Test content preference analysis."""
        patterns = await pattern_analyzer.analyze_user_patterns(str(test_user.id))
        
        content_patterns = [p for p in patterns if p.pattern_type == "content_preference"]
        assert len(content_patterns) >= 1
        
        # Should have patterns for both alert and impact_card
        target_types = set(p.target_type for p in content_patterns)
        assert "alert" in target_types
    
    async def test_cluster_similar_behaviors(
        self,
        pattern_analyzer: BehaviorPatternAnalyzer,
        db_session: AsyncSession
    ):
        """Test behavior clustering."""
        # Create multiple users with patterns
        users = []
        for i in range(3):
            user = User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                full_name=f"User {i}",
                hashed_password="hashed_password",
                role=UserRole.ANALYST
            )
            db_session.add(user)
            users.append(user)
        
        await db_session.commit()
        
        # Create behavior patterns for each user
        for user in users:
            pattern = BehaviorPattern(
                user_id=str(user.id),
                pattern_type="alert_response",
                target_type="alert",
                dismissal_rate=0.5 + (users.index(user) * 0.1),
                action_rate=0.3,
                pattern_strength=0.7
            )
            db_session.add(pattern)
        
        await db_session.commit()
        
        # Test clustering
        user_ids = [str(u.id) for u in users]
        clusters = await pattern_analyzer.cluster_similar_behaviors(user_ids)
        
        # Should create at least one cluster
        assert len(clusters) >= 1
        
        # All users should be assigned to clusters
        all_clustered_users = []
        for cluster_users in clusters.values():
            all_clustered_users.extend(cluster_users)
        
        assert len(set(all_clustered_users)) == len(users)


class TestAlertFatigueDetector:
    """Test cases for AlertFatigueDetector."""
    
    async def test_detect_alert_fatigue_no_fatigue(
        self,
        fatigue_detector: AlertFatigueDetector,
        test_user: User,
        sample_user_actions: List[UserAction]
    ):
        """Test fatigue detection when user is not fatigued."""
        indicators = await fatigue_detector.detect_alert_fatigue(str(test_user.id))
        
        assert isinstance(indicators, FatigueIndicators)
        assert indicators.dismissal_rate >= 0
        assert indicators.consecutive_dismissals >= 0
        assert indicators.response_time_trend in ["increasing", "stable", "decreasing"]
        assert 0 <= indicators.engagement_score <= 1
        assert isinstance(indicators.is_fatigued, bool)
        assert 0 <= indicators.confidence <= 1
    
    async def test_detect_alert_fatigue_high_dismissal(
        self,
        fatigue_detector: AlertFatigueDetector,
        test_user: User,
        behavior_tracker: UserBehaviorTracker
    ):
        """Test fatigue detection with high dismissal rate."""
        # Create actions with high dismissal rate
        for i in range(10):
            await behavior_tracker.record_action(
                user_id=str(test_user.id),
                session_id="fatigue_test",
                action_type="dismiss",
                target_type="alert",
                target_id=f"alert_{i}",
                reason="not_relevant",
                response_time_ms=1000 + (i * 100)  # Increasing response time
            )
        
        indicators = await fatigue_detector.detect_alert_fatigue(str(test_user.id))
        
        # High dismissal rate should indicate potential fatigue
        assert indicators.dismissal_rate > 0.8
        assert indicators.consecutive_dismissals > 5
        # May or may not be fatigued depending on other factors
    
    async def test_suggest_threshold_adjustment_high_dismissal(
        self,
        fatigue_detector: AlertFatigueDetector,
        test_user: User,
        behavior_tracker: UserBehaviorTracker
    ):
        """Test threshold suggestion with high dismissal rate."""
        # Create many dismissal actions
        for i in range(25):  # Need minimum actions for suggestion
            await behavior_tracker.record_action(
                user_id=str(test_user.id),
                session_id="threshold_test",
                action_type="dismiss",
                target_type="alert",
                target_id=f"alert_{i}",
                reason="not_relevant"
            )
        
        suggestion = await fatigue_detector.suggest_threshold_adjustment(
            str(test_user.id), current_threshold=0.7
        )
        
        if suggestion:  # May be None if confidence is too low
            assert isinstance(suggestion, ThresholdSuggestion)
            assert suggestion.current_threshold == 0.7
            assert suggestion.adjustment_type in ["increase", "decrease", "maintain"]
            assert 0 <= suggestion.confidence <= 1
            assert suggestion.reason is not None
            assert suggestion.expected_impact is not None
    
    async def test_suggest_threshold_adjustment_low_dismissal(
        self,
        fatigue_detector: AlertFatigueDetector,
        test_user: User,
        behavior_tracker: UserBehaviorTracker
    ):
        """Test threshold suggestion with low dismissal rate."""
        # Create mostly action-taking behavior
        for i in range(25):
            action_type = "act" if i % 5 != 0 else "dismiss"  # 20% dismissal rate
            await behavior_tracker.record_action(
                user_id=str(test_user.id),
                session_id="threshold_test",
                action_type=action_type,
                target_type="alert",
                target_id=f"alert_{i}",
                reason="relevant" if action_type == "act" else "not_relevant"
            )
        
        suggestion = await fatigue_detector.suggest_threshold_adjustment(
            str(test_user.id), current_threshold=0.7
        )
        
        if suggestion:
            assert isinstance(suggestion, ThresholdSuggestion)
            # With low dismissal rate and high action rate, might suggest lowering threshold
            # or maintaining current threshold
            assert suggestion.adjustment_type in ["decrease", "maintain"]
    
    async def test_fatigue_metrics_storage(
        self,
        fatigue_detector: AlertFatigueDetector,
        test_user: User,
        sample_user_actions: List[UserAction],
        db_session: AsyncSession
    ):
        """Test that fatigue metrics are stored correctly."""
        # Detect fatigue (which should store metrics)
        await fatigue_detector.detect_alert_fatigue(str(test_user.id))
        
        # Check that metrics were stored
        query = select(AlertFatigueMetric).where(AlertFatigueMetric.user_id == str(test_user.id))
        result = await db_session.execute(query)
        metrics = result.scalars().all()
        
        assert len(metrics) >= 1
        
        metric = metrics[0]
        assert metric.user_id == str(test_user.id)
        assert metric.period_start is not None
        assert metric.period_end is not None
        assert metric.alerts_received >= 0
        assert metric.dismissal_rate >= 0
    
    async def test_get_fatigue_history(
        self,
        fatigue_detector: AlertFatigueDetector,
        test_user: User,
        sample_user_actions: List[UserAction]
    ):
        """Test retrieving fatigue history."""
        # Generate some fatigue metrics
        await fatigue_detector.detect_alert_fatigue(str(test_user.id))
        
        # Get history
        history = await fatigue_detector.get_fatigue_history(str(test_user.id))
        
        assert len(history) >= 1
        assert all(h.user_id == str(test_user.id) for h in history)
        assert all(h.created_at is not None for h in history)


class TestIntegration:
    """Integration tests for the complete behavior tracking system."""
    
    async def test_complete_workflow(
        self,
        behavior_tracker: UserBehaviorTracker,
        pattern_analyzer: BehaviorPatternAnalyzer,
        fatigue_detector: AlertFatigueDetector,
        test_user: User
    ):
        """Test the complete workflow from action recording to pattern analysis."""
        # 1. Record various user actions
        actions_data = [
            ("dismiss", "alert", "alert_1", "not_relevant"),
            ("act", "alert", "alert_2", "relevant"),
            ("dismiss", "alert", "alert_3", "duplicate"),
            ("escalate", "impact_card", "card_1", None),
            ("share", "alert", "alert_4", None),
        ]
        
        for action_type, target_type, target_id, reason in actions_data:
            await behavior_tracker.record_action(
                user_id=str(test_user.id),
                session_id="integration_test",
                action_type=action_type,
                target_type=target_type,
                target_id=target_id,
                reason=reason,
                response_time_ms=2000
            )
        
        # 2. Analyze behavior patterns
        patterns = await pattern_analyzer.analyze_user_patterns(str(test_user.id))
        assert len(patterns) > 0
        
        # 3. Detect alert fatigue
        fatigue_indicators = await fatigue_detector.detect_alert_fatigue(str(test_user.id))
        assert fatigue_indicators is not None
        
        # 4. Check learning state
        learning_state = await behavior_tracker.get_learning_state(str(test_user.id))
        assert learning_state is not None
        assert learning_state.total_actions_recorded >= 5
    
    async def test_insufficient_data_handling(
        self,
        behavior_tracker: UserBehaviorTracker,
        pattern_analyzer: BehaviorPatternAnalyzer,
        fatigue_detector: AlertFatigueDetector,
        test_user: User
    ):
        """Test handling of insufficient data scenarios."""
        # Record only a few actions
        await behavior_tracker.record_action(
            user_id=str(test_user.id),
            session_id="minimal_test",
            action_type="dismiss",
            target_type="alert",
            target_id="alert_1"
        )
        
        # Pattern analysis should handle insufficient data gracefully
        patterns = await pattern_analyzer.analyze_user_patterns(str(test_user.id))
        # May return empty list or minimal patterns
        
        # Fatigue detection should handle insufficient data
        fatigue_indicators = await fatigue_detector.detect_alert_fatigue(str(test_user.id))
        assert fatigue_indicators.confidence == 0.0  # Low confidence with insufficient data
        
        # Threshold suggestion should return None for insufficient data
        suggestion = await fatigue_detector.suggest_threshold_adjustment(str(test_user.id))
        assert suggestion is None  # Not enough data for suggestion