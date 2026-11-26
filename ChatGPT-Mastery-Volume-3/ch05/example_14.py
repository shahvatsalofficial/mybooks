# runaway_circuit_breaker.py
import redis
import time

class CostCircuitBreaker:
    def __init__(self, redis_client: redis.Redis, max_tokens_per_minute: int = 50000):
        self.r = redis_client
        self.limit = max_tokens_per_minute

    def check_and_record_consumption(self, session_id: str, tokens_consumed: int) -> bool:
        """Returns True if within safe operational bounds, False if circuit breaker tripped."""
        now = int(time.time())
        key = f"token_meter:{session_id}"
        
        pipe = self.r.pipeline()
        pipe.zadd(key, {f"{now}:{tokens_consumed}": now})
        # Evict entries older than 60 seconds
        pipe.zremrangebyscore(key, 0, now - 60)
        pipe.zrange(key, 0, -1)
        pipe.expire(key, 120)
        _, _, recent_entries, _ = pipe.execute()
        
        total_tokens_in_window = sum(int(entry.decode().split(":")[1]) for entry in recent_entries)
        
        if total_tokens_in_window > self.limit:
            # Trip circuit breaker: quarantine session
            self.r.setex(f"quarantine:{session_id}", 300, "EXCEEDED_RATE_LIMIT")
            return False
            
        return True
