"""
Recipe 08.4: OpenTelemetry Instrumentation & Prometheus Metrics for Claude
Author: Vatsal Shah (Vatsal Shah)
License: Apache-2.0
"""

import time
from typing import Dict, Any, List
from opentelemetry import trace
from opentelemetry.trace import StatusCode, Status
import anthropic

tracer = trace.get_tracer("claude.telemetry", "2.1.0")

class ObservabilityClaudeClient:
    def __init__(self):
        self.client = anthropic.Anthropic()

    def create_message_instrumented(self, model: str, messages: List[Dict[str, Any]], system: str = None) -> str:
        with tracer.start_as_current_span("claude.messages.create") as span:
            span.set_attribute("gen_ai.system", "anthropic")
            span.set_attribute("gen_ai.request.model", model)
            span.set_attribute("gen_ai.request.temperature", 0.0)

            start_clock = time.perf_counter()
            try:
                kwargs = {"model": model, "messages": messages, "max_tokens": 2048}
                if system:
                    kwargs["system"] = system

                res = self.client.messages.create(**kwargs)
                duration = time.perf_counter() - start_clock

                # Record Generative AI Semantic Attributes
                span.set_attribute("gen_ai.usage.input_tokens", res.usage.input_tokens)
                span.set_attribute("gen_ai.usage.output_tokens", res.usage.output_tokens)
                span.set_attribute("gen_ai.usage.cache_read_tokens", getattr(res.usage, "cache_read_input_tokens", 0))
                span.set_attribute("gen_ai.usage.cache_creation_tokens", getattr(res.usage, "cache_creation_input_tokens", 0))
                span.set_attribute("gen_ai.response.duration_seconds", duration)
                span.set_status(Status(StatusCode.OK))

                return "".join([b.text for b in res.content if hasattr(b, "text")])

            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise
