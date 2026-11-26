class CrewAIHealthExporter:
    def __init__(self, crew: Crew):
        self.crew = crew

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        metrics = self.crew.usage_metrics
        return {
            "crew_agent_count": len(self.crew.agents),
            "crew_task_count": len(self.crew.tasks),
            "total_tokens_used": metrics.total_tokens if metrics else 0,
            "successful_requests": metrics.successful_requests if metrics else 0
        }
