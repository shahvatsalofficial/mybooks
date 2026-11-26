from __future__ import annotations

import asyncio
import time
from typing import Awaitable, Callable, Dict, Tuple
from pydantic import BaseModel


class IngressStats(BaseModel):
    accepted: int = 0
    deduplicated: int = 0
    rejected_full: int = 0
    processed: int = 0


class WebhookIngressQueue:
    """Bounded AsyncIO ingress buffer with idempotency deduplication."""

    def __init__(self, maxsize: int = 500, idempotency_ttl_s: int = 3600) -> None:
        self._queue: asyncio.Queue[Tuple[str, dict]] = asyncio.Queue(maxsize=maxsize)
        self._seen: Dict[str, float] = {}
        self._ttl = idempotency_ttl_s
        self.stats = IngressStats()

    def _evict_expired(self) -> None:
        now = time.monotonic()
        expired = [k for k, ts in self._seen.items() if (now - ts) > self._ttl]
        for key in expired:
            del self._seen[key]

    async def enqueue(self, idempotency_key: str, payload: dict) -> str:
        self._evict_expired()
        if idempotency_key in self._seen:
            self.stats.deduplicated += 1
            return "DEDUPLICATED"
        if self._queue.full():
            self.stats.rejected_full += 1
            return "BACKPRESSURE_429"
        self._seen[idempotency_key] = time.monotonic()
        await self._queue.put((idempotency_key, payload))
        self.stats.accepted += 1
        return "ACCEPTED"

    async def run_workers(
        self,
        worker_count: int,
        handler: Callable[[str, dict], Awaitable[None]],
    ) -> None:
        async def _worker() -> None:
            while True:
                key, item = await self._queue.get()
                try:
                    await handler(key, item)
                    self.stats.processed += 1
                finally:
                    self._queue.task_done()

        workers = [asyncio.create_task(_worker()) for _ in range(worker_count)]
        await self._queue.join()
        for w in workers:
            w.cancel()


async def main() -> None:
    ingress = WebhookIngressQueue(maxsize=10)
    results = []
    for key, body in [
        ("idem_01", {"ticket": "T1"}),
        ("idem_01", {"ticket": "T1_retry"}),
        ("idem_02", {"ticket": "T2"}),
    ]:
        results.append(await ingress.enqueue(key, body))

    async def process_ticket(key: str, data: dict) -> None:
        await asyncio.sleep(0.01)

    await ingress.run_workers(worker_count=2, handler=process_ticket)
    print("Enqueue results:", results)
    print("Ingress stats:", ingress.stats.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
