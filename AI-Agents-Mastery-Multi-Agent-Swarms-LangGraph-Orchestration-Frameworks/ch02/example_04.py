from langgraph.graph import StateGraph, START, END

# 1. Instantiate the Graph Builder
workflow = StateGraph(ResearchGraphState)

# 2. Add Nodes
workflow.add_node("researcher_node", researcher_node)
workflow.add_node("auditor_node", auditor_node)

# 3. Add Edges
workflow.add_edge(START, "researcher_node")
workflow.add_edge("researcher_node", "auditor_node")

# 4. Add Conditional Routing Edge
workflow.add_conditional_edges(
    "auditor_node",
    should_continue_router,
    {
        "researcher_node": "researcher_node",
        "__end__": END
    }
)

# 5. Compile into an Executable Runnable
app = workflow.compile()

# 6. Execute Graph with Initial Input State
if __name__ == "__main__":
    initial_input: ResearchGraphState = {
        "topic": "LangGraph Distributed Checkpointing",
        "draft_content": "",
        "audit_notes": [],
        "revision_count": 0,
        "is_approved": False,
        "final_output": None
    }
    
    final_state = app.invoke(initial_input)
    print("\n--- GRAPH EXECUTION SUMMARY ---")
    print(f"Total Revisions Required: {final_state['revision_count']}")
    print(f"Approval Status: {final_state['is_approved']}")
    print(f"Audit History:\n" + "\n".join(f"  - {note}" for note in final_state['audit_notes']))
