class ProductionSamplingEvaluator:
    def __init__(self, sample_rate: float = 0.05):
        self.sample_rate = sample_rate
        self.evaluated_spans: List[Dict[str, Any]] = []

    def should_sample(self) -> bool:
        return random.random() < self.sample_rate

    def evaluate_async(self, session_id: str, prompt: str, trajectory: str, final_answer: str) -> Optional[Dict[str, Any]]:
        if not self.should_sample():
            return None
            
        # Background evaluation simulation
        score = 5 if len(final_answer.split()) > 5 else 2
        metric_record = {
            "session_id": session_id,
            "metric": "agent.production.accuracy_score",
            "value": score,
            "timestamp": time.time(),
            "tags": ["env:production", "service:agent-gateway"]
        }
        self.evaluated_spans.append(metric_record)
        return metric_record

# Verification
sampler = ProductionSamplingEvaluator(sample_rate=1.0) # 100% for test
metric = sampler.evaluate_async("sess_104", "Fix bug", "Action: query()", "The bug is patched.")
print("Sampled Production Metric Exported:", metric["metric"], "Score:", metric["value"])
