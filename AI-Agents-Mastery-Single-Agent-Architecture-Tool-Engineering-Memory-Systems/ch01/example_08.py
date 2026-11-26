import hashlib
from datetime import datetime, timezone

class TrajectoryAuditRecorder:
    def __init__(self, audit_log_path: str):
        self.log_path = audit_log_path
        self.previous_hash = "0" * 64

    def log_turn(self, turn_number: int, thought: str, action: str, observation: str) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Calculate chained cryptographic hash for immutability
        state_repr = f"{self.previous_hash}:{turn_number}:{thought}:{action}:{observation}:{timestamp}"
        current_hash = hashlib.sha256(state_repr.encode("utf-8")).hexdigest()
        
        entry = {
            "turn": turn_number,
            "timestamp": timestamp,
            "thought": thought,
            "action": action,
            "observation": observation,
            "previous_hash": self.previous_hash,
            "current_hash": current_hash
        }
        
        self.previous_hash = current_hash
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "
")
            
        return current_hash

# Verification
recorder = TrajectoryAuditRecorder("/tmp/agent_audit.jsonl")
h1 = recorder.log_turn(1, "Looking up customer", "query_db(user='104')", "Found Elena Rostova")
h2 = recorder.log_turn(2, "Refunding order", "refund(order='ORD-991')", "Refund TX-991 approved")
print(f"Chained Turn 1 Hash: {h1[:16]}...")
print(f"Chained Turn 2 Hash: {h2[:16]}...")
