class SwarmMetricsExporter:
    def __init__(self):
        self.message_counter = 0
        self.error_counter = 0
        self.total_latency_ms = 0.0

    def record_interaction(self, sender: str, recipient: str, latency_ms: float, success: bool):
        self.message_counter += 1
        self.total_latency_ms += latency_ms
        if not success:
            self.error_counter += 1

    def generate_prometheus_payload(self) -> str:
        avg_latency = self.total_latency_ms / max(1, self.message_counter)
        return (
            "# HELP swarm_messages_total Total count of inter-agent messages\n"
            "# TYPE swarm_messages_total counter\n"
            f"swarm_messages_total {self.message_counter}\n"
            "# HELP swarm_errors_total Total count of failed agent operations\n"
            "# TYPE swarm_errors_total counter\n"
            f"swarm_errors_total {self.error_counter}\n"
            "# HELP swarm_avg_latency_ms Average latency per inter-agent turn\n"
            "# TYPE swarm_avg_latency_ms gauge\n"
            f"swarm_avg_latency_ms {avg_latency:.2f}\n"
        )
