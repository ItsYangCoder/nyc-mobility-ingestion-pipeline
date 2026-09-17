"""Tests for structured application logging."""

import io
import json
import logging
from pathlib import Path

import pytest

from nyc_mobility.logging import configure_logging, get_logger, log_event


def test_json_log_contains_event_and_context():
    stream = io.StringIO()
    configure_logging(stream=stream, force=True, service="test-service")
    logger = get_logger("tests.logging")

    log_event(
        logger,
        logging.INFO,
        "source.completed",
        "Source completed",
        file_path=Path("/tmp/source.json"),
        row_count=42,
    )

    payload = json.loads(stream.getvalue())
    assert payload["level"] == "INFO"
    assert payload["service"] == "test-service"
    assert payload["logger"] == "nyc_mobility.tests.logging"
    assert payload["event"] == "source.completed"
    assert payload["message"] == "Source completed"
    assert payload["context"] == {
        "file_path": "/tmp/source.json",
        "row_count": 42,
    }
    assert payload["timestamp"].endswith("Z")


def test_exception_is_serialized():
    stream = io.StringIO()
    configure_logging(stream=stream, force=True)
    logger = get_logger("tests.exception")

    try:
        raise RuntimeError("boom")
    except RuntimeError:
        log_event(
            logger,
            logging.ERROR,
            "task.failed",
            "Task failed",
            exc_info=True,
        )

    payload = json.loads(stream.getvalue())
    assert payload["level"] == "ERROR"
    assert "RuntimeError: boom" in payload["exception"]


def test_configuration_is_idempotent():
    stream = io.StringIO()
    application_logger = configure_logging(stream=stream, force=True)
    configure_logging(stream=stream)

    marked_handlers = [
        handler
        for handler in application_logger.handlers
        if getattr(handler, "_nyc_mobility_json_handler", False)
    ]
    assert len(marked_handlers) == 1


def test_invalid_log_level_is_rejected():
    with pytest.raises(ValueError, match="Invalid log level"):
        configure_logging(level="NOT_A_LEVEL", force=True)
