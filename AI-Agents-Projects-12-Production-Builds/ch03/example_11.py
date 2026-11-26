from __future__ import annotations

import hashlib
import hmac
import time
from pydantic import BaseModel


class ApprovalRequest(BaseModel):
    approval_id: str
    ticket_id: str
    tenant_id: str
    requested_usd: float
    expires_at_epoch: int
    signature: str


class DualApprovalGate:
    """Issues and verifies HMAC-signed human approval tokens for Tier-3 refunds."""

    def __init__(self, secret: str, ttl_seconds: int = 1800) -> None:
        self._secret = secret.encode("utf-8")
        self._ttl = ttl_seconds

    def _sign(self, payload: str) -> str:
        return hmac.new(self._secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def create_request(self, ticket_id: str, tenant_id: str, requested_usd: float) -> ApprovalRequest:
        exp = int(time.time()) + self._ttl
        approval_id = f"apr_{hashlib.sha256(f'{ticket_id}:{exp}'.encode()).hexdigest()[:10]}"
        raw = f"{approval_id}:{ticket_id}:{tenant_id}:{requested_usd:.2f}:{exp}"
        return ApprovalRequest(
            approval_id=approval_id,
            ticket_id=ticket_id,
            tenant_id=tenant_id,
            requested_usd=requested_usd,
            expires_at_epoch=exp,
            signature=self._sign(raw),
        )

    def verify(self, req: ApprovalRequest) -> bool:
        if int(time.time()) > req.expires_at_epoch:
            return False
        raw = f"{req.approval_id}:{req.ticket_id}:{req.tenant_id}:{req.requested_usd:.2f}:{req.expires_at_epoch}"
        expected = self._sign(raw)
        return hmac.compare_digest(expected, req.signature)


if __name__ == "__main__":
    gate = DualApprovalGate(secret="prod-finance-hmac-key-2026")
    req = gate.create_request("TKT-A49E1C7B2D", "ten_acme_01", 2500.0)
    print("Approval request:", req.model_dump())
    print("Signature valid:", gate.verify(req))
