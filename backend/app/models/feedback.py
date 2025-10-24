from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

from app.database import Base


class InsightFeedback(Base):
    __tablename__ = "insight_feedback"

    id = Column(Integer, primary_key=True, index=True)
    impact_card_id = Column(Integer, ForeignKey("impact_cards.id"), nullable=False, index=True)
    action_index = Column(Integer, nullable=True)
    user_identifier = Column(String(255), nullable=True)
    sentiment = Column(String(20), nullable=False)  # up, down
    comments = Column(String(1024), nullable=True)
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
