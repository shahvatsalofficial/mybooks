from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from pydantic import BaseModel, Field


class Severity(str, Enum):
    P0 = "P0"  # Critical outage / security breach
    P1 = "P1"  # Production degraded
    P2 = "P2"  # Partial feature issue
    P3 = "P3"  # General question / feature request


class SlaAssessment(BaseModel):
    severity: Severity
    sla_budget_minutes: int
    deadline_utc: datetime
    remaining_minutes: float
    is_at_risk: bool
    queue_priority_score: int = Field(ge=0, le=1000)


class SlaDeadlineCalculator:
    """Computes contractual SLA deadlines and queue priority scores."""

    CRITICAL_KEYWORDS = ("502", "503", "outage", "down", "unauthorized", "breach", "payouts failing")

    @classmethod
    def assess(
        cls,
        body_clean: str,
        tier: str,
        p1_sla_minutes: int,
        p2_sla_minutes: int,
        received_at: datetime,
        now_utc: datetime | None = None,
    ) -> SlaAssessment:
        now = now_utc or datetime.now(timezone.utc)
        lowered = body_clean.lower()

        if any(k in lowered for k in ("breach", "unauthorized", "compromised")):
            severity = Severity.P0
            budget_min = max(5, p1_sla_minutes // 2)
        elif any(k in lowered for k in cls.CRITICAL_KEYWORDS):
            severity = Severity.P1
            budget_min = p1_sla_minutes
        elif "error" in lowered or "failed" in lowered or "timeout" in lowered:
            severity = Severity.P2
            budget_min = p2_sla_minutes
        else:
            severity = Severity.P3
            budget_min = p2_sla_minutes * 4

        deadline = received_at + timedelta(minutes=budget_min)
        remaining = round((deadline - now).total_seconds() / 60.0, 2)
        at_risk = remaining <= (budget_min * 0.25)

        tier_bonus = {"enterprise": 400, "growth": 200, "starter": 50}.get(tier, 50)
        sev_bonus = {"P0": 550, "P1": 400, "P2": 200, "P3": 50}[severity.value]
        urgency_bonus = 50 if at_risk else 0
        score = min(1000, tier_bonus + sev_bonus + urgency_bonus)

        return SlaAssessment(
            severity=severity,
            sla_budget_minutes=budget_min,
            deadline_utc=deadline,
            remaining_minutes=remaining,
            is_at_risk=at_risk,
            queue_priority_score=score,
        )


if __name__ == "__main__":
    received = datetime.now(timezone.utc) - timedelta(minutes=12)
    assessment = SlaDeadlineCalculator.assess(
        body_clean="Production payouts are failing with 502s since 06:40 UTC.",
        tier="enterprise",
        p1_sla_minutes=15,
        p2_sla_minutes=60,
        received_at=received,
    )
    print(assessment.model_dump_json(indent=2))
