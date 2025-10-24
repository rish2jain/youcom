from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.sql import func

from app.database import Base


class ApiCallLog(Base):
    __tablename__ = "api_call_logs"

    id = Column(Integer, primary_key=True, index=True)
    api_type = Column(String(50), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    status_code = Column(Integer, nullable=True)
    success = Column(Boolean, default=True, nullable=False, index=True)
    latency_ms = Column(Float, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        status = "success" if self.success else "failure"
        return f"<ApiCallLog(api_type={self.api_type}, status={status}, latency_ms={self.latency_ms})>"
