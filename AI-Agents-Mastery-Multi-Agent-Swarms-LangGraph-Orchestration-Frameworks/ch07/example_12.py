def verify_read_after_write(store: ConcurrentSharedStore, state_id: str, expected_val: Any) -> bool:
    snapshot = store.get(state_id)
    assert snapshot is not None, "State not found."
    # Verify write reached read replica
    return snapshot.data.get("status") == expected_val
