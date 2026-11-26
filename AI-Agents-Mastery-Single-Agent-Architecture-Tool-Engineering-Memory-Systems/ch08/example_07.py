@dataclass
class CloudProviderEndpoint:
    provider_id: str
    weight: int
    is_healthy: bool = True
    consecutive_failures: int = 0

class MultiCloudModelBalancer:
    def __init__(self, endpoints: List[CloudProviderEndpoint]):
        self.endpoints = endpoints
        self.current_idx = 0

    def select_healthy_endpoint(self) -> CloudProviderEndpoint:
        healthy = [ep for ep in self.endpoints if ep.is_healthy]
        if not healthy:
            raise RuntimeError("CRITICAL OUTAGE: All cloud model provider endpoints are marked UNHEALTHY.")
            
        self.current_idx = (self.current_idx + 1) % len(healthy)
        return healthy[self.current_idx]

    def report_status(self, provider_id: str, success: bool):
        for ep in self.endpoints:
            if ep.provider_id == provider_id:
                if success:
                    ep.consecutive_failures = 0
                    ep.is_healthy = True
                else:
                    ep.consecutive_failures += 1
                    if ep.consecutive_failures >= 3:
                        ep.is_healthy = False
                        print(f"[FAILOVER ALERT] Pruned unhealthy provider endpoint '{provider_id}' from routing pool.")

# Verification
balancer = MultiCloudModelBalancer([
    CloudProviderEndpoint("Anthropic-Direct-US", weight=50),
    CloudProviderEndpoint("AWS-Bedrock-US-East", weight=50)
])

# Simulate 3 failures on Anthropic Direct
balancer.report_status("Anthropic-Direct-US", success=False)
balancer.report_status("Anthropic-Direct-US", success=False)
balancer.report_status("Anthropic-Direct-US", success=False)

selected = balancer.select_healthy_endpoint()
print("Failover Target Selected:", selected.provider_id)
