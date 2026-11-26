from typing import Protocol

class MetricsCollector(Protocol):
    def record_gauge(self, name: str, value: float) -> None:
        ...

class CloudWatchCollector:
    """Zero inheritance from MetricsCollector!"""
    def record_gauge(self, name: str, value: float) -> None:
        # Sends metrics directly to AWS CloudWatch API...
        pass

def track_service_health(collector: MetricsCollector, cpu_util: float) -> None:
    collector.record_gauge("cpu.utilization", cpu_util)

# 100% legal, valid, and type-safe under Mypy!
track_service_health(CloudWatchCollector(), 88.5)
