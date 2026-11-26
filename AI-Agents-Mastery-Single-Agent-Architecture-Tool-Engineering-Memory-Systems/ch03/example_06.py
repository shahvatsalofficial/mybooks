import hmac
import hashlib

class HumanApprovalGate:
    def __init__(self, secret_key: bytes):
        self.secret = secret_key
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}

    def request_approval(self, action_id: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        self.pending_approvals[action_id] = {
            "tool": tool_name,
            "args": arguments,
            "timestamp": time.time(),
            "status": "pending"
        }
        return (
            f"SUSPENDED: Action '{tool_name}' requires human approval. "
            f"Action ID: {action_id}. Please review parameters."
        )

    def submit_approval(self, action_id: str, operator_email: str, signature: str) -> bool:
        if action_id not in self.pending_approvals:
            raise KeyError(f"Action ID '{action_id}' not found.")
            
        payload = f"{action_id}:{operator_email}"
        expected = hmac.new(self.secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(expected, signature):
            raise PermissionError("Security Rejection: Invalid operator HMAC signature.")

        self.pending_approvals[action_id]["status"] = "approved"
        return True

# Verification
gate = HumanApprovalGate(secret_key=b"enterprise_master_key_9941")
suspension_msg = gate.request_approval("ACT-109", "drop_table", {"table": "temp_staging"})
print(suspension_msg)

# Valid approval submission
op = "security_lead@acme.corp"
sig = hmac.new(b"enterprise_master_key_9941", f"ACT-109:{op}".encode("utf-8"), hashlib.sha256).hexdigest()
is_ok = gate.submit_approval("ACT-109", op, sig)
print("Action Execution Authorized:", is_ok)
