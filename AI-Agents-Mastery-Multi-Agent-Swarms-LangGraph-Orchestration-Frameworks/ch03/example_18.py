def deadlock_breaker_interceptor(subgraph_thread_id: str, max_allowed_steps: int = 8):
    # Query current checkpoint history
    history = list(parent_app.get_state_history({"configurable": {"thread_id": subgraph_thread_id}}))
    if len(history) > max_allowed_steps:
        print(f"[DEADLOCK BREAKER] Thread {subgraph_thread_id} exceeded {max_allowed_steps} steps! Injecting abort...")
        parent_app.update_state(
            {"configurable": {"thread_id": subgraph_thread_id}},
            values={"resolution_status": "escalated", "final_resolution_summary": "DEADLOCK_ABORT_TRIGGERED"}
        )
        return True
    return False
