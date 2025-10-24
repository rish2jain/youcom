from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.notification import NotificationRule, NotificationLog

router = APIRouter(prefix="/notifications", tags=["notifications"])


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
            }
            for rule in rules
        ]
    }
