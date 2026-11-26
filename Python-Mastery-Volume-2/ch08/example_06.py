# CATASTROPHIC FLAW IN v5.2.0 PRODUCTION CODE:
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# FLAW: SimpleSpanProcessor blocks the calling application thread synchronously
# on EVERY SINGLE SPAN END until an HTTP POST request completes over the network!
tracer_provider.add_span_processor(
    SimpleSpanProcessor(OTLPSpanExporter(endpoint="https://telemetry.corp.internal/v1/traces"))
)
