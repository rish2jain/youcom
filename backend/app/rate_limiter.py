"""
Rate limiter configuration for the Enterprise CIA application
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings

# Create shared rate limiter instance with Redis backend
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)