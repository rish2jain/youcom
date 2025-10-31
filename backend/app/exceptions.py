"""
Enterprise CIA - Comprehensive Exception Hierarchy

This module provides a structured exception hierarchy for consistent error handling
across the application. All custom exceptions inherit from EnterpriseBaseException.

Exception Hierarchy:
    EnterpriseBaseException
    ├── APIException
    │   ├── YouComAPIException
    │   │   ├── YouComAPIError (existing - aliased)
    │   │   ├── YouComRateLimitError
    │   │   ├── YouComAuthenticationError
    │   │   └── YouComServiceUnavailableError
    │   └── ExternalAPIException
    ├── DatabaseException
    │   ├── DatabaseConnectionError
    │   ├── DatabaseQueryError
    │   └── DatabaseMigrationError
    ├── CacheException
    │   ├── CacheConnectionError
    │   └── CacheOperationError
    ├── ValidationException
    │   ├── ConfigurationError
    │   └── InputValidationError
    └── BusinessLogicException
        ├── InsufficientDataError
        ├── AnalysisError
        └── OrchestrationError

Usage:
    from app.exceptions import YouComAPIException, DatabaseConnectionError

    # Raise with context
    raise YouComAPIException(
        message="API request failed",
        status_code=500,
        details={"endpoint": "/search", "reason": "timeout"}
    )

    # Catch specific exceptions
    try:
        result = await api_call()
    except YouComRateLimitError:
        # Handle rate limiting
        pass
    except YouComAPIException as e:
        # Handle general API errors
        logger.error(f"API error: {e.message}", extra=e.to_dict())
"""

from typing import Any, Dict, Optional
from datetime import datetime, timezone


