"""
Human Escalation Protocol Dispatcher.
Serializes failed agent trajectories into structured PagerDuty/JIRA incident envelopes.
"""

from typing import Dict, Any, List
import uuid
import time
import json


class HumanEscalationDispatcher:
    """Dispatches high-context incident tickets to human on-call engineers."""

    def __init__(self, incident_sink: Any):
        self.sink = incident_sink

    def dispatch_incident(
        self,
        session_id: str,
        macro_objective: str,
        failure_reason: str,
        attempted_actions: List[Dict[str, Any]],
        recommended_human_decision: str
    ) -> str:
        """Assembles and transmits standardized incident telemetry envelope."""
        incident_id = f"INC-{str(uuid.uuid4())[:8].upper()}"

        incident_packet = {
            "incident_id": incident_id,
            "session_id": session_id,
            "timestamp": time.time(),
            "macro_objective": macro_objective,
            "failure_summary": failure_reason,
            "trajectory_audit": attempted_actions,
            "required_decision": recommended_human_decision,
            "status": "WAITING_HUMAN_INTERVENTION"
        }

        self.sink.publish_incident(incident_packet)
        return incident_id
