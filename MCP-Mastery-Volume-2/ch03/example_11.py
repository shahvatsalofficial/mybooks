"""
Distributed Redis Caching Tier with Distributed Mutex Lock & Stampede Prevention
Author: Vatsal Shah | Opportunity4u Press
Runtime: Python 3.11+ with redis.asyncio
"""

import time
import json
import hashlib
import logging
import asyncio
from typing import Callable, Any, Awaitable, Optional, Tuple
import redis.asyncio as aioredis

logger = logging.getLogger("mcp.cache.redis")

class RedisToolCacheManager:
    """Thread-safe, distributed tool output cache with stampede protection."""

    def __init__(self, redis_url: str, default_ttl_seconds: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl_seconds
        self._redis: Optional[aioredis.Redis] = None

    async def initialize(self):
        logger.info("Connecting to Redis tool cache cluster...")
        self._redis = aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=1.5
        )

    def generate_cache_key(self, tool_name: str, arguments: dict, tenant_id: str = "default") -> str:
        """Derive deterministic SHA-256 cache key from normalized arguments."""
        normalized_json = json.dumps(arguments, sort_keys=True)
        arg_hash = hashlib.sha256(normalized_json.encode("utf-8")).hexdigest()[:16]
        return f"mcp:cache:{{{tenant_id}}}:{tool_name}:{arg_hash}"

    async def get_or_compute(
        self,
        tool_name: str,
        arguments: dict,
        compute_fn: Callable[[], Awaitable[str]],
        tenant_id: str = "default",
        ttl: Optional[int] = None
    ) -> Tuple[str, bool]:
        """
        Retrieve cached payload or execute compute_fn under distributed lock.
        Returns: (result_payload: str, was_cache_hit: bool)
        """
        if not self._redis:
            # Fallback directly to compute if cache is offline
            return await compute_fn(), False

        cache_key = self.generate_cache_key(tool_name, arguments, tenant_id)
        lock_key = f"lock:{cache_key}"
        expiry = ttl or self.default_ttl

        # 1. Attempt Cache Read
        cached_val = await self._redis.get(cache_key)
        if cached_val:
            logger.debug(f"[CACHE HIT] Key: {cache_key}")
            return cached_val, True

        # 2. Cache Miss: Acquire Distributed Lock to Prevent Stampede
        # SET lock:key token NX EX 5
        acquired_lock = await self._redis.set(lock_key, "locked", nx=True, ex=5)

        if not acquired_lock:
            # Another worker is already computing this query; wait and poll
            logger.info(f"[LOCK WAIT] Concurrent worker computing: {cache_key}. Polling...")
            for _ in range(20):  # Poll for up to 2 seconds
                await asyncio.sleep(0.100)
                cached_val = await self._redis.get(cache_key)
                if cached_val:
                    logger.info(f"[LOCK RESOLVED] Retrieved value from primary worker: {cache_key}")
                    return cached_val, True

        try:
            # 3. Execute Expensive Downstream Database Query
            logger.info(f"[CACHE MISS & COMPUTE] Executing database query for: {cache_key}")
            start_t = time.perf_counter()
            result_payload = await compute_fn()
            duration_ms = (time.perf_counter() - start_t) * 1000.0

            # 4. Store in Cache with Configured TTL
            await self._redis.set(cache_key, result_payload, ex=expiry)
            logger.info(f"[CACHE STORED] Key: {cache_key} (Computed in {duration_ms:.1f}ms, TTL: {expiry}s)")
            return result_payload, False

        finally:
            # 5. Release Distributed Lock
            if acquired_lock:
                await self._redis.delete(lock_key)

    async def close(self):
        if self._redis:
            await self._redis.close()
