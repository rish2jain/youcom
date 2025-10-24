"""Comments and annotations system"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Comment(Base):
    """Comments and annotations for collaborative analysis"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Polymorphic relationships - can comment on different entities
    shared_watchlist_id = Column(Integer, ForeignKey("shared_watchlists.id"), nullable=True)
    impact_card_id = Column(Integer, ForeignKey("impact_cards.id"), nullable=True)
    company_research_id = Column(Integer, ForeignKey("company_research.id"), nullable=True)

    # Comment content
    content = Column(Text, nullable=False)
    annotations = Column(JSON, nullable=True)  # For highlighting specific sections

    # Threading support
    parent_comment_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_edited = Column(Integer, default=0)  # Count of edits

    # Relationships
    user = relationship("User", back_populates="comments")
    shared_watchlist = relationship("SharedWatchlist", back_populates="comments")
    parent_comment = relationship("Comment", remote_side=[id], backref="replies")

    def __repr__(self):
        return f"<Comment(id={self.id}, user_id={self.user_id}, content={self.content[:50]})>"
