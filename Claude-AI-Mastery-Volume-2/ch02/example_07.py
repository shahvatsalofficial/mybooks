# Production Patch: Bounded Semaphore Dispatcher + Circuit Breaker
class BoundedToolDispatcher:
    def __init__(self, max_concurrent_db_calls: int = 10):
        # Strictly clamp concurrent database calls to protect connection pool
        self.semaphore = asyncio.Semaphore(max_concurrent_db_calls)

    async def execute_bounded_query(self, container_id: str) -> dict:
        async with self.semaphore:
            # Enforces that at most 10 database queries run simultaneously
            return await db_pool.fetch_manifest(container_id)
