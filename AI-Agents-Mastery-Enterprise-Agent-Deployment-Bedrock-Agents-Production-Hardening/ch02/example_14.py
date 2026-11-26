import time
import json
from typing import Dict, Any, List

class AgentSpanTracer:
    """Tracks latency and attributes across agentic reasoning stages."""

    def __init__(self, trace_id: str):
        self.trace_id = trace_id
        self.spans: List[Dict[str, Any]] = []

    def start_span(self, name: str) -> Dict[str, Any]:
        span = {
            "name": name,
            "start_time": time.time(),
            "attributes": {}
        }
        self.spans.append(span)
        return span

    def finish_span(self, span: Dict[str, Any], attributes: Dict[str, Any]) -> None:
        span["end_time"] = time.time()
        span["duration_ms"] = (span["end_time"] - span["start_time"]) * 1000
        span["attributes"].update(attributes)

    def export_summary(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "total_spans": len(self.spans),
            "spans": [
                {"name": s["name"], "duration_ms": round(s.get("duration_ms", 0), 2), "attrs": s["attributes"]}
                for s in self.spans
            ]
        }

if __name__ == "__main__":
    tracer = AgentSpanTracer("trace-adk-883a")
    s1 = tracer.start_span("gemini_inference_hop_1")
    time.sleep(0.04)
    tracer.finish_span(s1, {"model": "gemini-2.5-pro", "prompt_tokens": 420})
    
    s2 = tracer.start_span("tool_exec_k8s_query")
    time.sleep(0.02)
    tracer.finish_span(s2, {"tool": "k8s_query", "status": "200_OK"})
    
    print("Trace Export:", json.dumps(tracer.export_summary(), indent=2))
