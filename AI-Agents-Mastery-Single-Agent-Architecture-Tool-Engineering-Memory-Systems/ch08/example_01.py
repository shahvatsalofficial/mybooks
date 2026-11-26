import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ModelPricingTier(BaseModel):
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float

PRICING_TABLE = {
    "claude-3-5-sonnet": ModelPricingTier(cost_per_1k_input_tokens=0.003, cost_per_1k_output_tokens=0.015),
    "gpt-4o": ModelPricingTier(cost_per_1k_input_tokens=0.0025, cost_per_1k_output_tokens=0.010)
}

class TenantBudgetGovernor:
    def __init__(self, monthly_budget_usd: float):
        self.monthly_budget_usd = monthly_budget_usd
        self.accumulated_spend_usd = 0.0
        self.total_tokens_consumed = 0

    def authorize_and_charge(self, model: str, input_tokens: int, output_tokens: int) -> bool:
        if model not in PRICING_TABLE:
            raise KeyError(f"Pricing not configured for model '{model}'.")
            
        tier = PRICING_TABLE[model]
        cost = (input_tokens / 1000.0 * tier.cost_per_1k_input_tokens) + \
               (output_tokens / 1000.0 * tier.cost_per_1k_output_tokens)
        
        # Hard financial stop gate
        if (self.accumulated_spend_usd + cost) > self.monthly_budget_usd:
            raise PermissionError(
                f"Financial Circuit Breaker: Monthly budget ceiling of ${self.monthly_budget_usd:.2f} "
                f"exceeded. Current spend: ${self.accumulated_spend_usd:.2f}, Requested: ${cost:.4f}."
            )

        self.accumulated_spend_usd += cost
        self.total_tokens_consumed += (input_tokens + output_tokens)
        return True

    def get_budget_status(self) -> Dict[str, Any]:
        return {
            "monthly_budget_usd": self.monthly_budget_usd,
            "accumulated_spend_usd": round(self.accumulated_spend_usd, 4),
            "remaining_budget_usd": round(max(0.0, self.monthly_budget_usd - self.accumulated_spend_usd), 4),
            "total_tokens_consumed": self.total_tokens_consumed
        }

# Verification
governor = TenantBudgetGovernor(monthly_budget_usd=50.00)
# Turn 1
governor.authorize_and_charge("claude-3-5-sonnet", input_tokens=4000, output_tokens=1000)
print("Budget Status after Turn 1:", governor.get_budget_status())
