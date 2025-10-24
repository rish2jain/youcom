from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.sql import func

from app.database import Base


class NotificationRule(Base):
    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True, index=True)
    competitor_name = Column(String(255), nullable=False, index=True)
    condition_type = Column(String(50), nullable=False)  # risk_threshold, news_spike, custom
    threshold_value = Column(Float, nullable=True)
    channel = Column(String(50), nullable=False)  # slack, email, log
    target = Column(String(255), nullable=False)  # webhook URL or email address
    active = Column(Boolean, default=True, nullable=False)
    last_triggered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=True, index=True)
    competitor_name = Column(String(255), nullable=False)
    message = Column(String(1024), nullable=False)
    channel = Column(String(50), nullable=False)
    target = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
