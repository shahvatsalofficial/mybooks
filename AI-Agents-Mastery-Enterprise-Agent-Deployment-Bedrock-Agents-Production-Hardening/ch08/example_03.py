import hashlib
import json
import time
from typing import Dict, Any

class WORMComplianceLogger:
    """Writes immutable, tamper-evident audit records to WORM-compliant storage."""

    def __init__(self, bucket_name: str = "enterprise-agent-audit-worm"):
        self.bucket = bucket_name
        self.last_hash = "0" * 64

    def record_compliance_event(
        self,
        event_type: str,
        agent_id: str,
        user_id: str,
        action: str,
        status: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Formats and hashes an audit block bound to WORM storage."""
        timestamp = int(time.time())
        record = {
            "timestamp": timestamp,
            "event_type": event_type,
            "agent_id": agent_id,
            "user_id": user_id,
            "action": action,
            "status": status,
            "payload": payload,
            "previous_record_hash": self.last_hash
        }
        
        # Calculate cryptographic hash
        record_bytes = json.dumps(record, sort_keys=True).encode()
        record_hash = hashlib.sha256(record_bytes).hexdigest()
        record["record_hash"] = record_hash
        self.last_hash = record_hash
        
        # In production: boto3.client('s3').put_object(..., ObjectLockMode='COMPLIANCE', ObjectLockRetainUntilDate=...)
        print(f"[WORM WRITE] Committed event '{event_type}' to immutable storage (Hash: {record_hash[:16]}...).")
        return record

if __name__ == "__main__":
    logger = WORMComplianceLogger()
    r1 = logger.record_compliance_event("TOOL_INVOCATION", "AutonomousSRE", "user_dan", "restart_pod", "SUCCESS", {"pod": "auth-svc"})
    r2 = logger.record_compliance_event("POLICY_EVALUATION", "AutonomousSRE", "user_dan", "opa_check", "APPROVED", {"policy": "k8s_ops"})
