"""
Architectural Drill 5: Atomic Token Bucket Rate Limiter with Redis Lua
"""

import redis

LUA_TOKEN_BUCKET = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2]) -- tokens per second
local requested = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

local data = redis.call('HMGET', key, 'tokens', 'last_updated')
local tokens = tonumber(data[1])
local last_updated = tonumber(data[2])

if not tokens then
    tokens = max_tokens
    last_updated = now
else
    local delta = math.max(0, now - last_updated)
    tokens = math.min(max_tokens, tokens + (delta * refill_rate))
    last_updated = now
end

if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)
    redis.call('EXPIRE', key, 86400)
    return {1, tokens} -- Allowed: true, Remaining tokens
else
    return {0, tokens} -- Allowed: false, Current tokens
end
"""

def check_user_quota(redis_client: redis.Redis, user_id: str, cost: int = 1) -> bool:
    import time
    key = f"rate_limit:{user_id}"
    now = int(time.time())
    
    # 100 max capacity, refill 0.01 tokens/sec (approx 1 token every 100s)
    result = redis_client.eval(LUA_TOKEN_BUCKET, 1, key, 100, 0.01, cost, now)
    allowed, remaining = result[0], result[1]
    return bool(allowed)
