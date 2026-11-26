from typing import List, Dict, Any

class TrajectoryDiffAuditor:
    def diff_trajectories(self, golden: List[str], candidate: List[str]) -> Dict[str, Any]:
        golden_set = set(golden)
        candidate_set = set(candidate)

        missing_critical_tools = golden_set - candidate_set
        unplanned_extra_tools = candidate_set - golden_set
        step_delta = len(candidate) - len(golden)

        return {
            "step_delta": step_delta,
            "missing_tools": list(missing_critical_tools),
            "unplanned_tools": list(unplanned_extra_tools),
            "has_regression": len(missing_critical_tools) > 0 or step_delta > 2
        }

auditor = TrajectoryDiffAuditor()
golden = ["auth_check", "fetch_records", "sanitize_pii", "generate_pdf"]
candidate = ["auth_check", "search_web", "fetch_records", "generate_pdf"]  # Missing sanitize_pii!
diff = auditor.diff_trajectories(golden, candidate)
print("Regression Diff Result:", diff)
