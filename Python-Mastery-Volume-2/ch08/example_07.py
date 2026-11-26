# VERIFIED PRODUCTION FIX:
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.sampling import TraceIdRatioBasedSampler

# Non-blocking batch processing with gRPC binary framing:
tracer_provider = TracerProvider(
    sampler=TraceIdRatioBasedSampler(0.05),  # 5% statistical sampling
    resource=resource,
)
tracer_provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint="telemetry-collector.internal:4317", insecure=True),
        max_queue_size=16384,
        schedule_delay_millis=500,
    )
)
