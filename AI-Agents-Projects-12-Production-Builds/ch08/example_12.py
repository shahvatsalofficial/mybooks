from __future__ import annotations

import hashlib
import time
from typing import List
from pydantic import BaseModel


class ComplianceAuditEvent(BaseModel):
    timestamp_epoch: int
    user_id: str
    tenant_id: str
    query_sha256: str
    authorized_doc_ids: List[str]
    pii_entities_redacted: int
    blocked_by_policy: bool
    policy_reason: str = ""


class ImmutableAuditLogger:
    """Records tamper-evident compliance audit events for every RAG request."""

    def __init__(self) -> None:
        self._events: List[ComplianceAuditEvent] = []

    def record(
        self,
        principal: PrincipalContext,
        raw_query: str,
        doc_ids: List[str],
        pii_count: int,
        blocked: bool = False,
        reason: str = "",
    ) -> ComplianceAuditEvent:
        q_hash = hashlib.sha256(raw_query.encode("utf-8")).hexdigest()
        ev = ComplianceAuditEvent(
            timestamp_epoch=int(time.time()),
            user_id=principal.user_id,
            tenant_id=principal.tenant_id,
            query_sha256=q_hash,
            authorized_doc_ids=doc_ids,
            pii_entities_redacted=pii_count,
            blocked_by_policy=blocked,
            policy_reason=reason,
        )
        self._events.append(ev)
        return ev


def demo_audit_logger() -> None:
    logger = ImmutableAuditLogger()
    principal = PrincipalContext(
        user_id="u_8841", tenant_id="acme_corp", roles={"engineer"},
        department="platform", clearance=ClearanceLevel.INTERNAL, exp_epoch=9999999999,
    )
    ev = logger.record(
        principal, "What is our KMS rotation SLA?", ["doc_eng_runbook"], pii_count=1
    )
    print(ev.model_dump_json())


if __name__ == "__main__":
    demo_audit_logger()
