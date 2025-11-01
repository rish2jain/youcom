"""Comment notification system for team collaboration"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CommentNotification(Base):
    """Notifications for comment activities"""
    __tablename__ = "comment_notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    
    # Notification type: mention, reply, new_comment, thread_update
    notification_type = Column(String(50), nullable=False)
    
    # Context information
    context_type = Column(String(50), nullable=False)  # impact_card, shared_watchlist, company_research
    context_id = Column(Integer, nullable=False)
    
    # Notification status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id], backref="comment_notifications")
    comment = relationship("Comment", backref="notifications")

    def __repr__(self):
        return f"<CommentNotification(id={self.id}, type={self.notification_type}, recipient_id={self.recipient_id})>"


class ConflictDetection(Base):
    """Track conflicting interpretations in comments"""
    __tablename__ = "conflict_detections"

    id = Column(Integer, primary_key=True, index=True)
    
    # Context where conflict was detected
    context_type = Column(String(50), nullable=False)  # impact_card, shared_watchlist
    context_id = Column(Integer, nullable=False)
    
    # Conflicting comments
    comment_1_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    comment_2_id = Column(Integer, ForeignKey("comments.id"), nullable=False)
    
    # Conflict details
    conflict_type = Column(String(50), nullable=False)  # interpretation, priority, action
    confidence_score = Column(Integer, nullable=False)  # 0-100
    description = Column(Text, nullable=True)
    
    # Resolution
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Metadata
    detected_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    comment_1 = relationship("Comment", foreign_keys=[comment_1_id])
    comment_2 = relationship("Comment", foreign_keys=[comment_2_id])
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<ConflictDetection(id={self.id}, type={self.conflict_type}, resolved={self.is_resolved})>"