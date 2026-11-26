from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Dict
from pydantic import BaseModel


class LedgerReceipt(BaseModel):
    receipt_id: str
    idempotency_key: str
    ticket_id: str
    tenant_id: str
    amount_usd: float
    committed_at: datetime
    replayed_from_cache: bool


class IdempotentLedgerExecutor:
    """Executes financial credits exactly once per ticket-action key."""

    def __init__(self) -> None:
        self._ledger: Dict[str, LedgerReceipt] = {}

    @staticmethod
    def build_key(ticket_id: str, action: str, amount_usd: float) -> str:
        cents = int(round(amount_usd * 100))
        raw = f"{ticket_id}:{action}:{cents}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:20]

    def commit_credit(self, ticket_id: str, tenant_id: str, amount_usd: float) -> LedgerReceipt:
        key = self.build_key(ticket_id, "sla_credit", amount_usd)
        if key in self._ledger:
            existing = self._ledger[key]
            return existing.model_copy(update={"replayed_from_cache": True})

        receipt = LedgerReceipt(
            receipt_id=f"rcpt_{key[:10]}",
            idempotency_key=key,
            ticket_id=ticket_id,
            tenant_id=tenant_id,
            amount_usd=amount_usd,
            committed_at=datetime.now(timezone.utc),
            replayed_from_cache=False,
        )
        self._ledger[key] = receipt
        return receipt


if __name__ == "__main__":
    executor = IdempotentLedgerExecutor()
    first = executor.commit_credit("TKT-A49E1C7B2D", "ten_acme_01", 350.0)
    retry = executor.commit_credit("TKT-A49E1C7B2D", "ten_acme_01", 350.0)
    print("First commit:", first.model_dump())
    print("Retry commit:", retry.model_dump())
