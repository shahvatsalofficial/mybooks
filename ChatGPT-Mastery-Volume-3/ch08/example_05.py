# opentelemetry_genai_tracer.py — Standard W3C Trace Context Instrumentation
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialize Central Tracer
provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="otel-collector.internal:4317", insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("enterprise.genai.gateway", "3.0.0")

def instrument_llm_call(tenant_id: str, model: str, prompt: str):
    """Context manager instrumenting GenAI semantic conventions."""
    with tracer.start_as_current_span("genai.chat.completions") as span:
        # Standard GenAI Semantic Convention Attributes
        span.set_attribute("gen_ai.system", "azure_openai")
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("gen_ai.tenant.id", tenant_id)
        span.set_attribute("gen_ai.prompt.length", len(prompt))

        try:
            # Simulate Model Inference
            tokens_in = 412
            tokens_out = 180
            span.set_attribute("gen_ai.usage.prompt_tokens", tokens_in)
            span.set_attribute("gen_ai.usage.completion_tokens", tokens_out)
            span.set_attribute("gen_ai.usage.total_tokens", tokens_in + tokens_out)
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
