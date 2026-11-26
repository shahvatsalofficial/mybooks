from __future__ import annotations

from enum import IntEnum
from pydantic import BaseModel, Field


class RiskTier(IntEnum):
    TIER_0_READ_ONLY = 0
    TIER_1_LOW_BLAST = 1
    TIER_2_MEDIUM_BLAST = 2
    TIER_3_DESTRUCTIVE = 3


class RunbookSpec(BaseModel):
    runbook_id: str
    title: str
    tier: RiskTier
    max_affected_pods_pct: float = Field(ge=0.0, le=100.0)
    requires_human_approval: bool
    supports_auto_rollback: bool
    required_params: list[str]


RUNBOOK_CATALOG: dict[str, RunbookSpec] = {
    "RB-RESTART-POD": RunbookSpec(
        runbook_id="RB-RESTART-POD",
        title="Evict single CrashLooping pod respecting PDB",
        tier=RiskTier.TIER_1_LOW_BLAST,
        max_affected_pods_pct=10.0,
        requires_human_approval=False,
        supports_auto_rollback=False,
        required_params=["namespace", "pod_name"],
    ),
    "RB-ROLLBACK-DEPLOYMENT": RunbookSpec(
        runbook_id="RB-ROLLBACK-DEPLOYMENT",
        title="Roll back Kubernetes Deployment to previous ReplicaSet revision",
        tier=RiskTier.TIER_2_MEDIUM_BLAST,
        max_affected_pods_pct=100.0,
        requires_human_approval=True,
        supports_auto_rollback=True,
        required_params=["namespace", "deployment", "target_revision"],
    ),
    "RB-DB-PRIMARY-FAILOVER": RunbookSpec(
        runbook_id="RB-DB-PRIMARY-FAILOVER",
        title="Promote read replica to primary PostgreSQL node",
        tier=RiskTier.TIER_3_DESTRUCTIVE,
        max_affected_pods_pct=100.0,
        requires_human_approval=True,
        supports_auto_rollback=False,
        required_params=["cluster_id", "target_replica"],
    ),
}


def authorize_runbook_plan(
    runbook_id: str,
    params: dict[str, str],
    confidence: float,
) -> tuple[RunbookSpec, str]:
    spec = RUNBOOK_CATALOG.get(runbook_id)
    if spec is None:
        raise KeyError(f"Unregistered runbook_id: {runbook_id}")

    missing = [p for p in spec.required_params if not params.get(p)]
    if missing:
        raise ValueError(f"Missing required parameters for {runbook_id}: {missing}")

    if spec.tier == RiskTier.TIER_3_DESTRUCTIVE:
        return spec, "BLOCKED_FOR_AGENT_DUAL_SRE_REQUIRED"
    if spec.requires_human_approval or confidence < 0.90:
        return spec, "PENDING_HUMAN_APPROVAL"
    return spec, "AUTO_APPROVED"


if __name__ == "__main__":
    spec, decision = authorize_runbook_plan(
        "RB-ROLLBACK-DEPLOYMENT",
        {"namespace": "prod-payments", "deployment": "checkout-orchestrator", "target_revision": "41"},
        confidence=0.94,
    )
    print(f"Runbook={spec.runbook_id} Tier={spec.tier.name} Decision={decision}")
