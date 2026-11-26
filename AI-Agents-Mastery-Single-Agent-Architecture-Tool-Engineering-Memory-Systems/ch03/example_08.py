class DistributedRateLeaseCoordinator:
    def __init__(self, global_tps: int = 100, lease_size: int = 10):
        self.global_tps = global_tps
        self.lease_size = lease_size
        self.available_tokens = global_tps
        self.last_refill = time.time()

    def lease_tokens(self, worker_id: str) -> int:
        now = time.time()
        elapsed = now - self.last_refill
        # Refill tokens
        self.available_tokens = min(self.global_tps, self.available_tokens + int(elapsed * self.global_tps))
        self.last_refill = now
        
        granted = min(self.available_tokens, self.lease_size)
        self.available_tokens -= granted
        return granted

# Verification
coordinator = DistributedRateLeaseCoordinator(global_tps=50, lease_size=10)
print(f"Worker 1 Leased Tokens: {coordinator.lease_tokens('pod-worker-01')}")
print(f"Worker 2 Leased Tokens: {coordinator.lease_tokens('pod-worker-02')}")
