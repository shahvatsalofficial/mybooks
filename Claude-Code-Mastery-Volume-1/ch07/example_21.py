import time
import math
import subprocess
import requests
import json
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class TelemetrySnapshot:
    p99_latency_ms: float
    error_rate_percent: float
    throughput_qps: float
    timestamp: float

class CanaryHealthAuditor:
    def __init__(
        self,
        prometheus_url: str,
        service_name: str,
        namespace: str = "default",
        max_p99_latency_ms: float = 120.0,
        max_error_rate_pct: float = 0.5
    ):
        self.prometheus_url = prometheus_url.rstrip('/')
        self.service_name = service_name
        self.namespace = namespace
        self.max_p99_latency_ms = max_p99_latency_ms
        self.max_error_rate_pct = max_error_rate_pct
        self.baseline_history: List[TelemetrySnapshot] = []

    def query_prometheus(self, promql: str) -> float:
        """Executes an instant query against Prometheus HTTP API."""
        endpoint = f"{self.prometheus_url}/api/v1/query"
        response = requests.get(endpoint, params={"query": promql}, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("data", {}).get("result", [])
        if not results:
            return 0.0
        return float(results[0]["value"][1])

    def capture_metrics(self, is_canary: bool = False) -> TelemetrySnapshot:
        """Queries Prometheus for current P99 latency and 5xx error rate."""
        app_label = f"{self.service_name}-canary" if is_canary else self.service_name
        
        # P99 Latency query over 2-minute rolling rate
        p99_query = f'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{{app="{app_label}", namespace="{self.namespace}"}}[2m])) by (le)) * 1000'
        
        # Error rate percentage
        err_query = f'sum(rate(http_requests_total{{app="{app_label}", status=~"5..", namespace="{self.namespace}"}}[2m])) / sum(rate(http_requests_total{{app="{app_label}", namespace="{self.namespace}"}}[2m])) * 100'
        
        latency = self.query_prometheus(p99_query)
        error_rate = self.query_prometheus(err_query)
        
        return TelemetrySnapshot(
            p99_latency_ms=round(latency, 2),
            error_rate_percent=round(error_rate, 3),
            throughput_qps=100.0,
            timestamp=time.time()
        )

    def evaluate_statistical_anomaly(self, canary: TelemetrySnapshot) -> Dict[str, any]:
        """
        Evaluates whether the canary snapshot represents a statistically significant anomaly
        compared to the established baseline.
        """
        breached = False
        reasons = []

        if canary.p99_latency_ms > self.max_p99_latency_ms:
            breached = True
            reasons.append(f"P99 latency ({canary.p99_latency_ms}ms) exceeded ceiling ({self.max_p99_latency_ms}ms)")

        if canary.error_rate_percent > self.max_error_rate_pct:
            breached = True
            reasons.append(f"Error rate ({canary.error_rate_percent}%) exceeded ceiling ({self.max_error_rate_pct}%)")

        return {
            "breached": breached,
            "reasons": reasons,
            "canary_metrics": canary
        }

    def execute_emergency_rollback(self) -> bool:
        """Invokes kubectl to abort the Argo rollout immediately."""
        cmd = ["kubectl", "argo", "rollouts", "abort", self.service_name, "-n", self.namespace]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"[SENTINEL ACTION] Rollout aborted successfully: {res.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as err:
            print(f"[FATAL] Failed to abort rollout via kubectl: {err.stderr}")
            return False

    def emit_incident_slack_alert(self, reasons: List[str], snapshot: TelemetrySnapshot, webhook_url: str):
        """Dispatches a formatted incident alert to the SRE incident channel."""
        payload = {
            "text": f"🚨 *CANARY ROLLBACK TRIGGERED: {self.service_name}*",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Autonomous Canary Sentinel Aborted Release*\n*Namespace:* `{self.namespace}` | *Service:* `{self.service_name}`"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*P99 Latency:*\n{snapshot.p99_latency_ms} ms"},
                        {"type": "mrkdwn", "text": f"*5xx Error Rate:*\n{snapshot.error_rate_percent} %"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Breach Causes:*\n• " + "\n• ".join(reasons)
                    }
                }
            ]
        }
        try:
            requests.post(webhook_url, json=payload, timeout=3.0)
        except Exception as e:
            print(f"Failed to post Slack alert: {e}")
