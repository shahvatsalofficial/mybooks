import concurrent.futures

def simulate_agent_worker(store: ConcurrentSharedStore, state_id: str, agent_name: str, update_key: str, update_val: Any) -> str:
    # 1. Read current state
    snapshot = store.get(state_id)
    print(f"[{agent_name}] Read state '{state_id}' at Version {snapshot.version}")
    
    # 2. Simulate compute latency
    time.sleep(0.05)
    
    # 3. Attempt update with optimistic check
    new_data = snapshot.data.copy()
    new_data[update_key] = update_val
    
    try:
        updated = store.update_atomic(
            state_id=state_id,
            expected_version=snapshot.version,
            new_data=new_data,
            agent_name=agent_name
        )
        return f"SUCCESS: {agent_name} committed Version {updated.version}."
    except StateConflictError as err:
        return f"ABORT: {agent_name} caught {err}."
