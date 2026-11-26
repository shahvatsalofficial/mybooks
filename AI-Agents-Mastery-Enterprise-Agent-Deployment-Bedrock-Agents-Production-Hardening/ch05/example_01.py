import os
import json
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

class AgentState(TypedDict):
    task: str
    plan: str
    requires_approval: bool
    human_decision: str
    execution_result: str

def planner_node(state: AgentState) -> Dict[str, Any]:
    """Generates an operational plan and flags mutation risk."""
    task = state["task"]
    plan = f"EXECUTE: Scale down replica count to 0 for deployment 'auth-service' in namespace 'prod'."
    return {
        "plan": plan,
        "requires_approval": True
    }

def human_approval_node(state: AgentState) -> Dict[str, Any]:
    """Freezes state machine and awaits external human approval input."""
    # The interrupt() call halts execution and serializes state to checkpointer
    decision = interrupt({
        "question": "Approve production deployment scale-down?",
        "proposed_plan": state["plan"],
        "risk_level": "CRITICAL"
    })
    return {"human_decision": decision}

def executor_node(state: AgentState) -> Dict[str, Any]:
    """Executes the approved mutation or performs safe abort."""
    if state.get("human_decision") == "APPROVED":
        return {"execution_result": "SUCCESS: Applied scale-down mutation to auth-service."}
    else:
        return {"execution_result": "ABORTED: Human operator rejected proposal."}

# Build the Graph
builder = StateGraph(AgentState)
builder.add_node("planner", planner_node)
builder.add_node("human_approval", human_approval_node)
builder.add_node("executor", executor_node)

builder.add_edge(START, "planner")
builder.add_edge("planner", "human_approval")
builder.add_edge("human_approval", "executor")
builder.add_edge("executor", END)

# MemorySaver provides in-process checkpointing (use PostgresSaver in production)
checkpointer = MemorySaver()
app = builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    thread_config = {"configurable": {"thread_id": "incident-409-remedy"}}
    
    print("--- STEP 1: Running Agent until Human Interrupt ---")
    initial_input = {"task": "Remediate memory leak in auth service", "human_decision": "", "execution_result": ""}
    events = app.stream(initial_input, config=thread_config)
    for event in events:
        print("Event:", event)
        
    # Inspect state at interrupt
    snapshot = app.get_state(thread_config)
    print("\n[STATE FROZEN] Next node waiting for human input:", snapshot.next)
    print("Pending Interrupt Payload:", snapshot.tasks[0].interrupts[0].value)
    
    print("\n--- STEP 2: Human Operator Submits 'APPROVED' Decision ---")
    resume_command = Command(resume="APPROVED")
    resumed_events = app.stream(resume_command, config=thread_config)
    for event in resumed_events:
        print("Event:", event)
        
    final_state = app.get_state(thread_config)
    print("\nFinal Workflow Result:", final_state.values["execution_result"])
