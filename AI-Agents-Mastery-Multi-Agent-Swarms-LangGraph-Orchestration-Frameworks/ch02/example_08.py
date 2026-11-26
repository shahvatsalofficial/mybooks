# Compile graph with human breakpoint before auditor execution
hitl_app = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["auditor_node"] # Halt execution before this node runs
)

thread_hitl = {"configurable": {"thread_id": "order_transfer_approval_001"}}
