class HandoffMetricsExporter:
    def __init__(self):
        self.handoff_counts: Dict[str, int] = {}

    def log_handoff(self, source_domain: str, target_domain: str):
        key = f"{source_domain}_to_{target_domain}"
        self.handoff_counts[key] = self.handoff_counts.get(key, 0) + 1

    def export_metrics(self) -> Dict[str, Any]:
        return {
            "total_cross_domain_handoffs": sum(self.handoff_counts.values()),
            "domain_transitions": self.handoff_counts
        }
