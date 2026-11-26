from __future__ import annotations

import hashlib
from pydantic import BaseModel

PROTECTED_STAGES = {"Negotiation", "Contract Sent", "Closed-Won", "Closed-Lost"}
AGENT_OWNED_FIELDS = {"meddic_score", "intent_score", "routing_tier", "last_enriched_at"}


class CrmSyncPlan(BaseModel):
    idempotency_key: str
    record_id: str
    patch_payload: dict[str, object]
    skipped_protected_fields: list[str]


def compute_safe_crm_diff(
    record_id: str,
    current_crm_state: dict[str, object],
    proposed_updates: dict[str, object],
) -> CrmSyncPlan:
    patch: dict[str, object] = {}
    skipped: list[str] = []
    current_stage = str(current_crm_state.get("dealstage", ""))

    for field, new_val in proposed_updates.items():
        if field == "dealstage" and current_stage in PROTECTED_STAGES:
            skipped.append(field)
            continue
        if field not in AGENT_OWNED_FIELDS and field != "dealstage":
            skipped.append(field)
            continue
        if current_crm_state.get(field) != new_val:
            patch[field] = new_val

    key_material = f"{record_id}:{sorted(patch.items())}"
    idem_key = hashlib.sha256(key_material.encode("utf-8")).hexdigest()[:16]
    return CrmSyncPlan(
        idempotency_key=idem_key,
        record_id=record_id,
        patch_payload=patch,
        skipped_protected_fields=skipped,
    )


if __name__ == "__main__":
    crm_row = {"dealstage": "Negotiation", "meddic_score": 72, "intent_score": 40.0, "owner_id": "ae-104"}
    agent_updates = {"dealstage": "MQL_New", "meddic_score": 89, "intent_score": 57.33, "owner_id": "bot-01"}
    plan = compute_safe_crm_diff("OPP-90211", crm_row, agent_updates)
    print(plan.model_dump_json(indent=2))
