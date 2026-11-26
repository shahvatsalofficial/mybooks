from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field


@dataclass
class AsyncTokenBucket:
    rate_per_sec: float
    capacity: float
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        self._tokens = self.capacity
        self._last_refill = time.monotonic()

    async def acquire(self, tokens: float = 1.0) -> float:
        wait_total = 0.0
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(self.capacity, self._tokens + elapsed * self.rate_per_sec)
                self._last_refill = now
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return wait_total
                deficit = tokens - self._tokens
                sleep_for = deficit / self.rate_per_sec
            await asyncio.sleep(sleep_for)
            wait_total += sleep_for


async def fetch_with_retry(
    node: SubQueryNode,
    bucket: AsyncTokenBucket,
    sem: asyncio.Semaphore,
    max_retries: int = 3,
) -> tuple[str, int, float]:
    start = time.perf_counter()
    for attempt in range(1, max_retries + 1):
        await bucket.acquire(1.0)
        async with sem:
            try:
                # Simulated network latency with occasional transient 429
                await asyncio.sleep(0.04 + random.uniform(0.01, 0.03))
                if attempt == 1 and node.node_id.endswith("1"):
                    raise TimeoutError("Simulated transient upstream 429")
                elapsed_ms = (time.perf_counter() - start) * 1000
                return node.node_id, node.max_results, elapsed_ms
            except TimeoutError:
                if attempt == max_retries:
                    raise
                backoff = (0.05 * (2 ** (attempt - 1))) + random.uniform(0.0, 0.02)
                await asyncio.sleep(backoff)
    raise RuntimeError("Unreachable retry exit")


async def main() -> None:
    bucket = AsyncTokenBucket(rate_per_sec=10.0, capacity=4.0)
    sem = asyncio.Semaphore(4)
    nodes = [
        SubQueryNode(
            node_id=f"q_{i}",
            query_text=f"benchmark query aspect {i}",
            target_tiers=[SourceTier.PRIMARY_OFFICIAL],
            max_results=5,
        )
        for i in range(6)
    ]
    t0 = time.perf_counter()
    results = await asyncio.gather(*(fetch_with_retry(n, bucket, sem) for n in nodes))
    total_ms = (time.perf_counter() - t0) * 1000
    for nid, count, lat in results:
        print(f"Node={nid} fetched={count} docs latency={lat:.1f}ms")
    print(f"All {len(results)} nodes completed in {total_ms:.1f}ms")


if __name__ == "__main__":
    asyncio.run(main())
