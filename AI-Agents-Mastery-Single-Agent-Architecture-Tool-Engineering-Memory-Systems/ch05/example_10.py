import os

class W3CTraceContextPropagator:
    @staticmethod
    def generate_traceparent(trace_id: Optional[str] = None, span_id: Optional[str] = None) -> str:
        tid = trace_id or secrets.token_hex(16)
        sid = span_id or secrets.token_hex(8)
        # Format: version-trace_id-parent_id-trace_flags (RFC W3C)
        return f"00-{tid}-{sid}-01"

    @staticmethod
    def inject_headers(headers: Dict[str, str]) -> Dict[str, str]:
        h = dict(headers)
        h["traceparent"] = W3CTraceContextPropagator.generate_traceparent()
        return h

# Verification
outgoing_headers = W3CTraceContextPropagator.inject_headers({"Content-Type": "application/json"})
print("Outgoing Tool HTTP Headers with Traceparent:", outgoing_headers["traceparent"])
