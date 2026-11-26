class PrometheusMetricsExporter:
    def __init__(self):
        self.request_counter: Dict[str, int] = {}
        self.latency_histogram_ms: List[float] = []
        self.error_counter: Dict[str, int] = {}

    def record_request(self, status: str, latency_ms: float, error_type: Optional[str] = None):
        self.request_counter[status] = self.request_counter.get(status, 0) + 1
        self.latency_histogram_ms.append(latency_ms)
        if error_type:
            self.error_counter[error_type] = self.error_counter.get(error_type, 0) + 1

    def calculate_percentiles(self) -> Dict[str, float]:
        if not self.latency_histogram_ms:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
        
        sorted_latencies = sorted(self.latency_histogram_ms)
        n = len(sorted_latencies)
        return {
            "p50": round(sorted_latencies[int(n * 0.50)], 2),
            "p95": round(sorted_latencies[int(n * 0.95)], 2),
            "p99": round(sorted_latencies[min(n - 1, int(n * 0.99))], 2)
        }

    def generate_prometheus_payload(self) -> str:
        percentiles = self.calculate_percentiles()
        lines = [
            "# HELP agent_requests_total Total count of autonomous agent requests",
            "# TYPE agent_requests_total counter",
            f'agent_requests_total{{status="success"}} {self.request_counter.get("success", 0)}',
            f'agent_requests_total{{status="error"}} {self.request_counter.get("error", 0)}',
            "# HELP agent_latency_ms Agent execution latency percentiles",
            "# TYPE agent_latency_ms gauge",
            f'agent_latency_ms{{quantile="0.50"}} {percentiles["p50"]}',
            f'agent_latency_ms{{quantile="0.95"}} {percentiles["p95"]}',
            f'agent_latency_ms{{quantile="0.99"}} {percentiles["p99"]}'
        ]
        return "\n".join(lines)

# Verification
metrics = PrometheusMetricsExporter()
for lat in [120.0, 140.0, 150.0, 180.0, 220.0, 850.0, 1200.0]:
    metrics.record_request("success", lat)
metrics.record_request("error", 450.0, error_type="RateLimitExceeded")

print("Prometheus Metrics Payload:")
print(metrics.generate_prometheus_payload())
