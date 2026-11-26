class SwarmEvaluationTelemetryExporter:
    def __init__(self):
        self.total_evals = 0
        self.passed_evals = 0

    def record_eval(self, passed: bool):
        self.total_evals += 1
        if passed:
            self.passed_evals += 1

    def generate_metrics(self) -> str:
        pass_rate = self.passed_evals / max(1, self.total_evals)
        return (
            f"swarm_evaluations_total {self.total_evals}\n"
            f"swarm_evaluation_pass_rate {pass_rate:.4f}\n"
        )
