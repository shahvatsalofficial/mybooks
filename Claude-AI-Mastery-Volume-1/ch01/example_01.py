"""
Enterprise Claude Architecture Gateway & Dynamic Router
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Vatsal Shah (c) 2026
"""

import os
import sys
import time
import json
import random
import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
import anthropic

# Configure structured enterprise logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [ClaudeGateway] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ClaudeGateway")

class ClaudeTier(str, Enum):
    HAIKU = "claude-3-5-haiku-20241022"
    SONNET = "claude-3-5-sonnet-20241022"
    OPUS = "claude-3-opus-20240229"

class TaskComplexity(str, Enum):
    TRIVIAL = "trivial"          # Extraction, classification, routing -> Haiku
    INTERMEDIATE = "intermediate" # Drafting, standard QA, summarization -> Sonnet/Haiku
    COMPLEX = "complex"          # Code generation, multi-file refactoring -> Sonnet
    DEEP_SYNTHESIS = "deep"      # Ambiguous legal/philosophical review -> Opus/Sonnet

class EnterpriseClaudeGateway:
    """
    Industrial-grade gateway managing model selection, resilient retry loops,
    and prompt-caching headers across the Claude 3.5 model family.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.critical("FATAL: ANTHROPIC_API_KEY environment variable is missing.")
            raise ValueError("ANTHROPIC_API_KEY must be provided.")
        
        # Initialize official asynchronous/synchronous Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info("Enterprise Claude Gateway successfully initialized.")

    def classify_task_complexity(self, prompt: str, system_prompt: str) -> TaskComplexity:
        """
        Determines reasoning complexity using heuristic token evaluation
        and semantic keyword detection.
        """
        combined_text = (prompt + " " + system_prompt).lower()
        token_estimate = len(combined_text.split()) * 1.33

        # Complex coding and schema markers
        code_markers = [
            "def ", "class ", "interface ", "async ", "sql", "pydantic", 
            "refactor", "ast", "fastapi", "typescript", "regex", "dockerfile"
        ]
        if any(marker in combined_text for marker in code_markers):
            return TaskComplexity.COMPLEX

        # Deep qualitative synthesis markers
        synthesis_markers = [
            "philosophical", "cross-jurisdictional", "epistemological", 
            "forensic audit", "board briefing", "ambiguous precedent"
        ]
        if any(marker in combined_text for marker in synthesis_markers):
            return TaskComplexity.DEEP_SYNTHESIS

        # Length and structure based routing
        if token_estimate < 1000 and not any(m in combined_text for m in ["architect", "analyze", "synthesize"]):
            return TaskComplexity.TRIVIAL

        return TaskComplexity.INTERMEDIATE

    def select_optimal_model(self, complexity: TaskComplexity, latency_sensitive: bool = False) -> ClaudeTier:
        """
        Maps classified task complexity to the most economical and capable model tier.
        """
        if latency_sensitive or complexity == TaskComplexity.TRIVIAL:
            return ClaudeTier.HAIKU
        
        if complexity in [TaskComplexity.INTERMEDIATE, TaskComplexity.COMPLEX]:
            return ClaudeTier.SONNET
        
        if complexity == TaskComplexity.DEEP_SYNTHESIS:
            return ClaudeTier.OPUS

        return ClaudeTier.SONNET

    def calculate_cost_estimate(self, model: str, input_tok: int, output_tok: int, cache_read_tok: int) -> float:
        """
        Calculates exact cost in USD based on Anthropic official pricing schedules.
        """
        if "haiku" in model:
            base_in = 0.80 / 1_000_000
            base_out = 4.00 / 1_000_000
            cache_read = 0.08 / 1_000_000
        elif "sonnet" in model:
            base_in = 3.00 / 1_000_000
            base_out = 15.00 / 1_000_000
            cache_read = 0.30 / 1_000_000
        else: # Opus
            base_in = 15.00 / 1_000_000
            base_out = 75.00 / 1_000_000
            cache_read = 1.50 / 1_000_000

        uncached_in = max(0, input_tok - cache_read_tok)
        total_cost = (uncached_in * base_in) + (cache_read_tok * cache_read) + (output_tok * base_out)
        return round(total_cost, 6)

    def execute_reasoning_request(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.0,
        enable_cache: bool = True,
        latency_sensitive: bool = False,
        max_retries: int = 4
    ) -> Dict[str, Any]:
        """
        Dispatches request through resilient retry loop with exponential backoff and jitter.
        """
        complexity = self.classify_task_complexity(prompt, system_prompt)
        selected_model = self.select_optimal_model(complexity, latency_sensitive)
        
        logger.info(f"Dispatching task [Complexity: {complexity.value}] -> Model: {selected_model.value}")
        
        # Construct system message payload with optional prompt caching block
        system_payload = []
        if system_prompt:
            system_block = {"type": "text", "text": system_prompt}
            if enable_cache and len(system_prompt) > 2000:
                # Inject ephemeral prompt cache breakpoint (Anthropic 5-minute TTL)
                system_block["cache_control"] = {"type": "ephemeral"}
            system_payload.append(system_block)

        messages_payload = [{"role": "user", "content": prompt}]

        attempt = 0
        backoff_base = 1.0

        while attempt < max_retries:
            attempt += 1
            start_time = time.time()
            try:
                response = self.client.messages.create(
                    model=selected_model.value,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_payload if system_payload else None,
                    messages=messages_payload
                )
                duration_ms = int((time.time() - start_time) * 1000)

                # Extract telemetry metrics
                usage = response.usage
                cache_read = getattr(usage, "cache_read_input_tokens", 0)
                cache_write = getattr(usage, "cache_creation_input_tokens", 0)
                
                cost_usd = self.calculate_cost_estimate(
                    selected_model.value, 
                    usage.input_tokens, 
                    usage.output_tokens, 
                    cache_read
                )

                telemetry = {
                    "model": selected_model.value,
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "cache_creation_tokens": cache_write,
                    "cache_read_tokens": cache_read,
                    "latency_ms": duration_ms,
                    "stop_reason": response.stop_reason,
                    "estimated_cost_usd": cost_usd
                }

                logger.info(
                    f"Execution Success! Model: {selected_model.name} | "
                    f"In: {usage.input_tokens} | Out: {usage.output_tokens} | "
                    f"CacheRead: {cache_read} | Cost: ${cost_usd:.4f} | Latency: {duration_ms}ms"
                )

                output_text = "".join([block.text for block in response.content if block.type == "text"])

                return {
                    "status": "SUCCESS",
                    "output": output_text,
                    "telemetry": telemetry
                }

            except anthropic.RateLimitError as rle:
                jitter = random.uniform(0.1, 0.5)
                sleep_time = (backoff_base * (2 ** (attempt - 1))) + jitter
                logger.warning(f"Rate limited (429). Retrying in {sleep_time:.2f}s... (Attempt {attempt}/{max_retries})")
                time.sleep(sleep_time)
                
                # Auto-fallback to Haiku on secondary retry if currently using Sonnet/Opus
                if attempt >= 2 and selected_model != ClaudeTier.HAIKU:
                    logger.warning("Cascading fallback triggered: Demoting to Claude 3.5 Haiku to preserve throughput.")
                    selected_model = ClaudeTier.HAIKU

            except anthropic.APIStatusError as ase:
                logger.error(f"Anthropic API Error [{ase.status_code}]: {ase.message}")
                if ase.status_code in [500, 502, 503, 529]:  # Server overloaded / transient gateway errors
                    sleep_time = (backoff_base * (2 ** (attempt - 1))) + random.uniform(0.2, 0.8)
                    time.sleep(sleep_time)
                else:
                    raise ase

            except Exception as e:
                logger.error(f"Unexpected fatal error during reasoning dispatch: {str(e)}")
                raise e

        raise RuntimeError(f"ClaudeGateway exhausted all {max_retries} retry attempts without successful completion.")

# Demonstration harness for enterprise verification
if __name__ == "__main__":
    gateway = EnterpriseClaudeGateway()

    # Test 1: Trivial Classification (Haiku routing verification)
    sample_trivial = "Classify sentiment: 'The transaction cleared without any protocol errors.'"
    res_trivial = gateway.execute_reasoning_request(prompt=sample_trivial)
    print(f"\n--- Test 1 Output ({res_trivial['telemetry']['model']}) ---")
    print(res_trivial["output"])

    # Test 2: Complex Engineering Schema (Sonnet routing verification)
    sample_code = """
    Write an asynchronous Python function using httpx to query an OpenSearch cluster,
    implementing mutual TLS (mTLS) authentication and streaming JSON response parsing.
    """
    res_code = gateway.execute_reasoning_request(
        prompt=sample_code,
        system_prompt="You are a principal systems architect. Emit clean, production-grade Python only."
    )
    print(f"\n--- Test 2 Output ({res_code['telemetry']['model']}) ---")
    print(res_code["output"][:300] + "... [truncated]")
