from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.feedback import InsightFeedback

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    impact_card_id: int
    action_index: int = Field(ge=0)
    sentiment: str = Field(pattern="^(up|down)$")
    comments: str | None = Field(default=None, max_length=1024)
    user_identifier: str | None = Field(default=None, max_length=255)


router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/impact", status_code=status.HTTP_201_CREATED)
async def submit_feedback(payload: FeedbackRequest, db: AsyncSession = Depends(get_db)):
    entry = InsightFeedback(
        impact_card_id=payload.impact_card_id,
        action_index=payload.action_index,
        sentiment=payload.sentiment,
        comments=payload.comments,
        user_identifier=payload.user_identifier,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {"id": entry.id}
