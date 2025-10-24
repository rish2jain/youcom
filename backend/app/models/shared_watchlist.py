"""Shared watchlist models for team collaboration"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


# Association table for watchlist assignments
watchlist_assignments = Table(
    'watchlist_assignments',
    Base.metadata,
    Column('shared_watchlist_id', Integer, ForeignKey('shared_watchlists.id'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), server_default=func.now())
)


class SharedWatchlist(Base):
    """Shared watchlist accessible by workspace members"""
    __tablename__ = "shared_watchlists"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # Watch item reference (linking to existing watch.py model)
    watch_item_id = Column(Integer, ForeignKey("watch_items.id"), nullable=False)

    # Owner and permissions
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)  # Public within workspace

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="shared_watchlists")
    watch_item = relationship("WatchItem", backref="shared_watchlists")
    comments = relationship("Comment", back_populates="shared_watchlist", cascade="all, delete-orphan")
    assigned_users = relationship("User", secondary=watchlist_assignments, backref="assigned_watchlists")

    def __repr__(self):
        return f"<SharedWatchlist(id={self.id}, name={self.name}, workspace_id={self.workspace_id})>"
