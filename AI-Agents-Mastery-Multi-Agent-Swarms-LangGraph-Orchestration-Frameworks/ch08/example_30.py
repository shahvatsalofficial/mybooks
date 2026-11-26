from typing import Dict, Any, List, Tuple
from pydantic import BaseModel

class TrajectoryStep(BaseModel):
    step_number: int
    agent_role: str
    action_type: str # TOOL_CALL, REASONING, FINAL_ANSWER
    target_tool: Optional[str] = None
    tokens_spent: int

class TrajectoryDiffReport(BaseModel):
    baseline_turns: int
    candidate_turns: int
    turn_delta: int
    token_delta_percent: float
    tool_sequence_divergence: bool
    verdict: str

class SwarmTrajectoryDiffAnalyzer:
    """Compares baseline and candidate swarm execution paths to detect behavioral drift."""
    
    @staticmethod
    def compare_trajectories(baseline: List[TrajectoryStep], candidate: List[TrajectoryStep]) -> TrajectoryDiffReport:
        b_turns = len(baseline)
        c_turns = len(candidate)
        turn_delta = c_turns - b_turns
        
        b_tokens = sum(s.tokens_spent for s in baseline)
        c_tokens = sum(s.tokens_spent for s in candidate)
        token_delta_pct = ((c_tokens - b_tokens) / max(1, b_tokens)) * 100.0
        
        b_tools = [s.target_tool for s in baseline if s.target_tool]
        c_tools = [s.target_tool for s in candidate if s.target_tool]
        tools_diverged = b_tools != c_tools
        
        is_regression = turn_delta > 1 or token_delta_pct > 25.0 or (tools_diverged and c_turns > b_turns)
        verdict = "REGRESSION_DETECTED" if is_regression else "BENCHMARK_PROMOTABLE"
        
        print(f"[TRAJECTORY DIFF] Turns: {b_turns} -> {c_turns} (Delta: {turn_delta:+d})")
        print(f"[TRAJECTORY DIFF] Tokens: {b_tokens} -> {c_tokens} ({token_delta_pct:+.1f}%)")
        print(f"[TRAJECTORY DIFF] Tool Sequence Match: {not tools_diverged} | Verdict: {verdict}")
        
        return TrajectoryDiffReport(
            baseline_turns=b_turns,
            candidate_turns=c_turns,
            turn_delta=turn_delta,
            token_delta_percent=round(token_delta_pct, 2),
            tool_sequence_divergence=tools_diverged,
            verdict=verdict
        )
