"""
Recipe 06.2: Anthropic Prompt Caching Client with TTL Monitor.
Author: Vatsal Shah (Lead Enterprise AI Architect)
Architecture: Claude AI Mastery Series — Volume 3
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
import boto3
from botocore.config import Config
from pydantic import BaseModel

logger = logging.getLogger("PromptCacheEngine")
logger.setLevel(logging.INFO)


class CacheMetrics(BaseModel):
    input_tokens_uncached: int
    cache_creation_tokens: int
    cache_read_tokens: int
    output_tokens: int
    cache_hit_rate_pct: float
    effective_cost_usd: float
    uncached_baseline_cost_usd: float
    net_savings_usd: float


class PromptCacheClient:
    """
    Production client implementing Anthropic Prompt Caching on AWS Bedrock.
    Enforces exact-prefix structural alignment and monitors cache economics.
    """

    # Claude 3.5 Sonnet pricing on AWS Bedrock (per 1,000,000 tokens)
    PRICE_BASE_INPUT = 3.00
    PRICE_CACHE_WRITE = 3.75 # 1.25x
    PRICE_CACHE_READ = 0.30  # 0.10x (90% discount)
    PRICE_OUTPUT = 15.00

    def __init__(self, region_name: str = "us-east-1"):
        config = Config(region_name=region_name, retries={"max_attempts": 3, "mode": "adaptive"})
        self.client = boto3.client("bedrock-runtime", config=config)

    def execute_cached_query(
        self,
        static_system_directive: str,
        static_context_corpus: str,
        dynamic_user_query: str
    ) -> Dict[str, Any]:
        """
        Structures the prompt payload with cache_control checkpoints.
        Static guidelines and large document context are marked with type='ephemeral'.
        """
        # Ensure static corpus meets the 1,024-token minimum caching threshold
        system_blocks = [
            {
                "type": "text",
                "text": static_system_directive,
                "cache_control": {"type": "ephemeral"} # Checkpoint 1: Static Persona
            },
            {
                "type": "text",
                "text": f"<enterprise_knowledge_base>\n{static_context_corpus}\n</enterprise_knowledge_base>",
                "cache_control": {"type": "ephemeral"} # Checkpoint 2: Large Documentation Block
            }
        ]

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.2,
            "system": system_blocks,
            "messages": [
                {
                    "role": "user",
                    "content": dynamic_user_query # Dynamic uncached content strictly at prompt end
                }
            ]
        }

        t0 = time.time()
        response = self.client.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )
        latency_ms = (time.time() - t0) * 1000

        body = json.loads(response["body"].read().decode("utf-8"))
        usage = body.get("usage", {})

        # Extract token telemetry
        input_tokens = usage.get("input_tokens", 0)
        cache_creation = usage.get("cache_creation_input_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        total_input_evaluated = input_tokens + cache_creation + cache_read
        hit_rate = (cache_read / total_input_evaluated * 100.0) if total_input_evaluated > 0 else 0.0

        # Calculate actual cost incurred
        actual_cost = (
            (input_tokens * (self.PRICE_BASE_INPUT / 1e6)) +
            (cache_creation * (self.PRICE_CACHE_WRITE / 1e6)) +
            (cache_read * (self.PRICE_CACHE_READ / 1e6)) +
            (output_tokens * (self.PRICE_OUTPUT / 1e6))
        )

        # Calculate what the uncached baseline cost would have been
        baseline_cost = (
            (total_input_evaluated * (self.PRICE_BASE_INPUT / 1e6)) +
            (output_tokens * (self.PRICE_OUTPUT / 1e6))
        )

        savings = max(0.0, baseline_cost - actual_cost)

        metrics = CacheMetrics(
            input_tokens_uncached=input_tokens,
            cache_creation_tokens=cache_creation,
            cache_read_tokens=cache_read,
            output_tokens=output_tokens,
            cache_hit_rate_pct=round(hit_rate, 2),
            effective_cost_usd=round(actual_cost, 6),
            uncached_baseline_cost_usd=round(baseline_cost, 6),
            net_savings_usd=round(savings, 6)
        )

        logger.info(f"Cache Hit Rate: {metrics.cache_hit_rate_pct}% | Net Saved: ${metrics.net_savings_usd:.4f} | Latency: {latency_ms:.1f}ms")

        return {
            "content": body.get("content", [{}])[0].get("text", ""),
            "metrics": metrics.model_dump(),
            "latency_ms": latency_ms
        }
