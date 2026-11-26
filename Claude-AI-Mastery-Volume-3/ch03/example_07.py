"""
Recipe 03.3: Production Active-Active Multi-Cloud Arbiter for AWS Bedrock & GCP Vertex AI.
Author: Vatsal Shah (Lead Enterprise AI Architect)
Architecture: Claude AI Mastery Series — Volume 3
"""

import asyncio
import logging
import time
from typing import AsyncGenerator, Dict, Any, List, Optional
from enum import Enum
import httpx

logger = logging.getLogger("MultiCloudArbiter")
logger.setLevel(logging.INFO)


class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal healthy execution
    OPEN = "OPEN"          # Provider failed; shedding all traffic
    HALF_OPEN = "HALF_OPEN"# Testing canary requests for recovery


class ProviderCircuitBreaker:
    """Maintains consecutive failure counts and circuit state for a cloud provider."""

    def __init__(self, provider_name: str, failure_threshold: int = 5, recovery_timeout_sec: float = 60.0):
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_sec
        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.last_failure_time = 0.0

    def record_success(self) -> None:
        self.consecutive_failures = 0
        if self.state != CircuitState.CLOSED:
            logger.info(f"[{self.provider_name}] Circuit recovered -> CLOSED")
            self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        if self.consecutive_failures >= self.failure_threshold and self.state == CircuitState.CLOSED:
            logger.warning(f"[{self.provider_name}] Threshold exceeded ({self.consecutive_failures}) -> Circuit OPEN")
            self.state = CircuitState.OPEN

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(f"[{self.provider_name}] Recovery timeout expired -> Testing HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN allows single canary probe


class MultiCloudClaudeArbiter:
    """
    Enterprise Arbiter managing dual active-active routes across AWS Bedrock and GCP Vertex AI.
    Executes hedged speculative calls when TTFT exceeds threshold.
    """

    def __init__(
        self,
        bedrock_client: Any,
        vertex_client: Any,
        hedge_delay_seconds: float = 0.600
    ):
        self.bedrock = bedrock_client
        self.vertex = vertex_client
        self.hedge_delay = hedge_delay_seconds
        self.cb_bedrock = ProviderCircuitBreaker("AWS_Bedrock")
        self.cb_vertex = ProviderCircuitBreaker("GCP_Vertex")

    async def execute_hedged_chat(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str = "",
        max_tokens: int = 4096
    ) -> AsyncGenerator[str, None]:
        """
        Launches primary request to available provider. If first token delayed by hedge_delay,
        dispatches parallel hedged request to alternate provider.
        """
        bedrock_ready = self.cb_bedrock.can_execute()
        vertex_ready = self.cb_vertex.can_execute()

        if not bedrock_ready and not vertex_ready:
            raise RuntimeError("Fatal: Both AWS Bedrock and GCP Vertex AI circuits are OPEN. System paralyzed.")

        # Determine primary and secondary based on health
        if bedrock_ready and vertex_ready:
            primary_name, primary_client, primary_cb = "AWS_Bedrock", self.bedrock, self.cb_bedrock
            secondary_name, secondary_client, secondary_cb = "GCP_Vertex", self.vertex, self.cb_vertex
        elif bedrock_ready:
            primary_name, primary_client, primary_cb = "AWS_Bedrock", self.bedrock, self.cb_bedrock
            secondary_name, secondary_client, secondary_cb = None, None, None
        else:
            primary_name, primary_client, primary_cb = "GCP_Vertex", self.vertex, self.cb_vertex
            secondary_name, secondary_client, secondary_cb = None, None, None

        logger.info(f"Selected Primary Route: [{primary_name}]")

        token_queue: asyncio.Queue = asyncio.Queue()
        winner_declared = asyncio.Event()

        async def worker(provider_name: str, client: Any, cb: ProviderCircuitBreaker, is_hedged: bool = False):
            if is_hedged:
                await asyncio.sleep(self.hedge_delay)
                if winner_declared.is_set():
                    return
                logger.info(f"Hedge timer ({self.hedge_delay*1000}ms) elapsed. Dispatching parallel [{provider_name}]")

            first_token_sent = False
            try:
                # Call respective streaming method
                stream = client.stream_chat(messages=messages, system_prompt=system_prompt, max_tokens=max_tokens)
                async for chunk in stream:
                    if not first_token_sent:
                        if winner_declared.is_set():
                            # Another provider won the race; abort immediately
                            logger.info(f"[{provider_name}] Aborting execution: race won by alternate provider.")
                            return
                        winner_declared.set()
                        first_token_sent = True
                        cb.record_success()
                        logger.info(f"[{provider_name}] WON the execution race! Streaming output.")

                    text = chunk.delta_text if hasattr(chunk, "delta_text") else str(chunk)
                    await token_queue.put(text)

                await token_queue.put(None)  # Sentinel to mark completion

            except Exception as e:
                logger.error(f"[{provider_name}] Worker error: {str(e)}")
                cb.record_failure()
                if not first_token_sent:
                    # If this was primary and failed before token, let secondary take over
                    logger.warning(f"[{provider_name}] Failed prior to first token.")

        tasks = [asyncio.create_task(worker(primary_name, primary_client, primary_cb, is_hedged=False))]
        if secondary_name:
            tasks.append(asyncio.create_task(worker(secondary_name, secondary_client, secondary_cb, is_hedged=True)))

        try:
            while True:
                token = await token_queue.get()
                if token is None:
                    break
                yield token
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
