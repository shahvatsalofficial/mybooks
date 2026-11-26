from typing import Dict, Any

def apply_human_modifications(
    current_agent_state: Dict[str, Any],
    human_input_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Merges human parameter overrides into the frozen execution state before resumption."""
    updated_state = current_agent_state.copy()
    
    overrides = human_input_payload.get("overrides", {})
    for param_name, new_val in overrides.items():
        print(f"Human operator modified parameter '{param_name}': {updated_state.get(param_name)} -> {new_val}")
        updated_state[param_name] = new_val
        
    updated_state["human_modified"] = True
    updated_state["modified_by"] = human_input_payload.get("operator_id", "unknown_operator")
    return updated_state

if __name__ == "__main__":
    frozen_state = {
        "action": "batch_purge_records",
        "table": "sessions",
        "purge_limit": 100000,
        "grace_days": 7
    }
    operator_feedback = {
        "operator_id": "dan@corp.com",
        "decision": "APPROVED_WITH_MODIFICATIONS",
        "overrides": {"purge_limit": 5000, "grace_days": 30}
    }
    res = apply_human_modifications(frozen_state, operator_feedback)
    print("Resumed state purge_limit:", res["purge_limit"], "grace_days:", res["grace_days"])
