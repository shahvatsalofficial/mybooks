"""
Recipe 08.1: Atomic Distributed Token Bucket in Redis
Author: Vatsal Shah (Vatsal Shah)
License: Apache-2.0
"""

import time
import asyncio
import logging
from typing import Optional, Tuple
import redis.asyncio as aioredis

logger = logging.getLogger("RateLimiter")

LUA_TOKEN_BUCKET = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local requested = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local state = redis.call('HMGET', key, 'tokens', 'last_updated')
local tokens = tonumber(state[1])
local last_updated = tonumber(state[2])

if not tokens then
    tokens = capacity
    last_updated = now
else
    local delta = math.max(0, now - last_updated)
    tokens = math.min(capacity, tokens + (delta * refill_rate))
end

if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', now)
    redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) * 2)
    return {1, 0} -- Allowed, zero wait
else
    local missing = requested - tokens
    local wait_time = missing / refill_rate
    return {0, wait_time} -- Denied with wait time
end
"""

class DistributedRateLimiter:
    def __init__(self, redis_url: str = "redis://localhost:6379", key_prefix: str = "claude:ratelimit"):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        self.key_prefix = key_prefix
        self.script_sha: Optional[str] = None

    async def initialize(self):
        self.script_sha = await self.redis.script_load(LUA_TOKEN_BUCKET)
        logger.info(f"Loaded Token Bucket Lua script. SHA: {self.script_sha}")

    async def acquire_dual_budget(self, tenant_id: str, estimated_tokens: int = 1500) -> None:
        """Atomically claims 1 Request Token (RPM) and N Context Tokens (TPM)."""
        rpm_key = f"{self.key_prefix}:{tenant_id}:rpm"
        tpm_key = f"{self.key_prefix}:{tenant_id}:tpm"

        # Tier 4 Enterprise: 4,000 RPM (66.67/s), 400,000 TPM (6,666.67/s)
        while True:
            now = time.time()
            
            # 1. Acquire RPM token
            res_rpm = await self.redis.evalsha(self.script_sha, 1, rpm_key, 4000, 66.67, 1, now)
            if res_rpm[0] == 0:
                wait_s = float(res_rpm[1])
                logger.warning(f"RPM quota saturated for [{tenant_id}]. Throttling for {wait_s:.2f}s...")
                await asyncio.sleep(min(wait_s, 2.0))
                continue

            # 2. Acquire TPM tokens
            res_tpm = await self.redis.evalsha(self.script_sha, 1, tpm_key, 400000, 6666.67, estimated_tokens, now)
            if res_tpm[0] == 0:
                wait_s = float(res_tpm[1])
                logger.warning(f"TPM quota saturated for [{tenant_id}]. Throttling for {wait_s:.2f}s...")
                await asyncio.sleep(min(wait_s, 3.0))
                continue

            # Successfully claimed both budgets
            return
