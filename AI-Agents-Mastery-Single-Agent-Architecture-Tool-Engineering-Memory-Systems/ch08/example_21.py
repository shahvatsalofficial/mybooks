class RegionFailoverGovernor:
    def __init__(self):
        self.primary_region = "us-east"
        self.secondary_region = "eu-west"
        self.latencies: deque = deque(maxlen=50)

    def record_latency(self, latency_ms: float):
        self.latencies.append(latency_ms)

    def get_target_region(self) -> str:
        if len(self.latencies) >= 20:
            sorted_lat = sorted(self.latencies)
            p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
            if p95 > 2500.0:
                return self.secondary_region
        return self.primary_region
