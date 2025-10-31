"""
Security Headers Middleware
Adds essential security headers to all HTTP responses
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking attacks
    - X-XSS-Protection: Enable browser XSS protection
    - Strict-Transport-Security: Enforce HTTPS (production only)
    - Content-Security-Policy: Restrict resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Disable unnecessary browser features
    """

    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment
        logger.info(f"🔒 Security headers middleware initialized for {environment} environment")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response"""
        response = await call_next(request)

        # X-Content-Type-Options: Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: Enable browser XSS filter (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: Disable unnecessary browser features
        # This restricts access to sensitive APIs like camera, microphone, etc.
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # Content-Security-Policy: Restrict resource loading
        # Relaxed for development, strict for production
        if self.environment == "production":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow inline scripts for Next.js
                "style-src 'self' 'unsafe-inline'; "  # Allow inline styles for Tailwind
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' wss: https:; "  # Allow WebSocket and API connections
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            # More permissive CSP for development
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss: http: https:"
            )

        # Strict-Transport-Security (HSTS): Enforce HTTPS in production
        # Only add in production to avoid issues with local development
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; "  # 1 year
                "includeSubDomains; "
                "preload"
            )

        return response
