from dataclasses import dataclass
from typing import List

@dataclass
class TokenBudgetConfig:
    max_context_window: int = 128000
    hard_reserved_for_output: int = 4096
    safety_margin_percentage: float = 0.15

class AdaptiveTokenGovernor:
    def __init__(self, config: TokenBudgetConfig):
        self.config = config
        self.tool_output_history: List[int] = []

    def record_tool_tokens(self, token_count: int) -> None:
        self.tool_output_history.append(token_count)
        if len(self.tool_output_history) > 20:
            self.tool_output_history.pop(0)

    def compute_allowed_input_budget(self) -> int:
        avg_tool = 1000 if not self.tool_output_history else int(sum(self.tool_output_history) / len(self.tool_output_history))
        dynamic_headroom = int(avg_tool * 2.5)
        ceiling = self.config.max_context_window - self.config.hard_reserved_for_output - dynamic_headroom
        return int(ceiling * (1.0 - self.config.safety_margin_percentage))

governor = AdaptiveTokenGovernor(TokenBudgetConfig())
governor.record_tool_tokens(1420)
governor.record_tool_tokens(2100)
print(f"Computed Safe Input Token Budget: {governor.compute_allowed_input_budget()} tokens")
