class GrafanaSwarmMetricsExporter:
    def __init__(self):
        self.p95_latencies: Dict[str, float] = {"supervisor": 120.0, "researcher": 450.0, "coder": 820.0}
        self.hourly_spend_usd = 4.82

    def format_grafana_metrics(self) -> str:
        lines = [
            "# HELP swarm_p95_latency_ms 95th percentile latency per agent role",
            "# TYPE swarm_p95_latency_ms gauge"
        ]
        for role, lat in self.p95_latencies.items():
            lines.append(f'swarm_p95_latency_ms{{role="{role}"}} {lat:.1f}')
        lines.append(f"swarm_hourly_spend_usd {self.hourly_spend_usd:.2f}")
        return "\n".join(lines)
