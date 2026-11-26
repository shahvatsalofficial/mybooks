# merkle_audit_logger.py
import hashlib
from typing import List

class MerkleAuditLedger:
    def __init__(self):
        self.leaves: List[str] = []

    def record_transaction(self, request_id: str, prompt: str, response: str, tenant_id: str) -> str:
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        response_hash = hashlib.sha256(response.encode("utf-8")).hexdigest()
        leaf_payload = f"{request_id}|{tenant_id}|{prompt_hash}|{response_hash}"
        leaf_hash = hashlib.sha256(leaf_payload.encode("utf-8")).hexdigest()
        self.leaves.append(leaf_hash)
        return leaf_hash

    def compute_root(self) -> str:
        if not self.leaves:
            return ""
        current_layer = self.leaves[:]
        while len(current_layer) > 1:
            if len(current_layer) % 2 == 1:
                current_layer.append(current_layer[-1]) # Duplicate odd leaf
            next_layer = []
            for i in range(0, len(current_layer), 2):
                combined = current_layer[i] + current_layer[i+1]
                parent = hashlib.sha256(combined.encode("utf-8")).hexdigest()
                next_layer.append(parent)
            current_layer = next_layer
        return current_layer[0]
