"""
Multi-Criteria Rubric Evaluator Engine.
Scores candidate artifacts across orthogonal weighted criteria, enforcing
hard minimum thresholds and generating structured delta critique instructions.
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import json


@dataclass
class CriterionResult:
    criterion_id: str
    name: str
    weight: float
    score: float  # [0.0, 10.0]
    critique: str
    deficiencies: List[str]


@dataclass
class EvaluationReport:
    composite_score: float
    passed: bool
    criterion_results: List[CriterionResult]
    actionable_delta_prompt: str


class RubricEvaluator:
    """Evaluates candidate artifacts against rigorous enterprise rubrics."""

    MIN_COMPOSITE_THRESHOLD = 8.5
    MIN_INDIVIDUAL_THRESHOLD = 7.0

    def __init__(self, llm_judge_client: Any, rubric_schema: List[Dict[str, Any]]):
        self.judge = llm_judge_client
        self.rubric = rubric_schema

    def evaluate_artifact(self, task_objective: str, candidate_artifact: str) -> EvaluationReport:
        """Executes multi-criteria evaluation pass using structured rubric."""
        rubric_json = json.dumps(self.rubric, indent=2)

        prompt = f"""
You are an Uncompromising Technical Code Auditor.
Audit this candidate artifact against the provided evaluation rubric.

<task_objective>
{task_objective}
</task_objective>

<candidate_artifact>
{candidate_artifact}
</candidate_artifact>

<rubric>
{rubric_json}
</rubric>

For each criterion, score from 0.0 to 10.0 and list exact deficiencies.
Output MUST be a JSON object:
{{
  "evaluations": [
    {{
      "criterion_id": "CRIT-01",
      "score": 8.5,
      "critique": "Functional correctness is high but missing null check on line 24.",
      "deficiencies": ["Missing null check on user_id"]
    }}
  ]
}}
"""
        response_text = self.judge.generate(prompt)
        try:
            eval_data = json.loads(response_text)
        except json.JSONDecodeError:
            raise ValueError(f"Judge output invalid JSON: {response_text}")

        results: List[CriterionResult] = []
        composite = 0.0
        all_passed = True

        for c_def in self.rubric:
            c_id = c_def["id"]
            weight = c_def["weight"]
            name = c_def["name"]

            match = next((e for e in eval_data["evaluations"] if e["criterion_id"] == c_id), None)
            score = float(match["score"]) if match else 0.0
            critique = match["critique"] if match else "Evaluation missing."
            deficiencies = match.get("deficiencies", []) if match else []

            if score < self.MIN_INDIVIDUAL_THRESHOLD:
                all_passed = False

            composite += score * weight
            results.append(CriterionResult(
                criterion_id=c_id,
                name=name,
                weight=weight,
                score=score,
                critique=critique,
                deficiencies=deficiencies
            ))

        if composite < self.MIN_COMPOSITE_THRESHOLD:
            all_passed = False

        delta_lines = ["### ACTIONABLE DEFICIENCIES TO REPAIR:"]
        for r in results:
            if r.score < self.MIN_INDIVIDUAL_THRESHOLD or r.deficiencies:
                delta_lines.append(f"- **{r.name} (Score: {r.score}/10)**: {r.critique}")
                for d in r.deficiencies:
                    delta_lines.append(f"  * Fix required: {d}")

        delta_prompt = "\n".join(delta_lines)

        return EvaluationReport(
            composite_score=round(composite, 2),
            passed=all_passed,
            criterion_results=results,
            actionable_delta_prompt=delta_prompt
        )
