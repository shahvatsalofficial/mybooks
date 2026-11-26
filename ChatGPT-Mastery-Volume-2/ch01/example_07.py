"""
Enterprise OpenAI Resilient Gateway Client
Author: Vatsal Shah, Enterprise AI Architect
Version: 2.0 (Production Hardened)
"""
import os
import time
import random
import logging
from typing import Dict, Any, Optional, List
import httpx
from openai import OpenAI, APIError, RateLimitError, APITimeoutError
import tiktoken

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("EnterpriseGateway")

class EnterpriseGatewayClient:
    def __init__(
        self,
        project_id: str,
        api_key: Optional[str] = None,
        max_retries: int = 5,
        base_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 32.0,
        timeout_seconds: float = 45.0
    ):
        self.project_id = project_id
        self.max_retries = max_retries
        self.base_backoff = base_backoff_seconds
        self.max_backoff = max_backoff_seconds
        
        self.api_key = api_key or os.getenv(f"OPENAI_API_KEY_{project_id.upper()}") or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise EnvironmentError(f"Missing API key for project boundary: {project_id}")
            
        self.encoding = tiktoken.get_encoding("o200k_base")
        
        # Dedicated custom HTTP transport pool
        self.http_client = httpx.Client(
            transport=httpx.HTTPTransport(retries=0),
            timeout=httpx.Timeout(timeout_seconds, connect=5.0),
            limits=httpx.Limits(max_connections=200, max_keepalive_connections=50)
        )
        
        self.client = OpenAI(
            api_key=self.api_key,
            project=self.project_id,
            max_retries=0, # Bypassing native SDK retry to execute full jitter algorithm
            http_client=self.http_client
        )

    def _calculate_jitter_backoff(self, attempt: int) -> float:
        """
        Computes Exponential Backoff with Full Jitter:
        t_sleep = random(0, min(max_backoff, base * 2^attempt))
        """
        exponential = min(self.max_backoff, self.base_backoff * (2 ** attempt))
        return random.uniform(0, exponential)

    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        tokens = 3 # ChatML envelope
        for msg in messages:
            tokens += 3 + len(self.encoding.encode(msg.get("content", "")))
        return tokens

    def execute_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.2,
        hard_token_limit: int = 120000
    ) -> Dict[str, Any]:
        # 1. Pre-Flight Token Budget Audit
        prompt_tokens = self.count_tokens(messages)
        if prompt_tokens + max_tokens > hard_token_limit:
            raise ValueError(
                f"REJECTED: Pre-flight tokens ({prompt_tokens} prompt + {max_tokens} max) exceeds budget ({hard_token_limit})."
            )

        attempt = 0
        while True:
            try:
                logger.info(f"Dispatching API call (Attempt {attempt + 1}/{self.max_retries + 1}) to model {model}...")
                start_time = time.perf_counter()
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                latency = time.perf_counter() - start_time
                logger.info(
                    f"SUCCESS: Received response in {latency:.3f}s. "
                    f"Tokens: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out."
                )
                
                return {
                    "content": response.choices[0].message.content,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "latency_seconds": latency,
                    "system_fingerprint": response.system_fingerprint
                }

            except RateLimitError as rle:
                attempt += 1
                if attempt > self.max_retries:
                    logger.critical(f"FATAL: Exhausted all {self.max_retries} retries on RateLimitError.")
                    raise rle
                    
                # Inspect retry-after header if present
                server_retry_after = None
                if hasattr(rle, "response") and rle.response is not None:
                    server_retry_after = rle.response.headers.get("retry-after")
                    
                if server_retry_after and server_retry_after.isdigit():
                    sleep_time = float(server_retry_after) + random.uniform(0.1, 0.5)
                    logger.warning(f"Rate limited (429). Server requested explicit Retry-After: {sleep_time:.2f}s.")
                else:
                    sleep_time = self._calculate_jitter_backoff(attempt)
                    logger.warning(f"Rate limited (429). Applying full jitter backoff: {sleep_time:.2f}s.")
                    
                time.sleep(sleep_time)

            except (APITimeoutError, httpx.TimeoutException) as te:
                attempt += 1
                if attempt > self.max_retries:
                    logger.critical(f"FATAL: Network timeout persisted across {self.max_retries} retries.")
                    raise te
                sleep_time = self._calculate_jitter_backoff(attempt)
                logger.warning(f"Gateway Timeout. Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)

            except APIError as ae:
                # Differentiate transient 5xx server errors from fatal 4xx client errors
                if ae.status_code and ae.status_code >= 500:
                    attempt += 1
                    if attempt > self.max_retries:
                        raise ae
                    sleep_time = self._calculate_jitter_backoff(attempt)
                    logger.warning(f"OpenAI 5xx Server Error ({ae.status_code}). Backing off for {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Non-retryable client error encountered ({ae.status_code}): {ae.message}")
                    raise ae

    def close(self):
        self.http_client.close()
