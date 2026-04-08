"""Structured JSON logging configuration.

Each log line is a single JSON object, making it easy to parse with
log aggregation tools (e.g., Datadog, CloudWatch Logs Insights).

Usage:
    from src.infrastructure.logging_config import setup_logging
    setup_logging()          # INFO level
    setup_logging("DEBUG")   # DEBUG level
"""

from __future__ import annotations

import json
import logging
import traceback
from datetime import UTC, datetime

# Fields that are part of LogRecord but should not be re-emitted as extras
_STDLIB_FIELDS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
})


class StructuredFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Append any extra fields passed via logger.info(..., extra={...})
        for key, value in record.__dict__.items():
            if key not in _STDLIB_FIELDS:
                entry[key] = value

        if record.exc_info:
            entry["exception"] = traceback.format_exception(*record.exc_info)

        return json.dumps(entry, default=str, ensure_ascii=False)


def setup_logging(level: str | int = logging.INFO) -> None:
    """Configure the root logger with structured JSON output to stdout."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logging.basicConfig(handlers=[handler], level=level, force=True)
