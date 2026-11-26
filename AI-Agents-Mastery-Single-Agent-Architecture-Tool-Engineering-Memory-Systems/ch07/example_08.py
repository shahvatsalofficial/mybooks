@dataclass
class ModelBenchmarkResult:
    model_name: str
    cost_usd: float
    latency_p95_ms: float
    accuracy_score: float

def compute_pareto_frontier(results: List[ModelBenchmarkResult]) -> List[ModelBenchmarkResult]:
    # A model is Pareto-optimal if no other model has higher accuracy AND lower cost AND lower latency
    frontier = []
    for candidate in results:
        dominated = False
        for other in results:
            if (other.accuracy_score >= candidate.accuracy_score and 
                other.cost_usd <= candidate.cost_usd and 
                other.latency_p95_ms <= candidate.latency_p95_ms and
                (other.accuracy_score > candidate.accuracy_score or other.cost_usd < candidate.cost_usd or other.latency_p95_ms < candidate.latency_p95_ms)):
                dominated = True
                break
        if not dominated:
            frontier.append(candidate)
    return frontier

# Verification
models = [
    ModelBenchmarkResult("FastModel-7B", 0.001, 450.0, 0.82),
    ModelBenchmarkResult("MidModel-70B", 0.008, 1200.0, 0.91),
    ModelBenchmarkResult("FrontierModel-400B", 0.040, 3200.0, 0.97),
    ModelBenchmarkResult("SuboptimalModel", 0.020, 2500.0, 0.85) # Dominated
]
pareto_set = compute_pareto_frontier(models)
print("Pareto Optimal Models:", [m.model_name for m in pareto_set])
