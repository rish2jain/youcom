import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # You.com API Configuration
    you_api_key: str = os.getenv("YOU_API_KEY", "")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/cia_hackathon")
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # You.com API URLs - CORRECTED based on official documentation
    # Search and News APIs use different base URL than Agent APIs
    you_search_base_url: str = "https://api.ydc-index.io"
    you_agent_base_url: str = "https://api.you.com/v1"

    # Correct endpoints verified from You.com API documentation
    you_search_url: str = f"{you_search_base_url}/v1/search"
    you_news_url: str = f"{you_search_base_url}/livenews"
    you_chat_url: str = f"{you_agent_base_url}/agents/runs"

    # ARI API fallback - using Express Agent for deep research
    # Note: ARI API endpoint not found in public documentation
    # Using Express Agent as fallback for comprehensive research queries
    you_ari_url: str = f"{you_agent_base_url}/agents/runs"  # Same as chat, use Express agent

    # Demo mode flag (kept for compatibility; defaults to real data)
    demo_mode: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    # API Rate Limits and Caching
    news_cache_ttl: int = 900  # 15 minutes
    search_cache_ttl: int = 3600  # 1 hour
    ari_cache_ttl: int = 604800  # 7 days
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields

settings = Settings()
