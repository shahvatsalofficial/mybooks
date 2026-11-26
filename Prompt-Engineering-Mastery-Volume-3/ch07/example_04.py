"""
Reflexion Loop Governor: Orchestrates iterative draft-critique-refine cycles,
tracking score delta trajectory and cutting off execution when diminishing returns occur.
"""

from typing import Dict, Any, List, Optional
import time


class ReflexionGovernor:
    """Manages iterative self-refinement with hard ceilings and delta tracking."""

    def __init__(
        self,
        generator_client: Any,
        evaluator: RubricEvaluator,
        max_iterations: int = 3,
        min_delta_gain: float = 0.3
    ):
        self.generator = generator_client
        self.evaluator = evaluator
        self.max_iterations = max_iterations
        self.min_delta_gain = min_delta_gain
        self.trajectory_history: List[Dict[str, Any]] = []

    def run_refinement_loop(
        self,
        task_objective: str,
        initial_prompt: str
    ) -> Dict[str, Any]:
        """
        Executes bounded iterative refinement until quality threshold is met
        or marginal gains diminish below cost threshold.
        """
        current_candidate = self.generator.generate(initial_prompt)
        iteration = 1
        previous_score = 0.0

        while iteration <= self.max_iterations:
            eval_report = self.evaluator.evaluate_artifact(task_objective, current_candidate)
            current_score = eval_report.composite_score
            delta_gain = current_score - previous_score if iteration > 1 else current_score

            self.trajectory_history.append({
                "iteration": iteration,
                "score": current_score,
                "delta_gain": round(delta_gain, 2),
                "passed": eval_report.passed,
                "candidate_length": len(current_candidate)
            })

            if eval_report.passed:
                return {
                    "status": "APPROVED",
                    "final_artifact": current_candidate,
                    "final_score": current_score,
                    "iterations": iteration,
                    "history": self.trajectory_history
                }

            if iteration > 1 and delta_gain < self.min_delta_gain:
                return {
                    "status": "TERMINATED_DIMINISHING_RETURNS",
                    "final_artifact": current_candidate,
                    "final_score": current_score,
                    "iterations": iteration,
                    "reason": f"Marginal score delta ({delta_gain:.2f}) dropped below cutoff ({self.min_delta_gain}).",
                    "history": self.trajectory_history
                }

            refinement_prompt = f"""
You are refining your previous implementation based on strict audit feedback.

<task_objective>
{task_objective}
</task_objective>

<previous_attempt>
{current_candidate}
</previous_attempt>

<audit_critique>
{eval_report.actionable_delta_prompt}
</audit_critique>

Apply surgical fixes addressing 100% of the listed deficiencies.
Output the complete corrected artifact.
"""
            current_candidate = self.generator.generate(refinement_prompt)
            previous_score = current_score
            iteration += 1

        return {
            "status": "MAX_ITERATIONS_EXCEEDED",
            "final_artifact": current_candidate,
            "final_score": previous_score,
            "iterations": self.max_iterations,
            "history": self.trajectory_history
        }
