from __future__ import annotations

from pydantic import BaseModel


class OutreachDispatchGuard(BaseModel):
    grounding_passed: bool
    compliance_passed: bool
    crm_stage_protected: bool


def evaluate_dispatch_safety(
    ungrounded_claims: list[str],
    compliance_violations: list[str],
    current_crm_stage: str,
) -> tuple[bool, OutreachDispatchGuard]:
    protected = current_crm_stage in {"Negotiation", "Closed-Won", "Closed-Lost"}
    guard = OutreachDispatchGuard(
        grounding_passed=len(ungrounded_claims) == 0,
        compliance_passed=len(compliance_violations) == 0,
        crm_stage_protected=protected,
    )
    can_send = guard.grounding_passed and guard.compliance_passed
    return can_send, guard


if __name__ == "__main__":
    ok, state = evaluate_dispatch_safety(
        ungrounded_claims=["$45M", "Series C"],
        compliance_violations=[],
        current_crm_stage="Negotiation",
    )
    print(f"Dispatch allowed={ok} state={state.model_dump_json()}")
