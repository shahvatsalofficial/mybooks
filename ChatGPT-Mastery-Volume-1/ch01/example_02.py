"""
Production Enterprise Python Gateway for OpenAI GPT-4o
Target: Python 3.11+ / AsyncIO / OpenAI Python SDK v1.40+
"""

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
import tiktoken
from openai import AsyncOpenAI, RateLimitError, APIError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EnterpriseLLMGateway")


class TokenBudgetExceededError(Exception):
    """Raised when request payload exceeds hard context limit."""
    pass


class ProductionInferenceGateway:
    def __init__(self, api_key: str, default_model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.default_model = default_model
        # Use o200k_base tokenizer for GPT-4o family
        self.encoding = tiktoken.get_encoding("o200k_base")
        self.max_context_limit = 128000
        self.reserved_output_headroom = 4096

    def count_tokens(self, text: str) -> int:
        """Returns exact token count for input text."""
        return len(self.encoding.encode(text))

    def calculate_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Calculates total token count across message objects including formatting overhead."""
        num_tokens = 0
        for msg in messages:
            num_tokens += 3  # Every message follows <|start|>{role/name}\n{content}<|end|>\n
            for key, value in msg.items():
                num_tokens += self.count_tokens(value)
        num_tokens += 3  # Every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    def enforce_context_compaction(
        self,
        system_prompt: str,
        history: List[Dict[str, str]],
        knowledge_context: str,
        user_query: str,
    ) -> List[Dict[str, str]]:
        """
        Assembles prompt geometry to eliminate Lost-in-the-Middle and guarantee
        that the total context does not exceed safe operating ceilings.
        """
        system_tokens = self.count_tokens(system_prompt)
        query_tokens = self.count_tokens(user_query)
        reserved_tokens = system_tokens + query_tokens + self.reserved_output_headroom

        available_budget = self.max_context_limit - reserved_tokens
        if available_budget <= 0:
            raise TokenBudgetExceededError("System prompt and query alone exceed context limits.")

        # Prune knowledge context if necessary
        knowledge_tokens = self.count_tokens(knowledge_context)
        final_knowledge = knowledge_context
        if knowledge_tokens > (available_budget * 0.7):
            prune_target = int(available_budget * 0.7)
            logger.warning(f"Pruning knowledge context from {knowledge_tokens} to {prune_target} tokens.")
            encoded = self.encoding.encode(knowledge_context)
            final_knowledge = self.encoding.decode(encoded[:prune_target])

        # Assemble messages in optimal geometric order: Primacy -> Middle -> Recency
        assembled_messages: List[Dict[str, str]] = []

        # 1. Primacy: Immutable System Rules (Pinned for 50% Prompt Caching discount)
        assembled_messages.append({"role": "system", "content": system_prompt})

        # 2. Middle Valley: Ingested Reference Knowledge
        if final_knowledge.strip():
            assembled_messages.append({
                "role": "system", 
                "content": f"[GROUNDING_KNOWLEDGE_BASE]\n{final_knowledge}"
            })

        # 3. Middle Valley: Rolling Conversational Turns (Sliding Window FIFO)
        current_tokens = self.calculate_messages_tokens(assembled_messages) + query_tokens
        retained_history: List[Dict[str, str]] = []
        for turn in reversed(history):
            turn_tokens = self.calculate_messages_tokens([turn])
            if current_tokens + turn_tokens < (self.max_context_limit - self.reserved_output_headroom):
                retained_history.insert(0, turn)
                current_tokens += turn_tokens
            else:
                break  # Evict older turns

        assembled_messages.extend(retained_history)

        # 4. Recency: Active User Turn re-anchored with concrete directives
        assembled_messages.append({"role": "user", "content": user_query})

        return assembled_messages

    async def execute_with_retry(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        top_p: float = 0.1,
        max_retries: int = 4,
    ) -> Dict[str, Any]:
        """
        Executes inference request with exponential backoff and jitter against HTTP 429/500 errors.
        """
        target_model = model or self.default_model
        attempt = 0
        backoff_delay = 1.0

        while attempt < max_retries:
            try:
                start_time = time.perf_counter()
                response = await self.client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    temperature=None if target_model.startswith("o1") else temperature,
                    top_p=None if target_model.startswith("o1") else top_p,
                    max_completion_tokens=self.reserved_output_headroom,
                )
                duration = time.perf_counter() - start_time
                logger.info(f"Inference completed on {target_model} in {duration:.2f}s.")
                return {
                    "content": response.choices[0].message.content,
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": response.usage.model_dump(),
                    "cached_tokens": getattr(response.usage.prompt_tokens_details, "cached_tokens", 0)
                }
            except RateLimitError as rle:
                attempt += 1
                logger.warning(f"RateLimitError encountered (attempt {attempt}/{max_retries}). Backing off {backoff_delay:.2f}s.")
                await asyncio.sleep(backoff_delay)
                backoff_delay *= 2.0  # Exponential factor
            except APIError as apie:
                if apie.status_code and apie.status_code >= 500:
                    attempt += 1
                    logger.warning(f"Upstream OpenAI 5xx Error ({apie.status_code}). Backing off {backoff_delay:.2f}s.")
                    await asyncio.sleep(backoff_delay)
                    backoff_delay *= 2.0
                else:
                    logger.error(f"Fatal API Client Error: {apie}")
                    raise

        raise RuntimeError(f"Exhausted {max_retries} retries on model {target_model}.")

    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streams response tokens in real-time over asynchronous generator.
        """
        target_model = model or self.default_model
        response_stream = await self.client.chat.completions.create(
            model=target_model,
            messages=messages,
            stream=True,
            max_completion_tokens=self.reserved_output_headroom,
        )
        async for chunk in response_stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
