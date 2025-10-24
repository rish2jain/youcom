"""Audit log for compliance and security"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class AuditAction(str, enum.Enum):
    """Types of actions that can be audited"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    SHARE = "share"
    PERMISSION_CHANGE = "permission_change"
    API_CALL = "api_call"


class AuditLog(Base):
    """Comprehensive audit trail for compliance (SOC 2, GDPR)"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for system actions

    # Action details
    action = Column(SQLEnum(AuditAction), nullable=False)
    resource_type = Column(String, nullable=False)  # e.g., "watchlist", "impact_card", "user"
    resource_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)

    # Context
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True)

    # Before/after state for compliance
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # Result
    success = Column(Integer, default=1)  # 1 = success, 0 = failure
    error_message = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, resource={self.resource_type}, user_id={self.user_id})>"
