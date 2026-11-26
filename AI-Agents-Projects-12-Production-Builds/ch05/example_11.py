from __future__ import annotations

from pydantic import BaseModel, Field


class ClusterBudgetState(BaseModel):
    total_replicas: int = Field(ge=1)
    ready_replicas: int = Field(ge=0)
    min_available: int = Field(ge=0)


class BlastRadiusDecision(BaseModel):
    allowed: bool
    max_batch_size: int
    reason: str


def evaluate_blast_radius(state: ClusterBudgetState, requested_batch: int) -> BlastRadiusDecision:
    disruption_headroom = state.ready_replicas - state.min_available
    if disruption_headroom <= 0:
        return BlastRadiusDecision(
            allowed=False,
            max_batch_size=0,
            reason=f"PDB violation: ready={state.ready_replicas} <= min_available={state.min_available}",
        )
    safe_batch = min(requested_batch, disruption_headroom, max(1, state.total_replicas // 4))
    return BlastRadiusDecision(
        allowed=True,
        max_batch_size=safe_batch,
        reason=f"Approved canary batch={safe_batch} within PDB headroom={disruption_headroom}",
    )


if __name__ == "__main__":
    healthy_headroom = ClusterBudgetState(total_replicas=12, ready_replicas=10, min_available=8)
    tight_pdb = ClusterBudgetState(total_replicas=12, ready_replicas=8, min_available=8)
    print(evaluate_blast_radius(healthy_headroom, requested_batch=6).model_dump_json())
    print(evaluate_blast_radius(tight_pdb, requested_batch=2).model_dump_json())
