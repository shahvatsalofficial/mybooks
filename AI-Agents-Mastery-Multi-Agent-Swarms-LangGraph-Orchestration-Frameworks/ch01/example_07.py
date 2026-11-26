class SwarmCircuitBreaker:
    def __init__(self, max_identical_invocations: int = 3, global_turn_limit: int = 12):
        self.max_identical_invocations = max_identical_invocations
        self.global_turn_limit = global_turn_limit
        self.call_history: List[Tuple[str, str, int]] = [] # (sender, recipient, content_hash)
        self.total_turns = 0

    def record_and_verify(self, sender: str, recipient: str, content: str) -> bool:
        self.total_turns += 1
        if self.total_turns > self.global_turn_limit:
            raise RecursionError(f"Global swarm turn limit ({self.global_turn_limit}) exceeded.")

        # Hash content to detect repeating loops
        c_hash = hash(content.strip().lower())
        signature = (sender, recipient, c_hash)
        
        count = sum(1 for item in self.call_history if item == signature)
        if count >= self.max_identical_invocations:
            raise RuntimeError(
                f"Deadlock detected! Agent {sender} and {recipient} repeated identical message exchange {count + 1} times."
            )
            
        self.call_history.append(signature)
        return True
