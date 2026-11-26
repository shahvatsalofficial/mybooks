"""
Distributed Sliding-Window Token Bucket Rate Limiter
Prevents race conditions using atomic Redis Lua scripts.
Author: Vatsal Shah, Enterprise AI Architect
"""
import time
import redis
from typing import Tuple

class RedisTokenBucketRateLimiter:
    LUA_SCRIPT = """
    local key = KEYS[1]
    local capacity = tonumber(ARGV[1])
    local refill_rate = tonumber(ARGV[2])
    local requested_tokens = tonumber(ARGV[3])
    local now = tonumber(ARGV[4])

    local data = redis.call("HMGET", key, "tokens", "last_update")
    local tokens = tonumber(data[1])
    local last_update = tonumber(data[2])

    if tokens == nil then
        tokens = capacity
        last_update = now
    else
        local delta = math.max(0, now - last_update)
        tokens = math.min(capacity, tokens + (delta * refill_rate))
        last_update = now
    end

    if tokens >= requested_tokens then
        tokens = tokens - requested_tokens
        redis.call("HMSET", key, "tokens", tokens, "last_update", last_update)
        redis.call("EXPIRE", key, 3600)
        return {1, tokens}
    else
        redis.call("HMSET", key, "tokens", tokens, "last_update", last_update)
        redis.call("EXPIRE", key, 3600)
        return {0, tokens}
    end
    """

    def __init__(self, redis_client: redis.Redis, capacity: int, refill_rate_per_sec: float):
        self.client = redis_client
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.script_sha = self.client.script_load(self.LUA_SCRIPT)

    def consume(self, bucket_key: str, tokens_needed: int) -> Tuple[bool, float]:
        now = time.time()
        result = self.client.evalsha(
            self.script_sha,
            1,
            bucket_key,
            self.capacity,
            self.refill_rate,
            tokens_needed,
            now
        )
        allowed = bool(result[0] == 1)
        remaining_tokens = float(result[1])
        return allowed, remaining_tokens
