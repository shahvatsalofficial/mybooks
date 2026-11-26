class TokenCostGovernor:
    # Model pricing per 1M tokens (Claude 3.5 Sonnet / GPT-4o standard tier)
    PROMPT_COST_PER_M = 3.00
    COMPLETION_COST_PER_M = 15.00

    def __init__(self, session_spending_ceiling_usd: float = 0.50):
        self.spending_ceiling = session_spending_ceiling_usd
        self.total_spent_usd = 0.0
        self.agent_spend_breakdown: Dict[str, float] = {}

    def log_turn(self, agent_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        cost = (prompt_tokens / 1_000_000 * self.PROMPT_COST_PER_M) + \
               (completion_tokens / 1_000_000 * self.COMPLETION_COST_PER_M)
        
        self.total_spent_usd += cost
        self.agent_spend_breakdown[agent_name] = self.agent_spend_breakdown.get(agent_name, 0.0) + cost
        
        if self.total_spent_usd > self.spending_ceiling:
            raise PermissionError(
                f"Financial Circuit Breaker Tripped! Session spent ${self.total_spent_usd:.4f}, "
                f"exceeding maximum ceiling of ${self.spending_ceiling:.2f}."
            )
        return cost
