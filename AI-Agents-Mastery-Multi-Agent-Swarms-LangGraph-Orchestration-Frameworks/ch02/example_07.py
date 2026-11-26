def fork_and_replay(thread_id: str, target_step: int, corrected_data: Dict[str, Any]):
    config = {"configurable": {"thread_id": thread_id}}
    
    # Locate target historical checkpoint
    target_checkpoint = None
    for snapshot in persisted_app.get_state_history(config):
        if snapshot.metadata.get("step") == target_step:
            target_checkpoint = snapshot
            break
            
    if not target_checkpoint:
        raise ValueError(f"Step {target_step} not found in thread {thread_id}")
        
    print(f"[TIME-TRAVEL] Forking execution from Checkpoint ID: {target_checkpoint.config['configurable']['checkpoint_id']}")
    
    # Update state at historical checkpoint
    fork_config = persisted_app.update_state(
        target_checkpoint.config,
        values=corrected_data,
        as_node="researcher_node" # Attribute the modification to node
    )
    
    # Resume execution from fork
    print("[TIME-TRAVEL] Resuming graph execution from forked state...")
    resumed_state = persisted_app.invoke(None, fork_config)
    return resumed_state
