# observability/tracing.py
"""Enterprise OpenTelemetry distributed tracing and W3C context initialization."""

from __future__ import annotations
import logging
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger("telemetry_tracing")


def initialize_telemetry_tracer(
    service_name: str,
    environment: str,
    otlp_endpoint: str = "http://otel-collector.monitoring:4317",
) -> trace.Tracer:
    """Configures global OpenTelemetry TracerProvider with OTLP gRPC export pipeline."""
    logger.info("Initializing OpenTelemetry Tracing for service='%s' env='%s'", service_name, environment)

    # 1. Define standard semantic resource attributes
    resource = Resource.create(
        attributes={
            "service.name": service_name,
            "service.version": "3.0.0",
            "deployment.environment": environment,
            "telemetry.sdk.language": "python",
        }
    )

    # 2. Instantiate TracerProvider with resource metadata
    provider = TracerProvider(resource=resource)

    # 3. Configure non-blocking OTLP gRPC Span Exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,  # In-cluster communication behind internal mesh
    )

    # 4. Attach BatchSpanProcessor: Buffers spans and exports in batches asynchronously
    span_processor = BatchSpanProcessor(
        otlp_exporter,
        max_queue_size=2048,
        schedule_delay_millis=5000,
        max_export_batch_size=512,
    )
    provider.add_span_processor(span_processor)

    # 5. Set global tracer provider and W3C trace context propagator
    trace.set_tracer_provider(provider)
    trace.set_tracer_provider(provider)

    return trace.get_tracer(service_name)
