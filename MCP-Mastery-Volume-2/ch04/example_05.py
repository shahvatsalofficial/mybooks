"""
Distributed Redis-Backed Circuit Breaker for Upstream API Bridges
Author: Vatsal Shah | Opportunity4u Press
Runtime: Python 3.11+ with redis.asyncio
"""

import time
import logging
from enum import Enum
from typing import Callable, Awaitable, Any, Optional
import redis.asyncio as aioredis
from mcp.shared.exceptions import McpError
from mcp.types import ErrorCode

logger = logging.getLogger("mcp.resilience.circuit_breaker")

class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class DistributedCircuitBreaker:
    """Manages distributed circuit state across multiple MCP gateway instances."""

    def __init__(
        self,
        service_name: str,
        redis_client: aioredis.Redis,
        failure_threshold_pct: float = 50.0,
        rolling_window_requests: int = 20,
        sleep_window_seconds: int = 30
    ):
        self.service = service_name
        self.redis = redis_client
        self.failure_threshold = failure_threshold_pct
        self.rolling_window = rolling_window_requests
        self.sleep_window = sleep_window_seconds

        self.state_key = f"circuit:{self.service}:state"
        self.history_key = f"circuit:{self.service}:history"
        self.trip_time_key = f"circuit:{self.service}:trip_time"

    async def get_state(self) -> CircuitState:
        """Evaluate and return active circuit state, handling sleep window expiration."""
        raw_state = await self.redis.get(self.state_key)
        state = CircuitState(raw_state) if raw_state else CircuitState.CLOSED

        if state == CircuitState.OPEN:
            trip_time = float(await self.redis.get(self.trip_time_key) or 0)
            if time.time() - trip_time > self.sleep_window:
                logger.info(f"[{self.service}] Sleep window elapsed. Transitioning from OPEN to HALF_OPEN.")
                await self.redis.set(self.state_key, CircuitState.HALF_OPEN.value)
                return CircuitState.HALF_OPEN

        return state

    async def execute(self, action_fn: Callable[[], Awaitable[Any]]) -> Any:
        """Execute upstream API call guarded by distributed circuit breaker."""
        state = await self.get_state()

        if state == CircuitState.OPEN:
            logger.warning(f"[{self.service}] Circuit is OPEN. Short-circuiting call.")
            raise McpError(
                ErrorCode.InternalError,
                f"Upstream service '{self.service}' is degraded (Circuit Breaker OPEN). Operation halted."
            )

        try:
            result = await action_fn()
            await self._record_result(success=True)
            if state == CircuitState.HALF_OPEN:
                logger.info(f"[{self.service}] Probe succeeded! Resetting circuit to CLOSED.")
                await self.redis.set(self.state_key, CircuitState.CLOSED.value)
                await self.redis.delete(self.history_key)
            return result

        except Exception as ex:
            await self._record_result(success=False)
            if state == CircuitState.HALF_OPEN:
                logger.warning(f"[{self.service}] Probe failed! Tripping circuit back to OPEN.")
                await self._trip_circuit()
            raise ex

    async def _record_result(self, success: bool):
        """Record binary result in sliding window list in Redis."""
        val = 1 if success else 0
        pipe = self.redis.pipeline()
        pipe.lpush(self.history_key, val)
        pipe.ltrim(self.history_key, 0, self.rolling_window - 1)
        res = await pipe.execute()

        # Check failure rate if window is full
        history = await self.redis.lrange(self.history_key, 0, -1)
        if len(history) >= self.rolling_window:
            failures = sum(1 for item in history if int(item) == 0)
            rate = (failures / len(history)) * 100.0
            if rate >= self.failure_threshold:
                logger.error(f"[{self.service}] Failure rate {rate:.1f}% exceeded threshold! Tripping circuit.")
                await self._trip_circuit()

    async def _trip_circuit(self):
        pipe = self.redis.pipeline()
        pipe.set(self.state_key, CircuitState.OPEN.value)
        pipe.set(self.trip_time_key, time.time())
        await pipe.execute()
