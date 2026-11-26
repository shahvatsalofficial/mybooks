"""
Recipe 06.1: Production Cognitive Complexity Router for Claude AI.
Author: Vatsal Shah (Lead Enterprise AI Architect)
Architecture: Claude AI Mastery Series — Volume 3
"""

import logging
import re
import time
from typing import Dict, Any, List, Optional
import boto3
from botocore.config import Config
from pydantic import BaseModel, Field

logger = logging.getLogger("FinOpsComplexityRouter")
logger.setLevel(logging.INFO)


class ComplexityScore(BaseModel):
    total_score: float = Field(..., ge=0.0, le=1.0)
    reasoning_depth_score: float
    math_density_score: float
    code_syntax_score: float
    selected_tier: str
    target_model_id: str
    estimated_cost_savings_pct: float


class CognitiveComplexityRouter:
    """
    Evaluates prompt complexity across semantic and syntactic dimensions
    to dynamically route traffic between Haiku 3.5, Sonnet 3.5, and Opus 3.
    """

    MODEL_TIERS = {
        "TIER_1_HAIKU": "anthropic.claude-3-5-haiku-20241022-v1:0",
        "TIER_2_SONNET": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "TIER_3_OPUS": "anthropic.claude-3-opus-20240229-v1:0",
    }

    # Regex indicators for reasoning complexity, math density, and code requirements
    CODE_KEYWORDS = re.compile(r"\b(def|class|function|sql|select|insert|update|terraform|lambda|async|await)\b", re.IGNORECASE)
    MATH_KEYWORDS = re.compile(r"(\$|%|\+|\-|\*|\/|=|\bvariance\b|\bz-score\b|\bequity\b|\bamortization\b)", re.IGNORECASE)
    REASONING_KEYWORDS = re.compile(r"\b(analyze|evaluate|critique|synthesize|reconcile|deduce|counterfactual|sox-404)\b", re.IGNORECASE)

    def __init__(self, region_name: str = "us-east-1"):
        config = Config(region_name=region_name, retries={"max_attempts": 3, "mode": "adaptive"})
        self.client = boto3.client("bedrock-runtime", config=config)

    def evaluate_complexity(self, prompt: str) -> ComplexityScore:
        """Calculates normalized complexity score based on text heuristics."""
        word_count = len(prompt.split())
        if word_count == 0:
            return ComplexityScore(
                total_score=0.1, reasoning_depth_score=0.0, math_density_score=0.0,
                code_syntax_score=0.0, selected_tier="TIER_1_HAIKU",
                target_model_id=self.MODEL_TIERS["TIER_1_HAIKU"],
                estimated_cost_savings_pct=92.0
            )

        # 1. Code Syntax Density (0.0 to 1.0)
        code_matches = len(self.CODE_KEYWORDS.findall(prompt))
        code_score = min(1.0, (code_matches * 15) / word_count)

        # 2. Mathematical Density (0.0 to 1.0)
        math_matches = len(self.MATH_KEYWORDS.findall(prompt))
        math_score = min(1.0, (math_matches * 12) / word_count)

        # 3. Deep Reasoning Indicators (0.0 to 1.0)
        reasoning_matches = len(self.REASONING_KEYWORDS.findall(prompt))
        reasoning_score = min(1.0, (reasoning_matches * 20) / word_count)

        # 4. Composite Weighted Score
        composite = (0.45 * reasoning_score) + (0.30 * code_score) + (0.25 * math_score)

        # Tier Decision Gates
        if composite < 0.35:
            tier = "TIER_1_HAIKU"
            savings = 92.0 # 92% cheaper than Sonnet
        elif composite <= 0.80:
            tier = "TIER_2_SONNET"
            savings = 80.0 # 80% cheaper than Opus
        else:
            tier = "TIER_3_OPUS"
            savings = 0.0 # Full baseline cost

        return ComplexityScore(
            total_score=round(composite, 4),
            reasoning_depth_score=round(reasoning_score, 4),
            math_density_score=round(math_score, 4),
            code_syntax_score=round(code_score, 4),
            selected_tier=tier,
            target_model_id=self.MODEL_TIERS[tier],
            estimated_cost_savings_pct=savings
        )

    def route_and_execute(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Evaluates complexity and invokes the optimal model tier with automatic fallback."""
        decision = self.evaluate_complexity(prompt)
        logger.info(f"Routed query to [{decision.selected_tier}] (Score: {decision.total_score}, Savings: {decision.estimated_cost_savings_pct}%)")

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            payload["system"] = system_prompt

        t0 = time.time()
        try:
            response = self.client.invoke_model(
                modelId=decision.target_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )
            body = json.loads(response["body"].read().decode("utf-8"))
            return {
                "content": body.get("content", [{}])[0].get("text", ""),
                "usage": body.get("usage", {}),
                "routing_decision": decision.model_dump(),
                "latency_ms": (time.time() - t0) * 1000
            }
        except Exception as e:
            # Fallback policy: If Haiku or Opus fails, fallback to reliable Sonnet 3.5
            logger.warning(f"Invocation of [{decision.target_model_id}] failed: {str(e)}. Falling back to Sonnet 3.5.")
            fallback_response = self.client.invoke_model(
                modelId=self.MODEL_TIERS["TIER_2_SONNET"],
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )
            body = json.loads(fallback_response["body"].read().decode("utf-8"))
            return {
                "content": body.get("content", [{}])[0].get("text", ""),
                "usage": body.get("usage", {}),
                "routing_decision": {"fallback": True, "executed_model": self.MODEL_TIERS["TIER_2_SONNET"]},
                "latency_ms": (time.time() - t0) * 1000
            }
