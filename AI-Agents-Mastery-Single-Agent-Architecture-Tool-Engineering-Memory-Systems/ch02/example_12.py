from typing import Dict, Any, TypedDict, Literal
import time

class AgentState(TypedDict):
    input_query: str
    plan: list[str]
    current_step: int
    tool_observations: list[str]
    iteration_count: int
    is_complete: bool

def planner_node(state: AgentState) -> Dict[str, Any]:
    print(f"[STATE GRAPH] Node: Planner | Query: '{state['input_query']}'")
    return {
        "plan": ["Fetch Cloudwatch Logs", "Analyze Heap Dump", "Generate Incident RCA"],
        "current_step": 0,
        "iteration_count": state["iteration_count"] + 1
    }

def executor_node(state: AgentState) -> Dict[str, Any]:
    step = state["plan"][state["current_step"]]
    print(f"[STATE GRAPH] Node: Executor | Running step {state['current_step'] + 1}: '{step}'")
    obs = f"Result of {step} at {time.strftime('%H:%M:%S')}"
    return {
        "tool_observations": state["tool_observations"] + [obs],
        "current_step": state["current_step"] + 1,
        "iteration_count": state["iteration_count"] + 1
    }

def router_condition(state: AgentState) -> Literal["executor", "verifier", "end"]:
    if state["iteration_count"] > 10:
        return "end"
    if state["current_step"] < len(state["plan"]):
        return "executor"
    return "verifier"

def verifier_node(state: AgentState) -> Dict[str, Any]:
    print("[STATE GRAPH] Node: Verifier | Validating completion criteria...")
    return {"is_complete": True, "iteration_count": state["iteration_count"] + 1}

# Execute compiled state graph loop
state: AgentState = {
    "input_query": "Diagnose pod crashloop backoff",
    "plan": [],
    "current_step": 0,
    "tool_observations": [],
    "iteration_count": 0,
    "is_complete": False
}

state.update(planner_node(state))
while not state["is_complete"] and state["iteration_count"] < 10:
    next_node = router_condition(state)
    if next_node == "executor":
        state.update(executor_node(state))
    elif next_node == "verifier":
        state.update(verifier_node(state))
    elif next_node == "end":
        break
