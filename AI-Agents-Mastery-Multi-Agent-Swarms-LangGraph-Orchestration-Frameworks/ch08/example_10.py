class LatencyWaterfallAnalyzer:
    @staticmethod
    def analyze_bottlenecks(spans: List[Dict[str, float]]) -> str:
        slowest_span = max(spans, key=lambda x: x["duration_ms"])
        return f"Primary Bottleneck: '{slowest_span['name']}' consuming {slowest_span['duration_ms']:.2f}ms."
