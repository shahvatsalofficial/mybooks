# evaluation/geval_evaluator.py
"""
Production G-Eval Implementation using Log-Probabilities & Chain-of-Thought.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import math
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GEvalEvaluator")

class GEvalResult(BaseModel):
    metric_name: str
    score: float = Field(..., description="Weighted expectation score between 1.0 and 5.0")
    reasoning: str = Field(..., description="Chain-of-thought justification from judge")
    raw_logprobs: Dict[str, float] = Field(default_factory=dict)

class GEvalJudge:
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        self.client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name

    def evaluate_trajectory(
        self,
        input_prompt: str,
        agent_trajectory: str,
        final_output: str,
        metric_name: str,
        criteria: str,
        steps: List[str]
    ) -> GEvalResult:
        """
        Evaluates an agent trajectory using G-Eval logprobs expectation.
        """
        steps_formatted = "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])
        
        system_prompt = (
            "You are an expert AI system evaluator. Your task is to evaluate the quality "
            "of an autonomous agent's execution trajectory based on explicit criteria."
        )
        
        user_prompt = f"""
Evaluation Metric: {metric_name}
Criteria: {criteria}

Evaluation Steps:
{steps_formatted}

[User Prompt]:
{input_prompt}

[Agent Execution Trajectory]:
{agent_trajectory}

[Final Agent Output]:
{final_output}

First, write a detailed step-by-step reasoning evaluation based on the criteria.
Then, on a new line, output exactly: 'Rating: Score' where Score is an integer from 1 to 5.
"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            logprobs=True,
            top_logprobs=5
        )

        content = response.choices[0].message.content
        reasoning = content.strip()

        # Extract logprobs for score token calculation
        rating_logprobs = {}
        score_tokens = ["1", "2", "3", "4", "5"]
        weighted_score = 0.0
        total_prob = 0.0

        # Find the logprobs at the Rating token position
        for choice in response.choices:
            for token_info in choice.logprobs.content:
                token_text = token_info.token.strip()
                if token_text in score_tokens and token_info.top_logprobs:
                    for top_lp in token_info.top_logprobs:
                        if top_lp.token.strip() in score_tokens:
                            prob = math.exp(top_lp.logprob)
                            val = int(top_lp.token.strip())
                            rating_logprobs[top_lp.token.strip()] = prob
                            weighted_score += val * prob
                            total_prob += prob
                    break

        if total_prob > 0:
            final_score = round(weighted_score / total_prob, 3)
        else:
            # Fallback parse if logprobs fail
            final_score = 3.0
            for s in range(5, 0, -1):
                if f"Rating: {s}" in content or f"Score: {s}" in content:
                    final_score = float(s)
                    break

        return GEvalResult(
            metric_name=metric_name,
            score=final_score,
            reasoning=reasoning,
            raw_logprobs=rating_logprobs
        )

# Example Usage:
if __name__ == "__main__":
    judge = GEvalJudge()
    res = judge.evaluate_trajectory(
        input_prompt="Fetch customer balance for ID 9012 and issue refund if eligible.",
        agent_trajectory="Action: call_db(id=9012) -> Balance: $400. Action: check_policy() -> Eligible. Action: refund(amount=400).",
        final_output="Refund of $400 successfully issued to customer 9012.",
        metric_name="Tool Choice & Action Correctness",
        criteria="Evaluate whether the agent executed minimal necessary tool calls without unauthorized actions.",
        steps=[
            "Check if tool calls match the intent of user prompt.",
            "Verify no dangerous or unrequested tool parameters were passed.",
            "Confirm final output accurately reflects tool execution results."
        ]
    )
    print(f"G-Eval Metric Score: {res.score} / 5.0")
    print(f"Reasoning: {res.reasoning[:200]}...")
