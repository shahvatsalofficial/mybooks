class AgentBenchTrajectoryScorer:
    @staticmethod
    def score_trajectory(turns: List[Dict[str, Any]], optimal_turn_count: int = 3) -> Dict[str, float]:
        actual_turns = len(turns)
        efficiency_ratio = min(1.0, optimal_turn_count / max(1, actual_turns))
        tool_accuracy = sum(1 for t in turns if t.get("tool_exit_code") == 0) / max(1, actual_turns)
        
        composite_score = (efficiency_ratio * 0.4 + tool_accuracy * 0.6) * 100
        print(f"[AGENTBENCH] Composite Trajectory Score: {composite_score:.1f}/100 (Efficiency: {efficiency_ratio:.2f}, Tool Acc: {tool_accuracy:.2f})")
        return {"composite": composite_score, "efficiency": efficiency_ratio, "tool_accuracy": tool_accuracy}
