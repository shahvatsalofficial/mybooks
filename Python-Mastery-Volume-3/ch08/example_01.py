# observability/logging_config.py
"""Structured JSON logging configuration with automated OpenTelemetry trace correlation."""

from __future__ import annotations
import logging
from opentelemetry import trace
import structlog


def inject_opentelemetry_trace_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Extracts active OpenTelemetry span context and injects trace_id and span_id into log records."""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        span_context = current_span.get_span_context()
        if span_context.is_valid:
            event_dict["trace_id"] = trace.format_trace_id(span_context.trace_id)
            event_dict["span_id"] = trace.format_span_id(span_context.span_id)
            event_dict["trace_sampled"] = span_context.trace_flags.sampled
    return event_dict


def configure_enterprise_logging() -> None:
    """Configures high-performance structured JSON logging pipeline."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            inject_opentelemetry_trace_context,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),  # Output strictly structured JSON
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
