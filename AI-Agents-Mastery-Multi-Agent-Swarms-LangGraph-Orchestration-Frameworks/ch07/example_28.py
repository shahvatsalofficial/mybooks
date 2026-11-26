class RedisContentionExporter:
    @staticmethod
    def export(lock_timeouts: int, avg_wait_ms: float) -> str:
        return (
            f"redis_lock_timeouts_total {lock_timeouts}\n"
            f"redis_avg_lock_wait_ms {avg_wait_ms:.2f}\n"
        )
