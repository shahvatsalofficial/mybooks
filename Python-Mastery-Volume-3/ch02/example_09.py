# gateway/rate_limiter.py
"""Distributed atomic Token Bucket rate limiter using Redis and asynchronous Lua execution."""

from __future__ import annotations
import math
import time
from typing import NamedTuple

from fastapi import HTTPException, Request, Response, status
import redis.asyncio as aioredis

# Atomic Token Bucket Lua Script
# KEYS[1]: Rate limit key (e.g., "ratelimit:client_ip:192.168.1.1")
# ARGV[1]: Bucket capacity (maximum burst tokens)
# ARGV[2]: Refill rate in tokens per second
# ARGV[3]: Current UNIX timestamp in seconds
# ARGV[4]: Tokens requested (typically 1)
LUA_TOKEN_BUCKET = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

-- Retrieve current bucket state: [tokens, last_refreshed_timestamp]
local data = redis.call("HMGET", key, "tokens", "last_updated")
local tokens = tonumber(data[1])
local last_updated = tonumber(data[2])

if tokens == nil then
    -- Initialize new bucket at full capacity
    tokens = capacity
    last_updated = now
else
    -- Calculate replenished tokens based on elapsed duration
    local elapsed = math.max(0, now - last_updated)
    tokens = math.min(capacity, tokens + (elapsed * refill_rate))
    last_updated = now
end

if tokens >= requested then
    -- Permit transaction: deduct tokens and update state
    tokens = tokens - requested
    redis.call("HMSET", key, "tokens", tokens, "last_updated", last_updated)
    -- Set TTL to ensure key cleanup if idle (capacity / refill_rate * 2)
    local ttl = math.ceil((capacity / refill_rate) * 2)
    redis.call("EXPIRE", key, ttl)
    return {1, math.floor(tokens), 0}
else
    -- Reject transaction: calculate wait time until next token arrives
    local missing = requested - tokens
    local retry_after = math.ceil(missing / refill_rate)
    return {0, math.floor(tokens), retry_after}
end
"""


class RateLimitResult(NamedTuple):
    allowed: bool
    remaining_tokens: int
    retry_after_seconds: int


class DistributedRateLimiter:
    """Manages Redis connection and executes atomic token bucket enforcement."""

    def __init__(self, redis_client: aioredis.Redis, capacity: int = 100, refill_rate: float = 20.0) -> None:
        self.redis = redis_client
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._script = self.redis.register_script(LUA_TOKEN_BUCKET)

    async def check(self, identifier: str, cost: int = 1) -> RateLimitResult:
        """Atomically evaluates whether an incoming transaction is permitted."""
        key = f"ratelimit:{identifier}"
        now = time.time()
        
        # Execute registered script atomically on Redis cluster
        result = await self._script(
            keys=[key],
            args=[self.capacity, self.refill_rate, now, cost],
        )
        
        allowed, remaining, retry_after = result
        return RateLimitResult(
            allowed=bool(allowed),
            remaining_tokens=int(remaining),
            retry_after_seconds=int(retry_after),
        )


async def enforce_rate_limit(
    request: Request,
    response: Response,
    limiter: DistributedRateLimiter,
) -> None:
    """FastAPI route dependency enforcing rate limits per client IP or API key."""
    # Extract unique client identity (falling back to remote host IP)
    client_id = request.headers.get("X-API-Key") or request.client.host
    
    result = await limiter.check(client_id, cost=1)
    
    # Inject standard RFC rate-limiting telemetry headers
    response.headers["X-RateLimit-Limit"] = str(limiter.capacity)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining_tokens)
    
    if not result.allowed:
        response.headers["Retry-After"] = str(result.retry_after_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please slow down and respect rate limits.",
                "retry_after_seconds": result.retry_after_seconds,
            },
            headers={"Retry-After": str(result.retry_after_seconds)},
        )
