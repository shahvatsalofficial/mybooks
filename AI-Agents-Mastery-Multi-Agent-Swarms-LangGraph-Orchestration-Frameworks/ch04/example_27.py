class CrewSLAMetricsExporter:
    @staticmethod
    def export(task_durations: Dict[str, float], sla_ceiling: float = 30.0) -> str:
        violations = sum(1 for d in task_durations.values() if d > sla_ceiling)
        return (
            f"crew_task_executions_total {len(task_durations)}\n"
            f"crew_sla_violations_total {violations}\n"
        )
