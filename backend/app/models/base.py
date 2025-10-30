"""Base model class for SQLAlchemy models."""

from app.database import Base

# Re-export Base for models that import from .base
__all__ = ["Base"]