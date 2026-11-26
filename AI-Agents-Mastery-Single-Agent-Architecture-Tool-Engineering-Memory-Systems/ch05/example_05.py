import time

class TelemetryCallbackHandler:
    def __init__(self):
        self.active_spans: Dict[str, float] = {}
        self.telemetry_events: List[Dict[str, Any]] = []

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any]):
        run_id = str(uuid.uuid4())
        self.active_spans["chain"] = time.perf_counter()
        self.telemetry_events.append({
            "event": "chain_start",
            "timestamp": time.time(),
            "inputs": inputs
        })

    def on_tool_start(self, tool_name: str, input_str: str):
        self.active_spans[tool_name] = time.perf_counter()
        self.telemetry_events.append({
            "event": "tool_start",
            "tool": tool_name,
            "input": input_str
        })

    def on_tool_end(self, tool_name: str, output: str):
        start_time = self.active_spans.pop(tool_name, time.perf_counter())
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        self.telemetry_events.append({
            "event": "tool_end",
            "tool": tool_name,
            "duration_ms": round(duration_ms, 2),
            "output_chars": len(output)
        })

    def export_telemetry_summary(self) -> Dict[str, Any]:
        return {
            "total_events": len(self.telemetry_events),
            "tool_calls": [e for e in self.telemetry_events if e["event"] == "tool_end"]
        }

# Verification
handler = TelemetryCallbackHandler()
handler.on_tool_start("search_knowledge_vault", '{"query": "p99 latency"}')
time.sleep(0.05)
handler.on_tool_end("search_knowledge_vault", "Found 4 documents.")
print("Telemetry Span Recorded:")
print(json.dumps(handler.export_telemetry_summary(), indent=2))
