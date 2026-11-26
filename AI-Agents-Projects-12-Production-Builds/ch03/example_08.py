from __future__ import annotations

from enum import Enum
from typing import Dict
from pydantic import BaseModel, Field


class PolicyVerdict(str, Enum):
    APPROVED = "approved"
    ESCALATE_HUMAN = "escalate_human"
    DENIED_CIRCUIT_BREAKER = "denied_circuit_breaker"


class PolicyCheckResult(BaseModel):
    verdict: PolicyVerdict
    requested_usd: float
    approved_usd: float
    reason: str


class PolicyCapGuard:
    """Deterministic financial policy engine enforcing hard refund/credit caps."""

    def __init__(
        self,
        rolling_30d_tenant_cap_usd: float = 1500.0,
        global_daily_cap_usd: float = 10000.0,
    ) -> None:
        self._tenant_30d_cap = rolling_30d_tenant_cap_usd
        self._global_daily_cap = global_daily_cap_usd
        self._tenant_30d_spent: Dict[str, float] = {}
        self._global_daily_spent: float = 0.0

    def evaluate(
        self,
        tenant_id: str,
        max_auto_refund_usd: float,
        requested_usd: float,
    ) -> PolicyCheckResult:
        if requested_usd <= 0:
            return PolicyCheckResult(
                verdict=PolicyVerdict.ESCALATE_HUMAN,
                requested_usd=requested_usd,
                approved_usd=0.0,
                reason="Non-positive refund amount requires manual review.",
            )

        if (self._global_daily_spent + requested_usd) > self._global_daily_cap:
            return PolicyCheckResult(
                verdict=PolicyVerdict.DENIED_CIRCUIT_BREAKER,
                requested_usd=requested_usd,
                approved_usd=0.0,
                reason="Global daily autonomous refund circuit breaker reached.",
            )

        if requested_usd > max_auto_refund_usd:
            return PolicyCheckResult(
                verdict=PolicyVerdict.ESCALATE_HUMAN,
                requested_usd=requested_usd,
                approved_usd=0.0,
                reason=(
                    f"Requested ${requested_usd:.2f} exceeds per-ticket cap "
                    f"of ${max_auto_refund_usd:.2f}."
                ),
            )

        tenant_spent = self._tenant_30d_spent.get(tenant_id, 0.0)
        if (tenant_spent + requested_usd) > self._tenant_30d_cap:
            return PolicyCheckResult(
                verdict=PolicyVerdict.ESCALATE_HUMAN,
                requested_usd=requested_usd,
                approved_usd=0.0,
                reason=(
                    f"Tenant 30-day rolling total (${tenant_spent + requested_usd:.2f}) "
                    f"exceeds ${self._tenant_30d_cap:.2f} cap."
                ),
            )

        self._tenant_30d_spent[tenant_id] = tenant_spent + requested_usd
        self._global_daily_spent += requested_usd
        return PolicyCheckResult(
            verdict=PolicyVerdict.APPROVED,
            requested_usd=requested_usd,
            approved_usd=requested_usd,
            reason="Within per-ticket, rolling tenant, and global daily caps.",
        )


if __name__ == "__main__":
    guard = PolicyCapGuard(rolling_30d_tenant_cap_usd=1500.0, global_daily_cap_usd=10000.0)
    ok = guard.evaluate("ten_acme_01", max_auto_refund_usd=500.0, requested_usd=350.0)
    blocked = guard.evaluate("ten_acme_01", max_auto_refund_usd=500.0, requested_usd=45000.0)
    print("Valid request:", ok.model_dump())
    print("Attack/Over-cap request:", blocked.model_dump())
