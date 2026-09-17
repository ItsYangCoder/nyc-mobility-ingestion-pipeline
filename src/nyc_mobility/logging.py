"""Structured JSON logging shared by local and Databricks workloads."""

from __future__ import annotations

import json
import logging
import os
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import IO, Any

DEFAULT_LOG_LEVEL = "INFO"
_HANDLER_MARKER = "_nyc_mobility_json_handler"


class JsonFormatter(logging.Formatter):
    """Serialize log records as one JSON object per line."""

    def __init__(self, service: str = "nyc-mobility") -> None:
        super().__init__()
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "service": self.service,
            "logger": record.name,
            "message": record.getMessage(),
        }

        event = getattr(record, "event", None)
        if event:
            payload["event"] = event

        context = getattr(record, "context", None)
        if isinstance(context, Mapping):
            payload["context"] = _json_safe(dict(context))

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if isinstance(value, os.PathLike):
        return os.fspath(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def configure_logging(
    level: str | int | None = None,
    *,
    stream: IO[str] | None = None,
    service: str = "nyc-mobility",
    force: bool = False,
) -> logging.Logger:
    """Configure an idempotent JSON handler on the application root logger."""
    application_logger = logging.getLogger("nyc_mobility")
    resolved_level = level or os.getenv("NYC_MOBILITY_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    numeric_level = (
        resolved_level
        if isinstance(resolved_level, int)
        else logging.getLevelNamesMapping().get(resolved_level.upper())
    )
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {resolved_level!r}")

    if force:
        for handler in list(application_logger.handlers):
            if getattr(handler, _HANDLER_MARKER, False):
                application_logger.removeHandler(handler)

    existing = next(
        (
            handler
            for handler in application_logger.handlers
            if getattr(handler, _HANDLER_MARKER, False)
        ),
        None,
    )
    if existing is None:
        handler = logging.StreamHandler(stream or sys.stdout)
        setattr(handler, _HANDLER_MARKER, True)
        handler.setFormatter(JsonFormatter(service=service))
        application_logger.addHandler(handler)
    else:
        existing.setLevel(numeric_level)

    application_logger.setLevel(numeric_level)
    application_logger.propagate = False
    return application_logger


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger without mutating global logging state."""
    normalized = name.removeprefix("nyc_mobility.")
    return logging.getLogger(f"nyc_mobility.{normalized}")


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str,
    *,
    exc_info: bool = False,
    **context: Any,
) -> None:
    """Emit a structured event with JSON-safe contextual fields."""
    logger.log(
        level,
        message,
        extra={"event": event, "context": context},
        exc_info=exc_info,
    )
