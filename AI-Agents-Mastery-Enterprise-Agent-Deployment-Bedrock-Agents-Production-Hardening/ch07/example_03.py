from typing import Dict, Any, List

class ModelRateCard:
    # Costs per 1,000,000 tokens (USD) as of late 2026
    RATES = {
        "gpt-4o": {"input": 2.50, "output": 10.00, "cached_input": 1.25},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60, "cached_input": 0.075},
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00, "cached_input": 0.30},
        "gemini-2.5-pro": {"input": 1.25, "output": 5.00, "cached_input": 0.30}
    }

class FinOpsCostAttributionEngine:
    """Calculates granular token costs and maintains departmental chargeback ledgers."""

    def __init__(self):
        self.ledger: List[Dict[str, Any]] = []

    def record_usage(
        self,
        department: str,
        project_code: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0
    ) -> float:
        rates = ModelRateCard.RATES.get(model_name, ModelRateCard.RATES["gpt-4o"])
        
        # Calculate cost in USD
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]
        cached_cost = (cached_tokens / 1_000_000) * rates["cached_input"]
        total_cost = input_cost + output_cost + cached_cost
        
        record = {
            "department": department,
            "project_code": project_code,
            "model": model_name,
            "tokens": {"input": input_tokens, "output": output_tokens, "cached": cached_tokens},
            "cost_usd": round(total_cost, 6)
        }
        self.ledger.append(record)
        return total_cost

    def generate_department_summary(self) -> Dict[str, float]:
        summary: Dict[str, float] = {}
        for entry in self.ledger:
            dept = entry["department"]
            summary[dept] = round(summary.get(dept, 0.0) + entry["cost_usd"], 4)
        return summary

if __name__ == "__main__":
    finops = FinOpsCostAttributionEngine()
    
    # Record usage across departments
    finops.record_usage("Risk_Ops", "PRJ-CREDIT-CHECK", "claude-3-5-sonnet", 45000, 3200, 10000)
    finops.record_usage("Customer_Support", "PRJ-CHATBOT", "gpt-4o-mini", 120000, 18000, 40000)
    finops.record_usage("Risk_Ops", "PRJ-FRAUD-DETECTION", "claude-3-5-sonnet", 85000, 6400, 25000)
    
    print("Departmental Token Cost Summary (USD):")
    print(json.dumps(finops.generate_department_summary(), indent=2))
