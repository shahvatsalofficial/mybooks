# otel_genai_instrumentation.py
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time

tracer = trace.get_tracer("enterprise.ai.gateway", "1.0.0")

class InstrumentedLLMClient:
    def __init__(self, underlying_client):
        self.client = underlying_client

    async def generate_completion(self, model: str, messages: list, tenant_id: str):
        with tracer.start_as_current_span("gen_ai.chat") as span:
            span.set_attribute("gen_ai.system", "azure_openai")
            span.set_attribute("gen_ai.request.model", model)
            span.set_attribute("gen_ai.request.temperature", 0.2)
            span.set_attribute("enterprise.tenant_id", tenant_id)
            
            start_t = time.perf_counter()
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.2
                )
                
                duration = time.perf_counter() - start_t
                usage = response.usage
                
                # Record standard OpenTelemetry semantic metrics
                span.set_attribute("gen_ai.response.model", response.model)
                span.set_attribute("gen_ai.usage.prompt_tokens", usage.prompt_tokens)
                span.set_attribute("gen_ai.usage.completion_tokens", usage.completion_tokens)
                span.set_attribute("gen_ai.usage.total_tokens", usage.total_tokens)
                span.set_attribute("gen_ai.latency.total_seconds", duration)
                
                span.set_status(Status(StatusCode.OK))
                return response
                
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise
