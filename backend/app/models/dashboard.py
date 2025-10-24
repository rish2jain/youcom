"""Custom dashboards for advanced analytics"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Dashboard(Base):
    """Custom dashboards for analytics and visualization"""
    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Dashboard configuration
    layout = Column(JSON, nullable=False)  # Widget positions and sizes
    widgets = Column(JSON, nullable=False)  # Widget configurations
    filters = Column(JSON, nullable=True)  # Default filters

    # Access control
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)  # Public within workspace
    is_default = Column(Boolean, default=False)  # Default dashboard for workspace

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)
    view_count = Column(Integer, default=0)

    # Relationships
    workspace = relationship("Workspace", back_populates="dashboards")

    def __repr__(self):
        return f"<Dashboard(id={self.id}, name={self.name}, workspace_id={self.workspace_id})>"


class ScheduledReport(Base):
    """Scheduled reports for automated delivery"""
    __tablename__ = "scheduled_reports"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    dashboard_id = Column(Integer, ForeignKey("dashboards.id"), nullable=True)

    # Report configuration
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(String, nullable=False)  # daily_summary, weekly_digest, impact_alert, etc.

    # Schedule
    schedule_cron = Column(String, nullable=False)  # Cron expression
    timezone = Column(String, default="UTC")
    is_active = Column(Boolean, default=True)

    # Recipients
    recipient_emails = Column(JSON, nullable=False)  # List of email addresses
    recipient_slack_channels = Column(JSON, nullable=True)  # Slack channel IDs

    # Configuration
    filters = Column(JSON, nullable=True)
    format = Column(String, default="pdf")  # pdf, html, json

    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)

    # Statistics
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)

    def __repr__(self):
        return f"<ScheduledReport(id={self.id}, name={self.name}, schedule={self.schedule_cron})>"
