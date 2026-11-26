from __future__ import annotations


class DualSreQuorumGate:
    def __init__(self) -> None:
        self.approvals: dict[str, set[str]] = {}

    def record_approval(self, incident_id: str, approver_id: str) -> tuple[bool, int]:
        signers = self.approvals.setdefault(incident_id, set())
        signers.add(approver_id)
        return len(signers) >= 2, len(signers)


if __name__ == "__main__":
    quorum = DualSreQuorumGate()
    print("First sign-off:", quorum.record_approval("INC-991", "sre-alice"))
    print("Duplicate sign-off:", quorum.record_approval("INC-991", "sre-alice"))
    print("Second distinct sign-off:", quorum.record_approval("INC-991", "sre-bob"))
