"""
Recipe 03.1: True Multi-Core Scaling CPU Harness with Biased Refcounting
Architecture: Free-threaded parallel worker matrix validating zero-GIL scaling.
Target Runtime: Python 3.13t (Free-Threaded CPython)
"""

from __future__ import annotations
import math
import sys
import threading
import time
from typing import Callable, List, Tuple


def check_free_threaded_runtime() -> bool:
    """Verifies that the current interpreter is running in free-threaded mode."""
    # sys._is_gil_enabled() returns False in free-threaded Python 3.13t
    if hasattr(sys, "_is_gil_enabled"):
        return not sys._is_gil_enabled()
    return False


def cpu_intensive_kernel(iterations: int) -> float:
    """Pure CPU-bound numerical work-function executing mathematical operations."""
    acc = 0.0
    for i in range(1, iterations + 1):
        # Numerical calculation exercising math library and floating-point registers
        acc += math.sin(i) * math.cos(i) + math.sqrt(i)
    return acc


class MultiCoreHarness:
    """Coordinates and benchmarks parallel worker threads across physical CPU cores."""

    def __init__(self, num_threads: int, total_work_units: int) -> None:
        self.num_threads = num_threads
        self.total_work_units = total_work_units
        self.results: List[float] = [0.0] * num_threads

    def _thread_worker(self, index: int, iterations_per_thread: int) -> None:
        self.results[index] = cpu_intensive_kernel(iterations_per_thread)

    def execute_benchmark(self) -> Tuple[float, float, float]:
        """Executes parallel threads and computes speedup against sequential baseline.
        
        Returns:
            Tuple of (Sequential Time, Parallel Time, Measured Speedup Factor)
        """
        work_per_thread = self.total_work_units // self.num_threads

        # 1. Measure Sequential Execution Time
        seq_start = time.perf_counter()
        _ = cpu_intensive_kernel(self.total_work_units)
        seq_duration = time.perf_counter() - seq_start

        # 2. Measure Parallel Thread Execution Time
        threads: List[threading.Thread] = []
        par_start = time.perf_counter()

        for i in range(self.num_threads):
            t = threading.Thread(
                target=self._thread_worker,
                args=(i, work_per_thread),
                name=f"WorkerCore_{i:02d}",
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        par_duration = time.perf_counter() - par_start
        speedup = seq_duration / par_duration if par_duration > 0 else 0.0

        return seq_duration, par_duration, speedup


if __name__ == "__main__":
    is_free_threaded = check_free_threaded_runtime()
    status_label = "ENABLED (PEP 703 Multi-Core)" if is_free_threaded else "DISABLED (Standard GIL)"
    print(f"CPython Free-Threaded Mode: {status_label}")

    core_count = 8
    workload = 10_000_000
    print(f"Executing CPU scaling harness across {core_count} threads ({workload:,} total iterations)...")

    harness = MultiCoreHarness(num_threads=core_count, total_work_units=workload)
    seq_time, par_time, speedup = harness.execute_benchmark()

    print(f"Sequential Duration: {seq_time:.3f} s")
    print(f"Parallel Duration:   {par_time:.3f} s")
    print(f"Measured Speedup:    {speedup:.2f}x (Theoretical Max: {core_count:.1f}x)")

    if is_free_threaded:
        assert speedup > 3.5, f"Expected >3.5x speedup on {core_count} cores, got {speedup:.2f}x"
