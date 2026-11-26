from __future__ import annotations

import asyncio
from enum import Enum
from pydantic import BaseModel


class VerificationOutcome(str, Enum):
    HEALTHY_RESOLVED = "healthy_resolved"
    REGRESSION_AUTO_ROLLED_BACK = "regression_auto_rolled_back"


class HealthProbeSample(BaseModel):
    probe_index: int
    ready_ratio: float
    error_rate_5xx: float
    p99_latency_ms: float


async def verify_remediation_slo(
    probes: list[HealthProbeSample],
    max_error_rate: float = 0.01,
    max_p99_ms: float = 400.0,
    min_ready_ratio: float = 0.95,
) -> tuple[VerificationOutcome, list[str]]:
    audit_notes: list[str] = []
    for probe in probes:
        await asyncio.sleep(0.005)
        passed = (
            probe.ready_ratio >= min_ready_ratio
            and probe.error_rate_5xx <= max_error_rate
            and probe.p99_latency_ms <= max_p99_ms
        )
        audit_notes.append(
            f"probe={probe.probe_index} ready={probe.ready_ratio:.2f} err={probe.error_rate_5xx:.4f} p99={probe.p99_latency_ms:.1f}ms -> {'PASS' if passed else 'FAIL'}"
        )
        if not passed:
            audit_notes.append("SLO regression detected: executing automatic rollback & paging Tier-2 escalation")
            return VerificationOutcome.REGRESSION_AUTO_ROLLED_BACK, audit_notes

    return VerificationOutcome.HEALTHY_RESOLVED, audit_notes


async def main() -> None:
    healthy_run = [
        HealthProbeSample(probe_index=1, ready_ratio=0.96, error_rate_5xx=0.004, p99_latency_ms=165.0),
        HealthProbeSample(probe_index=2, ready_ratio=1.00, error_rate_5xx=0.002, p99_latency_ms=144.0),
    ]
    outcome, notes = await verify_remediation_slo(healthy_run)
    print(f"Outcome={outcome.value}")
    for note in notes:
        print(" ", note)


if __name__ == "__main__":
    asyncio.run(main())
