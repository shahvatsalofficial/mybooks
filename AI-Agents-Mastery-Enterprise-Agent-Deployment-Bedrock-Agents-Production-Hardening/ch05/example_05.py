import time
from typing import Dict, Any, List

class EscalationTier:
    def __init__(self, name: str, timeout_seconds: int, notify_target: str):
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.notify_target = notify_target

class SLAEscalationWatchdog:
    """Monitors active approval timeouts and triggers progressive escalation tiers."""

    def __init__(self, action_id: str, tiers: List[EscalationTier]):
        self.action_id = action_id
        self.tiers = tiers
        self.start_time = time.time()
        self.current_tier_index = 0
        self.resolved = False

    def evaluate_sla(self, current_time: float) -> Dict[str, Any]:
        if self.resolved:
            return {"status": "RESOLVED"}
            
        elapsed = current_time - self.start_time
        
        if self.current_tier_index < len(self.tiers):
            tier = self.tiers[self.current_tier_index]
            if elapsed >= tier.timeout_seconds:
                self.current_tier_index += 1
                return {
                    "status": "ESCALATING",
                    "action_id": self.action_id,
                    "elapsed_seconds": round(elapsed, 1),
                    "escalated_to": tier.name,
                    "target": tier.notify_target,
                    "instruction": f"Primary responder timed out after {tier.timeout_seconds}s. Paging {tier.name}."
                }
            return {"status": "AWAITING_RESPONSE", "elapsed": round(elapsed, 1), "tier": tier.name}
        else:
            return {
                "status": "HARD_TIMEOUT_ABORT",
                "action_id": self.action_id,
                "message": "All escalation tiers exhausted without human response. Triggering automatic safe rollback."
            }

if __name__ == "__main__":
    tiers = [
        EscalationTier("Tier1_PrimaryOnCall", 5, "slack:#sre-oncall"),
        EscalationTier("Tier2_SecondaryLead", 10, "pagerduty:sre-lead-esc"),
        EscalationTier("Tier3_IncidentCommander", 15, "pagerduty:director-ops")
    ]
    watchdog = SLAEscalationWatchdog("ACT-9912-RESTART", tiers)
    
    # Simulate time progression
    t0 = time.time()
    print("Evaluating SLA at t=0s:", watchdog.evaluate_sla(t0)["status"])
    print("Evaluating SLA at t=6s:", watchdog.evaluate_sla(t0 + 6)["status"], "-", watchdog.evaluate_sla(t0 + 6).get("instruction"))
    print("Evaluating SLA at t=16s:", watchdog.evaluate_sla(t0 + 16)["status"], "-", watchdog.evaluate_sla(t0 + 16).get("message"))
