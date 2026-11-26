"""
Recipe 01.1: Enterprise Claude Messages API Client
Author: Vatsal Shah (Opportunity4u Press)
License: Apache-2.0
"""

import os
import sys
import time
import random
import logging
import asyncio
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel, Field, ValidationError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ClaudeGateway")

class TokenUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: Optional[int] = 0
    cache_read_input_tokens: Optional[int] = 0

class ContentBlock(BaseModel):
    type: str
    text: Optional[str] = None
    cache_control: Optional[Dict[str, str]] = None

class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: Any  # Union[str, List[ContentBlock]]

class ClaudeResponse(BaseModel):
    id: str
    type: str
    role: str
    model: str
    content: List[Dict[str, Any]]
    stop_reason: Optional[str] = None
    stop_sequence: Optional[str] = None
    usage: TokenUsage

class HardenedClaudeClient:
    """Production-grade asynchronous client for Anthropic Messages API."""
    
    BASE_URL = "https://api.anthropic.com/v1/messages"
    DEFAULT_API_VERSION = "2023-06-01"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout_seconds: float = 60.0,
        max_retries: int = 4,
        base_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 32.0
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Critical Security Error: ANTHROPIC_API_KEY environment variable missing.")
        
        self.max_retries = max_retries
        self.base_backoff = base_backoff_seconds
        self.max_backoff = max_backoff_seconds
        
        # Configure enterprise connection pool with keepalive tuning
        limits = httpx.Limits(max_keepalive_connections=50, max_connections=200, keepalive_expiry=30.0)
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds, connect=10.0),
            limits=limits,
            http2=True
        )

    async def close(self):
        await self.http_client.aclose()

    def _calculate_jittered_backoff(self, attempt: int) -> float:
        """Full Jitter backoff algorithm: Uniform(0, min(max_backoff, base * 2^attempt))."""
        ceiling = min(self.max_backoff, self.base_backoff * (2 ** attempt))
        return random.uniform(0, ceiling)

    async def execute_request(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        system: Optional[Any] = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> ClaudeResponse:
        """Executes a structured Messages API request with exponential backoff and telemetry extraction."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.DEFAULT_API_VERSION,
            "content-type": "application/json",
            "accept": "application/json"
        }
        if extra_headers:
            headers.update(extra_headers)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if system is not None:
            payload["system"] = system

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.perf_counter()
                response = await self.http_client.post(self.BASE_URL, headers=headers, json=payload)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                # Success Path
                if response.status_code == 200:
                    raw_data = response.json()
                    parsed = ClaudeResponse(**raw_data)
                    logger.info(
                        f"Claude API Success | ID: {parsed.id} | Model: {parsed.model} | "
                        f"Latency: {elapsed_ms:.1f}ms | InTok: {parsed.usage.input_tokens} | "
                        f"OutTok: {parsed.usage.output_tokens} | CacheRead: {parsed.usage.cache_read_input_tokens}"
                    )
                    return parsed

                # Transient Status Codes: 429 (Rate Limit), 529 (Overloaded), 500/503 (Server Error)
                if response.status_code in (429, 529, 500, 503):
                    retry_after = response.headers.get("retry-after")
                    if retry_after and retry_after.isdigit():
                        backoff = float(retry_after) + random.uniform(0.1, 0.5)
                    else:
                        backoff = self._calculate_jittered_backoff(attempt)
                    
                    logger.warning(
                        f"Transient Error HTTP {response.status_code} on attempt {attempt+1}/{self.max_retries+1}. "
                        f"Retrying in {backoff:.2f}s... Response: {response.text[:200]}"
                    )
                    await asyncio.sleep(backoff)
                    continue

                # Unrecoverable Client Error (400, 401, 403, 404)
                logger.error(f"Fatal Client Error HTTP {response.status_code}: {response.text}")
                response.raise_for_status()

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as net_err:
                last_exception = net_err
                backoff = self._calculate_jittered_backoff(attempt)
                logger.warning(f"Network error: {net_err}. Retrying in {backoff:.2f}s (Attempt {attempt+1})")
                await asyncio.sleep(backoff)

        raise RuntimeError(f"Claude API Failed after {self.max_retries} retries. Final error: {last_exception}")
