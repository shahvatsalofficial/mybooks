class DAGFlowVisualizer:
    @staticmethod
    def render_ascii_summary(spans: List[Dict[str, Any]]) -> str:
        """Outputs structured hierarchical tree of completed spans."""
        output_lines = ["\n--- SWARM EXECUTION DAG ---"]
        for s in spans:
            indent = "  " if s.get("parent_id") else ""
            output_lines.append(f"{indent}* [{s['agent']}] {s['name']} (Latency: {s['latency_ms']:.1f}ms)")
        return "\n".join(output_lines)
