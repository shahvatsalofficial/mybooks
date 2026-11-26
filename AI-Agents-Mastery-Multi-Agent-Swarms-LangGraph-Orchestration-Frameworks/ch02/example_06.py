# Query current state of thread
current_state = persisted_app.get_state(thread_config)
print(f"[CHECKPOINT] Current Thread Step: {current_state.metadata.get('step', 'N/A')}")
print(f"[CHECKPOINT] Values: {current_state.values.keys()}")

# Traverse full historical checkpoint audit trail
print("\n--- HISTORICAL CHECKPOINT AUDIT TRAIL ---")
for state_snapshot in persisted_app.get_state_history(thread_config):
    step_num = state_snapshot.metadata.get("step", 0)
    writes = state_snapshot.metadata.get("writes", {})
    print(f"Step {step_num} | Node: {list(writes.keys())} | Timestamp: {state_snapshot.created_at}")
