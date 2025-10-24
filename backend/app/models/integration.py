"""Enterprise integrations (Slack, Notion, etc.)"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class IntegrationType(str, enum.Enum):
    """Types of integrations"""
    SLACK = "slack"
    NOTION = "notion"
    SALESFORCE = "salesforce"
    MICROSOFT_TEAMS = "microsoft_teams"
    JIRA = "jira"
    WEBHOOK = "webhook"


class Integration(Base):
    """Enterprise integrations configuration"""
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    type = Column(SQLEnum(IntegrationType), nullable=False)

    # Configuration
    config = Column(JSON, nullable=False)  # Integration-specific settings
    credentials = Column(JSON, nullable=True)  # Encrypted credentials

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Statistics
    total_syncs = Column(Integer, default=0)
    successful_syncs = Column(Integer, default=0)
    failed_syncs = Column(Integer, default=0)

    def __repr__(self):
        return f"<Integration(id={self.id}, type={self.type}, workspace_id={self.workspace_id})>"


class IntegrationLog(Base):
    """Logs for integration activities"""
    __tablename__ = "integration_logs"

    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)

    # Action details
    action = Column(String, nullable=False)  # sync, send_notification, create_issue, etc.
    status = Column(String, nullable=False)  # success, failure, partial
    message = Column(Text, nullable=True)

    # Request/response
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    error_details = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    duration_ms = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<IntegrationLog(id={self.id}, integration_id={self.integration_id}, action={self.action})>"
