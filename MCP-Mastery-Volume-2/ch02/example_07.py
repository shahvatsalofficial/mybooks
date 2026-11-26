"""
Distributed Redis Lua Token Bucket Interceptor for Multi-Tenant MCP Fleets
Author: Vatsal Shah | Opportunity4u Press
Runtime: Python 3.11+ with redis.asyncio
"""

import time
import logging
import asyncio
from typing import Optional, Tuple
import redis.asyncio as aioredis
from mcp.shared.exceptions import McpError
from mcp.types import ErrorCode

logger = logging.getLogger("mcp.ratelimit.redis")

# Atomic Sliding Token Bucket Lua Script
# KEYS[1]: Redis key for tenant token bucket (e.g. "mcp:ratelimit:tenant_alpha")
# ARGV[1]: Bucket capacity (maximum tokens allowed)
# ARGV[2]: Refill rate in tokens per second
# ARGV[3]: Current UNIX timestamp in seconds (floating point)
# ARGV[4]: Requested tokens (cost of current tool call)
SLIDING_TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

-- Retrieve current state [tokens, last_updated]
local state = redis.call('HMGET', key, 'tokens', 'last_updated')
local tokens = tonumber(state[1])
local last_updated = tonumber(state[2])

if not tokens then
    -- Bucket does not exist; initialize to full capacity
    tokens = capacity
    last_updated = now
else
    -- Calculate tokens refilled since last request
    local elapsed = math.max(0, now - last_updated)
    tokens = math.min(capacity, tokens + (elapsed * refill_rate))
    last_updated = now
end

if tokens >= requested then
    -- Allow execution: deduct tokens and update timestamp
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)
    -- Expire bucket key after 1 hour of total inactivity
    redis.call('EXPIRE', key, 3600)
    return {1, tokens, 0}
else
    -- Reject execution: calculate wait time in seconds until enough tokens refill
    local deficit = requested - tokens
    local retry_after = deficit / refill_rate
    return {0, tokens, retry_after}
end
"""

class DistributedTenantRateLimiter:
    """Atomic distributed rate limiter backed by Redis Lua evaluation."""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
        self._script_sha: Optional[str] = None

    async def initialize(self):
        """Connect to Redis and pre-compile Lua script SHA."""
        logger.info("Connecting to Redis rate-limiting cluster...")
        self._redis = aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=2.0
        )
        self._script_sha = await self._redis.script_load(SLIDING_TOKEN_BUCKET_LUA)
        logger.info(f"Loaded Token Bucket Lua Script (SHA: {self._script_sha})")

    async def check_rate_limit(
        self,
        tenant_id: str,
        capacity: int = 60,
        refill_rate_per_sec: float = 2.0,
        cost: int = 1
    ) -> Tuple[bool, float, float]:
        """
        Evaluate rate limit atomically.
        Returns: (allowed: bool, remaining_tokens: float, retry_after_seconds: float)
        """
        if not self._redis or not self._script_sha:
            raise RuntimeError("Rate limiter not initialized")

        bucket_key = f"mcp:ratelimit:{tenant_id}:bucket"
        now = time.time()

        try:
            result = await self._redis.evalsha(
                self._script_sha,
                1,  # Number of KEYS
                bucket_key,
                capacity,
                refill_rate_per_sec,
                now,
                cost
            )
            allowed = bool(result[0] == 1)
            remaining_tokens = float(result[1])
            retry_after = float(result[2])
            return allowed, remaining_tokens, retry_after

        except aioredis.NoScriptError:
            # Script was flushed from Redis cache; reload and retry once
            logger.warning("Lua script cache miss in Redis. Reloading script...")
            self._script_sha = await self._redis.script_load(SLIDING_TOKEN_BUCKET_LUA)
            return await self.check_rate_limit(tenant_id, capacity, refill_rate_per_sec, cost)

    async def close(self):
        if self._redis:
            await self._redis.close()


# Interceptor Integration Example
async def enforce_tenant_quotas(
    rate_limiter: DistributedTenantRateLimiter,
    tenant_id: str,
    plan_tier: str
):
    """Enforces tiered quota limits per tenant before tool execution."""
    # Define SLA tiers
    tiers = {
        "STARTER": {"capacity": 20, "refill_rate": 0.5},       # 30 req/min
        "PRO": {"capacity": 60, "refill_rate": 2.0},           # 120 req/min
        "ENTERPRISE": {"capacity": 200, "refill_rate": 10.0}    # 600 req/min
    }
    quota = tiers.get(plan_tier, tiers["STARTER"])

    allowed, remaining, retry_after = await rate_limiter.check_rate_limit(
        tenant_id=tenant_id,
        capacity=quota["capacity"],
        refill_rate_per_sec=quota["refill_rate"],
        cost=1
    )

    if not allowed:
        logger.warning(
            f"Throttled tenant '{tenant_id}' (Plan: {plan_tier}). "
            f"Retry-After: {retry_after:.2f}s"
        )
        raise McpError(
            ErrorCode.InvalidRequest,
            f"Too Many Requests: Quota exceeded for tenant '{tenant_id}'. "
            f"Please retry after {retry_after:.1f} seconds."
        )

    logger.debug(f"Quota approved for '{tenant_id}'. Remaining tokens: {remaining:.1f}")
