import time
from typing import Dict, Any, Set, List

class QuorumApprovalTracker:
    """Enforces M-of-N consensus across distinct organizational stakeholders."""

    def __init__(self, action_id: str, required_approvals: int = 2, authorized_roles: Set[str] = None):
        self.action_id = action_id
        self.required_approvals = required_approvals
        self.authorized_roles = authorized_roles or {"LeadSRE", "SecurityOfficer", "VP_Engineering"}
        self.recorded_approvals: Dict[str, Dict[str, Any]] = {}

    def register_vote(self, operator_id: str, operator_role: str, vote: str) -> Dict[str, Any]:
        if operator_role not in self.authorized_roles:
            return {"status": "REJECTED", "reason": f"Role '{operator_role}' is not authorized to vote."}
            
        if operator_id in self.recorded_approvals:
            return {"status": "DUPLICATE", "reason": f"Operator '{operator_id}' has already voted."}
            
        self.recorded_approvals[operator_id] = {
            "role": operator_role,
            "vote": vote,
            "timestamp": int(time.time())
        }
        
        # Count affirmative approvals
        affirmative = sum(1 for v in self.recorded_approvals.values() if v["vote"] == "APPROVE")
        rejections = sum(1 for v in self.recorded_approvals.values() if v["vote"] == "REJECT")
        
        if rejections > 0:
            return {
                "decision": "VETOED",
                "message": f"Action vetoed by {operator_id} ({operator_role}). Workflow aborted."
            }
            
        if affirmative >= self.required_approvals:
            return {
                "decision": "QUORUM_REACHED",
                "message": f"Approved by {affirmative}/{self.required_approvals} required stakeholders. Proceeding."
            }
            
        return {
            "decision": "PENDING_QUORUM",
            "current_affirmative": affirmative,
            "required": self.required_approvals
        }

if __name__ == "__main__":
    gate = QuorumApprovalTracker("ACTION-RESTORE-CORE-ROUTER", required_approvals=2)
    
    # Vote 1: SRE approves
    v1 = gate.register_vote("alice@corp.com", "LeadSRE", "APPROVE")
    print("Vote 1 Status:", v1["decision"], f"({v1.get('current_affirmative')}/{v1.get('required')})")
    
    # Vote 2: Security Officer approves
    v2 = gate.register_vote("bob@corp.com", "SecurityOfficer", "APPROVE")
    print("Vote 2 Status:", v2["decision"], "-", v2["message"])
