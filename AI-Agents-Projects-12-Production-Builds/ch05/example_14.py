from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pydantic import BaseModel


class AuditEvent(BaseModel):
    seq: int
    timestamp_utc: datetime
    incident_id: str
    actor: str
    action: str
    prev_hash: str
    entry_hash: str = ""


class ImmutableAuditLedger:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, incident_id: str, actor: str, action: str) -> AuditEvent:
        prev_hash = self.events[-1].entry_hash if self.events else "0" * 64
        seq = len(self.events) + 1
        ts = datetime.now(timezone.utc)
        material = f"{seq}|{ts.isoformat()}|{incident_id}|{actor}|{action}|{prev_hash}"
        entry_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
        event = AuditEvent(
            seq=seq,
            timestamp_utc=ts,
            incident_id=incident_id,
            actor=actor,
            action=action,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )
        self.events.append(event)
        return event


if __name__ == "__main__":
    ledger = ImmutableAuditLedger()
    e1 = ledger.append("INC-7E4B91C20F8A3D14", "triage-agent", "CORRELATED_COMMIT:9f3a2c1")
    e2 = ledger.append("INC-7E4B91C20F8A3D14", "sre-oncall-vatsal", "APPROVED_RUNBOOK:RB-ROLLBACK-DEPLOYMENT")
    e3 = ledger.append("INC-7E4B91C20F8A3D14", "triage-agent", "VERIFIED_SLO:healthy_resolved")
    for ev in (e1, e2, e3):
        print(f"#{ev.seq} actor={ev.actor} action={ev.action} hash={ev.entry_hash[:12]}...")