class EnterpriseBaseException(Exception):
    """Base exception for all Enterprise CIA exceptions"""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code or 500
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses"""
        return {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
            "timestamp": self.timestamp,
        }

    def __str__(self) -> str:
        return f"{self.error_code}: {self.message}"


# ============================================================
# API Exceptions
# ============================================================


class APIException(EnterpriseBaseException):
    """Base exception for all API-related errors"""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        endpoint: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, status_code=status_code, **kwargs)
        if endpoint:
            self.details["endpoint"] = endpoint


class YouComAPIException(APIException):
    """Base exception for You.com API errors"""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        api_type: Optional[str] = None,  # "news", "search", "chat", "ari"
        **kwargs
    ) -> None:
        super().__init__(message, status_code=status_code or 502, **kwargs)
        if api_type:
            self.details["api_type"] = api_type


class YouComRateLimitError(YouComAPIException):
    """Raised when You.com API rate limit is exceeded"""

    def __init__(
        self,
        message: str = "You.com API rate limit exceeded",
        *,
        retry_after: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__(message, status_code=429, **kwargs)
        if retry_after:
            self.details["retry_after_seconds"] = retry_after


class YouComAuthenticationError(YouComAPIException):
    """Raised when You.com API authentication fails"""

    def __init__(
        self,
        message: str = "You.com API authentication failed",
        **kwargs
    ) -> None:
        super().__init__(message, status_code=401, **kwargs)


class YouComServiceUnavailableError(YouComAPIException):
    """Raised when You.com API service is unavailable"""

    def __init__(
        self,
        message: str = "You.com API service unavailable",
        **kwargs
    ) -> None:
        super().__init__(message, status_code=503, **kwargs)


class ExternalAPIException(APIException):
    """Exception for external API errors (HubSpot, Slack, etc.)"""

    def __init__(
        self,
        message: str,
        *,
        service_name: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        if service_name:
            self.details["service"] = service_name


# ============================================================
# Database Exceptions
# ============================================================


class DatabaseException(EnterpriseBaseException):
    """Base exception for database-related errors"""

    def __init__(
        self,
        message: str,
        *,
        query: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, status_code=500, **kwargs)
        if query:
            # Redact sensitive data from query
            self.details["query"] = self._redact_query(query)

    @staticmethod
    def _redact_query(query: str) -> str:
        """Redact sensitive information from SQL queries"""
        # Simple redaction - could be enhanced
        if len(query) > 200:
            return query[:200] + "... (truncated)"
        return query


class DatabaseConnectionError(DatabaseException):
    """Raised when database connection fails"""

    def __init__(
        self,
        message: str = "Database connection failed",
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)


class DatabaseQueryError(DatabaseException):
    """Raised when database query execution fails"""

    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        if operation:
            self.details["operation"] = operation


class DatabaseMigrationError(DatabaseException):
    """Raised when database migration fails"""

    def __init__(
        self,
        message: str,
        *,
        migration_version: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        if migration_version:
            self.details["migration"] = migration_version


# ============================================================
# Cache Exceptions
# ============================================================


class CacheException(EnterpriseBaseException):
    """Base exception for cache-related errors"""

    def __init__(
        self,
        message: str,
        *,
        cache_key: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, status_code=500, **kwargs)
        if cache_key:
            self.details["cache_key"] = cache_key


class CacheConnectionError(CacheException):
    """Raised when Redis connection fails"""

    def __init__(
        self,
        message: str = "Cache connection failed",
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)


class CacheOperationError(CacheException):
    """Raised when cache operation fails"""

    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        if operation:
            self.details["operation"] = operation


# ============================================================
# Validation Exceptions
# ============================================================


class ValidationException(EnterpriseBaseException):
    """Base exception for validation errors"""

    def __init__(
        self,
        message: str,
        *,
        field: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, status_code=400, **kwargs)
        if field:
            self.details["field"] = field


class ConfigurationError(ValidationException):
    """Raised when configuration validation fails"""

    def __init__(
        self,
        message: str,
        *,
        config_key: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, status_code=500, **kwargs)
        if config_key:
            self.details["config_key"] = config_key


class InputValidationError(ValidationException):
    """Raised when input validation fails"""

    def __init__(
        self,
        message: str,
        *,
        validation_errors: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        if validation_errors:
            self.details["validation_errors"] = validation_errors


# ============================================================
# Business Logic Exceptions
# ============================================================


class BusinessLogicException(EnterpriseBaseException):
    """Base exception for business logic errors"""

    def __init__(
        self,
        message: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, status_code=422, **kwargs)
        if context:
            self.details["context"] = context


class InsufficientDataError(BusinessLogicException):
    """Raised when insufficient data is available for analysis"""

    def __init__(
        self,
        message: str = "Insufficient data for analysis",
        *,
        required_sources: Optional[int] = None,
        actual_sources: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        if required_sources:
            self.details["required_sources"] = required_sources
        if actual_sources:
            self.details["actual_sources"] = actual_sources


class AnalysisError(BusinessLogicException):
    """Raised when competitive analysis fails"""

    def __init__(
        self,
        message: str,
        *,
        competitor: Optional[str] = None,
        analysis_stage: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        if competitor:
            self.details["competitor"] = competitor
        if analysis_stage:
            self.details["stage"] = analysis_stage


class OrchestrationError(BusinessLogicException):
    """Raised when API orchestration fails"""

    def __init__(
        self,
        message: str,
        *,
        failed_stage: Optional[str] = None,
        partial_results: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        if failed_stage:
            self.details["failed_stage"] = failed_stage
        if partial_results:
            self.details["partial_results"] = partial_results


# ============================================================
# Backward Compatibility Alias
# ============================================================

# Alias for backward compatibility with existing code
YouComAPIError = YouComAPIException


# ============================================================
# Exception Handler Utilities
# ============================================================

def format_exception_for_api(exc: EnterpriseBaseException) -> Dict[str, Any]:
    """
    Format exception for API response

    Returns a dict suitable for FastAPI JSONResponse
    """
    return {
        "error": exc.error_code,
        "message": exc.message,
        "details": exc.details,
        "timestamp": exc.timestamp,
    }


def format_exception_for_logging(exc: EnterpriseBaseException) -> Dict[str, Any]:
    """
    Format exception for structured logging

    Returns a dict with additional context for logging systems
    """
    return {
        **exc.to_dict(),
        "exception_type": type(exc).__name__,
        "exception_hierarchy": [cls.__name__ for cls in type(exc).__mro__ if cls != object],
    }
