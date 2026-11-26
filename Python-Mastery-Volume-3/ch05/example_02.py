# resilience/bulkhead.py
"""Asynchronous Bulkhead concurrency limiter with timeout-based load shedding."""

from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import logging

logger = logging.getLogger("bulkhead")


class BulkheadFullException(Exception):
    """Raised when bulkhead capacity and acquisition timeout are exhausted."""
    pass


class AsyncBulkhead:
    """Isolates operational concurrency using an asyncio.Semaphore with bounded acquisition waits."""

    def __init__(self, name: str, max_concurrent: int = 20, max_wait_duration: float = 0.5) -> None:
        self.name = name
        self.max_concurrent = max_concurrent
        self.max_wait_duration = max_wait_duration
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_count = 0
        self._lock = asyncio.Lock()

    @property
    def active_slots(self) -> int:
        return self._active_count

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        """Context manager acquiring a bulkhead execution slot or shedding load upon timeout."""
        try:
            # Attempt to acquire a slot within the bounded wait timeout
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.max_wait_duration,
            )
        except asyncio.TimeoutError as err:
            logger.warning(
                "Bulkhead [%s]: Capacity exhausted (%d active). Shedding request after %.2fs timeout.",
                self.name,
                self._active_count,
                self.max_wait_duration,
            )
            raise BulkheadFullException(
                f"Bulkhead '{self.name}' is saturated. Inflight ceiling of {self.max_concurrent} reached."
            ) from err

        async with self._lock:
            self._active_count += 1
            logger.debug("Bulkhead [%s]: Slot acquired. Active: %d/%d", self.name, self._active_count, self.max_concurrent)

        try:
            yield
        finally:
            async with self._lock:
                self._active_count -= 1
                logger.debug("Bulkhead [%s]: Slot released. Active: %d/%d", self.name, self._active_count, self.max_concurrent)
            self._semaphore.release()
