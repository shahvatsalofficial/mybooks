class SwarmLoadShedder:
    def __init__(self, max_concurrent_heavy_tasks: int = 10):
        self.max_heavy = max_concurrent_heavy_tasks
        self.active_heavy_tasks = 0

    def select_model_tier(self, customer_tier: str) -> str:
        if self.active_heavy_tasks >= self.max_heavy and customer_tier != "enterprise":
            print(f"[LOAD SHEDDING] Concurrency ceiling reached ({self.active_heavy_tasks}). Downgrading standard customer to fast model.")
            return "gpt-4o-mini"
        return "gpt-4o"
