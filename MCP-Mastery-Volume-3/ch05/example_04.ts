// distributed_limiter.ts — Production Redis Sliding-Window Rate Limiter
import Redis from 'ioredis';
import crypto from 'crypto';

export interface RateLimitResult {
    allowed: boolean;
    remaining: number;
    retryAfterSeconds: number;
}

export class DistributedRateLimiter {
    private redis: Redis;

    constructor(redisUrl: string = 'redis://127.0.0.1:6379') {
        this.redis = new Redis(redisUrl);
        this.defineLuaScript();
    }

    private defineLuaScript(): void {
        this.redis.defineCommand('slidingWindowRateLimit', {
            numberOfKeys: 1,
            lua: `
                local key = KEYS[1]
                local now = tonumber(ARGV[1])
                local window_ms = tonumber(ARGV[2])
                local max_limit = tonumber(ARGV[3])
                local request_id = ARGV[4]

                local clear_before = now - window_ms
                redis.call('ZREMRANGEBYSCORE', key, 0, clear_before)
                local current_count = redis.call('ZCARD', key)

                if current_count < max_limit then
                    redis.call('ZADD', key, now, request_id)
                    redis.call('PEXPIRE', key, window_ms)
                    return { 1, max_limit - current_count - 1, 0 }
                else
                    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                    local oldest_time = tonumber(oldest[2])
                    local retry_after_ms = (oldest_time + window_ms) - now
                    local retry_after_sec = math.ceil(retry_after_ms / 1000)
                    if retry_after_sec < 1 then retry_after_sec = 1 end
                    return { 0, 0, retry_after_sec }
                end
            `
        });
    }

    public async checkRateLimit(
        tenantId: string,
        maxRequestsPerMinute: number = 600
    ): Promise<RateLimitResult> {
        const key = `mcp:ratelimit:sliding:${tenantId}`;
        const now = Date.now();
        const windowMs = 60000;
        const requestId = crypto.randomUUID();

        const [allowedFlag, remaining, retryAfter] = (await (this.redis as any).slidingWindowRateLimit(
            key,
            now,
            windowMs,
            maxRequestsPerMinute,
            requestId
        )) as [number, number, number];

        return {
            allowed: allowedFlag === 1,
            remaining,
            retryAfterSeconds: retryAfter
        };
    }
}
