import hashlib
import json
import time
from typing import List, Dict, Any

class ImmutableAgentAuditLog:
    """Maintains a cryptographically chained, tamper-evident record of agent actions."""

    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self._genesis_block()

    def _genesis_block(self) -> None:
        genesis = {
            "index": 0,
            "timestamp": int(time.time()),
            "action": "GENESIS_INITIALIZATION",
            "actor": "SYSTEM",
            "previous_hash": "0" * 64
        }
        genesis["hash"] = self._compute_hash(genesis)
        self.chain.append(genesis)

    @staticmethod
    def _compute_hash(block: Dict[str, Any]) -> str:
        record_bytes = json.dumps({k: v for k, v in block.items() if k != "hash"}, sort_keys=True).encode()
        return hashlib.sha256(record_bytes).hexdigest()

    def log_action(self, actor: str, action: str, details: Dict[str, Any]) -> Dict[str, Any]:
        prev_block = self.chain[-1]
        block = {
            "index": len(self.chain),
            "timestamp": int(time.time()),
            "actor": actor,
            "action": action,
            "details": details,
            "previous_hash": prev_block["hash"]
        }
        block["hash"] = self._compute_hash(block)
        self.chain.append(block)
        return block

    def verify_integrity(self) -> bool:
        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]
            if curr["previous_hash"] != prev["hash"]:
                return False
            if curr["hash"] != self._compute_hash(curr):
                return False
        return True

if __name__ == "__main__":
    audit = ImmutableAgentAuditLog()
    audit.log_action("agent_sre_01", "RESTART_POD", {"pod": "payment-api-49a", "namespace": "prod"})
    audit.log_action("agent_sre_01", "QUERY_LOGS", {"cluster": "prod-us-east"})
    
    print(f"Audit log length: {len(audit.chain)} blocks.")
    print("Chain Cryptographic Integrity Verified:", audit.verify_integrity())
