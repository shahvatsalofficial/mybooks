"""
Recipe 02.3: Runtime Type Guard & Custom Type Narrowing Engine
File: recipe_02_3_type_guard.py
Python Version: 3.12+ (Supports TypeGuard and TypeIs)
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Union
# Python 3.13 / typing_extensions feature: TypeIs
# In Python 3.12, TypeGuard is fully standard; TypeIs narrows both positive and negative branches
from typing_extensions import TypeGuard, TypeIs


@dataclass(frozen=True)
class SuccessfulTransaction:
    transaction_id: uuid.UUID
    amount_cents: int
    authorization_code: str
    settled: bool


@dataclass(frozen=True)
class FailedTransaction:
    transaction_id: uuid.UUID
    amount_cents: int
    error_code: str
    decline_reason: str


# Domain Union
TransactionResult = Union[SuccessfulTransaction, FailedTransaction]


# 1. Standard TypeGuard: Narrows the positive 'if' branch
def is_successful_transaction(tx: TransactionResult) -> TypeGuard[SuccessfulTransaction]:
    """Narrows TransactionResult to SuccessfulTransaction when True."""
    return hasattr(tx, "authorization_code") and isinstance(getattr(tx, "settled", None), bool)


# 2. Modern TypeIs (PEP 742): Narrows BOTH positive and negative branches!
# When is_valid_tx_payload returns True: payload is narrowed to Dict[str, Any]
# When it returns False: payload is proven to NOT be Dict[str, Any]
def is_valid_transaction_payload(payload: object) -> TypeIs[Dict[str, Any]]:
    """Validates whether an unknown object conforms to dictionary schema boundaries."""
    if not isinstance(payload, dict):
        return False
    # Verify mandatory string keys
    required_keys = {"tx_id", "amount", "status"}
    return required_keys.issubset(payload.keys())


# 3. Processing Pipeline demonstrating compile-time exhaustive narrowing
def process_settlement_ledger(transactions: List[TransactionResult]) -> int:
    """Processes ledger, computing total settled volume with zero casts."""
    total_settled_cents = 0

    for tx in transactions:
        # Before check: type of 'tx' is SuccessfulTransaction | FailedTransaction
        if is_successful_transaction(tx):
            # Inside this branch: Mypy narrows 'tx' strictly to SuccessfulTransaction!
            if tx.settled:
                total_settled_cents += tx.amount_cents
                print(f"[SETTLED] Tx {tx.transaction_id}: Auth {tx.authorization_code}")
        else:
            # Inside negative branch: Mypy narrows 'tx' strictly to FailedTransaction!
            print(f"[DECLINED] Tx {tx.transaction_id}: Reason {tx.decline_reason}")

    return total_settled_cents


if __name__ == "__main__":
    t1 = SuccessfulTransaction(uuid.uuid4(), 45000, "AUTH-9921", settled=True)
    t2 = FailedTransaction(uuid.uuid4(), 12500, "ERR-502", "INSUFFICIENT_FUNDS")
    t3 = SuccessfulTransaction(uuid.uuid4(), 89000, "AUTH-8812", settled=True)

    ledger = [t1, t2, t3]
    total = process_settlement_ledger(ledger)
    print(f"[*] Total Settled Ledger Amount: ${total / 100:.2f}")
