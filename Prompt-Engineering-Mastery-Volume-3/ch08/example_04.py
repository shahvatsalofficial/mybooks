"""
Prompt-Driven Finite State Machine Orchestrator.
Enforces strict directed graph topology, validates transition guards,
and dynamically adjusts available tools based on current workflow state.
"""

from typing import Dict, Any, List, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field
import json
import re


class InvalidStateTransitionError(Exception):
    """Raised when an agent attempts an illegal state jump."""
    pass


@dataclass
class WorkflowState:
    state_id: str
    description: str
    allowed_tools: List[str]
    valid_next_states: Set[str]
    transition_guards: Dict[str, Callable[[Dict[str, Any]], bool]] = field(default_factory=dict)


class PromptStateMachineEngine:
    """Manages deterministic state machine lifecycles for autonomous agents."""

    def __init__(self, states: Dict[str, WorkflowState], initial_state_id: str):
        self.states = states
        if initial_state_id not in self.states:
            raise ValueError(f"Initial state '{initial_state_id}' not defined.")
        self.current_state_id = initial_state_id
        self.transition_history: List[Dict[str, Any]] = []
        self.context_variables: Dict[str, Any] = {}

    @property
    def current_state(self) -> WorkflowState:
        return self.states[self.current_state_id]

    def render_state_prompt_envelope(self) -> str:
        """Generates dynamic Moore prompt restricting instructions and tools to current state."""
        state = self.current_state
        return f"""
<active_workflow_state id="{state.state_id}">
  <operational_mandate>
    {state.description}
  </operational_mandate>
  <authorized_tools>
    {json.dumps(state.allowed_tools)}
  </authorized_tools>
  <authorized_next_states>
    {json.dumps(list(state.valid_next_states))}
  </authorized_next_states>
  <accumulated_variables>
    {json.dumps(self.context_variables, indent=2)}
  </accumulated_variables>
</active_workflow_state>
"""

    def parse_transition_block(self, model_output: str) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """Extracts and validates <state_transition> XML syntax."""
        pattern = r'<state_transition\s+from=["\'](.*?)["\']\s+to=["\'](.*?)["\']>(.*?)</state_transition>'
        match = re.search(pattern, model_output, re.DOTALL)
        if not match:
            return None

        from_state = match.group(1).strip()
        to_state = match.group(2).strip()
        raw_payload = match.group(3).strip()

        try:
            payload = json.loads(raw_payload) if raw_payload else {}
        except json.JSONDecodeError as err:
            raise ValueError(f"State transition payload invalid JSON: {err}")

        return from_state, to_state, payload

    def attempt_transition(
        self,
        from_state: str,
        to_state: str,
        evidence_payload: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validates transition against adjacency matrix and guard expressions.
        Returns: (success, diagnostic_message)
        """
        if from_state != self.current_state_id:
            return False, (
                f"STATE_MISMATCH_ERROR: Claimed origin state '{from_state}' does not "
                f"match actual active state '{self.current_state_id}'."
            )

        if to_state not in self.current_state.valid_next_states:
            return False, (
                f"ILLEGAL_TRANSITION_ERROR: Cannot transition directly from "
                f"'{self.current_state_id}' to '{to_state}'. Permitted next states: "
                f"{list(self.current_state.valid_next_states)}."
            )

        guard_fn = self.current_state.transition_guards.get(to_state)
        if guard_fn:
            passed = guard_fn(evidence_payload)
            if not passed:
                return False, (
                    f"GUARD_EVALUATION_FAILED: Evidence payload failed guard conditions "
                    f"for transition to '{to_state}'."
                )

        previous = self.current_state_id
        self.current_state_id = to_state
        self.context_variables.update(evidence_payload)
        self.transition_history.append({
            "from": previous,
            "to": to_state,
            "evidence": evidence_payload
        })

        return True, f"SUCCESS: State advanced from '{previous}' to '{to_state}'."
