"""
Configuration Check API endpoints.
Helps users understand what services are configured and available.
"""

from fastapi import APIRouter, Depends
from app.config import settings
from app.services.email_service import get_email_service

router = APIRouter(prefix="/config", tags=["configuration"])

@router.get("/status")
async def get_configuration_status():
    """
    Get the status of various service configurations.
    Helps users understand what features are available.
    """
    
    # Check email service
    email_service = get_email_service(settings)
    email_configured = email_service is not None
    
    # Check You.com API
    you_api_configured = bool(settings.you_api_key.get_secret_value())
    
    # Check database
    database_configured = bool(settings.database_url)
    
    # Check Redis
    redis_configured = bool(settings.redis_url)
    
    return {
        "services": {
            "email": {
                "configured": email_configured,
                "required_for": ["PDF sharing via email", "Alert notifications"],
                "missing_settings": [] if email_configured else [
                    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "FROM_EMAIL"
                ]
            },
            "you_api": {
                "configured": you_api_configured,
                "required_for": ["Company research", "Impact cards", "News monitoring"],
                "missing_settings": [] if you_api_configured else ["YOU_API_KEY"]
            },
            "database": {
                "configured": database_configured,
                "required_for": ["Data persistence", "User management"],
                "missing_settings": [] if database_configured else ["DATABASE_URL"]
            },
            "redis": {
                "configured": redis_configured,
                "required_for": ["Caching", "Background tasks"],
                "missing_settings": [] if redis_configured else ["REDIS_URL"]
            }
        },
        "overall_status": "ready" if all([
            email_configured, you_api_configured, database_configured, redis_configured
        ]) else "partial",
        "recommendations": _get_configuration_recommendations(
            email_configured, you_api_configured, database_configured, redis_configured
        )
    }

def _get_configuration_recommendations(email_configured: bool, you_api_configured: bool, 
                                     database_configured: bool, redis_configured: bool) -> list:
    """Generate configuration recommendations based on current status."""
    recommendations = []
    
    if not email_configured:
        recommendations.append({
            "priority": "medium",
            "service": "Email Service",
            "message": "Configure SMTP settings to enable PDF sharing and email notifications",
            "action": "Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, and FROM_EMAIL environment variables"
        })
    
    if not you_api_configured:
        recommendations.append({
            "priority": "high",
            "service": "You.com API",
            "message": "You.com API key required for core functionality",
            "action": "Set YOU_API_KEY environment variable with your You.com API key"
        })
    
    if not database_configured:
        recommendations.append({
            "priority": "high",
            "service": "Database",
            "message": "Database connection required for data persistence",
            "action": "Set DATABASE_URL environment variable"
        })
    
    if not redis_configured:
        recommendations.append({
            "priority": "medium",
            "service": "Redis",
            "message": "Redis improves performance through caching",
            "action": "Set REDIS_URL environment variable"
        })
    
    return recommendations

@router.get("/email/test")
async def test_email_configuration():
    """
    Test email configuration without sending an actual email.
    Returns detailed information about email service status.
    """
    email_service = get_email_service(settings)
    
    if not email_service:
        return {
            "status": "not_configured",
            "message": "Email service is not configured",
            "required_settings": {
                "SMTP_HOST": "SMTP server hostname (e.g., smtp.gmail.com)",
                "SMTP_PORT": "SMTP server port (e.g., 587 for TLS)",
                "SMTP_USER": "SMTP username/email",
                "SMTP_PASSWORD": "SMTP password or app password",
                "FROM_EMAIL": "Email address to send from"
            },
            "current_settings": {
                "SMTP_HOST": settings.smtp_host or "Not set",
                "SMTP_PORT": settings.smtp_port,
                "SMTP_USER": settings.smtp_user or "Not set",
                "SMTP_PASSWORD": "***" if settings.smtp_password.get_secret_value() else "Not set",
                "FROM_EMAIL": settings.from_email or "Not set"
            }
        }
    
    return {
        "status": "configured",
        "message": "Email service is properly configured",
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "from_email": settings.from_email,
        "note": "Email service is ready to send reports and notifications"
    }