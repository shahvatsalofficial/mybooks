import time
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class SwarmMetricSample(BaseModel):
    metric_name: str
    labels: Dict[str, str]
    value: float
    timestamp: float = Field(default_factory=time.time)

class PrometheusSwarmExporter:
    """Exports multi-agent orchestration telemetry in standard Prometheus text format."""
    
    def __init__(self, namespace: str = "swarm_orchestrator"):
        self.namespace = namespace
        self.turn_durations: List[float] = []
        self.failed_delegations: int = 0
        self.active_workers: int = 0
        self.token_burn_counter: Dict[str, int] = {}
        self.alert_webhook_url: str = "https://alerts.infra.internal/v1/swarm-breach"

    def record_turn_latency(self, worker_id: str, duration_sec: float) -> None:
        self.turn_durations.append(duration_sec)
        if duration_sec > 4.5:
            self._dispatch_latency_alert(worker_id, duration_sec)

    def record_worker_failure(self, worker_id: str, error_type: str) -> None:
        self.failed_delegations += 1
        print(f"[METRIC ALERT] Worker '{worker_id}' delegation failure: {error_type}")

    def update_token_spend(self, agent_role: str, tokens: int) -> None:
        self.token_burn_counter[agent_role] = self.token_burn_counter.get(agent_role, 0) + tokens

    def _dispatch_latency_alert(self, worker_id: str, latency: float) -> None:
        payload = {
            "severity": "WARNING",
            "alert_rule": "AgentTurnLatencyHigh",
            "worker_id": worker_id,
            "latency_observed": latency,
            "threshold": 4.5
        }
        print(f"[WEBHOOK DISPATCH] Alert triggered: {payload['alert_rule']} on {worker_id} ({latency:.2f}s)")

    def render_prometheus_text(self) -> str:
        lines = [
            f"# HELP {self.namespace}_failed_delegations_total Total unhandled delegation failures",
            f"# TYPE {self.namespace}_failed_delegations_total counter",
            f"{self.namespace}_failed_delegations_total {self.failed_delegations}",
            f"# HELP {self.namespace}_active_workers_gauge Currently executing worker agents",
            f"# TYPE {self.namespace}_active_workers_gauge gauge",
            f"{self.namespace}_active_workers_gauge {self.active_workers}",
            f"# HELP {self.namespace}_tokens_total Total tokens consumed by agent role",
            f"# TYPE {self.namespace}_tokens_total counter"
        ]
        for role, count in self.token_burn_counter.items():
            clean_role = role.replace(" ", "_").lower()
            lines.append(f'{self.namespace}_tokens_total{{agent_role="{clean_role}"}} {count}')
        return "\n".join(lines) + "\n"
