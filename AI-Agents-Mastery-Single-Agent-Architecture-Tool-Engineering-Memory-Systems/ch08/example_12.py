from typing import Dict

class PrometheusAgentMetrics:
    def __init__(self):
        self.counters: Dict[str, float] = {
            "agent_tokens_total": 0.0,
            "agent_turns_total": 0.0,
            "agent_cost_usd_total": 0.0
        }

    def record_turn(self, input_tokens: int, output_tokens: int, cost_usd: float) -> None:
        self.counters["agent_tokens_total"] += (input_tokens + output_tokens)
        self.counters["agent_turns_total"] += 1.0
        self.counters["agent_cost_usd_total"] += cost_usd

    def generate_prometheus_payload(self) -> str:
        lines = [
            "# HELP agent_tokens_total Cumulative tokens consumed by autonomous agents",
            "# TYPE agent_tokens_total counter",
            f"agent_tokens_total {self.counters['agent_tokens_total']}",
            "# HELP agent_cost_usd_total Cumulative cost in USD",
            "# TYPE agent_cost_usd_total counter",
            f"agent_cost_usd_total {self.counters['agent_cost_usd_total']:.4f}"
        ]
        return "\n".join(lines)

metrics = PrometheusAgentMetrics()
metrics.record_turn(1500, 320, 0.0091)
print(metrics.generate_prometheus_payload())
