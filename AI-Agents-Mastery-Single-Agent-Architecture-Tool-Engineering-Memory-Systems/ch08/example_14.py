from typing import Dict

class W3CTraceContextPropagator:
    def inject_trace_context(self, trace_id: str, span_id: str) -> Dict[str, str]:
        # Formulate W3C TraceContext traceparent standard header
        # Version 00 - TraceID (32 hex) - ParentID (16 hex) - TraceFlags (01 recorded)
        traceparent = f"00-{trace_id}-{span_id}-01"
        return {
            "traceparent": traceparent,
            "x-agent-origin": "ai-agents-runtime-v1"
        }

propagator = W3CTraceContextPropagator()
headers = propagator.inject_trace_context("4bf92f3577b34da6a3ce929d0e0e4736", "00f067aa0ba902b7")
print("Outgoing Downstream Tool Headers:\n", headers)
