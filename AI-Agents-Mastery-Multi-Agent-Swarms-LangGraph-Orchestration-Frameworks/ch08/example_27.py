class OTelSpanPropagator:
    @staticmethod
    def inject_w3c_traceparent(trace_id: str, span_id: str) -> Dict[str, str]:
        # Formulate W3C Trace Context Header (version-traceid-spanid-traceflags)
        traceparent = f"00-{trace_id[:32]}-{span_id[:16]}-01"
        return {"traceparent": traceparent}
