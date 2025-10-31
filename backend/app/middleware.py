"""
Enterprise CIA - Request Middleware

Provides middleware for:
- Request ID generation and propagation
- Request/response logging
- Performance tracking
- Error handling with structured responses
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.logging_config import set_request_id, get_logger
from app.exceptions import EnterpriseBaseException, format_exception_for_api


logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID to all requests

    Generates or extracts request ID and makes it available throughout
    the request lifecycle via context variables.

    Request ID can be provided by client via X-Request-ID header,
    or will be auto-generated.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        request_id = set_request_id(request_id)

        # Add to request state for easy access
        request.state.request_id = request_id

        # Call next middleware/endpoint
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests and responses with performance metrics

    Logs:
    - Request method, path, query params
    - Response status code
    - Request duration
    - Client IP
    - User agent
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        start_time = time.perf_counter()

        # Extract request info
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else None
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log successful request
            logger.info(
                f"{method} {path} - {response.status_code}",
                extra={
                    "method": method,
                    "path": path,
                    "query_params": query_params,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                }
            )

            return response

        except Exception as exc:
            # Calculate duration for failed requests
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log failed request
            logger.error(
                f"{method} {path} - ERROR",
                exc_info=True,
                extra={
                    "method": method,
                    "path": path,
                    "query_params": query_params,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "error": str(exc),
                }
            )

            # Re-raise to let error handler deal with it
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle exceptions and return structured error responses

    Converts custom exceptions to structured JSON responses with:
    - Error code
    - User-friendly message
    - Request ID
    - Timestamp
    - Details (when appropriate)
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        try:
            return await call_next(request)

        except EnterpriseBaseException as exc:
            # Handle our custom exceptions
            logger.error(
                f"Enterprise exception: {exc.message}",
                exc_info=True,
                extra=exc.to_dict()
            )

            response_data = format_exception_for_api(exc)
            response_data["request_id"] = getattr(request.state, "request_id", None)

            return JSONResponse(
                status_code=exc.status_code,
                content=response_data
            )

        except Exception as exc:
            # Handle unexpected exceptions
            logger.exception(
                "Unexpected exception",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                }
            )

            return JSONResponse(
                status_code=500,
                content={
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "request_id": getattr(request.state, "request_id", None),
                    "details": {
                        "type": type(exc).__name__,
                        # Don't expose full error message in production
                        "message": str(exc) if logger.level == logging.DEBUG else "Internal error"
                    }
                }
            )


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track performance metrics

    Tracks:
    - Slow requests (>2s warning, >5s critical)
    - Request distribution by endpoint
    - Average response times
    """

    SLOW_REQUEST_WARNING_MS = 2000
    SLOW_REQUEST_CRITICAL_MS = 5000

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log slow requests
        if duration_ms >= self.SLOW_REQUEST_CRITICAL_MS:
            logger.critical(
                f"CRITICAL: Slow request {request.method} {request.url.path}",
                extra={
                    "duration_ms": round(duration_ms, 2),
                    "threshold": "critical",
                    "path": request.url.path,
                }
            )
        elif duration_ms >= self.SLOW_REQUEST_WARNING_MS:
            logger.warning(
                f"WARNING: Slow request {request.method} {request.url.path}",
                extra={
                    "duration_ms": round(duration_ms, 2),
                    "threshold": "warning",
                    "path": request.url.path,
                }
            )

        # Add performance header
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response


def setup_middleware(app):
    """
    Add all middleware to FastAPI app in correct order

    Order matters! Middleware is applied in reverse order (last added = first executed)

    Execution order:
    1. SecurityHeadersMiddleware (outermost - adds security headers)
    2. PerformanceMonitoringMiddleware (tracks total time)
    3. RequestLoggingMiddleware (logs requests/responses)
    4. ErrorHandlingMiddleware (catches errors)
    5. RequestIDMiddleware (innermost - sets up request ID)

    Usage:
        from app.middleware import setup_middleware
        setup_middleware(app)
    """
    from app.security_headers import SecurityHeadersMiddleware
    from app.config import settings

    # Add in reverse order (LIFO)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(PerformanceMonitoringMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, environment=settings.environment)

    logger.info("✅ Middleware configured: SecurityHeaders, RequestID, Logging, ErrorHandling, Performance")
