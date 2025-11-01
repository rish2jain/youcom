"""Simplified tests for user behavior tracking system."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.user_behavior import UserAction, BehaviorPattern, AlertFatigueMetric, LearningLoopState
from app.services.user_behavior_tracker import UserBehaviorTracker
from app.services.alert_fatigue_detector import AlertFatigueDetector


@pytest.mark.asyncio
async def test_user_action_creation(db_session: AsyncSession):
    """Test creating a user action record."""
    # Create a test user
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
    
    # Create behavior tracker
    tracker = UserBehaviorTracker(db_session)
    
    # Record an action
    action = await tracker.record_action(
        user_id=str(user.id),
        session_id="test_session",
        action_type="dismiss",
        target_type="alert",
        target_id="alert_123",
        reason="not_relevant",
        confidence=0.8,
        response_time_ms=2500
    )
    
    # Verify action was created correctly
    assert action.user_id == str(user.id)
    assert action.action_type == "dismiss"
    assert action.target_type == "alert"
    assert action.target_id == "alert_123"
    assert action.reason == "not_relevant"
    assert action.confidence == 0.8
    assert action.response_time_ms == 2500
    assert action.timestamp is not None


@pytest.mark.asyncio
async def test_behavior_pattern_analysis(db_session: AsyncSession):
    """Test basic behavior pattern analysis."""
    # Create a test user
    user = User(
        email="test2@example.com",
        username="testuser2",
        full_name="Test User 2",
        hashed_password="hashed_password",
        role=UserRole.ANALYST,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create behavior tracker
    tracker = UserBehaviorTracker(db_session)
    
    # Record multiple actions to create a pattern
    actions_data = [
        ("dismiss", "alert", "alert_1", "not_relevant"),
        ("act", "alert", "alert_2", "relevant"),
        ("dismiss", "alert", "alert_3", "duplicate"),
        ("act", "impact_card", "card_1", "actionable"),
        ("dismiss", "alert", "alert_4", "low_priority"),
    ]
    
    for action_type, target_type, target_id, reason in actions_data:
        await tracker.record_action(
            user_id=str(user.id),
            session_id="pattern_test",
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            response_time_ms=2000
        )
    
    # Analyze patterns
    patterns = await tracker.analyze_behavior_patterns(str(user.id))
    
    # Should have at least one pattern
    assert len(patterns) >= 1
    
    # Check that patterns have valid data
    for pattern in patterns:
        assert pattern.user_id == str(user.id)
        assert pattern.total_interactions > 0
        assert 0 <= pattern.dismissal_rate <= 1
        assert pattern.pattern_strength >= 0


@pytest.mark.asyncio
async def test_alert_fatigue_detection(db_session: AsyncSession):
    """Test basic alert fatigue detection."""
    # Create a test user
    user = User(
        email="test3@example.com",
        username="testuser3",
        full_name="Test User 3",
        hashed_password="hashed_password",
        role=UserRole.ANALYST,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create services
    tracker = UserBehaviorTracker(db_session)
    fatigue_detector = AlertFatigueDetector(db_session)
    
    # Record actions with high dismissal rate
    for i in range(8):
        action_type = "dismiss" if i < 6 else "act"  # 75% dismissal rate
        await tracker.record_action(
            user_id=str(user.id),
            session_id="fatigue_test",
            action_type=action_type,
            target_type="alert",
            target_id=f"alert_{i}",
            reason="not_relevant" if action_type == "dismiss" else "relevant",
            response_time_ms=1000 + (i * 100)
        )
    
    # Detect fatigue
    indicators = await fatigue_detector.detect_alert_fatigue(str(user.id))
    
    # Verify fatigue indicators
    assert indicators is not None
    assert indicators.dismissal_rate > 0.5  # Should be high
    assert 0 <= indicators.engagement_score <= 1
    assert indicators.response_time_trend in ["increasing", "stable", "decreasing"]
    assert 0 <= indicators.confidence <= 1


@pytest.mark.asyncio
async def test_learning_state_tracking(db_session: AsyncSession):
    """Test learning state tracking."""
    # Create a test user
    user = User(
        email="test4@example.com",
        username="testuser4",
        full_name="Test User 4",
        hashed_password="hashed_password",
        role=UserRole.ANALYST,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create behavior tracker
    tracker = UserBehaviorTracker(db_session)
    
    # Record some actions
    for i in range(3):
        await tracker.record_action(
            user_id=str(user.id),
            session_id="learning_test",
            action_type="act",
            target_type="alert",
            target_id=f"alert_{i}",
            response_time_ms=2000
        )
    
    # Get learning state
    learning_state = await tracker.get_learning_state(str(user.id))
    
    # Verify learning state
    assert learning_state is not None
    assert learning_state.user_id == str(user.id)
    assert learning_state.total_actions_recorded >= 3
    assert learning_state.learning_phase in ["initialization", "learning", "optimizing"]
    assert 0 <= learning_state.confidence_level <= 1


@pytest.mark.asyncio
async def test_threshold_suggestion_basic(db_session: AsyncSession):
    """Test basic threshold suggestion functionality."""
    # Create a test user
    user = User(
        email="test5@example.com",
        username="testuser5",
        full_name="Test User 5",
        hashed_password="hashed_password",
        role=UserRole.ANALYST,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create services
    tracker = UserBehaviorTracker(db_session)
    fatigue_detector = AlertFatigueDetector(db_session)
    
    # Record enough actions for threshold suggestion (need at least 20)
    for i in range(25):
        action_type = "dismiss" if i % 4 == 0 else "act"  # 25% dismissal rate
        await tracker.record_action(
            user_id=str(user.id),
            session_id="threshold_test",
            action_type=action_type,
            target_type="alert",
            target_id=f"alert_{i}",
            reason="not_relevant" if action_type == "dismiss" else "relevant"
        )
    
    # Get threshold suggestion
    suggestion = await fatigue_detector.suggest_threshold_adjustment(
        str(user.id), current_threshold=0.7
    )
    
    # Verify suggestion (may be None if confidence is too low)
    if suggestion:
        assert suggestion.current_threshold == 0.7
        assert suggestion.adjustment_type in ["increase", "decrease", "maintain"]
        assert 0 <= suggestion.confidence <= 1
        assert suggestion.reason is not None
        assert suggestion.expected_impact is not None