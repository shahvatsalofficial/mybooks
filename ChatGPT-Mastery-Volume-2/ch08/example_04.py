"""
Enterprise OpenTelemetry Tracing Pipeline for OpenAI API
Captures GenAI semantic spans, token telemetry, and latency percentiles.
Author: Vatsal Shah, Enterprise AI Architect
"""
import time
from typing import Dict, Any
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from openai import OpenAI

tracer = trace.get_tracer("enterprise.llm.gateway", "2.0.0")
client = OpenAI()

def traced_chat_completion(
    model: str,
    messages: list,
    temperature: float = 0.2,
    tenant_id: str = "dept_finance"
) -> Dict[str, Any]:
    with tracer.start_as_current_span("gen_ai.chat.completion") as span:
        span.set_attribute("gen_ai.system", "openai")
        span.set_attribute("gen_ai.request.model", model)
        span.set_attribute("gen_ai.request.temperature", temperature)
        span.set_attribute("app.tenant_id", tenant_id)

        start_time = time.time()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            duration_ms = (time.time() - start_time) * 1000

            # Record Token Telemetry Attributes
            usage = response.usage
            span.set_attribute("gen_ai.usage.prompt_tokens", usage.prompt_tokens)
            span.set_attribute("gen_ai.usage.completion_tokens", usage.completion_tokens)
            span.set_attribute("gen_ai.usage.total_tokens", usage.total_tokens)
            span.set_attribute("gen_ai.response.finish_reasons", [choice.finish_reason for choice in response.choices])
            span.set_attribute("llm.duration_ms", duration_ms)
            span.set_status(Status(StatusCode.OK))

            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                "duration_ms": duration_ms
            }

        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise exc
