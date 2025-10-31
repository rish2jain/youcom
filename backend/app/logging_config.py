"""
Enterprise CIA - Structured Logging Configuration

This module provides structured logging with request ID tracking for
comprehensive observability and debugging.

Features:
- Request ID propagation across async calls
- Structured JSON logging for production
- Context-aware logging with automatic metadata
- Performance metrics logging
- Error tracking with stack traces

Usage:
    from app.logging_config import get_logger, log_performance

    # Get a logger for your module
    logger = get_logger(__name__)

    # Log with automatic request ID
    logger.info("Processing request", extra={"user_id": user_id})

    # Log performance metrics
    with log_performance("api_orchestration"):
        result = await orchestrate_apis()
"""

import contextvars
import logging
import time
import json
import uuid
from typing import Any, Dict, Optional
from contextlib import contextmanager
from datetime import datetime


# Context variable for request ID propagation
request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'request_id', default=None
)


def generate_request_id() -> str:
    """Generate a unique request ID"""
    return f"req_{uuid.uuid4().hex[:16]}"


def get_request_id() -> Optional[str]:
    """Get the current request ID from context"""
    return request_id_var.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    """Set request ID in context, generating one if not provided"""
    if request_id is None:
        request_id = generate_request_id()
    request_id_var.set(request_id)
    return request_id


class RequestIDFilter(logging.Filter):
    """Add request ID to log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "no-request-id"
        return True


class StructuredFormatter(logging.Formatter):
    """
    Format log records as structured JSON

    Produces JSON logs suitable for log aggregation systems like:
    - ELK Stack (Elasticsearch, Logstash, Kibana)
    - Datadog
    - CloudWatch
    - Splunk
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, 'request_id', None),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields from logger.info("msg", extra={...})
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in [
                    'name', 'msg', 'args', 'created', 'filename', 'funcName',
                    'levelname', 'levelno', 'lineno', 'module', 'msecs',
                    'pathname', 'process', 'processName', 'relativeCreated',
                    'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                    'request_id', 'message'
                ]:
                    log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data, default=str)


class HumanReadableFormatter(logging.Formatter):
    """
    Format log records for human-readable console output

    Includes request ID and colored output (when supported)
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m',     # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        # Add color if terminal supports it
        if hasattr(record, 'request_id'):
            request_id = f"[{record.request_id}]"
        else:
            request_id = "[no-req-id]"

        level_color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']

        # Format: timestamp | level | request_id | logger | message
        return (
            f"{level_color}{record.levelname:8}{reset} | "
            f"{request_id} | "
            f"{record.name:30} | "
            f"{record.getMessage()}"
        )


def setup_logging(
    level: str = "INFO",
    structured: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Configure application logging

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Use structured JSON logging (True for production)
        log_file: Optional file path for file logging
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = StructuredFormatter() if structured else HumanReadableFormatter()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIDFilter())
    root_logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())  # Always use JSON for files
        file_handler.addFilter(RequestIDFilter())
        root_logger.addHandler(file_handler)

    # Set library loggers to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name

    Automatically includes request ID in all log messages

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


@contextmanager
def log_performance(
    operation: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    **extra_context: Any
):
    """
    Context manager for logging operation performance

    Usage:
        with log_performance("database_query", table="users"):
            result = await db.execute(query)

    Args:
        operation: Name of the operation being timed
        logger: Optional logger (uses root logger if not provided)
        level: Logging level for performance log
        **extra_context: Additional context to log
    """
    if logger is None:
        logger = logging.getLogger()

    start_time = time.perf_counter()
    start_timestamp = datetime.utcnow().isoformat()

    try:
        yield
        success = True
        error = None
    except Exception as e:
        success = False
        error = str(e)
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        log_data = {
            "operation": operation,
            "duration_ms": round(elapsed_ms, 2),
            "success": success,
            "start_time": start_timestamp,
            **extra_context
        }

        if error:
            log_data["error"] = error

        logger.log(
            level,
            f"Performance: {operation} completed in {elapsed_ms:.2f}ms",
            extra=log_data
        )


def log_api_call(
    logger: logging.Logger,
    api_type: str,
    endpoint: str,
    status_code: Optional[int],
    success: bool,
    latency_ms: float,
    error_message: Optional[str] = None,
    **extra_context: Any
):
    """
    Log API call with structured data

    Args:
        logger: Logger instance
        api_type: Type of API (news, search, chat, ari)
        endpoint: API endpoint URL
        status_code: HTTP status code
        success: Whether call succeeded
        latency_ms: Latency in milliseconds
        error_message: Optional error message
        **extra_context: Additional context
    """
    log_data = {
        "api_type": api_type,
        "endpoint": endpoint,
        "status_code": status_code,
        "success": success,
        "latency_ms": round(latency_ms, 2),
        **extra_context
    }

    if error_message:
        log_data["error"] = error_message

    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        f"API {api_type}: {endpoint} - {status_code} ({latency_ms:.2f}ms)",
        extra=log_data
    )


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    success: bool,
    duration_ms: float,
    rows_affected: Optional[int] = None,
    error_message: Optional[str] = None,
    **extra_context: Any
):
    """
    Log database operation with structured data

    Args:
        logger: Logger instance
        operation: Operation type (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        success: Whether operation succeeded
        duration_ms: Duration in milliseconds
        rows_affected: Number of rows affected
        error_message: Optional error message
        **extra_context: Additional context
    """
    log_data = {
        "operation": operation,
        "table": table,
        "success": success,
        "duration_ms": round(duration_ms, 2),
        **extra_context
    }

    if rows_affected is not None:
        log_data["rows_affected"] = rows_affected

    if error_message:
        log_data["error"] = error_message

    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        f"Database {operation} on {table} - {duration_ms:.2f}ms",
        extra=log_data
    )


# Initialize logging on module import
# This can be overridden by calling setup_logging() explicitly
from app.config import settings

setup_logging(
    level="INFO" if settings.environment == "production" else "DEBUG",
    structured=settings.environment == "production",
    log_file=None  # Can be configured via environment variable
)
