"""
Architectural Drill 5: Multi-Action Distributed Saga with Compensating Rollbacks
"""

import uuid
import time
import requests
from typing import Dict, Any, Optional

class EnterpriseSagaOrchestrator:
    def __init__(self, warehouse_base_url: str, ledger_base_url: str, auth_token: str):
        self.warehouse_url = warehouse_base_url
        self.ledger_url = ledger_base_url
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    def execute_procurement_saga(self, sku: str, quantity: int, account_id: str, amount_usd: float) -> Dict[str, Any]:
        saga_id = str(uuid.uuid4())
        idempotency_key = f"saga-{saga_id}"
        reservation_id: Optional[str] = None

        # Step 1: Execute Warehouse Reservation
        warehouse_payload = {
            "idempotency_key": f"{idempotency_key}-wh",
            "sku": sku,
            "quantity": quantity
        }
        
        try:
            wh_resp = requests.post(
                f"{self.warehouse_url}/api/v1/inventory/reserve",
                json=warehouse_payload,
                headers=self.headers,
                timeout=5.0
            )
            wh_resp.raise_for_status()
            reservation_id = wh_resp.json().get("reservation_id")
        except Exception as exc:
            return {
                "status": "ABORTED_STAGE_1",
                "saga_id": saga_id,
                "error": f"Failed to acquire warehouse inventory lock: {str(exc)}"
            }

        # Step 2: Execute Ledger Charge
        ledger_payload = {
            "idempotency_key": f"{idempotency_key}-ledger",
            "account_id": account_id,
            "amount_usd": amount_usd,
            "reference_reservation_id": reservation_id
        }

        try:
            ledger_resp = requests.post(
                f"{self.ledger_url}/api/v1/ledger/debit",
                json=ledger_payload,
                headers=self.headers,
                timeout=5.0
            )
            ledger_resp.raise_for_status()
            tx_id = ledger_resp.json().get("transaction_id")
            
            return {
                "status": "COMPLETED",
                "saga_id": saga_id,
                "reservation_id": reservation_id,
                "transaction_id": tx_id
            }

        except Exception as ledger_exc:
            # TRIGGER COMPENSATING ROLLBACK ON STAGE 1
            rollback_success = self._rollback_warehouse_reservation(reservation_id, idempotency_key)
            return {
                "status": "ROLLED_BACK",
                "saga_id": saga_id,
                "failed_stage": "STAGE_2_LEDGER",
                "error": str(ledger_exc),
                "compensating_action_executed": rollback_success
            }

    def _rollback_warehouse_reservation(self, reservation_id: Optional[str], saga_id: str) -> bool:
        if not reservation_id:
            return True
        try:
            rollback_resp = requests.post(
                f"{self.warehouse_url}/api/v1/inventory/release",
                json={"idempotency_key": f"{saga_id}-rollback", "reservation_id": reservation_id},
                headers=self.headers,
                timeout=5.0
            )
            return rollback_resp.status_code in [200, 204]
        except Exception:
            # In production, dispatch to dead-letter queue (DLQ) for asynchronous reconciliation
            return False
