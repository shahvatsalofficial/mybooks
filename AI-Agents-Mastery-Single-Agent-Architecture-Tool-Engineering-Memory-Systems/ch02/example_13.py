from typing import List, Dict, Any
from pydantic import BaseModel, Field

class ExecutionPlan(BaseModel):
    remaining_steps: List[str]
    rationale: str

class DynamicReplanner:
    def __init__(self):
        self.step_history: List[Dict[str, Any]] = []

    def record_step(self, step: str, success: bool, output: str) -> None:
        self.step_history.append({"step": step, "success": success, "output": output})

    def replan_if_needed(self, original_plan: List[str], current_index: int) -> List[str]:
        last_step = self.step_history[-1]
        if last_step["success"]:
            return original_plan[current_index + 1:]

        print(f"[REPLANNER] Step '{last_step['step']}' failed! Output: '{last_step['output']}'")
        # In production, this invokes an LLM to generate replacement trajectory
        remediated_plan = [
            f"Fallback alternative for {last_step['step']}",
            "Verify alternative output integrity"
        ] + original_plan[current_index + 1:]
        return remediated_plan

replanner = DynamicReplanner()
replanner.record_step("Query ElasticSearch Cluster", False, "Connection refused: port 9200")
new_steps = replanner.replan_if_needed(["Query ElasticSearch Cluster", "Aggregate Metrics", "Alert On-Call"], 0)
print("Updated Trajectory:", new_steps)
