"""Structured logging configuration using *structlog*.

Behaviour
---------
* **Development** (LOG_LEVEL != "INFO" or DEBUG): coloured, human-readable
  console output via :class:`structlog.dev.ConsoleRenderer`.
* **Production**: newline-delimited JSON suitable for log aggregators.

Usage
-----
    import structlog
    log = structlog.get_logger(__name__)

    log.info("document.uploaded", doc_id=str(doc.id), size=doc.file_size)

Context binding helpers::

    from app.core.logging import bind_request_id, bind_query_id
    bind_request_id(request_id)
    bind_query_id(query_id)
"""
from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

from app.core.config import settings


# --------------------------------------------------------------------------- #
# Custom processors
# --------------------------------------------------------------------------- #

def _add_app_version(_: WrappedLogger, __: str, event_dict: EventDict) -> EventDict:
    """Inject the application version into every log record."""
    event_dict["app_version"] = settings.APP_VERSION
    return event_dict


def _drop_color_message_key(
    _: WrappedLogger, __: str, event_dict: EventDict
) -> EventDict:
    """Remove uvicorn's internal ``color_message`` key to keep logs clean."""
    event_dict.pop("color_message", None)
    return event_dict


# --------------------------------------------------------------------------- #
# Setup
# --------------------------------------------------------------------------- #

def configure_logging() -> None:
    """Configure structlog and the stdlib *logging* root handler.

    Call this **once** during application startup, before any log statements.
    """
    log_level: int = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    is_development: bool = settings.LOG_LEVEL.upper() == "DEBUG"

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_app_version,
        _drop_color_message_key,
        structlog.processors.StackInfoRenderer(),
    ]

    if is_development:
        # Human-friendly output for local development
        renderer: Any = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # Machine-parseable JSON for production / log aggregators
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Silence noisy third-party loggers in production
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(
            logging.DEBUG if is_development else logging.WARNING
        )


# --------------------------------------------------------------------------- #
# Context helpers
# --------------------------------------------------------------------------- #

def bind_request_id(request_id: str) -> None:
    """Bind *request_id* into the current structlog context."""
    structlog.contextvars.bind_contextvars(request_id=request_id)


def bind_query_id(query_id: str) -> None:
    """Bind *query_id* into the current structlog context."""
    structlog.contextvars.bind_contextvars(query_id=query_id)


def clear_context() -> None:
    """Clear all structlog context variables for the current coroutine/thread."""
    structlog.contextvars.clear_contextvars()
