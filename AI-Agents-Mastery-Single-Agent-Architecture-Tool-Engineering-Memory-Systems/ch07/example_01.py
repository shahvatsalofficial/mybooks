import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class RecordedToolCall:
    tool_name: str
    arguments: Dict[str, Any]
    step_number: int

class TrajectoryDiffEvaluator:
    def __init__(self, golden_tool_sequence: List[str], max_allowed_steps: int):
        self.golden_sequence = golden_tool_sequence
        self.max_steps = max_allowed_steps

    def evaluate_trajectory(self, recorded_calls: List[RecordedToolCall]) -> Dict[str, Any]:
        actual_tools = [c.tool_name for c in recorded_calls]
        step_count = len(actual_tools)
        
        # 1. Step Budget Check
        exceeded_budget = step_count > self.max_steps
        
        # 2. Sequence Verification
        is_subsequence = True
        golden_idx = 0
        for tool in actual_tools:
            if golden_idx < len(self.golden_sequence) and tool == self.golden_sequence[golden_idx]:
                golden_idx += 1
        
        sequence_matched = (golden_idx == len(self.golden_sequence))
        
        # 3. Efficiency Score: Golden Length / Actual Length
        efficiency_score = round(len(self.golden_sequence) / max(1, step_count), 2)
        
        passed = sequence_matched and not exceeded_budget
        
        return {
            "passed": passed,
            "actual_steps": step_count,
            "max_allowed_steps": self.max_steps,
            "efficiency_score": efficiency_score,
            "missing_golden_tools": self.golden_sequence[golden_idx:],
            "actual_tool_sequence": actual_tools
        }

# Verification
golden_path = ["lookup_account", "verify_identity", "issue_refund"]
evaluator = TrajectoryDiffEvaluator(golden_tool_sequence=golden_path, max_allowed_steps=4)

# Test Run A: Perfect execution
run_a = [
    RecordedToolCall("lookup_account", {"id": "ACC-10"}, 1),
    RecordedToolCall("verify_identity", {"id": "ACC-10"}, 2),
    RecordedToolCall("issue_refund", {"amount": 50}, 3)
]

# Test Run B: Degraded trajectory with redundant calls
run_b = [
    RecordedToolCall("lookup_account", {"id": "ACC-10"}, 1),
    RecordedToolCall("search_helpdesk", {"q": "policy"}, 2),
    RecordedToolCall("verify_identity", {"id": "ACC-10"}, 3),
    RecordedToolCall("lookup_account", {"id": "ACC-10"}, 4), # Redundant
    RecordedToolCall("issue_refund", {"amount": 50}, 5)      # Exceeds max_allowed_steps=4
]

print("Run A Result:", evaluator.evaluate_trajectory(run_a)["passed"])
print("Run B Result:", evaluator.evaluate_trajectory(run_b)["passed"])
