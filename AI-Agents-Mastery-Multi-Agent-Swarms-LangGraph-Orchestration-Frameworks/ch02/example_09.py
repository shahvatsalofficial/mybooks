# Step 1: Execute graph until first breakpoint
initial_task: ResearchGraphState = {
    "topic": "PCI-DSS Payment Gateway Deployment",
    "draft_content": "",
    "audit_notes": [],
    "revision_count": 0,
    "is_approved": False,
    "final_output": None
}

print("[HITL] Initiating execution...")
result = hitl_app.invoke(initial_task, thread_hitl)

# Inspect graph state at breakpoint
paused_state = hitl_app.get_state(thread_hitl)
print(f"[HITL] Graph Paused! Next Pending Node: {paused_state.next}")
print(f"[HITL] Draft awaiting human approval:\n{paused_state.values['draft_content']}")
