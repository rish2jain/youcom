import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import SecretStr, field_validator
from typing import Optional
from dotenv import load_dotenv

# Load .env file from parent directory
load_dotenv(Path(__file__).parent.parent.parent / ".env")

class Settings(BaseSettings):
    # You.com API Configuration
    you_api_key: SecretStr = SecretStr(os.getenv("YOU_API_KEY", ""))
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/cia_hackathon")

    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6380")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # You.com API URLs - CORRECTED based on official documentation
    # Search and News APIs use different base URL than Agent APIs
    you_search_base_url: str = os.getenv("YOU_SEARCH_BASE_URL", "https://api.ydc-index.io")
    you_agent_base_url: str = os.getenv("YOU_AGENT_BASE_URL", "https://api.you.com/v1")

    @property
    def you_search_url(self) -> str:
        """Search API endpoint - verified from You.com documentation"""
        return f"{self.you_search_base_url}/v1/search"

    @property
    def you_news_url(self) -> str:
        """News API endpoint - verified from You.com documentation"""
        return f"{self.you_search_base_url}/livenews"

    @property
    def you_chat_url(self) -> str:
        """Chat API endpoint for Custom Agents"""
        return f"{self.you_agent_base_url}/agents/runs"

    @property
    def you_ari_url(self) -> str:
        """ARI API fallback - using Express Agent for deep research

        Note: ARI API endpoint not found in public documentation.
        Using Express Agent as fallback for comprehensive research queries.
        """
        return f"{self.you_agent_base_url}/agents/runs"

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
    smtp_password: SecretStr = SecretStr(os.getenv("SMTP_PASSWORD", ""))
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
    
    # HubSpot Integration Configuration
    hubspot_client_id: str = os.getenv("HUBSPOT_CLIENT_ID", "")
    hubspot_client_secret: SecretStr = SecretStr(os.getenv("HUBSPOT_CLIENT_SECRET", ""))
    
    # Data directory for ML models and storage
    data_dir: str = os.getenv("DATA_DIR") or str(Path(__file__).resolve().parent.parent.parent / "data")

    @field_validator('you_api_key')
    @classmethod
    def validate_you_api_key(cls, v):
        """Validate You.com API key is properly configured"""
        import logging
        
        # Short-circuit validation in demo mode
        if os.environ.get("DEMO_MODE") in {"1", "true", "yes"}:
            logger = logging.getLogger(__name__)
            logger.warning("Skipping YOU_API_KEY validation in demo mode")
            return v
            
        key_value = v.get_secret_value() if hasattr(v, 'get_secret_value') else v

        if not key_value or key_value in ["", "your_you_api_key_here"]:
            raise ValueError(
                "YOU_API_KEY is required. Get your API key from https://api.you.com "
                "and set it in your .env file"
            )

        if len(key_value) < 20:
            raise ValueError("YOU_API_KEY appears to be invalid (too short)")

        return v

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        """Validate SECRET_KEY is properly configured for production"""
        import warnings
        import secrets
        
        environment = os.getenv('ENVIRONMENT', os.getenv('ENV', 'development'))

        # Check for old placeholder and emit deprecation warning
        if v == "your-secret-key-here":
            warnings.warn(
                "Using placeholder SECRET_KEY 'your-secret-key-here' is deprecated and will be rejected in a future release. "
                "Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'",
                DeprecationWarning,
                stacklevel=2
            )

        # In development, generate a secure random key if not provided
        if environment == 'development':
            if not v or v in ["", "your-secret-key-here"]:
                return secrets.token_urlsafe(32)

        # In production, require a strong secret key
        if not v or v in ["", "your-secret-key-here"]:
            raise ValueError(
                "SECRET_KEY must be set in production. "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters for security")

        return v

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
