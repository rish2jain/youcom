"""Annotation system for Impact Cards and collaborative analysis"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Annotation(Base):
    """Annotations for Impact Cards with position and type support"""
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    impact_card_id = Column(Integer, ForeignKey("impact_cards.id"), nullable=False)

    # Annotation content
    content = Column(Text, nullable=False)
    annotation_type = Column(String(50), nullable=False)  # insight, question, concern, action

    # Position data for UI highlighting
    position = Column(JSON, nullable=True)  # {x: number, y: number, width?: number, height?: number}
    target_element = Column(String(255), nullable=True)  # CSS selector or element ID
    target_text = Column(Text, nullable=True)  # Selected text for highlighting

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_resolved = Column(Integer, default=0)  # 0 = open, 1 = resolved
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="annotations")
    resolver = relationship("User", foreign_keys=[resolved_by])
    impact_card = relationship("ImpactCard", backref="annotations")

    def __repr__(self):
        return f"<Annotation(id={self.id}, type={self.annotation_type}, user_id={self.user_id})>"