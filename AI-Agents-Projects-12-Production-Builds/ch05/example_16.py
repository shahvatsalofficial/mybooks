from __future__ import annotations

from pydantic import BaseModel


class RemediationGuardPolicy(BaseModel):
    min_available_pods: int = 8
    deploy_correlation_threshold: float = 0.85


def select_safe_remediation(
    ready_pods: int,
    deploy_posterior: float,
    policy: RemediationGuardPolicy,
) -> str:
    if deploy_posterior >= policy.deploy_correlation_threshold:
        return "TIER_2_ROLLBACK_DEPLOYMENT_WITH_HMAC_GATE"
    if ready_pods <= policy.min_available_pods:
        return "BLOCK_POD_EVICTION_PDB_PROTECTED_ESCALATE"
    return "TIER_1_CANARY_SINGLE_POD_EVICTION"


if __name__ == "__main__":
    pol = RemediationGuardPolicy()
    print("Scenario A (commit correlated):", select_safe_remediation(ready_pods=6, deploy_posterior=0.96, policy=pol))
    print("Scenario B (low PDB headroom):", select_safe_remediation(ready_pods=7, deploy_posterior=0.40, policy=pol))
