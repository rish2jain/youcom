"""User and authentication models for enterprise features"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    """User roles for RBAC"""
    VIEWER = "viewer"  # Can view data only
    ANALYST = "analyst"  # Can view and create research
    ADMIN = "admin"  # Full access including user management


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.ANALYST, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # SSO fields
    sso_provider = Column(String, nullable=True)  # google, okta, azure, etc.
    sso_id = Column(String, nullable=True)  # External SSO user ID

    # GDPR Compliance fields - Week 2 Implementation
    consent_marketing = Column(Boolean, default=False)
    consent_analytics = Column(Boolean, default=True)
    consent_integrations = Column(Boolean, default=True)
    data_retention_days = Column(Integer, default=730)  # 2 years default

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workspace_memberships = relationship("WorkspaceMember", back_populates="user", foreign_keys="WorkspaceMember.user_id", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    # User behavior tracking relationships
    actions = relationship("UserAction", back_populates="user", cascade="all, delete-orphan")
    behavior_patterns = relationship("BehaviorPattern", back_populates="user", cascade="all, delete-orphan")
    fatigue_metrics = relationship("AlertFatigueMetric", back_populates="user", cascade="all, delete-orphan")
    learning_state = relationship("LearningLoopState", back_populates="user", uselist=False, cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == UserRole.ADMIN
    
    @property
    def last_login(self) -> Optional[DateTime]:
        """Alias for GDPR service compatibility"""
        return self.last_login_at

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
