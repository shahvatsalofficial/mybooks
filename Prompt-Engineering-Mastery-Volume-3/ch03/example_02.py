"""
Production-Grade ReAct Loop Orchestrator with Anti-Thrashing Guardrails.
Enforces strict XML parsing, canonical action hashing, and automatic circuit-breaking.
"""

import json
import re
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field


@dataclass
class ToolExecutionResult:
    success: bool
    output: Any
    error_message: Optional[str] = None


@dataclass
class ReActTurn:
    index: int
    thought: str
    action_name: str
    action_params: Dict[str, Any]
    observation: Optional[str] = None
    action_hash: str = ""

    def compute_hash(self) -> str:
        canonical_params = json.dumps(self.action_params, sort_keys=True)
        raw_sig = f"{self.action_name}::{canonical_params}"
        self.action_hash = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()
        return self.action_hash


class ReActLoopGovernor:
    """Orchestrates multi-turn ReAct cycles with strict invariant enforcement."""

    def __init__(
        self,
        tool_registry: Dict[str, Callable[[Dict[str, Any]], ToolExecutionResult]],
        max_steps: int = 10,
        repetition_threshold: int = 2,
    ):
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        self.repetition_threshold = repetition_threshold
        self.history: List[ReActTurn] = []
        self.seen_action_hashes: Dict[str, int] = {}

    def extract_thought_and_action(self, model_response: str) -> Tuple[str, str, Dict[str, Any]]:
        """Parses model response into validated thought, action_name, and arguments."""
        thought_match = re.search(r"<thought>(.*?)</thought>", model_response, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""

        action_match = re.search(
            r'<action\s+name=["\'](.*?)["\']>(.*?)</action>',
            model_response,
            re.DOTALL
        )
        if not action_match:
            raise ValueError("Malformed turn: Missing or unclosed <action> block.")

        action_name = action_match.group(1).strip()
        raw_params = action_match.group(2).strip()

        try:
            action_params = json.loads(raw_params) if raw_params else {}
        except json.JSONDecodeError as err:
            raise ValueError(f"Action arguments invalid JSON: {err}")

        return thought, action_name, action_params

    def evaluate_anti_thrashing(self, turn: ReActTurn) -> Optional[str]:
        """Detects identical action loops and injects system circuit-breakers."""
        act_hash = turn.compute_hash()
        count = self.seen_action_hashes.get(act_hash, 0) + 1
        self.seen_action_hashes[act_hash] = count

        if count > self.repetition_threshold:
            return (
                f"CIRCUIT_BREAKER_TRIGGERED: You have executed tool '{turn.action_name}' "
                f"with identical arguments {count} times consecutively. The environment "
                f"state has not changed. You are strictly forbidden from re-attempting this action. "
                f"You must revise your hypothesis or abort."
            )
        return None

    def execute_turn(
        self,
        turn_index: int,
        model_output: str
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Executes a single ReAct step.
        Returns: (is_finished, formatted_observation_for_model, final_result_payload)
        """
        try:
            thought, action_name, action_params = self.extract_thought_and_action(model_output)
        except ValueError as parse_err:
            obs = f"<observation status='PARSE_ERROR'>{str(parse_err)}</observation>"
            return False, obs, None

        turn = ReActTurn(
            index=turn_index,
            thought=thought,
            action_name=action_name,
            action_params=action_params
        )

        # Check for Terminal Actions
        if action_name.upper() == "FINISH":
            self.history.append(turn)
            return True, None, action_params.get("final_output", action_params)

        if action_name.upper() == "ABORT":
            self.history.append(turn)
            return True, None, {"status": "ABORTED", "reason": action_params.get("reason", "Unknown")}

        # Check Anti-Thrashing Guardrail
        thrashing_warning = self.evaluate_anti_thrashing(turn)
        if thrashing_warning:
            obs = f"<observation status='THROTTLED'>{thrashing_warning}</observation>"
            turn.observation = obs
            self.history.append(turn)
            return False, obs, None

        # Execute Registered Tool
        if action_name not in self.tool_registry:
            obs = (
                f"<observation status='UNKNOWN_TOOL'>Tool '{action_name}' does not exist. "
                f"Available tools: {list(self.tool_registry.keys())}</observation>"
            )
            turn.observation = obs
            self.history.append(turn)
            return False, obs, None

        handler = self.tool_registry[action_name]
        try:
            result = handler(action_params)
            status_tag = "SUCCESS" if result.success else "FAILURE"
            output_str = json.dumps(result.output) if isinstance(result.output, (dict, list)) else str(result.output)
            obs = f"<observation status='{status_tag}'>{output_str}</observation>"
        except Exception as exc:
            obs = f"<observation status='EXECUTION_EXCEPTION'>{type(exc).__name__}: {str(exc)}</observation>"

        turn.observation = obs
        self.history.append(turn)
        return False, obs, None
