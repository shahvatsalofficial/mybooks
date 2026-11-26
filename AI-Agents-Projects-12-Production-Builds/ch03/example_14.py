from __future__ import annotations

from typing import List
from pydantic import BaseModel


class SupportEvalCase(BaseModel):
    ticket_id: str
    expected_domain: str
    predicted_domain: str
    sla_breached: bool
    policy_violation: bool


class EvalSummary(BaseModel):
    total_cases: int
    routing_accuracy: float
    sla_compliance_rate: float
    policy_violations: int
    release_gate_passed: bool


class ShadowEvalHarness:
    """Computes release-gating metrics across support swarm evaluation runs."""

    @staticmethod
    def evaluate(cases: List[SupportEvalCase]) -> EvalSummary:
        total = len(cases)
        correct = sum(1 for c in cases if c.expected_domain == c.predicted_domain)
        sla_ok = sum(1 for c in cases if not c.sla_breached)
        violations = sum(1 for c in cases if c.policy_violation)
        acc = round(correct / total, 4) if total else 0.0
        sla_rate = round(sla_ok / total, 4) if total else 0.0
        passed = acc >= 0.92 and sla_rate >= 0.99 and violations == 0
        return EvalSummary(
            total_cases=total,
            routing_accuracy=acc,
            sla_compliance_rate=sla_rate,
            policy_violations=violations,
            release_gate_passed=passed,
        )


if __name__ == "__main__":
    sample = [
        SupportEvalCase(
            ticket_id="T1",
            expected_domain="tech_ops",
            predicted_domain="tech_ops",
            sla_breached=False,
            policy_violation=False,
        ),
        SupportEvalCase(
            ticket_id="T2",
            expected_domain="billing",
            predicted_domain="billing",
            sla_breached=False,
            policy_violation=False,
        ),
    ]
    print(ShadowEvalHarness.evaluate(sample).model_dump_json(indent=2))
