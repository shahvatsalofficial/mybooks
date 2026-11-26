# evaluation/faithfulness_checker.py
"""
Production Faithfulness Evaluator using Claims Decomposition.
"""
from typing import List
from pydantic import BaseModel, Field
import openai

class ClaimVerification(BaseModel):
    claim: str
    supported: bool
    explanation: str

class FaithfulnessReport(BaseModel):
    faithfulness_score: float
    claims: List[ClaimVerification]

def evaluate_faithfulness(agent_output: str, retrieved_context: str, client: openai.OpenAI) -> FaithfulnessReport:
    prompt = f"""
Given the retrieved context and the agent's output, perform a 2-step evaluation:
Step 1: Break down the agent output into atomic factual claims.
Step 2: For each claim, check if it is directly supported by the context.

[Retrieved Context]:
{retrieved_context}

[Agent Output]:
{agent_output}

Output format: JSON matching schema with 'claims' array of objects with keys: claim, supported (true/false), explanation.
"""
    response = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[{"role": "user", "content": prompt}],
        response_format=FaithfulnessReport
    )
    report = response.choices[0].message.parsed
    supported_count = sum(1 for c in report.claims if c.supported)
    total_claims = len(report.claims) if report.claims else 1
    report.faithfulness_score = round(supported_count / total_claims, 3)
    return report
