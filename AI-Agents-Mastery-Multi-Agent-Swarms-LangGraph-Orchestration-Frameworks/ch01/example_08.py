class SafeSwarmSupervisor(SwarmSupervisor):
    def __init__(self, max_turns: int = 10):
        super().__init__(max_turns=max_turns)
        self.breaker = SwarmCircuitBreaker(max_identical_invocations=2, global_turn_limit=max_turns)

    def dispatch(self, role: AgentRole, instruction: str) -> AgentMessage:
        worker = self.workers[role]
        # Enforce circuit breaker check
        self.breaker.record_and_verify(self.name, worker.name, instruction)
        return super().dispatch(role, instruction)
