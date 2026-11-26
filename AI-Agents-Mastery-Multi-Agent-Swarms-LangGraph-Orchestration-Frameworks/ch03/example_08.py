class HandoffDebtTracker:
    def __init__(self, max_total_hops: int = 6):
        self.max_total_hops = max_total_hops
        self.handoff_chain: List[str] = []

    def register_hop(self, from_agent: str, to_agent: str):
        self.handoff_chain.append(f"{from_agent}->{to_agent}")
        if len(self.handoff_chain) > self.max_total_hops:
            chain_str = " => ".join(self.handoff_chain)
            raise RuntimeError(
                f"Swarm Handoff Budget Depleted! Maximum hops ({self.max_total_hops}) exceeded. "
                f"Handoff Chain: {chain_str}"
            )
        
        # Check for immediate cyclic ping-pong (A->B then B->A)
        if len(self.handoff_chain) >= 2:
            prev = self.handoff_chain[-2].split("->")
            curr = self.handoff_chain[-1].split("->")
            if prev[0] == curr[1] and prev[1] == curr[0]:
                raise RuntimeError(
                    f"Ping-Pong Deadlock Detected between '{curr[0]}' and '{curr[1]}'! Halting swarm."
                )
