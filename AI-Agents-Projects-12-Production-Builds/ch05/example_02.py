from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class MetricAnomaly(BaseModel):
    metric_name: str
    baseline_mean: float
    baseline_std: float
    current_value: float
    z_score: float = Field(description="Standard deviations above baseline")
    is_anomalous: bool


@dataclass
class AsyncCircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout_sec: float = 30.0
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    opened_at: float = 0.0

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if (time.monotonic() - self.opened_at) >= self.recovery_timeout_sec:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = time.monotonic()


class PrometheusQueryEngine:
    def __init__(self, base_url: str, timeout_sec: float = 4.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec
        self.breaker = AsyncCircuitBreaker()

    async def fetch_range_series(self, promql: str, samples: list[float]) -> list[float]:
        """Simulates async PromQL /api/v1/query_range with circuit-breaker protection."""
        if not self.breaker.allow_request():
            raise RuntimeError(f"Prometheus circuit breaker OPEN for query: {promql}")

        try:
            await asyncio.sleep(0.015)
            if not samples:
                raise ValueError("Empty metric series returned by Prometheus")
            self.breaker.record_success()
            return samples
        except Exception:
            self.breaker.record_failure()
            raise

    @staticmethod
    def score_anomaly(metric_name: str, series: list[float], z_threshold: float = 3.0) -> MetricAnomaly:
        if len(series) < 4:
            raise ValueError("Need at least 4 samples to compute baseline statistics")
        baseline = series[:-1]
        current = series[-1]
        mean = sum(baseline) / len(baseline)
        variance = sum((x - mean) ** 2 for x in baseline) / len(baseline)
        std = max(math.sqrt(variance), 1e-6)
        z_score = (current - mean) / std
        return MetricAnomaly(
            metric_name=metric_name,
            baseline_mean=round(mean, 3),
            baseline_std=round(std, 3),
            current_value=round(current, 3),
            z_score=round(z_score, 2),
            is_anomalous=z_score >= z_threshold,
        )


async def main() -> None:
    engine = PrometheusQueryEngine("http://prometheus.monitoring.svc:9090")
    latency_samples = [138.0, 141.0, 145.0, 139.0, 144.0, 142.0, 14800.0]
    error_rate_samples = [0.002, 0.003, 0.002, 0.004, 0.003, 0.002, 0.418]

    lat_series, err_series = await asyncio.gather(
        engine.fetch_range_series('histogram_quantile(0.99, rate(http_request_duration_ms_bucket[5m]))', latency_samples),
        engine.fetch_range_series('rate(http_requests_total{status=~"5.."}[5m])', error_rate_samples),
    )

    anomalies = [
        engine.score_anomaly("http_p99_latency_ms", lat_series),
        engine.score_anomaly("http_5xx_error_ratio", err_series),
    ]
    for item in anomalies:
        print(item.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())
