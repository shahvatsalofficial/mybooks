import time
from typing import Dict, Any

class AgentPrometheusMetrics:
    """Collects and formats Prometheus metrics for autonomous agent loops."""

    def __init__(self):
        self.metrics = {
            "agent_reasoning_hops_total": {},
            "agent_tool_duration_seconds": {},
            "agent_token_consumption_total": {}
        }

    def record_turn_metrics(self, agent_name: str, model: str, hops: int, tokens: int, tool_duration_s: float):
        labels = f'agent="{agent_name}",model="{model}"'
        self.metrics["agent_reasoning_hops_total"][labels] = self.metrics["agent_reasoning_hops_total"].get(labels, 0) + hops
        self.metrics["agent_token_consumption_total"][labels] = self.metrics["agent_token_consumption_total"].get(labels, 0) + tokens
        self.metrics["agent_tool_duration_seconds"][labels] = round(tool_duration_s, 3)

    def export_prometheus_text(self) -> str:
        lines = []
        for metric_name, entries in self.metrics.items():
            lines.append(f"# TYPE {metric_name} gauge")
            for labels, val in entries.items():
                lines.append(f"{metric_name}{{{labels}}} {val}")
        return "\n".join(lines)

if __name__ == "__main__":
    prom = AgentPrometheusMetrics()
    prom.record_turn_metrics("AutonomousSRE", "gemini-2.5-pro", hops=4, tokens=2840, tool_duration_s=1.24)
    print("Prometheus Exposition Output:\n" + prom.export_prometheus_text())
