# Step 2: Human reviews and modifies state
print("[HUMAN SUPERVISOR] Injecting required TLS and HSM encryption standards...")
hitl_app.update_state(
    thread_hitl,
    values={
        "draft_content": (
            "Technical Brief on PCI-DSS Payment Gateway Deployment (Approved by SecOps):\n"
            "- Implementation: Use Redis Checkpointer with distributed locking.\n"
            "- Security Gate: Enforce TLS 1.3 encryption and mutual auth with Hardware Security Module (HSM)."
        )
    }
)

# Step 3: Resume graph execution by passing None as input
print("[HITL] Resuming graph execution post human approval...")
resumed_result = hitl_app.invoke(None, thread_hitl)

print(f"[HITL] Post-Resume Status: {resumed_result['is_approved']}")
print(f"[HITL] Final Output:\n{resumed_result['final_output']}")
