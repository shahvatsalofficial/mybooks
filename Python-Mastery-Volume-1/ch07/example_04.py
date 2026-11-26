"""
Recipe 07.3: Custom Freelist Memory Pool
File: recipe_07_3_custom_freelist.py
Python Version: 3.12+
"""

from __future__ import annotations
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FreelistBuffer")


class TelemetryEvent:
    """Slotted, reusable object instance."""
    __slots__ = ("sensor_id", "timestamp_ns", "temperature", "voltage")

    def __init__(self) -> None:
        self.sensor_id: int = 0
        self.timestamp_ns: int = 0
        self.temperature: float = 0.0
        self.voltage: float = 0.0

    def reset(self, sensor_id: int, timestamp_ns: int, temp: float, volt: float) -> TelemetryEvent:
        """In-place attribute mutation without re-allocating PyObject on heap."""
        self.sensor_id = sensor_id
        self.timestamp_ns = timestamp_ns
        self.temperature = temp
        self.voltage = volt
        return self


class TelemetryEventFreelist:
    """High-speed object freelist eliminating heap allocation churn."""
    
    def __init__(self, capacity: int = 5000) -> None:
        self.capacity = capacity
        # Pre-allocate pool of instances
        self._pool: list[TelemetryEvent] = [TelemetryEvent() for _ in range(capacity)]
        self._index: int = capacity # Points to next available slot

    def acquire(self, sensor_id: int, timestamp_ns: int, temp: float, volt: float) -> TelemetryEvent:
        """Retrieves an existing instance from freelist or allocates fallback."""
        if self._index > 0:
            self._index -= 1
            event = self._pool[self._index]
            return event.reset(sensor_id, timestamp_ns, temp, volt)
        
        # Pool exhausted: Fallback to heap allocation
        obj = TelemetryEvent()
        return obj.reset(sensor_id, timestamp_ns, temp, volt)

    def release(self, event: TelemetryEvent) -> None:
        """Returns instance to freelist pool for instant recycling."""
        if self._index < self.capacity:
            self._pool[self._index] = event
            self._index += 1


def benchmark_freelist_vs_standard() -> None:
    ITERATIONS = 2_000_000

    # 1. Standard Allocation Benchmark
    start_std = time.perf_counter()
    for i in range(ITERATIONS):
        # Allocates brand new PyObject struct on heap every iteration
        e = TelemetryEvent()
        e.reset(i, 1000, 36.5, 3.3)
    duration_std = time.perf_counter() - start_std

    # 2. Freelist Recycled Benchmark
    freelist = TelemetryEventFreelist(capacity=1000)
    start_fl = time.perf_counter()
    for i in range(ITERATIONS):
        e = freelist.acquire(i, 1000, 36.5, 3.3)
        freelist.release(e) # Instantly returned to pool
    duration_fl = time.perf_counter() - start_fl

    logger.info(f"Standard Heap Allocations: {duration_std:.3f}s ({ITERATIONS/duration_std:,.0f} ops/sec)")
    logger.info(f"Freelist Recycled Pool:     {duration_fl:.3f}s ({ITERATIONS/duration_fl:,.0f} ops/sec)")
    logger.info(f"Throughput Gain: {duration_std / duration_fl:.2f}x faster with ZERO GC garbage!")


if __name__ == "__main__":
    benchmark_freelist_vs_standard()
