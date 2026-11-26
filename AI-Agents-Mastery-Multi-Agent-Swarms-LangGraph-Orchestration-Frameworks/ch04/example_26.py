class CrewCostAccountant:
    def __init__(self):
        self.spend_by_agent: Dict[str, float] = {}

    def log_agent_usage(self, agent_role: str, prompt_tok: int, comp_tok: int):
        cost = (prompt_tok / 1e6 * 3.0) + (comp_tok / 1e6 * 15.0)
        self.spend_by_agent[agent_role] = self.spend_by_agent.get(agent_role, 0.0) + cost
        print(f"[COST ACCOUNTANT] {agent_role}: +${cost:.4f} (Total: ${self.spend_by_agent[agent_role]:.4f})")
