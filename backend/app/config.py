import os
from pydantic_settings import BaseSettings
from pydantic import SecretStr, field_validator
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

    # Email Configuration for sharing reports
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    from_email: str = os.getenv("FROM_EMAIL", "noreply@enterprisecia.com")

    # SSO Configuration - Week 1 Implementation
    # Google OAuth2
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: SecretStr = SecretStr(os.getenv("GOOGLE_CLIENT_SECRET", ""))
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
    
    # Azure AD OAuth2
    azure_client_id: str = os.getenv("AZURE_CLIENT_ID", "")
    azure_client_secret: SecretStr = SecretStr(os.getenv("AZURE_CLIENT_SECRET", ""))
    azure_tenant_id: str = os.getenv("AZURE_TENANT_ID", "")
    azure_redirect_uri: str = os.getenv("AZURE_REDIRECT_URI", "http://localhost:3000/auth/azure/callback")
    
    # Okta OAuth2
    okta_client_id: str = os.getenv("OKTA_CLIENT_ID", "")
    okta_client_secret: SecretStr = SecretStr(os.getenv("OKTA_CLIENT_SECRET", ""))
    okta_domain: str = os.getenv("OKTA_DOMAIN", "")
    okta_redirect_uri: str = os.getenv("OKTA_REDIRECT_URI", "http://localhost:3000/auth/okta/callback")
    
    # Microsoft Teams Integration - Week 2 Implementation
    teams_bot_token: SecretStr = SecretStr(os.getenv("TEAMS_BOT_TOKEN", ""))
    teams_app_id: str = os.getenv("TEAMS_APP_ID", "")
    teams_app_password: SecretStr = SecretStr(os.getenv("TEAMS_APP_PASSWORD", ""))
    
    # Frontend URL for links in notifications
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    @field_validator('google_redirect_uri', 'azure_redirect_uri', 'okta_redirect_uri')
    @classmethod
    def validate_redirect_uris(cls, v):
        """Validate redirect URIs are not localhost in production"""
        environment = os.getenv('ENVIRONMENT', os.getenv('ENV', 'development'))
        
        if environment != 'development' and 'localhost' in v:
            raise ValueError(f"Redirect URI cannot contain 'localhost' in {environment} environment")
        
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields

settings = Settings()
