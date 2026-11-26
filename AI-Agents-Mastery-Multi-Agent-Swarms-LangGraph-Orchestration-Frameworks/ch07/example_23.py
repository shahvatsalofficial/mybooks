class MultiTierStateCache:
    def __init__(self):
        self.l1_local: Dict[str, Any] = {}
        self.l2_redis_mock: Dict[str, Any] = {}

    def fetch_state(self, thread_id: str) -> Any:
        if thread_id in self.l1_local:
            print(f"[CACHE L1 HIT] {thread_id} (< 0.1ms)")
            return self.l1_local[thread_id]
        if thread_id in self.l2_redis_mock:
            print(f"[CACHE L2 HIT] {thread_id} (~1.5ms)")
            val = self.l2_redis_mock[thread_id]
            self.l1_local[thread_id] = val # Backfill L1
            return val
        print(f"[CACHE L3 MISS] Querying PostgreSQL (~12ms)...")
        # In production: fetch from Postgres and backfill L1 and L2
        return None
