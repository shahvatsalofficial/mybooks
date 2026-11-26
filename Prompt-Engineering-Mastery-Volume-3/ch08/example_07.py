"""
State Machine Watchdog: Detects execution stagnation where an agent
remains trapped in an intermediate state exceeding maximum SLA timeouts.
"""

import time
from typing import Dict, Any, Optional


class StateMachineWatchdog:
    """Monitors state dwell time and triggers automated escalations on stalls."""

    def __init__(self, state_timeouts_seconds: Dict[str, int]):
        self.timeouts = state_timeouts_seconds

    def check_state_dwell_time(
        self,
        current_state: str,
        state_entered_timestamp: float
    ) -> Optional[Dict[str, Any]]:
        """Evaluates whether current state dwell time exceeds enterprise threshold."""
        allowed_duration = self.timeouts.get(current_state, 300)
        current_dwell = time.time() - state_entered_timestamp

        if current_dwell > allowed_duration:
            return {
                "alert": "STATE_STALL_TIMEOUT_EXCEEDED",
                "state": current_state,
                "dwell_seconds": round(current_dwell, 1),
                "allowed_seconds": allowed_duration,
                "action": "ESCALATE_HUMAN_INTERVENTION"
            }

        return None
