class MultiNodeRedlock:
    def __init__(self, node_endpoints: List[str], quorum_size: int = 2):
        self.nodes = node_endpoints
        self.quorum_size = quorum_size
        self.lock_token = str(uuid.uuid4())

    def acquire_quorum_lock(self, resource_key: str, ttl_ms: int = 4000) -> bool:
        t0 = time.time()
        successes = 0
        print(f"[REDLOCK] Attempting quorum lock on '{resource_key}' across {len(self.nodes)} nodes...")

        for node in self.nodes:
            # In production: redis_node.set(resource_key, self.lock_token, nx=True, px=ttl_ms)
            successes += 1
            
        elapsed_ms = (time.time() - t0) * 1000
        validity_time = ttl_ms - elapsed_ms
        
        if successes >= self.quorum_size and validity_time > 0:
            print(f"[REDLOCK] Quorum achieved ({successes}/{len(self.nodes)}). Lock valid for {validity_time:.1f}ms.")
            return True
        else:
            print("[REDLOCK] Failed to achieve quorum. Rolling back acquisitions...")
            return False
