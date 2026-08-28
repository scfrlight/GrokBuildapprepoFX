"""Structured logging. Secret values must never be logged."""

from __future__ import annotations

import logging
import sys

import structlog

from botmoduleproject1.app.settings import Settings

_CONFIGURED = False


def configure_logging(settings: Settings) -> None:
    global _CONFIGURED
    level = getattr(logging, settings.logging.level)
    logging.basicConfig(level=level, stream=sys.stdout, format="%(message)s")
    processors: list[object] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if settings.logging.json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _CONFIGURED = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
