from __future__ import annotations

import hashlib
import hmac
import json
import time
from pydantic import BaseModel


class ApprovalTokenPayload(BaseModel):
    incident_id: str
    runbook_id: str
    namespace: str
    target: str
    expires_at: int


class HmacApprovalGate:
    def __init__(self, signing_secret: bytes) -> None:
        if len(signing_secret) < 16:
            raise ValueError("Signing secret must be at least 16 bytes")
        self._secret = signing_secret

    def issue_token(self, payload: ApprovalTokenPayload) -> str:
        raw = payload.model_dump_json().encode("utf-8")
        sig = hmac.new(self._secret, raw, hashlib.sha256).hexdigest()
        return f"{raw.hex()}.{sig}"

    def verify_approval(self, token: str, approver_id: str, now_epoch: int | None = None) -> ApprovalTokenPayload:
        try:
            hex_body, provided_sig = token.split(".", 1)
            raw = bytes.fromhex(hex_body)
        except ValueError as exc:
            raise PermissionError("Malformed approval token") from exc

        expected_sig = hmac.new(self._secret, raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(provided_sig, expected_sig):
            raise PermissionError("Invalid HMAC signature on approval token")

        payload = ApprovalTokenPayload.model_validate(json.loads(raw.decode("utf-8")))
        current = now_epoch if now_epoch is not None else int(time.time())
        if current > payload.expires_at:
            raise PermissionError(f"Approval token expired at {payload.expires_at}")
        if not approver_id.strip():
            raise PermissionError("Approver identity cannot be empty")
        return payload


if __name__ == "__main__":
    gate = HmacApprovalGate(b"prod-triage-hmac-secret-key-2026")
    now = 1_795_572_851
    req = ApprovalTokenPayload(
        incident_id="INC-7E4B91C20F8A3D14",
        runbook_id="RB-ROLLBACK-DEPLOYMENT",
        namespace="prod-payments",
        target="checkout-orchestrator",
        expires_at=now + 300,
    )
    signed_token = gate.issue_token(req)
    verified = gate.verify_approval(signed_token, approver_id="sre-oncall-vatsal", now_epoch=now + 42)
    print(f"Verified approval for {verified.incident_id} -> {verified.runbook_id} (len={len(signed_token)})")
