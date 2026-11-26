class FinOpsCostEngine:
    RATES = {
        "gpt-4o": {"input": 0.0000025, "output": 0.0000100},
        "claude-3-5-sonnet": {"input": 0.0000030, "output": 0.0000150}
    }

    def __init__(self):
        self.ledger: List[Dict[str, Any]] = []

    def record_usage(self, tenant_id: str, cost_center: str, model: str, input_tokens: int, output_tokens: int):
        rates = self.RATES.get(model, {"input": 0.000003, "output": 0.000015})
        total_usd = (input_tokens * rates["input"]) + (output_tokens * rates["output"])
        
        self.ledger.append({
            "tenant_id": tenant_id,
            "cost_center": cost_center,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(total_usd, 6),
            "timestamp": time.time()
        })

    def aggregate_by_cost_center(self) -> Dict[str, float]:
        summary: Dict[str, float] = {}
        for entry in self.ledger:
            cc = entry["cost_center"]
            summary[cc] = round(summary.get(cc, 0.0) + entry["cost_usd"], 4)
        return summary

# Verification
finops = FinOpsCostEngine()
finops.record_usage("acme", "engineering", "claude-3-5-sonnet", 12000, 1800)
finops.record_usage("acme", "support", "claude-3-5-sonnet", 4500, 600)
finops.record_usage("acme", "engineering", "gpt-4o", 8000, 1200)
print("Cost Allocation by Department:", finops.aggregate_by_cost_center())
