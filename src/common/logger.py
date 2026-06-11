"""Structured logging configuration with JSON support and rotation.

Provides two logging formats:
- Human-readable for development (colored text)
- JSON for production (machine-parseable)

Features:
- Automatic log rotation (max 10MB per file, keep 5 backups)
- Context-aware logging (request ID, user ID)
- Performance-safe (async-compatible)
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Optional


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for production environments.

    Produces machine-parseable logs compatible with ELK stack,
    CloudWatch, and other log aggregation systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string.

        Args:
            record: Log record to format.

        Returns:
            JSON-formatted log line.
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        return json.dumps(log_data, ensure_ascii=False)


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that adds context (request_id, user_id) to log records.

    Usage:
        logger = ContextAdapter(logging.getLogger(__name__), extra={})
        logger.update_context(request_id="abc123")
        logger.info("Processing request")  # Includes request_id in output
    """

    def __init__(self, logger: logging.Logger, extra: dict = None):
        super().__init__(logger, extra or {})

    def update_context(self, **kwargs):
        """Update context fields for subsequent log messages.

        Args:
            **kwargs: Context fields to add (e.g., request_id, user_id).
        """
        self.extra.update(kwargs)

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Inject context into log record."""
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def _get_console_formatter(is_production: bool = False) -> logging.Formatter:
    """Get appropriate console formatter based on environment.

    Args:
        is_production: If True, use JSON format; otherwise use human-readable.

    Returns:
        Formatter instance.
    """
    if is_production:
        return JSONFormatter()

    # Human-readable format with colors (ANSI codes)
    class ColoredFormatter(logging.Formatter):
        """Add color to log levels for better readability."""

        COLORS = {
            "DEBUG": "\033[36m",      # Cyan
            "INFO": "\033[32m",       # Green
            "WARNING": "\033[33m",    # Yellow
            "ERROR": "\033[31m",      # Red
            "CRITICAL": "\033[35m",   # Magenta
        }
        RESET = "\033[0m"

        def format(self, record: logging.LogRecord) -> str:
            level = record.levelname
            color = self.COLORS.get(level, self.RESET)
            record.levelname = f"{color}{level}{self.RESET}"
            return super().format(record)

    return ColoredFormatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def setup_logger(
    name: str = "autotest-agent",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    is_production: bool = False,
) -> ContextAdapter:
    """Configure and return a structured logger with context support.

    Args:
        name: Logger name.
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional file path for log output with rotation.
        is_production: If True, use JSON format; otherwise use colored text.

    Returns:
        ContextAdapter instance for context-aware logging.

    Example:
        logger = setup_logger(__name__)
        logger.update_context(request_id="req-123")
        logger.info("Processing request")
    """
    if level is None:
        level = "INFO"

    base_logger = logging.getLogger(name)
    base_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid adding handlers multiple times
    if base_logger.handlers:
        return ContextAdapter(base_logger)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(_get_console_formatter(is_production))
    base_logger.addHandler(console_handler)

    # File handler with rotation (optional)
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # Rotating file handler: max 10MB per file, keep 5 backups
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)

        if is_production:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | "
                "%(filename)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            ))

        base_logger.addHandler(file_handler)

    return ContextAdapter(base_logger)


def get_logger(name: str = None) -> ContextAdapter:
    """Get a logger instance by name.

    Convenience function for getting loggers in modules.

    Args:
        name: Logger name (defaults to calling module's __name__).

    Returns:
        ContextAdapter instance.

    Example:
        logger = get_logger(__name__)
        logger.info("Hello, world!")
    """
    if name is None:
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get("__name__", "unknown")

    base_logger = logging.getLogger(name)
    return ContextAdapter(base_logger)