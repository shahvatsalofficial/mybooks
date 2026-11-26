import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class AgentHealthReport(BaseModel):
    agent_role: str
    consecutive_tool_failures: int = 0
    total_tokens_consumed: int = 0
    last_error_signature: Optional[str] = None
    is_quarantined: bool = False

class CrewSelfHealingController:
    """Monitors step execution, detects stalled worker agents, and injects runtime prompt repairs."""
    
    def __init__(self, failure_threshold: int = 3):
        self.threshold = failure_threshold
        self.agent_health: Dict[str, AgentHealthReport] = {}

    def get_or_create_report(self, role: str) -> AgentHealthReport:
        if role not in self.agent_health:
            self.agent_health[role] = AgentHealthReport(agent_role=role)
        return self.agent_health[role]

    def record_step_result(self, role: str, step_output: Dict[str, Any]) -> Optional[str]:
        report = self.get_or_create_report(role)
        is_error = step_output.get("is_error", False)
        error_msg = step_output.get("error_message", "")
        
        if is_error:
            report.consecutive_tool_failures += 1
            report.last_error_signature = error_msg
            print(f"[HEALTH CONTROLLER] Warning: Agent '{role}' failed step (Strike {report.consecutive_tool_failures}/{self.threshold})")
            
            if report.consecutive_tool_failures >= self.threshold:
                return self._generate_prompt_repair_injection(role, error_msg)
        else:
            report.consecutive_tool_failures = 0
            report.last_error_signature = None
        return None

    def _generate_prompt_repair_injection(self, role: str, error_msg: str) -> str:
        injection = (
            f"\n[SYSTEM RECOVERY ADVICE FOR {role.upper()}]: You have encountered repeated errors: '{error_msg}'. "
            f"Cease calling the current tool with previous parameters. Re-read the tool schema, "
            f"simplify your arguments, or report the obstacle directly to the Manager Agent."
        )
        print(f"[RECOVERY INJECTION] Generated targeted prompt repair for '{role}'. Resetting strike counter.")
        self.agent_health[role].consecutive_tool_failures = 1 # Back off strike counter
        return injection
