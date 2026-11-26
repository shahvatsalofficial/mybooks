class SwarmCanaryGovernor:
    def __init__(self, canary_percentage: float = 0.10):
        self.canary_ratio = canary_percentage
        self.request_counter = 0

    def should_route_to_canary(self) -> bool:
        self.request_counter += 1
        is_canary = (self.request_counter % int(1.0 / self.canary_ratio)) == 0
        target = "CANARY_V2_PROMPT" if is_canary else "STABLE_V1_PROMPT"
        print(f"[CANARY GOVERNOR] Request #{self.request_counter} routed to {target}.")
        return is_canary
