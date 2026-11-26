class HandoffTelemetryExporter:
    def __init__(self):
        self.total_handoffs = 0
        self.total_handoff_latency = 0.0

    def record_handoff_latency(self, duration_ms: float):
        self.total_handoffs += 1
        self.total_handoff_latency += duration_ms

    def export(self) -> str:
        avg = self.total_handoff_latency / max(1, self.total_handoffs)
        return (
            f"langgraph_handoffs_total {self.total_handoffs}\n"
            f"langgraph_avg_handoff_latency_ms {avg:.2f}\n"
        )
