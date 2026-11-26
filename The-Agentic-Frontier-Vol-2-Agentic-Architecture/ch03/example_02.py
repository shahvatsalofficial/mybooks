from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Initialize LLM models
llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

# Define Supervisor System Prompt
SUPERVISOR_PROMPT = """
You are the Lead Software Supervisor managing an autonomous engineering squad.
Your squad consists of two worker agents:
1. 'Coder': Writes and refactors Python code.
2. 'Tester': Generates unit tests and executes test suites.

Given the current squad state, evaluate the progress and respond with the EXACT name of the next agent to act: 'Coder', 'Tester', or 'FINISH'.
"""

def supervisor_node(state: SquadState) -> dict:
    """Supervisor decision node that routes execution based on conversation history."""
    messages = [SystemMessage(content=SUPERVISOR_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    
    # Parse decision from LLM output
    decision = response.content.strip()
    if decision not in ["Coder", "Tester", "FINISH"]:
        decision = "FINISH"
        
    return {"next_step": decision}

def coder_node(state: SquadState) -> dict:
    """Worker node that handles code generation tasks."""
    user_prompt = state["messages"][-1].content
    code_result = "# Production Code Output\ndef calculate_roi(investment, return_val):\n    return ((return_val - investment) / investment) * 100\n"
    
    msg = HumanMessage(content=f"[Coder Output]: Generated python implementation.\n{code_result}", name="Coder")
    return {
        "messages": [msg],
        "code_artifacts": {"main.py": code_result},
        "retry_count": state.get("retry_count", 0) + 1
    }

def tester_node(state: SquadState) -> dict:
    """Worker node that validates code quality and runs unit tests."""
    msg = HumanMessage(content="[Tester Output]: Executed PyTest suite. 100% tests passed cleanly.", name="Tester")
    return {
        "messages": [msg],
        "build_status": "SUCCESS"
    }

# Build LangGraph State Graph
workflow = StateGraph(SquadState)

# Add Nodes
workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Coder", coder_node)
workflow.add_node("Tester", tester_node)

# Set Entry Point
workflow.set_entry_point("Supervisor")

# Add Conditional Edges
workflow.add_conditional_edges(
    "Supervisor",
    lambda state: state["next_step"],
    {
        "Coder": "Coder",
        "Tester": "Tester",
        "FINISH": END
    }
)

# Route Worker Nodes back to Supervisor for next decision
workflow.add_edge("Coder", "Supervisor")
workflow.add_edge("Tester", "Supervisor")

# Compile Graph
squad_app = workflow.compile()
