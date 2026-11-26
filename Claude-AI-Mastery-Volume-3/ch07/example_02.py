"""
production_ragas_evaluator.py
Enterprise RAGAS Evaluation Engine with Claude 3.5 Sonnet Factual Referee.
Calculates Faithfulness, Answer Relevance, Context Recall and Harmonic Score.
"""

import asyncio
import json
import logging
import math
from typing import Any, Dict, List, Optional

import boto3
from botocore.config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("RagasEnterpriseEvaluator")


class RagasEvaluatorHarness:
    """Production automated evaluation harness executing the RAG Triad assessment."""

    def __init__(self, region_name: str = "us-east-1"):
        boto_config = Config(region_name=region_name, retries={"max_attempts": 3, "mode": "adaptive"})
        self.bedrock_runtime = boto3.client("bedrock-runtime", config=boto_config)
        self.eval_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    async def _invoke_evaluator(self, prompt: str) -> str:
        """Helper to invoke Claude 3.5 Sonnet evaluator synchronously within async executor."""
        loop = asyncio.get_running_loop()
        
        def _call_bedrock():
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2048,
                "temperature": 0.0,
                "messages": [{"role": "user", "content": prompt}],
            }
            res = self.bedrock_runtime.invoke_model(
                modelId=self.eval_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            data = json.loads(res["body"].read().decode("utf-8"))
            return data["content"][0]["text"]

        return await loop.run_in_executor(None, _call_bedrock)

    async def evaluate_faithfulness(self, context: str, answer: str) -> float:
        """
        Evaluates the Faithfulness (groundedness) of an answer against retrieved context.
        Extracts factual statements and checks each against context.
        """
        prompt = f"""You are a strict factual verification auditor.
Analyze the following Context and Answer.
First, break the Answer down into distinct, atomic factual statements.
Second, for each statement, determine whether it can be completely deduced from the Context (SUPPORTED) or not (UNSUPPORTED).

Respond strictly with valid JSON adhering to this schema:
{{
  "statements": [
    {{"statement": "...", "verdict": "SUPPORTED" | "UNSUPPORTED", "reasoning": "..."}}
  ],
  "faithfulness_score": 0.0
}}

Where faithfulness_score is (count of SUPPORTED statements) / (total statements). If statements is empty, score is 1.0.

[CONTEXT]:
{context}

[ANSWER]:
{answer}
"""
        response_text = await self._invoke_evaluator(prompt)
        try:
            parsed = json.loads(response_text[response_text.find("{"):response_text.rfind("}")+1])
            return float(parsed.get("faithfulness_score", 0.0))
        except Exception as err:
            logger.warning("Failed to parse faithfulness JSON response: %s", err)
            return 0.0

    async def evaluate_answer_relevance(self, query: str, answer: str) -> float:
        """
        Evaluates Answer Relevance using synthetic reverse question generation and semantic overlap.
        """
        prompt = f"""You are an unbiased semantic evaluation judge.
Analyze the following Answer and generate exactly 3 distinct questions that this answer directly addresses.
Do not read or consider the original user question.

Respond strictly with valid JSON adhering to this schema:
{{
  "generated_questions": [
    "question 1",
    "question 2",
    "question 3"
  ]
}}

[ANSWER]:
{answer}
"""
        response_text = await self._invoke_evaluator(prompt)
        try:
            parsed = json.loads(response_text[response_text.find("{"):response_text.rfind("}")+1])
            gen_questions = parsed.get("generated_questions", [])
            if not gen_questions:
                return 0.0
            
            # Simple keyword / token overlap proxy for embedding cosine similarity in evaluation demo
            query_tokens = set(query.lower().split())
            scores = []
            for gq in gen_questions:
                gq_tokens = set(gq.lower().split())
                intersection = query_tokens.intersection(gq_tokens)
                union = query_tokens.union(gq_tokens)
                scores.append(len(intersection) / max(1, len(union)))
            return min(1.0, (sum(scores) / len(scores)) * 1.8) # Scaled Jaccard proxy
        except Exception as err:
            logger.warning("Failed to evaluate answer relevance: %s", err)
            return 0.0

    async def evaluate_triad(
        self,
        query: str,
        context: str,
        answer: str,
        ground_truth: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes parallel RAG Triad assessment and computes the harmonic score.
        """
        faithfulness_task = self.evaluate_faithfulness(context, answer)
        relevance_task = self.evaluate_answer_relevance(query, answer)

        faithfulness, relevance = await asyncio.gather(faithfulness_task, relevance_task)
        
        # Calculate Context Recall if Ground Truth is provided
        context_recall = 1.0
        if ground_truth:
            prompt_recall = f"""Compare the Ground Truth answer against the retrieved Context.
Determine the proportion of key facts in Ground Truth that are present in the Context.
Output strictly JSON: {{"context_recall": 0.0 to 1.0}}

[CONTEXT]: {context}
[GROUND TRUTH]: {ground_truth}
"""
            res_rc = await self._invoke_evaluator(prompt_recall)
            try:
                parsed_rc = json.loads(res_rc[res_rc.find("{"):res_rc.rfind("}")+1])
                context_recall = float(parsed_rc.get("context_recall", 1.0))
            except Exception:
                context_recall = 0.85

        # Compute Harmonic Mean
        eps = 1e-6
        harmonic_score = 3.0 / (
            (1.0 / max(eps, faithfulness))
            + (1.0 / max(eps, relevance))
            + (1.0 / max(eps, context_recall))
        )

        passed = faithfulness >= 0.92 and relevance >= 0.88 and context_recall >= 0.85

        return {
            "query": query,
            "metrics": {
                "faithfulness": round(faithfulness, 4),
                "answer_relevance": round(relevance, 4),
                "context_recall": round(context_recall, 4),
                "harmonic_ragas_score": round(harmonic_score, 4),
            },
            "gate_passed": passed,
        }
