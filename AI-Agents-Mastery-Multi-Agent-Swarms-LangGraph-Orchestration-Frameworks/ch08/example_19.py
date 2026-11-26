class SwarmAutomatedRollbackGovernor:
    def __init__(self, failure_threshold_percent: float = 15.0):
        self.threshold = failure_threshold_percent

    def evaluate_recent_window(self, recent_evaluations: List[bool]):
        failures = recent_evaluations.count(False)
        rate = (failures / len(recent_evaluations)) * 100
        if rate > self.threshold:
            print(f"[CIRCUIT BREAKER] High failure rate ({rate:.1f}%)! Rolling back deployment to v1.2.")
            return "TRIGGER_ROLLBACK"
        return "HEALTHY"
