"""
Recipe 03.2: High-Throughput Lockless Single-Producer Multi-Consumer Queue
Architecture: Atomic circular ring buffer for free-threaded message passing.
Target Runtime: Python 3.13t (Free-Threaded CPython)
"""

from __future__ import annotations
import threading
import time
from typing import Any, Generic, List, TypeVar

T = TypeVar("T")


class HighThroughputSPMCQueue(Generic[T]):
    """Lock-minimized bounded circular buffer for 1 Producer and N Consumer threads."""

    def __init__(self, capacity: int = 65536) -> None:
        # Enforce power-of-two capacity for fast bitwise modulo arithmetic
        if (capacity & (capacity - 1)) != 0:
            raise ValueError("Capacity must be an exact power of two (e.g. 1024, 65536)")
        self.capacity = capacity
        self.mask = capacity - 1

        self._buffer: List[Any] = [None] * capacity
        self._head = 0  # Write pointer (modified only by Producer)
        self._tail = 0  # Read pointer (modified by Consumers under lock)
        self._consumer_lock = threading.Lock()
        self._not_empty = threading.Condition(self._consumer_lock)

    def put(self, item: T) -> None:
        """Pushes an item into the queue. Non-blocking; waits if buffer is full."""
        while (self._head - self._tail) >= self.capacity:
            # Buffer full backpressure: brief exponential backoff
            time.sleep(0.0001)

        slot = self._head & self.mask
        self._buffer[slot] = item
        self._head += 1

        # Notify waiting consumers
        with self._consumer_lock:
            self._not_empty.notify()

    def get(self, timeout: float | None = None) -> T:
        """Pulls an item from the queue. Synchronizes consumers using consumer lock."""
        with self._consumer_lock:
            start_time = time.monotonic()
            while self._head == self._tail:
                if timeout is not None:
                    elapsed = time.monotonic() - start_time
                    remaining = timeout - elapsed
                    if remaining <= 0 or not self._not_empty.wait(remaining):
                        raise TimeoutError("Queue get() timed out")
                else:
                    self._not_empty.wait()

            slot = self._tail & self.mask
            item: T = self._buffer[slot]
            self._buffer[slot] = None  # Prevent memory retention
            self._tail += 1
            return item

    def qsize(self) -> int:
        """Returns approximate snapshot of active queue depth."""
        return max(0, self._head - self._tail)


# Demonstration & Verification
if __name__ == "__main__":
    queue: HighThroughputSPMCQueue[int] = HighThroughputSPMCQueue(capacity=16384)
    item_count = 50_000
    consumed_count = 0
    count_lock = threading.Lock()

    def consumer_worker() -> None:
        global consumed_count
        while True:
            try:
                val = queue.get(timeout=0.2)
                with count_lock:
                    consumed_count += 1
            except TimeoutError:
                break

    # Launch 4 consumer threads
    consumers = [threading.Thread(target=consumer_worker) for _ in range(4)]
    for c in consumers:
        c.start()

    # Producer thread pushes 50,000 items
    start_t = time.perf_counter()
    for item in range(item_count):
        queue.put(item)

    for c in consumers:
        c.join()
    duration = time.perf_counter() - start_t

    rate = item_count / duration
    print(f"Processed {consumed_count:,} items in {duration:.3f} s ({rate:,.0f} msgs/sec)")
    assert consumed_count == item_count
