"""
Audit Log Model for Security and Compliance

Model for storing audit trails, security events, and compliance-related logs.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Boolean, Index, Enum
from datetime import datetime
import enum

from app.models.base import Base

class AuditAction(enum.Enum):
    """Enum for audit log actions."""
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
    """Model for storing audit logs and security events."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)  # Can be null for system events
    action = Column(Enum(AuditAction), nullable=False, index=True)  # Action performed
    resource_type = Column(String, nullable=False, index=True)  # Type of resource affected
    resource_id = Column(String, index=True)  # ID of the specific resource
    details = Column(JSON)  # Additional details about the action
    ip_address = Column(String, index=True)  # Source IP address
    user_agent = Column(Text)  # User agent string
    session_id = Column(String, index=True)  # Session identifier
    success = Column(Boolean, default=True)  # Whether the action was successful
    error_message = Column(Text)  # Error message if action failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Indexes for common query patterns
    __table_args__ = (
        Index('idx_audit_user_action_time', 'user_id', 'action', 'created_at'),
        Index('idx_audit_resource_time', 'resource_type', 'resource_id', 'created_at'),
        Index('idx_audit_ip_time', 'ip_address', 'created_at'),
        Index('idx_audit_action_time', 'action', 'created_at'),
    )