class StateTelemetryMetrics:
    def __init__(self):
        self.occ_conflicts = 0
        self.lock_acquisitions = 0

    def record_occ_conflict(self):
        self.occ_conflicts += 1

    def export(self) -> str:
        return (
            f"agent_occ_conflicts_total {self.occ_conflicts}\n"
            f"agent_lock_acquisitions_total {self.lock_acquisitions}\n"
        )
