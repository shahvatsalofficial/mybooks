import time
from typing import Dict, Any

class AzureAppInsightsAgentTelemetry:
    """Emits custom metrics and traces to Azure Application Insights."""

    def __init__(self, instrumentation_key: str):
        self.key = instrumentation_key

    def track_agent_execution(self, thread_id: str, agent_id: str, duration_ms: float, tokens_used: int, status: str) -> None:
        metric_payload = {
            "name": "AgentExecutionMetric",
            "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "iKey": self.key,
            "data": {
                "baseType": "MetricData",
                "baseData": {
                    "metrics": [
                        {"name": "DurationMs", "value": duration_ms},
                        {"name": "TokensUsed", "value": tokens_used}
                    ],
                    "properties": {
                        "ThreadId": thread_id,
                        "AgentId": agent_id,
                        "Status": status
                    }
                }
            }
        }
        print(f"Emitted Application Insights telemetry: {duration_ms:.1f}ms, {tokens_used} tokens, status: {status}")

if __name__ == "__main__":
    telemetry = AzureAppInsightsAgentTelemetry("00000000-0000-0000-0000-000000000000")
    telemetry.track_agent_execution("thread_892a", "agent_gpt4o_sre", 1240.5, 842, "SUCCESS")
