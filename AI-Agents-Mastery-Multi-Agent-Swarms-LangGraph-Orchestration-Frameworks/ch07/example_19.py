class WALVectorSyncStreamer:
    @staticmethod
    def process_wal_change_event(event: Dict[str, Any]):
        table = event.get("table")
        operation = event.get("op") # INSERT, UPDATE
        if table == "agent_checkpoints" and operation in ("INSERT", "UPDATE"):
            new_state = event.get("after", {})
            print(f"[CDC VECTOR SYNC] Streaming WAL event for Thread {new_state.get('thread_id')} to vector index...")
