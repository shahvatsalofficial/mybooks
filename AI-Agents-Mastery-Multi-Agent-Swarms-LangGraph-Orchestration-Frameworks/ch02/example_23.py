class PregelTelemetryMetrics:
    def __init__(self):
        self.superstep_count = 0
        self.total_node_executions = 0

    def record_step(self, active_node_count: int):
        self.superstep_count += 1
        self.total_node_executions += active_node_count

    def generate_metrics(self) -> str:
        return (
            f"langgraph_supersteps_total {self.superstep_count}\n"
            f"langgraph_node_executions_total {self.total_node_executions}\n"
        )
