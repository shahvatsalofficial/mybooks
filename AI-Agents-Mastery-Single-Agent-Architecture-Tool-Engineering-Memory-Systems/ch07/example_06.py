class PRRegressionReporter:
    @staticmethod
    def generate_markdown_report(baseline: Dict[str, float], candidate: Dict[str, float]) -> str:
        delta_tsr = candidate["tsr"] - baseline["tsr"]
        delta_latency = candidate["latency_ms"] - baseline["latency_ms"]
        delta_tokens = candidate["tokens"] - baseline["tokens"]

        table = (
            "| Evaluation Metric | Main Branch Baseline | Candidate PR | Delta | Status |
"
            "| :--- | :--- | :--- | :--- | :--- |
"
            f"| **Task Success Rate** | {baseline['tsr']*100:.1f}% | {candidate['tsr']*100:.1f}% | {delta_tsr*100:+.1f}% | {'✅ PASS' if delta_tsr >= 0 else '❌ REGRESSION'} |
"
            f"| **P95 Latency** | {baseline['latency_ms']:.0f}ms | {candidate['latency_ms']:.0f}ms | {delta_latency:+.0f}ms | {'✅ PASS' if delta_latency <= 200 else '⚠️ WARN'} |
"
            f"| **Avg Token Cost** | {baseline['tokens']:.0f} | {candidate['tokens']:.0f} | {delta_tokens:+.0f} | {'✅ PASS' if delta_tokens <= 500 else '❌ REGRESSION'} |"
        )
        return table

# Verification
b = {"tsr": 0.96, "latency_ms": 1200.0, "tokens": 4200.0}
c = {"tsr": 0.98, "latency_ms": 1150.0, "tokens": 4100.0}
print("Generated PR Markdown Table:
")
print(PRRegressionReporter.generate_markdown_report(b, c))
