import uuid
from typing import Dict, Any, Optional

class HumanApprovalQueue:
    def __init__(self):
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}

    def pause_for_approval(self, agent_id: str, action_name: str, payload: Dict[str, Any]) -> str:
        ticket_id = f"TICK-{uuid.uuid4().hex[:8].upper()}"
        self.pending_approvals[ticket_id] = {
            "agent_id": agent_id,
            "action": action_name,
            "payload": payload,
            "status": "PENDING"
        }
        print(f"[HITL GATE] Agent '{agent_id}' PAUSED! Generated approval ticket: {ticket_id}")
        return ticket_id

    def submit_decision(self, ticket_id: str, approved: bool, reviewer: str) -> Dict[str, Any]:
        if ticket_id not in self.pending_approvals:
            raise KeyError("Invalid Ticket ID")
        ticket = self.pending_approvals[ticket_id]
        ticket["status"] = "APPROVED" if approved else "REJECTED"
        ticket["reviewer"] = reviewer
        print(f"[HITL GATE] Ticket '{ticket_id}' {ticket['status']} by {reviewer}")
        return ticket

queue = HumanApprovalQueue()
tid = queue.pause_for_approval("agent_cluster_admin", "k8s_delete_namespace", {"namespace": "staging-legacy"})
res = queue.submit_decision(tid, approved=True, reviewer="lead_sre_vatsal")
