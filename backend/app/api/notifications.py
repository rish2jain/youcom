from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.notification import NotificationRule, NotificationLog

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Pydantic schemas for request/response
class NotificationRuleCreate(BaseModel):
    competitor_name: str
    condition_type: str  # "risk_threshold", "trend_change", "daily_digest"
    threshold_value: float = None
    channel: str  # "email", "slack", "webhook"
    target: str  # email address, slack channel, webhook URL
    active: bool = True

class NotificationRuleUpdate(BaseModel):
    competitor_name: str = None
    condition_type: str = None
    threshold_value: float = None
    channel: str = None
    target: str = None
    active: bool = None


def _validate_notification_rule(
    condition_type: Optional[str] = None,
    threshold_value: Optional[float] = None,
    channel: Optional[str] = None,
    target: Optional[str] = None
) -> None:
    """Validate notification rule parameters"""
    
    # Validate condition type and threshold
    if condition_type in ["risk_threshold", "trend_change"] and threshold_value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="threshold_value is required for risk_threshold and trend_change conditions"
        )
    
    # Validate channel and target
    if channel == "email" and target and "@" not in target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address for email channel"
        )


@router.get("/logs")
async def list_notification_logs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(NotificationLog)
        .order_by(NotificationLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return {
        "items": [
            {
                "id": log.id,
                "competitor_name": log.competitor_name,
                "message": log.message,
                "channel": log.channel,
                "target": log.target,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }


@router.get("/rules")
async def list_notification_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NotificationRule))
    rules = result.scalars().all()
    return {
        "items": [
            {
                "id": rule.id,
                "competitor_name": rule.competitor_name,
                "condition_type": rule.condition_type,
                "threshold_value": rule.threshold_value,
                "channel": rule.channel,
                "target": rule.target,
                "active": rule.active,
                "last_triggered_at": rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
                "created_at": rule.created_at.isoformat() if rule.created_at else None,
            }
            for rule in rules
        ]
    }

@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_notification_rule(
    rule_data: NotificationRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification rule"""
    
    # Validate using helper function
    _validate_notification_rule(
        condition_type=rule_data.condition_type,
        threshold_value=rule_data.threshold_value,
        channel=rule_data.channel,
        target=rule_data.target
    )
    
    db_rule = NotificationRule(**rule_data.model_dump())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    
    return {
        "id": db_rule.id,
        "competitor_name": db_rule.competitor_name,
        "condition_type": db_rule.condition_type,
        "threshold_value": db_rule.threshold_value,
        "channel": db_rule.channel,
        "target": db_rule.target,
        "active": db_rule.active,
        "created_at": db_rule.created_at.isoformat() if db_rule.created_at else None,
    }

@router.put("/rules/{rule_id}")
async def update_notification_rule(
    rule_id: int,
    rule_update: NotificationRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a notification rule"""
    
    # Check if rule exists
    result = await db.execute(select(NotificationRule).where(NotificationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification rule not found"
        )
    
    # Get update data and merge with existing values for validation
    update_data = rule_update.model_dump(exclude_unset=True)
    if update_data:
        # Create merged dict for validation - use update value if present, otherwise existing value
        merged_values = {
            "condition_type": update_data.get("condition_type", rule.condition_type),
            "threshold_value": update_data.get("threshold_value", rule.threshold_value),
            "channel": update_data.get("channel", rule.channel),
            "target": update_data.get("target", rule.target)
        }
        
        # Validate using merged values
        _validate_notification_rule(
            condition_type=merged_values["condition_type"],
            threshold_value=merged_values["threshold_value"],
            channel=merged_values["channel"],
            target=merged_values["target"]
        )
        
        # Perform update
        await db.execute(
            update(NotificationRule)
            .where(NotificationRule.id == rule_id)
            .values(**update_data)
        )
        await db.commit()
        
        # Re-query the updated rule instead of using refresh
        result = await db.execute(select(NotificationRule).where(NotificationRule.id == rule_id))
        rule = result.scalar_one()
    
    return {
        "id": rule.id,
        "competitor_name": rule.competitor_name,
        "condition_type": rule.condition_type,
        "threshold_value": rule.threshold_value,
        "channel": rule.channel,
        "target": rule.target,
        "active": rule.active,
        "last_triggered_at": rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
    }

@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification rule"""
    
    result = await db.execute(select(NotificationRule).where(NotificationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification rule not found"
        )
    
    await db.execute(delete(NotificationRule).where(NotificationRule.id == rule_id))
    await db.commit()

@router.post("/rules/{rule_id}/test")
async def test_notification_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Test a notification rule by sending a test alert"""
    
    result = await db.execute(select(NotificationRule).where(NotificationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification rule not found"
        )
    
    # Import here to avoid circular imports
    from app.services.scheduler import alert_scheduler
    
    # Create test context
    test_context = {
        "competitor": rule.competitor_name,
        "risk_score": 85,
        "risk_level": "high",
        "confidence": 90,
        "total_sources": 25,
        "key_insights": ["Test alert - this is a test notification"],
        "triggered_at": "Test Mode"
    }
    
    try:
        await alert_scheduler._send_alert(db, rule, test_context)
        return {"message": f"Test alert sent successfully to {rule.target}"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test alert: {str(e)}"
        )
