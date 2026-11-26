workflow = StateGraph(AgentState)
# ... node definitions ...
graph = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["destructive_tools"]
)
